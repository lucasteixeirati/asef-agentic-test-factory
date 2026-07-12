from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .domain import RunState, RunStatus, TERMINAL_STATES, utc_now


class InvalidTransition(ValueError):
    pass


Guard = Callable[[RunState], bool]


@dataclass(slots=True, frozen=True)
class Transition:
    source: RunStatus
    target: RunStatus
    reason: str
    guard: Guard | None = None


def _always(_: RunState) -> bool:
    return True


TRANSITIONS: tuple[Transition, ...] = (
    Transition(RunStatus.RECEIVED, RunStatus.VALIDATING_INPUT, "start"),
    Transition(RunStatus.VALIDATING_INPUT, RunStatus.INSPECTING_SUT, "input_valid"),
    Transition(RunStatus.VALIDATING_INPUT, RunStatus.FAILED, "input_invalid"),
    Transition(RunStatus.INSPECTING_SUT, RunStatus.ANALYZING_REQUIREMENT, "sut_supported"),
    Transition(RunStatus.INSPECTING_SUT, RunStatus.FAILED, "sut_unsupported"),
    Transition(RunStatus.ANALYZING_REQUIREMENT, RunStatus.WAITING_FOR_CLARIFICATION, "clarification_required"),
    Transition(RunStatus.ANALYZING_REQUIREMENT, RunStatus.ANALYZING_RISK, "analysis_complete"),
    Transition(RunStatus.WAITING_FOR_CLARIFICATION, RunStatus.ANALYZING_REQUIREMENT, "clarification_received"),
    Transition(RunStatus.WAITING_FOR_CLARIFICATION, RunStatus.CANCELLED, "clarification_cancelled"),
    Transition(RunStatus.ANALYZING_RISK, RunStatus.DESIGNING_SCENARIOS, "risks_ready"),
    Transition(RunStatus.DESIGNING_SCENARIOS, RunStatus.REVIEWING_TEST_DESIGN, "design_ready"),
    Transition(RunStatus.REVIEWING_TEST_DESIGN, RunStatus.DESIGNING_SCENARIOS, "design_retry"),
    Transition(RunStatus.REVIEWING_TEST_DESIGN, RunStatus.GENERATING_TESTS, "design_accepted"),
    Transition(RunStatus.GENERATING_TESTS, RunStatus.STATIC_VALIDATION, "tests_generated"),
    Transition(RunStatus.STATIC_VALIDATION, RunStatus.CORRECTING_TESTS, "test_correction_required"),
    Transition(RunStatus.STATIC_VALIDATION, RunStatus.EXECUTING_TESTS, "static_validation_passed"),
    Transition(RunStatus.STATIC_VALIDATION, RunStatus.POLICY_BLOCKED, "policy_violation"),
    Transition(RunStatus.CORRECTING_TESTS, RunStatus.STATIC_VALIDATION, "tests_corrected"),
    Transition(RunStatus.EXECUTING_TESTS, RunStatus.EXECUTING_TESTS, "infrastructure_retry"),
    Transition(RunStatus.EXECUTING_TESTS, RunStatus.FAILED, "infrastructure_failed"),
    Transition(RunStatus.EXECUTING_TESTS, RunStatus.EVALUATING_EVIDENCE, "execution_complete"),
    Transition(RunStatus.EVALUATING_EVIDENCE, RunStatus.CORRECTING_TESTS, "test_invalid"),
    Transition(RunStatus.EVALUATING_EVIDENCE, RunStatus.WAITING_FOR_HUMAN_REVIEW, "sut_defect_suspected"),
    Transition(RunStatus.EVALUATING_EVIDENCE, RunStatus.GENERATING_REPORT, "evaluation_complete"),
    Transition(RunStatus.WAITING_FOR_HUMAN_REVIEW, RunStatus.CORRECTING_TESTS, "human_requests_test_correction"),
    Transition(RunStatus.WAITING_FOR_HUMAN_REVIEW, RunStatus.GENERATING_REPORT, "human_decision_recorded"),
    Transition(RunStatus.WAITING_FOR_HUMAN_REVIEW, RunStatus.CANCELLED, "human_cancelled"),
    Transition(RunStatus.GENERATING_REPORT, RunStatus.SUCCEEDED, "success_reported"),
    Transition(RunStatus.GENERATING_REPORT, RunStatus.FAILED, "failure_reported"),
    Transition(RunStatus.GENERATING_REPORT, RunStatus.POLICY_BLOCKED, "policy_reported"),
    Transition(RunStatus.GENERATING_REPORT, RunStatus.BUDGET_EXHAUSTED, "budget_reported"),
)


class WorkflowMachine:
    def __init__(self, state: RunState) -> None:
        self.state = state
        self._index = {(t.source, t.target, t.reason): t for t in TRANSITIONS}

    def allowed_targets(self) -> set[RunStatus]:
        return {t.target for t in TRANSITIONS if t.source == self.state.status}

    def transition(self, target: RunStatus, reason: str) -> RunState:
        if self.state.is_terminal:
            raise InvalidTransition(f"terminal state {self.state.status} cannot transition")

        if target in {RunStatus.CANCELLED, RunStatus.POLICY_BLOCKED, RunStatus.BUDGET_EXHAUSTED}:
            transition = Transition(self.state.status, target, reason, _always)
        else:
            transition = self._index.get((self.state.status, target, reason))

        if transition is None:
            raise InvalidTransition(
                f"invalid transition {self.state.status.value} -> {target.value} ({reason})"
            )
        if transition.guard is not None and not transition.guard(self.state):
            raise InvalidTransition(f"guard rejected transition: {reason}")

        source = self.state.status
        now = utc_now()
        self.state.status = target
        self.state.updated_at = now
        self.state.history.append(
            {"source": source.value, "target": target.value, "reason": reason, "timestamp": now}
        )
        return self.state
