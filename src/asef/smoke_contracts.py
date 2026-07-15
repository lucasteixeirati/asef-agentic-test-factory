from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import Enum, StrEnum
from pathlib import PurePosixPath
from typing import Any

from .contracts import ContractValidationError, EvidenceRef
from .evaluation_contracts import EvaluationAction
from .evaluation_contracts import DatasetCase
from .outcomes import RunClassification, RunStatus


SMOKE_SCHEMA_VERSION = "1.0.0"
SMOKE_CASE_IDS = tuple(f"SMK-{number:03d}" for number in range(1, 11))
MAX_SMOKE_CORRECTIONS = 2
_SHA256 = frozenset("0123456789abcdef")


class SmokeExecutorKind(StrEnum):
    PYTEST_DOCKER = "PYTEST_DOCKER"
    INJECTED_DOCKER_UNAVAILABLE = "INJECTED_DOCKER_UNAVAILABLE"
    NOT_REACHED = "NOT_REACHED"


class SmokeTerminalAction(StrEnum):
    ACCEPT = "ACCEPT"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    STOP = "STOP"
    NOT_REACHED = "NOT_REACHED"


class SmokeComparison(StrEnum):
    MATCHED = "MATCHED"
    MISMATCH = "MISMATCH"
    RUNNER_ERROR = "RUNNER_ERROR"


@dataclass(slots=True, frozen=True)
class CounterExpectation:
    minimum: int
    maximum: int

    def validate(self) -> None:
        if (
            isinstance(self.minimum, bool)
            or isinstance(self.maximum, bool)
            or not isinstance(self.minimum, int)
            or not isinstance(self.maximum, int)
        ):
            raise ContractValidationError("smoke counter bounds must be integers")
        if self.minimum < 0 or self.maximum < self.minimum:
            raise ContractValidationError("smoke counter bounds must be non-negative and ordered")

    def matches(self, actual: int) -> bool:
        self.validate()
        return self.minimum <= actual <= self.maximum


@dataclass(slots=True, frozen=True)
class SmokeExpectedUsage:
    model_calls: CounterExpectation
    provider_retries: CounterExpectation
    corrections: CounterExpectation
    execution_attempts: CounterExpectation

    def validate(self) -> None:
        for expectation in (
            self.model_calls,
            self.provider_retries,
            self.corrections,
            self.execution_attempts,
        ):
            expectation.validate()
        if self.corrections.maximum > MAX_SMOKE_CORRECTIONS:
            raise ContractValidationError(
                f"smoke corrections cannot exceed {MAX_SMOKE_CORRECTIONS}"
            )


@dataclass(slots=True, frozen=True)
class SmokeExpectation:
    status: RunStatus
    classification: RunClassification
    action: SmokeTerminalAction
    usage: SmokeExpectedUsage
    docker_called: bool
    oracle_executed: bool
    human_checkpoint_requested: bool

    def validate(self) -> None:
        if (
            not isinstance(self.status, RunStatus)
            or not isinstance(self.classification, RunClassification)
            or not isinstance(self.action, SmokeTerminalAction)
        ):
            raise ContractValidationError("smoke expectation requires typed terminal enums")
        if not all(
            isinstance(value, bool)
            for value in (
                self.docker_called,
                self.oracle_executed,
                self.human_checkpoint_requested,
            )
        ):
            raise ContractValidationError("smoke expectation flags must be booleans")
        self.usage.validate()
        allowed_terminals = {
            (RunStatus.SUCCEEDED, RunClassification.ACCEPTED, SmokeTerminalAction.ACCEPT),
            (
                RunStatus.WAITING_FOR_CLARIFICATION,
                RunClassification.WAITING_HUMAN,
                SmokeTerminalAction.NOT_REACHED,
            ),
            (
                RunStatus.WAITING_FOR_HUMAN_REVIEW,
                RunClassification.SUT_DEFECT_SUSPECTED,
                SmokeTerminalAction.HUMAN_REVIEW,
            ),
            (
                RunStatus.BUDGET_EXHAUSTED,
                RunClassification.BUDGET_ERROR,
                SmokeTerminalAction.NOT_REACHED,
            ),
            (
                RunStatus.POLICY_BLOCKED,
                RunClassification.POLICY_VIOLATION,
                SmokeTerminalAction.NOT_REACHED,
            ),
            (
                RunStatus.FAILED,
                RunClassification.INFRASTRUCTURE_ERROR,
                SmokeTerminalAction.NOT_REACHED,
            ),
            (
                RunStatus.FAILED,
                RunClassification.INFRASTRUCTURE_ERROR,
                SmokeTerminalAction.STOP,
            ),
            (
                RunStatus.FAILED,
                RunClassification.INCONCLUSIVE,
                SmokeTerminalAction.STOP,
            ),
        }
        if (self.status, self.classification, self.action) not in allowed_terminals:
            raise ContractValidationError("smoke expected terminal status/classification/action is invalid")
        if self.action is SmokeTerminalAction.HUMAN_REVIEW and (
            self.status is not RunStatus.WAITING_FOR_HUMAN_REVIEW
            or self.classification is not RunClassification.SUT_DEFECT_SUSPECTED
            or not self.human_checkpoint_requested
        ):
            raise ContractValidationError(
                "HUMAN_REVIEW requires a suspected SUT defect and a human checkpoint"
            )
        if self.human_checkpoint_requested and self.action is not SmokeTerminalAction.HUMAN_REVIEW:
            raise ContractValidationError("human checkpoint requires HUMAN_REVIEW")
        if self.oracle_executed and not self.docker_called:
            raise ContractValidationError("oracle execution requires Docker execution")


@dataclass(slots=True, frozen=True)
class SmokeDemoSpec:
    case_id: str
    case_version: str
    context_ref: str
    system_id: str
    analysis_cassette_ref: str
    artifact_cassette_refs: tuple[str, ...]
    executor: SmokeExecutorKind
    expected: SmokeExpectation
    schema_version: str = SMOKE_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != SMOKE_SCHEMA_VERSION:
            raise ContractValidationError(
                f"smoke demo schema {self.schema_version!r} must be {SMOKE_SCHEMA_VERSION!r}"
            )
        if self.case_id not in SMOKE_CASE_IDS:
            raise ContractValidationError("smoke demo case_id must be SMK-001 through SMK-010")
        _validate_semver(self.case_version, "smoke case version")
        if not isinstance(self.system_id, str) or not self.system_id.strip():
            raise ContractValidationError("smoke system_id is required")
        if not isinstance(self.executor, SmokeExecutorKind):
            raise ContractValidationError("smoke executor must be a typed enum")
        for ref in (
            self.context_ref,
            self.analysis_cassette_ref,
            *self.artifact_cassette_refs,
        ):
            _validate_repo_ref(ref)
        if len(self.artifact_cassette_refs) > 1 + MAX_SMOKE_CORRECTIONS:
            raise ContractValidationError("smoke demo allows one generation and at most two corrections")
        if len(set(self.artifact_cassette_refs)) != len(self.artifact_cassette_refs):
            raise ContractValidationError("smoke artifact cassette refs must be unique")
        if self.analysis_cassette_ref in self.artifact_cassette_refs:
            raise ContractValidationError("analysis and artifact cassettes must be distinct")
        self.expected.validate()
        if self.expected.usage.corrections.maximum > max(0, len(self.artifact_cassette_refs) - 1):
            raise ContractValidationError("correction expectation exceeds available cassettes")
        if self.executor is SmokeExecutorKind.NOT_REACHED:
            if self.expected.docker_called or self.expected.oracle_executed:
                raise ContractValidationError("NOT_REACHED executor cannot call Docker or oracle")
            if self.expected.usage.execution_attempts.maximum != 0:
                raise ContractValidationError("NOT_REACHED executor requires zero execution attempts")
        elif not self.artifact_cassette_refs:
            raise ContractValidationError("an executable smoke case requires an artifact cassette")
        if self.executor is SmokeExecutorKind.PYTEST_DOCKER and not self.expected.docker_called:
            raise ContractValidationError("PYTEST_DOCKER must expect a Docker call")
        if (
            self.executor is SmokeExecutorKind.INJECTED_DOCKER_UNAVAILABLE
            and self.expected.oracle_executed
        ):
            raise ContractValidationError("injected Docker failure cannot execute the oracle")
        if self.executor is SmokeExecutorKind.INJECTED_DOCKER_UNAVAILABLE and (
            self.expected.status is not RunStatus.FAILED
            or self.expected.classification is not RunClassification.INFRASTRUCTURE_ERROR
            or self.expected.usage.execution_attempts.minimum != 1
        ):
            raise ContractValidationError(
                "injected Docker failure requires FAILED/INFRASTRUCTURE_ERROR and one attempt"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


@dataclass(slots=True, frozen=True)
class LoadedSmokeCase:
    case: DatasetCase
    demo: SmokeDemoSpec
    directory_ref: str


@dataclass(slots=True, frozen=True)
class LoadedSmokeDataset:
    root_ref: str
    cases: tuple[LoadedSmokeCase, ...]
    dataset_hash: str
    loaded_bytes: int


@dataclass(slots=True, frozen=True)
class SmokeActualUsage:
    model_calls: int
    provider_retries: int
    corrections: int
    execution_attempts: int

    def validate(self) -> None:
        values = (
            self.model_calls,
            self.provider_retries,
            self.corrections,
            self.execution_attempts,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in values
        ):
            raise ContractValidationError("actual smoke counters must be non-negative integers")


@dataclass(slots=True, frozen=True)
class SmokeObservation:
    status: RunStatus
    classification: RunClassification
    action: SmokeTerminalAction
    usage: SmokeActualUsage
    docker_called: bool
    oracle_executed: bool
    human_checkpoint_requested: bool
    artifact_hash: str | None = None
    oracle_hash: str | None = None

    def validate(self) -> None:
        if (
            not isinstance(self.status, RunStatus)
            or not isinstance(self.classification, RunClassification)
            or not isinstance(self.action, SmokeTerminalAction)
        ):
            raise ContractValidationError("smoke observation requires typed terminal enums")
        if not all(
            isinstance(value, bool)
            for value in (
                self.docker_called,
                self.oracle_executed,
                self.human_checkpoint_requested,
            )
        ):
            raise ContractValidationError("smoke observation flags must be booleans")
        self.usage.validate()
        for digest in (self.artifact_hash, self.oracle_hash):
            if digest is not None:
                _validate_sha256(digest)


@dataclass(slots=True, frozen=True)
class SmokeCaseResult:
    case_id: str
    case_version: str
    repetition: int
    run_id: str
    run_dir_ref: str
    expected: SmokeExpectation
    actual: SmokeObservation | None
    comparison: SmokeComparison
    semantic_fingerprint: str
    evidence_refs: tuple[EvidenceRef, ...] = ()
    message: str = ""
    schema_version: str = SMOKE_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != SMOKE_SCHEMA_VERSION:
            raise ContractValidationError("unsupported smoke case result schema")
        if (
            self.case_id not in SMOKE_CASE_IDS
            or isinstance(self.repetition, bool)
            or not isinstance(self.repetition, int)
            or self.repetition < 1
        ):
            raise ContractValidationError("invalid smoke result identity")
        if not isinstance(self.comparison, SmokeComparison):
            raise ContractValidationError("smoke comparison must be a typed enum")
        _validate_semver(self.case_version, "smoke result case version")
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ContractValidationError("smoke result run_id is required")
        _validate_repo_ref(self.run_dir_ref)
        self.expected.validate()
        if self.comparison is SmokeComparison.RUNNER_ERROR:
            if self.actual is not None:
                raise ContractValidationError("runner errors cannot claim an actual observation")
        elif self.actual is None:
            raise ContractValidationError("matched and mismatched results require actual facts")
        if self.actual is not None:
            self.actual.validate()
        _validate_sha256(self.semantic_fingerprint)
        if len(self.message.encode("utf-8")) > 2048:
            raise ContractValidationError("smoke result message exceeds 2048 bytes")
        if _looks_absolute(self.message):
            raise ContractValidationError("smoke result message cannot expose an absolute path")
        for ref in self.evidence_refs:
            ref.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


@dataclass(slots=True, frozen=True)
class SmokeSuiteReport:
    suite_id: str
    asef_version: str
    dataset_hash: str
    repeat: int
    environment: str
    results: tuple[SmokeCaseResult, ...]
    matched: int
    mismatched: int
    runner_errors: int
    limitations: tuple[str, ...]
    mode: str = "demo"
    schema_version: str = SMOKE_SCHEMA_VERSION

    @property
    def total(self) -> int:
        return len(self.results)

    def validate(self) -> None:
        if self.schema_version != SMOKE_SCHEMA_VERSION:
            raise ContractValidationError("unsupported smoke suite report schema")
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.suite_id, self.asef_version, self.environment)
        ):
            raise ContractValidationError("smoke suite identity and environment are required")
        _validate_sha256(self.dataset_hash)
        if (
            self.mode != "demo"
            or isinstance(self.repeat, bool)
            or not isinstance(self.repeat, int)
            or not 1 <= self.repeat <= 3
        ):
            raise ContractValidationError("smoke suite supports demo mode and repeat from 1 to 3")
        if (
            not self.results
            or not self.limitations
            or any(not isinstance(item, str) or not item.strip() for item in self.limitations)
        ):
            raise ContractValidationError("smoke suite results and limitations are required")
        for result in self.results:
            result.validate()
            if result.repetition > self.repeat:
                raise ContractValidationError("result repetition exceeds suite repeat")
        actual_counts = {
            comparison: sum(item.comparison is comparison for item in self.results)
            for comparison in SmokeComparison
        }
        if (self.matched, self.mismatched, self.runner_errors) != (
            actual_counts[SmokeComparison.MATCHED],
            actual_counts[SmokeComparison.MISMATCH],
            actual_counts[SmokeComparison.RUNNER_ERROR],
        ):
            raise ContractValidationError("smoke suite counters do not reconcile with results")
        identities = {(item.repetition, item.case_id) for item in self.results}
        if len(identities) != len(self.results):
            raise ContractValidationError("smoke suite contains duplicate case repetitions")
        expected_identities = {
            (repetition, case_id)
            for repetition in range(1, self.repeat + 1)
            for case_id in SMOKE_CASE_IDS
        }
        if identities != expected_identities:
            raise ContractValidationError(
                "smoke suite must contain all ten cases in every repetition"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = _primitive(asdict(self))
        value["total"] = self.total
        return value


def smoke_demo_spec_from_dict(value: dict[str, Any]) -> SmokeDemoSpec:
    _reject_unknown(
        value,
        {
            "schema_version",
            "case_id",
            "case_version",
            "context_ref",
            "system_id",
            "analysis_cassette_ref",
            "artifact_cassette_refs",
            "executor",
            "expected",
        },
        "smoke demo",
    )
    try:
        expected_value = value["expected"]
        if not isinstance(expected_value, dict):
            raise TypeError("expected must be an object")
        _reject_unknown(
            expected_value,
            {
                "status",
                "classification",
                "action",
                "usage",
                "docker_called",
                "oracle_executed",
                "human_checkpoint_requested",
            },
            "smoke expectation",
        )
        usage_value = expected_value["usage"]
        if not isinstance(usage_value, dict):
            raise TypeError("usage must be an object")
        _reject_unknown(
            usage_value,
            {"model_calls", "provider_retries", "corrections", "execution_attempts"},
            "smoke usage",
        )
        usage = SmokeExpectedUsage(
            model_calls=_counter_from_value(usage_value["model_calls"]),
            provider_retries=_counter_from_value(usage_value["provider_retries"]),
            corrections=_counter_from_value(usage_value["corrections"]),
            execution_attempts=_counter_from_value(usage_value["execution_attempts"]),
        )
        expected = SmokeExpectation(
            status=RunStatus(expected_value["status"]),
            classification=RunClassification(expected_value["classification"]),
            action=SmokeTerminalAction(expected_value["action"]),
            usage=usage,
            docker_called=_strict_bool(expected_value["docker_called"]),
            oracle_executed=_strict_bool(expected_value["oracle_executed"]),
            human_checkpoint_requested=_strict_bool(
                expected_value["human_checkpoint_requested"]
            ),
        )
        spec = SmokeDemoSpec(
            case_id=value["case_id"],
            case_version=value["case_version"],
            context_ref=value["context_ref"],
            system_id=value["system_id"],
            analysis_cassette_ref=value["analysis_cassette_ref"],
            artifact_cassette_refs=tuple(value["artifact_cassette_refs"]),
            executor=SmokeExecutorKind(value["executor"]),
            expected=expected,
            schema_version=value.get("schema_version", SMOKE_SCHEMA_VERSION),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ContractValidationError):
            raise
        raise ContractValidationError(f"smoke demo is invalid: {exc}") from exc
    spec.validate()
    return spec


def semantic_fingerprint(value: dict[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def action_from_evaluation(action: EvaluationAction | None) -> SmokeTerminalAction:
    if action is None:
        return SmokeTerminalAction.NOT_REACHED
    return SmokeTerminalAction(action.value)


def _counter_from_value(value: Any) -> CounterExpectation:
    if isinstance(value, bool):
        raise ContractValidationError("smoke counter cannot be boolean")
    if isinstance(value, int):
        return CounterExpectation(value, value)
    if isinstance(value, dict):
        _reject_unknown(value, {"min", "max"}, "smoke counter")
        if set(value) != {"min", "max"}:
            raise ContractValidationError("smoke counter range requires min and max")
        return CounterExpectation(value["min"], value["max"])
    raise ContractValidationError("smoke counter must be an integer or min/max object")


def _strict_bool(value: Any) -> bool:
    if not isinstance(value, bool):
        raise ContractValidationError("smoke flags must be booleans")
    return value


def _reject_unknown(value: dict[str, Any], allowed: set[str], label: str) -> None:
    extras = set(value) - allowed
    if extras:
        raise ContractValidationError(f"{label} contains unknown fields: {sorted(extras)}")


def _validate_repo_ref(value: str) -> None:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ContractValidationError("smoke refs must be non-empty POSIX paths")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path == PurePosixPath("."):
        raise ContractValidationError("smoke refs must remain inside the workspace")
    if path.as_posix() != value:
        raise ContractValidationError("smoke refs must use canonical POSIX paths")


def _validate_semver(value: str, label: str) -> None:
    if not isinstance(value, str):
        raise ContractValidationError(f"{label} must be a string")
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ContractValidationError(f"{label} must use numeric major.minor.patch")


def _validate_sha256(value: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or set(value) - _SHA256:
        raise ContractValidationError("smoke fingerprint must be a lowercase SHA-256")


def _looks_absolute(message: str) -> bool:
    lowered = message.lower()
    return bool(
        "file://" in lowered
        or "traceback (" in lowered
        or re.search(r"(?:^|\s)(?:[a-zA-Z]:[\\/]|/[^\s]+|\\\\[^\s]+)", message)
    )


def _primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_primitive(item) for item in value]
    return value
