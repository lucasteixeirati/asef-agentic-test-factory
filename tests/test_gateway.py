from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from asef.adapters.gateway import GatewayError, OpenAIResponsesGateway, RecordedModelGateway
from asef.legacy.domain import BudgetLimits, BudgetUsage
from asef.runtime.budgets import BudgetController


class RecordedGatewayTests(unittest.TestCase):
    def test_replays_cassette_and_records_usage(self) -> None:
        usage = BudgetUsage()
        gateway = RecordedModelGateway(
            Path("tests/fixtures/cassettes/wf001_analysis_success.json"),
            BudgetController(BudgetLimits(), usage),
        )
        result = gateway.generate(prompt="ignored", schema={}, schema_name="wf001_analysis")
        self.assertTrue(result.recorded)
        self.assertEqual(result.output["clarification_required"], False)
        self.assertEqual(usage.model_calls, 1)
        self.assertEqual(usage.input_tokens, 72)

    def test_schema_mismatch_fails(self) -> None:
        gateway = RecordedModelGateway(
            Path("tests/fixtures/cassettes/wf001_analysis_success.json"),
            BudgetController(BudgetLimits(), BudgetUsage()),
        )
        with self.assertRaises(GatewayError):
            gateway.generate(prompt="ignored", schema={}, schema_name="different")

    def test_live_gateway_requires_key(self) -> None:
        with self.assertRaises(GatewayError):
            OpenAIResponsesGateway(
                BudgetController(BudgetLimits(api_budget_brl=10), BudgetUsage()),
                api_key="",
            )


if __name__ == "__main__":
    unittest.main()
