from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from asef.adapters.docker_api_fixture import DockerApiFixtureExecutor
from asef.api_contracts import ApiAssertion, ApiScenario, ApiTestPlan


class DockerApiFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        Path(".asef").mkdir(exist_ok=True)

    @staticmethod
    def _plan() -> ApiTestPlan:
        return ApiTestPlan(
            "API-DOCKER-001",
            "http://127.0.0.1:8765",
            (ApiScenario("SCN-001", "health", "GET", "/health", ApiAssertion(200, {"status": "ok"})),),
        )

    def _workspace(self, root: Path) -> tuple[Path, Path]:
        return DockerApiFixtureExecutor.stage(self._plan(), root)

    def test_runs_with_networkless_readonly_container_policy_and_normalizes_result(self) -> None:
        commands: list[list[str]] = []

        def fake(command, **kwargs):
            del kwargs
            commands.append(command)
            if command[:2] == ["docker", "run"]:
                output_mount = next(item for item in command if item.endswith("dst=/asef-output"))
                source = output_mount.split(",src=", 1)[1].rsplit(",dst=", 1)[0]
                payload = {
                    "schema_version": "1.0.0",
                    "plan_id": "API-DOCKER-001",
                    "status": "PASSED",
                    "tests": 1,
                    "passed": 1,
                    "failed": 0,
                    "errors": 0,
                    "scenarios": [{
                        "scenario_id": "SCN-001", "status": "PASSED", "observed_status": 200,
                        "duration_ms": 2, "response_bytes": 16, "diagnostic_code": None,
                    }],
                }
                (Path(source) / "api-result.json").write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = self._workspace(root)
            result = DockerApiFixtureExecutor(root, fake).execute(workspace, output)
        docker_run = commands[0]
        self.assertEqual("PASSED", result.status)
        self.assertEqual("none", docker_run[docker_run.index("--network") + 1])
        self.assertIn("--read-only", docker_run)
        self.assertIn("no-new-privileges:true", docker_run)
        self.assertIn("com.asef.capability=backend-api-fixture", docker_run)

    def test_invalid_native_result_fails_closed(self) -> None:
        def fake(command, **kwargs):
            del kwargs
            if command[:2] == ["docker", "run"]:
                output_mount = next(item for item in command if item.endswith("dst=/asef-output"))
                source = output_mount.split(",src=", 1)[1].rsplit(",dst=", 1)[0]
                (Path(source) / "api-result.json").write_text("{}", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = self._workspace(root)
            result = DockerApiFixtureExecutor(root, fake).execute(workspace, output)
        self.assertEqual("ERROR", result.status)
        self.assertEqual("SANDBOX_EXECUTION_ERROR", result.scenarios[0].diagnostic_code)


if __name__ == "__main__":
    unittest.main()
