from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from .contracts import EvidenceRef


class CapabilityRunContractError(ValueError):
    pass


class CapabilityRunStatus(StrEnum):
    RECEIVED = "RECEIVED"
    GENERATING_PLAN = "GENERATING_PLAN"
    WAITING_FOR_HUMAN_REVIEW = "WAITING_FOR_HUMAN_REVIEW"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


class CapabilityRunClassification(StrEnum):
    UNCLASSIFIED = "UNCLASSIFIED"
    PLAN_READY_FOR_REVIEW = "PLAN_READY_FOR_REVIEW"
    ACCEPTED = "ACCEPTED"
    FUNCTIONAL_FAILURE = "FUNCTIONAL_FAILURE"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    BUDGET_ERROR = "BUDGET_ERROR"


TERMINAL_CAPABILITY_STATUSES = frozenset(
    {
        CapabilityRunStatus.SUCCEEDED,
        CapabilityRunStatus.FAILED,
        CapabilityRunStatus.POLICY_BLOCKED,
        CapabilityRunStatus.BUDGET_EXHAUSTED,
    }
)

_ALLOWED_TRANSITIONS = {
    CapabilityRunStatus.RECEIVED: {
        CapabilityRunStatus.GENERATING_PLAN,
        CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW,
        CapabilityRunStatus.POLICY_BLOCKED,
    },
    CapabilityRunStatus.GENERATING_PLAN: {
        CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW,
        CapabilityRunStatus.POLICY_BLOCKED,
        CapabilityRunStatus.BUDGET_EXHAUSTED,
        CapabilityRunStatus.FAILED,
    },
    CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW: {
        CapabilityRunStatus.EXECUTING,
        CapabilityRunStatus.POLICY_BLOCKED,
        CapabilityRunStatus.BUDGET_EXHAUSTED,
    },
    CapabilityRunStatus.EXECUTING: {
        CapabilityRunStatus.SUCCEEDED,
        CapabilityRunStatus.FAILED,
        CapabilityRunStatus.POLICY_BLOCKED,
        CapabilityRunStatus.BUDGET_EXHAUSTED,
    },
}


@dataclass(slots=True, frozen=True)
class CapabilityRunBudgets:
    max_model_calls: int = 2
    max_provider_retries: int = 1
    max_input_tokens: int = 10_000
    max_output_tokens: int = 5_000
    max_requests: int = 20
    max_workflow_seconds: int = 60
    api_budget_brl: float = 0.0

    def validate(self) -> None:
        for name in (
            "max_model_calls",
            "max_provider_retries",
            "max_input_tokens",
            "max_output_tokens",
            "max_requests",
            "max_workflow_seconds",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise CapabilityRunContractError(f"{name} must be a non-negative integer")
        if self.max_requests < 1 or self.max_workflow_seconds < 1:
            raise CapabilityRunContractError("request and workflow budgets must be positive")
        if not math.isfinite(self.api_budget_brl) or self.api_budget_brl < 0:
            raise CapabilityRunContractError("api_budget_brl must be finite and non-negative")


@dataclass(slots=True)
class CapabilityRunUsage:
    model_calls: int = 0
    provider_retries: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    requests: int = 0
    elapsed_ms: int = 0
    estimated_cost_brl: float = 0.0

    def validate(self) -> None:
        for name in ("model_calls", "provider_retries", "input_tokens", "output_tokens", "requests", "elapsed_ms"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise CapabilityRunContractError(f"{name} usage must be a non-negative integer")
        if not math.isfinite(self.estimated_cost_brl) or self.estimated_cost_brl < 0:
            raise CapabilityRunContractError("estimated_cost_brl usage must be finite and non-negative")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class CapabilityRunState:
    workflow_id: str
    skill_id: str
    language_profile: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = "1.0.0"
    status: CapabilityRunStatus = CapabilityRunStatus.RECEIVED
    classification: CapabilityRunClassification = CapabilityRunClassification.UNCLASSIFIED
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    plan_id: str | None = None
    plan_sha256: str | None = None
    budgets: CapabilityRunBudgets = field(default_factory=CapabilityRunBudgets)
    usage: CapabilityRunUsage = field(default_factory=CapabilityRunUsage)
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL_CAPABILITY_STATUSES

    def transition(self, status: CapabilityRunStatus, event: str) -> None:
        if self.terminal:
            raise CapabilityRunContractError("terminal capability run cannot transition")
        previous = self.status
        if status not in _ALLOWED_TRANSITIONS.get(previous, set()):
            raise CapabilityRunContractError(
                f"invalid capability run transition: {previous.value} -> {status.value}"
            )
        self.status = status
        self.updated_at = _utc_now()
        self.history.append(
            {
                "schema_version": "1.0.0",
                "event_id": str(uuid4()),
                "timestamp": self.updated_at,
                "from": previous.value,
                "to": status.value,
                "event": event,
            }
        )

    def validate(self) -> None:
        if self.schema_version != "1.0.0":
            raise CapabilityRunContractError("unsupported capability run schema")
        try:
            UUID(self.run_id)
        except ValueError as exc:
            raise CapabilityRunContractError("run_id must be a UUID") from exc
        if not all(value.strip() for value in (self.workflow_id, self.skill_id, self.language_profile)):
            raise CapabilityRunContractError("workflow, skill and language profile are required")
        try:
            datetime.fromisoformat(self.created_at)
            datetime.fromisoformat(self.updated_at)
        except ValueError as exc:
            raise CapabilityRunContractError("run timestamps must be ISO-8601") from exc
        if (self.plan_id is None) != (self.plan_sha256 is None):
            raise CapabilityRunContractError("plan identity and hash must be set together")
        if self.plan_sha256 is not None and (
            len(self.plan_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.plan_sha256)
        ):
            raise CapabilityRunContractError("plan_sha256 must be lowercase SHA-256")
        if self.status in {
            CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW,
            CapabilityRunStatus.EXECUTING,
            CapabilityRunStatus.SUCCEEDED,
        } and self.plan_id is None:
            raise CapabilityRunContractError("current capability run status requires a persisted plan")
        self.budgets.validate()
        self.usage.validate()
        exceeded = (
            self.usage.model_calls > self.budgets.max_model_calls
            or self.usage.provider_retries > self.budgets.max_provider_retries
            or self.usage.input_tokens > self.budgets.max_input_tokens
            or self.usage.output_tokens > self.budgets.max_output_tokens
            or self.usage.requests > self.budgets.max_requests
            or self.usage.elapsed_ms > self.budgets.max_workflow_seconds * 1_000
            or self.usage.estimated_cost_brl > self.budgets.api_budget_brl
        )
        if exceeded and self.status is not CapabilityRunStatus.BUDGET_EXHAUSTED:
            raise CapabilityRunContractError("usage exceeds budget outside BUDGET_EXHAUSTED")
        allowed_classifications = {
            CapabilityRunStatus.RECEIVED: {CapabilityRunClassification.UNCLASSIFIED},
            CapabilityRunStatus.GENERATING_PLAN: {CapabilityRunClassification.UNCLASSIFIED},
            CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW: {CapabilityRunClassification.PLAN_READY_FOR_REVIEW},
            CapabilityRunStatus.EXECUTING: {CapabilityRunClassification.PLAN_READY_FOR_REVIEW},
            CapabilityRunStatus.SUCCEEDED: {CapabilityRunClassification.ACCEPTED},
            CapabilityRunStatus.FAILED: {
                CapabilityRunClassification.FUNCTIONAL_FAILURE,
                CapabilityRunClassification.INFRASTRUCTURE_ERROR,
            },
            CapabilityRunStatus.POLICY_BLOCKED: {CapabilityRunClassification.POLICY_VIOLATION},
            CapabilityRunStatus.BUDGET_EXHAUSTED: {CapabilityRunClassification.BUDGET_ERROR},
        }
        if self.classification not in allowed_classifications[self.status]:
            raise CapabilityRunContractError("classification does not match capability run status")
        for ref in self.evidence_refs:
            ref.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["status"] = self.status.value
        value["classification"] = self.classification.value
        value["terminal"] = self.terminal
        return value


def capability_run_from_dict(raw: Any) -> CapabilityRunState:
    if not isinstance(raw, dict):
        raise CapabilityRunContractError("capability run state must be an object")
    allowed = {
        "schema_version", "workflow_id", "skill_id", "language_profile", "run_id",
        "status", "classification", "created_at", "updated_at", "plan_id", "plan_sha256",
        "budgets", "usage", "evidence_refs", "facts", "errors", "history", "terminal",
    }
    if set(raw) != allowed:
        raise CapabilityRunContractError("capability run state fields do not match schema 1.0.0")
    try:
        evidence = [EvidenceRef(**item) for item in raw["evidence_refs"]]
        state = CapabilityRunState(
            schema_version=raw["schema_version"],
            workflow_id=raw["workflow_id"],
            skill_id=raw["skill_id"],
            language_profile=raw["language_profile"],
            run_id=raw["run_id"],
            status=CapabilityRunStatus(raw["status"]),
            classification=CapabilityRunClassification(raw["classification"]),
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
            plan_id=raw["plan_id"],
            plan_sha256=raw["plan_sha256"],
            budgets=CapabilityRunBudgets(**raw["budgets"]),
            usage=CapabilityRunUsage(**raw["usage"]),
            evidence_refs=evidence,
            facts=raw["facts"],
            errors=raw["errors"],
            history=raw["history"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise CapabilityRunContractError("capability run state contains invalid fields") from exc
    state.validate()
    if raw["terminal"] is not state.terminal:
        raise CapabilityRunContractError("terminal flag does not match status")
    return state
