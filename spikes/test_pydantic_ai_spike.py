from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pydantic_ai import models
from pydantic_ai.models.test import TestModel

from asef_spike.budgets import BudgetController
from asef_spike.domain import BudgetLimits, BudgetUsage, WorkflowRequest
from asef_spike.gateway import GatewayError
from asef_spike.runner import DemoWorkflowRunner, RISK_SCHEMA
from pydantic_ai_spike import PydanticAIModelGateway


VALID_ANALYSIS = {
    "behaviors": ["Return the sum of two integers"],
    "risks": ["Integer boundaries"],
    "scenarios": ["Add two positive integers"],
    "clarification_required": False,
}


class PydanticAISpikeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        models.ALLOW_MODEL_REQUESTS = False

    def gateway(self, usage: BudgetUsage, output: dict = VALID_ANALYSIS) -> PydanticAIModelGateway:
        return PydanticAIModelGateway(
            BudgetController(BudgetLimits(), usage),
            TestModel(custom_output_args=output),
        )

    def test_typed_output_conforms_to_existing_gateway_contract(self) -> None:
        usage = BudgetUsage()
        result = self.gateway(usage).generate(
            prompt="Analyze addition",
            schema=RISK_SCHEMA,
            schema_name="wf001_analysis",
        )
        self.assertEqual(result.output, VALID_ANALYSIS)
        self.assertEqual(usage.model_calls, 1)
        self.assertGreater(usage.input_tokens, 0)
        self.assertGreater(usage.output_tokens, 0)

    def test_invalid_typed_output_becomes_gateway_error(self) -> None:
        invalid = {**VALID_ANALYSIS, "clarification_required": "not-a-boolean"}
        with self.assertRaises(GatewayError):
            self.gateway(BudgetUsage(), invalid).generate(
                prompt="Analyze addition",
                schema=RISK_SCHEMA,
                schema_name="wf001_analysis",
            )

    def test_extra_field_becomes_gateway_error(self) -> None:
        invalid = {**VALID_ANALYSIS, "unexpected": "field"}
        with self.assertRaises(GatewayError):
            self.gateway(BudgetUsage(), invalid).generate(
                prompt="Analyze addition",
                schema=RISK_SCHEMA,
                schema_name="wf001_analysis",
            )

    def test_unknown_schema_is_rejected_without_model_call(self) -> None:
        usage = BudgetUsage()
        with self.assertRaises(GatewayError):
            self.gateway(usage).generate(prompt="x", schema={}, schema_name="unknown")
        self.assertEqual(usage.model_calls, 0)

    def test_gateway_runs_existing_workflow_without_owning_control_flow(self) -> None:
        usage = BudgetUsage()
        with tempfile.TemporaryDirectory() as directory:
            gateway = self.gateway(usage)
            runner = DemoWorkflowRunner(
                gateway,
                output_root=Path(directory),
                budget_controller=gateway.budgets,
            )
            state = runner.run(
                WorkflowRequest("Add", "Return the sum of two integers", "calculator.add")
            )
        self.assertEqual(state.status.value, "SUCCEEDED")
        self.assertEqual(usage.model_calls, 1)


if __name__ == "__main__":
    unittest.main()
