from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from time import monotonic
from typing import Callable

from ..adapters.capability_run_store import CapabilityRunStore
from ..adapters.java_unit_compiler import JavaUnitTestCompiler
from ..adapters.java_unit_execution import DockerJavaUnitExecutor
from ..adapters.java_unit_plan_agent import JavaUnitPlanAgentAdapter
from ..application.ports import ExecutionOutput, ProviderTransientError
from ..capability_runs import CapabilityRunBudgets, CapabilityRunClassification, CapabilityRunContractError, CapabilityRunState, CapabilityRunStatus
from ..contracts import TestExecutionOutcome
from ..java_unit_contracts import JavaUnitTestPlan


@dataclass(slots=True, frozen=True)
class JavaUnitPlanRunOutput:
    state: CapabilityRunState
    plan: JavaUnitTestPlan | None


@dataclass(slots=True, frozen=True)
class JavaUnitExecutionRunOutput:
    state: CapabilityRunState
    result: ExecutionOutput | None


class GenerateJavaUnitPlanService:
    def __init__(self, agent: JavaUnitPlanAgentAdapter, store: CapabilityRunStore) -> None:
        self.agent, self.store = agent, store

    def execute(self, requirement: str, budgets: CapabilityRunBudgets | None = None) -> JavaUnitPlanRunOutput:
        state = CapabilityRunState("WF-JAVA-001", "java-unit", "java-junit", budgets=budgets or CapabilityRunBudgets())
        self.store.create(state)
        state.transition(CapabilityRunStatus.GENERATING_PLAN, "plan_generation_started")
        self.store.save_state(state)
        if state.budgets.max_model_calls < 1:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "model_call_budget_exhausted")
            self.store.save_state(state)
            return JavaUnitPlanRunOutput(state, None)
        generated = None
        started = monotonic()
        while generated is None:
            state.usage.model_calls += 1; self.store.save_state(state)
            try:
                generated = self.agent.generate(requirement)
            except ProviderTransientError as exc:
                state.errors.append({"type": type(exc).__name__, "message": str(exc)[:500]})
                if state.usage.provider_retries >= state.budgets.max_provider_retries or state.usage.model_calls >= state.budgets.max_model_calls:
                    state.classification = CapabilityRunClassification.INFRASTRUCTURE_ERROR
                    state.transition(CapabilityRunStatus.FAILED, "provider_retry_budget_exhausted")
                    self.store.save_state(state); raise
                state.usage.provider_retries += 1; self.store.save_state(state)
            except Exception as exc:
                state.usage.input_tokens += max(0, int(getattr(exc, "input_tokens", 0)))
                state.usage.output_tokens += max(0, int(getattr(exc, "output_tokens", 0)))
                state.errors.append({"type": type(exc).__name__, "message": str(exc)[:500]})
                state.classification = CapabilityRunClassification.POLICY_VIOLATION
                state.transition(CapabilityRunStatus.POLICY_BLOCKED, "plan_generation_rejected")
                self.store.save_state(state); raise
        state.usage.input_tokens += generated.input_tokens
        state.usage.output_tokens += generated.output_tokens
        state.usage.estimated_cost_brl = round(state.usage.estimated_cost_brl + generated.estimated_cost_brl, 8)
        state.usage.elapsed_ms += max(0, round((monotonic() - started) * 1000))
        state.facts["generation"] = {
            "provider": generated.provider, "model": generated.model, "response_id": generated.response_id,
            "requirement_sha256": hashlib.sha256(requirement.encode()).hexdigest(),
        }
        if (state.usage.input_tokens > state.budgets.max_input_tokens or state.usage.output_tokens > state.budgets.max_output_tokens or state.usage.estimated_cost_brl > state.budgets.api_budget_brl):
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "generation_budget_exhausted")
        else:
            state.classification = CapabilityRunClassification.PLAN_READY_FOR_REVIEW
            state.transition(CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW, "plan_ready_for_review")
        self.store.save_java_plan(state, generated.plan); self.store.save_state(state)
        return JavaUnitPlanRunOutput(state, generated.plan)


class ExecuteJavaUnitPlanService:
    def __init__(self, store: CapabilityRunStore,
                 executor_factory: Callable[[object], DockerJavaUnitExecutor] | None = None) -> None:
        self.store = store
        self.executor_factory = executor_factory or (lambda root: DockerJavaUnitExecutor(root))

    def execute(self, run_id: str) -> JavaUnitExecutionRunOutput:
        state = self.store.load_state(run_id)
        if state.status is not CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW:
            raise CapabilityRunContractError("Java unit run must be waiting for human review")
        plan = self.store.load_java_plan(state)
        if state.usage.requests + len(plan.scenarios) > state.budgets.max_requests:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "scenario_budget_exhausted")
            self.store.save_state(state); return JavaUnitExecutionRunOutput(state, None)
        state.transition(CapabilityRunStatus.EXECUTING, "human_review_approved"); self.store.save_state(state)
        sandbox = self.store.run_dir(run_id) / "java-unit-sandbox"; sandbox.mkdir(exist_ok=False)
        workspace, output = DockerJavaUnitExecutor.stage(plan, sandbox)
        started = monotonic()
        try:
            result = self.executor_factory(sandbox).execute(workspace, output)
            self.store.save_java_result(state, result)
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)
        state.usage.elapsed_ms += max(0, round((monotonic() - started) * 1000))
        state.usage.requests += result.tests or 0
        if state.usage.elapsed_ms > state.budgets.max_workflow_seconds * 1000:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "workflow_time_budget_exhausted")
        elif result.outcome is TestExecutionOutcome.PASSED:
            state.classification = CapabilityRunClassification.ACCEPTED
            state.transition(CapabilityRunStatus.SUCCEEDED, "java_unit_assertions_passed")
        elif result.outcome is TestExecutionOutcome.ASSERTION_FAILURE:
            state.classification = CapabilityRunClassification.FUNCTIONAL_FAILURE
            state.transition(CapabilityRunStatus.FAILED, "java_unit_assertions_failed")
        else:
            state.classification = CapabilityRunClassification.INFRASTRUCTURE_ERROR
            state.transition(CapabilityRunStatus.FAILED, "java_unit_execution_error")
        state.facts["execution"] = {
            "outcome": result.outcome.value, "tests": result.tests, "passed": result.passed,
            "compiled_artifact_sha256": JavaUnitTestCompiler.compile(plan).sha256, "network_scope": "none",
        }
        self.store.save_state(state)
        return JavaUnitExecutionRunOutput(state, result)
