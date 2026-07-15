from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..runtime.budgets import BudgetController
from ..application.ports import (
    ProviderPermanentError,
    ProviderRefusalError,
    ProviderTransientError,
)


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
    provider: str = "recorded"
    latency_ms: int = 0


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
            provider="recorded",
        )


class OpenAIResponsesGateway:
    """Minimal direct HTTP gateway for the framework comparison spike."""

    endpoint = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        budgets: BudgetController | None = None,
        *,
        model: str | None = None,
        api_key: str | None = None,
        timeout_seconds: int = 60,
        api_budget_brl: float | None = None,
        max_output_tokens: int = 600,
    ) -> None:
        self.budgets = budgets
        self.model = model or os.environ.get("ASEF_OPENAI_MODEL", "gpt-5.4-mini-2026-03-17")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.timeout_seconds = timeout_seconds
        self.api_budget_brl = (
            budgets.limits.api_budget_brl if api_budget_brl is None and budgets is not None else api_budget_brl
        )
        self.max_output_tokens = max_output_tokens
        if not self.api_key:
            raise GatewayError("OPENAI_API_KEY is not available to the current process")
        if self.timeout_seconds < 1:
            raise GatewayError("provider timeout must be positive")
        if self.max_output_tokens < 1:
            raise GatewayError("max_output_tokens must be positive")
        if self.api_budget_brl is not None and not math.isfinite(self.api_budget_brl):
            raise GatewayError("api_budget_brl must be finite")

    def generate(self, *, prompt: str, schema: dict[str, Any], schema_name: str) -> ModelResult:
        if (
            self.api_budget_brl is None
            or not math.isfinite(self.api_budget_brl)
            or self.api_budget_brl <= 0
        ):
            raise GatewayError("live calls require an explicit positive api_budget_brl")
        if self.budgets is not None:
            self.budgets.reserve_model_call()
        body = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": self.max_output_tokens,
            "store": False,
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
        started = time.perf_counter()
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in {408, 409, 429} or exc.code >= 500:
                raise ProviderTransientError(f"OpenAI HTTP {exc.code}") from exc
            raise ProviderPermanentError(f"OpenAI HTTP {exc.code}") from exc
        except URLError as exc:
            raise ProviderTransientError("OpenAI connection failed") from exc
        except (TimeoutError, json.JSONDecodeError) as exc:
            raise ProviderTransientError("OpenAI returned an unavailable or invalid response") from exc
        latency_ms = max(0, int((time.perf_counter() - started) * 1_000))

        usage = payload.get("usage")
        if not isinstance(usage, dict):
            raise ProviderPermanentError("OpenAI response did not contain token usage")
        try:
            input_tokens = int(usage.get("input_tokens", 0))
            output_tokens = int(usage.get("output_tokens", 0))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ProviderPermanentError("OpenAI response contained invalid usage") from exc
        if input_tokens < 0 or output_tokens < 0:
            raise ProviderPermanentError("OpenAI response contained negative token usage")
        try:
            output_text = _extract_output_text(payload)
            structured = json.loads(output_text)
        except (ProviderPermanentError, InvalidStructuredOutput) as exc:
            exc.provider = "openai"
            exc.model = str(payload.get("model", self.model))
            exc.response_id = str(payload.get("id", "unknown"))
            exc.input_tokens = input_tokens
            exc.output_tokens = output_tokens
            exc.latency_ms = latency_ms
            exc.usage_observed = True
            raise
        except json.JSONDecodeError as exc:
            invalid = InvalidStructuredOutput(
                "response did not contain valid JSON structured output"
            )
            invalid.provider = "openai"
            invalid.model = str(payload.get("model", self.model))
            invalid.response_id = str(payload.get("id", "unknown"))
            invalid.input_tokens = input_tokens
            invalid.output_tokens = output_tokens
            invalid.latency_ms = latency_ms
            invalid.usage_observed = True
            raise invalid from exc
        if self.budgets is not None:
            self.budgets.record_tokens(input_tokens, output_tokens)
        return ModelResult(
            output=structured,
            model=payload.get("model", self.model),
            response_id=payload.get("id", "unknown"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider="openai",
            latency_ms=latency_ms,
        )


def _extract_output_text(payload: dict[str, Any]) -> str:
    if payload.get("status") == "failed" or payload.get("error"):
        raise ProviderPermanentError("OpenAI response reported a provider error")
    if payload.get("status") == "incomplete":
        raise InvalidStructuredOutput("OpenAI response was incomplete")
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal" or content.get("refusal"):
                raise ProviderRefusalError("OpenAI refused the structured-output request")
            if content.get("type") == "output_text":
                return str(content.get("text", ""))
    raise ProviderPermanentError("OpenAI response did not contain output_text")
