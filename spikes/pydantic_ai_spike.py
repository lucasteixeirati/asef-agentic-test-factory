from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.models import Model

from asef_spike.budgets import BudgetController
from asef_spike.gateway import GatewayError, InvalidStructuredOutput, ModelResult


class RiskAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    behaviors: list[str]
    risks: list[str]
    scenarios: list[str]
    clarification_required: bool


class PydanticAIModelGateway:
    """Typed provider adapter spike; it does not control workflow transitions."""

    def __init__(self, budgets: BudgetController, model: Model) -> None:
        self.budgets = budgets
        self.model = model
        self.agent = Agent(
            model,
            output_type=RiskAnalysis,
            instructions="Analyze requirements for evidence-based software test design.",
            retries=0,
        )

    def generate(self, *, prompt: str, schema: dict[str, Any], schema_name: str) -> ModelResult:
        del schema
        if schema_name != "wf001_analysis":
            raise GatewayError(f"unsupported schema for spike: {schema_name}")

        self.budgets.reserve_model_call()
        try:
            result = self.agent.run_sync(prompt)
        except UnexpectedModelBehavior as exc:
            raise InvalidStructuredOutput(
                "PydanticAI could not produce valid structured output"
            ) from exc

        usage = result.usage
        input_tokens = int(usage.input_tokens or 0)
        output_tokens = int(usage.output_tokens or 0)
        self.budgets.record_tokens(input_tokens, output_tokens)
        return ModelResult(
            output=result.output.model_dump(),
            model=getattr(self.model, "model_name", type(self.model).__name__),
            response_id="not-exposed-by-spike",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            recorded=True,
        )
