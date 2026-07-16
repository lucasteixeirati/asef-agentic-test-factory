from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from asef.adapters.recorded_agent import RecordedAgentAdapter, RecordedAgentError
from asef.application.alpha_evaluation import AlphaEvaluationResult
from asef.application.generate_unit import GenerateUnitResult
from asef.application.run_alpha_case import RunAlphaCaseService
from asef.contracts import SkeletonRunRequest, SkeletonRunState, TestExecutionOutcome, UnitTestArtifact
from asef.evaluation_contracts import build_correction_feedback
from asef.outcomes import RunClassification, RunStatus


ROOT = Path(__file__).resolve().parents[1]


def request() -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="examples/context/python-alpha-smoke-context.json",
        system_id="alpha-reference-sut",
        requested_skill="unit",
        requirement_title="Alpha case",
        requirement_description="Exercise the composed Alpha service.",
    )


def artifact() -> UnitTestArtifact:
    return UnitTestArtifact(
        "tests_generated/test_alpha.py",
        "def test_alpha():\n    assert True\n",
        ("SCN-001",),
    )


class RunAlphaCaseServiceTests(unittest.TestCase):
    def test_pre_execution_terminal_result_does_not_call_evaluation(self) -> None:
        state = SkeletonRunState(request())
        state.status = RunStatus.WAITING_FOR_CLARIFICATION
        state.classification = RunClassification.WAITING_HUMAN
        generated = GenerateUnitResult(state, Path("run"), SimpleNamespace())

        class Generation:
            def execute(self, value):
                self.request = value
                return generated

        class Evaluation:
            def execute(self, *args):
                raise AssertionError("evaluation must not run")

        result = RunAlphaCaseService(Generation(), Evaluation()).execute(request(), None)
        self.assertEqual(result.attempts_executed, 0)
        self.assertIsNone(result.terminal_action)
        self.assertIsNone(result.artifact)

    def test_composes_evaluation_and_removes_initial_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            workspace = run_dir / "workspace"
            workspace.mkdir(parents=True)
            state = SkeletonRunState(request())
            state.facts["workspace"] = {"ref": "workspace"}
            initial = artifact()
            generated = GenerateUnitResult(
                state,
                run_dir,
                SimpleNamespace(),
                initial,
                SimpleNamespace(workspace=workspace),
            )

            class Generation:
                def execute(self, value):
                    return generated

            class Evaluation:
                def execute(self, state, run_dir, context, artifact, oracle_ref):
                    self.oracle_ref = oracle_ref
                    self.workspace_was_removed = not workspace.exists()
                    state.status = RunStatus.SUCCEEDED
                    state.classification = RunClassification.ACCEPTED
                    state.facts["latest_evaluation"] = {"action": "ACCEPT"}
                    return AlphaEvaluationResult(state, artifact, 1)

            evaluation = Evaluation()
            result = RunAlphaCaseService(Generation(), evaluation).execute(
                request(), "datasets/smoke/SMK-001/oracle/test_oracle.py"
            )
            self.assertTrue(evaluation.workspace_was_removed)
            self.assertEqual(result.terminal_action.value, "ACCEPT")
            self.assertEqual(result.attempts_executed, 1)
            self.assertTrue(state.facts["workspace"]["ephemeral_removed_before_evaluation"])

    def test_accepted_case_runs_requested_quality_after_functional_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            workspace = run_dir / "workspace"
            workspace.mkdir(parents=True)
            state = SkeletonRunState(request())
            initial = artifact()
            context = SimpleNamespace()
            generated = GenerateUnitResult(
                state, run_dir, context, initial, SimpleNamespace(workspace=workspace)
            )

            class Generation:
                def execute(self, value):
                    return generated

            class Evaluation:
                def execute(self, state, run_dir, context, artifact, oracle_ref):
                    state.status = RunStatus.SUCCEEDED
                    state.classification = RunClassification.ACCEPTED
                    return AlphaEvaluationResult(state, artifact, 1)

            quality_report = object()

            class Quality:
                def execute(self, state, actual_run_dir, actual_context, artifact, requests):
                    self.arguments = (state, actual_run_dir, actual_context, artifact, requests)
                    return SimpleNamespace(report=quality_report)

            quality = Quality()
            requests = (object(),)
            result = RunAlphaCaseService(Generation(), Evaluation(), quality).execute(
                request(), None, requests  # type: ignore[arg-type]
            )
            self.assertIs(result.quality_report, quality_report)
            self.assertEqual(quality.arguments[1:], (run_dir, context, initial, requests))

            workspace.mkdir()
            with self.assertRaisesRegex(ValueError, "no quality service"):
                RunAlphaCaseService(Generation(), Evaluation()).execute(
                    request(), None, requests  # type: ignore[arg-type]
                )


class RecordedCorrectionSequenceTests(unittest.TestCase):
    def test_recorded_agent_delivers_correction_only_when_requested(self) -> None:
        base = ROOT / "datasets/smoke/SMK-006/demo"
        agent = RecordedAgentAdapter(
            base / "analysis.json",
            base / "artifact-001.json",
            (base / "correction-001.json",),
        )
        analysis = agent.analyze(request())
        first = agent.generate(request(), analysis).artifact
        self.assertEqual(first.attempt, 1)
        feedback = build_correction_feedback(
            TestExecutionOutcome.TEST_ERROR,
            "",
            "ImportError: unavailable_symbol",
        )
        corrected = agent.correct(request(), first, feedback).artifact
        self.assertEqual(corrected.attempt, 2)
        self.assertEqual(corrected.relative_path, first.relative_path)
        self.assertNotEqual(corrected.content_sha256, first.content_sha256)
        with self.assertRaisesRegex(RecordedAgentError, "exhausted"):
            agent.correct(request(), corrected, feedback)


if __name__ == "__main__":
    unittest.main()
