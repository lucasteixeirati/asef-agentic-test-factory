from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from asef.adapters.web_ui_compiler import WebUiPlanCompiler
from asef.adapters.web_ui_execution import DockerWebUiExecutor
from asef.web_ui_contracts import (
    WebUiAction,
    WebUiAssertion,
    WebUiLocator,
    WebUiScenario,
    WebUiTestPlan,
)


IMAGE_ID = "sha256:" + "b" * 64


def reference_plan(*, expected: str = "1 of 2 checks complete") -> WebUiTestPlan:
    return WebUiTestPlan(
        plan_id="WEB-FIXTURE-001",
        base_url="http://127.0.0.1:4173",
        scenarios=(WebUiScenario(
            scenario_id="SCN-CHECKLIST",
            description="Update the resettable local quality checklist",
            actions=(
                WebUiAction("ACT-GOTO", "goto", path="/"),
                WebUiAction("ACT-CHECK", "check", locator=WebUiLocator("test_id", "requirements-check")),
                WebUiAction("ACT-FILL", "fill", locator=WebUiLocator("label", "Review note"), value="Evidence ready"),
                WebUiAction("ACT-SAVE", "click", locator=WebUiLocator("role", "button", "Save review")),
            ),
            assertions=(
                WebUiAssertion("AST-URL", "url", "/"),
                WebUiAssertion("AST-SUMMARY", "text", expected, WebUiLocator("role", "status", "1 of 2 checks complete")),
                WebUiAssertion("AST-RESULT", "text", "Evidence ready", WebUiLocator("role", "status", "Evidence ready")),
            ),
        ),),
    )


def passing_result() -> dict[str, object]:
    return {
        "schema_version": "1.0.0", "plan_id": "WEB-FIXTURE-001", "status": "PASSED",
        "tests": 1, "passed": 1, "failed": 0, "errors": 0, "timeouts": 0,
        "policy_blocked": 0,
        "scenarios": [{
            "scenario_id": "SCN-CHECKLIST", "status": "PASSED", "duration_ms": 12,
            "diagnostic_code": None, "failed_step_id": None, "screenshot_ref": None,
        }],
    }


class WebUiPlanCompilerTests(unittest.TestCase):
    def test_compiler_is_deterministic_data_only_and_bound_to_plan(self) -> None:
        first = WebUiPlanCompiler.compile(reference_plan())
        second = WebUiPlanCompiler.compile(reference_plan())
        self.assertEqual(first, second)
        self.assertEqual(64, len(first.sha256))
        self.assertIn('"plan_id":"WEB-FIXTURE-001"', first.source)
        for forbidden in ("eval(", "child_process", "process.env", "page.", "http://example"):
            self.assertNotIn(forbidden, first.source)


class DockerWebUiExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        Path(".asef").mkdir(exist_ok=True)

    @staticmethod
    def fake(payload: dict[str, object] | None, *, exit_code: int = 0, screenshot: str | None = None):
        commands: list[list[str]] = []

        def execute(command, **kwargs):
            del kwargs
            commands.append(command)
            if command[:3] == ["docker", "image", "inspect"]:
                return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
            if command[:2] == ["docker", "run"]:
                mount = next(item for item in command if item.endswith("dst=/asef-output"))
                source = mount.split(",src=", 1)[1].rsplit(",dst=", 1)[0]
                if payload is not None:
                    (Path(source) / "web-ui-result.json").write_text(json.dumps(payload), encoding="utf-8")
                if screenshot is not None:
                    (Path(source) / screenshot).write_bytes(b"\x89PNG\r\n\x1a\nASEF")
                return subprocess.CompletedProcess(command, exit_code, "", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        return commands, execute

    def test_stage_and_execute_use_reviewed_artifact_and_hardened_container(self) -> None:
        commands, fake = self.fake(passing_result())
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiExecutor.stage(reference_plan(), root)
            result = DockerWebUiExecutor(root, fake).execute(workspace, output)
        run = next(item for item in commands if item[:2] == ["docker", "run"])
        self.assertEqual("PASSED", result.status)
        self.assertEqual(["run"], run[-1:])
        self.assertEqual("none", run[run.index("--network") + 1])
        self.assertIn("readonly", next(item for item in run if item.endswith("dst=/workspace,readonly")))
        self.assertIn("com.asef.capability=web-ui-execution", run)

    def test_tampered_artifact_is_blocked_before_docker(self) -> None:
        commands, fake = self.fake(passing_result())
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiExecutor.stage(reference_plan(), root)
            (workspace / "generated" / "web-ui-plan.ts").write_text("export default {};\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                DockerWebUiExecutor(root, fake).execute(workspace, output)
        self.assertFalse(any(item[:2] == ["docker", "run"] for item in commands))

    def test_spoofed_result_identity_fails_closed(self) -> None:
        payload = passing_result()
        payload["plan_id"] = "WEB-SPOOFED"
        commands, fake = self.fake(payload)
        del commands
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiExecutor.stage(reference_plan(), root)
            result = DockerWebUiExecutor(root, fake).execute(workspace, output)
        self.assertEqual("ERROR", result.status)
        self.assertEqual("SANDBOX_EXECUTION_ERROR", result.scenarios[0].diagnostic_code)

    def test_functional_failure_preserves_valid_private_screenshot(self) -> None:
        payload = passing_result()
        payload.update({"status": "FAILED", "passed": 0, "failed": 1})
        payload["scenarios"][0].update({
            "status": "FAILED", "diagnostic_code": "ASSERTION_MISMATCH",
            "failed_step_id": "AST-RESULT", "screenshot_ref": "screenshots/SCN-CHECKLIST.png",
        })
        commands, fake = self.fake(payload, exit_code=1, screenshot="screenshots/SCN-CHECKLIST.png")
        del commands
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiExecutor.stage(reference_plan(), root)
            result = DockerWebUiExecutor(root, fake).execute(workspace, output)
        self.assertEqual("FAILED", result.status)
        self.assertEqual("screenshots/SCN-CHECKLIST.png", result.scenarios[0].screenshot_ref)

    def test_missing_result_and_exit_mismatch_fail_closed(self) -> None:
        for payload, exit_code in ((None, 2), (passing_result(), 1)):
            commands, fake = self.fake(payload, exit_code=exit_code)
            del commands
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory(dir=".asef") as directory:
                root = Path(directory)
                workspace, output = DockerWebUiExecutor.stage(reference_plan(), root)
                result = DockerWebUiExecutor(root, fake).execute(workspace, output)
            self.assertEqual("ERROR", result.status)

    def test_invalid_image_identity_is_rejected(self) -> None:
        def fake(command, **kwargs):
            del kwargs
            return subprocess.CompletedProcess(command, 1, "", "missing")
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiExecutor.stage(reference_plan(), root)
            with self.assertRaisesRegex(OSError, "unavailable"):
                DockerWebUiExecutor(root, fake).execute(workspace, output)

    def test_stage_rejects_origin_outside_fixed_fixture(self) -> None:
        plan = reference_plan()
        invalid = WebUiTestPlan(plan.plan_id, "http://127.0.0.1:9999", plan.scenarios)
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            with self.assertRaisesRegex(ValueError, "port"):
                DockerWebUiExecutor.stage(invalid, Path(directory))


if __name__ == "__main__":
    unittest.main()
