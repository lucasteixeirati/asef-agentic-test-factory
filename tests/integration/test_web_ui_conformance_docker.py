from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import unittest
from uuid import uuid4

from asef.adapters.web_ui_execution import DockerWebUiExecutor, web_ui_functional_fingerprint
from asef.web_ui_contracts import (
    WebUiAction, WebUiAssertion, WebUiLocator, WebUiScenario, WebUiTestPlan,
)


def locator(kind: str, value: str, name: str | None = None) -> WebUiLocator:
    return WebUiLocator(kind, value, name)


def scenario(control: str) -> tuple[WebUiScenario, ...]:
    goto = WebUiAction("ACT-GOTO", "goto", path="/")
    if control == "reading":
        return (WebUiScenario("SCN-READ", "Read the fixture", (goto,), (
            WebUiAssertion("AST-HEADING", "visible", True, locator("role", "heading", "Quality checklist")),
        )),)
    if control == "resettable_mutation":
        check = locator("test_id", "requirements-check")
        return (
            WebUiScenario("SCN-MUTATE", "Mutate isolated state", (goto, WebUiAction("ACT-CHECK", "check", locator=check)), (
                WebUiAssertion("AST-CHECKED", "checked", True, check),
            )),
            WebUiScenario("SCN-RESET", "Observe fresh context", (WebUiAction("ACT-GOTO-RESET", "goto", path="/"),), (
                WebUiAssertion("AST-UNCHECKED", "checked", False, check),
            )),
        )
    if control == "semantic_locator":
        note = locator("label", "Review note")
        return (WebUiScenario("SCN-SEMANTIC", "Use semantic locators", (goto, WebUiAction("ACT-FILL", "fill", locator=note, value="Ready")), (
            WebUiAssertion("AST-VALUE", "value", "Ready", note),
        )),)
    if control == "assertion_mismatch":
        return (WebUiScenario("SCN-MISMATCH", "Capture functional mismatch", (goto,), (
            WebUiAssertion("AST-MISMATCH", "value", "unexpected", locator("label", "Review note")),
        )),)
    if control == "step_timeout":
        return (WebUiScenario("SCN-TIMEOUT", "Bound a missing element", (goto,), (
            WebUiAssertion("AST-MISSING", "visible", True, locator("test_id", "does-not-exist")),
        )),)
    names = {
        "external_request": "Request external resource", "popup": "Open popup",
        "dialog": "Open dialog", "download": "Start download",
    }
    path = WebUiAction("ACT-CONFORMANCE", "goto", path="/conformance.html")
    click = WebUiAction("ACT-TRIGGER", "click", locator=locator("role", "button" if control != "download" else "link", names[control]))
    stable = WebUiAssertion("AST-HEADING", "visible", True, locator("role", "heading", "Adversarial browser controls"))
    return (WebUiScenario(f"SCN-{control.upper().replace('_', '-')}", f"Block {control}", (path, click), (stable,)),)


@unittest.skipUnless(os.environ.get("ASEF_RUN_WEB_UI_DOCKER_TESTS") == "1", "Web UI Docker tests disabled")
class WebUiConformanceDockerTests(unittest.TestCase):
    def test_dataset_docker_oracles_repeat_with_stable_functional_fingerprints(self) -> None:
        manifest = json.loads(Path("datasets/web-ui/manifest.json").read_text(encoding="utf-8"))
        cases = [item for item in manifest["cases"] if item["docker"]]
        self.assertEqual(9, len(cases))
        for case in cases:
            fingerprints = []
            for _ in range(manifest["repetitions"]):
                plan = WebUiTestPlan(f"WEB-{case['case_id']}", "http://127.0.0.1:4173", scenario(case["control"]))
                root = Path(".asef") / f"web-ui-conformance-{uuid4().hex}"
                root.mkdir()
                try:
                    workspace, output = DockerWebUiExecutor.stage(plan, root)
                    result = DockerWebUiExecutor(root).execute(workspace, output)
                    self.assertEqual(case["expected"], result.status, (case["case_id"], result.to_dict()))
                    if result.status != "PASSED":
                        self.assertIsNotNone(result.scenarios[0].screenshot_ref)
                    fingerprints.append(web_ui_functional_fingerprint(result))
                finally:
                    shutil.rmtree(root)
            self.assertEqual([fingerprints[0]] * 2, fingerprints)


if __name__ == "__main__":
    unittest.main()
