from __future__ import annotations

import hashlib
import math
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import PurePosixPath
from typing import Any
from uuid import uuid4

from .outcomes import RunClassification, RunStatus


STATE_SCHEMA_VERSION = "1.3.0"
CONTRACT_SCHEMA_VERSION = "1.0.0"
EXECUTION_SCHEMA_VERSION = "1.1.0"
WORKFLOW_ID = "WF-001"
WORKFLOW_VERSION = "0.1.0-skeleton"
MAX_REQUIREMENT_CHARS = 20_000
MAX_ARTIFACT_BYTES = 20 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ContractValidationError(ValueError):
    pass


class IncompatibleSchemaError(ContractValidationError):
    pass


class RunOrigin(str, Enum):
    NEW = "NEW"
    IMPORTED = "IMPORTED"
    REPLAY = "REPLAY"


class ContextResolution(str, Enum):
    UNRESOLVED = "CONTEXT_UNRESOLVED"
    RESOLVED = "CONTEXT_RESOLVED"


class TestExecutionOutcome(str, Enum):
    UNCLASSIFIED = "UNCLASSIFIED"
    PASSED = "PASSED"
    ASSERTION_FAILURE = "ASSERTION_FAILURE"
    TEST_ERROR = "TEST_ERROR"
    NO_TESTS = "NO_TESTS"
    TOOL_ERROR = "TOOL_ERROR"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True, frozen=True)
class SkeletonRunRequest:
    context_ref: str
    system_id: str
    requested_skill: str
    requirement_title: str
    requirement_description: str
    output_root_ref: str = ".asef/runs"
    execution_mode: str = "demo"
    api_budget_brl: float = 0.0
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        _require_version(self.schema_version, CONTRACT_SCHEMA_VERSION, "run request")
        for name in (
            "context_ref",
            "system_id",
            "requested_skill",
            "requirement_title",
            "requirement_description",
            "output_root_ref",
        ):
            if not str(getattr(self, name)).strip():
                raise ContractValidationError(f"{name} is required")
        if self.execution_mode not in {"demo", "live"}:
            raise ContractValidationError("execution_mode must be demo or live")
        if len(self.requirement_description) > MAX_REQUIREMENT_CHARS:
            raise ContractValidationError(
                f"requirement_description exceeds {MAX_REQUIREMENT_CHARS} characters"
            )
        if not _is_finite_number(self.api_budget_brl):
            raise ContractValidationError("api_budget_brl must be finite")
        if self.api_budget_brl < 0:
            raise ContractValidationError("api_budget_brl cannot be negative")
        if self.execution_mode == "live" and self.api_budget_brl <= 0:
            raise ContractValidationError("live mode requires a positive api_budget_brl")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(slots=True, frozen=True)
class UnitTestArtifact:
    relative_path: str
    content: str
    scenario_ids: tuple[str, ...]
    attempt: int = 1
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        _require_version(self.schema_version, CONTRACT_SCHEMA_VERSION, "unit test artifact")
        if "\\" in self.relative_path:
            raise ContractValidationError("artifact path must use forward slashes")
        path = PurePosixPath(self.relative_path)
        if not self.relative_path.strip() or path == PurePosixPath("."):
            raise ContractValidationError("evidence path is required")
        if path.is_absolute() or ".." in path.parts:
            raise ContractValidationError("artifact path escapes the generated test root")
        if path.parent != PurePosixPath("tests_generated") or path.suffix != ".py":
            raise ContractValidationError(
                "skeleton artifact must be one .py file directly under tests_generated"
            )
        if not self.content.strip():
            raise ContractValidationError("artifact content is required")
        if len(self.content.encode("utf-8")) > MAX_ARTIFACT_BYTES:
            raise ContractValidationError(f"artifact exceeds {MAX_ARTIFACT_BYTES} bytes")
        if self.attempt < 1:
            raise ContractValidationError("attempt must be at least 1")
        if not self.scenario_ids or any(not item.strip() for item in self.scenario_ids):
            raise ContractValidationError("at least one non-empty scenario_id is required")

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["scenario_ids"] = list(self.scenario_ids)
        value["content_sha256"] = self.content_sha256
        return value


@dataclass(slots=True, frozen=True)
class ContextSnapshot:
    source_sha256: str
    qa_profile_id: str
    team_id: str
    system_id: str
    repository_id: str
    skill_id: str
    language_profile: str
    image: str
    provider: str
    model: str
    mode: str
    read_scopes: tuple[str, ...]
    write_scopes: tuple[str, ...]
    mcp_server_ids: tuple[str, ...] = ()
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        _require_version(self.schema_version, CONTRACT_SCHEMA_VERSION, "context snapshot")
        if not _SHA256.fullmatch(self.source_sha256):
            raise ContractValidationError("source_sha256 must be a lowercase SHA-256 digest")
        for name in (
            "qa_profile_id",
            "team_id",
            "system_id",
            "repository_id",
            "skill_id",
            "language_profile",
            "image",
            "provider",
            "model",
            "mode",
        ):
            if not str(getattr(self, name)).strip():
                raise ContractValidationError(f"{name} is required")
        if "@sha256:" not in self.image:
            raise ContractValidationError("context snapshot image must be fixed by digest")
        if self.mode not in {"demo", "live"}:
            raise ContractValidationError("snapshot mode must be demo or live")
        if not self.read_scopes:
            raise ContractValidationError("at least one read scope is required")
        if any(_looks_sensitive(item) for item in (*self.read_scopes, *self.write_scopes)):
            raise ContractValidationError("context snapshot scopes contain a sensitive value")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _to_primitive(self)


@dataclass(slots=True, frozen=True)
class EvidenceRef:
    kind: str
    relative_path: str
    sha256: str
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        _require_version(self.schema_version, CONTRACT_SCHEMA_VERSION, "evidence reference")
        if not self.kind.strip():
            raise ContractValidationError("evidence kind is required")
        path = PurePosixPath(self.relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise ContractValidationError("evidence path must remain relative to the run")
        if not _SHA256.fullmatch(self.sha256):
            raise ContractValidationError("evidence sha256 is invalid")


@dataclass(slots=True, frozen=True)
class NormalizedExecutionResult:
    image: str
    command: tuple[str, ...]
    exit_code: int
    duration_ms: int
    stdout_ref: EvidenceRef
    stderr_ref: EvidenceRef
    tests: int | None = None
    passed: int | None = None
    failed: int | None = None
    errors: int | None = None
    skipped: int | None = None
    tool_id: str | None = None
    tool_version: str | None = None
    outcome: TestExecutionOutcome = TestExecutionOutcome.UNCLASSIFIED
    raw_result_ref: EvidenceRef | None = None
    timed_out: bool = False
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    schema_version: str = EXECUTION_SCHEMA_VERSION

    def validate(self) -> None:
        _require_version(self.schema_version, EXECUTION_SCHEMA_VERSION, "execution result")
        if "@sha256:" not in self.image and not re.fullmatch(r"sha256:[0-9a-f]{64}", self.image):
            raise ContractValidationError("execution image must be fixed by registry digest or image ID")
        if not self.command or any(not item or "\x00" in item for item in self.command):
            raise ContractValidationError("execution command must contain safe arguments")
        if any(_looks_sensitive(item) for item in self.command):
            raise ContractValidationError("execution command contains a sensitive value")
        if self.duration_ms < 0:
            raise ContractValidationError("duration_ms cannot be negative")
        for value in (self.tests, self.passed, self.failed, self.errors, self.skipped):
            if value is not None and value < 0:
                raise ContractValidationError("test counts cannot be negative")
        if self.tests is not None and self.passed is not None and self.failed is not None:
            if self.passed + self.failed > self.tests:
                raise ContractValidationError("passed + failed cannot exceed tests")
        counts = (self.passed, self.failed, self.errors, self.skipped)
        if self.tests is not None and all(value is not None for value in counts):
            if sum(value for value in counts if value is not None) != self.tests:
                raise ContractValidationError("pytest outcome counts must equal tests")
        if (self.tool_id is None) != (self.tool_version is None):
            raise ContractValidationError("execution tool_id and tool_version must be set together")
        if self.tool_id is not None and (not self.tool_id.strip() or not self.tool_version.strip()):
            raise ContractValidationError("execution tool and version cannot be blank")
        self.stdout_ref.validate()
        self.stderr_ref.validate()
        if self.raw_result_ref:
            self.raw_result_ref.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _to_primitive(self)


@dataclass(slots=True, frozen=True)
class SkeletonBudgetLimits:
    max_model_calls: int = 4
    max_provider_retries: int = 1
    max_test_corrections: int = 2
    max_workflow_seconds: int = 300
    max_input_tokens: int = 30_000
    max_output_tokens: int = 10_000
    api_budget_brl: float = 0.0

    def validate(self) -> None:
        if self.max_model_calls < 1:
            raise ContractValidationError("max_model_calls must be positive")
        if self.max_provider_retries < 0:
            raise ContractValidationError("max_provider_retries cannot be negative")
        if self.max_test_corrections < 0 or self.max_test_corrections > 2:
            raise ContractValidationError("max_test_corrections must be between zero and two")
        for name in ("max_workflow_seconds", "max_input_tokens", "max_output_tokens"):
            if getattr(self, name) < 1:
                raise ContractValidationError(f"{name} must be positive")
        if not _is_finite_number(self.api_budget_brl):
            raise ContractValidationError("api_budget_brl must be finite")
        if self.api_budget_brl < 0:
            raise ContractValidationError("api_budget_brl cannot be negative")


@dataclass(slots=True)
class SkeletonBudgetUsage:
    model_calls: int = 0
    provider_retries: int = 0
    test_corrections: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    elapsed_ms: int = 0
    estimated_cost_brl: float = 0.0

    def validate(self) -> None:
        for name in (
            "model_calls",
            "provider_retries",
            "test_corrections",
            "input_tokens",
            "output_tokens",
            "elapsed_ms",
            "estimated_cost_brl",
        ):
            value = getattr(self, name)
            if not _is_finite_number(value):
                raise ContractValidationError(f"{name} usage must be finite")
            if value < 0:
                raise ContractValidationError(f"{name} usage cannot be negative")


@dataclass(slots=True)
class SkeletonRunState:
    request: SkeletonRunRequest
    run_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = STATE_SCHEMA_VERSION
    workflow_id: str = WORKFLOW_ID
    workflow_version: str = WORKFLOW_VERSION
    status: RunStatus = RunStatus.RECEIVED
    classification: RunClassification = RunClassification.UNCLASSIFIED
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    origin: RunOrigin = RunOrigin.NEW
    context_resolution: ContextResolution = ContextResolution.UNRESOLVED
    source_run_id: str | None = None
    source_schema_version: str | None = None
    context_snapshot_ref: str | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    attempts: dict[str, int] = field(default_factory=dict)
    budgets: SkeletonBudgetLimits = field(default_factory=SkeletonBudgetLimits)
    usage: SkeletonBudgetUsage = field(default_factory=SkeletonBudgetUsage)
    errors: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    imported_facts: dict[str, Any] = field(default_factory=dict)
    imported_usage: dict[str, Any] = field(default_factory=dict)
    imported_budgets: dict[str, Any] = field(default_factory=dict)

    def record_event(self, event: str, **details: Any) -> dict[str, Any]:
        timestamp = utc_now()
        try:
            previous = datetime.fromisoformat(self.updated_at)
            current = datetime.fromisoformat(timestamp)
            elapsed_ms = max(0, int((current - previous).total_seconds() * 1_000))
        except ValueError:
            elapsed_ms = 0
        item = {
            "schema_version": "1.0.0",
            "event_id": str(uuid4()),
            "run_id": self.run_id,
            "timestamp": timestamp,
            "elapsed_since_previous_ms": elapsed_ms,
            "event": event,
            **details,
        }
        self.history.append(item)
        self.updated_at = timestamp
        return item

    def validate(self) -> None:
        ensure_compatible_state_schema(self.schema_version)
        self.request.validate()
        if self.workflow_id != WORKFLOW_ID:
            raise ContractValidationError(f"workflow_id must be {WORKFLOW_ID}")
        if self.workflow_version != WORKFLOW_VERSION:
            raise ContractValidationError(f"workflow_version must be {WORKFLOW_VERSION}")
        if self.context_resolution is ContextResolution.RESOLVED and not self.context_snapshot_ref:
            raise ContractValidationError("resolved context requires context_snapshot_ref")
        if self.context_resolution is ContextResolution.UNRESOLVED and self.context_snapshot_ref:
            raise ContractValidationError("unresolved context cannot reference a snapshot")
        if self.origin is RunOrigin.NEW and (self.source_run_id or self.source_schema_version):
            raise ContractValidationError("new run cannot have source provenance")
        if self.origin in {RunOrigin.IMPORTED, RunOrigin.REPLAY}:
            if not self.source_run_id or not self.source_schema_version:
                raise ContractValidationError("imported and replay runs require source provenance")
        if self.origin is RunOrigin.IMPORTED and self.context_resolution is not ContextResolution.UNRESOLVED:
            raise ContractValidationError("imported state must remain context unresolved")
        for ref in self.evidence_refs:
            ref.validate()
        self.budgets.validate()
        self.usage.validate()
        if self.request.api_budget_brl != self.budgets.api_budget_brl:
            raise ContractValidationError("request and state api budgets must match")
        if self.usage.model_calls > self.budgets.max_model_calls:
            raise ContractValidationError("model call usage exceeds state budget")
        if self.usage.provider_retries > self.budgets.max_provider_retries:
            raise ContractValidationError("provider retry usage exceeds state budget")
        if self.usage.test_corrections > self.budgets.max_test_corrections:
            raise ContractValidationError("test correction usage exceeds state budget")
        budget_exhausted = self.status is RunStatus.BUDGET_EXHAUSTED
        if self.usage.input_tokens > self.budgets.max_input_tokens and not budget_exhausted:
            raise ContractValidationError("input token usage exceeds state budget")
        if self.usage.output_tokens > self.budgets.max_output_tokens and not budget_exhausted:
            raise ContractValidationError("output token usage exceeds state budget")
        if self.usage.estimated_cost_brl > self.budgets.api_budget_brl and not budget_exhausted:
            raise ContractValidationError("estimated provider cost exceeds state budget")
        if any(value < 0 for value in self.attempts.values()):
            raise ContractValidationError("attempt counters cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _to_primitive(self)


def ensure_compatible_state_schema(version: str) -> None:
    major = _version_major(version)
    expected_major = _version_major(STATE_SCHEMA_VERSION)
    if major != expected_major:
        raise IncompatibleSchemaError(
            f"state schema major {major} is incompatible with expected major {expected_major}"
        )


def import_state_v1(document: dict[str, Any], request: SkeletonRunRequest) -> SkeletonRunState:
    """Import spike state as evidence; this never resumes or executes the old run."""
    _reject_sensitive_structure(document)
    version = str(document.get("schema_version", ""))
    if version != "1.0.0":
        raise IncompatibleSchemaError(
            f"only state schema 1.0.0 can be imported into {STATE_SCHEMA_VERSION}"
        )
    source_run_id = str(document.get("run_id", "")).strip()
    if not source_run_id:
        raise ContractValidationError("imported state requires run_id")
    usage_data = document.get("usage", {})
    usage = SkeletonBudgetUsage(
        model_calls=int(usage_data.get("model_calls", 0)),
        provider_retries=int(usage_data.get("provider_retries", 0)),
        input_tokens=int(usage_data.get("input_tokens", 0)),
        output_tokens=int(usage_data.get("output_tokens", 0)),
    )
    limits = SkeletonBudgetLimits(
        max_model_calls=max(4, usage.model_calls),
        max_provider_retries=max(1, usage.provider_retries),
        max_input_tokens=max(30_000, usage.input_tokens),
        max_output_tokens=max(10_000, usage.output_tokens),
        api_budget_brl=request.api_budget_brl,
    )
    history = list(document.get("history", []))
    history.append({
        "event": "STATE_IMPORTED",
        "source_schema_version": version,
        "resume_supported": False,
    })
    state = SkeletonRunState(
        request=request,
        run_id=source_run_id,
        origin=RunOrigin.IMPORTED,
        source_run_id=source_run_id,
        source_schema_version=version,
        attempts=dict(document.get("attempts", {})),
        budgets=limits,
        usage=usage,
        errors=list(document.get("errors", [])),
        history=history,
        imported_facts=dict(document.get("facts", {})),
        imported_usage=dict(document.get("usage", {})),
        imported_budgets=dict(document.get("budgets", {})),
    )
    state.validate()
    return state


def start_replay(
    imported: SkeletonRunState,
    *,
    context_snapshot_ref: str,
) -> SkeletonRunState:
    """Create a fresh run linked to an imported run; no mid-node resume is claimed."""
    if imported.origin is not RunOrigin.IMPORTED:
        raise ContractValidationError("replay source must be an imported state")
    if not context_snapshot_ref.strip():
        raise ContractValidationError("replay requires a context snapshot reference")
    attempts = dict(imported.attempts)
    attempts["replay"] = attempts.get("replay", 0) + 1
    state = SkeletonRunState(
        request=imported.request,
        origin=RunOrigin.REPLAY,
        context_resolution=ContextResolution.RESOLVED,
        source_run_id=imported.run_id,
        source_schema_version=imported.schema_version,
        context_snapshot_ref=context_snapshot_ref,
        attempts=attempts,
        budgets=imported.budgets,
        imported_facts=dict(imported.imported_facts),
        imported_usage=dict(imported.imported_usage),
        imported_budgets=dict(imported.imported_budgets),
        history=[*imported.history, {
            "event": "REPLAY_STARTED",
            "source_run_id": imported.run_id,
            "resume_supported": False,
        }],
    )
    state.validate()
    return state


def resolve_new_run_context(
    state: SkeletonRunState,
    *,
    context_snapshot_ref: str,
) -> SkeletonRunState:
    """Bind a validated snapshot before a new run may perform side effects."""
    if state.origin is not RunOrigin.NEW:
        raise ContractValidationError("only a new run can resolve context in place")
    if state.context_resolution is not ContextResolution.UNRESOLVED:
        raise ContractValidationError("run context is already resolved")
    if not context_snapshot_ref.strip():
        raise ContractValidationError("context snapshot reference is required")
    state.context_snapshot_ref = context_snapshot_ref
    state.context_resolution = ContextResolution.RESOLVED
    state.record_event("CONTEXT_RESOLVED", snapshot_ref=context_snapshot_ref)
    state.validate()
    return state


def context_snapshot_from_dict(value: dict[str, Any]) -> ContextSnapshot:
    snapshot = ContextSnapshot(
        source_sha256=value["source_sha256"],
        qa_profile_id=value["qa_profile_id"],
        team_id=value["team_id"],
        system_id=value["system_id"],
        repository_id=value["repository_id"],
        skill_id=value["skill_id"],
        language_profile=value["language_profile"],
        image=value["image"],
        provider=value["provider"],
        model=value["model"],
        mode=value["mode"],
        read_scopes=tuple(value["read_scopes"]),
        write_scopes=tuple(value["write_scopes"]),
        mcp_server_ids=tuple(value.get("mcp_server_ids", [])),
        schema_version=value.get("schema_version", CONTRACT_SCHEMA_VERSION),
    )
    snapshot.validate()
    return snapshot


def state_from_dict(value: dict[str, Any]) -> SkeletonRunState:
    try:
        state = SkeletonRunState(
            request=SkeletonRunRequest(**value["request"]),
            run_id=value["run_id"],
            schema_version=value["schema_version"],
            workflow_id=value["workflow_id"],
            workflow_version=value["workflow_version"],
            status=RunStatus(value["status"]),
            classification=RunClassification(value["classification"]),
            created_at=value["created_at"],
            updated_at=value["updated_at"],
            origin=RunOrigin(value["origin"]),
            context_resolution=ContextResolution(value["context_resolution"]),
            source_run_id=value.get("source_run_id"),
            source_schema_version=value.get("source_schema_version"),
            context_snapshot_ref=value.get("context_snapshot_ref"),
            evidence_refs=[EvidenceRef(**item) for item in value.get("evidence_refs", [])],
            attempts=dict(value.get("attempts", {})),
            budgets=SkeletonBudgetLimits(**value.get("budgets", {})),
            usage=SkeletonBudgetUsage(**value.get("usage", {})),
            errors=list(value.get("errors", [])),
            history=list(value.get("history", [])),
            facts=dict(value.get("facts", {})),
            imported_facts=dict(value.get("imported_facts", {})),
            imported_usage=dict(value.get("imported_usage", {})),
            imported_budgets=dict(value.get("imported_budgets", {})),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractValidationError(f"persisted state is invalid: {exc}") from exc
    state.validate()
    return state


def _require_version(actual: str, expected: str, label: str) -> None:
    if actual != expected:
        raise IncompatibleSchemaError(f"{label} schema {actual!r} must be {expected!r}")


def _version_major(version: str) -> int:
    try:
        return int(version.split(".", 1)[0])
    except (ValueError, AttributeError) as exc:
        raise IncompatibleSchemaError(f"invalid schema version: {version!r}") from exc


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _looks_sensitive(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in ("api_key=", "password=", "token=", "secret="))


def _reject_sensitive_structure(value: Any, path: str = "state") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            sensitive_keys = {
                "api_key",
                "access_token",
                "auth_token",
                "password",
                "private_key",
                "secret",
            }
            if lowered in sensitive_keys or lowered.endswith("_secret"):
                raise ContractValidationError(f"imported state contains sensitive field at {path}.{key}")
            _reject_sensitive_structure(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_sensitive_structure(nested, f"{path}[{index}]")
    elif isinstance(value, str) and _looks_sensitive(value):
        raise ContractValidationError(f"imported state contains sensitive value at {path}")


def _to_primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: _to_primitive(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _to_primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_primitive(item) for item in value]
    return value
