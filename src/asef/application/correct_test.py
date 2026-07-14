from __future__ import annotations

from dataclasses import dataclass

from ..contracts import SkeletonRunState, UnitTestArtifact
from ..evaluation_contracts import CorrectionFeedback
from ..outcomes import RunClassification, RunStatus
from ..skills.unit import UnitSkill, UnitSkillPolicyError
from .ports import InvalidAgentOutputError, RunStorePort, TestCorrectionPort
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

        PrepareRunService._move(state, RunStatus.CORRECTING_TESTS, "generated_test_requires_correction")
        state.usage.model_calls += 1
        state.usage.test_corrections += 1
        state.attempts["test_correction"] = state.usage.test_corrections
        correction["last_fingerprint"] = feedback.fingerprint
        correction["feedback_truncated"] = feedback.truncated
        state.validate()
        if self.run_store is not None:
            self.run_store.save_state(state)
        try:
            generated = self.corrector.correct(state.request, previous, feedback)
        except (InvalidAgentOutputError, OSError, ValueError) as exc:
            state.errors.append({"type": "CORRECTION_PROVIDER_ERROR", "message": str(exc)[:500]})
            state.classification = RunClassification.PROVIDER_ERROR
            PrepareRunService._move(state, RunStatus.FAILED, "test_correction_provider_failed")
            if self.run_store is not None:
                self.run_store.save_state(state)
            return CorrectionStepResult(None, "provider_error")
        artifact = generated.artifact
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
        }
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

        next_input = state.usage.input_tokens + max(0, generated.input_tokens)
        next_output = state.usage.output_tokens + max(0, generated.output_tokens)
        if next_input > state.budgets.max_input_tokens or next_output > state.budgets.max_output_tokens:
            state.usage.input_tokens = next_input
            state.usage.output_tokens = next_output
            state.classification = RunClassification.BUDGET_ERROR
            PrepareRunService._move(state, RunStatus.BUDGET_EXHAUSTED, "correction_token_budget_exhausted")
            if self.run_store is not None:
                self.run_store.save_state(state)
            return CorrectionStepResult(None, "budget_exhausted")
        state.usage.input_tokens = next_input
        state.usage.output_tokens = next_output
        correction["last_artifact_sha256"] = artifact.content_sha256
        PrepareRunService._move(state, RunStatus.STATIC_VALIDATION, "corrected_test_policy_passed")
        state.validate()
        if self.run_store is not None:
            self.run_store.save_state(state)
        return CorrectionStepResult(artifact)
