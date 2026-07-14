from __future__ import annotations

import unittest

from asef.application.correct_test import CorrectionLoopController
from asef.application.ports import GeneratedArtifactResult
from asef.contracts import SkeletonRunRequest, SkeletonRunState, TestExecutionOutcome, UnitTestArtifact
from asef.evaluation_contracts import build_correction_feedback
from asef.outcomes import RunClassification, RunStatus
from asef.skills.unit import UnitSkill, UnitSkillPolicyError


def request() -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title="correction",
        requirement_description="correct a generated unit test using bounded feedback",
    )


def artifact(attempt: int, marker: int = 0) -> UnitTestArtifact:
    return UnitTestArtifact(
        relative_path="tests_generated/test_value.py",
        content=f"def test_value():\n    assert {marker} == {marker}\n",
        scenario_ids=("SCN-001",),
        attempt=attempt,
    )


class Corrector:
    def __init__(self) -> None:
        self.calls = 0

    def correct(self, request, previous, feedback) -> GeneratedArtifactResult:
        del request, feedback
        self.calls += 1
        return GeneratedArtifactResult(
            artifact=artifact(previous.attempt + 1, self.calls),
            model="recorded-corrector",
            response_id=f"correction-{self.calls}",
            input_tokens=10,
            output_tokens=5,
        )


class CorrectionFeedbackTests(unittest.TestCase):
    def test_feedback_is_redacted_bounded_and_stably_fingerprinted(self) -> None:
        value = "api_key=super-secret\x00\n" + "failure " * 100
        first = build_correction_feedback(TestExecutionOutcome.TEST_ERROR, value, "", max_bytes=128)
        second = build_correction_feedback(TestExecutionOutcome.TEST_ERROR, value, "", max_bytes=128)
        self.assertNotIn("super-secret", first.diagnostic)
        self.assertIn("[REDACTED]", first.diagnostic)
        self.assertTrue(first.truncated)
        self.assertEqual(first.fingerprint, second.fingerprint)


class CorrectionLoopControllerTests(unittest.TestCase):
    def test_two_corrections_are_allowed_and_third_exhausts_budget(self) -> None:
        state = SkeletonRunState(request())
        corrector = Corrector()
        controller = CorrectionLoopController(corrector, UnitSkill())
        current = artifact(1)
        for index in range(2):
            feedback = build_correction_feedback(
                TestExecutionOutcome.TEST_ERROR, "", f"failure {index}"
            )
            result = controller.correct_once(state, current, feedback)
            self.assertIsNotNone(result.artifact)
            current = result.artifact

        exhausted = controller.correct_once(
            state,
            current,
            build_correction_feedback(TestExecutionOutcome.TEST_ERROR, "", "third failure"),
        )
        self.assertEqual(exhausted.stop_reason, "budget_exhausted")
        self.assertEqual(state.status, RunStatus.BUDGET_EXHAUSTED)
        self.assertEqual(state.classification, RunClassification.BUDGET_ERROR)
        self.assertEqual(state.usage.test_corrections, 2)
        self.assertEqual(corrector.calls, 2)

    def test_repeated_diagnostic_stops_before_spending_another_correction(self) -> None:
        state = SkeletonRunState(request())
        corrector = Corrector()
        controller = CorrectionLoopController(corrector, UnitSkill())
        feedback = build_correction_feedback(TestExecutionOutcome.TEST_ERROR, "", "same failure")
        first = controller.correct_once(state, artifact(1), feedback)
        repeated = controller.correct_once(state, first.artifact, feedback)
        self.assertEqual(repeated.stop_reason, "repeated_diagnostic")
        self.assertEqual(state.usage.test_corrections, 1)
        self.assertEqual(corrector.calls, 1)

    def test_correction_cannot_change_path_scenarios_or_attempt_sequence(self) -> None:
        previous = artifact(1)
        feedback = build_correction_feedback(TestExecutionOutcome.TEST_ERROR, "", "failure")

        class InvalidCorrector:
            def correct(self, request, previous, feedback):
                del request, previous, feedback
                return GeneratedArtifactResult(
                    UnitTestArtifact("tests_generated/other.py", "def test_x():\n    assert True\n", ("SCN-001",), 2),
                    "model",
                    "response",
                )

        state = SkeletonRunState(request())
        result = CorrectionLoopController(InvalidCorrector(), UnitSkill()).correct_once(
            state, previous, feedback
        )
        self.assertEqual(result.stop_reason, "policy_violation")
        self.assertEqual(state.status, RunStatus.POLICY_BLOCKED)
        self.assertEqual(state.usage.test_corrections, 1)
        self.assertEqual(state.usage.model_calls, 1)

    def test_provider_failure_persists_reserved_budget(self) -> None:
        class FailingCorrector:
            def correct(self, request, previous, feedback):
                del request, previous, feedback
                raise OSError("provider unavailable")

        class Store:
            def __init__(self):
                self.snapshots = []

            def save_state(self, state):
                self.snapshots.append((state.status, state.usage.model_calls, state.usage.test_corrections))

        state = SkeletonRunState(request())
        store = Store()
        result = CorrectionLoopController(FailingCorrector(), UnitSkill(), store).correct_once(
            state,
            artifact(1),
            build_correction_feedback(TestExecutionOutcome.TEST_ERROR, "", "provider failure"),
        )
        self.assertEqual(result.stop_reason, "provider_error")
        self.assertEqual(state.classification, RunClassification.PROVIDER_ERROR)
        self.assertEqual(store.snapshots[0][1:], (1, 1))
        self.assertEqual(store.snapshots[-1][0], RunStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
