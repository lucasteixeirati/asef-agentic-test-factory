from __future__ import annotations

from dataclasses import dataclass

from ..contracts import SkeletonRunState, UnitTestArtifact
from ..evaluation_contracts import CorrectionFeedback
from ..outcomes import RunClassification, RunStatus
from ..skills.unit import UnitSkill, UnitSkillPolicyError
from .ports import (
    InvalidAgentOutputError,
    ProviderPermanentError,
    ProviderEvidenceError,
    ProviderTransientError,
    RunStorePort,
    TestCorrectionPort,
)
from .prepare_run import PrepareRunService


@dataclass(slots=True, frozen=True)
class CorrectionStepResult:
    artifact: UnitTestArtifact | None
    stop_reason: str | None = None


class CorrectionLoopController:
    def __init__(
        self,
        corrector: TestCorrectionPort,
        skill: UnitSkill,
        run_store: RunStorePort | None = None,
    ) -> None:
        self.corrector = corrector
        self.skill = skill
        self.run_store = run_store

    def correct_once(
        self,
        state: SkeletonRunState,
        previous: UnitTestArtifact,
        feedback: CorrectionFeedback,
    ) -> CorrectionStepResult:
        correction = state.facts.setdefault("correction", {})
        if correction.get("last_fingerprint") == feedback.fingerprint:
            state.classification = RunClassification.TEST_ERROR
            state.record_event("CORRECTION_STOPPED", reason="repeated_diagnostic", fingerprint=feedback.fingerprint)
            return CorrectionStepResult(None, "repeated_diagnostic")
        if state.usage.test_corrections >= state.budgets.max_test_corrections:
            state.classification = RunClassification.BUDGET_ERROR
            PrepareRunService._move(state, RunStatus.BUDGET_EXHAUSTED, "test_correction_budget_exhausted")
            return CorrectionStepResult(None, "budget_exhausted")
        if state.usage.model_calls >= state.budgets.max_model_calls:
            state.classification = RunClassification.BUDGET_ERROR
            PrepareRunService._move(state, RunStatus.BUDGET_EXHAUSTED, "model_call_budget_exhausted")
            return CorrectionStepResult(None, "budget_exhausted")
        if (
            state.usage.input_tokens >= state.budgets.max_input_tokens
            or state.usage.output_tokens >= state.budgets.max_output_tokens
            or state.usage.elapsed_ms >= state.budgets.max_workflow_seconds * 1_000
            or (
                state.request.execution_mode == "live"
                and state.usage.estimated_cost_brl >= state.budgets.api_budget_brl
            )
        ):
            state.classification = RunClassification.BUDGET_ERROR
            PrepareRunService._move(state, RunStatus.BUDGET_EXHAUSTED, "provider_usage_budget_exhausted")
            if self.run_store is not None:
                self.run_store.save_state(state)
            return CorrectionStepResult(None, "budget_exhausted")

        PrepareRunService._move(state, RunStatus.CORRECTING_TESTS, "generated_test_requires_correction")
        state.usage.model_calls += 1
        state.usage.test_corrections += 1
        state.attempts["test_correction"] = state.usage.test_corrections
        correction["last_fingerprint"] = feedback.fingerprint
        correction["feedback_truncated"] = feedback.truncated
        state.validate()
        if self.run_store is not None:
            self.run_store.save_state(state)
        while True:
            try:
                generated = self.corrector.correct(state.request, previous, feedback)
                break
            except (ProviderTransientError, InvalidAgentOutputError) as exc:
                if not self._record_observed_error_usage(state, exc):
                    return CorrectionStepResult(None, "budget_exhausted")
                invalid_output = isinstance(exc, InvalidAgentOutputError)
                state.errors.append(
                    {
                        "type": (
                            "CORRECTION_PROVIDER_OUTPUT_INVALID"
                            if invalid_output
                            else "CORRECTION_PROVIDER_TRANSIENT"
                        ),
                        "message": str(exc)[:500],
                    }
                )
                if (
                    state.usage.provider_retries >= state.budgets.max_provider_retries
                    or state.usage.model_calls >= state.budgets.max_model_calls
                ):
                    state.classification = (
                        RunClassification.BUDGET_ERROR
                        if invalid_output
                        else RunClassification.PROVIDER_ERROR
                    )
                    PrepareRunService._move(
                        state,
                        RunStatus.BUDGET_EXHAUSTED if invalid_output else RunStatus.FAILED,
                        "test_correction_provider_failed",
                    )
                    if self.run_store is not None:
                        self.run_store.save_state(state)
                    return CorrectionStepResult(None, "provider_error")
                state.usage.provider_retries += 1
                state.usage.model_calls += 1
                state.validate()
                if self.run_store is not None:
                    self.run_store.save_state(state)
            except (ProviderPermanentError, OSError, ValueError) as exc:
                if not self._record_observed_error_usage(state, exc):
                    return CorrectionStepResult(None, "budget_exhausted")
                evidence_error = isinstance(exc, ProviderEvidenceError)
                state.errors.append(
                    {
                        "type": (
                            "CORRECTION_PROVIDER_EVIDENCE_ERROR"
                            if evidence_error
                            else "CORRECTION_PROVIDER_ERROR"
                        ),
                        "message": str(exc)[:500],
                    }
                )
                state.classification = (
                    RunClassification.INFRASTRUCTURE_ERROR
                    if evidence_error
                    else RunClassification.PROVIDER_ERROR
                )
                PrepareRunService._move(state, RunStatus.FAILED, "test_correction_provider_failed")
                if self.run_store is not None:
                    self.run_store.save_state(state)
                return CorrectionStepResult(None, "provider_error")
        try:
            artifact = generated.artifact
        except AttributeError as exc:
            state.errors.append({"type": "CORRECTION_PROVIDER_ERROR", "message": str(exc)[:500]})
            state.classification = RunClassification.PROVIDER_ERROR
            PrepareRunService._move(state, RunStatus.FAILED, "test_correction_provider_failed")
            if self.run_store is not None:
                self.run_store.save_state(state)
            return CorrectionStepResult(None, "provider_error")
        metadata = {
            "schema_version": "1.0.0",
            "attempt": artifact.attempt,
            "model": generated.model,
            "response_id": generated.response_id,
            "feedback_fingerprint": feedback.fingerprint,
            "feedback": feedback.diagnostic,
            "feedback_truncated": feedback.truncated,
            "input_tokens": max(0, generated.input_tokens),
            "output_tokens": max(0, generated.output_tokens),
            "provider": generated.provider,
            "latency_ms": max(0, generated.latency_ms),
            "estimated_cost_brl": max(0.0, generated.estimated_cost_brl),
        }
        next_input = state.usage.input_tokens + max(0, generated.input_tokens)
        next_output = state.usage.output_tokens + max(0, generated.output_tokens)
        next_elapsed = state.usage.elapsed_ms + max(0, generated.latency_ms)
        next_cost = round(
            state.usage.estimated_cost_brl + max(0.0, generated.estimated_cost_brl), 8
        )
        state.usage.input_tokens = next_input
        state.usage.output_tokens = next_output
        state.usage.elapsed_ms = next_elapsed
        state.usage.estimated_cost_brl = next_cost
        state.facts.setdefault("provider_calls", []).append(
            {
                "provider": generated.provider,
                "model": generated.model,
                "response_id": generated.response_id,
                "input_tokens": max(0, generated.input_tokens),
                "output_tokens": max(0, generated.output_tokens),
                "latency_ms": max(0, generated.latency_ms),
                "estimated_cost_brl": max(0.0, generated.estimated_cost_brl),
                "operation": "correction",
                "accepted_output": True,
            }
        )
        exceeded = (
            next_input > state.budgets.max_input_tokens
            or next_output > state.budgets.max_output_tokens
            or next_elapsed > state.budgets.max_workflow_seconds * 1_000
            or next_cost > state.budgets.api_budget_brl
        )
        if exceeded:
            state.classification = RunClassification.BUDGET_ERROR
            PrepareRunService._move(state, RunStatus.BUDGET_EXHAUSTED, "correction_usage_budget_exhausted")
            if self.run_store is not None:
                try:
                    refs = self.run_store.save_attempt_artifact(
                        state, artifact, {**metadata, "status": "BUDGET_EXHAUSTED"}
                    )
                    state.evidence_refs.extend(refs)
                except (ValueError, FileExistsError):
                    pass
                self.run_store.save_state(state)
            return CorrectionStepResult(None, "budget_exhausted")
        state.validate()
        if self.run_store is not None:
            self.run_store.save_state(state)
        try:
            if artifact.attempt != previous.attempt + 1:
                raise UnitSkillPolicyError("corrected artifact attempt must increment exactly once")
            if artifact.relative_path != previous.relative_path:
                raise UnitSkillPolicyError("correction cannot change the generated artifact path")
            if artifact.scenario_ids != previous.scenario_ids:
                raise UnitSkillPolicyError("correction cannot change approved scenario_ids")
            if artifact.content_sha256 == previous.content_sha256:
                raise UnitSkillPolicyError("correction must change the generated artifact content")
            self.skill.validate(artifact)
        except UnitSkillPolicyError as exc:
            state.errors.append({"type": "CORRECTION_POLICY_VIOLATION", "message": str(exc)[:500]})
            state.classification = RunClassification.POLICY_VIOLATION
            PrepareRunService._move(state, RunStatus.POLICY_BLOCKED, "corrected_test_policy_violation")
            if self.run_store is not None:
                try:
                    refs = self.run_store.save_attempt_artifact(
                        state, artifact, {**metadata, "status": "REJECTED", "reason": str(exc)[:500]}
                    )
                    state.evidence_refs.extend(refs)
                except (ValueError, FileExistsError):
                    pass
                self.run_store.save_state(state)
            return CorrectionStepResult(None, "policy_violation")

        if self.run_store is not None:
            refs = self.run_store.save_attempt_artifact(state, artifact, {**metadata, "status": "ACCEPTED"})
            state.evidence_refs.extend(refs)

        correction["last_artifact_sha256"] = artifact.content_sha256
        PrepareRunService._move(state, RunStatus.STATIC_VALIDATION, "corrected_test_policy_passed")
        state.validate()
        if self.run_store is not None:
            self.run_store.save_state(state)
        return CorrectionStepResult(artifact)

    def _record_observed_error_usage(self, state: SkeletonRunState, exc: Exception) -> bool:
        if not getattr(exc, "usage_observed", False):
            return True
        next_input = state.usage.input_tokens + max(0, getattr(exc, "input_tokens", 0))
        next_output = state.usage.output_tokens + max(0, getattr(exc, "output_tokens", 0))
        next_elapsed = state.usage.elapsed_ms + max(0, getattr(exc, "latency_ms", 0))
        next_cost = round(
            state.usage.estimated_cost_brl
            + max(0.0, getattr(exc, "estimated_cost_brl", 0.0)),
            8,
        )
        state.usage.input_tokens = next_input
        state.usage.output_tokens = next_output
        state.usage.elapsed_ms = next_elapsed
        state.usage.estimated_cost_brl = next_cost
        state.facts.setdefault("provider_calls", []).append(
            {
                "provider": getattr(exc, "provider", "unknown"),
                "model": getattr(exc, "model", "unknown"),
                "response_id": getattr(exc, "response_id", "unknown"),
                "input_tokens": max(0, getattr(exc, "input_tokens", 0)),
                "output_tokens": max(0, getattr(exc, "output_tokens", 0)),
                "latency_ms": max(0, getattr(exc, "latency_ms", 0)),
                "estimated_cost_brl": max(0.0, getattr(exc, "estimated_cost_brl", 0.0)),
                "operation": "correction",
                "accepted_output": False,
            }
        )
        exceeded = (
            next_input > state.budgets.max_input_tokens
            or next_output > state.budgets.max_output_tokens
            or next_elapsed > state.budgets.max_workflow_seconds * 1_000
            or next_cost > state.budgets.api_budget_brl
        )
        if exceeded:
            state.classification = RunClassification.BUDGET_ERROR
            PrepareRunService._move(state, RunStatus.BUDGET_EXHAUSTED, "correction_usage_budget_exhausted")
        state.validate()
        if self.run_store is not None:
            self.run_store.save_state(state)
        return not exceeded
