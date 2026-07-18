from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from asef.adapters.api_plan_agent import ApiPlanAgentAdapter, ApiPlanOutputError
from asef.adapters.gateway import ModelResult
from asef.openapi_contracts import OpenApiContractError, OpenApiJsonLoader
from asef.skills.backend_api import BackendApiPolicy


class OpenApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        Path(".asef").mkdir(exist_ok=True)

    @staticmethod
    def _document() -> dict[str, object]:
        return {
            "openapi": "3.1.0",
            "info": {"title": "Local fixture", "version": "1.0.0"},
            "servers": [{"url": "https://untrusted.example"}],
            "paths": {
                "/health": {
                    "get": {
                        "operationId": "health",
                        "summary": "Read health",
                        "responses": {"200": {"description": "healthy"}},
                    },
                    "post": {"responses": {"201": {"description": "ignored mutation"}}},
                },
                "/items/{item_id}": {
                    "get": {"responses": {"200": {"description": "ignored template"}}}
                },
            },
        }

    def _load(self, value: object):
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            path = Path(directory) / "openapi.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return OpenApiJsonLoader().load(path)

    def test_extracts_only_concrete_read_only_success_operations(self) -> None:
        summary = self._load(self._document())
        self.assertEqual("3.1.0", summary.openapi_version)
        self.assertEqual([("GET", "/health", 200)], [
            (item.method, item.path, item.expected_status) for item in summary.operations
        ])
        self.assertNotIn("untrusted.example", json.dumps(summary.prompt_value()))

    def test_rejects_duplicate_keys_and_external_references(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"openapi":"3.1.0","openapi":"3.0.3"}', encoding="utf-8")
            with self.assertRaisesRegex(OpenApiContractError, "duplicate JSON key"):
                OpenApiJsonLoader().load(path)
        document = self._document()
        document["components"] = {"schemas": {"Remote": {"$ref": "https://example.test/schema"}}}
        with self.assertRaisesRegex(OpenApiContractError, "external OpenAPI references"):
            self._load(document)

    def test_agent_rejects_scenario_outside_contract_and_preserves_usage(self) -> None:
        class Gateway:
            def generate(self, **kwargs):
                self.prompt = kwargs["prompt"]
                return ModelResult(
                    output={"scenarios": [{
                        "description": "outside", "method": "GET", "path": "/admin",
                        "expected_status": 200, "expected_json_properties": [],
                    }]},
                    model="fake", response_id="response-1", provider="recorded",
                    input_tokens=31, output_tokens=17,
                )

        gateway = Gateway()
        summary = self._load(self._document())
        with self.assertRaisesRegex(ApiPlanOutputError, "outside the supplied OpenAPI") as raised:
            ApiPlanAgentAdapter(gateway, BackendApiPolicy(allowed_ports=(8765,))).generate(
                "Check the documented health operation", "http://127.0.0.1:8765", summary
            )
        self.assertEqual((31, 17), (raised.exception.input_tokens, raised.exception.output_tokens))
        self.assertIn('"path": "/health"', gateway.prompt)
        self.assertNotIn("untrusted.example", gateway.prompt)


if __name__ == "__main__":
    unittest.main()
