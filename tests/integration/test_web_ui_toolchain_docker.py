from __future__ import annotations

import os
from pathlib import Path
import shutil
import unittest
from uuid import uuid4

from asef.adapters.web_ui_toolchain import DockerWebUiToolchainProbe
from asef.adapters.web_ui_execution import DockerWebUiExecutor
from asef.web_ui_contracts import (
    WebUiAction, WebUiAssertion, WebUiLocator, WebUiScenario, WebUiTestPlan,
)


@unittest.skipUnless(os.environ.get("ASEF_RUN_WEB_UI_DOCKER_TESTS") == "1", "Web UI Docker tests disabled")
class WebUiToolchainDockerIntegrationTests(unittest.TestCase):
    def test_chromium_starts_nonroot_under_networkless_readonly_policy(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        root = Path(".asef") / f"web-ui-toolchain-{uuid4().hex}"
        root.mkdir()
        try:
            workspace, output = DockerWebUiToolchainProbe.stage(root)
            os.chmod(output, 0o777)
            result = DockerWebUiToolchainProbe(root).execute(workspace, output)
        finally:
            shutil.rmtree(root)
        self.assertEqual("PASSED", result.status, result.diagnostic_code)
        self.assertNotEqual(0, result.uid)
        self.assertTrue(result.rootfs_read_only)
        self.assertTrue(result.workspace_read_only)
        self.assertTrue(result.egress_blocked)

    def test_declarative_plan_executes_fixture_and_failure_produces_private_png(self) -> None:
        locator = WebUiLocator("test_id", "requirements-check")
        passing = WebUiTestPlan("WEB-DOCKER-001", "http://127.0.0.1:4173", (
            WebUiScenario("SCN-PASS", "Check the local fixture", (
                WebUiAction("ACT-GOTO", "goto", path="/"),
                WebUiAction("ACT-CHECK", "check", locator=locator),
            ), (WebUiAssertion("AST-CHECKED", "checked", True, locator),)),
        ))
        failing = WebUiTestPlan("WEB-DOCKER-002", "http://127.0.0.1:4173", (
            WebUiScenario("SCN-FAIL", "Observe an assertion mismatch", (
                WebUiAction("ACT-GOTO", "goto", path="/"),
            ), (WebUiAssertion("AST-VALUE", "value", "unexpected", WebUiLocator("label", "Review note")),)),
        ))
        for plan, expected in ((passing, "PASSED"), (failing, "FAILED")):
            root = Path(".asef") / f"web-ui-execution-{uuid4().hex}"
            root.mkdir()
            try:
                workspace, output = DockerWebUiExecutor.stage(plan, root)
                result = DockerWebUiExecutor(root).execute(workspace, output)
                self.assertEqual(expected, result.status)
                if expected == "FAILED":
                    ref = result.scenarios[0].screenshot_ref
                    self.assertIsNotNone(ref)
                    self.assertTrue((output / ref).is_file())
            finally:
                shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
