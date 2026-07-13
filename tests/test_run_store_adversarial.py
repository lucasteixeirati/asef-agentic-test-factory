from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from asef.adapters.run_store import JsonRunStore


class RunStoreAdversarialTests(unittest.TestCase):
    def test_run_id_cannot_escape_or_select_nested_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonRunStore(Path(directory))
            for run_id in ("", "..", "../outside", "nested/run", "nested\\run"):
                with self.subTest(run_id=run_id), self.assertRaisesRegex(ValueError, "invalid run_id"):
                    store.load_state(run_id)

    def test_missing_corrupt_and_non_object_state_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = JsonRunStore(root)
            run = root / "run-1"
            run.mkdir()
            with self.assertRaisesRegex(ValueError, "cannot load state.json"):
                store.load_state("run-1")
            (run / "state.json").write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot load state.json"):
                store.load_state("run-1")
            (run / "state.json").write_text(json.dumps([]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must contain an object"):
                store.load_state("run-1")

    def test_report_markdown_escapes_control_characters(self) -> None:
        value = "unsafe | `code` <tag>\nnext"
        self.assertEqual(
            JsonRunStore._markdown_text(value),
            "unsafe \\| \\`code\\` &lt;tag&gt; next",
        )

    def test_corrupt_event_stream_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text("not-json\n", encoding="utf-8")
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "corrupt events.jsonl"):
                JsonRunStore._append_new_events(path, [{"event": "NEW"}])
            self.assertEqual(path.read_bytes(), before)

    def test_json_write_is_atomic_and_leaves_no_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "value.json"
            JsonRunStore._write_json(target, {"value": 1})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"value": 1})
            self.assertEqual([item for item in root.iterdir() if item != target], [])
