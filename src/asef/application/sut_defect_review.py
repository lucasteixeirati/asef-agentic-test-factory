from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from ..contracts import ContractValidationError, SkeletonRunState, utc_now
from ..outcomes import RunClassification, RunStatus
from .ports import HumanCheckpointPort, RunStorePort
from .prepare_run import PrepareRunService


class SutDefectDecision(StrEnum):
    CONFIRM_SUSPECTED_DEFECT = "confirm_suspected_defect"
    REJECT_AS_INCONCLUSIVE = "reject_as_inconclusive"


@dataclass(slots=True, frozen=True)
class SutDefectReviewResult:
    state: SkeletonRunState
    report_path: str
    idempotent_replay: bool = False


class SutDefectReviewService:
    def __init__(
        self,
        checkpoint: HumanCheckpointPort,
        run_store: RunStorePort,
        output_root: Path,
    ) -> None:
        self.checkpoint = checkpoint
        self.run_store = run_store
        self.output_root = output_root

    def resume(
        self,
        run_id: str,
        decision: SutDefectDecision,
        rationale: str,
    ) -> SutDefectReviewResult:
        rationale = self._validate_rationale(rationale)
        state = self.run_store.load_state(run_id)
        existing = state.facts.get("sut_defect_review")
        if isinstance(existing, dict):
            if existing.get("decision") != decision.value:
                raise ContractValidationError("SUT defect review already has a different decision")
            return SutDefectReviewResult(state, "report.md", True)
        if state.status is not RunStatus.WAITING_FOR_HUMAN_REVIEW:
            raise ContractValidationError("run is not waiting for SUT defect review")
        checkpoint_fact = state.facts.get("human_checkpoint")
        if not isinstance(checkpoint_fact, dict) or checkpoint_fact.get("kind") != "sut_defect_review":
            raise ContractValidationError("SUT defect review checkpoint metadata is missing")

        result = self.checkpoint.resume(
            run_id,
            self.output_root / run_id / "checkpoint.sqlite",
            decision.value,
        )
        checkpoint_decision = result.get("decision", {})
        if checkpoint_decision.get("action") != "resume" or checkpoint_decision.get("answer") != decision.value:
            raise ContractValidationError("checkpoint SUT defect decision is inconsistent")
        payload = result.get("payload")
        if not isinstance(payload, dict) or payload.get("attempt") != checkpoint_fact.get("attempt"):
            raise ContractValidationError("checkpoint attempt differs from persisted review metadata")

        state.facts["sut_defect_review"] = {
            "decision_id": str(uuid4()),
            "decision": decision.value,
            "rationale": rationale,
            "attempt": checkpoint_fact["attempt"],
            "created_at": utc_now(),
        }
        state.record_event(
            "HUMAN_DECISION_RECORDED",
            action=decision.value,
            attempt=checkpoint_fact["attempt"],
            value_recorded_in_facts=True,
        )
        if decision is SutDefectDecision.CONFIRM_SUSPECTED_DEFECT:
            state.classification = RunClassification.SUT_DEFECT_SUSPECTED
            conclusion = "Human review confirmed the evidence-backed SUT defect suspicion"
        else:
            state.classification = RunClassification.INCONCLUSIVE
            conclusion = "Human review rejected the SUT defect suspicion as inconclusive"
        PrepareRunService._move(state, RunStatus.FAILED, "sut_defect_review_recorded")
        latest = state.facts.get("latest_evaluation", {})
        evaluation = {
            "accepted": False,
            "conclusion": conclusion,
            "attempt": checkpoint_fact["attempt"],
            "combined_evaluation": latest,
        }
        report_path = self.run_store.save_report(state, None, evaluation)
        return SutDefectReviewResult(state, report_path)

    @staticmethod
    def _validate_rationale(value: str) -> str:
        normalized = value.strip()
        if not normalized or len(normalized) > 2_000:
            raise ContractValidationError("review rationale must contain 1 to 2000 characters")
        lowered = normalized.lower()
        if any(marker in lowered for marker in ("sk-", "api_key=", "password=", "secret=")):
            raise ContractValidationError("review rationale contains a sensitive value marker")
        return normalized
