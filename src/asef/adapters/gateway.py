from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..runtime.budgets import BudgetController


class GatewayError(RuntimeError):
    pass


class InvalidStructuredOutput(GatewayError):
    pass


@dataclass(slots=True, frozen=True)
class ModelResult:
    output: dict[str, Any]
    model: str
    response_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    recorded: bool = False


class ModelGateway(Protocol):
    def generate(self, *, prompt: str, schema: dict[str, Any], schema_name: str) -> ModelResult: ...


class RecordedModelGateway:
    def __init__(self, cassette_path: Path, budgets: BudgetController) -> None:
        self.cassette_path = cassette_path
        self.budgets = budgets

    def generate(self, *, prompt: str, schema: dict[str, Any], schema_name: str) -> ModelResult:
        del prompt, schema
        self.budgets.reserve_model_call()
        cassette = json.loads(self.cassette_path.read_text(encoding="utf-8"))
        if cassette.get("schema_name") != schema_name:
            raise GatewayError(
                f"cassette schema mismatch: expected {schema_name}, got {cassette.get('schema_name')}"
            )
        usage = cassette.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        self.budgets.record_tokens(input_tokens, output_tokens)
        return ModelResult(
            output=cassette["output"],
            model=cassette.get("model", "recorded"),
            response_id=cassette.get("response_id", "cassette"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            recorded=True,
        )


class OpenAIResponsesGateway:
    """Minimal direct HTTP gateway for the framework comparison spike."""

    endpoint = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        budgets: BudgetController,
        *,
        model: str | None = None,
        api_key: str | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        self.budgets = budgets
        self.model = model or os.environ.get("ASEF_OPENAI_MODEL", "gpt-5.4-mini-2026-03-17")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.timeout_seconds = timeout_seconds
        if not self.api_key:
            raise GatewayError("OPENAI_API_KEY is not available to the current process")

    def generate(self, *, prompt: str, schema: dict[str, Any], schema_name: str) -> ModelResult:
        if self.budgets.limits.api_budget_brl <= 0:
            raise GatewayError("live calls require an explicit positive api_budget_brl")
        self.budgets.reserve_model_call()
        body = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": 600,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        request = Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1_000]
            raise GatewayError(f"OpenAI HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise GatewayError(f"OpenAI connection failed: {exc.reason}") from exc

        output_text = _extract_output_text(payload)
        try:
            structured = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise InvalidStructuredOutput(
                "response did not contain valid JSON structured output"
            ) from exc

        usage = payload.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        self.budgets.record_tokens(input_tokens, output_tokens)
        return ModelResult(
            output=structured,
            model=payload.get("model", self.model),
            response_id=payload.get("id", "unknown"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


def _extract_output_text(payload: dict[str, Any]) -> str:
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return str(content.get("text", ""))
    raise GatewayError("response did not contain output_text")
