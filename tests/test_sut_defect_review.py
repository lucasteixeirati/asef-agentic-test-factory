from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from asef.application.sut_defect_review import SutDefectDecision, SutDefectReviewService
from asef.contracts import ContractValidationError, SkeletonRunRequest, SkeletonRunState
from asef.outcomes import RunClassification, RunStatus


def waiting_state() -> SkeletonRunState:
    state = SkeletonRunState(
        SkeletonRunRequest(
            context_ref="context.json",
            system_id="sut",
            requested_skill="unit",
            requirement_title="review",
            requirement_description="review an evidence-backed suspected SUT defect",
        )
    )
    state.status = RunStatus.WAITING_FOR_HUMAN_REVIEW
    state.classification = RunClassification.SUT_DEFECT_SUSPECTED
    state.attempts["generated_execution"] = 1
    state.facts["latest_evaluation"] = {"classification": "SUT_DEFECT_SUSPECTED"}
    state.facts["human_checkpoint"] = {
        "kind": "sut_defect_review",
        "ref": "checkpoint.sqlite",
        "attempt": 0,
        "evaluation_ref": "attempts/000/evaluation.json",
    }
    return state


class Store:
    def __init__(self, state):
        self.state = state
        self.reports = 0

    def load_state(self, run_id):
        if run_id != self.state.run_id:
            raise ValueError("missing")
        return self.state

    def save_report(self, state, execution, evaluation):
        del execution
        self.state = state
        self.evaluation = evaluation
        self.reports += 1
        return "report.md"


class Checkpoint:
    def __init__(self, state):
        self.state = state
        self.calls = 0

    def resume(self, run_id, database, answer):
        del run_id, database
        self.calls += 1
        return {
            "decision": {"action": "resume", "answer": answer},
            "payload": {"attempt": self.state.facts["human_checkpoint"]["attempt"]},
        }


class SutDefectReviewServiceTests(unittest.TestCase):
    def service(self, state, root):
        store = Store(state)
        checkpoint = Checkpoint(state)
        return SutDefectReviewService(checkpoint, store, root), store, checkpoint

    def test_same_confirmed_decision_is_idempotent_and_does_not_repeat_work(self) -> None:
        state = waiting_state()
        executions_before = dict(state.attempts)
        with tempfile.TemporaryDirectory() as directory:
            service, store, checkpoint = self.service(state, Path(directory))
            first = service.resume(
                state.run_id,
                SutDefectDecision.CONFIRM_SUSPECTED_DEFECT,
                "The curated oracle reproduces the requirement violation.",
            )
            second = service.resume(
                state.run_id,
                SutDefectDecision.CONFIRM_SUSPECTED_DEFECT,
                "Repeated client request must return the persisted decision.",
            )

        self.assertEqual(first.state.status, RunStatus.FAILED)
        self.assertEqual(first.state.classification, RunClassification.SUT_DEFECT_SUSPECTED)
        self.assertTrue(second.idempotent_replay)
        self.assertEqual(checkpoint.calls, 1)
        self.assertEqual(store.reports, 1)
        self.assertEqual(state.attempts, executions_before)
        self.assertEqual(
            sum(event.get("event") == "HUMAN_DECISION_RECORDED" for event in state.history),
            1,
        )

    def test_rejection_finishes_as_inconclusive_and_conflicting_replay_is_blocked(self) -> None:
        state = waiting_state()
        with tempfile.TemporaryDirectory() as directory:
            service, _, checkpoint = self.service(state, Path(directory))
            result = service.resume(
                state.run_id,
                SutDefectDecision.REJECT_AS_INCONCLUSIVE,
                "The oracle evidence is insufficient for a defect conclusion.",
            )
            self.assertEqual(result.state.classification, RunClassification.INCONCLUSIVE)
            with self.assertRaisesRegex(ContractValidationError, "different decision"):
                service.resume(
                    state.run_id,
                    SutDefectDecision.CONFIRM_SUSPECTED_DEFECT,
                    "Conflicting retry.",
                )
        self.assertEqual(checkpoint.calls, 1)

    def test_missing_review_metadata_fails_before_checkpoint(self) -> None:
        state = waiting_state()
        state.facts.pop("human_checkpoint")
        with tempfile.TemporaryDirectory() as directory:
            service, _, checkpoint = self.service(state, Path(directory))
            with self.assertRaisesRegex(ContractValidationError, "metadata"):
                service.resume(
                    state.run_id,
                    SutDefectDecision.CONFIRM_SUSPECTED_DEFECT,
                    "Valid rationale.",
                )
        self.assertEqual(checkpoint.calls, 0)


if __name__ == "__main__":
    unittest.main()
