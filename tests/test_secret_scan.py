from __future__ import annotations

import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from tools.secret_scan import main


class SecretScanTests(unittest.TestCase):
    def test_clean_text_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            path.write_text('{"provider": "recorded"}', encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(main([str(path)]), 0)

    def test_key_signature_is_reported_without_printing_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.txt"
            path.write_text("sk-" + "A" * 24, encoding="utf-8")
            stderr = StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(main([str(path)]), 1)
            self.assertIn("OpenAI API key", stderr.getvalue())
            self.assertNotIn("A" * 24, stderr.getvalue())

    def test_wheel_content_is_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "sample.whl"
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr("package/data.txt", "ghp_" + "B" * 24)
            with redirect_stderr(StringIO()):
                self.assertEqual(main([str(wheel)]), 1)


if __name__ == "__main__":
    unittest.main()
