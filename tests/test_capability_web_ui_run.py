from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from asef.adapters.capability_run_store import CapabilityRunStore
from asef.adapters.gateway import ModelResult
from asef.adapters.web_ui_plan_agent import (
    WEB_UI_PLAN_SCHEMA, WebUiPlanAgentAdapter, WebUiPlanAgentPricing, WebUiPlanOutputError,
)
from asef.application.ports import ProviderTransientError
from asef.application.web_ui_run import ExecuteWebUiPlanService, GenerateWebUiPlanService
from asef.capability_runs import (
    CapabilityRunBudgets, CapabilityRunClassification, CapabilityRunContractError,
    CapabilityRunStatus,
)
from asef.skills.web_ui import WebUiPolicy
from asef.web_ui_contracts import WebUiExecutionResult, WebUiScenarioResult


def model_output() -> dict[str, object]:
    return {"scenarios": [{
        "description": "Check the requirements item",
        "actions": [
            {"kind": "goto", "path": "/"},
            {"kind": "check", "locator": {"kind": "test_id", "value": "requirements-check"}},
        ],
        "assertions": [
            {"kind": "checked", "expected": True, "locator": {"kind": "test_id", "value": "requirements-check"}},
        ],
    }]}


class Gateway:
    def __init__(self, callback=None) -> None:
        self.callback = callback
        self.calls = 0

    def generate(self, *, prompt, schema, schema_name):
        del prompt, schema
        self.calls += 1
        if self.callback:
            self.callback()
        self.schema_name = schema_name
        return ModelResult(model_output(), "recorded-test", "web-response-1", 80, 50)


class PassingExecutor:
    def execute(self, workspace, output):
        del workspace, output
        return WebUiExecutionResult(
            "WEB-PLAN-PLACEHOLDER", "PASSED", 1, 1, 0, 0, 0, 0,
            (WebUiScenarioResult("SCN-001", "PASSED", 10),),
        )


class CapabilityWebUiRunTests(unittest.TestCase):
    def setUp(self) -> None:
        Path(".asef").mkdir(exist_ok=True)

    def generate(self, root: Path, gateway=None, budgets=None):
        store = CapabilityRunStore(root)
        output = GenerateWebUiPlanService(
            WebUiPlanAgentAdapter(
                gateway or Gateway(),
                WebUiPolicy(allowed_hosts=("127.0.0.1",), allowed_ports=(4173,)),
            ), store,
        ).execute("Check requirements", "http://127.0.0.1:4173", budgets)
        return store, output

    def test_run_exists_before_gateway_and_waits_for_review(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            gateway = Gateway(lambda: self.assertEqual(1, len(list(root.iterdir()))))
            store, output = self.generate(root, gateway)
            self.assertEqual(CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW, output.state.status)
            self.assertEqual(CapabilityRunClassification.PLAN_READY_FOR_REVIEW, output.state.classification)
            self.assertEqual("web_ui_plan_v1", gateway.schema_name)
            self.assertEqual(output.plan.plan_id, store.load_web_plan(output.state).plan_id)
            self.assertEqual((1, 80, 50), (output.state.usage.model_calls, output.state.usage.input_tokens, output.state.usage.output_tokens))

    def test_zero_model_budget_stops_before_gateway(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            gateway = Gateway()
            _, output = self.generate(Path(directory), gateway, CapabilityRunBudgets(max_model_calls=0))
            self.assertEqual(CapabilityRunStatus.BUDGET_EXHAUSTED, output.state.status)
            self.assertEqual(0, gateway.calls)

    def test_generation_token_budget_is_accounted_before_stopping(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            _, output = self.generate(
                Path(directory), budgets=CapabilityRunBudgets(max_input_tokens=1, max_output_tokens=1)
            )
            self.assertEqual(CapabilityRunStatus.BUDGET_EXHAUSTED, output.state.status)
            self.assertEqual((80, 50), (output.state.usage.input_tokens, output.state.usage.output_tokens))

    def test_sensitive_or_malformed_generation_fails_closed_with_persisted_state(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            store = CapabilityRunStore(root)
            gateway = Gateway()
            service = GenerateWebUiPlanService(
                WebUiPlanAgentAdapter(gateway, WebUiPolicy(allowed_ports=(4173,))), store
            )
            with self.assertRaisesRegex(ValueError, "sensitive"):
                service.execute("password=example", "http://127.0.0.1:4173")
            state = store.load_state(next(root.iterdir()).name)
            self.assertEqual(CapabilityRunStatus.POLICY_BLOCKED, state.status)
            self.assertEqual(0, gateway.calls)

    def test_agent_rejects_malformed_nested_model_shapes(self) -> None:
        valid = model_output()
        malformed = [
            {"unexpected": []},
            {"scenarios": [{"description": "x", "actions": []}]},
            {"scenarios": [{"description": "x", "actions": [{"kind": "check", "locator": "css"}], "assertions": [{"kind": "url", "expected": "/"}]}]},
            {"scenarios": [{"description": "x", "actions": [{"kind": "goto", "path": "/", "script": "x"}], "assertions": [{"kind": "url", "expected": "/"}]}]},
            {"scenarios": [{"description": "x", "actions": [{"kind": "goto", "path": "/"}], "assertions": [{"kind": "url"}]}]},
        ]
        for output in malformed:
            class BadGateway:
                def generate(self, **kwargs):
                    del kwargs
                    return ModelResult(output, "bad", "bad-response", 3, 4)
            with self.subTest(output=output), self.assertRaises(WebUiPlanOutputError):
                WebUiPlanAgentAdapter(
                    BadGateway(), WebUiPolicy(allowed_ports=(4173,))
                ).generate("Check fixture", "http://127.0.0.1:4173")

    def test_live_pricing_retry_and_strict_schema_are_bounded_without_provider_call(self) -> None:
        def assert_strict(node):
            if isinstance(node, dict):
                if node.get("type") == "object":
                    self.assertFalse(node.get("additionalProperties", True))
                    self.assertEqual(set(node.get("properties", {})), set(node.get("required", [])))
                for value in node.values():
                    assert_strict(value)
            elif isinstance(node, list):
                for value in node:
                    assert_strict(value)
        assert_strict(WEB_UI_PLAN_SCHEMA)
        pricing = WebUiPlanAgentPricing(1000.0, 2000.0)
        pricing.validate_live()
        class RetryGateway(Gateway):
            def generate(self, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    raise ProviderTransientError("temporary")
                return ModelResult(model_output(), "live-test", "response-live", 80, 50, provider="openai")
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            gateway = RetryGateway()
            store = CapabilityRunStore(Path(directory))
            output = GenerateWebUiPlanService(
                WebUiPlanAgentAdapter(gateway, WebUiPolicy(allowed_ports=(4173,)), pricing), store
            ).execute(
                "Check fixture", "http://127.0.0.1:4173",
                CapabilityRunBudgets(max_model_calls=2, max_provider_retries=1, api_budget_brl=1.0),
            )
            self.assertEqual(CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW, output.state.status)
            self.assertEqual((2, 1), (output.state.usage.model_calls, output.state.usage.provider_retries))
            self.assertEqual(0.18, output.state.usage.estimated_cost_brl)

    def test_plan_tampering_blocks_reviewed_execution(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store, output = self.generate(Path(directory))
            path = store.run_dir(output.state.run_id) / "artifacts" / "web-ui-plan.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(CapabilityRunContractError, "integrity mismatch"):
                ExecuteWebUiPlanService(store).execute(output.state.run_id)

    def test_accepted_execution_reconciles_manifest_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store, generated = self.generate(Path(directory))

            class Executor:
                def execute(inner, workspace, output):
                    del inner, workspace, output
                    return WebUiExecutionResult(
                        generated.plan.plan_id, "PASSED", 1, 1, 0, 0, 0, 0,
                        (WebUiScenarioResult("SCN-001", "PASSED", 10),),
                    )

            completed = ExecuteWebUiPlanService(store, lambda root: Executor()).execute(generated.state.run_id)
            self.assertEqual(CapabilityRunStatus.SUCCEEDED, completed.state.status)
            self.assertEqual(CapabilityRunClassification.ACCEPTED, completed.state.classification)
            self.assertEqual({"web_ui_test_plan", "web_ui_execution_result"}, {item.kind for item in completed.state.evidence_refs})
            manifest = json.loads((store.run_dir(completed.state.run_id) / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["terminal"])

    def test_scenario_budget_blocks_before_executor(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store, generated = self.generate(Path(directory), budgets=CapabilityRunBudgets(max_requests=1))
            state = store.load_state(generated.state.run_id)
            state.usage.requests = 1
            store.save_state(state)
            called = False
            def factory(root):
                nonlocal called
                called = True
                return PassingExecutor()
            completed = ExecuteWebUiPlanService(store, factory).execute(generated.state.run_id)
            self.assertIsNone(completed.result)
            self.assertEqual(CapabilityRunStatus.BUDGET_EXHAUSTED, completed.state.status)
            self.assertFalse(called)

    def test_nonpassing_results_keep_function_policy_and_infrastructure_distinct(self) -> None:
        matrix = (
            ("FAILED", CapabilityRunClassification.FUNCTIONAL_FAILURE, CapabilityRunStatus.FAILED),
            ("POLICY_BLOCKED", CapabilityRunClassification.POLICY_VIOLATION, CapabilityRunStatus.POLICY_BLOCKED),
            ("ERROR", CapabilityRunClassification.INFRASTRUCTURE_ERROR, CapabilityRunStatus.FAILED),
            ("TIMEOUT", CapabilityRunClassification.INFRASTRUCTURE_ERROR, CapabilityRunStatus.FAILED),
        )
        for status, classification, terminal in matrix:
            with self.subTest(status=status), tempfile.TemporaryDirectory(dir=".asef") as directory:
                store, generated = self.generate(Path(directory))
                class Executor:
                    def execute(inner, workspace, output):
                        del inner, workspace, output
                        counts = {name: int(name == status) for name in ("FAILED", "ERROR", "TIMEOUT", "POLICY_BLOCKED")}
                        return WebUiExecutionResult(
                            generated.plan.plan_id, status, 1, 0, counts["FAILED"], counts["ERROR"],
                            counts["TIMEOUT"], counts["POLICY_BLOCKED"],
                            (WebUiScenarioResult("SCN-001", status, 1, "EXPECTED_NONPASS"),),
                        )
                completed = ExecuteWebUiPlanService(store, lambda root: Executor()).execute(generated.state.run_id)
                self.assertEqual(classification, completed.state.classification)
                self.assertEqual(terminal, completed.state.status)


if __name__ == "__main__":
    unittest.main()
