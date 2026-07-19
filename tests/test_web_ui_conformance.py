from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from asef.adapters.capability_run_store import CapabilityRunStore
from asef.adapters.gateway import ModelResult
from asef.adapters.web_ui_execution import DockerWebUiExecutor, web_ui_functional_fingerprint
from asef.adapters.web_ui_plan_agent import WebUiPlanAgentAdapter
from asef.application.web_ui_run import ExecuteWebUiPlanService, GenerateWebUiPlanService
from asef.capability_runs import CapabilityRunBudgets, CapabilityRunStatus
from asef.skills.web_ui import WebUiPolicy, WebUiPolicyError, WebUiSkill
from asef.web_ui_contracts import (
    WebUiAction, WebUiAssertion, WebUiContractError, WebUiExecutionResult,
    WebUiLocator, WebUiScenario, WebUiScenarioResult, WebUiTestPlan,
    web_ui_plan_from_dict,
)


IMAGE_ID = "sha256:" + "c" * 64


def reference_plan() -> WebUiTestPlan:
    return WebUiTestPlan("WEB-CONFORMANCE", "http://127.0.0.1:4173", (
        WebUiScenario("SCN-001", "Read the local fixture", (
            WebUiAction("ACT-GOTO", "goto", path="/"),
        ), (
            WebUiAssertion("AST-URL", "url", "/"),
        )),
    ))


class WebUiConformanceDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = json.loads(Path("datasets/web-ui/manifest.json").read_text(encoding="utf-8"))
        Path(".asef").mkdir(exist_ok=True)

    def test_manifest_is_closed_unique_and_covers_stage_645_matrix(self) -> None:
        self.assertEqual("1.0.0", self.raw["schema_version"])
        self.assertEqual(2, self.raw["repetitions"])
        cases = self.raw["cases"]
        self.assertEqual(14, len(cases))
        self.assertEqual(len(cases), len({item["case_id"] for item in cases}))
        self.assertEqual({
            "reading", "resettable_mutation", "semantic_locator", "assertion_mismatch",
            "step_timeout", "external_navigation", "external_request", "popup", "dialog",
            "download", "secret", "artifact_tampering", "private_screenshot", "request_budget",
        }, {item["control"] for item in cases})
        for item in cases:
            self.assertEqual({"case_id", "control", "expected", "docker"}, set(item))

    def test_external_navigation_and_secret_are_rejected_before_docker(self) -> None:
        raw = reference_plan().to_dict()
        raw["scenarios"][0]["actions"][0]["path"] = "https://example.test/"
        with self.assertRaises(WebUiContractError):
            web_ui_plan_from_dict(raw)
        secret = WebUiTestPlan("WEB-SECRET", "http://127.0.0.1:4173", (
            WebUiScenario("SCN-SECRET", "Enter password", (
                WebUiAction("ACT-GOTO", "goto", path="/"),
            ), (WebUiAssertion("AST-URL", "url", "/"),)),
        ))
        with self.assertRaisesRegex(WebUiPolicyError, "sensitive"):
            WebUiSkill(WebUiPolicy(allowed_ports=(4173,))).validate(secret)

    def test_artifact_tampering_is_rejected_before_docker(self) -> None:
        commands: list[list[str]] = []
        def fake(command, **kwargs):
            del kwargs
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiExecutor.stage(reference_plan(), root)
            (workspace / "generated" / "web-ui-plan.ts").write_text("export default {};\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                DockerWebUiExecutor(root, fake).execute(workspace, output)
        self.assertFalse(any(item[:2] == ["docker", "run"] for item in commands))

    def test_private_screenshot_oracle_and_functional_fingerprint_ignore_volatile_fields(self) -> None:
        def result(duration: int, ref: str) -> WebUiExecutionResult:
            return WebUiExecutionResult(
                "WEB-CONFORMANCE", "FAILED", 1, 0, 1, 0, 0, 0,
                (WebUiScenarioResult("SCN-001", "FAILED", duration, "ASSERTION_MISMATCH", "AST-URL", ref),),
            )
        first = result(10, "screenshots/SCN-001.png")
        second = result(999, "screenshots/alternate.png")
        self.assertEqual(web_ui_functional_fingerprint(first), web_ui_functional_fingerprint(second))
        validation = WebUiSkill(WebUiPolicy(allowed_ports=(4173,))).validate(reference_plan())
        self.assertFalse(validation["screenshots_publishable"])

    def test_request_budget_oracle_blocks_the_executor(self) -> None:
        class Gateway:
            def generate(self, **kwargs):
                del kwargs
                return ModelResult({"scenarios": [{
                    "description": "Read the local fixture",
                    "actions": [{"kind": "goto", "path": "/"}],
                    "assertions": [{"kind": "url", "expected": "/"}],
                }]}, "conformance", "response-1", 10, 10)

        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store = CapabilityRunStore(Path(directory))
            generated = GenerateWebUiPlanService(
                WebUiPlanAgentAdapter(Gateway(), WebUiPolicy(allowed_ports=(4173,))), store,
            ).execute(
                "Read the fixture", "http://127.0.0.1:4173",
                CapabilityRunBudgets(max_requests=1),
            )
            state = store.load_state(generated.state.run_id)
            state.usage.requests = 1
            store.save_state(state)
            executor_called = False
            def factory(root):
                del root
                nonlocal executor_called
                executor_called = True
                raise AssertionError("executor must not be constructed")
            completed = ExecuteWebUiPlanService(store, factory).execute(generated.state.run_id)
        self.assertEqual(CapabilityRunStatus.BUDGET_EXHAUSTED, completed.state.status)
        self.assertFalse(executor_called)


if __name__ == "__main__":
    unittest.main()
