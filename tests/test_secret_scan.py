from __future__ import annotations

import tempfile
import tarfile
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

    def test_sdist_content_is_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "data.txt"
            source.write_text("AKIA" + "C" * 16, encoding="utf-8")
            archive_path = root / "sample.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(source, arcname="package/data.txt")
            with redirect_stderr(StringIO()):
                self.assertEqual(main([str(archive_path)]), 1)

    def test_invalid_archive_and_oversized_file_are_visible_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = root / "invalid.whl"
            invalid.write_text("not a wheel", encoding="utf-8")
            oversized = root / "large.txt"
            with oversized.open("wb") as handle:
                handle.truncate(5 * 1024 * 1024 + 1)
            stderr = StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(main([str(invalid), str(oversized)]), 2)
            self.assertIn("archive is invalid", stderr.getvalue())
            self.assertIn("file size limit exceeded", stderr.getvalue())

    def test_sensitive_assignment_is_detected_without_printing_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.txt"
            secret = "private_" + "key=runtime-sentinel"
            path.write_text(secret, encoding="utf-8")
            stderr = StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(main([str(path)]), 1)
            self.assertIn("sensitive assignment", stderr.getvalue())
            self.assertNotIn("runtime-sentinel", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
