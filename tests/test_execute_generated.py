from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from asef.adapters.run_store import JsonRunStore
from asef.adapters.workspace import EphemeralWorkspaceAdapter
from asef.application.execute_generated import ExecuteGeneratedAttemptService
from asef.application.ports import ExecutionOutput, ResolvedQualityContext
from asef.context import QualityContext
from asef.contracts import SkeletonRunRequest, SkeletonRunState, TestExecutionOutcome, UnitTestArtifact


class Executor:
    def execute(self, workspace, snapshot):
        self.workspace = workspace
        self.snapshot = snapshot
        return ExecutionOutput(
            image="sha256:" + "f" * 64,
            command=("pytest", "tests_generated"),
            exit_code=0,
            duration_ms=1,
            stdout="1 passed",
            stderr="",
            tests=1,
            passed=1,
            failed=0,
            errors=0,
            skipped=0,
            outcome=TestExecutionOutcome.PASSED,
        )


def request():
    return SkeletonRunRequest(
        context_ref="examples/context/walking-skeleton-context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title="generated attempt",
        requirement_description="execute one immutable generated attempt",
    )


class ExecuteGeneratedAttemptServiceTests(unittest.TestCase):
    def test_stages_executes_and_persists_attempt_without_changing_sut(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sut = root / "sut"
            sut.mkdir()
            source = sut / "calculator.py"
            source.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            quality = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
            context = ResolvedQualityContext(quality.snapshot_for(request()), sut, ("calculator.py",))
            run_dir = root / "run"
            run_dir.mkdir()
            state = SkeletonRunState(request(), run_id="run")
            artifact = UnitTestArtifact(
                "tests_generated/test_add.py",
                "from calculator import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
                ("SCN-001",),
                1,
            )
            executor = Executor()
            result = ExecuteGeneratedAttemptService(
                EphemeralWorkspaceAdapter(), executor, JsonRunStore(root)
            ).execute(state, run_dir, context, artifact, 0)

            self.assertEqual(executor.workspace, run_dir / "attempt-workspaces/000/generated")
            self.assertTrue((executor.workspace / "tests_generated/test_add.py").is_file())
            self.assertEqual(result.normalized.stdout_ref.relative_path, "attempts/000/generated/stdout.txt")
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)

    def test_attempt_workspace_cannot_be_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sut = root / "sut"
            sut.mkdir()
            (sut / "calculator.py").write_text("VALUE = 1\n", encoding="utf-8")
            quality = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
            context = ResolvedQualityContext(quality.snapshot_for(request()), sut, ("calculator.py",))
            run_dir = root / "run"
            run_dir.mkdir()
            artifact = UnitTestArtifact("tests_generated/test_x.py", "def test_x():\n    assert True\n", ("SCN-001",))
            adapter = EphemeralWorkspaceAdapter()
            adapter.stage_attempt(run_dir, context, artifact, 0)
            with self.assertRaises(FileExistsError):
                adapter.stage_attempt(run_dir, context, artifact, 0)


if __name__ == "__main__":
    unittest.main()
