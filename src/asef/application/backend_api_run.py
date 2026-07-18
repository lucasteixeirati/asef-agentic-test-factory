from __future__ import annotations

from dataclasses import dataclass
import hashlib
from time import monotonic

from ..adapters.api_plan_agent import ApiPlanAgentAdapter
from ..adapters.api_report_store import ApiReportPaths, ApiReportStore
from ..adapters.capability_run_store import CapabilityRunStore
from ..adapters.http_api_execution import LoopbackHttpApiExecutor
from ..adapters.gateway import GatewayError, InvalidStructuredOutput
from ..api_contracts import ApiExecutionResult, ApiTestPlan
from ..capability_runs import (
    CapabilityRunBudgets,
    CapabilityRunClassification,
    CapabilityRunContractError,
    CapabilityRunState,
    CapabilityRunStatus,
)
from ..skills.backend_api import BackendApiSkill
from ..openapi_contracts import OpenApiSummary
from .ports import ProviderPermanentError, ProviderTransientError


@dataclass(slots=True, frozen=True)
class ApiPlanRunOutput:
    state: CapabilityRunState
    plan: ApiTestPlan | None


@dataclass(slots=True, frozen=True)
class ApiExecutionRunOutput:
    state: CapabilityRunState
    result: ApiExecutionResult | None
    reports: ApiReportPaths | None


class GenerateBackendApiPlanService:
    def __init__(self, agent: ApiPlanAgentAdapter, store: CapabilityRunStore) -> None:
        self.agent = agent
        self.store = store

    def execute(
        self,
        requirement: str,
        base_url: str,
        budgets: CapabilityRunBudgets | None = None,
        openapi: OpenApiSummary | None = None,
    ) -> ApiPlanRunOutput:
        state = CapabilityRunState(
            workflow_id="WF-API-001",
            skill_id="backend-api",
            language_profile="python-pytest",
            budgets=budgets or CapabilityRunBudgets(),
        )
        self.store.create(state)
        state.transition(CapabilityRunStatus.GENERATING_PLAN, "plan_generation_started")
        self.store.save_state(state)
        generated = None
        while generated is None:
            if state.usage.model_calls >= state.budgets.max_model_calls:
                state.classification = CapabilityRunClassification.BUDGET_ERROR
                state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "model_call_budget_exhausted")
                self.store.save_state(state)
                return ApiPlanRunOutput(state, None)
            state.usage.model_calls += 1
            self.store.save_state(state)
            started = monotonic()
            try:
                generated = self.agent.generate(requirement, base_url, openapi)
            except ProviderTransientError as exc:
                self._record_exception_usage(state, exc, started)
                state.errors.append({"type": type(exc).__name__, "message": str(exc)[:500]})
                if self._budget_exceeded(state):
                    state.classification = CapabilityRunClassification.BUDGET_ERROR
                    state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "provider_failure_budget_exhausted")
                    self.store.save_state(state)
                    raise
                if state.usage.provider_retries >= state.budgets.max_provider_retries:
                    state.classification = CapabilityRunClassification.INFRASTRUCTURE_ERROR
                    state.transition(CapabilityRunStatus.FAILED, "provider_retry_budget_exhausted")
                    self.store.save_state(state)
                    raise
                state.usage.provider_retries += 1
                self.store.save_state(state)
            except (ProviderPermanentError, InvalidStructuredOutput, GatewayError) as exc:
                self._record_exception_usage(state, exc, started)
                state.errors.append({"type": type(exc).__name__, "message": str(exc)[:500]})
                state.classification = CapabilityRunClassification.INFRASTRUCTURE_ERROR
                state.transition(CapabilityRunStatus.FAILED, "provider_generation_failed")
                self.store.save_state(state)
                raise
            except Exception as exc:
                self._record_exception_usage(state, exc, started)
                state.errors.append({"type": type(exc).__name__, "message": str(exc)[:500]})
                state.classification = CapabilityRunClassification.POLICY_VIOLATION
                state.transition(CapabilityRunStatus.POLICY_BLOCKED, "plan_generation_rejected")
                self.store.save_state(state)
                raise
        state.usage.input_tokens += generated.input_tokens
        state.usage.output_tokens += generated.output_tokens
        state.usage.elapsed_ms += max(0, round((monotonic() - started) * 1_000))
        state.usage.estimated_cost_brl = round(
            state.usage.estimated_cost_brl + generated.estimated_cost_brl,
            8,
        )
        state.facts["generation"] = {
            "provider": generated.provider,
            "model": generated.model,
            "response_id": generated.response_id,
            "requirement_sha256": hashlib.sha256(requirement.encode("utf-8")).hexdigest(),
            "estimated_cost_brl": generated.estimated_cost_brl,
            "openapi_sha256": generated.openapi_sha256,
        }
        exceeded = self._budget_exceeded(state)
        if exceeded:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "generation_budget_exhausted")
        self.store.save_plan(state, generated.plan)
        if openapi is not None:
            self.store.save_openapi_summary(state, openapi)
        if exceeded:
            return ApiPlanRunOutput(state, generated.plan)
        state.classification = CapabilityRunClassification.PLAN_READY_FOR_REVIEW
        state.transition(CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW, "plan_ready_for_review")
        self.store.save_state(state)
        return ApiPlanRunOutput(state, generated.plan)

    @staticmethod
    def _budget_exceeded(state: CapabilityRunState) -> bool:
        return (
            state.usage.model_calls > state.budgets.max_model_calls
            or state.usage.provider_retries > state.budgets.max_provider_retries
            or state.usage.input_tokens > state.budgets.max_input_tokens
            or state.usage.output_tokens > state.budgets.max_output_tokens
            or state.usage.elapsed_ms > state.budgets.max_workflow_seconds * 1_000
            or state.usage.estimated_cost_brl > state.budgets.api_budget_brl
        )

    def _record_exception_usage(self, state: CapabilityRunState, exc: Exception, started: float) -> None:
        input_tokens = max(0, int(getattr(exc, "input_tokens", 0)))
        output_tokens = max(0, int(getattr(exc, "output_tokens", 0)))
        state.usage.input_tokens += input_tokens
        state.usage.output_tokens += output_tokens
        state.usage.elapsed_ms += max(0, round((monotonic() - started) * 1_000))
        state.usage.estimated_cost_brl = round(
            state.usage.estimated_cost_brl + self.agent.pricing.estimate(input_tokens, output_tokens),
            8,
        )


class ExecuteBackendApiPlanService:
    def __init__(
        self,
        executor: LoopbackHttpApiExecutor,
        store: CapabilityRunStore,
        reports: ApiReportStore,
        *,
        asef_version: str,
    ) -> None:
        self.executor = executor
        self.store = store
        self.reports = reports
        self.asef_version = asef_version

    def execute(self, run_id: str) -> ApiExecutionRunOutput:
        state = self.store.load_state(run_id)
        if state.status is not CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW:
            raise CapabilityRunContractError("API run must be waiting for human review before execution")
        plan = self.store.load_plan(state)
        if state.usage.requests + len(plan.scenarios) > state.budgets.max_requests:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "request_budget_exhausted")
            self.store.save_state(state)
            return ApiExecutionRunOutput(state, None, None)
        state.transition(CapabilityRunStatus.EXECUTING, "human_review_approved")
        self.store.save_state(state)
        started = monotonic()
        result = self.executor.execute(plan)
        state.usage.elapsed_ms += max(0, round((monotonic() - started) * 1_000))
        state.usage.requests += result.tests
        if state.usage.elapsed_ms > state.budgets.max_workflow_seconds * 1_000:
            state.classification = CapabilityRunClassification.BUDGET_ERROR
            state.transition(CapabilityRunStatus.BUDGET_EXHAUSTED, "workflow_time_budget_exhausted")
        elif result.status == "PASSED":
            state.classification = CapabilityRunClassification.ACCEPTED
            state.transition(CapabilityRunStatus.SUCCEEDED, "API_assertions_passed")
        elif result.status == "FAILED":
            state.classification = CapabilityRunClassification.FUNCTIONAL_FAILURE
            state.transition(CapabilityRunStatus.FAILED, "API_assertions_failed")
        else:
            state.classification = CapabilityRunClassification.INFRASTRUCTURE_ERROR
            state.transition(CapabilityRunStatus.FAILED, "API_execution_error")
        self.store.save_result(state, result)
        paths = self.reports.save(
            self.store.run_dir(run_id) / "reports",
            result,
            asef_version=self.asef_version,
            run_id=state.run_id,
            classification=state.classification.value,
            generation_mode=(
                "recorded-natural-language"
                if "generation" in state.facts
                else "supplied-plan"
            ),
        )
        self.store.register_evidence(state, "api_report_json", paths.report_json)
        self.store.register_evidence(state, "api_report_markdown", paths.report_markdown)
        state.facts["execution"] = {
            "result": result.status,
            "tests": result.tests,
            "passed": result.passed,
            "failed": result.failed,
            "errors": result.errors,
            "network_scope": "loopback-only",
        }
        self.store.save_state(state)
        return ApiExecutionRunOutput(state, result, paths)


class RegisterBackendApiPlanService:
    """Persist an operator-supplied plan before the explicit execution command."""

    def __init__(self, skill: BackendApiSkill, store: CapabilityRunStore) -> None:
        self.skill = skill
        self.store = store

    def execute(
        self,
        plan: ApiTestPlan,
        budgets: CapabilityRunBudgets | None = None,
    ) -> ApiPlanRunOutput:
        state = CapabilityRunState(
            workflow_id="WF-API-001",
            skill_id="backend-api",
            language_profile="python-pytest",
            budgets=budgets or CapabilityRunBudgets(max_model_calls=0),
        )
        self.store.create(state)
        try:
            self.skill.validate(plan)
        except Exception as exc:
            state.errors.append({"type": type(exc).__name__, "message": str(exc)[:500]})
            state.classification = CapabilityRunClassification.POLICY_VIOLATION
            state.transition(CapabilityRunStatus.POLICY_BLOCKED, "supplied_plan_rejected")
            self.store.save_state(state)
            raise
        self.store.save_plan(state, plan)
        state.classification = CapabilityRunClassification.PLAN_READY_FOR_REVIEW
        state.transition(CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW, "supplied_plan_registered")
        self.store.save_state(state)
        return ApiPlanRunOutput(state, plan)
