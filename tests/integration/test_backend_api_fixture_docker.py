from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from asef.adapters.docker_api_fixture import DockerApiFixtureExecutor
from asef.api_contracts import ApiAssertion, ApiScenario, ApiTestPlan


@unittest.skipUnless(os.environ.get("ASEF_RUN_DOCKER_TESTS") == "1", "Docker tests disabled")
class BackendApiFixtureDockerIntegrationTests(unittest.TestCase):
    def test_fixture_and_executor_run_inside_networkless_container(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            plan = ApiTestPlan(
                "API-DOCKER-INTEGRATION-001",
                "http://127.0.0.1:8765",
                (ApiScenario("SCN-001", "health", "GET", "/health", ApiAssertion(200, {"status": "ok"})),),
            )
            workspace, output = DockerApiFixtureExecutor.stage(plan, root)
            os.chmod(output, 0o777)
            result = DockerApiFixtureExecutor(root).execute(workspace, output)
            self.assertEqual("PASSED", result.status)
            self.assertEqual(1, result.passed)


if __name__ == "__main__":
    unittest.main()
