from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from asef.adapters.context_file import FileQualityContextAdapter
from asef.adapters.docker_execution import DockerUnitTestAdapter
from asef.adapters.recorded_agent import RecordedAgentAdapter
from asef.adapters.run_store import JsonRunStore
from asef.adapters.workspace import EphemeralWorkspaceAdapter
from asef.application.complete_workflow import CompleteWorkflowService
from asef.application.generate_unit import GenerateUnitTestService
from asef.application.ports import ExecutionOutput
from asef.application.prepare_run import PrepareRunService
from asef.context import QualityContext
from asef.contracts import SkeletonRunRequest, TestExecutionOutcome
from asef.outcomes import RunClassification, RunStatus
from asef.skills.unit import UnitSkill


def request() -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="examples/context/walking-skeleton-context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title="Add integers",
        requirement_description="Return the arithmetic sum of two integers",
    )


class FakeExecutionPort:
    def __init__(self, output: ExecutionOutput | Exception) -> None:
        self.output = output

    def execute(self, workspace: Path, snapshot: object) -> ExecutionOutput:
        del workspace, snapshot
        if isinstance(self.output, Exception):
            raise self.output
        return self.output


def output(*, exit_code: int = 0, tests: int = 4, passed: int = 4, failed: int = 0) -> ExecutionOutput:
    return ExecutionOutput(
        image="python@sha256:" + "a" * 64,
        command=("python", "-B", "-m", "unittest"),
        exit_code=exit_code,
        duration_ms=25,
        stdout="",
        stderr=f"Ran {tests} tests in 0.001s\n\n{'OK' if exit_code == 0 else 'FAILED'}\n",
        tests=tests,
        passed=passed,
        failed=failed,
    )


class CompleteWorkflowServiceTests(unittest.TestCase):
    def service(self, root: Path, execution: ExecutionOutput | Exception) -> CompleteWorkflowService:
        store = JsonRunStore(root)
        prepare = PrepareRunService(FileQualityContextAdapter(), store)
        generation = GenerateUnitTestService(
            prepare,
            RecordedAgentAdapter(
                Path("tests/fixtures/cassettes/wf001_analysis_success.json"),
                Path("tests/fixtures/cassettes/wf001_unit_artifact_success.json"),
            ),
            UnitSkill(),
            EphemeralWorkspaceAdapter(),
            store,
        )
        return CompleteWorkflowService(generation, FakeExecutionPort(execution), store)

    def test_success_closes_ws001_and_writes_consistent_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.service(Path(directory), output()).execute(request())
            self.assertEqual(result.state.status, RunStatus.SUCCEEDED)
            self.assertEqual(result.state.classification, RunClassification.ACCEPTED)
            self.assertEqual(result.report_path, "report.md")
            self.assertEqual(len(result.state.evidence_refs), 3)
            report = json.loads((result.run_dir / "report.json").read_text(encoding="utf-8"))
            state = json.loads((result.run_dir / "state.json").read_text(encoding="utf-8"))
            manifest = json.loads((result.run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual({report["status"], state["status"], manifest["status"]}, {"SUCCEEDED"})
            self.assertTrue(report["functional_result"]["accepted"])
            self.assertEqual(report["schema_version"], "1.0.0")
            self.assertEqual(manifest["reports"]["json"]["relative_path"], "report.json")
            self.assertEqual(manifest["reports"]["markdown"]["relative_path"], "report.md")
            self.assertTrue((result.run_dir / "results/execution.json").is_file())
            self.assertTrue((result.run_dir / "report.md").is_file())

    def test_report_serializes_quality_as_evidence_without_changing_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.service(root, output()).execute(request())
            result.state.facts["quality"] = {
                "schema_version": "1.0.0",
                "complete": True,
                "duration_ms": 50,
                "observations": [{"capability": "coverage", "status": "COMPLETED"}],
                "limitations": ["evidence only"],
            }
            JsonRunStore(root).save_report(
                result.state, None, result.state.facts["evaluation"]
            )
            report = json.loads((result.run_dir / "report.json").read_text(encoding="utf-8"))
            markdown = (result.run_dir / "report.md").read_text(encoding="utf-8")
            self.assertTrue(report["quality"][0]["complete"])
            self.assertEqual(report["quality"][0]["capability"], "coverage")
            self.assertIn("## Quality capabilities", markdown)
            self.assertIn("evidence only; no universal threshold", markdown)
            self.assertEqual(
                (report["status"], report["classification"]),
                ("SUCCEEDED", "ACCEPTED"),
            )

    def test_failed_tests_are_a_functional_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.service(
                Path(directory), output(exit_code=1, tests=4, passed=3, failed=1)
            ).execute(request())
            self.assertEqual(result.state.status, RunStatus.FAILED)
            self.assertEqual(result.state.classification, RunClassification.TEST_FAILURE)
            self.assertFalse(result.state.facts["evaluation"]["accepted"])

    def test_missing_docker_is_an_infrastructure_failure_with_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.service(Path(directory), FileNotFoundError("docker unavailable")).execute(
                request()
            )
            self.assertEqual(result.state.status, RunStatus.FAILED)
            self.assertEqual(result.state.classification, RunClassification.INFRASTRUCTURE_ERROR)
            self.assertTrue((result.run_dir / "report.json").is_file())
            self.assertFalse((result.run_dir / "results/execution.json").exists())

    def test_docker_engine_exit_code_is_infrastructure_not_test_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.service(
                Path(directory), output(exit_code=125, tests=0, passed=0, failed=0)
            ).execute(request())
            self.assertEqual(result.state.classification, RunClassification.INFRASTRUCTURE_ERROR)

    def test_pytest_collection_error_is_classified_as_test_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            execution = output(exit_code=2, tests=1, passed=0, failed=0)
            execution = ExecutionOutput(
                **{
                    field: getattr(execution, field)
                    for field in ("image", "command", "exit_code", "duration_ms", "stdout", "stderr", "tests", "passed", "failed")
                },
                errors=1,
                skipped=0,
                tool_id="pytest",
                tool_version="8.3.3",
                outcome=TestExecutionOutcome.TEST_ERROR,
                raw_result_content='<testsuite tests="1" errors="1"/>',
                raw_result_filename="pytest-junit.xml",
                raw_result_media_type="application/junit+xml",
            )
            result = self.service(Path(directory), execution).execute(request())
            self.assertEqual(result.state.classification, RunClassification.TEST_ERROR)
            self.assertEqual(result.execution.outcome, TestExecutionOutcome.TEST_ERROR)
            self.assertEqual(len(result.state.evidence_refs), 4)
            self.assertTrue((result.run_dir / "results/pytest-junit.xml").is_file())

    def test_skipped_generated_test_is_not_silently_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            execution = output(tests=2, passed=1)
            execution = ExecutionOutput(
                **{
                    field: getattr(execution, field)
                    for field in ("image", "command", "exit_code", "duration_ms", "stdout", "stderr", "tests", "passed", "failed")
                },
                errors=0,
                skipped=1,
                tool_id="pytest",
                tool_version="8.3.3",
                outcome=TestExecutionOutcome.PASSED,
            )
            result = self.service(Path(directory), execution).execute(request())
            self.assertEqual(result.state.classification, RunClassification.TEST_FAILURE)
            self.assertFalse(result.state.facts["evaluation"]["accepted"])


class DockerUnitTestAdapterTests(unittest.TestCase):
    def test_normalizes_unittest_output_and_uses_snapshot_image(self) -> None:
        commands: list[list[str]] = []

        def executor(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            del kwargs
            commands.append(command)
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="",
                stderr="Ran 4 tests in 0.001s\n\nOK\n",
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            context = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
            snapshot = context.snapshot_for(request())
            result = DockerUnitTestAdapter(root, executor).execute(workspace, snapshot)
            self.assertEqual((result.tests, result.passed, result.failed), (4, 4, 0))
            self.assertEqual(result.image, snapshot.image)
            self.assertIn(snapshot.image, commands[0])
            self.assertIn("--network", commands[0])

    def test_last_unittest_count_wins_over_spoofed_output(self) -> None:
        output_text = "Ran 99 tests in 0.001s\nRan 0 tests in 0.001s\nOK\n"
        self.assertEqual(DockerUnitTestAdapter._count_tests(output_text), 0)


if __name__ == "__main__":
    unittest.main()
