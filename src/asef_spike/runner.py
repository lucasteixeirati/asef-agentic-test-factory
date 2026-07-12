from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .budgets import BudgetController, BudgetExceeded
from .domain import RunState, RunStatus, WorkflowRequest
from .events import Event, JsonlEventSink
from .gateway import InvalidStructuredOutput, ModelGateway
from .state_machine import WorkflowMachine


RISK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "behaviors": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "scenarios": {"type": "array", "items": {"type": "string"}},
        "clarification_required": {"type": "boolean"},
    },
    "required": ["behaviors", "risks", "scenarios", "clarification_required"],
}


class AnalysisValidationError(ValueError):
    pass


def validate_analysis_output(value: dict[str, Any]) -> dict[str, Any]:
    expected = {"behaviors", "risks", "scenarios", "clarification_required"}
    if set(value) != expected:
        raise AnalysisValidationError(
            f"analysis keys must be exactly {sorted(expected)}, got {sorted(value)}"
        )
    for field in ("behaviors", "risks", "scenarios"):
        items = value[field]
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            raise AnalysisValidationError(f"{field} must be a list of strings")
    if not isinstance(value["clarification_required"], bool):
        raise AnalysisValidationError("clarification_required must be boolean")
    return value


class DemoWorkflowRunner:
    """Executes a thin vertical slice while keeping transitions explicit."""

    def __init__(
        self,
        gateway: ModelGateway,
        output_root: Path,
        budget_controller: BudgetController,
    ) -> None:
        self.gateway = gateway
        self.output_root = output_root
        self.budget_controller = budget_controller

    def run(self, request: WorkflowRequest) -> RunState:
        state = RunState(
            request=request,
            budgets=self.budget_controller.limits,
            usage=self.budget_controller.usage,
        )
        machine = WorkflowMachine(state)
        run_dir = self.output_root / state.run_id
        event_sink = JsonlEventSink(run_dir / "events.jsonl")

        def move(target: RunStatus, reason: str) -> None:
            source = state.status
            machine.transition(target, reason)
            event_sink.append(
                Event(
                    run_id=state.run_id,
                    event_type="state.transition",
                    status=state.status.value,
                    payload={"source": source.value, "target": target.value, "reason": reason},
                )
            )

        move(RunStatus.VALIDATING_INPUT, "start")
        errors = request.validate()
        if errors:
            state.errors.extend({"type": "INPUT_ERROR", "message": item} for item in errors)
            move(RunStatus.FAILED, "input_invalid")
            self._write_run(run_dir, state)
            return state

        move(RunStatus.INSPECTING_SUT, "input_valid")
        state.facts["sut"] = {"entrypoint": request.sut_entrypoint, "profile": request.language_profile}
        move(RunStatus.ANALYZING_REQUIREMENT, "sut_supported")

        prompt = (
            "Analyze this software requirement for test design. Return behaviors, risks, scenarios, "
            "and whether clarification is required.\n\n"
            f"Title: {request.requirement_title}\n"
            f"Description: {request.requirement_description}\n"
            f"SUT entrypoint: {request.sut_entrypoint}"
        )
        while True:
            try:
                result = self.gateway.generate(
                    prompt=prompt,
                    schema=RISK_SCHEMA,
                    schema_name="wf001_analysis",
                )
            except InvalidStructuredOutput as exc:
                if not self._reserve_provider_recovery(state, machine, event_sink, run_dir, exc):
                    return state
                prompt = self._repair_prompt(exc)
                continue
            except BudgetExceeded as exc:
                state.errors.append(
                    {"type": "BUDGET_EXCEEDED", "budget": exc.budget, "message": str(exc)}
                )
                move(RunStatus.BUDGET_EXHAUSTED, "provider_budget_exhausted")
                self._write_run(run_dir, state)
                return state

            try:
                analysis = validate_analysis_output(result.output)
                break
            except AnalysisValidationError as exc:
                attempt = state.usage.provider_retries + 1
                state.errors.append(
                    {
                        "type": "PROVIDER_OUTPUT_INVALID",
                        "attempt": attempt,
                        "message": str(exc),
                    }
                )
                if not self._reserve_provider_recovery(
                    state, machine, event_sink, run_dir, exc, error_already_recorded=True
                ):
                    return state
                prompt = self._repair_prompt(exc)

        state.facts["analysis"] = analysis
        state.facts["model"] = {
            "id": result.model,
            "response_id": result.response_id,
            "recorded": result.recorded,
        }

        if bool(result.output["clarification_required"]):
            move(RunStatus.WAITING_FOR_CLARIFICATION, "clarification_required")
            self._write_run(run_dir, state)
            return state

        move(RunStatus.ANALYZING_RISK, "analysis_complete")
        move(RunStatus.DESIGNING_SCENARIOS, "risks_ready")
        move(RunStatus.REVIEWING_TEST_DESIGN, "design_ready")
        move(RunStatus.GENERATING_TESTS, "design_accepted")
        state.facts["spike_scope"] = "test generation is intentionally stubbed"
        move(RunStatus.STATIC_VALIDATION, "tests_generated")
        move(RunStatus.EXECUTING_TESTS, "static_validation_passed")
        state.facts["execution"] = {"status": "simulated", "tests": 1, "passed": 1}
        move(RunStatus.EVALUATING_EVIDENCE, "execution_complete")
        move(RunStatus.GENERATING_REPORT, "evaluation_complete")
        move(RunStatus.SUCCEEDED, "success_reported")
        self._write_run(run_dir, state)
        return state

    @staticmethod
    def _write_run(run_dir: Path, state: RunState) -> None:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "state.json").write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        manifest = {
            "schema_version": "1.0.0",
            "run_id": state.run_id,
            "workflow_id": state.workflow_id,
            "workflow_version": state.workflow_version,
            "status": state.status.value,
            "request": asdict(state.request),
            "usage": asdict(state.usage),
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _repair_prompt(exc: Exception) -> str:
        return (
            "Your previous response failed local schema validation. Return a corrected response "
            "with exactly these fields: behaviors, risks, scenarios, clarification_required. "
            "The first three fields must be arrays of strings and clarification_required must be "
            f"a boolean. Validation error: {str(exc)[:500]}"
        )

    def _reserve_provider_recovery(
        self,
        state: RunState,
        machine: WorkflowMachine,
        event_sink: JsonlEventSink,
        run_dir: Path,
        exc: Exception,
        *,
        error_already_recorded: bool = False,
    ) -> bool:
        if not error_already_recorded:
            state.errors.append(
                {
                    "type": "PROVIDER_OUTPUT_INVALID",
                    "attempt": state.usage.provider_retries + 1,
                    "message": str(exc),
                }
            )
        try:
            self.budget_controller.reserve_provider_retry()
            return True
        except BudgetExceeded as budget_exc:
            state.errors.append(
                {
                    "type": "BUDGET_EXCEEDED",
                    "budget": budget_exc.budget,
                    "message": str(budget_exc),
                }
            )
            source = state.status
            machine.transition(RunStatus.BUDGET_EXHAUSTED, "provider_retry_budget_exhausted")
            event_sink.append(
                Event(
                    run_id=state.run_id,
                    event_type="state.transition",
                    status=state.status.value,
                    payload={
                        "source": source.value,
                        "target": RunStatus.BUDGET_EXHAUSTED.value,
                        "reason": "provider_retry_budget_exhausted",
                    },
                )
            )
            self._write_run(run_dir, state)
            return False
