from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from asef.adapters.web_ui_plan_file import WebUiPlanFileAdapter
from asef.skills.web_ui import WebUiPolicy, WebUiPolicyError, WebUiSkill
from asef.web_ui_contracts import (
    WebUiAction,
    WebUiAssertion,
    WebUiContractError,
    WebUiExecutionResult,
    WebUiLocator,
    WebUiScenario,
    WebUiScenarioResult,
    WebUiTestPlan,
    web_ui_execution_result_from_dict,
    web_ui_plan_from_dict,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PORT = 4173


def valid_plan() -> WebUiTestPlan:
    return WebUiTestPlan(
        plan_id="WEB-PLAN-001",
        base_url=f"http://127.0.0.1:{FIXTURE_PORT}",
        scenarios=(
            WebUiScenario(
                scenario_id="SCN-001",
                description="review the local quality checklist",
                actions=(
                    WebUiAction("ACT-001", "goto", path="/"),
                    WebUiAction(
                        "ACT-002",
                        "check",
                        locator=WebUiLocator("label", "Requirements reviewed"),
                    ),
                    WebUiAction(
                        "ACT-003",
                        "fill",
                        locator=WebUiLocator("label", "Review note"),
                        value="Evidence checked",
                    ),
                    WebUiAction(
                        "ACT-004",
                        "click",
                        locator=WebUiLocator("role", "button", "Save review"),
                    ),
                ),
                assertions=(
                    WebUiAssertion("AST-001", "url", "/"),
                    WebUiAssertion(
                        "AST-002",
                        "text",
                        "Evidence checked",
                        WebUiLocator("role", "status", "Evidence checked"),
                    ),
                ),
            ),
        ),
    )


class WebUiPlanContractTests(unittest.TestCase):
    def test_valid_plan_round_trips_through_strict_parser(self) -> None:
        plan = valid_plan()
        parsed = web_ui_plan_from_dict(plan.to_dict())
        self.assertEqual(plan, parsed)

    def test_parser_rejects_unknown_fields_and_free_form_selectors(self) -> None:
        value = valid_plan().to_dict()
        value["unexpected"] = True
        with self.assertRaisesRegex(WebUiContractError, "root fields"):
            web_ui_plan_from_dict(value)

        value = valid_plan().to_dict()
        value["scenarios"][0]["actions"][1]["locator"] = {
            "kind": "css",
            "value": "#requirements-check",
        }
        with self.assertRaisesRegex(WebUiContractError, "role, label or test_id"):
            web_ui_plan_from_dict(value)

    def test_navigation_rejects_external_fragment_backslash_and_whitespace_paths(self) -> None:
        for path in ("https://example.test/", "//example.test/", "/#fragment", "/\\example.test", "/a b"):
            with self.subTest(path=path):
                plan = replace(
                    valid_plan(),
                    scenarios=(replace(valid_plan().scenarios[0], actions=(WebUiAction("ACT-001", "goto", path=path),)),),
                )
                with self.assertRaises(WebUiContractError):
                    plan.validate()

    def test_identifiers_are_bounded_and_reject_control_characters(self) -> None:
        scenario = replace(valid_plan().scenarios[0], scenario_id="SCN-001\nforged")
        with self.assertRaisesRegex(WebUiContractError, "uppercase identifier"):
            replace(valid_plan(), scenarios=(scenario,)).validate()

    def test_action_shapes_and_assertion_types_are_closed(self) -> None:
        with self.assertRaisesRegex(WebUiContractError, "accepts only a relative path"):
            WebUiAction(
                "ACT-001", "goto", path="/", locator=WebUiLocator("label", "Review note")
            ).validate()

    def test_locator_and_fill_shapes_reject_ambiguous_values(self) -> None:
        with self.assertRaisesRegex(WebUiContractError, "role locator name"):
            WebUiLocator("role", "button").validate()
        with self.assertRaisesRegex(WebUiContractError, "only role locators"):
            WebUiLocator("label", "Review note", "unexpected").validate()
        with self.assertRaisesRegex(WebUiContractError, "fill value"):
            WebUiAction(
                "ACT-001", "fill", locator=WebUiLocator("label", "Review note"), value="bad\nvalue"
            ).validate()
        with self.assertRaisesRegex(WebUiContractError, "only fill actions"):
            WebUiAction(
                "ACT-001", "click", locator=WebUiLocator("label", "Review note"), value="unexpected"
            ).validate()

    def test_plan_rejects_invalid_origin_viewport_and_duplicate_scenarios(self) -> None:
        for base_url in ("https://127.0.0.1:4173", "http://user@127.0.0.1:4173", "http://127.0.0.1"):
            with self.subTest(base_url=base_url), self.assertRaises(WebUiContractError):
                replace(valid_plan(), base_url=base_url).validate()
        with self.assertRaisesRegex(WebUiContractError, "viewport"):
            replace(valid_plan(), viewport_width=200).validate()
        scenario = valid_plan().scenarios[0]
        with self.assertRaisesRegex(WebUiContractError, "scenario ids must be unique"):
            replace(valid_plan(), scenarios=(scenario, scenario)).validate()
        with self.assertRaisesRegex(WebUiContractError, "require a boolean"):
            WebUiAssertion(
                "AST-001", "checked", "yes", WebUiLocator("test_id", "requirements-check")
            ).validate()


class WebUiExecutionResultTests(unittest.TestCase):
    def result(self, scenario: WebUiScenarioResult | None = None) -> WebUiExecutionResult:
        selected = scenario or WebUiScenarioResult("SCN-001", "PASSED", 25)
        counts = {status: int(selected.status == status) for status in (
            "PASSED", "FAILED", "ERROR", "TIMEOUT", "POLICY_BLOCKED"
        )}
        return WebUiExecutionResult(
            plan_id="WEB-PLAN-001",
            status=selected.status,
            tests=1,
            passed=counts["PASSED"],
            failed=counts["FAILED"],
            errors=counts["ERROR"],
            timeouts=counts["TIMEOUT"],
            policy_blocked=counts["POLICY_BLOCKED"],
            scenarios=(selected,),
        )

    def test_result_round_trips_and_reconciles_counters(self) -> None:
        result = self.result()
        self.assertEqual(result, web_ui_execution_result_from_dict(result.to_dict()))
        with self.assertRaisesRegex(WebUiContractError, "counters do not reconcile"):
            replace(result, passed=0).validate()

    def test_failure_evidence_is_contained_and_png_only(self) -> None:
        valid = WebUiScenarioResult(
            "SCN-001", "FAILED", 30, "ASSERTION_MISMATCH", "AST-002", "screenshots/SCN-001.png"
        )
        self.result(valid).validate()
        for ref in ("../outside.png", "/absolute.png", "screenshots\\failure.png", "failure.jpg"):
            with self.subTest(ref=ref), self.assertRaisesRegex(WebUiContractError, "relative PNG"):
                replace(valid, screenshot_ref=ref).validate()

    def test_passed_result_cannot_claim_failure_evidence(self) -> None:
        with self.assertRaisesRegex(WebUiContractError, "passed scenario"):
            WebUiScenarioResult("SCN-001", "PASSED", 5, screenshot_ref="failure.png").validate()

    def test_parser_rejects_unknown_nested_fields_and_boolean_counter(self) -> None:
        value = self.result().to_dict()
        value["scenarios"][0]["raw_stdout"] = "untrusted"
        with self.assertRaisesRegex(WebUiContractError, "scenario result fields"):
            web_ui_execution_result_from_dict(value)
        value = self.result().to_dict()
        value["tests"] = True
        with self.assertRaisesRegex(WebUiContractError, "counters must be integers"):
            web_ui_execution_result_from_dict(value)

    def test_non_passing_result_requires_valid_diagnostic_and_step(self) -> None:
        with self.assertRaisesRegex(WebUiContractError, "requires a diagnostic"):
            WebUiScenarioResult("SCN-001", "FAILED", 1).validate()
        with self.assertRaisesRegex(WebUiContractError, "action or assertion"):
            WebUiScenarioResult("SCN-001", "ERROR", 1, "BROWSER_ERROR", "STEP-1").validate()
        with self.assertRaisesRegex(WebUiContractError, "non-negative integer"):
            WebUiScenarioResult("SCN-001", "ERROR", -1, "BROWSER_ERROR").validate()

    def test_result_status_precedence_is_deterministic(self) -> None:
        scenarios = (
            WebUiScenarioResult("SCN-001", "FAILED", 1, "ASSERTION_MISMATCH"),
            WebUiScenarioResult("SCN-002", "TIMEOUT", 2, "SCENARIO_TIMEOUT"),
        )
        result = WebUiExecutionResult(
            "WEB-PLAN-001", "FAILED", 2, 0, 1, 0, 1, 0, scenarios
        )
        with self.assertRaisesRegex(WebUiContractError, "status does not match counters"):
            result.validate()
        replace(result, status="TIMEOUT").validate()


class WebUiPolicyAndAdapterTests(unittest.TestCase):
    def policy(self) -> WebUiPolicy:
        return WebUiPolicy(allowed_ports=(FIXTURE_PORT,))

    def test_policy_requires_explicit_loopback_port_authorization(self) -> None:
        with self.assertRaisesRegex(WebUiPolicyError, "explicitly allowed fixture port"):
            WebUiSkill()
        with self.assertRaisesRegex(WebUiPolicyError, "port is outside"):
            WebUiSkill(WebUiPolicy(allowed_ports=(4174,))).validate(valid_plan())
        validation = WebUiSkill(self.policy()).validate(valid_plan())
        self.assertEqual(("loopback-only", False), (
            validation["network_scope"], validation["screenshots_publishable"]
        ))

    def test_policy_rejects_external_host_and_sensitive_markers(self) -> None:
        external = replace(valid_plan(), base_url="http://example.test:4173")
        with self.assertRaisesRegex(WebUiPolicyError, "loopback allowlist"):
            WebUiSkill(self.policy()).validate(external)
        sensitive = replace(
            valid_plan(),
            scenarios=(replace(valid_plan().scenarios[0], description="fill the password field"),),
        )
        with self.assertRaisesRegex(WebUiPolicyError, "sensitive data markers"):
            WebUiSkill(self.policy()).validate(sensitive)

    def test_policy_configuration_and_budgets_fail_closed(self) -> None:
        invalid_policies = (
            WebUiPolicy(allowed_hosts=("example.test",), allowed_ports=(FIXTURE_PORT,)),
            WebUiPolicy(allowed_ports=(FIXTURE_PORT, FIXTURE_PORT)),
            WebUiPolicy(allowed_ports=(0,)),
            WebUiPolicy(allowed_ports=(FIXTURE_PORT,), max_scenarios=0),
            WebUiPolicy(allowed_ports=(FIXTURE_PORT,), max_scenario_seconds=121),
        )
        for policy in invalid_policies:
            with self.subTest(policy=policy), self.assertRaises(WebUiPolicyError):
                policy.validate()
        query = replace(
            valid_plan(),
            scenarios=(replace(
                valid_plan().scenarios[0],
                actions=(WebUiAction("ACT-001", "goto", path="/?token=redacted"),),
            ),),
        )
        with self.assertRaisesRegex(WebUiPolicyError, "sensitive query parameters"):
            WebUiSkill(self.policy()).validate(query)

    def test_file_adapter_round_trips_and_rejects_duplicate_keys(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=".asef") as temporary:
            path = Path(temporary) / "plan.json"
            adapter = WebUiPlanFileAdapter()
            adapter.save(path, valid_plan())
            self.assertEqual(valid_plan(), adapter.load(path))
            path.write_text(
                '{"schema_version":"1.0.0","plan_id":"WEB-A","plan_id":"WEB-B"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(WebUiContractError, "duplicate JSON key"):
                adapter.load(path)

    def test_file_adapter_rejects_missing_and_invalid_json(self) -> None:
        adapter = WebUiPlanFileAdapter()
        with self.assertRaisesRegex(WebUiContractError, "regular JSON file"):
            adapter.load(Path(".asef/does-not-exist-web-plan.json"))
        Path(".asef").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=".asef") as temporary:
            path = Path(temporary) / "invalid.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(WebUiContractError, "valid UTF-8 JSON"):
                adapter.load(path)


class WebUiFixtureTests(unittest.TestCase):
    def test_fixture_is_local_resettable_and_has_no_external_dependency(self) -> None:
        root = ROOT / "examples" / "web-ui"
        manifest = json.loads((root / "fixture-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([], manifest["external_dependencies"])
        self.assertEqual("in-memory-resettable", manifest["state_model"])
        self.assertEqual("index.html", manifest["entrypoint"])
        for name in ("index.html", "app.js", "styles.css"):
            self.assertTrue((root / name).is_file(), name)

    def test_fixture_uses_semantic_controls_and_no_egress_or_persistence_apis(self) -> None:
        root = ROOT / "examples" / "web-ui"
        html = (root / "index.html").read_text(encoding="utf-8")
        javascript = (root / "app.js").read_text(encoding="utf-8")
        for marker in ('<main>', '<label', 'role="status"', 'type="checkbox"', 'type="submit"'):
            self.assertIn(marker, html)
        self.assertIn("form.reset()", javascript)
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "localStorage", "sessionStorage", "document.cookie"):
            self.assertNotIn(forbidden, javascript)


if __name__ == "__main__":
    unittest.main()
