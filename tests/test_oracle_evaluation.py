from __future__ import annotations

import unittest

from asef.contracts import ContractValidationError, EvidenceRef, TestExecutionOutcome
from asef.evaluation_contracts import EvaluationAction, evaluate_generated_and_oracle
from asef.outcomes import RunClassification


def evidence(name: str) -> EvidenceRef:
    return EvidenceRef(kind="pytest-junit", relative_path=f"results/{name}.xml", sha256="a" * 64)


class CombinedOracleEvaluationTests(unittest.TestCase):
    def evaluate(self, generated: TestExecutionOutcome, oracle: TestExecutionOutcome | None):
        return evaluate_generated_and_oracle(
            generated,
            oracle,
            evidence("generated"),
            evidence("oracle") if oracle is not None else None,
        )

    def test_both_passing_is_accepted(self) -> None:
        result = self.evaluate(TestExecutionOutcome.PASSED, TestExecutionOutcome.PASSED)
        self.assertEqual((result.classification, result.action), (RunClassification.ACCEPTED, EvaluationAction.ACCEPT))
        self.assertEqual(result.to_dict()["classification"], "ACCEPTED")

    def test_invalid_generated_test_is_correctable_without_oracle(self) -> None:
        for outcome in (TestExecutionOutcome.TEST_ERROR, TestExecutionOutcome.NO_TESTS):
            with self.subTest(outcome=outcome):
                result = self.evaluate(outcome, None)
                self.assertEqual(
                    (result.classification, result.action),
                    (RunClassification.TEST_ERROR, EvaluationAction.CORRECT_TEST),
                )

    def test_generated_failure_conflicting_with_passing_oracle_is_correctable(self) -> None:
        result = self.evaluate(TestExecutionOutcome.ASSERTION_FAILURE, TestExecutionOutcome.PASSED)
        self.assertEqual((result.classification, result.action), (RunClassification.TEST_ERROR, EvaluationAction.CORRECT_TEST))

    def test_failing_oracle_requires_human_review_for_possible_sut_defect(self) -> None:
        for generated in (TestExecutionOutcome.PASSED, TestExecutionOutcome.ASSERTION_FAILURE):
            with self.subTest(generated=generated):
                result = self.evaluate(generated, TestExecutionOutcome.ASSERTION_FAILURE)
                self.assertEqual(
                    (result.classification, result.action),
                    (RunClassification.SUT_DEFECT_SUSPECTED, EvaluationAction.HUMAN_REVIEW),
                )

    def test_oracle_error_is_inconclusive_not_a_sut_defect(self) -> None:
        for oracle in (TestExecutionOutcome.TEST_ERROR, TestExecutionOutcome.NO_TESTS, TestExecutionOutcome.UNCLASSIFIED):
            with self.subTest(oracle=oracle):
                result = self.evaluate(TestExecutionOutcome.PASSED, oracle)
                self.assertEqual((result.classification, result.action), (RunClassification.INCONCLUSIVE, EvaluationAction.STOP))

    def test_infrastructure_has_precedence_and_stops(self) -> None:
        result = self.evaluate(TestExecutionOutcome.PASSED, TestExecutionOutcome.INFRASTRUCTURE_ERROR)
        self.assertEqual(
            (result.classification, result.action),
            (RunClassification.INFRASTRUCTURE_ERROR, EvaluationAction.STOP),
        )

    def test_oracle_outcome_and_evidence_reference_must_be_consistent(self) -> None:
        with self.assertRaises(ContractValidationError):
            evaluate_generated_and_oracle(
                TestExecutionOutcome.PASSED,
                TestExecutionOutcome.PASSED,
                evidence("generated"),
                None,
            )


if __name__ == "__main__":
    unittest.main()
