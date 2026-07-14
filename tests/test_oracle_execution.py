from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from asef.adapters.oracle_workspace import IsolatedOracleWorkspaceAdapter
from asef.adapters.run_store import JsonRunStore
from asef.application.execute_oracle import ExecuteOracleService
from asef.application.ports import ExecutionOutput, ResolvedQualityContext
from asef.context import QualityContext
from asef.contracts import ContextSnapshot, SkeletonRunRequest, TestExecutionOutcome


class RecordingExecutor:
    def __init__(self) -> None:
        self.workspace: Path | None = None

    def execute(self, workspace: Path, snapshot: ContextSnapshot) -> ExecutionOutput:
        self.workspace = workspace
        self.assert_snapshot = snapshot
        return ExecutionOutput(
            image=snapshot.image,
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


def snapshot() -> ContextSnapshot:
    context = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
    return context.snapshot_for(
        SkeletonRunRequest(
            context_ref="examples/context/walking-skeleton-context.json",
            system_id="calculator-service",
            requested_skill="unit",
            requirement_title="oracle",
            requirement_description="execute an isolated curated oracle",
        )
    )


class IsolatedOracleExecutionTests(unittest.TestCase):
    def test_oracle_is_materialized_only_in_its_own_workspace_and_executed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            sut_root = repository / "sut"
            (sut_root / "src/package").mkdir(parents=True)
            source = sut_root / "src/package/value.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            oracle = repository / "datasets/case/oracle/test_oracle.py"
            oracle.parent.mkdir(parents=True)
            oracle.write_text("from package.value import VALUE\n\ndef test_value():\n    assert VALUE == 1\n", encoding="utf-8")
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            context = ResolvedQualityContext(snapshot(), sut_root, ("src/package/value.py",))
            run_dir = root / "run"
            run_dir.mkdir()
            generation_workspace = run_dir / "workspace"
            generation_workspace.mkdir()

            executor = RecordingExecutor()
            result = ExecuteOracleService(
                IsolatedOracleWorkspaceAdapter(repository), executor, JsonRunStore(root)
            ).execute(
                SimpleNamespace(run_id="run", evidence_refs=[], facts={}),
                run_dir,
                context,
                context.snapshot,
                "datasets/case/oracle/test_oracle.py",
                0,
            )

            self.assertEqual(result.execution.outcome, TestExecutionOutcome.PASSED)
            self.assertEqual(executor.workspace, run_dir / "oracle-workspace")
            self.assertFalse((generation_workspace / "tests_generated/test_oracle.py").exists())
            staged_oracle = run_dir / "oracle-workspace/tests_generated/test_oracle.py"
            self.assertEqual(staged_oracle.read_bytes(), oracle.read_bytes())
            self.assertEqual(result.workspace.oracle_sha256, hashlib.sha256(oracle.read_bytes()).hexdigest())
            self.assertEqual(result.execution.stdout_ref.relative_path, "attempts/000/oracle/stdout.txt")
            self.assertTrue((run_dir / "attempts/000/oracle/execution.json").is_file())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), source_hash)

    def test_oracle_path_escape_and_oracle_inside_sut_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            sut_root = repository / "sut"
            sut_root.mkdir()
            source = sut_root / "source.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            context = ResolvedQualityContext(snapshot(), sut_root, ("source.py",))
            adapter = IsolatedOracleWorkspaceAdapter(repository)
            run_dir = repository / "run"
            run_dir.mkdir()

            with self.assertRaisesRegex(ValueError, "inside the repository"):
                adapter.stage_oracle(run_dir, context, "../oracle.py")
            with self.assertRaisesRegex(ValueError, "outside"):
                adapter.stage_oracle(run_dir, context, "sut/source.py")


if __name__ == "__main__":
    unittest.main()
