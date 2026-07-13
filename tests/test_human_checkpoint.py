from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from asef.adapters.langgraph_checkpoint import (
    HumanCheckpointError,
    LangGraphHumanCheckpointAdapter,
)


HAS_LANGGRAPH = importlib.util.find_spec("langgraph") is not None


@unittest.skipUnless(HAS_LANGGRAPH, "workflow-langgraph optional extra is not installed")
class LangGraphHumanCheckpointTests(unittest.TestCase):
    def test_resume_after_adapter_recreation_preserves_primitive_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "checkpoint.sqlite"
            payload = {"schema_version": "1.0.0", "analysis_response_id": "analysis-1"}
            LangGraphHumanCheckpointAdapter().pause("run-1", database, payload)
            result = LangGraphHumanCheckpointAdapter().resume("run-1", database, "Use integer inputs")
            self.assertEqual(result["payload"], payload)
            self.assertEqual(result["decision"]["action"], "resume")

    def test_cancel_is_an_explicit_checkpoint_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "checkpoint.sqlite"
            adapter = LangGraphHumanCheckpointAdapter()
            adapter.pause("run-cancel", database, {"kind": "clarification"})
            result = adapter.cancel("run-cancel", database, "User cancelled")
            self.assertEqual(result["decision"], {"action": "cancel", "reason": "User cancelled"})

    def test_missing_checkpoint_fails_safely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(HumanCheckpointError, "does not exist"):
                LangGraphHumanCheckpointAdapter().resume(
                    "missing", Path(directory) / "missing.sqlite", "answer"
                )

    def test_repeating_same_resume_returns_confirmed_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "checkpoint.sqlite"
            adapter = LangGraphHumanCheckpointAdapter()
            adapter.pause("idempotent", database, {"analysis_response_id": "one"})
            first = adapter.resume("idempotent", database, "Integer inputs")
            second = LangGraphHumanCheckpointAdapter().resume(
                "idempotent", database, "Integer inputs"
            )
            self.assertEqual(first, second)

    def test_corrupt_checkpoint_fails_safely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "checkpoint.sqlite"
            database.write_bytes(b"not-a-sqlite-database")
            with self.assertRaisesRegex(HumanCheckpointError, "cannot be resumed safely"):
                LangGraphHumanCheckpointAdapter().resume("corrupt", database, "answer")


if __name__ == "__main__":
    unittest.main()
