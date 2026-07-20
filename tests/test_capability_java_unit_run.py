from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from asef.adapters.capability_run_store import CapabilityRunStore
from asef.adapters.gateway import ModelResult
from asef.adapters.java_unit_plan_agent import JavaUnitPlanAgentAdapter, JavaUnitPlanAgentPricing, JavaUnitPlanOutputError
from asef.application.java_unit_run import ExecuteJavaUnitPlanService, GenerateJavaUnitPlanService
from asef.application.ports import ExecutionOutput, ProviderTransientError
from asef.capability_runs import CapabilityRunBudgets, CapabilityRunClassification, CapabilityRunContractError, CapabilityRunStatus
from asef.contracts import TestExecutionOutcome


def output():
    return {"scenarios": [
        {"description": "Add values", "operation": "add", "left": 2, "right": 3, "expected": 5},
        {"description": "Reject zero division", "operation": "divide", "left": 1, "right": 0, "expected": "ArithmeticException"},
    ]}


class Gateway:
    def __init__(self, value=None, callback=None): self.value, self.callback, self.calls = value or output(), callback, 0
    def generate(self, **kwargs):
        self.calls += 1
        if self.callback: self.callback()
        self.schema_name = kwargs["schema_name"]
        return ModelResult(self.value, "recorded-test", "java-response-1", 70, 50)


class CapabilityJavaUnitRunTests(unittest.TestCase):
    def setUp(self): Path(".asef").mkdir(exist_ok=True)

    def generate(self, root, gateway=None):
        store = CapabilityRunStore(root)
        result = GenerateJavaUnitPlanService(JavaUnitPlanAgentAdapter(gateway or Gateway()), store).execute("Test Calculator arithmetic")
        return store, result

    def test_run_exists_before_generation_and_waits_for_review(self):
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory); gateway = Gateway(callback=lambda: self.assertEqual(1, len(list(root.iterdir()))))
            store, generated = self.generate(root, gateway)
            self.assertEqual(CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW, generated.state.status)
            self.assertEqual("java_unit_plan_v1", gateway.schema_name)
            self.assertEqual(generated.plan, store.load_java_plan(generated.state))
            self.assertEqual((1, 70, 50), (generated.state.usage.model_calls, generated.state.usage.input_tokens, generated.state.usage.output_tokens))

    def test_malformed_and_sensitive_generation_fail_closed(self):
        malformed = [
            {"script": "System.exit(0)"},
            {"scenarios": [{"description": "x", "operation": "exec", "left": 1, "right": 2, "expected": 3}]},
            {"scenarios": [{"description": "x", "operation": "add", "left": True, "right": 2, "expected": 3}]},
        ]
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(JavaUnitPlanOutputError):
                JavaUnitPlanAgentAdapter(Gateway(value)).generate("Test arithmetic")

    def test_zero_and_token_budgets_stop_at_the_correct_boundary(self):
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store = CapabilityRunStore(Path(directory)); gateway = Gateway()
            stopped = GenerateJavaUnitPlanService(JavaUnitPlanAgentAdapter(gateway), store).execute(
                "Test arithmetic", CapabilityRunBudgets(max_model_calls=0)
            )
            self.assertEqual(CapabilityRunStatus.BUDGET_EXHAUSTED, stopped.state.status)
            self.assertEqual(0, gateway.calls)
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store = CapabilityRunStore(Path(directory))
            stopped = GenerateJavaUnitPlanService(JavaUnitPlanAgentAdapter(Gateway()), store).execute(
                "Test arithmetic", CapabilityRunBudgets(max_input_tokens=1, max_output_tokens=1)
            )
            self.assertEqual((CapabilityRunStatus.BUDGET_EXHAUSTED, 70, 50),
                             (stopped.state.status, stopped.state.usage.input_tokens, stopped.state.usage.output_tokens))

    def test_transient_retry_and_live_pricing_are_accounted(self):
        class RetryGateway(Gateway):
            def generate(self, **kwargs):
                self.calls += 1
                if self.calls == 1: raise ProviderTransientError("temporary")
                return ModelResult(output(), "live-test", "response-live", 70, 50, provider="openai")
        pricing = JavaUnitPlanAgentPricing(1000.0, 2000.0); pricing.validate_live()
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            gateway = RetryGateway(); store = CapabilityRunStore(Path(directory))
            generated = GenerateJavaUnitPlanService(JavaUnitPlanAgentAdapter(gateway, pricing=pricing), store).execute(
                "Test arithmetic", CapabilityRunBudgets(max_model_calls=2, max_provider_retries=1, api_budget_brl=1.0)
            )
            self.assertEqual((2, 1, 0.17), (generated.state.usage.model_calls, generated.state.usage.provider_retries, generated.state.usage.estimated_cost_brl))

    def test_scenario_budget_blocks_before_executor(self):
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store = CapabilityRunStore(Path(directory))
            generated = GenerateJavaUnitPlanService(JavaUnitPlanAgentAdapter(Gateway()), store).execute(
                "Test arithmetic", CapabilityRunBudgets(max_requests=1)
            )
            called = False
            def factory(root):
                nonlocal called; called = True; return object()
            stopped = ExecuteJavaUnitPlanService(store, factory).execute(generated.state.run_id)
            self.assertEqual(CapabilityRunStatus.BUDGET_EXHAUSTED, stopped.state.status)
            self.assertIsNone(stopped.result); self.assertFalse(called)

    def test_plan_tamper_blocks_execution(self):
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store, generated = self.generate(Path(directory))
            (store.run_dir(generated.state.run_id) / "artifacts/java-unit-plan.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(CapabilityRunContractError, "integrity mismatch"):
                ExecuteJavaUnitPlanService(store).execute(generated.state.run_id)

    def test_accepted_execution_persists_normalized_and_native_evidence(self):
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store, generated = self.generate(Path(directory))
            class Executor:
                def execute(self, workspace, output):
                    del workspace, output
                    return ExecutionOutput("sha256:" + "a" * 64, ("run",), 0, 10, "", "", 2, 2, 0, 0, 0,
                                           "maven-surefire", "3.5.5", TestExecutionOutcome.PASSED,
                                           '<testsuite tests="2" failures="0" errors="0" skipped="0"/>',
                                           "surefire.xml", "application/junit+xml")
            completed = ExecuteJavaUnitPlanService(store, lambda root: Executor()).execute(generated.state.run_id)
            self.assertEqual((CapabilityRunStatus.SUCCEEDED, CapabilityRunClassification.ACCEPTED), (completed.state.status, completed.state.classification))
            self.assertEqual({"java_unit_test_plan", "java_unit_execution_result", "java_unit_surefire_xml"}, {item.kind for item in completed.state.evidence_refs})
            manifest = json.loads((store.run_dir(completed.state.run_id) / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["terminal"])

    def test_assertion_and_tool_results_remain_distinct(self):
        for outcome, classification in (
            (TestExecutionOutcome.ASSERTION_FAILURE, CapabilityRunClassification.FUNCTIONAL_FAILURE),
            (TestExecutionOutcome.TOOL_ERROR, CapabilityRunClassification.INFRASTRUCTURE_ERROR),
        ):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory(dir=".asef") as directory:
                store, generated = self.generate(Path(directory))
                class Executor:
                    def execute(self, workspace, output):
                        del workspace, output
                        return ExecutionOutput("sha256:" + "b" * 64, ("run",), 1, 1, "", "", 2 if outcome is TestExecutionOutcome.ASSERTION_FAILURE else None, 1 if outcome is TestExecutionOutcome.ASSERTION_FAILURE else None, 1 if outcome is TestExecutionOutcome.ASSERTION_FAILURE else None, 0, 0, "maven-surefire", "3.5.5", outcome)
                completed = ExecuteJavaUnitPlanService(store, lambda root: Executor()).execute(generated.state.run_id)
                self.assertEqual(classification, completed.state.classification)


if __name__ == "__main__": unittest.main()
