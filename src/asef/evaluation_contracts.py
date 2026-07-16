from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from enum import Enum, StrEnum
from pathlib import PurePosixPath
from typing import Any

from .contracts import (
    CONTRACT_SCHEMA_VERSION,
    ContractValidationError,
    EvidenceRef,
    TestExecutionOutcome,
)
from .outcomes import RunClassification


DATASET_SCHEMA_VERSION = "1.0.0"
_DATASET_CASE_FIELDS = {
    "schema_version",
    "case_id",
    "version",
    "kind",
    "title",
    "objective",
    "origin",
    "license",
    "curator",
    "language_profile",
    "sut_ref",
    "requirement_ref",
    "oracle_ref",
    "generation_input_refs",
    "evaluation_input_refs",
    "expected_classifications",
    "allowed_modes",
    "exposure",
    "oracle_policy",
    "tags",
}


class DatasetKind(StrEnum):
    SMOKE = "SMOKE"
    SECURITY = "SECURITY"


class DatasetExposure(StrEnum):
    PUBLIC = "PUBLIC"
    PROTECTED = "PROTECTED"


class OraclePolicy(StrEnum):
    NONE = "NONE"
    PROMPT_ISOLATED = "PROMPT_ISOLATED"


class EvaluationAction(StrEnum):
    ACCEPT = "ACCEPT"
    CORRECT_TEST = "CORRECT_TEST"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    STOP = "STOP"


class QualityCapability(StrEnum):
    COVERAGE = "coverage"
    MUTATION = "mutation"


class QualityCapabilityStatus(StrEnum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


@dataclass(slots=True, frozen=True)
class CorrectionFeedback:
    outcome: TestExecutionOutcome
    diagnostic: str
    fingerprint: str
    truncated: bool = False


def build_correction_feedback(
    outcome: TestExecutionOutcome,
    stdout: str,
    stderr: str,
    *,
    max_bytes: int = 4096,
) -> CorrectionFeedback:
    if max_bytes < 128:
        raise ValueError("correction feedback max_bytes must be at least 128")
    combined = "\n".join(part for part in (stderr, stdout) if part).replace("\x00", "")
    combined = re.sub(
        r"(?i)(api[_-]?key|password|token|secret)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        combined,
    )
    combined = "\n".join(line.rstrip() for line in combined.splitlines()).strip()
    encoded = combined.encode("utf-8")
    truncated = len(encoded) > max_bytes
    if truncated:
        combined = encoded[:max_bytes].decode("utf-8", errors="ignore").rstrip() + "\n[TRUNCATED]"
    canonical = f"{outcome.value}\n{combined}".encode("utf-8")
    return CorrectionFeedback(
        outcome=outcome,
        diagnostic=combined,
        fingerprint=hashlib.sha256(canonical).hexdigest(),
        truncated=truncated,
    )


@dataclass(slots=True, frozen=True)
class CombinedOracleEvaluation:
    generated_outcome: TestExecutionOutcome
    oracle_outcome: TestExecutionOutcome | None
    classification: RunClassification
    action: EvaluationAction
    conclusion: str
    generated_result_ref: EvidenceRef
    oracle_result_ref: EvidenceRef | None = None
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != CONTRACT_SCHEMA_VERSION:
            raise ContractValidationError(
                f"oracle evaluation schema {self.schema_version!r} must be {CONTRACT_SCHEMA_VERSION!r}"
            )
        if not self.conclusion.strip():
            raise ContractValidationError("oracle evaluation conclusion is required")
        self.generated_result_ref.validate()
        if self.oracle_result_ref:
            self.oracle_result_ref.validate()
        expected = evaluate_generated_and_oracle(
            self.generated_outcome,
            self.oracle_outcome,
            self.generated_result_ref,
            self.oracle_result_ref,
        )
        if (self.classification, self.action) != (expected.classification, expected.action):
            raise ContractValidationError("oracle evaluation classification and action are inconsistent")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


def evaluate_generated_and_oracle(
    generated: TestExecutionOutcome,
    oracle: TestExecutionOutcome | None,
    generated_result_ref: EvidenceRef,
    oracle_result_ref: EvidenceRef | None = None,
) -> CombinedOracleEvaluation:
    """Apply the deterministic 5.3 decision matrix without model judgment."""
    infrastructure = {TestExecutionOutcome.TOOL_ERROR, TestExecutionOutcome.INFRASTRUCTURE_ERROR}
    invalid_test = {TestExecutionOutcome.TEST_ERROR, TestExecutionOutcome.NO_TESTS}

    if generated in infrastructure or oracle in infrastructure:
        classification = RunClassification.INFRASTRUCTURE_ERROR
        action = EvaluationAction.STOP
        conclusion = "Execution infrastructure or tooling did not produce conclusive evidence"
    elif generated in invalid_test:
        classification = RunClassification.TEST_ERROR
        action = EvaluationAction.CORRECT_TEST
        conclusion = "The generated test is invalid and may be corrected within budget"
    elif oracle is None or oracle in invalid_test or oracle is TestExecutionOutcome.UNCLASSIFIED:
        classification = RunClassification.INCONCLUSIVE
        action = EvaluationAction.STOP
        conclusion = "The independent oracle did not produce conclusive evidence"
    elif oracle is TestExecutionOutcome.ASSERTION_FAILURE:
        classification = RunClassification.SUT_DEFECT_SUSPECTED
        action = EvaluationAction.HUMAN_REVIEW
        conclusion = "The independent oracle found a possible SUT defect requiring human review"
    elif oracle is TestExecutionOutcome.PASSED and generated is TestExecutionOutcome.PASSED:
        classification = RunClassification.ACCEPTED
        action = EvaluationAction.ACCEPT
        conclusion = "Generated test and independent oracle both passed"
    elif oracle is TestExecutionOutcome.PASSED and generated is TestExecutionOutcome.ASSERTION_FAILURE:
        classification = RunClassification.TEST_ERROR
        action = EvaluationAction.CORRECT_TEST
        conclusion = "The generated test conflicts with a passing independent oracle"
    else:
        classification = RunClassification.INCONCLUSIVE
        action = EvaluationAction.STOP
        conclusion = "The available execution evidence is not sufficient for a deterministic conclusion"

    if oracle is not None and oracle_result_ref is None:
        raise ContractValidationError("oracle_result_ref is required when oracle outcome is present")
    if oracle is None and oracle_result_ref is not None:
        raise ContractValidationError("oracle_result_ref requires an oracle outcome")
    return CombinedOracleEvaluation(
        generated_outcome=generated,
        oracle_outcome=oracle,
        classification=classification,
        action=action,
        conclusion=conclusion,
        generated_result_ref=generated_result_ref,
        oracle_result_ref=oracle_result_ref,
    )


@dataclass(slots=True, frozen=True)
class DatasetCase:
    case_id: str
    version: str
    kind: DatasetKind
    title: str
    objective: str
    origin: str
    license: str
    curator: str
    language_profile: str
    sut_ref: str
    requirement_ref: str
    oracle_ref: str | None
    generation_input_refs: tuple[str, ...]
    evaluation_input_refs: tuple[str, ...]
    expected_classifications: tuple[str, ...]
    allowed_modes: tuple[str, ...] = ("demo",)
    exposure: DatasetExposure = DatasetExposure.PUBLIC
    oracle_policy: OraclePolicy = OraclePolicy.NONE
    tags: tuple[str, ...] = ()
    schema_version: str = DATASET_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != DATASET_SCHEMA_VERSION:
            raise ContractValidationError(
                f"dataset case schema {self.schema_version!r} must be {DATASET_SCHEMA_VERSION!r}"
            )
        expected_prefix = "SMK-" if self.kind is DatasetKind.SMOKE else "SEC-"
        if not self.case_id.startswith(expected_prefix):
            raise ContractValidationError(
                f"case_id {self.case_id!r} does not match dataset kind {self.kind.value}"
            )
        suffix = self.case_id.removeprefix(expected_prefix)
        if len(suffix) != 3 or not suffix.isdigit():
            raise ContractValidationError("dataset case_id must end in three digits")
        _validate_semver(self.version, "dataset version")
        for name in (
            "version",
            "title",
            "objective",
            "origin",
            "license",
            "curator",
            "language_profile",
        ):
            if not str(getattr(self, name)).strip():
                raise ContractValidationError(f"dataset {name} is required")
        if not self.expected_classifications:
            raise ContractValidationError("dataset expected_classifications cannot be empty")
        valid_classifications = {item.value for item in RunClassification}
        unknown_classifications = set(self.expected_classifications) - valid_classifications
        if unknown_classifications:
            raise ContractValidationError(
                "dataset expected_classifications contains unknown values: "
                f"{sorted(unknown_classifications)}"
            )
        if not self.generation_input_refs:
            raise ContractValidationError("dataset generation_input_refs cannot be empty")
        for name, values in (
            ("generation_input_refs", self.generation_input_refs),
            ("evaluation_input_refs", self.evaluation_input_refs),
            ("expected_classifications", self.expected_classifications),
            ("tags", self.tags),
        ):
            if any(not item.strip() for item in values) or len(values) != len(set(values)):
                raise ContractValidationError(f"dataset {name} must contain unique non-empty values")
        if not self.allowed_modes or any(mode not in {"demo", "live"} for mode in self.allowed_modes):
            raise ContractValidationError("dataset allowed_modes must contain demo and/or live")

        refs = (
            self.sut_ref,
            self.requirement_ref,
            *self.generation_input_refs,
            *self.evaluation_input_refs,
        )
        if self.oracle_ref:
            refs = (*refs, self.oracle_ref)
        for ref in refs:
            _validate_repo_ref(ref)

        generation = set(self.generation_input_refs)
        evaluation = set(self.evaluation_input_refs)
        if self.oracle_ref:
            if self.oracle_policy is not OraclePolicy.PROMPT_ISOLATED:
                raise ContractValidationError("oracle_ref requires PROMPT_ISOLATED oracle_policy")
            if self.oracle_ref in generation:
                raise ContractValidationError("oracle_ref cannot be exposed to generation inputs")
            if self.oracle_ref not in evaluation:
                raise ContractValidationError("oracle_ref must be an evaluation input")
        elif self.oracle_policy is not OraclePolicy.NONE:
            raise ContractValidationError("oracle_policy must be NONE when oracle_ref is absent")
        if generation & evaluation:
            raise ContractValidationError("generation and evaluation input refs must be disjoint")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


@dataclass(slots=True, frozen=True)
class CoverageResult:
    tool_id: str
    tool_version: str
    scope: tuple[str, ...]
    lines_covered: int
    lines_total: int
    branches_covered: int
    branches_total: int
    duration_ms: int
    raw_result_ref: EvidenceRef
    exclusions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        _validate_metric_header(
            self.schema_version,
            self.tool_id,
            self.tool_version,
            self.scope,
            self.duration_ms,
            self.raw_result_ref,
        )
        _validate_ratio(self.lines_covered, self.lines_total, "line coverage")
        _validate_ratio(self.branches_covered, self.branches_total, "branch coverage")

    @property
    def line_percent(self) -> float | None:
        return _percent(self.lines_covered, self.lines_total)

    @property
    def branch_percent(self) -> float | None:
        return _percent(self.branches_covered, self.branches_total)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = _primitive(asdict(self))
        value["line_percent"] = self.line_percent
        value["branch_percent"] = self.branch_percent
        return value


@dataclass(slots=True, frozen=True)
class MutationResult:
    tool_id: str
    tool_version: str
    scope: tuple[str, ...]
    mutants_total: int
    killed: int
    survived: int
    invalid: int
    timed_out: int
    not_run: int
    duration_ms: int
    max_mutants: int
    timeout_seconds: int
    raw_result_ref: EvidenceRef
    limitations: tuple[str, ...] = ()
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        _validate_metric_header(
            self.schema_version,
            self.tool_id,
            self.tool_version,
            self.scope,
            self.duration_ms,
            self.raw_result_ref,
        )
        counts = (self.mutants_total, self.killed, self.survived, self.invalid, self.timed_out, self.not_run)
        if any(value < 0 for value in counts):
            raise ContractValidationError("mutation counts cannot be negative")
        if sum(counts[1:]) != self.mutants_total:
            raise ContractValidationError("mutation outcome counts must equal mutants_total")
        if self.max_mutants < 1 or self.timeout_seconds < 1:
            raise ContractValidationError("mutation budgets must be positive")
        processed = self.killed + self.survived + self.invalid + self.timed_out
        if processed > self.max_mutants:
            raise ContractValidationError("processed mutants exceed max_mutants budget")

    @property
    def mutation_score(self) -> float | None:
        conclusive = self.killed + self.survived
        return _percent(self.killed, conclusive)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = _primitive(asdict(self))
        value["mutation_score"] = self.mutation_score
        return value


@dataclass(slots=True, frozen=True)
class QualityCapabilityRequest:
    capability: QualityCapability
    tool_id: str
    tool_version: str
    scope: tuple[str, ...]
    test_paths: tuple[str, ...]
    timeout_seconds: int
    execution_environment_ref: str
    max_mutants: int | None = None
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != CONTRACT_SCHEMA_VERSION:
            raise ContractValidationError(
                f"quality request schema {self.schema_version!r} must be {CONTRACT_SCHEMA_VERSION!r}"
            )
        if not isinstance(self.capability, QualityCapability):
            raise ContractValidationError("quality request capability is invalid")
        if not self.tool_id.strip() or not self.tool_version.strip():
            raise ContractValidationError("quality request tool and version are required")
        _validate_quality_paths(self.scope, "scope")
        _validate_quality_paths(self.test_paths, "test_paths")
        if self.timeout_seconds < 1:
            raise ContractValidationError("quality request timeout_seconds must be positive")
        _validate_public_text(
            self.execution_environment_ref,
            "quality request execution_environment_ref",
            max_chars=300,
        )
        if self.capability is QualityCapability.COVERAGE and self.max_mutants is not None:
            raise ContractValidationError("coverage request cannot declare max_mutants")
        if self.capability is QualityCapability.MUTATION and (
            self.max_mutants is None or self.max_mutants < 1
        ):
            raise ContractValidationError("mutation request requires positive max_mutants")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


@dataclass(slots=True, frozen=True)
class MutationAdmission:
    discovered: tuple[str, ...]
    admitted: tuple[str, ...]
    deferred: tuple[str, ...]
    max_mutants: int

    def validate(self) -> None:
        if self.max_mutants < 1:
            raise ContractValidationError("mutation admission max_mutants must be positive")
        if not self.discovered:
            raise ContractValidationError("mutation admission requires discovered mutants")
        for name, values in (
            ("discovered", self.discovered),
            ("admitted", self.admitted),
            ("deferred", self.deferred),
        ):
            if len(values) != len(set(values)):
                raise ContractValidationError(f"mutation admission {name} contains duplicates")
            if any(not item.strip() or any(ord(char) < 32 for char in item) for item in values):
                raise ContractValidationError(
                    f"mutation admission {name} contains an invalid mutant name"
                )
        if self.discovered != tuple(sorted(self.discovered)):
            raise ContractValidationError("mutation admission discovery order must be canonical")
        if len(self.admitted) > self.max_mutants:
            raise ContractValidationError("mutation admission exceeds max_mutants")
        if self.admitted + self.deferred != self.discovered:
            raise ContractValidationError("mutation admission must partition discovered mutants")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


def admit_mutants(mutant_names: tuple[str, ...], max_mutants: int) -> MutationAdmission:
    if max_mutants < 1:
        raise ContractValidationError("mutation admission max_mutants must be positive")
    if not mutant_names:
        raise ContractValidationError("mutation admission requires discovered mutants")
    if len(mutant_names) != len(set(mutant_names)):
        raise ContractValidationError("mutation admission discovered contains duplicates")
    canonical = tuple(sorted(mutant_names))
    admission = MutationAdmission(
        discovered=canonical,
        admitted=canonical[:max_mutants],
        deferred=canonical[max_mutants:],
        max_mutants=max_mutants,
    )
    admission.validate()
    return admission


@dataclass(slots=True, frozen=True)
class QualityCapabilityObservation:
    capability: QualityCapability
    status: QualityCapabilityStatus
    tool_id: str
    tool_version: str
    scope: tuple[str, ...]
    duration_ms: int
    result: CoverageResult | MutationResult | None = None
    raw_result_ref: EvidenceRef | None = None
    stdout_ref: EvidenceRef | None = None
    stderr_ref: EvidenceRef | None = None
    diagnostic_code: str | None = None
    diagnostic: str | None = None
    limitations: tuple[str, ...] = ()
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != CONTRACT_SCHEMA_VERSION:
            raise ContractValidationError(
                f"quality observation schema {self.schema_version!r} must be {CONTRACT_SCHEMA_VERSION!r}"
            )
        if not isinstance(self.capability, QualityCapability):
            raise ContractValidationError("quality observation capability is invalid")
        if not isinstance(self.status, QualityCapabilityStatus):
            raise ContractValidationError("quality observation status is invalid")
        if not self.tool_id.strip() or not self.tool_version.strip():
            raise ContractValidationError("quality observation tool and version are required")
        _validate_quality_paths(self.scope, "scope")
        if self.duration_ms < 0:
            raise ContractValidationError("quality observation duration_ms cannot be negative")

        if self.status is QualityCapabilityStatus.COMPLETED and self.result is None:
            raise ContractValidationError("completed quality observation requires a result")
        if self.status in {
            QualityCapabilityStatus.UNAVAILABLE,
            QualityCapabilityStatus.FAILED,
        } and self.result is not None:
            raise ContractValidationError(f"{self.status.value} quality observation cannot contain metrics")
        if self.status is not QualityCapabilityStatus.COMPLETED:
            if self.diagnostic_code is None or self.diagnostic is None:
                raise ContractValidationError(
                    "incomplete quality observation requires diagnostic code and message"
                )
        if self.diagnostic_code is not None and not re.fullmatch(
            r"[A-Z][A-Z0-9_]{2,63}", self.diagnostic_code
        ):
            raise ContractValidationError("quality observation diagnostic_code is invalid")
        if self.diagnostic is not None:
            _validate_public_text(self.diagnostic, "quality observation diagnostic", max_chars=500)

        if self.result is not None:
            expected_type = (
                CoverageResult
                if self.capability is QualityCapability.COVERAGE
                else MutationResult
            )
            if not isinstance(self.result, expected_type):
                raise ContractValidationError("quality observation result does not match capability")
            self.result.validate()
            if (
                self.result.tool_id != self.tool_id
                or self.result.tool_version != self.tool_version
                or self.result.scope != self.scope
                or self.result.duration_ms != self.duration_ms
            ):
                raise ContractValidationError("quality observation header differs from result")
            if self.raw_result_ref != self.result.raw_result_ref:
                raise ContractValidationError("quality observation raw evidence differs from result")

        for ref in (self.raw_result_ref, self.stdout_ref, self.stderr_ref):
            if ref is not None:
                ref.validate()
        _validate_unique_text(self.limitations, "quality observation limitations")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = _primitive(asdict(self))
        if self.result is not None:
            value["result"] = self.result.to_dict()
        return value


@dataclass(slots=True, frozen=True)
class QualityEvaluationReport:
    observations: tuple[QualityCapabilityObservation, ...]
    duration_ms: int
    limitations: tuple[str, ...] = ()
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != CONTRACT_SCHEMA_VERSION:
            raise ContractValidationError(
                f"quality report schema {self.schema_version!r} must be {CONTRACT_SCHEMA_VERSION!r}"
            )
        if not self.observations:
            raise ContractValidationError("quality report requires observations")
        capabilities = [item.capability for item in self.observations]
        if len(capabilities) != len(set(capabilities)):
            raise ContractValidationError("quality report capabilities must be unique")
        if self.duration_ms < 0:
            raise ContractValidationError("quality report duration_ms cannot be negative")
        for observation in self.observations:
            observation.validate()
        _validate_unique_text(self.limitations, "quality report limitations")

    @property
    def complete(self) -> bool:
        return bool(self.observations) and all(
            item.status is QualityCapabilityStatus.COMPLETED for item in self.observations
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = _primitive(asdict(self))
        value["observations"] = [item.to_dict() for item in self.observations]
        value["complete"] = self.complete
        return value


def dataset_case_from_dict(value: dict[str, Any]) -> DatasetCase:
    extras = set(value) - _DATASET_CASE_FIELDS
    if extras:
        raise ContractValidationError(f"dataset case contains unknown fields: {sorted(extras)}")
    try:
        case = DatasetCase(
            case_id=value["case_id"],
            version=value["version"],
            kind=DatasetKind(value["kind"]),
            title=value["title"],
            objective=value["objective"],
            origin=value["origin"],
            license=value["license"],
            curator=value["curator"],
            language_profile=value["language_profile"],
            sut_ref=value["sut_ref"],
            requirement_ref=value["requirement_ref"],
            oracle_ref=value.get("oracle_ref"),
            generation_input_refs=tuple(value["generation_input_refs"]),
            evaluation_input_refs=tuple(value.get("evaluation_input_refs", [])),
            expected_classifications=tuple(value["expected_classifications"]),
            allowed_modes=tuple(value.get("allowed_modes", ["demo"])),
            exposure=DatasetExposure(value.get("exposure", "PUBLIC")),
            oracle_policy=OraclePolicy(value.get("oracle_policy", "NONE")),
            tags=tuple(value.get("tags", [])),
            schema_version=value.get("schema_version", DATASET_SCHEMA_VERSION),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractValidationError(f"dataset case is invalid: {exc}") from exc
    case.validate()
    return case


def _validate_repo_ref(value: str) -> None:
    if not value or "\\" in value:
        raise ContractValidationError("dataset refs must be non-empty POSIX paths")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path == PurePosixPath("."):
        raise ContractValidationError("dataset refs must remain inside the repository")
    if path.as_posix() != value:
        raise ContractValidationError("dataset refs must use canonical POSIX paths")
    lowered = value.lower()
    if any(marker in lowered for marker in ("api_key=", "password=", "token=", "secret=")):
        raise ContractValidationError("dataset ref contains a sensitive value")


def _validate_semver(value: str, label: str) -> None:
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ContractValidationError(f"{label} must use numeric major.minor.patch")


def _validate_quality_paths(values: tuple[str, ...], label: str) -> None:
    if not values:
        raise ContractValidationError(f"quality request {label} cannot be empty")
    if len(values) != len(set(values)):
        raise ContractValidationError(f"quality request {label} must be unique")
    for value in values:
        _validate_public_text(value, f"quality request {label}", max_chars=300)
        if "sk-" in value.lower():
            raise ContractValidationError(f"quality request {label} contains a sensitive value")
        if not value or "\\" in value:
            raise ContractValidationError(f"quality request {label} must use POSIX relative paths")
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or path == PurePosixPath("."):
            raise ContractValidationError(f"quality request {label} must remain inside the workspace")
        if path.as_posix() != value:
            raise ContractValidationError(f"quality request {label} must use canonical paths")


def _validate_public_text(value: str, label: str, *, max_chars: int) -> None:
    if not value.strip() or len(value) > max_chars:
        raise ContractValidationError(f"{label} must contain between 1 and {max_chars} characters")
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ContractValidationError(f"{label} contains control characters")
    lowered = value.lower()
    if any(marker in lowered for marker in ("api_key=", "password=", "token=", "secret=")):
        raise ContractValidationError(f"{label} contains a sensitive value")


def _validate_unique_text(values: tuple[str, ...], label: str) -> None:
    if len(values) != len(set(values)):
        raise ContractValidationError(f"{label} must be unique")
    for value in values:
        _validate_public_text(value, label, max_chars=500)


def _validate_metric_header(
    schema_version: str,
    tool_id: str,
    tool_version: str,
    scope: tuple[str, ...],
    duration_ms: int,
    raw_result_ref: EvidenceRef,
) -> None:
    if schema_version != CONTRACT_SCHEMA_VERSION:
        raise ContractValidationError(
            f"quality result schema {schema_version!r} must be {CONTRACT_SCHEMA_VERSION!r}"
        )
    if not tool_id.strip() or not tool_version.strip():
        raise ContractValidationError("quality result tool and version are required")
    if not scope or any(not item.strip() for item in scope):
        raise ContractValidationError("quality result scope cannot be empty")
    if duration_ms < 0:
        raise ContractValidationError("quality result duration_ms cannot be negative")
    raw_result_ref.validate()


def _validate_ratio(covered: int, total: int, label: str) -> None:
    if covered < 0 or total < 0:
        raise ContractValidationError(f"{label} counts cannot be negative")
    if covered > total:
        raise ContractValidationError(f"{label} covered count cannot exceed total")


def _percent(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator * 100 / denominator, 2)


def _primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_primitive(item) for item in value]
    return value
