from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any, Mapping

from .contracts import ContractValidationError
from .outcomes import RunClassification, RunStatus


REPORT_SCHEMA_VERSION = "1.0.0"
MAX_REPORT_BYTES = 1024 * 1024
MAX_PUBLIC_TEXT_CHARS = 2_000
MAX_REPORT_ITEMS = 500
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_TRACE_ID = re.compile(
    r"^(?:REQ|BEH|RSK|SCN)-[0-9]{3}|ART-ATTEMPT-[0-9]{3}|"
    r"EXEC-ATTEMPT-[0-9]{3}-(?:generated|oracle)$"
)
_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SECRET = re.compile(
    r"(?:\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"(?i:\b(?:api[_-]?key|password|access[_-]?token|private[_-]?key|secret)"
    r"\b[\"']?\s*[:=]\s*[\"']?[^\s,;\"'}]{4,}))"
)


class ReportSupportLevel(StrEnum):
    REFERENCE = "reference"
    SUPPORTED = "supported"
    EXPERIMENTAL = "experimental"
    PLANNED = "planned"


class TraceNodeKind(StrEnum):
    REQUIREMENT = "REQUIREMENT"
    BEHAVIOR = "BEHAVIOR"
    RISK = "RISK"
    SCENARIO = "SCENARIO"
    ARTIFACT = "ARTIFACT"
    EXECUTION = "EXECUTION"


class TraceLinkKind(StrEnum):
    DERIVED_FROM_REQUIREMENT = "DERIVED_FROM_REQUIREMENT"
    COVERS_SCENARIO = "COVERS_SCENARIO"
    EXECUTES_ARTIFACT = "EXECUTES_ARTIFACT"


class ReportFactCategory(StrEnum):
    REQUIREMENT = "REQUIREMENT"
    ANALYSIS = "ANALYSIS"
    ARTIFACT = "ARTIFACT"
    EXECUTION = "EXECUTION"
    ORACLE = "ORACLE"
    QUALITY = "QUALITY"
    HUMAN = "HUMAN"
    POLICY = "POLICY"
    BUDGET = "BUDGET"
    USAGE = "USAGE"
    INTEGRITY = "INTEGRITY"


class ReportFactSource(StrEnum):
    REQUEST = "REQUEST"
    STATE = "STATE"
    SNAPSHOT = "SNAPSHOT"
    MANIFEST = "MANIFEST"
    EXECUTION = "EXECUTION"
    EVALUATION = "EVALUATION"
    QUALITY = "QUALITY"
    HUMAN_DECISION = "HUMAN_DECISION"
    RUNTIME = "RUNTIME"


class ReportObservationStatus(StrEnum):
    OBSERVED = "OBSERVED"
    NOT_OBSERVED = "NOT_OBSERVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ReportInferenceKind(StrEnum):
    CLASSIFICATION = "CLASSIFICATION"
    FUNCTIONAL_RESULT = "FUNCTIONAL_RESULT"
    QUALITY_INTERPRETATION = "QUALITY_INTERPRETATION"
    EVIDENCE_INTEGRITY = "EVIDENCE_INTEGRITY"
    READINESS = "READINESS"


class ReportRecommendationCode(StrEnum):
    REVIEW_SUT_DEFECT = "REVIEW_SUT_DEFECT"
    REVIEW_GENERATED_TEST = "REVIEW_GENERATED_TEST"
    RUN_ASEF_DOCTOR = "RUN_ASEF_DOCTOR"
    REVIEW_POLICY = "REVIEW_POLICY"
    REVIEW_BUDGET = "REVIEW_BUDGET"
    PROVIDE_CLARIFICATION = "PROVIDE_CLARIFICATION"
    INSPECT_EVIDENCE = "INSPECT_EVIDENCE"
    DO_NOT_USE_IN_PRODUCTION = "DO_NOT_USE_IN_PRODUCTION"


class EvidenceIntegrityStatus(StrEnum):
    VERIFIED = "VERIFIED"
    MISSING = "MISSING"
    MISMATCH = "MISMATCH"
    NOT_CHECKED = "NOT_CHECKED"


class LimitationSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"


class QualityObservationStatus(StrEnum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    NOT_REQUESTED = "NOT_REQUESTED"


@dataclass(slots=True, frozen=True)
class ReportRequirement:
    requirement_id: str
    title: str
    description: str

    def validate(self) -> None:
        if self.requirement_id != "REQ-001":
            raise ContractValidationError("report requirement_id must be REQ-001")
        _public_text(self.title, "report requirement title")
        _public_text(self.description, "report requirement description")


@dataclass(slots=True, frozen=True)
class ReportTraceNode:
    node_id: str
    kind: TraceNodeKind
    statement: str
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        _trace_id(self.node_id, "report trace node")
        if not isinstance(self.kind, TraceNodeKind):
            raise ContractValidationError("report trace node kind must be typed")
        if not _trace_kind_matches(self.node_id, self.kind):
            raise ContractValidationError("report trace node id does not match its kind")
        _public_text(self.statement, "report trace statement")
        _unique_ids(self.evidence_ids, "report trace evidence_ids")


@dataclass(slots=True, frozen=True)
class ReportTraceLink:
    source_id: str
    target_id: str
    kind: TraceLinkKind

    def validate(self) -> None:
        _trace_id(self.source_id, "report trace source")
        _trace_id(self.target_id, "report trace target")
        if self.source_id == self.target_id:
            raise ContractValidationError("report trace link cannot reference itself")
        if not isinstance(self.kind, TraceLinkKind):
            raise ContractValidationError("report trace link kind must be typed")


@dataclass(slots=True, frozen=True)
class ReportEvidence:
    evidence_id: str
    kind: str
    relative_path: str
    sha256: str
    schema_version: str
    integrity_status: EvidenceIntegrityStatus
    publishable: bool
    sanitized: bool

    def validate(self) -> None:
        _safe_id(self.evidence_id, "report evidence_id")
        _public_text(self.kind, "report evidence kind")
        _relative_path(self.relative_path, "report evidence path")
        if not _SHA256.fullmatch(self.sha256):
            raise ContractValidationError("report evidence sha256 is invalid")
        _public_text(self.schema_version, "report evidence schema_version")
        if not isinstance(self.integrity_status, EvidenceIntegrityStatus):
            raise ContractValidationError("report evidence integrity_status must be typed")
        if not isinstance(self.publishable, bool) or not isinstance(self.sanitized, bool):
            raise ContractValidationError("report evidence publication flags must be booleans")
        if self.publishable and not self.sanitized:
            raise ContractValidationError("publishable report evidence must be sanitized")
        if self.publishable and self.integrity_status is not EvidenceIntegrityStatus.VERIFIED:
            raise ContractValidationError("publishable report evidence must be verified")


PublicScalar = str | int | float | bool | None


@dataclass(slots=True, frozen=True)
class ReportFact:
    fact_id: str
    category: ReportFactCategory
    statement_code: str
    value: PublicScalar
    source_kind: ReportFactSource
    observation_status: ReportObservationStatus
    source_ref: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        _safe_id(self.fact_id, "report fact_id")
        if not isinstance(self.category, ReportFactCategory):
            raise ContractValidationError("report fact category must be typed")
        _code(self.statement_code, "report fact statement_code")
        _public_scalar(self.value, "report fact value")
        if not isinstance(self.source_kind, ReportFactSource):
            raise ContractValidationError("report fact source_kind must be typed")
        if not isinstance(self.observation_status, ReportObservationStatus):
            raise ContractValidationError("report fact observation_status must be typed")
        if self.observation_status is not ReportObservationStatus.OBSERVED and self.value is not None:
            raise ContractValidationError("unobserved report fact cannot carry a value")
        if self.observation_status is ReportObservationStatus.OBSERVED and self.value is None:
            raise ContractValidationError("observed report fact requires a value")
        if self.source_ref is not None:
            _relative_path(self.source_ref, "report fact source_ref")
        _unique_ids(self.evidence_ids, "report fact evidence_ids")


@dataclass(slots=True, frozen=True)
class ReportInference:
    inference_id: str
    kind: ReportInferenceKind
    conclusion_code: str
    statement: str
    basis_fact_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    uncertainty: str | None = None

    def validate(self) -> None:
        _safe_id(self.inference_id, "report inference_id")
        if not isinstance(self.kind, ReportInferenceKind):
            raise ContractValidationError("report inference kind must be typed")
        _code(self.conclusion_code, "report inference conclusion_code")
        _public_text(self.statement, "report inference statement")
        _unique_ids(self.basis_fact_ids, "report inference basis_fact_ids", required=True)
        _unique_ids(self.evidence_ids, "report inference evidence_ids", required=True)
        if self.uncertainty is not None:
            _public_text(self.uncertainty, "report inference uncertainty")


@dataclass(slots=True, frozen=True)
class ReportRecommendation:
    recommendation_id: str
    recommendation_code: ReportRecommendationCode
    applies_to: str
    statement: str
    blocking: bool
    related_inference_ids: tuple[str, ...] = ()
    limitation_codes: tuple[str, ...] = ()

    def validate(self) -> None:
        _safe_id(self.recommendation_id, "report recommendation_id")
        if not isinstance(self.recommendation_code, ReportRecommendationCode):
            raise ContractValidationError("report recommendation_code must be allowlisted")
        _safe_id(self.applies_to, "report recommendation applies_to")
        _public_text(self.statement, "report recommendation statement")
        if not isinstance(self.blocking, bool):
            raise ContractValidationError("report recommendation blocking must be boolean")
        _unique_ids(
            self.related_inference_ids,
            "report recommendation related_inference_ids",
        )
        _unique_codes(self.limitation_codes, "report recommendation limitation_codes")
        if not self.related_inference_ids and not self.limitation_codes:
            raise ContractValidationError(
                "report recommendation requires an inference or limitation"
            )


@dataclass(slots=True, frozen=True)
class ReportLimitation:
    limitation_code: str
    severity: LimitationSeverity
    statement: str

    def validate(self) -> None:
        _code(self.limitation_code, "report limitation_code")
        if not isinstance(self.severity, LimitationSeverity):
            raise ContractValidationError("report limitation severity must be typed")
        _public_text(self.statement, "report limitation statement")


@dataclass(slots=True, frozen=True)
class ReportArtifact:
    artifact_id: str
    relative_path: str
    sha256: str
    scenario_ids: tuple[str, ...]
    attempt: int
    evidence_ids: tuple[str, ...]

    def validate(self) -> None:
        _trace_id(self.artifact_id, "report artifact_id")
        if not self.artifact_id.startswith("ART-ATTEMPT-"):
            raise ContractValidationError("report artifact_id must identify an attempt")
        _relative_path(self.relative_path, "report artifact path")
        if not _SHA256.fullmatch(self.sha256):
            raise ContractValidationError("report artifact sha256 is invalid")
        _unique_ids(self.scenario_ids, "report artifact scenario_ids", required=True)
        if any(not value.startswith("SCN-") for value in self.scenario_ids):
            raise ContractValidationError("report artifact scenario_ids must be SCN identifiers")
        _non_negative_int(self.attempt, "report artifact attempt", positive=True)
        if self.artifact_id != f"ART-ATTEMPT-{self.attempt:03d}":
            raise ContractValidationError("report artifact_id does not reconcile with attempt")
        _unique_ids(self.evidence_ids, "report artifact evidence_ids", required=True)


@dataclass(slots=True, frozen=True)
class ReportAttempt:
    attempt: int
    artifact_id: str
    generated_execution_id: str
    oracle_execution_id: str | None
    outcome: str
    evidence_ids: tuple[str, ...]

    def validate(self) -> None:
        _non_negative_int(self.attempt, "report attempt", positive=True)
        if self.artifact_id != f"ART-ATTEMPT-{self.attempt:03d}":
            raise ContractValidationError("report attempt artifact_id does not reconcile")
        expected = f"EXEC-ATTEMPT-{self.attempt:03d}-generated"
        if self.generated_execution_id != expected:
            raise ContractValidationError("report generated execution id does not reconcile")
        if self.oracle_execution_id is not None and not self.oracle_execution_id.endswith("-oracle"):
            raise ContractValidationError("report oracle execution id is invalid")
        expected_oracle = f"EXEC-ATTEMPT-{self.attempt:03d}-oracle"
        if self.oracle_execution_id is not None and self.oracle_execution_id != expected_oracle:
            raise ContractValidationError("report oracle execution id does not reconcile")
        _code(self.outcome, "report attempt outcome")
        _unique_ids(self.evidence_ids, "report attempt evidence_ids", required=True)


@dataclass(slots=True, frozen=True)
class ReportFunctionalResult:
    accepted: bool
    conclusion_code: str
    tests: int | None
    passed: int | None
    failed: int | None
    errors: int | None
    skipped: int | None
    inference_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]

    def validate(self) -> None:
        if not isinstance(self.accepted, bool):
            raise ContractValidationError("report functional accepted must be boolean")
        _code(self.conclusion_code, "report functional conclusion_code")
        for value, label in (
            (self.tests, "tests"),
            (self.passed, "passed"),
            (self.failed, "failed"),
            (self.errors, "errors"),
            (self.skipped, "skipped"),
        ):
            if value is not None:
                _non_negative_int(value, f"report functional {label}")
        if self.tests is not None:
            parts = (self.passed, self.failed, self.errors, self.skipped)
            if all(value is not None for value in parts) and sum(parts) != self.tests:
                raise ContractValidationError("report functional counters do not reconcile")
        if self.accepted and not (
            self.tests is not None
            and self.tests > 0
            and self.passed == self.tests
            and self.failed == 0
            and self.errors == 0
            and self.skipped == 0
        ):
            raise ContractValidationError("accepted report functional result must fully pass")
        _unique_ids(self.inference_ids, "report functional inference_ids", required=True)
        _unique_ids(self.evidence_ids, "report functional evidence_ids", required=True)


@dataclass(slots=True, frozen=True)
class ReportQualityObservation:
    capability: str
    status: QualityObservationStatus
    complete: bool
    fact_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    limitation_codes: tuple[str, ...] = ()

    def validate(self) -> None:
        _safe_id(self.capability, "report quality capability")
        if not isinstance(self.status, QualityObservationStatus):
            raise ContractValidationError("report quality status must be typed")
        if not isinstance(self.complete, bool):
            raise ContractValidationError("report quality complete must be boolean")
        if self.complete != (self.status is QualityObservationStatus.COMPLETED):
            raise ContractValidationError("report quality complete does not reconcile with status")
        _unique_ids(self.fact_ids, "report quality fact_ids")
        _unique_ids(self.evidence_ids, "report quality evidence_ids")
        _unique_codes(self.limitation_codes, "report quality limitation_codes")
        if not self.complete and not self.limitation_codes:
            raise ContractValidationError("incomplete report quality requires a limitation")
        if self.complete and (not self.fact_ids or not self.evidence_ids):
            raise ContractValidationError("complete report quality requires facts and evidence")


@dataclass(slots=True, frozen=True)
class ReportHumanIntervention:
    intervention_id: str
    kind: str
    decision_code: str
    evidence_ids: tuple[str, ...]

    def validate(self) -> None:
        _safe_id(self.intervention_id, "report human intervention_id")
        _code(self.kind, "report human intervention kind")
        _code(self.decision_code, "report human decision_code")
        _unique_ids(self.evidence_ids, "report human evidence_ids", required=True)


@dataclass(slots=True, frozen=True)
class ReportPolicyAndBudgets:
    max_model_calls: int
    max_test_corrections: int
    max_input_tokens: int
    max_output_tokens: int
    max_workflow_seconds: int
    api_budget_brl: float

    def validate(self) -> None:
        for value, label in (
            (self.max_model_calls, "max_model_calls"),
            (self.max_test_corrections, "max_test_corrections"),
            (self.max_input_tokens, "max_input_tokens"),
            (self.max_output_tokens, "max_output_tokens"),
            (self.max_workflow_seconds, "max_workflow_seconds"),
        ):
            _non_negative_int(value, f"report budget {label}")
        _non_negative_number(self.api_budget_brl, "report api budget")


@dataclass(slots=True, frozen=True)
class ReportUsage:
    model_calls: int
    provider_retries: int
    test_corrections: int
    input_tokens: int
    output_tokens: int
    elapsed_ms: int
    estimated_cost_brl: float

    def validate(self) -> None:
        for value, label in (
            (self.model_calls, "model_calls"),
            (self.provider_retries, "provider_retries"),
            (self.test_corrections, "test_corrections"),
            (self.input_tokens, "input_tokens"),
            (self.output_tokens, "output_tokens"),
            (self.elapsed_ms, "elapsed_ms"),
        ):
            _non_negative_int(value, f"report usage {label}")
        _non_negative_number(self.estimated_cost_brl, "report estimated cost")


@dataclass(slots=True, frozen=True)
class AlphaRunReport:
    report_id: str
    asef_version: str
    run_id: str
    workflow_id: str
    workflow_version: str
    status: RunStatus
    classification: RunClassification
    terminal: bool
    execution_mode: str
    language_profile: str
    support_level: ReportSupportLevel
    context_snapshot_ref: str
    report_generated_from_state_schema: str
    requirement: ReportRequirement
    traceability_nodes: tuple[ReportTraceNode, ...]
    traceability_links: tuple[ReportTraceLink, ...]
    artifacts: tuple[ReportArtifact, ...]
    attempts: tuple[ReportAttempt, ...]
    functional_result: ReportFunctionalResult | None
    quality: tuple[ReportQualityObservation, ...]
    human_interventions: tuple[ReportHumanIntervention, ...]
    policy_and_budgets: ReportPolicyAndBudgets
    usage: ReportUsage
    evidence: tuple[ReportEvidence, ...]
    facts: tuple[ReportFact, ...]
    inferences: tuple[ReportInference, ...]
    recommendations: tuple[ReportRecommendation, ...]
    limitations: tuple[ReportLimitation, ...]
    schema_version: str = REPORT_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != REPORT_SCHEMA_VERSION:
            raise ContractValidationError("unsupported Alpha report schema")
        for value, label in (
            (self.report_id, "report_id"),
            (self.asef_version, "ASEF version"),
            (self.run_id, "run_id"),
            (self.workflow_id, "workflow_id"),
            (self.workflow_version, "workflow_version"),
            (self.language_profile, "language_profile"),
            (self.report_generated_from_state_schema, "state schema"),
        ):
            _safe_id(value, f"Alpha report {label}")
        if self.report_id != self.run_id:
            raise ContractValidationError("Alpha report_id must equal run_id")
        if not isinstance(self.status, RunStatus) or not isinstance(
            self.classification, RunClassification
        ):
            raise ContractValidationError("Alpha report status/classification must be typed")
        if not isinstance(self.terminal, bool):
            raise ContractValidationError("Alpha report terminal must be boolean")
        expected_terminal = self.status in _TERMINAL_STATUSES
        if self.terminal != expected_terminal:
            raise ContractValidationError("Alpha report terminal does not reconcile with status")
        _status_classification(self.status, self.classification)
        if self.execution_mode not in {"demo", "live"}:
            raise ContractValidationError("Alpha report execution_mode must be demo or live")
        if not isinstance(self.support_level, ReportSupportLevel):
            raise ContractValidationError("Alpha report support_level must be typed")
        _relative_path(self.context_snapshot_ref, "Alpha report context_snapshot_ref")

        self.requirement.validate()
        _bounded(self.traceability_nodes, "traceability nodes", required=True)
        _bounded(self.traceability_links, "traceability links")
        _bounded(self.artifacts, "artifacts")
        _bounded(self.attempts, "attempts")
        _bounded(self.quality, "quality observations")
        _bounded(self.human_interventions, "human interventions")
        _bounded(self.evidence, "evidence", required=True)
        _bounded(self.facts, "facts", required=True)
        _bounded(self.inferences, "inferences", required=True)
        _bounded(self.recommendations, "recommendations")
        _bounded(self.limitations, "limitations", required=True)

        for collection in (
            self.traceability_nodes,
            self.traceability_links,
            self.artifacts,
            self.attempts,
            self.quality,
            self.human_interventions,
            self.evidence,
            self.facts,
            self.inferences,
            self.recommendations,
            self.limitations,
        ):
            for item in collection:
                item.validate()
        self.policy_and_budgets.validate()
        self.usage.validate()
        if self.functional_result is not None:
            self.functional_result.validate()
        if self.status is RunStatus.SUCCEEDED and self.functional_result is None:
            raise ContractValidationError("successful Alpha report requires functional_result")
        if self.status is RunStatus.SUCCEEDED and (not self.artifacts or not self.attempts):
            raise ContractValidationError("successful Alpha report requires artifacts and attempts")

        self._validate_references()
        encoded = json.dumps(self.to_dict(validate=False), ensure_ascii=False).encode("utf-8")
        if len(encoded) > MAX_REPORT_BYTES:
            raise ContractValidationError("Alpha report exceeds the public size limit")

    def _validate_references(self) -> None:
        nodes = _identity_set(self.traceability_nodes, "node_id", "traceability nodes")
        if "REQ-001" not in nodes:
            raise ContractValidationError("Alpha report traceability requires REQ-001")
        evidence = _identity_set(self.evidence, "evidence_id", "evidence")
        facts = _identity_set(self.facts, "fact_id", "facts")
        inferences = _identity_set(self.inferences, "inference_id", "inferences")
        artifacts = _identity_set(self.artifacts, "artifact_id", "artifacts")
        limitations = _identity_set(self.limitations, "limitation_code", "limitations")
        _identity_set(self.recommendations, "recommendation_id", "recommendations")
        _identity_set(self.human_interventions, "intervention_id", "human interventions")
        quality_capabilities = [item.capability for item in self.quality]
        if len(quality_capabilities) != len(set(quality_capabilities)):
            raise ContractValidationError("Alpha report quality capabilities must be unique")
        attempt_numbers = [item.attempt for item in self.attempts]
        if len(attempt_numbers) != len(set(attempt_numbers)):
            raise ContractValidationError("Alpha report attempts must be unique")
        for prefix in ("BEH", "RSK", "SCN"):
            _canonical_trace_sequence(nodes, prefix)

        link_keys: set[tuple[str, str, TraceLinkKind]] = set()
        for link in self.traceability_links:
            if link.source_id not in nodes or link.target_id not in nodes:
                raise ContractValidationError("Alpha report trace link references an unknown node")
            key = (link.source_id, link.target_id, link.kind)
            if key in link_keys:
                raise ContractValidationError("Alpha report contains duplicate trace links")
            link_keys.add(key)
            _validate_link_semantics(link, self.traceability_nodes)

        for node in self.traceability_nodes:
            _known(node.evidence_ids, evidence, "trace node evidence")
        scenario_nodes = {
            node.node_id
            for node in self.traceability_nodes
            if node.kind is TraceNodeKind.SCENARIO
        }
        artifact_nodes = {
            node.node_id
            for node in self.traceability_nodes
            if node.kind is TraceNodeKind.ARTIFACT
        }
        execution_nodes = {
            node.node_id
            for node in self.traceability_nodes
            if node.kind is TraceNodeKind.EXECUTION
        }
        for artifact in self.artifacts:
            if artifact.artifact_id not in artifact_nodes:
                raise ContractValidationError("Alpha report artifact lacks a trace node")
            _known(artifact.scenario_ids, scenario_nodes, "artifact scenario")
            _known(artifact.evidence_ids, evidence, "artifact evidence")
            for scenario_id in artifact.scenario_ids:
                expected_link = (
                    artifact.artifact_id,
                    scenario_id,
                    TraceLinkKind.COVERS_SCENARIO,
                )
                if expected_link not in link_keys:
                    raise ContractValidationError(
                        "Alpha report artifact scenario lacks a trace link"
                    )
        for attempt in self.attempts:
            if attempt.artifact_id not in artifacts:
                raise ContractValidationError("Alpha report attempt references unknown artifact")
            if attempt.generated_execution_id not in execution_nodes:
                raise ContractValidationError("Alpha report attempt lacks generated execution node")
            if (
                attempt.oracle_execution_id is not None
                and attempt.oracle_execution_id not in execution_nodes
            ):
                raise ContractValidationError("Alpha report attempt lacks oracle execution node")
            expected_link = (
                attempt.generated_execution_id,
                attempt.artifact_id,
                TraceLinkKind.EXECUTES_ARTIFACT,
            )
            if expected_link not in link_keys:
                raise ContractValidationError(
                    "Alpha report attempt execution lacks a trace link"
                )
            _known(attempt.evidence_ids, evidence, "attempt evidence")
        for item in self.quality:
            _known(item.fact_ids, facts, "quality fact")
            _known(item.evidence_ids, evidence, "quality evidence")
            _known(item.limitation_codes, limitations, "quality limitation")
        for item in self.human_interventions:
            _known(item.evidence_ids, evidence, "human evidence")
        for fact in self.facts:
            _known(fact.evidence_ids, evidence, "fact evidence")
        for inference in self.inferences:
            _known(inference.basis_fact_ids, facts, "inference fact")
            _known(inference.evidence_ids, evidence, "inference evidence")
        for recommendation in self.recommendations:
            _known(
                recommendation.related_inference_ids,
                inferences,
                "recommendation inference",
            )
            _known(
                recommendation.limitation_codes,
                limitations,
                "recommendation limitation",
            )
        if self.functional_result is not None:
            _known(
                self.functional_result.inference_ids,
                inferences,
                "functional inference",
            )
            _known(
                self.functional_result.evidence_ids,
                evidence,
                "functional evidence",
            )
            if self.functional_result.accepted != (
                self.status is RunStatus.SUCCEEDED
                and self.classification is RunClassification.ACCEPTED
            ):
                raise ContractValidationError(
                    "Alpha report functional acceptance does not reconcile with terminal outcome"
                )
        integrity_failed = any(
            item.integrity_status
            in {EvidenceIntegrityStatus.MISSING, EvidenceIntegrityStatus.MISMATCH}
            for item in self.evidence
        )
        if integrity_failed and "EVIDENCE_INTEGRITY_FAILURE" not in limitations:
            raise ContractValidationError(
                "Alpha report evidence failure requires EVIDENCE_INTEGRITY_FAILURE"
            )

    def to_dict(self, *, validate: bool = True) -> dict[str, Any]:
        if validate:
            self.validate()
        return _primitive(asdict(self))


_TERMINAL_STATUSES = {
    RunStatus.SUCCEEDED,
    RunStatus.FAILED,
    RunStatus.CANCELLED,
    RunStatus.POLICY_BLOCKED,
    RunStatus.BUDGET_EXHAUSTED,
}


def alpha_run_report_from_dict(value: Mapping[str, Any]) -> AlphaRunReport:
    _strict_object(value, _REPORT_FIELDS, "Alpha report")
    try:
        report = AlphaRunReport(
            report_id=_string(value, "report_id"),
            asef_version=_string(value, "asef_version"),
            run_id=_string(value, "run_id"),
            workflow_id=_string(value, "workflow_id"),
            workflow_version=_string(value, "workflow_version"),
            status=RunStatus(_string(value, "status")),
            classification=RunClassification(_string(value, "classification")),
            terminal=_boolean(value, "terminal"),
            execution_mode=_string(value, "execution_mode"),
            language_profile=_string(value, "language_profile"),
            support_level=ReportSupportLevel(_string(value, "support_level")),
            context_snapshot_ref=_string(value, "context_snapshot_ref"),
            report_generated_from_state_schema=_string(
                value, "report_generated_from_state_schema"
            ),
            requirement=_requirement(_object(value, "requirement")),
            traceability_nodes=_objects(
                value, "traceability_nodes", _trace_node
            ),
            traceability_links=_objects(
                value, "traceability_links", _trace_link
            ),
            artifacts=_objects(value, "artifacts", _artifact),
            attempts=_objects(value, "attempts", _attempt),
            functional_result=(
                None
                if value.get("functional_result") is None
                else _functional(_object(value, "functional_result"))
            ),
            quality=_objects(value, "quality", _quality),
            human_interventions=_objects(
                value, "human_interventions", _human
            ),
            policy_and_budgets=_budgets(_object(value, "policy_and_budgets")),
            usage=_usage(_object(value, "usage")),
            evidence=_objects(value, "evidence", _evidence),
            facts=_objects(value, "facts", _fact),
            inferences=_objects(value, "inferences", _inference),
            recommendations=_objects(
                value, "recommendations", _recommendation
            ),
            limitations=_objects(value, "limitations", _limitation),
            schema_version=_string(value, "schema_version"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractValidationError(f"invalid Alpha report: {exc}") from exc
    report.validate()
    return report


_REPORT_FIELDS = {
    "schema_version",
    "report_id",
    "asef_version",
    "run_id",
    "workflow_id",
    "workflow_version",
    "status",
    "classification",
    "terminal",
    "execution_mode",
    "language_profile",
    "support_level",
    "context_snapshot_ref",
    "report_generated_from_state_schema",
    "requirement",
    "traceability_nodes",
    "traceability_links",
    "artifacts",
    "attempts",
    "functional_result",
    "quality",
    "human_interventions",
    "policy_and_budgets",
    "usage",
    "evidence",
    "facts",
    "inferences",
    "recommendations",
    "limitations",
}


def _requirement(value: Mapping[str, Any]) -> ReportRequirement:
    _strict_object(value, {"requirement_id", "title", "description"}, "requirement")
    return ReportRequirement(*(_string(value, key) for key in ("requirement_id", "title", "description")))


def _trace_node(value: Mapping[str, Any]) -> ReportTraceNode:
    _strict_object(value, {"node_id", "kind", "statement", "evidence_ids"}, "trace node")
    return ReportTraceNode(
        _string(value, "node_id"),
        TraceNodeKind(_string(value, "kind")),
        _string(value, "statement"),
        _strings(value, "evidence_ids"),
    )


def _trace_link(value: Mapping[str, Any]) -> ReportTraceLink:
    _strict_object(value, {"source_id", "target_id", "kind"}, "trace link")
    return ReportTraceLink(
        _string(value, "source_id"),
        _string(value, "target_id"),
        TraceLinkKind(_string(value, "kind")),
    )


def _artifact(value: Mapping[str, Any]) -> ReportArtifact:
    _strict_object(
        value,
        {"artifact_id", "relative_path", "sha256", "scenario_ids", "attempt", "evidence_ids"},
        "artifact",
    )
    return ReportArtifact(
        _string(value, "artifact_id"),
        _string(value, "relative_path"),
        _string(value, "sha256"),
        _strings(value, "scenario_ids"),
        _integer(value, "attempt"),
        _strings(value, "evidence_ids"),
    )


def _attempt(value: Mapping[str, Any]) -> ReportAttempt:
    _strict_object(
        value,
        {"attempt", "artifact_id", "generated_execution_id", "oracle_execution_id", "outcome", "evidence_ids"},
        "attempt",
    )
    oracle = value.get("oracle_execution_id")
    if oracle is not None and not isinstance(oracle, str):
        raise ContractValidationError("attempt oracle_execution_id must be a string or null")
    return ReportAttempt(
        _integer(value, "attempt"),
        _string(value, "artifact_id"),
        _string(value, "generated_execution_id"),
        oracle,
        _string(value, "outcome"),
        _strings(value, "evidence_ids"),
    )


def _functional(value: Mapping[str, Any]) -> ReportFunctionalResult:
    fields = {"accepted", "conclusion_code", "tests", "passed", "failed", "errors", "skipped", "inference_ids", "evidence_ids"}
    _strict_object(value, fields, "functional result")
    return ReportFunctionalResult(
        _boolean(value, "accepted"),
        _string(value, "conclusion_code"),
        *(_optional_integer(value, key) for key in ("tests", "passed", "failed", "errors", "skipped")),
        _strings(value, "inference_ids"),
        _strings(value, "evidence_ids"),
    )


def _quality(value: Mapping[str, Any]) -> ReportQualityObservation:
    _strict_object(value, {"capability", "status", "complete", "fact_ids", "evidence_ids", "limitation_codes"}, "quality")
    return ReportQualityObservation(
        _string(value, "capability"),
        QualityObservationStatus(_string(value, "status")),
        _boolean(value, "complete"),
        _strings(value, "fact_ids"),
        _strings(value, "evidence_ids"),
        _strings(value, "limitation_codes"),
    )


def _human(value: Mapping[str, Any]) -> ReportHumanIntervention:
    _strict_object(value, {"intervention_id", "kind", "decision_code", "evidence_ids"}, "human intervention")
    return ReportHumanIntervention(
        _string(value, "intervention_id"),
        _string(value, "kind"),
        _string(value, "decision_code"),
        _strings(value, "evidence_ids"),
    )


def _budgets(value: Mapping[str, Any]) -> ReportPolicyAndBudgets:
    fields = {"max_model_calls", "max_test_corrections", "max_input_tokens", "max_output_tokens", "max_workflow_seconds", "api_budget_brl"}
    _strict_object(value, fields, "policy and budgets")
    return ReportPolicyAndBudgets(
        *(
            _integer(value, key)
            for key in (
                "max_model_calls",
                "max_test_corrections",
                "max_input_tokens",
                "max_output_tokens",
                "max_workflow_seconds",
            )
        ),
        _number(value, "api_budget_brl"),
    )


def _usage(value: Mapping[str, Any]) -> ReportUsage:
    fields = {"model_calls", "provider_retries", "test_corrections", "input_tokens", "output_tokens", "elapsed_ms", "estimated_cost_brl"}
    _strict_object(value, fields, "usage")
    return ReportUsage(
        *(_integer(value, key) for key in ("model_calls", "provider_retries", "test_corrections", "input_tokens", "output_tokens", "elapsed_ms")),
        _number(value, "estimated_cost_brl"),
    )


def _evidence(value: Mapping[str, Any]) -> ReportEvidence:
    fields = {"evidence_id", "kind", "relative_path", "sha256", "schema_version", "integrity_status", "publishable", "sanitized"}
    _strict_object(value, fields, "evidence")
    return ReportEvidence(
        _string(value, "evidence_id"),
        _string(value, "kind"),
        _string(value, "relative_path"),
        _string(value, "sha256"),
        _string(value, "schema_version"),
        EvidenceIntegrityStatus(_string(value, "integrity_status")),
        _boolean(value, "publishable"),
        _boolean(value, "sanitized"),
    )


def _fact(value: Mapping[str, Any]) -> ReportFact:
    fields = {"fact_id", "category", "statement_code", "value", "source_kind", "observation_status", "source_ref", "evidence_ids"}
    _strict_object(value, fields, "fact")
    source_ref = value.get("source_ref")
    if source_ref is not None and not isinstance(source_ref, str):
        raise ContractValidationError("fact source_ref must be a string or null")
    scalar = value.get("value")
    if not isinstance(scalar, (str, int, float, bool, type(None))):
        raise ContractValidationError("fact value must be a public scalar")
    return ReportFact(
        _string(value, "fact_id"),
        ReportFactCategory(_string(value, "category")),
        _string(value, "statement_code"),
        scalar,
        ReportFactSource(_string(value, "source_kind")),
        ReportObservationStatus(_string(value, "observation_status")),
        source_ref,
        _strings(value, "evidence_ids"),
    )


def _inference(value: Mapping[str, Any]) -> ReportInference:
    fields = {"inference_id", "kind", "conclusion_code", "statement", "basis_fact_ids", "evidence_ids", "uncertainty"}
    _strict_object(value, fields, "inference")
    uncertainty = value.get("uncertainty")
    if uncertainty is not None and not isinstance(uncertainty, str):
        raise ContractValidationError("inference uncertainty must be a string or null")
    return ReportInference(
        _string(value, "inference_id"),
        ReportInferenceKind(_string(value, "kind")),
        _string(value, "conclusion_code"),
        _string(value, "statement"),
        _strings(value, "basis_fact_ids"),
        _strings(value, "evidence_ids"),
        uncertainty,
    )


def _recommendation(value: Mapping[str, Any]) -> ReportRecommendation:
    fields = {"recommendation_id", "recommendation_code", "applies_to", "statement", "blocking", "related_inference_ids", "limitation_codes"}
    _strict_object(value, fields, "recommendation")
    return ReportRecommendation(
        _string(value, "recommendation_id"),
        ReportRecommendationCode(_string(value, "recommendation_code")),
        _string(value, "applies_to"),
        _string(value, "statement"),
        _boolean(value, "blocking"),
        _strings(value, "related_inference_ids"),
        _strings(value, "limitation_codes"),
    )


def _limitation(value: Mapping[str, Any]) -> ReportLimitation:
    _strict_object(value, {"limitation_code", "severity", "statement"}, "limitation")
    return ReportLimitation(
        _string(value, "limitation_code"),
        LimitationSeverity(_string(value, "severity")),
        _string(value, "statement"),
    )


def _primitive(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {key: _primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_primitive(item) for item in value]
    return value


def _strict_object(value: Mapping[str, Any], fields: set[str], label: str) -> None:
    if not isinstance(value, Mapping):
        raise ContractValidationError(f"{label} must be an object")
    unknown = set(value) - fields
    missing = fields - set(value)
    if unknown:
        raise ContractValidationError(f"{label} contains unknown fields: {sorted(unknown)}")
    if missing:
        raise ContractValidationError(f"{label} is missing fields: {sorted(missing)}")


def _objects(value: Mapping[str, Any], key: str, factory: Any) -> tuple[Any, ...]:
    raw = value.get(key)
    if not isinstance(raw, list):
        raise ContractValidationError(f"Alpha report {key} must be an array")
    if any(not isinstance(item, Mapping) for item in raw):
        raise ContractValidationError(f"Alpha report {key} must contain objects")
    return tuple(factory(item) for item in raw)


def _object(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    raw = value.get(key)
    if not isinstance(raw, Mapping):
        raise ContractValidationError(f"Alpha report {key} must be an object")
    return raw


def _string(value: Mapping[str, Any], key: str) -> str:
    raw = value.get(key)
    if not isinstance(raw, str):
        raise ContractValidationError(f"Alpha report {key} must be a string")
    return raw


def _strings(value: Mapping[str, Any], key: str) -> tuple[str, ...]:
    raw = value.get(key)
    if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
        raise ContractValidationError(f"Alpha report {key} must be an array of strings")
    return tuple(raw)


def _boolean(value: Mapping[str, Any], key: str) -> bool:
    raw = value.get(key)
    if not isinstance(raw, bool):
        raise ContractValidationError(f"Alpha report {key} must be a boolean")
    return raw


def _integer(value: Mapping[str, Any], key: str) -> int:
    raw = value.get(key)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ContractValidationError(f"Alpha report {key} must be an integer")
    return raw


def _optional_integer(value: Mapping[str, Any], key: str) -> int | None:
    raw = value.get(key)
    if raw is None:
        return None
    return _integer(value, key)


def _number(value: Mapping[str, Any], key: str) -> float:
    raw = value.get(key)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ContractValidationError(f"Alpha report {key} must be a number")
    return float(raw)


def _public_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{label} is required")
    if len(value) > MAX_PUBLIC_TEXT_CHARS:
        raise ContractValidationError(f"{label} exceeds the public text limit")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        raise ContractValidationError(f"{label} contains control characters")
    if _SECRET.search(value):
        raise ContractValidationError(f"{label} contains a sensitive value")


def _public_scalar(value: PublicScalar, label: str) -> None:
    if isinstance(value, str):
        _public_text(value, label)
    elif isinstance(value, bool) or value is None:
        return
    elif isinstance(value, int):
        return
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ContractValidationError(f"{label} must be finite")
    else:
        raise ContractValidationError(f"{label} must be a public scalar")


def _safe_id(value: str, label: str) -> None:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ContractValidationError(f"{label} is invalid")


def _trace_id(value: str, label: str) -> None:
    if not isinstance(value, str) or not _TRACE_ID.fullmatch(value):
        raise ContractValidationError(f"{label} is invalid")


def _code(value: str, label: str) -> None:
    if not isinstance(value, str) or not _CODE.fullmatch(value):
        raise ContractValidationError(f"{label} is invalid")


def _relative_path(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ContractValidationError(f"{label} must be a canonical relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or ":" in path.parts[0]
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ContractValidationError(f"{label} must be contained")


def _unique_ids(values: tuple[str, ...], label: str, *, required: bool = False) -> None:
    if not isinstance(values, tuple) or any(not isinstance(value, str) for value in values):
        raise ContractValidationError(f"{label} must be a tuple of strings")
    if required and not values:
        raise ContractValidationError(f"{label} is required")
    if len(values) != len(set(values)):
        raise ContractValidationError(f"{label} must be unique")
    for value in values:
        _safe_id(value, label)


def _unique_codes(values: tuple[str, ...], label: str) -> None:
    if len(values) != len(set(values)):
        raise ContractValidationError(f"{label} must be unique")
    for value in values:
        _code(value, label)


def _bounded(values: tuple[Any, ...], label: str, *, required: bool = False) -> None:
    if not isinstance(values, tuple):
        raise ContractValidationError(f"Alpha report {label} must be a tuple")
    if required and not values:
        raise ContractValidationError(f"Alpha report {label} is required")
    if len(values) > MAX_REPORT_ITEMS:
        raise ContractValidationError(f"Alpha report {label} exceeds the item limit")


def _identity_set(values: tuple[Any, ...], attribute: str, label: str) -> set[str]:
    identities = [getattr(value, attribute) for value in values]
    if len(identities) != len(set(identities)):
        raise ContractValidationError(f"Alpha report {label} must have unique identities")
    return set(identities)


def _known(values: tuple[str, ...], known: set[str], label: str) -> None:
    unknown = set(values) - known
    if unknown:
        raise ContractValidationError(f"Alpha report {label} references unknown ids")


def _non_negative_int(value: int, label: str, *, positive: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractValidationError(f"{label} must be an integer")
    minimum = 1 if positive else 0
    if value < minimum:
        raise ContractValidationError(f"{label} must be at least {minimum}")


def _non_negative_number(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractValidationError(f"{label} must be a number")
    if not math.isfinite(float(value)) or value < 0:
        raise ContractValidationError(f"{label} must be finite and non-negative")


def _trace_kind_matches(node_id: str, kind: TraceNodeKind) -> bool:
    prefixes = {
        TraceNodeKind.REQUIREMENT: "REQ-",
        TraceNodeKind.BEHAVIOR: "BEH-",
        TraceNodeKind.RISK: "RSK-",
        TraceNodeKind.SCENARIO: "SCN-",
        TraceNodeKind.ARTIFACT: "ART-",
        TraceNodeKind.EXECUTION: "EXEC-",
    }
    return node_id.startswith(prefixes[kind])


def _validate_link_semantics(
    link: ReportTraceLink, nodes: tuple[ReportTraceNode, ...]
) -> None:
    kinds = {node.node_id: node.kind for node in nodes}
    pair = (kinds[link.source_id], kinds[link.target_id])
    allowed = {
        TraceLinkKind.DERIVED_FROM_REQUIREMENT: {
            (TraceNodeKind.REQUIREMENT, TraceNodeKind.BEHAVIOR),
            (TraceNodeKind.REQUIREMENT, TraceNodeKind.RISK),
            (TraceNodeKind.REQUIREMENT, TraceNodeKind.SCENARIO),
        },
        TraceLinkKind.COVERS_SCENARIO: {
            (TraceNodeKind.ARTIFACT, TraceNodeKind.SCENARIO),
        },
        TraceLinkKind.EXECUTES_ARTIFACT: {
            (TraceNodeKind.EXECUTION, TraceNodeKind.ARTIFACT),
        },
    }
    if pair not in allowed[link.kind]:
        raise ContractValidationError("Alpha report trace link kind is inconsistent")


def _status_classification(status: RunStatus, classification: RunClassification) -> None:
    exact = {
        RunStatus.SUCCEEDED: RunClassification.ACCEPTED,
        RunStatus.CANCELLED: RunClassification.CANCELLED_BY_USER,
        RunStatus.POLICY_BLOCKED: RunClassification.POLICY_VIOLATION,
        RunStatus.BUDGET_EXHAUSTED: RunClassification.BUDGET_ERROR,
        RunStatus.WAITING_FOR_CLARIFICATION: RunClassification.WAITING_HUMAN,
        RunStatus.WAITING_FOR_HUMAN_REVIEW: RunClassification.SUT_DEFECT_SUSPECTED,
    }
    if status in exact and classification is not exact[status]:
        raise ContractValidationError("Alpha report status/classification do not reconcile")
    if classification is RunClassification.ACCEPTED and status is not RunStatus.SUCCEEDED:
        raise ContractValidationError("Alpha report ACCEPTED classification requires SUCCEEDED")
    if status is RunStatus.FAILED and classification in {
        RunClassification.ACCEPTED,
        RunClassification.UNCLASSIFIED,
        RunClassification.WAITING_HUMAN,
    }:
        raise ContractValidationError("Alpha report failed status has invalid classification")


def _canonical_trace_sequence(identities: set[str], prefix: str) -> None:
    selected = sorted(value for value in identities if value.startswith(f"{prefix}-"))
    expected = [f"{prefix}-{index:03d}" for index in range(1, len(selected) + 1)]
    if selected != expected:
        raise ContractValidationError(
            f"Alpha report {prefix} trace identifiers must be contiguous"
        )
