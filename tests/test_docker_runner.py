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
        self.assertIn("com.asef.managed=true", command)
        self.assertIn("com.asef.capability=generic", command)
        self.assertTrue(any(item.startswith("com.asef.execution=asef-") for item in command))
        self.assertEqual(command[-3:], ["python", "-c", "print('ok')"])

    def test_executor_receives_argument_list(self) -> None:
        captured: list[list[str]] = []

        def fake(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            captured.append(command)
            if command[:2] == ["docker", "ps"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            return subprocess.CompletedProcess(command, 0, "ok", "")

        with tempfile.TemporaryDirectory() as directory:
            result = DockerRunner(DockerPolicy("image@digest"), fake).run(
                Path(directory), ["python", "-V"]
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "ok")
        self.assertTrue(result.cleanup_succeeded)
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

    def test_writable_output_must_be_separate_and_inside_allowed_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            output = root / "output"
            workspace.mkdir()
            output.mkdir()
            runner = DockerRunner(DockerPolicy("image@digest", allowed_workspace_root=root))
            command = runner.build_command(workspace, ["python", "-V"], output_dir=output)
            self.assertTrue(any("dst=/workspace,readonly" in item for item in command))
            self.assertTrue(any("dst=/asef-output" in item for item in command))
            with self.assertRaisesRegex(ValueError, "cannot overlap"):
                runner.build_command(workspace, ["python", "-V"], output_dir=workspace)
            nested = workspace / "results"
            nested.mkdir()
            with self.assertRaisesRegex(ValueError, "cannot overlap"):
                runner.build_command(workspace, ["python", "-V"], output_dir=nested)
            outside = root.parent / "outside-output"
            outside.mkdir(exist_ok=True)
            try:
                with self.assertRaisesRegex(ValueError, "escapes allowed root"):
                    runner.build_command(workspace, ["python", "-V"], output_dir=outside)
            finally:
                outside.rmdir()

    def test_timeout_forces_container_cleanup(self) -> None:
        captured: list[list[str]] = []

        def fake(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            captured.append(command)
            if command[:3] == ["docker", "rm", "-f"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            if command[:2] == ["docker", "ps"]:
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
        self.assertTrue(result.cleanup_succeeded)

    def test_interrupt_and_executor_error_force_cleanup_and_repropagate(self) -> None:
        for raised in (KeyboardInterrupt(), RuntimeError("executor failed")):
            captured: list[list[str]] = []

            def fake(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                captured.append(command)
                if command[:3] == ["docker", "rm", "-f"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:2] == ["docker", "ps"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                raise raised

            with tempfile.TemporaryDirectory() as directory:
                runner = DockerRunner(DockerPolicy("image@digest"), fake)
                with self.subTest(error=type(raised).__name__), self.assertRaises(type(raised)):
                    runner.run(Path(directory), ["python", "-V"])
                self.assertIsNotNone(runner.last_cleanup)
                self.assertTrue(runner.last_cleanup.absent)
                self.assertEqual(captured[1][:3], ["docker", "rm", "-f"])

    def test_cleanup_failure_is_separate_from_container_exit(self) -> None:
        def fake(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            if command[:2] == ["docker", "run"]:
                return subprocess.CompletedProcess(command, 0, "ok", "")
            if command[:2] == ["docker", "ps"]:
                return subprocess.CompletedProcess(command, 0, "residual-id", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory:
            result = DockerRunner(DockerPolicy("image@digest"), fake).run(
                Path(directory), ["python", "-V"]
            )
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.cleanup_succeeded)
        self.assertEqual(result.cleanup_diagnostic, "CONTAINER_RESIDUAL")

    def test_managed_orphan_detection_uses_exact_ownership_labels(self) -> None:
        captured: list[list[str]] = []

        def fake(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            captured.append(command)
            return subprocess.CompletedProcess(command, 0, "first\nsecond\n", "")

        runner = DockerRunner(
            DockerPolicy("image@digest", capability_id="security"),
            fake,
        )
        self.assertEqual(runner.managed_container_ids(), ("first", "second"))
        self.assertEqual(
            captured[0],
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                "label=com.asef.managed=true",
                "--filter",
                "label=com.asef.capability=security",
            ],
        )


if __name__ == "__main__":
    unittest.main()
