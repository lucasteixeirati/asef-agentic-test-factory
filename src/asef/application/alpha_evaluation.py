from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from ..contracts import EvidenceRef, SkeletonRunState, UnitTestArtifact
from ..evaluation_contracts import EvaluationAction, build_correction_feedback, evaluate_generated_and_oracle
from ..outcomes import RunClassification, RunStatus
from .correct_test import CorrectionLoopController
from .execute_generated import ExecuteGeneratedAttemptService
from .execute_oracle import ExecuteOracleService
from .ports import HumanCheckpointPort, ResolvedQualityContext, RunStorePort
from .prepare_run import PrepareRunService


@dataclass(slots=True, frozen=True)
class AlphaEvaluationResult:
    state: SkeletonRunState
    artifact: UnitTestArtifact
    attempts_executed: int


class AlphaEvaluationCoordinator:
    def __init__(
        self,
        generated: ExecuteGeneratedAttemptService,
        oracle: ExecuteOracleService,
        corrections: CorrectionLoopController,
        run_store: RunStorePort,
        checkpoint: HumanCheckpointPort | None = None,
    ) -> None:
        self.generated = generated
        self.oracle = oracle
        self.corrections = corrections
        self.corrections.run_store = run_store
        self.run_store = run_store
        self.checkpoint = checkpoint

    def execute(
        self,
        state: SkeletonRunState,
        run_dir: Path,
        context: ResolvedQualityContext,
        artifact: UnitTestArtifact,
        oracle_ref: str,
    ) -> AlphaEvaluationResult:
        current = artifact
        executed = 0
        try:
            initial_fact = state.facts.get("artifact", {})
            initial_refs = self.run_store.save_attempt_artifact(
                state,
                artifact,
                {
                    "schema_version": "1.0.0",
                    "attempt": artifact.attempt,
                    "status": "ACCEPTED",
                    "source": "initial_generation",
                    "model": initial_fact.get("model") if isinstance(initial_fact, dict) else None,
                    "response_id": initial_fact.get("response_id") if isinstance(initial_fact, dict) else None,
                },
            )
            state.evidence_refs.extend(ref for ref in initial_refs if ref not in state.evidence_refs)
            oracle = self.oracle.execute(state, run_dir, context, context.snapshot, oracle_ref, 0)
            self._add_execution_refs(state, oracle.execution)
            while True:
                attempt = current.attempt - 1
                PrepareRunService._move(state, RunStatus.EXECUTING_TESTS, "generated_attempt_ready")
                generated = self.generated.execute(state, run_dir, context, current, attempt)
                executed += 1
                self._add_execution_refs(state, generated.normalized)
                PrepareRunService._move(state, RunStatus.EVALUATING_EVIDENCE, "attempt_evidence_saved")
                evaluation = evaluate_generated_and_oracle(
                    generated.normalized.outcome,
                    oracle.execution.outcome,
                    generated.normalized.raw_result_ref or generated.normalized.stdout_ref,
                    oracle.execution.raw_result_ref or oracle.execution.stdout_ref,
                )
                evaluation_ref = self.run_store.save_attempt_evaluation(state, evaluation.to_dict(), attempt)
                state.evidence_refs.append(evaluation_ref)
                state.facts["latest_evaluation"] = evaluation.to_dict()

                if evaluation.action is EvaluationAction.ACCEPT:
                    state.classification = evaluation.classification
                    PrepareRunService._move(state, RunStatus.SUCCEEDED, "combined_oracle_accepted")
                    self.run_store.save_state(state)
                    return AlphaEvaluationResult(state, current, executed)
                if evaluation.action is EvaluationAction.HUMAN_REVIEW:
                    state.classification = evaluation.classification
                    PrepareRunService._move(state, RunStatus.WAITING_FOR_HUMAN_REVIEW, "sut_defect_suspected")
                    if self.checkpoint is not None:
                        self.checkpoint.pause(
                            state.run_id,
                            run_dir / "checkpoint.sqlite",
                            {
                                "schema_version": "1.0.0",
                                "checkpoint_kind": "sut_defect_review",
                                "evaluation": evaluation.to_dict(),
                                "attempt": attempt,
                            },
                        )
                    state.facts["human_checkpoint"] = {
                        "kind": "sut_defect_review",
                        "ref": "checkpoint.sqlite",
                        "attempt": attempt,
                        "evaluation_ref": evaluation_ref.relative_path,
                    }
                    self.run_store.save_state(state)
                    return AlphaEvaluationResult(state, current, executed)
                if evaluation.action is EvaluationAction.CORRECT_TEST:
                    feedback = build_correction_feedback(
                        generated.normalized.outcome,
                        generated.raw.stdout,
                        generated.raw.stderr,
                    )
                    corrected = self.corrections.correct_once(state, current, feedback)
                    if corrected.artifact is not None:
                        current = corrected.artifact
                        continue
                    self.run_store.save_state(state)
                    return AlphaEvaluationResult(state, current, executed)

                state.classification = evaluation.classification
                PrepareRunService._move(state, RunStatus.FAILED, "combined_oracle_inconclusive")
                self.run_store.save_state(state)
                return AlphaEvaluationResult(state, current, executed)
        except (OSError, ValueError, RuntimeError) as exc:
            state.errors.append({"type": "ALPHA_INFRASTRUCTURE_ERROR", "message": str(exc)[:500]})
            state.classification = RunClassification.INFRASTRUCTURE_ERROR
            PrepareRunService._move(state, RunStatus.FAILED, "alpha_infrastructure_failed")
            self.run_store.save_state(state)
            return AlphaEvaluationResult(state, current, executed)
        finally:
            shutil.rmtree(run_dir / "oracle-workspace", ignore_errors=True)
            shutil.rmtree(run_dir / "attempt-workspaces", ignore_errors=True)

    @staticmethod
    def _add_execution_refs(state: SkeletonRunState, execution) -> None:
        refs: tuple[EvidenceRef | None, ...] = (
            execution.stdout_ref,
            execution.stderr_ref,
            execution.raw_result_ref,
        )
        state.evidence_refs.extend(ref for ref in refs if ref is not None)
