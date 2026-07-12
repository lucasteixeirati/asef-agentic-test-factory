from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from asef.adapters.docker import DockerPolicy, DockerRunner, _truncate


class DockerRunnerTests(unittest.TestCase):
    def test_command_contains_security_controls_and_no_shell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = DockerRunner(DockerPolicy(image="python@example"))
            command = runner.build_command(Path(directory), ["python", "-c", "print('ok')"])

        self.assertEqual(command[:2], ["docker", "run"])
        self.assertIn("none", command)
        self.assertIn("--read-only", command)
        self.assertIn("ALL", command)
        self.assertIn("no-new-privileges:true", command)
        self.assertIn("65534:65534", command)
        self.assertIn("--memory-swap", command)
        self.assertEqual(command[-3:], ["python", "-c", "print('ok')"])

    def test_executor_receives_argument_list(self) -> None:
        captured: list[list[str]] = []

        def fake(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            captured.append(command)
            return subprocess.CompletedProcess(command, 0, "ok", "")

        with tempfile.TemporaryDirectory() as directory:
            result = DockerRunner(DockerPolicy("image@digest"), fake).run(
                Path(directory), ["python", "-V"]
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "ok")
        self.assertEqual(captured[0][0], "docker")

    def test_output_is_truncated_by_bytes(self) -> None:
        output, truncated = _truncate("á" * 10, 12)
        self.assertTrue(truncated)
        self.assertIn("truncated", output)

    def test_workspace_must_stay_inside_allowed_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            allowed = root / "allowed"
            allowed.mkdir()
            runner = DockerRunner(
                DockerPolicy(image="python@example", allowed_workspace_root=allowed)
            )
            with self.assertRaisesRegex(ValueError, "escapes allowed root"):
                runner.build_command(root, ["python", "-V"])

    def test_timeout_forces_container_cleanup(self) -> None:
        captured: list[list[str]] = []

        def fake(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            captured.append(command)
            if command[:3] == ["docker", "rm", "-f"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            raise subprocess.TimeoutExpired(command, 1, output="partial")

        with tempfile.TemporaryDirectory() as directory:
            result = DockerRunner(DockerPolicy("image@digest", timeout_seconds=1), fake).run(
                Path(directory), ["python", "-c", "pass"]
            )

        self.assertTrue(result.timed_out)
        self.assertEqual(result.exit_code, 124)
        self.assertEqual(result.stdout, "partial")
        self.assertEqual(captured[1], ["docker", "rm", "-f", result.container_name])


if __name__ == "__main__":
    unittest.main()
