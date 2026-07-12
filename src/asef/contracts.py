from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import PurePosixPath
from typing import Any
from uuid import uuid4

from .outcomes import RunClassification, RunStatus


STATE_SCHEMA_VERSION = "2.0.0"
CONTRACT_SCHEMA_VERSION = "1.0.0"
WORKFLOW_ID = "WF-001"
WORKFLOW_VERSION = "0.1.0-skeleton"
MAX_REQUIREMENT_CHARS = 20_000
MAX_ARTIFACT_BYTES = 20 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ContractValidationError(ValueError):
    pass


class IncompatibleSchemaError(ContractValidationError):
    pass


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
    timed_out: bool = False
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def validate(self) -> None:
        _require_version(self.schema_version, CONTRACT_SCHEMA_VERSION, "execution result")
        if "@sha256:" not in self.image:
            raise ContractValidationError("execution image must be fixed by digest")
        if not self.command or any(not item or "\x00" in item for item in self.command):
            raise ContractValidationError("execution command must contain safe arguments")
        if any(_looks_sensitive(item) for item in self.command):
            raise ContractValidationError("execution command contains a sensitive value")
        if self.duration_ms < 0:
            raise ContractValidationError("duration_ms cannot be negative")
        for value in (self.tests, self.passed, self.failed):
            if value is not None and value < 0:
                raise ContractValidationError("test counts cannot be negative")
        if self.tests is not None and self.passed is not None and self.failed is not None:
            if self.passed + self.failed > self.tests:
                raise ContractValidationError("passed + failed cannot exceed tests")
        self.stdout_ref.validate()
        self.stderr_ref.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _to_primitive(self)


@dataclass(slots=True, frozen=True)
class SkeletonBudgetLimits:
    max_model_calls: int = 4
    max_provider_retries: int = 1
    max_workflow_seconds: int = 300
    max_input_tokens: int = 30_000
    max_output_tokens: int = 10_000
    api_budget_brl: float = 0.0

    def validate(self) -> None:
        if self.max_model_calls < 1:
            raise ContractValidationError("max_model_calls must be positive")
        if self.max_provider_retries < 0:
            raise ContractValidationError("max_provider_retries cannot be negative")
        for name in ("max_workflow_seconds", "max_input_tokens", "max_output_tokens"):
            if getattr(self, name) < 1:
                raise ContractValidationError(f"{name} must be positive")
        if self.api_budget_brl < 0:
            raise ContractValidationError("api_budget_brl cannot be negative")


@dataclass(slots=True)
class SkeletonBudgetUsage:
    model_calls: int = 0
    provider_retries: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    elapsed_ms: int = 0

    def validate(self) -> None:
        for name in (
            "model_calls",
            "provider_retries",
            "input_tokens",
            "output_tokens",
            "elapsed_ms",
        ):
            if getattr(self, name) < 0:
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
    context_snapshot_ref: str | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    attempts: dict[str, int] = field(default_factory=dict)
    budgets: SkeletonBudgetLimits = field(default_factory=SkeletonBudgetLimits)
    usage: SkeletonBudgetUsage = field(default_factory=SkeletonBudgetUsage)
    errors: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        ensure_compatible_state_schema(self.schema_version)
        self.request.validate()
        if self.workflow_id != WORKFLOW_ID:
            raise ContractValidationError(f"workflow_id must be {WORKFLOW_ID}")
        if self.workflow_version != WORKFLOW_VERSION:
            raise ContractValidationError(f"workflow_version must be {WORKFLOW_VERSION}")
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
        if self.usage.input_tokens > self.budgets.max_input_tokens:
            raise ContractValidationError("input token usage exceeds state budget")
        if self.usage.output_tokens > self.budgets.max_output_tokens:
            raise ContractValidationError("output token usage exceeds state budget")
        if any(value < 0 for value in self.attempts.values()):
            raise ContractValidationError("attempt counters cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _to_primitive(self)


def ensure_compatible_state_schema(version: str) -> None:
    major = _version_major(version)
    expected_major = _version_major(STATE_SCHEMA_VERSION)
    if major == 1:
        raise IncompatibleSchemaError(
            "state schema 1.x belongs to architectural spikes and cannot be resumed; start a new run"
        )
    if major != expected_major:
        raise IncompatibleSchemaError(
            f"state schema major {major} is incompatible with expected major {expected_major}"
        )


def _require_version(actual: str, expected: str, label: str) -> None:
    if actual != expected:
        raise IncompatibleSchemaError(f"{label} schema {actual!r} must be {expected!r}")


def _version_major(version: str) -> int:
    try:
        return int(version.split(".", 1)[0])
    except (ValueError, AttributeError) as exc:
        raise IncompatibleSchemaError(f"invalid schema version: {version!r}") from exc


def _looks_sensitive(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in ("api_key=", "password=", "token=", "secret="))


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
