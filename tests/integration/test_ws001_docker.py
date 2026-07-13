from __future__ import annotations

import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from uuid import uuid4

from asef.cli import main


@unittest.skipUnless(os.environ.get("ASEF_RUN_DOCKER_TESTS") == "1", "Docker tests disabled")
class Ws001DockerEndToEndTests(unittest.TestCase):
    def test_recorded_ws001_succeeds_with_reports(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        output = Path(".asef") / f"ws001-e2e-{uuid4().hex}"
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["run", "--output", str(output)])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(code, 0, stderr.getvalue())
        self.assertEqual(payload["status"], "SUCCEEDED")
        self.assertEqual(payload["classification"], "ACCEPTED")
        self.assertTrue(payload["report_path"].endswith("/report.md"))


if __name__ == "__main__":
    unittest.main()
