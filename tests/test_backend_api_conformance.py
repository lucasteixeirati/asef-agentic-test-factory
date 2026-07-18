from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from asef.api_contracts import ApiAssertion, ApiScenario, ApiTestPlan
from asef.openapi_contracts import OpenApiContractError, OpenApiJsonLoader
from asef.skills.backend_api import BackendApiPolicy, BackendApiPolicyError, BackendApiSkill


class BackendApiConformanceDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        raw = json.loads(Path("datasets/backend-api/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("1.0.0", raw["schema_version"])
        self.cases = raw["cases"]
        self.skill = BackendApiSkill(BackendApiPolicy(allowed_ports=(8765,)))
        Path(".asef").mkdir(exist_ok=True)

    @staticmethod
    def _plan(*, host="127.0.0.1", method="GET", path="/health", headers=()):
        return ApiTestPlan(
            "API-CONFORMANCE-PLAN", f"http://{host}:8765",
            (ApiScenario("SCN-001", "bounded case", method, path, ApiAssertion(200), headers=headers),),
        )

    def _evaluate(self, control: str) -> str:
        try:
            if control == "loopback_plan":
                self.skill.validate(self._plan())
            elif control == "external_host":
                self.skill.validate(self._plan(host="example.test"))
            elif control == "mutating_method":
                self.skill.validate(self._plan(method="POST"))
            elif control == "sensitive_header":
                self.skill.validate(self._plan(headers=(("Authorization", "redacted"),)))
            elif control == "sensitive_query":
                self.skill.validate(self._plan(path="/health?token=redacted"))
            elif control.startswith("openapi_"):
                self._load_openapi(control)
            else:
                self.fail(f"unknown dataset control: {control}")
        except (BackendApiPolicyError, OpenApiContractError):
            return "POLICY_BLOCKED"
        return "ACCEPTED"

    def _load_openapi(self, control: str) -> None:
        if control == "openapi_duplicate_key":
            content = '{"openapi":"3.1.0","openapi":"3.0.3"}'
        else:
            document = {
                "openapi": "3.1.0", "info": {"title": "Fixture", "version": "1"},
                "paths": {"/health": {"get": {"responses": {"200": {"description": "ok"}}}}},
            }
            if control == "openapi_external_ref":
                document["components"] = {"schemas": {"X": {"$ref": "https://example.test/x"}}}
            content = json.dumps(document)
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            path = Path(directory) / "openapi.json"
            path.write_text(content, encoding="utf-8")
            OpenApiJsonLoader().load(path)

    def test_all_declared_cases_match_their_oracles(self) -> None:
        self.assertEqual(8, len(self.cases))
        self.assertEqual(len(self.cases), len({case["case_id"] for case in self.cases}))
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                self.assertEqual(case["expected"], self._evaluate(case["control"]))


if __name__ == "__main__":
    unittest.main()
