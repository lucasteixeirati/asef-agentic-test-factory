from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from asef.application.alpha_evaluation import AlphaEvaluationCoordinator
from asef.application.correct_test import CorrectionLoopController
from asef.application.ports import ExecutionOutput, GeneratedArtifactResult, ResolvedQualityContext
from asef.contracts import (
    EvidenceRef,
    NormalizedExecutionResult,
    SkeletonRunRequest,
    SkeletonRunState,
    SkeletonBudgetLimits,
    TestExecutionOutcome,
    UnitTestArtifact,
)
from asef.context import QualityContext
from asef.outcomes import RunClassification, RunStatus
from asef.skills.unit import UnitSkill


IMAGE = "sha256:" + "e" * 64


def request() -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="examples/context/walking-skeleton-context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title="alpha evaluation",
        requirement_description="evaluate generated test against isolated oracle",
    )


def artifact(attempt: int = 1) -> UnitTestArtifact:
    return UnitTestArtifact(
        "tests_generated/test_value.py",
        f"def test_value():\n    assert {attempt} == {attempt}\n",
        ("SCN-001",),
        attempt,
    )


def normalized(role: str, outcome: TestExecutionOutcome) -> NormalizedExecutionResult:
    failed = 1 if outcome is TestExecutionOutcome.ASSERTION_FAILURE else 0
    errors = 1 if outcome is TestExecutionOutcome.TEST_ERROR else 0
    passed = 1 - failed - errors
    return NormalizedExecutionResult(
        image=IMAGE,
        command=("pytest",),
        exit_code=0 if outcome is TestExecutionOutcome.PASSED else 1,
        duration_ms=1,
        stdout_ref=EvidenceRef("stdout", f"attempts/000/{role}/stdout.txt", "a" * 64),
        stderr_ref=EvidenceRef("stderr", f"attempts/000/{role}/stderr.txt", "b" * 64),
        tests=1,
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=0,
        outcome=outcome,
    )


class Store:
    def __init__(self) -> None:
        self.evaluations = []
        self.saved = 0

    def save_attempt_evaluation(self, state, evaluation, attempt):
        self.evaluations.append((attempt, evaluation))
        return EvidenceRef("combined_oracle_evaluation", f"attempts/{attempt:03d}/evaluation.json", "c" * 64)

    def save_state(self, state):
        self.saved += 1

    def save_attempt_artifact(self, state, artifact, metadata):
        del state, metadata
        return (
            EvidenceRef("unit_test_artifact", f"artifacts/attempt-{artifact.attempt:03d}/{artifact.relative_path}", artifact.content_sha256),
            EvidenceRef("artifact_metadata", f"artifacts/attempt-{artifact.attempt:03d}/metadata.json", "d" * 64),
        )


class Oracle:
    def __init__(self, outcome):
        self.outcome = outcome

    def execute(self, *args):
        return SimpleNamespace(
            execution=normalized("oracle", self.outcome),
            evidence_refs=(
                EvidenceRef("curated_oracle", "oracle/test_oracle.py", "e" * 64),
                EvidenceRef("oracle_identity", "oracle/identity.json", "f" * 64),
            ),
            workspace=SimpleNamespace(oracle_sha256="e" * 64),
        )


class Generated:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def execute(self, state, run_dir, context, current, attempt):
        del state, run_dir, context, current
        outcome = self.outcomes[self.calls]
        self.calls += 1
        raw = ExecutionOutput(
            IMAGE, ("pytest",), 0, 1, "failure output", "diagnostic", 1, 1, 0,
            errors=0, skipped=0, outcome=outcome,
        )
        return SimpleNamespace(raw=raw, normalized=normalized("generated", outcome))


class Corrector:
    def correct(self, request, previous, feedback):
        del request, feedback
        return GeneratedArtifactResult(artifact(previous.attempt + 1), "model", "response", 1, 1)


class Checkpoint:
    def __init__(self):
        self.calls = []

    def pause(self, run_id, database, payload):
        self.calls.append((run_id, database, payload))


class AlphaEvaluationCoordinatorTests(unittest.TestCase):
    def context(self):
        quality = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
        return ResolvedQualityContext(quality.snapshot_for(request()), Path.cwd(), ("README.md",))

    def coordinator(self, generated, oracle, store, checkpoint=None):
        return AlphaEvaluationCoordinator(
            generated,
            oracle,
            CorrectionLoopController(Corrector(), UnitSkill()),
            store,
            checkpoint,
        )

    def test_both_passing_succeeds_with_one_attempt(self) -> None:
        state = SkeletonRunState(request())
        store = Store()
        with tempfile.TemporaryDirectory() as directory:
            result = self.coordinator(Generated([TestExecutionOutcome.PASSED]), Oracle(TestExecutionOutcome.PASSED), store).execute(
                state, Path(directory), self.context(), artifact(), "oracle.py"
            )
        self.assertEqual((result.state.status, result.state.classification), (RunStatus.SUCCEEDED, RunClassification.ACCEPTED))
        self.assertEqual(result.attempts_executed, 1)

    def test_test_error_is_corrected_then_accepted(self) -> None:
        state = SkeletonRunState(request())
        store = Store()
        generated = Generated([TestExecutionOutcome.TEST_ERROR, TestExecutionOutcome.PASSED])
        with tempfile.TemporaryDirectory() as directory:
            result = self.coordinator(generated, Oracle(TestExecutionOutcome.PASSED), store).execute(
                state, Path(directory), self.context(), artifact(), "oracle.py"
            )
        self.assertEqual(result.state.status, RunStatus.SUCCEEDED)
        self.assertEqual(result.artifact.attempt, 2)
        self.assertEqual(result.state.usage.test_corrections, 1)
        self.assertEqual([item[0] for item in store.evaluations], [0, 1])

    def test_failing_oracle_pauses_for_human_review_without_correction(self) -> None:
        state = SkeletonRunState(request())
        store = Store()
        checkpoint = Checkpoint()
        with tempfile.TemporaryDirectory() as directory:
            result = self.coordinator(
                Generated([TestExecutionOutcome.PASSED]),
                Oracle(TestExecutionOutcome.ASSERTION_FAILURE),
                store,
                checkpoint,
            ).execute(state, Path(directory), self.context(), artifact(), "oracle.py")
        self.assertEqual(result.state.status, RunStatus.WAITING_FOR_HUMAN_REVIEW)
        self.assertEqual(result.state.classification, RunClassification.SUT_DEFECT_SUSPECTED)
        self.assertEqual(result.state.usage.test_corrections, 0)
        self.assertEqual(len(checkpoint.calls), 1)

    def test_invalid_oracle_is_inconclusive(self) -> None:
        state = SkeletonRunState(request())
        store = Store()
        with tempfile.TemporaryDirectory() as directory:
            result = self.coordinator(
                Generated([TestExecutionOutcome.PASSED]),
                Oracle(TestExecutionOutcome.TEST_ERROR),
                store,
            ).execute(state, Path(directory), self.context(), artifact(), "oracle.py")
        self.assertEqual((result.state.status, result.state.classification), (RunStatus.FAILED, RunClassification.INCONCLUSIVE))

    def test_zero_correction_budget_stops_without_calling_corrector(self) -> None:
        state = SkeletonRunState(request(), budgets=SkeletonBudgetLimits(max_test_corrections=0))
        store = Store()
        with tempfile.TemporaryDirectory() as directory:
            result = self.coordinator(
                Generated([TestExecutionOutcome.TEST_ERROR]),
                Oracle(TestExecutionOutcome.PASSED),
                store,
            ).execute(state, Path(directory), self.context(), artifact(), "oracle.py")
        self.assertEqual((result.state.status, result.state.classification), (RunStatus.BUDGET_EXHAUSTED, RunClassification.BUDGET_ERROR))
        self.assertEqual(result.state.usage.test_corrections, 0)

    def test_infrastructure_failure_is_normalized_and_workspaces_are_cleaned(self) -> None:
        class BrokenGenerated:
            def execute(self, state, run_dir, context, current, attempt):
                del state, context, current, attempt
                (run_dir / "attempt-workspaces/000/generated").mkdir(parents=True)
                raise OSError("docker unavailable")

        state = SkeletonRunState(request())
        store = Store()
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            result = self.coordinator(
                BrokenGenerated(), Oracle(TestExecutionOutcome.PASSED), store
            ).execute(state, run_dir, self.context(), artifact(), "oracle.py")
            self.assertFalse((run_dir / "attempt-workspaces").exists())
            self.assertFalse((run_dir / "oracle-workspace").exists())
        self.assertEqual((result.state.status, result.state.classification), (RunStatus.FAILED, RunClassification.INFRASTRUCTURE_ERROR))

    def test_missing_oracle_is_allowed_for_an_injected_executor_failure(self) -> None:
        class BrokenGenerated:
            def execute(self, *args):
                raise OSError("injected docker unavailable")

        class OracleMustNotRun:
            def execute(self, *args):
                raise AssertionError("oracle must not run when no oracle_ref is declared")

        state = SkeletonRunState(request())
        store = Store()
        with tempfile.TemporaryDirectory() as directory:
            result = self.coordinator(BrokenGenerated(), OracleMustNotRun(), store).execute(
                state, Path(directory), self.context(), artifact(), None
            )
        self.assertEqual(result.attempts_executed, 1)
        self.assertEqual(
            (result.state.status, result.state.classification),
            (RunStatus.FAILED, RunClassification.INFRASTRUCTURE_ERROR),
        )


if __name__ == "__main__":
    unittest.main()
