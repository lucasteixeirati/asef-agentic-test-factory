from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from ..contracts import ContractValidationError, SkeletonRunState, utc_now
from ..outcomes import RunClassification, RunStatus
from .complete_workflow import CompleteWorkflowResult, CompleteWorkflowService
from .generate_unit import GenerateUnitTestService
from .ports import AnalysisResult, HumanCheckpointPort, QualityContextPort, RunStorePort
from .prepare_run import PrepareRunResult, PrepareRunService


@dataclass(slots=True, frozen=True)
class HumanDecisionResult:
    state: SkeletonRunState
    run_dir: Path
    report_path: str | None


class HumanDecisionService:
    def __init__(
        self,
        context_port: QualityContextPort,
        checkpoint: HumanCheckpointPort,
        generation: GenerateUnitTestService,
        completion: CompleteWorkflowService,
        run_store: RunStorePort,
        output_root: Path,
    ) -> None:
        self.context_port = context_port
        self.checkpoint = checkpoint
        self.generation = generation
        self.completion = completion
        self.run_store = run_store
        self.output_root = output_root

    def resume(self, run_id: str, answer: str) -> CompleteWorkflowResult:
        answer = self._validate_text(answer, "clarification answer")
        state, prepared = self._load_waiting(run_id)
        result = self.checkpoint.resume(
            run_id,
            prepared.run_dir / "checkpoint.sqlite",
            answer,
        )
        decision = result["decision"]
        if decision.get("action") != "resume" or decision.get("answer") != answer:
            raise ContractValidationError("checkpoint resume decision is inconsistent")
        analysis_value = result["payload"].get("analysis")
        if not isinstance(analysis_value, dict):
            raise ContractValidationError("checkpoint analysis payload is missing")
        analysis = AnalysisResult(
            behaviors=tuple(analysis_value["behaviors"]),
            risks=tuple(analysis_value["risks"]),
            scenarios=tuple(analysis_value["scenarios"]),
            clarification_required=False,
            model=str(analysis_value["model"]),
            response_id=str(analysis_value["response_id"]),
        )
        state.facts["clarification"] = answer
        self._append_decision(state, "resume", answer)
        state.classification = RunClassification.UNCLASSIFIED
        self.run_store.save_state(state)
        generated = self.generation.continue_after_analysis(prepared, analysis)
        return self.completion.complete_generated(generated)

    def cancel(self, run_id: str, reason: str) -> HumanDecisionResult:
        reason = self._validate_text(reason, "cancellation reason")
        state, prepared = self._load_waiting(run_id)
        result = self.checkpoint.cancel(
            run_id,
            prepared.run_dir / "checkpoint.sqlite",
            reason,
        )
        if result["decision"].get("action") != "cancel":
            raise ContractValidationError("checkpoint cancellation decision is inconsistent")
        self._append_decision(state, "cancel", reason)
        state.classification = RunClassification.CANCELLED_BY_USER
        PrepareRunService._move(state, RunStatus.CANCELLED, "human_cancelled_wait")
        evaluation = {
            "accepted": False,
            "conclusion": "Run cancelled by human decision",
            "tests": None,
            "passed": None,
            "failed": None,
        }
        report_path = self.run_store.save_report(state, None, evaluation)
        return HumanDecisionResult(state, prepared.run_dir, report_path)

    def _load_waiting(self, run_id: str):
        state = self.run_store.load_state(run_id)
        if state.status is not RunStatus.WAITING_FOR_CLARIFICATION:
            raise ContractValidationError("run is not waiting for clarification")
        stored_snapshot = self.run_store.load_snapshot(run_id)
        resolved = self.context_port.resolve(state.request)
        if stored_snapshot.to_dict() != resolved.snapshot.to_dict():
            raise ContractValidationError("current QualityContext differs from the persisted snapshot")
        return state, PrepareRunResult(state, self.output_root / run_id, resolved)

    @staticmethod
    def _append_decision(state: SkeletonRunState, action: str, value: str) -> None:
        decisions = state.facts.setdefault("human_decisions", [])
        if any(item.get("action") == action and item.get("value") == value for item in decisions):
            return
        decision_id = str(uuid4())
        decisions.append(
            {
                "decision_id": decision_id,
                "action": action,
                "value": value,
                "created_at": utc_now(),
            }
        )
        state.record_event(
            "HUMAN_DECISION_RECORDED",
            action=action,
            decision_id=decision_id,
            value_recorded_in_facts=True,
        )

    @staticmethod
    def _validate_text(value: str, label: str) -> str:
        normalized = value.strip()
        if not normalized or len(normalized) > 2_000:
            raise ContractValidationError(f"{label} must contain 1 to 2000 characters")
        lowered = normalized.lower()
        if any(marker in lowered for marker in ("sk-", "api_key=", "password=", "secret=")):
            raise ContractValidationError(f"{label} contains a sensitive value marker")
        return normalized
