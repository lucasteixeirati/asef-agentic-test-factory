from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from asef.adapters.smoke_dataset import SmokeDatasetLoader
from asef.adapters.smoke_report_store import SmokeReportStore
from asef.application.run_alpha_case import AlphaCaseRunResult
from asef.application.smoke_runner import SmokeSuiteRunner
from asef.contracts import SkeletonRunState, UnitTestArtifact
from asef.cli import main
from asef.evaluation_contracts import EvaluationAction
from asef.smoke_contracts import SmokeComparison, SmokeTerminalAction


ROOT = Path(__file__).resolve().parents[1]


class ExpectedExecutor:
    def __init__(self, *, mismatch_case: str | None = None, error_case: str | None = None) -> None:
        self.mismatch_case = mismatch_case
        self.error_case = error_case
        self.calls: list[str] = []

    def execute(self, loaded, request):
        self.calls.append(loaded.case.case_id)
        if loaded.case.case_id == self.error_case:
            raise OSError("injected runner store failure")
        expected = loaded.demo.expected
        state = SkeletonRunState(request)
        state.status = expected.status
        state.classification = expected.classification
        state.usage.model_calls = expected.usage.model_calls.minimum
        state.usage.provider_retries = expected.usage.provider_retries.minimum
        state.usage.test_corrections = expected.usage.corrections.minimum
        if expected.oracle_executed:
            state.facts["oracle"] = {"sha256": "b" * 64}
        if expected.human_checkpoint_requested:
            state.facts["human_checkpoint"] = {"kind": "sut_defect_review"}
        terminal_action = (
            EvaluationAction(expected.action.value)
            if expected.action is not SmokeTerminalAction.NOT_REACHED
            else None
        )
        if loaded.case.case_id == self.mismatch_case:
            state.status = type(state.status).FAILED
            terminal_action = EvaluationAction.STOP
        run_dir = ROOT / request.output_root_ref / state.run_id
        return AlphaCaseRunResult(
            state=state,
            run_dir=run_dir,
            context=None,  # type: ignore[arg-type]
            artifact=None,
            attempts_executed=expected.usage.execution_attempts.minimum,
            terminal_action=terminal_action,
        )


class UnstableExecutor(ExpectedExecutor):
    def execute(self, loaded, request):
        outcome = super().execute(loaded, request)
        if loaded.case.case_id != "SMK-001":
            return outcome
        artifact = UnitTestArtifact(
            "tests_generated/test_unstable.py",
            f"def test_unstable():\n    assert {len(self.calls)} > 0\n",
            ("SCN-001",),
        )
        return AlphaCaseRunResult(
            outcome.state,
            outcome.run_dir,
            outcome.context,
            artifact,
            outcome.attempts_executed,
            outcome.terminal_action,
        )


class SmokeSuiteRunnerTests(unittest.TestCase):
    def runner(self, executor) -> SmokeSuiteRunner:
        return SmokeSuiteRunner(
            SmokeDatasetLoader(ROOT),
            executor,
            SmokeReportStore(ROOT),
            asef_version="0.1.0a3",
            environment="unit-test",
        )

    def test_negative_expected_results_are_matches_and_reports_reconcile(self) -> None:
        executor = ExpectedExecutor()
        with tempfile.TemporaryDirectory(dir=ROOT / ".asef") as output:
            result = self.runner(executor).run("datasets/smoke", Path(output), repeat=2)
            self.assertEqual((result.report.total, result.report.matched), (20, 20))
            self.assertEqual((result.report.mismatched, result.report.runner_errors), (0, 0))
            self.assertEqual(len(executor.calls), 20)
            self.assertTrue(result.suite_json.is_file())
            self.assertTrue(result.suite_markdown.is_file())
            payload = json.loads(result.suite_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["total"], 20)
            for case_id in {item.case_id for item in result.report.results}:
                fingerprints = {
                    item.semantic_fingerprint
                    for item in result.report.results
                    if item.case_id == case_id
                }
                self.assertEqual(len(fingerprints), 1)

    def test_mismatch_and_runner_error_do_not_stop_later_cases(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".asef") as output:
            mismatch_executor = ExpectedExecutor(mismatch_case="SMK-001")
            mismatch = self.runner(mismatch_executor).run(
                "datasets/smoke", Path(output), repeat=1
            )
            self.assertEqual(mismatch.report.mismatched, 1)
            self.assertEqual(len(mismatch_executor.calls), 10)

        with tempfile.TemporaryDirectory(dir=ROOT / ".asef") as output:
            error_executor = ExpectedExecutor(error_case="SMK-001")
            error = self.runner(error_executor).run("datasets/smoke", Path(output), repeat=1)
            self.assertEqual(error.report.runner_errors, 1)
            self.assertEqual(len(error_executor.calls), 10)
            self.assertIs(
                error.report.results[0].comparison,
                SmokeComparison.RUNNER_ERROR,
            )

    def test_fingerprint_instability_turns_both_repetitions_into_mismatches(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".asef") as output:
            result = self.runner(UnstableExecutor()).run(
                "datasets/smoke", Path(output), repeat=2
            )
            unstable = [item for item in result.report.results if item.case_id == "SMK-001"]
            self.assertEqual(
                [item.comparison for item in unstable],
                [SmokeComparison.MISMATCH, SmokeComparison.MISMATCH],
            )
            self.assertEqual(result.report.mismatched, 2)

    def test_invalid_arguments_fail_before_suite_directory_creation(self) -> None:
        executor = ExpectedExecutor()
        with tempfile.TemporaryDirectory(dir=ROOT / ".asef") as output:
            output_path = Path(output)
            with self.assertRaisesRegex(ValueError, "repeat"):
                self.runner(executor).run("datasets/smoke", output_path, repeat=4)
            self.assertEqual(list(output_path.iterdir()), [])
        with tempfile.TemporaryDirectory() as outside:
            with self.assertRaisesRegex(ValueError, "under the workspace .asef"):
                self.runner(executor).run("datasets/smoke", Path(outside))


class SmokeCliTests(unittest.TestCase):
    def execute(self, executor, output: Path) -> tuple[int, dict[str, object], str]:
        stdout, stderr = StringIO(), StringIO()
        with (
            patch("asef.cli.SmokeCaseExecutorAdapter", return_value=executor),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            code = main(
                [
                    "smoke",
                    "--dataset-root",
                    "datasets/smoke",
                    "--context",
                    "examples/context/python-alpha-smoke-context.json",
                    "--output",
                    str(output),
                ]
            )
        return code, json.loads(stdout.getvalue()), stderr.getvalue()

    def test_public_exit_matrix_uses_suite_result_not_negative_case_statuses(self) -> None:
        cases = (
            (ExpectedExecutor(), 0, "ACCEPTED"),
            (ExpectedExecutor(mismatch_case="SMK-001"), 4, "SMOKE_MISMATCH"),
            (ExpectedExecutor(error_case="SMK-001"), 7, "INFRASTRUCTURE_ERROR"),
        )
        for executor, expected_code, classification in cases:
            with self.subTest(code=expected_code):
                with tempfile.TemporaryDirectory(dir=ROOT / ".asef") as output:
                    code, payload, stderr = self.execute(executor, Path(output))
                    self.assertEqual(code, expected_code)
                    self.assertEqual(payload["classification"], classification)
                    self.assertEqual(payload["total"], 10)
                    self.assertEqual(stderr, "")

    def test_repeat_validation_returns_two_without_creating_a_suite(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".asef") as output:
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(["smoke", "--output", output, "--repeat", "4"])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(stdout.getvalue())["status"], "REJECTED")
            self.assertIn("repeat", stderr.getvalue())
            self.assertEqual(list(Path(output).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
