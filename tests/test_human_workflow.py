from __future__ import annotations

import importlib.util
import tempfile
import unittest
import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from asef.adapters.context_file import FileQualityContextAdapter
from asef.adapters.langgraph_checkpoint import LangGraphHumanCheckpointAdapter
from asef.adapters.recorded_agent import RecordedAgentAdapter
from asef.adapters.run_store import JsonRunStore
from asef.adapters.workspace import EphemeralWorkspaceAdapter
from asef.application.complete_workflow import CompleteWorkflowService
from asef.application.generate_unit import GenerateUnitTestService
from asef.application.human_decision import HumanDecisionService
from asef.application.ports import ExecutionOutput
from asef.application.prepare_run import PrepareRunService
from asef.contracts import SkeletonRunRequest
from asef.outcomes import RunClassification, RunStatus
from asef.skills.unit import UnitSkill
from asef.cli import main
from unittest.mock import patch


HAS_LANGGRAPH = importlib.util.find_spec("langgraph") is not None
ANALYSIS = Path("tests/fixtures/cassettes/wf001_analysis_calculator_clarification.json")
ARTIFACT = Path("tests/fixtures/cassettes/wf001_unit_artifact_success.json")


class SuccessfulExecution:
    def execute(self, workspace: Path, snapshot: object) -> ExecutionOutput:
        del workspace, snapshot
        return ExecutionOutput(
            image="python@sha256:" + "a" * 64,
            command=("python", "-B", "-m", "unittest"),
            exit_code=0,
            duration_ms=10,
            stdout="",
            stderr="Ran 4 tests in 0.001s\n\nOK\n",
            tests=4,
            passed=4,
            failed=0,
        )


def request() -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="examples/context/walking-skeleton-context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title="Add integer inputs",
        requirement_description="Return the arithmetic sum; clarify the accepted numeric type",
    )


@unittest.skipUnless(HAS_LANGGRAPH, "workflow-langgraph optional extra is not installed")
class HumanWorkflowTests(unittest.TestCase):
    def services(self, root: Path):
        store = JsonRunStore(root)
        context = FileQualityContextAdapter()
        checkpoint = LangGraphHumanCheckpointAdapter()
        prepare = PrepareRunService(context, store)
        generation = GenerateUnitTestService(
            prepare,
            RecordedAgentAdapter(ANALYSIS, ARTIFACT),
            UnitSkill(),
            EphemeralWorkspaceAdapter(),
            store,
            checkpoint,
        )
        completion = CompleteWorkflowService(generation, SuccessfulExecution(), store)
        decisions = HumanDecisionService(
            context, checkpoint, generation, completion, store, root
        )
        return generation, decisions

    def test_ws002_resumes_same_run_without_repeating_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generation, _ = self.services(root)
            waiting = generation.execute(request())
            self.assertEqual(waiting.state.status, RunStatus.WAITING_FOR_CLARIFICATION)
            self.assertEqual(waiting.state.usage.model_calls, 1)
            self.assertFalse((waiting.run_dir / "workspace").exists())

            _, recreated_decisions = self.services(root)
            completed = recreated_decisions.resume(
                waiting.state.run_id, "Only signed integer inputs are accepted"
            )
            self.assertEqual(completed.state.run_id, waiting.state.run_id)
            self.assertEqual(completed.state.status, RunStatus.SUCCEEDED)
            self.assertEqual(completed.state.usage.model_calls, 2)
            self.assertEqual(len(completed.state.facts["human_decisions"]), 1)
            self.assertEqual(
                completed.state.facts["analysis"]["response_id"],
                "cassette-calculator-clarification-001",
            )

    def test_ws007_cancels_wait_without_artifact_or_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generation, _ = self.services(root)
            waiting = generation.execute(request())
            _, recreated_decisions = self.services(root)
            cancelled = recreated_decisions.cancel(waiting.state.run_id, "No longer required")
            self.assertEqual(cancelled.state.status, RunStatus.CANCELLED)
            self.assertEqual(
                cancelled.state.classification, RunClassification.CANCELLED_BY_USER
            )
            self.assertEqual(cancelled.state.usage.model_calls, 1)
            self.assertFalse((cancelled.run_dir / "workspace").exists())
            self.assertFalse((cancelled.run_dir / "artifacts").exists())
            self.assertTrue((cancelled.run_dir / "report.json").is_file())

    def test_public_wait_resume_and_cancel_exit_codes(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory, patch(
            "asef.cli.DockerUnitTestAdapter", return_value=SuccessfulExecution()
        ):
            wait_out, wait_err = StringIO(), StringIO()
            with redirect_stdout(wait_out), redirect_stderr(wait_err):
                wait_code = main(["wait", "--output", directory])
            waiting = json.loads(wait_out.getvalue())
            self.assertEqual(wait_code, 3)

            resume_out = StringIO()
            with redirect_stdout(resume_out):
                resume_code = main(
                    [
                        "resume",
                        "--output",
                        directory,
                        "--run-id",
                        waiting["run_id"],
                        "--answer",
                        "Only signed integer inputs",
                    ]
                )
            self.assertEqual(resume_code, 0)

        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            wait_out = StringIO()
            with redirect_stdout(wait_out):
                self.assertEqual(main(["wait", "--output", directory]), 3)
            run_id = json.loads(wait_out.getvalue())["run_id"]
            cancel_out = StringIO()
            with redirect_stdout(cancel_out):
                cancel_code = main(
                    [
                        "cancel",
                        "--output",
                        directory,
                        "--run-id",
                        run_id,
                        "--reason",
                        "No longer required",
                    ]
                )
            self.assertEqual(cancel_code, 130)


if __name__ == "__main__":
    unittest.main()
