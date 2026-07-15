from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..contracts import EvidenceRef, SkeletonRunRequest, SkeletonRunState, UnitTestArtifact
from ..outcomes import RunClassification, RunStatus
from ..skills.unit import UnitSkill, UnitSkillPolicyError
from .ports import (
    AgenticTestPort,
    AnalysisResult,
    HumanCheckpointPort,
    InvalidAgentOutputError,
    ProviderPermanentError,
    ProviderEvidenceError,
    ProviderRefusalError,
    ProviderTransientError,
    ResolvedQualityContext,
    RunStorePort,
    WorkspacePort,
    WorkspaceResult,
)
from .prepare_run import PrepareRunResult, PrepareRunService


@dataclass(slots=True, frozen=True)
class GenerateUnitResult:
    state: SkeletonRunState
    run_dir: Path
    context: ResolvedQualityContext
    artifact: UnitTestArtifact | None = None
    workspace: WorkspaceResult | None = None


class GenerateUnitTestService:
    """Continue a freshly prepared run through deterministic static validation."""

    def __init__(
        self,
        prepare_service: PrepareRunService,
        agent: AgenticTestPort,
        skill: UnitSkill,
        workspace: WorkspacePort,
        run_store: RunStorePort,
        checkpoint: HumanCheckpointPort | None = None,
    ) -> None:
        self.prepare_service = prepare_service
        self.agent = agent
        self.skill = skill
        self.workspace = workspace
        self.run_store = run_store
        self.checkpoint = checkpoint

    def execute(self, request: SkeletonRunRequest) -> GenerateUnitResult:
        prepared = self.prepare_service.execute(request)
        state = prepared.state
        expected_provider = getattr(self.agent, "provider_id", "recorded")
        if prepared.context.snapshot.provider != expected_provider:
            message = (
                f"context provider {prepared.context.snapshot.provider} "
                f"does not match adapter {expected_provider}"
            )
            state.errors.append({"type": "PROVIDER_POLICY_MISMATCH", "message": message})
            state.classification = RunClassification.POLICY_VIOLATION
            PrepareRunService._move(state, RunStatus.POLICY_BLOCKED, "provider_policy_mismatch")
            self.run_store.save_state(state)
            return GenerateUnitResult(state, prepared.run_dir, prepared.context)
        bind_context = getattr(self.agent, "bind_context", None)
        if bind_context is not None:
            try:
                bind_context(prepared.context)
            except (OSError, ValueError) as exc:
                state.errors.append({"type": "SOURCE_CONTEXT_POLICY", "message": str(exc)[:500]})
                state.classification = RunClassification.POLICY_VIOLATION
                PrepareRunService._move(state, RunStatus.POLICY_BLOCKED, "source_context_policy_blocked")
                self.run_store.save_state(state)
                return GenerateUnitResult(state, prepared.run_dir, prepared.context)
        validate_request = getattr(self.agent, "validate_request", None)
        if validate_request is not None:
            try:
                validate_request(request)
            except ValueError as exc:
                state.errors.append({"type": "PROVIDER_INPUT_POLICY", "message": str(exc)[:500]})
                state.classification = RunClassification.POLICY_VIOLATION
                PrepareRunService._move(state, RunStatus.POLICY_BLOCKED, "provider_input_policy_blocked")
                self.run_store.save_state(state)
                return GenerateUnitResult(state, prepared.run_dir, prepared.context)
        analysis = self._analyze_with_recovery(state)
        if analysis is None:
            return GenerateUnitResult(state, prepared.run_dir, prepared.context)
        if not self._record_usage(state, analysis, "analysis"):
            return GenerateUnitResult(state, prepared.run_dir, prepared.context)
        state.facts["analysis"] = {
            "behaviors": list(analysis.behaviors),
            "risks": list(analysis.risks),
            "scenarios": list(analysis.scenarios),
            "model": analysis.model,
            "response_id": analysis.response_id,
            "provider": analysis.provider,
            "recorded": analysis.provider == "recorded",
        }
        if analysis.clarification_required:
            PrepareRunService._move(
                state, RunStatus.WAITING_FOR_CLARIFICATION, "recorded_analysis_requires_clarification"
            )
            state.classification = RunClassification.WAITING_HUMAN
            if self.checkpoint is not None:
                payload: dict[str, object] = {
                    "schema_version": "1.0.0",
                    "checkpoint_kind": "requirement_clarification",
                    "analysis": {
                        "behaviors": list(analysis.behaviors),
                        "risks": list(analysis.risks),
                        "scenarios": list(analysis.scenarios),
                        "model": analysis.model,
                        "response_id": analysis.response_id,
                    },
                }
                self.checkpoint.pause(
                    state.run_id,
                    prepared.run_dir / "checkpoint.sqlite",
                    payload,
                )
                state.facts["human_checkpoint"] = {
                    "kind": "requirement_clarification",
                    "ref": "checkpoint.sqlite",
                }
            self.run_store.save_state(state)
            return GenerateUnitResult(state, prepared.run_dir, prepared.context)

        return self.continue_after_analysis(prepared, analysis)

    def continue_after_analysis(
        self,
        prepared: PrepareRunResult,
        analysis: AnalysisResult,
    ) -> GenerateUnitResult:
        state = prepared.state

        PrepareRunService._move(state, RunStatus.ANALYZING_RISK, "analysis_complete")
        PrepareRunService._move(state, RunStatus.DESIGNING_SCENARIOS, "risks_identified")
        state.facts["test_design"] = {
            "scenario_ids": [f"SCN-{index:03d}" for index, _ in enumerate(analysis.scenarios, 1)],
            "scenario_count": len(analysis.scenarios),
        }
        PrepareRunService._move(state, RunStatus.GENERATING_TESTS, "design_ready")
        generated = self._generate_with_recovery(state, analysis)
        if generated is None:
            return GenerateUnitResult(state, prepared.run_dir, prepared.context)
        if not self._record_usage(state, generated, "generation"):
            return GenerateUnitResult(state, prepared.run_dir, prepared.context)
        artifact = generated.artifact
        state.attempts["test_generation"] = 1

        try:
            expected_scenarios = set(state.facts["test_design"]["scenario_ids"])
            if set(artifact.scenario_ids) != expected_scenarios:
                raise UnitSkillPolicyError(
                    "artifact scenario_ids must exactly match the approved test design"
                )
            validation = self.skill.validate(artifact)
        except UnitSkillPolicyError as exc:
            validation = {
                "schema_version": "1.0.0",
                "status": "POLICY_BLOCKED",
                "skill_id": "unit",
                "message": str(exc),
                "artifact_sha256": artifact.content_sha256,
            }
            state.errors.append({"type": "POLICY_VIOLATION", "message": str(exc)})
            state.classification = RunClassification.POLICY_VIOLATION
            PrepareRunService._move(state, RunStatus.POLICY_BLOCKED, "unit_skill_policy_violation")
            self.run_store.save_static_validation(state, artifact, validation)
            return GenerateUnitResult(state, prepared.run_dir, prepared.context, artifact)

        PrepareRunService._move(state, RunStatus.STATIC_VALIDATION, "artifact_policy_passed")
        workspace = self.workspace.stage(prepared.run_dir, prepared.context, artifact)
        artifact_ref = f"artifacts/attempt-{artifact.attempt:03d}/{artifact.relative_path}"
        state.evidence_refs.append(
            EvidenceRef(kind="unit_test_artifact", relative_path=artifact_ref, sha256=artifact.content_sha256)
        )
        state.facts["artifact"] = {
            "relative_path": artifact_ref,
            "sha256": artifact.content_sha256,
            "scenario_ids": list(artifact.scenario_ids),
            "model": generated.model,
            "response_id": generated.response_id,
        }
        state.facts["workspace"] = {
            "ref": "workspace",
            "copied_files": list(workspace.copied_files),
            "generated_file": workspace.generated_file,
            "sut_original_modified": False,
        }
        state.validate()
        self.run_store.save_static_validation(state, artifact, validation)
        return GenerateUnitResult(state, prepared.run_dir, prepared.context, artifact, workspace)

    def _record_usage(self, state: SkeletonRunState, result, operation: str) -> bool:
        state.usage.input_tokens += max(0, result.input_tokens)
        state.usage.output_tokens += max(0, result.output_tokens)
        state.usage.elapsed_ms += max(0, result.latency_ms)
        state.usage.estimated_cost_brl = round(
            state.usage.estimated_cost_brl + max(0.0, result.estimated_cost_brl), 8
        )
        state.facts.setdefault("provider_calls", []).append(
            {
                "provider": result.provider,
                "model": result.model,
                "response_id": result.response_id,
                "input_tokens": max(0, result.input_tokens),
                "output_tokens": max(0, result.output_tokens),
                "latency_ms": max(0, result.latency_ms),
                "estimated_cost_brl": max(0.0, result.estimated_cost_brl),
                "operation": operation,
            }
        )
        exceeded = (
            state.usage.input_tokens > state.budgets.max_input_tokens
            or state.usage.output_tokens > state.budgets.max_output_tokens
            or state.usage.elapsed_ms > state.budgets.max_workflow_seconds * 1_000
            or state.usage.estimated_cost_brl > state.budgets.api_budget_brl
        )
        if exceeded:
            state.classification = RunClassification.BUDGET_ERROR
            PrepareRunService._move(state, RunStatus.BUDGET_EXHAUSTED, "provider_usage_budget_exhausted")
        state.validate()
        self.run_store.save_state(state)
        return not exceeded

    def _reserve_model_call(self, state: SkeletonRunState) -> bool:
        exhausted = (
            state.usage.model_calls >= state.budgets.max_model_calls
            or state.usage.input_tokens >= state.budgets.max_input_tokens
            or state.usage.output_tokens >= state.budgets.max_output_tokens
            or state.usage.elapsed_ms >= state.budgets.max_workflow_seconds * 1_000
            or (
                state.request.execution_mode == "live"
                and state.usage.estimated_cost_brl >= state.budgets.api_budget_brl
            )
        )
        if exhausted:
            state.classification = RunClassification.BUDGET_ERROR
            PrepareRunService._move(state, RunStatus.BUDGET_EXHAUSTED, "model_call_budget_exhausted")
            self.run_store.save_state(state)
            return False
        state.usage.model_calls += 1
        state.validate()
        self.run_store.save_state(state)
        return True

    def _analyze_with_recovery(self, state: SkeletonRunState) -> AnalysisResult | None:
        while self._reserve_model_call(state):
            try:
                return self.agent.analyze(state.request)
            except InvalidAgentOutputError as exc:
                if not self._retry_or_stop(state, exc, invalid_output=True, operation="analysis"):
                    return None
            except ProviderTransientError as exc:
                if not self._retry_or_stop(state, exc, invalid_output=False, operation="analysis"):
                    return None
            except ProviderPermanentError as exc:
                self._provider_failed(state, exc, operation="analysis")
                return None
        return None

    def _generate_with_recovery(
        self,
        state: SkeletonRunState,
        analysis: AnalysisResult,
    ):
        while True:
            if not self._reserve_model_call(state):
                return None
            try:
                return self.agent.generate(state.request, analysis)
            except InvalidAgentOutputError as exc:
                if not self._retry_or_stop(state, exc, invalid_output=True, operation="generation"):
                    return None
            except ProviderTransientError as exc:
                if not self._retry_or_stop(state, exc, invalid_output=False, operation="generation"):
                    return None
            except ProviderPermanentError as exc:
                self._provider_failed(state, exc, operation="generation")
                return None

    def _retry_or_stop(
        self,
        state: SkeletonRunState,
        exc: Exception,
        *,
        invalid_output: bool,
        operation: str,
    ) -> bool:
        if getattr(exc, "usage_observed", False) and not self._record_usage(
            state, exc, operation
        ):
            return False
        state.errors.append(
            {
                "type": "PROVIDER_OUTPUT_INVALID" if invalid_output else "PROVIDER_TRANSIENT_ERROR",
                "attempt": state.usage.provider_retries + 1,
                "message": str(exc)[:500],
            }
        )
        if state.usage.provider_retries >= state.budgets.max_provider_retries:
            if invalid_output:
                state.classification = RunClassification.BUDGET_ERROR
                PrepareRunService._move(
                    state, RunStatus.BUDGET_EXHAUSTED, "invalid_output_retry_budget_exhausted"
                )
            else:
                self._provider_failed(
                    state, exc, append_error=False, operation=operation, record_usage=False
                )
            self.run_store.save_state(state)
            return False
        state.usage.provider_retries += 1
        state.validate()
        self.run_store.save_state(state)
        return True

    def _provider_failed(
        self,
        state: SkeletonRunState,
        exc: Exception,
        *,
        append_error: bool = True,
        operation: str,
        record_usage: bool = True,
    ) -> None:
        if (
            record_usage
            and getattr(exc, "usage_observed", False)
            and not self._record_usage(state, exc, operation)
        ):
            return
        if append_error:
            state.errors.append(
                {
                    "type": (
                        "PROVIDER_EVIDENCE_ERROR"
                        if isinstance(exc, ProviderEvidenceError)
                        else (
                            "PROVIDER_REFUSAL"
                            if isinstance(exc, ProviderRefusalError)
                            else "PROVIDER_ERROR"
                        )
                    ),
                    "message": str(exc)[:500],
                }
            )
        state.classification = (
            RunClassification.INFRASTRUCTURE_ERROR
            if isinstance(exc, ProviderEvidenceError)
            else RunClassification.PROVIDER_ERROR
        )
        PrepareRunService._move(
            state,
            RunStatus.FAILED,
            "provider_evidence_failed" if isinstance(exc, ProviderEvidenceError) else "provider_failed",
        )
        self.run_store.save_state(state)
