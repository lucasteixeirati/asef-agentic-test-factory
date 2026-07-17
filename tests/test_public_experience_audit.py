from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tools.public_experience_audit import _contained, _read_json_object, main


class PublicExperienceAuditTests(unittest.TestCase):
    def test_strict_json_rejects_duplicate_keys_and_non_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            duplicate = root / "duplicate.json"
            duplicate.write_text('{"status":"A","status":"B"}', encoding="utf-8")
            array = root / "array.json"
            array.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "strict JSON"):
                _read_json_object(duplicate, "fixture")
            with self.assertRaisesRegex(ValueError, "must contain an object"):
                _read_json_object(array, "fixture")

    def test_containment_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "escapes"):
                _contained(root, "../outside")

    def test_cli_failure_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing.json"
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        "--workspace",
                        str(root),
                        "--doctor-stdout",
                        str(missing),
                        "--run-stdout",
                        str(missing),
                        "--output",
                        str(root / "audit"),
                    ]
                )
            payload = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload, {"schema_version": "1.0.0", "passed": False, "error": "ValueError"})


if __name__ == "__main__":
    unittest.main()
