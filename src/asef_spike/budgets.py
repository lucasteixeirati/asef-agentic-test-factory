from __future__ import annotations

from dataclasses import dataclass

from .domain import BudgetLimits, BudgetUsage


class BudgetExceeded(RuntimeError):
    def __init__(self, budget: str, used: float, limit: float) -> None:
        super().__init__(f"budget exceeded: {budget} used={used} limit={limit}")
        self.budget = budget
        self.used = used
        self.limit = limit


@dataclass(slots=True)
class BudgetController:
    limits: BudgetLimits
    usage: BudgetUsage

    def reserve_model_call(self) -> None:
        next_value = self.usage.model_calls + 1
        self._check("model_calls", next_value, self.limits.max_model_calls)
        self.usage.model_calls = next_value

    def record_tokens(self, input_tokens: int, output_tokens: int) -> None:
        next_input = self.usage.input_tokens + max(input_tokens, 0)
        next_output = self.usage.output_tokens + max(output_tokens, 0)
        self._check("input_tokens", next_input, self.limits.max_input_tokens)
        self._check("output_tokens", next_output, self.limits.max_output_tokens)
        self.usage.input_tokens = next_input
        self.usage.output_tokens = next_output

    def reserve_test_correction(self) -> None:
        next_value = self.usage.test_corrections + 1
        self._check("test_corrections", next_value, self.limits.max_test_corrections)
        self.usage.test_corrections = next_value

    def reserve_provider_retry(self) -> None:
        next_value = self.usage.provider_retries + 1
        self._check("provider_retries", next_value, self.limits.max_provider_retries)
        self.usage.provider_retries = next_value

    @staticmethod
    def _check(name: str, value: float, limit: float) -> None:
        if value > limit:
            raise BudgetExceeded(name, value, limit)
