from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from asef.adapters.run_store import JsonRunStore
from asef.application.ports import ExecutionOutput
from asef.contracts import ContractValidationError, TestExecutionOutcome
from asef.contracts import UnitTestArtifact


IMAGE = "sha256:" + "d" * 64


def output(label: str, outcome: TestExecutionOutcome = TestExecutionOutcome.PASSED) -> ExecutionOutput:
    return ExecutionOutput(
        image=IMAGE,
        command=("python", "-m", "pytest"),
        exit_code=0,
        duration_ms=10,
        stdout=f"{label} stdout",
        stderr=f"{label} stderr",
        tests=1,
        passed=1,
        failed=0,
        errors=0,
        skipped=0,
        tool_id="pytest",
        tool_version="8.3.3",
        outcome=outcome,
        raw_result_content=f"<{label}/>",
        raw_result_filename="pytest-junit.xml",
        raw_result_media_type="application/junit+xml",
    )


class ImmutableAttemptStoreTests(unittest.TestCase):
    def test_generated_and_oracle_evidence_are_namespaced_and_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "run-1"
            run_dir.mkdir()
            store = JsonRunStore(root)
            state = SimpleNamespace(run_id="run-1")

            generated = store.save_attempt_execution(state, output("generated"), 0, "generated")
            oracle = store.save_attempt_execution(state, output("oracle"), 0, "oracle")

            self.assertEqual(generated.stdout_ref.relative_path, "attempts/000/generated/stdout.txt")
            self.assertEqual(oracle.stdout_ref.relative_path, "attempts/000/oracle/stdout.txt")
            self.assertEqual(
                (run_dir / generated.stdout_ref.relative_path).read_text(encoding="utf-8"),
                "generated stdout",
            )
            self.assertEqual(
                (run_dir / oracle.stdout_ref.relative_path).read_text(encoding="utf-8"),
                "oracle stdout",
            )
            persisted = json.loads(
                (run_dir / "attempts/000/oracle/execution.json").read_text(encoding="utf-8")
            )
            self.assertEqual(persisted["raw_result_ref"]["relative_path"], "attempts/000/oracle/pytest-junit.xml")

    def test_existing_attempt_role_cannot_be_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "run-1").mkdir()
            store = JsonRunStore(root)
            state = SimpleNamespace(run_id="run-1")
            store.save_attempt_execution(state, output("first"), 1, "generated")
            before = (root / "run-1/attempts/001/generated/stdout.txt").read_bytes()

            with self.assertRaisesRegex(FileExistsError, "already exists"):
                store.save_attempt_execution(state, output("replacement"), 1, "generated")
            self.assertEqual((root / "run-1/attempts/001/generated/stdout.txt").read_bytes(), before)

    def test_invalid_identity_or_contract_leaves_no_partial_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "run-1").mkdir()
            store = JsonRunStore(root)
            state = SimpleNamespace(run_id="run-1")

            for attempt, role in ((-1, "generated"), (0, "unknown")):
                with self.subTest(attempt=attempt, role=role), self.assertRaises(ValueError):
                    store.save_attempt_execution(state, output("invalid"), attempt, role)
            invalid = replace(output("invalid"), image="mutable:latest")
            with self.assertRaises(ContractValidationError):
                store.save_attempt_execution(state, invalid, 2, "generated")
            attempts = root / "run-1/attempts"
            self.assertFalse((attempts / "002/generated").exists())
            self.assertEqual(list((attempts / "002").glob(".*.tmp")), [])

    def test_artifact_and_oracle_sources_are_preserved_with_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "run-1").mkdir()
            store = JsonRunStore(root)
            state = SimpleNamespace(run_id="run-1")
            artifact = UnitTestArtifact(
                "tests_generated/test_x.py", "def test_x():\n    assert True\n", ("SCN-001",), 2
            )
            artifact_refs = store.save_attempt_artifact(
                state, artifact, {"schema_version": "1.0.0", "status": "ACCEPTED"}
            )
            oracle_content = "def test_oracle():\n    assert True\n"
            import hashlib
            oracle_hash = hashlib.sha256(oracle_content.encode("utf-8")).hexdigest()
            oracle_refs = store.save_oracle_evidence(
                state, "datasets/case/oracle.py", oracle_content.encode("utf-8"), oracle_hash
            )
            self.assertTrue((root / "run-1" / artifact_refs[0].relative_path).is_file())
            self.assertTrue((root / "run-1" / artifact_refs[1].relative_path).is_file())
            self.assertEqual((root / "run-1" / oracle_refs[0].relative_path).read_text(encoding="utf-8"), oracle_content)
            with self.assertRaises(FileExistsError):
                store.save_oracle_evidence(state, "datasets/case/oracle.py", oracle_content.encode("utf-8"), oracle_hash)


if __name__ == "__main__":
    unittest.main()
