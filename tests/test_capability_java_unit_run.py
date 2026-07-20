from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from asef.adapters.capability_run_store import CapabilityRunStore
from asef.adapters.gateway import ModelResult
from asef.adapters.java_unit_plan_agent import JavaUnitPlanAgentAdapter, JavaUnitPlanOutputError
from asef.application.java_unit_run import ExecuteJavaUnitPlanService, GenerateJavaUnitPlanService
from asef.application.ports import ExecutionOutput
from asef.capability_runs import CapabilityRunClassification, CapabilityRunContractError, CapabilityRunStatus
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
