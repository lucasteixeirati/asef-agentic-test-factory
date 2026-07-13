from __future__ import annotations

import unittest

from asef.legacy.domain import BudgetLimits, BudgetUsage
from asef.runtime.budgets import BudgetController, BudgetExceeded


class BudgetControllerTests(unittest.TestCase):
    def test_model_call_limit(self) -> None:
        controller = BudgetController(BudgetLimits(max_model_calls=1), BudgetUsage())
        controller.reserve_model_call()
        with self.assertRaises(BudgetExceeded) as raised:
            controller.reserve_model_call()
        self.assertEqual(raised.exception.budget, "model_calls")
        self.assertEqual(raised.exception.used, 2)
        self.assertEqual(raised.exception.limit, 1)
        self.assertEqual(
            str(raised.exception),
            "budget exceeded: model_calls used=2 limit=1",
        )

    def test_token_limit_does_not_partially_update_usage(self) -> None:
        usage = BudgetUsage()
        controller = BudgetController(BudgetLimits(max_input_tokens=10), usage)
        with self.assertRaises(BudgetExceeded):
            controller.record_tokens(11, 1)
        self.assertEqual(usage.input_tokens, 0)
        self.assertEqual(usage.output_tokens, 0)

    def test_test_correction_limit(self) -> None:
        controller = BudgetController(BudgetLimits(max_test_corrections=0), BudgetUsage())
        with self.assertRaises(BudgetExceeded):
            controller.reserve_test_correction()

    def test_provider_retry_limit(self) -> None:
        usage = BudgetUsage()
        controller = BudgetController(BudgetLimits(max_provider_retries=1), usage)
        controller.reserve_provider_retry()
        with self.assertRaises(BudgetExceeded):
            controller.reserve_provider_retry()
        self.assertEqual(usage.provider_retries, 1)


if __name__ == "__main__":
    unittest.main()
