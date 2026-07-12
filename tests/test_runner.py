from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from asef_spike.budgets import BudgetController
from asef_spike.domain import BudgetLimits, BudgetUsage, RunStatus, WorkflowRequest
from asef_spike.gateway import InvalidStructuredOutput, ModelResult, RecordedModelGateway
from asef_spike.runner import AnalysisValidationError, DemoWorkflowRunner, validate_analysis_output


class DemoWorkflowRunnerTests(unittest.TestCase):
    class SequenceGateway:
        def __init__(self, outputs: list[dict | Exception], controller: BudgetController) -> None:
            self.outputs = iter(outputs)
            self.controller = controller
            self.prompts: list[str] = []

        def generate(self, *, prompt: str, schema: dict, schema_name: str) -> ModelResult:
            del schema, schema_name
            self.prompts.append(prompt)
            self.controller.reserve_model_call()
            self.controller.record_tokens(10, 5)
            output = next(self.outputs)
            if isinstance(output, Exception):
                raise output
            return ModelResult(
                output=output,
                model="sequence-test",
                response_id=f"response-{len(self.prompts)}",
                input_tokens=10,
                output_tokens=5,
                recorded=True,
            )

    def test_local_structured_output_validation_rejects_wrong_type(self) -> None:
        with self.assertRaises(AnalysisValidationError):
            validate_analysis_output(
                {
                    "behaviors": "not-a-list",
                    "risks": [],
                    "scenarios": [],
                    "clarification_required": False,
                }
            )

    def test_local_structured_output_validation_rejects_extra_key(self) -> None:
        with self.assertRaises(AnalysisValidationError):
            validate_analysis_output(
                {
                    "behaviors": [],
                    "risks": [],
                    "scenarios": [],
                    "clarification_required": False,
                    "unexpected": True,
                }
            )

    def test_demo_happy_path_writes_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            controller = BudgetController(BudgetLimits(), BudgetUsage())
            gateway = RecordedModelGateway(
                Path("tests/fixtures/cassettes/wf001_analysis_success.json"),
                controller,
            )
            state = DemoWorkflowRunner(gateway, root, controller).run(
                WorkflowRequest("Add", "Return the sum of two integers", "calculator.add")
            )

            self.assertEqual(state.status, RunStatus.SUCCEEDED)
            run_dir = root / state.run_id
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "state.json").exists())
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "SUCCEEDED")
            self.assertEqual(manifest["usage"]["model_calls"], 1)

    def test_invalid_input_fails_without_model_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            usage = BudgetUsage()
            controller = BudgetController(BudgetLimits(), usage)
            gateway = RecordedModelGateway(
                Path("tests/fixtures/cassettes/wf001_analysis_success.json"),
                controller,
            )
            state = DemoWorkflowRunner(gateway, Path(directory), controller).run(
                WorkflowRequest("", "", "")
            )
            self.assertEqual(state.status, RunStatus.FAILED)
            self.assertEqual(usage.model_calls, 0)

    def test_invalid_output_is_repaired_once_with_bounded_prompt(self) -> None:
        invalid = {
            "behaviors": "wrong",
            "risks": [],
            "scenarios": [],
            "clarification_required": False,
        }
        valid = {
            "behaviors": ["Add integers"],
            "risks": ["Boundary values"],
            "scenarios": ["Add two positive integers"],
            "clarification_required": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            usage = BudgetUsage()
            controller = BudgetController(BudgetLimits(max_provider_retries=1), usage)
            gateway = self.SequenceGateway([invalid, valid], controller)
            state = DemoWorkflowRunner(gateway, Path(directory), controller).run(
                WorkflowRequest("Add", "Return the sum of two integers", "calculator.add")
            )

        self.assertEqual(state.status, RunStatus.SUCCEEDED)
        self.assertEqual(usage.model_calls, 2)
        self.assertEqual(usage.provider_retries, 1)
        self.assertEqual(len(gateway.prompts), 2)
        self.assertIn("failed local schema validation", gateway.prompts[1])
        self.assertNotIn(str(invalid), gateway.prompts[1])
        self.assertEqual(state.errors[0]["type"], "PROVIDER_OUTPUT_INVALID")

    def test_repeated_invalid_output_exhausts_retry_budget_and_writes_evidence(self) -> None:
        invalid = {
            "behaviors": "wrong",
            "risks": [],
            "scenarios": [],
            "clarification_required": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            usage = BudgetUsage()
            controller = BudgetController(BudgetLimits(max_provider_retries=1), usage)
            gateway = self.SequenceGateway([invalid, invalid], controller)
            state = DemoWorkflowRunner(gateway, root, controller).run(
                WorkflowRequest("Add", "Return the sum of two integers", "calculator.add")
            )
            persisted = json.loads(
                (root / state.run_id / "state.json").read_text(encoding="utf-8")
            )

        self.assertEqual(state.status, RunStatus.BUDGET_EXHAUSTED)
        self.assertEqual(usage.model_calls, 2)
        self.assertEqual(usage.provider_retries, 1)
        self.assertEqual(
            [error["type"] for error in state.errors],
            ["PROVIDER_OUTPUT_INVALID", "PROVIDER_OUTPUT_INVALID", "BUDGET_EXCEEDED"],
        )
        self.assertEqual(persisted["status"], "BUDGET_EXHAUSTED")
        self.assertEqual(persisted["usage"]["provider_retries"], 1)

    def test_gateway_level_structured_error_uses_same_recovery_policy(self) -> None:
        valid = {
            "behaviors": ["Add integers"],
            "risks": ["Boundary values"],
            "scenarios": ["Add two positive integers"],
            "clarification_required": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            usage = BudgetUsage()
            controller = BudgetController(BudgetLimits(max_provider_retries=1), usage)
            gateway = self.SequenceGateway(
                [InvalidStructuredOutput("malformed provider JSON"), valid],
                controller,
            )
            state = DemoWorkflowRunner(gateway, Path(directory), controller).run(
                WorkflowRequest("Add", "Return the sum of two integers", "calculator.add")
            )

        self.assertEqual(state.status, RunStatus.SUCCEEDED)
        self.assertEqual(usage.model_calls, 2)
        self.assertEqual(usage.provider_retries, 1)
        self.assertEqual(state.errors[0]["type"], "PROVIDER_OUTPUT_INVALID")


if __name__ == "__main__":
    unittest.main()
