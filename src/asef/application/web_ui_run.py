from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from time import monotonic
from typing import Callable

from ..adapters.capability_run_store import CapabilityRunStore
from ..adapters.web_ui_execution import DockerWebUiExecutor
from ..adapters.web_ui_plan_agent import WebUiPlanAgentAdapter
from ..adapters.web_ui_compiler import WebUiPlanCompiler
from ..capability_runs import (
    CapabilityRunBudgets, CapabilityRunClassification, CapabilityRunContractError,
    CapabilityRunState, CapabilityRunStatus,
)
from ..web_ui_contracts import WebUiExecutionResult, WebUiTestPlan
from .ports import ProviderTransientError


@dataclass(slots=True, frozen=True)
class WebUiPlanRunOutput:
    state: CapabilityRunState
    plan: WebUiTestPlan | None


@dataclass(slots=True, frozen=True)
class WebUiExecutionRunOutput:
    state: CapabilityRunState
    result: WebUiExecutionResult | None


class GenerateWebUiPlanService:
    def __init__(self, agent: WebUiPlanAgentAdapter, store: CapabilityRunStore) -> None:
        self.agent, self.store = agent, store

    def execute(self, requirement: str, base_url: str, budgets: CapabilityRunBudgets | None = None) -> WebUiPlanRunOutput:
        state = CapabilityRunState("WF-WEB-001", "web-ui", "node-typescript", budgets=budgets or CapabilityRunBudgets())
        self.store.create(state)
        state.transition(CapabilityRunStatus.GENERATING_PLAN, "plan_generation_started")
        self.store.save_state(state)
        if state.budgets.max_model_calls < 1:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "model_call_budget_exhausted")
            self.store.save_state(state)
            return WebUiPlanRunOutput(state, None)
        generated = None
        started = monotonic()
        while generated is None:
            state.usage.model_calls += 1
            self.store.save_state(state)
            try:
                generated = self.agent.generate(requirement, base_url)
            except ProviderTransientError as exc:
                state.errors.append({"type": type(exc).__name__, "message": str(exc)[:500]})
                if (state.usage.provider_retries >= state.budgets.max_provider_retries
                        or state.usage.model_calls >= state.budgets.max_model_calls):
                    state.classification = CapabilityRunClassification.INFRASTRUCTURE_ERROR
                    state.transition(CapabilityRunStatus.FAILED, "provider_retry_budget_exhausted")
                    self.store.save_state(state)
                    raise
                state.usage.provider_retries += 1
                self.store.save_state(state)
            except Exception as exc:
                state.usage.input_tokens += max(0, int(getattr(exc, "input_tokens", 0)))
                state.usage.output_tokens += max(0, int(getattr(exc, "output_tokens", 0)))
                state.errors.append({"type": type(exc).__name__, "message": str(exc)[:500]})
                state.classification = CapabilityRunClassification.POLICY_VIOLATION
                state.transition(CapabilityRunStatus.POLICY_BLOCKED, "plan_generation_rejected")
                self.store.save_state(state)
                raise
        state.usage.input_tokens += generated.input_tokens
        state.usage.output_tokens += generated.output_tokens
        state.usage.estimated_cost_brl = round(
            state.usage.estimated_cost_brl + generated.estimated_cost_brl, 8
        )
        state.usage.elapsed_ms += max(0, round((monotonic() - started) * 1000))
        state.facts["generation"] = {
            "provider": generated.provider, "model": generated.model,
            "response_id": generated.response_id,
            "requirement_sha256": hashlib.sha256(requirement.encode()).hexdigest(),
        }
        exceeded = (state.usage.input_tokens > state.budgets.max_input_tokens
                    or state.usage.output_tokens > state.budgets.max_output_tokens
                    or state.usage.estimated_cost_brl > state.budgets.api_budget_brl)
        if exceeded:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "generation_budget_exhausted")
        else:
            state.classification = CapabilityRunClassification.PLAN_READY_FOR_REVIEW
            state.transition(CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW, "plan_ready_for_review")
        self.store.save_web_plan(state, generated.plan)
        self.store.save_state(state)
        return WebUiPlanRunOutput(state, generated.plan)


class ExecuteWebUiPlanService:
    def __init__(
        self,
        store: CapabilityRunStore,
        executor_factory: Callable[[object], DockerWebUiExecutor] | None = None,
    ) -> None:
        self.store = store
        self.executor_factory = executor_factory or (lambda root: DockerWebUiExecutor(root))

    def execute(self, run_id: str) -> WebUiExecutionRunOutput:
        state = self.store.load_state(run_id)
        if state.status is not CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW:
            raise CapabilityRunContractError("Web UI run must be waiting for human review")
        plan = self.store.load_web_plan(state)
        if state.usage.requests + len(plan.scenarios) > state.budgets.max_requests:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "scenario_budget_exhausted")
            self.store.save_state(state)
            return WebUiExecutionRunOutput(state, None)
        state.transition(CapabilityRunStatus.EXECUTING, "human_review_approved")
        self.store.save_state(state)
        sandbox = self.store.run_dir(run_id) / "web-ui-sandbox"
        sandbox.mkdir(exist_ok=False)
        workspace, output = DockerWebUiExecutor.stage(plan, sandbox)
        started = monotonic()
        try:
            result = self.executor_factory(sandbox).execute(workspace, output)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)
        state.usage.elapsed_ms += max(0, round((monotonic() - started) * 1000))
        state.usage.requests += result.tests
        if state.usage.elapsed_ms > state.budgets.max_workflow_seconds * 1000:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "workflow_time_budget_exhausted")
        elif result.status == "PASSED":
            state.classification = CapabilityRunClassification.ACCEPTED
            state.transition(CapabilityRunStatus.SUCCEEDED, "web_ui_assertions_passed")
        elif result.status == "FAILED":
            state.classification = CapabilityRunClassification.FUNCTIONAL_FAILURE
            state.transition(CapabilityRunStatus.FAILED, "web_ui_assertions_failed")
        elif result.status == "POLICY_BLOCKED":
            state.classification = CapabilityRunClassification.POLICY_VIOLATION
            state.transition(CapabilityRunStatus.POLICY_BLOCKED, "web_ui_policy_blocked")
        else:
            state.classification = CapabilityRunClassification.INFRASTRUCTURE_ERROR
            state.transition(CapabilityRunStatus.FAILED, "web_ui_execution_error")
        self.store.save_web_result(state, result)
        for scenario in result.scenarios:
            if scenario.screenshot_ref:
                self.store.register_evidence(state, "web_ui_private_screenshot", output / scenario.screenshot_ref)
        state.facts["execution"] = {
            "result": result.status, "tests": result.tests, "passed": result.passed,
            "compiled_artifact_sha256": WebUiPlanCompiler.compile(plan).sha256,
            "network_scope": "container-none-loopback-fixture",
        }
        self.store.save_state(state)
        return WebUiExecutionRunOutput(state, result)
