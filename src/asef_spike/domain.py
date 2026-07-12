from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class RunStatus(StrEnum):
    RECEIVED = "RECEIVED"
    VALIDATING_INPUT = "VALIDATING_INPUT"
    INSPECTING_SUT = "INSPECTING_SUT"
    ANALYZING_REQUIREMENT = "ANALYZING_REQUIREMENT"
    WAITING_FOR_CLARIFICATION = "WAITING_FOR_CLARIFICATION"
    ANALYZING_RISK = "ANALYZING_RISK"
    DESIGNING_SCENARIOS = "DESIGNING_SCENARIOS"
    REVIEWING_TEST_DESIGN = "REVIEWING_TEST_DESIGN"
    GENERATING_TESTS = "GENERATING_TESTS"
    STATIC_VALIDATION = "STATIC_VALIDATION"
    EXECUTING_TESTS = "EXECUTING_TESTS"
    EVALUATING_EVIDENCE = "EVALUATING_EVIDENCE"
    WAITING_FOR_HUMAN_REVIEW = "WAITING_FOR_HUMAN_REVIEW"
    CORRECTING_TESTS = "CORRECTING_TESTS"
    GENERATING_REPORT = "GENERATING_REPORT"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


TERMINAL_STATES = frozenset(
    {
        RunStatus.SUCCEEDED,
        RunStatus.FAILED,
        RunStatus.CANCELLED,
        RunStatus.POLICY_BLOCKED,
        RunStatus.BUDGET_EXHAUSTED,
    }
)


@dataclass(slots=True, frozen=True)
class BudgetLimits:
    max_workflow_seconds: int = 900
    max_model_calls: int = 8
    max_input_tokens: int = 120_000
    max_output_tokens: int = 40_000
    max_test_corrections: int = 2
    max_design_retries: int = 1
    max_provider_retries: int = 2
    max_infrastructure_retries: int = 1
    api_budget_brl: float = 0.0


@dataclass(slots=True)
class BudgetUsage:
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    test_corrections: int = 0
    design_retries: int = 0
    provider_retries: int = 0
    infrastructure_retries: int = 0
    estimated_cost_brl: float = 0.0


@dataclass(slots=True, frozen=True)
class WorkflowRequest:
    requirement_title: str
    requirement_description: str
    sut_entrypoint: str
    language_profile: str = "python-pytest"
    execution_mode: str = "demo"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.requirement_title.strip():
            errors.append("requirement_title is required")
        if not self.requirement_description.strip():
            errors.append("requirement_description is required")
        if not self.sut_entrypoint.strip():
            errors.append("sut_entrypoint is required")
        if self.execution_mode not in {"demo", "live"}:
            errors.append("execution_mode must be demo or live")
        if len(self.requirement_description) > 20_000:
            errors.append("requirement_description exceeds 20000 characters")
        return errors


@dataclass(slots=True)
class RunState:
    request: WorkflowRequest
    run_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = "1.0.0"
    workflow_id: str = "WF-001"
    workflow_version: str = "0.0.1-spike"
    status: RunStatus = RunStatus.RECEIVED
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    attempts: dict[str, int] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    budgets: BudgetLimits = field(default_factory=BudgetLimits)
    usage: BudgetUsage = field(default_factory=BudgetUsage)

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATES

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result

