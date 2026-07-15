from __future__ import annotations

import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from asef.adapters.gateway import (
    GatewayError,
    InvalidStructuredOutput,
    OpenAIResponsesGateway,
    RecordedModelGateway,
)
from asef.application.ports import (
    ProviderPermanentError,
    ProviderRefusalError,
    ProviderTransientError,
)
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
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(GatewayError):
            OpenAIResponsesGateway(
                BudgetController(BudgetLimits(api_budget_brl=10), BudgetUsage()),
                api_key="",
            )

    def test_live_gateway_requires_positive_budget_before_transport(self) -> None:
        gateway = OpenAIResponsesGateway(
            BudgetController(BudgetLimits(api_budget_brl=0), BudgetUsage()),
            api_key="test-key",
        )
        with patch("asef.adapters.gateway.urlopen") as transport, self.assertRaisesRegex(
            GatewayError, "positive api_budget_brl"
        ):
            gateway.generate(prompt="x", schema={}, schema_name="result")
        transport.assert_not_called()

    def test_live_gateway_rejects_non_finite_budget_before_transport(self) -> None:
        with patch("asef.adapters.gateway.urlopen") as transport, self.assertRaisesRegex(
            GatewayError, "must be finite"
        ):
            OpenAIResponsesGateway(api_key="test-key", api_budget_brl=float("nan"))
        transport.assert_not_called()

    def test_live_gateway_parses_structured_output_and_usage(self) -> None:
        usage = BudgetUsage()
        gateway = OpenAIResponsesGateway(
            BudgetController(BudgetLimits(api_budget_brl=10), usage),
            api_key="test-key",
            model="test-model",
        )
        payload = {
            "id": "response-1",
            "model": "test-model",
            "status": "completed",
            "usage": {"input_tokens": 9, "output_tokens": 4},
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": '{"ok": true}'}]}
            ],
        }
        with patch("asef.adapters.gateway.urlopen", return_value=_Response(payload)) as transport:
            result = gateway.generate(prompt="x", schema={"type": "object"}, schema_name="result")
        self.assertEqual(result.output, {"ok": True})
        self.assertEqual((usage.model_calls, usage.input_tokens, usage.output_tokens), (1, 9, 4))
        request = transport.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")

    def test_live_gateway_normalizes_transport_and_output_failures(self) -> None:
        def gateway() -> OpenAIResponsesGateway:
            return OpenAIResponsesGateway(
                BudgetController(BudgetLimits(api_budget_brl=10), BudgetUsage()),
                api_key="test-key",
            )

        http_error = HTTPError(
            "https://example.invalid",
            429,
            "rate limited",
            {},
            io.BytesIO(b'{"error":"limited"}'),
        )
        with patch("asef.adapters.gateway.urlopen", side_effect=http_error), self.assertRaisesRegex(
            ProviderTransientError, "HTTP 429"
        ):
            gateway().generate(prompt="x", schema={}, schema_name="result")
        with patch(
            "asef.adapters.gateway.urlopen", side_effect=URLError("offline")
        ), self.assertRaisesRegex(ProviderTransientError, "connection failed"):
            gateway().generate(prompt="x", schema={}, schema_name="result")
        with patch(
            "asef.adapters.gateway.urlopen",
            return_value=_Response({"output": [], "usage": {"input_tokens": 1, "output_tokens": 1}}),
        ), self.assertRaisesRegex(ProviderPermanentError, "output_text"):
            gateway().generate(prompt="x", schema={}, schema_name="result")
        invalid = {
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "not-json"}]}
            ]
        }
        with patch(
            "asef.adapters.gateway.urlopen", return_value=_Response(invalid)
        ), self.assertRaises(InvalidStructuredOutput):
            gateway().generate(prompt="x", schema={}, schema_name="result")
        with patch(
            "asef.adapters.gateway.urlopen",
            return_value=_Response(
                {"status": "incomplete", "usage": {"input_tokens": 1, "output_tokens": 1}}
            ),
        ), self.assertRaisesRegex(InvalidStructuredOutput, "incomplete"):
            gateway().generate(prompt="x", schema={}, schema_name="result")
        refusal = {
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "output": [
                {"type": "message", "content": [{"type": "refusal", "refusal": "declined"}]}
            ]
        }
        with patch(
            "asef.adapters.gateway.urlopen", return_value=_Response(refusal)
        ), self.assertRaises(ProviderRefusalError):
            gateway().generate(prompt="x", schema={}, schema_name="result")


class _Response:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


if __name__ == "__main__":
    unittest.main()
