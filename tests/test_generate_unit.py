from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from asef.adapters.context_file import FileQualityContextAdapter
from asef.adapters.recorded_agent import RecordedAgentAdapter
from asef.adapters.run_store import JsonRunStore
from asef.adapters.workspace import EphemeralWorkspaceAdapter
from asef.application.generate_unit import GenerateUnitTestService
from asef.application.ports import AnalysisResult, GeneratedArtifactResult
from asef.application.prepare_run import PrepareRunService
from asef.cli import main
from asef.contracts import SkeletonRunRequest, UnitTestArtifact
from asef.outcomes import RunClassification, RunStatus
from asef.skills.unit import UnitSkill, UnitSkillPolicyError


ANALYSIS = Path("tests/fixtures/cassettes/wf001_analysis_success.json")
ARTIFACT = Path("tests/fixtures/cassettes/wf001_unit_artifact_success.json")
SUT = Path("examples/calculator/calculator.py")


def request() -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="examples/context/walking-skeleton-context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title="Add integers",
        requirement_description="Return the arithmetic sum of two integers",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GenerateUnitTestServiceTests(unittest.TestCase):
    def service(self, root: Path, agent: object | None = None) -> GenerateUnitTestService:
        store = JsonRunStore(root)
        return GenerateUnitTestService(
            PrepareRunService(FileQualityContextAdapter(), store),
            agent or RecordedAgentAdapter(ANALYSIS, ARTIFACT),
            UnitSkill(),
            EphemeralWorkspaceAdapter(),
            store,
        )

    def test_recorded_generation_passes_policy_and_preserves_original_sut(self) -> None:
        before = sha256(SUT)
        with tempfile.TemporaryDirectory() as directory:
            result = self.service(Path(directory)).execute(request())
            self.assertEqual(result.state.status, RunStatus.STATIC_VALIDATION)
            self.assertEqual(result.state.usage.model_calls, 2)
            self.assertEqual(result.state.usage.input_tokens, 192)
            self.assertIsNotNone(result.workspace)
            self.assertEqual(sha256(SUT), before)
            run_dir = result.run_dir
            self.assertTrue((run_dir / "workspace/calculator.py").is_file())
            self.assertTrue(
                (run_dir / "workspace/tests_generated/test_calculator.py").is_file()
            )
            self.assertTrue(
                (run_dir / "artifacts/attempt-001/tests_generated/test_calculator.py").is_file()
            )
            validation = json.loads(
                (run_dir / "results/static-validation.json").read_text(encoding="utf-8")
            )
            self.assertEqual(validation["status"], "PASSED")
            self.assertEqual(validation["test_methods"], 4)

    def test_path_escape_is_policy_blocked_without_workspace(self) -> None:
        class EscapeAgent:
            def analyze(self, request: SkeletonRunRequest) -> AnalysisResult:
                del request
                return AnalysisResult(("add",), ("wrong sum",), ("positive",), False, "fake", "a")

            def generate(self, request: SkeletonRunRequest, analysis: AnalysisResult) -> GeneratedArtifactResult:
                del request, analysis
                return GeneratedArtifactResult(
                    UnitTestArtifact("../escape.py", "def test_x():\n    pass\n", ("SCN-001",)),
                    "fake",
                    "g",
                )

        with tempfile.TemporaryDirectory() as directory:
            result = self.service(Path(directory), EscapeAgent()).execute(request())
            self.assertEqual(result.state.status, RunStatus.POLICY_BLOCKED)
            self.assertEqual(result.state.classification, RunClassification.POLICY_VIOLATION)
            self.assertFalse((result.run_dir / "workspace").exists())
            self.assertTrue((result.run_dir / "artifacts/rejected/attempt-001.txt").is_file())
            self.assertFalse((result.run_dir / "artifacts/escape.py").exists())
            validation = json.loads(
                (result.run_dir / "results/static-validation.json").read_text(encoding="utf-8")
            )
            self.assertEqual(validation["status"], "POLICY_BLOCKED")

    def test_clarification_stops_before_generation_and_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(
                Path(directory),
                RecordedAgentAdapter(
                    Path("tests/fixtures/cassettes/wf001_analysis_clarification.json"), ARTIFACT
                ),
            )
            result = service.execute(request())
            self.assertEqual(result.state.status, RunStatus.WAITING_FOR_CLARIFICATION)
            self.assertEqual(result.state.classification, RunClassification.WAITING_HUMAN)
            self.assertEqual(result.state.usage.model_calls, 1)
            self.assertIsNone(result.artifact)
            self.assertFalse((result.run_dir / "workspace").exists())


class UnitSkillTests(unittest.TestCase):
    def artifact(self, content: str) -> UnitTestArtifact:
        return UnitTestArtifact("tests_generated/test_x.py", content, ("SCN-001",))

    def test_forbidden_import_is_rejected(self) -> None:
        with self.assertRaisesRegex(UnitSkillPolicyError, "forbidden imports"):
            UnitSkill().validate(self.artifact("import os\n\ndef test_x():\n    pass\n"))

    def test_forbidden_builtin_call_is_rejected(self) -> None:
        with self.assertRaisesRegex(UnitSkillPolicyError, "forbidden call"):
            UnitSkill().validate(self.artifact("def test_x():\n    open('x')\n"))

    def test_forbidden_attribute_call_is_rejected(self) -> None:
        with self.assertRaisesRegex(UnitSkillPolicyError, "forbidden call"):
            UnitSkill().validate(
                self.artifact("def test_x():\n    thing.open('x')\n")
            )

    def test_invalid_syntax_is_rejected(self) -> None:
        with self.assertRaisesRegex(UnitSkillPolicyError, "invalid Python syntax"):
            UnitSkill().validate(self.artifact("def test_x(:\n    pass\n"))


class GenerateCliTests(unittest.TestCase):
    def test_generate_command_returns_static_validation_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(["generate", "--output", directory])
            payload = json.loads(stdout.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "STATIC_VALIDATION")
            self.assertEqual(payload["ready_for"], "test_execution")
            self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
