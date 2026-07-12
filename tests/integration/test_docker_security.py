from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from asef.adapters.docker import DockerPolicy, DockerRunner


IMAGE = (
    "python@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0"
)


@unittest.skipUnless(os.environ.get("ASEF_RUN_DOCKER_TESTS") == "1", "Docker tests disabled")
class DockerSecurityIntegrationTests(unittest.TestCase):
    workspace_path = Path(".asef/docker-test-workspace")

    @classmethod
    def setUpClass(cls) -> None:
        cls.workspace_path.mkdir(parents=True, exist_ok=True)

    def runner(self) -> DockerRunner:
        return DockerRunner(
            DockerPolicy(
                image=IMAGE,
                allowed_workspace_root=Path(".asef"),
                timeout_seconds=20,
            )
        )

    def test_identity_secrets_and_workspace(self) -> None:
        result = self.runner().run(
            self.workspace_path,
            [
                "python",
                "-c",
                (
                    "import json,os; print(json.dumps({"
                    "'uid':os.getuid(),"
                    "'api_key_visible':bool(os.getenv('OPENAI_API_KEY'))," 
                    "'workspace_writable':os.access('/workspace',os.W_OK)}))"
                ),
            ],
        )
        self.assertEqual(result.exit_code, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["uid"], 65534)
        self.assertFalse(payload["api_key_visible"])
        self.assertFalse(payload["workspace_writable"])

    def test_network_is_blocked(self) -> None:
        result = self.runner().run(
            self.workspace_path,
            [
                "python",
                "-c",
                (
                    "import json,socket; blocked=False\n"
                    "try: socket.create_connection(('1.1.1.1',53),timeout=1)\n"
                    "except OSError: blocked=True\n"
                    "print(json.dumps({'blocked':blocked}))"
                ),
            ],
        )
        self.assertEqual(result.exit_code, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["blocked"])

    def test_root_filesystem_is_read_only(self) -> None:
        result = self.runner().run(
            self.workspace_path,
            [
                "python",
                "-c",
                (
                    "import json; blocked=False\n"
                    "try: open('/forbidden','w').write('x')\n"
                    "except OSError: blocked=True\n"
                    "print(json.dumps({'blocked':blocked}))"
                ),
            ],
        )
        self.assertEqual(result.exit_code, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["blocked"])

    def test_timeout_is_classified_and_container_is_removed(self) -> None:
        runner = DockerRunner(
            DockerPolicy(
                image=IMAGE,
                allowed_workspace_root=Path(".asef"),
                timeout_seconds=1,
            )
        )
        result = runner.run(
            self.workspace_path,
            ["python", "-c", "import time; time.sleep(30)"],
        )
        self.assertTrue(result.timed_out)
        self.assertEqual(result.exit_code, 124)
        inspection = runner.executor(
            ["docker", "ps", "-aq", "--filter", f"name=^{result.container_name}$"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        self.assertEqual(inspection.stdout.strip(), "")

    def test_memory_limit_stops_excessive_allocation(self) -> None:
        runner = DockerRunner(
            DockerPolicy(
                image=IMAGE,
                allowed_workspace_root=Path(".asef"),
                memory="64m",
                timeout_seconds=20,
            )
        )
        result = runner.run(
            self.workspace_path,
            ["python", "-c", "x=bytearray(256*1024*1024); print(len(x))"],
        )
        self.assertEqual(result.exit_code, 137, result.stderr)

    def test_pid_limit_blocks_process_fanout(self) -> None:
        runner = DockerRunner(
            DockerPolicy(
                image=IMAGE,
                allowed_workspace_root=Path(".asef"),
                pids_limit=16,
                timeout_seconds=20,
            )
        )
        script = (
            "import json,subprocess,sys\n"
            "children=[]; blocked=False\n"
            "try:\n"
            "  for _ in range(64):\n"
            "    children.append(subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)']))\n"
            "except (OSError,BlockingIOError): blocked=True\n"
            "finally:\n"
            "  [child.terminate() for child in children]\n"
            "  [child.wait() for child in children]\n"
            "print(json.dumps({'blocked':blocked,'spawned':len(children)}))"
        )
        result = runner.run(self.workspace_path, ["python", "-c", script])
        self.assertEqual(result.exit_code, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["blocked"])
        self.assertLess(payload["spawned"], 64)

    def test_parent_path_is_rejected_before_docker(self) -> None:
        with self.assertRaisesRegex(ValueError, "escapes allowed root"):
            self.runner().build_command(Path(".asef") / "..", ["python", "-V"])

    def test_symlink_escape_is_rejected_before_docker(self) -> None:
        link = Path(".asef/docker-escape-link")
        try:
            link.symlink_to(Path.cwd(), target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"host cannot create directory symlink: {exc}")
        try:
            with self.assertRaisesRegex(ValueError, "escapes allowed root"):
                self.runner().build_command(link, ["python", "-V"])
        finally:
            link.unlink(missing_ok=True)

    def test_real_stdout_and_stderr_are_truncated(self) -> None:
        runner = DockerRunner(
            DockerPolicy(
                image=IMAGE,
                allowed_workspace_root=Path(".asef"),
                timeout_seconds=20,
                stdout_limit_bytes=256,
                stderr_limit_bytes=256,
            )
        )
        result = runner.run(
            self.workspace_path,
            [
                "python",
                "-c",
                "import sys; print('o'*2048); print('e'*2048,file=sys.stderr)",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.stdout_truncated)
        self.assertTrue(result.stderr_truncated)
        self.assertLessEqual(len(result.stdout.encode("utf-8")), 256)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 256)


if __name__ == "__main__":
    unittest.main()
