from __future__ import annotations

import http.client
import json
import time
from typing import Any
from urllib.parse import urlsplit

from ..api_contracts import ApiExecutionResult, ApiScenario, ApiScenarioResult, ApiTestPlan
from ..skills.backend_api import BackendApiPolicy, BackendApiSkill


def _contains_subset(observed: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(observed, dict) and all(
            key in observed and _contains_subset(observed[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(observed, list) and observed == expected
    return observed == expected


class LoopbackHttpApiExecutor:
    """Execute a validated REST plan without proxies, redirects or external hosts."""

    def __init__(self, policy: BackendApiPolicy | None = None) -> None:
        self.policy = policy or BackendApiPolicy()
        self.skill = BackendApiSkill(self.policy)

    def execute(self, plan: ApiTestPlan) -> ApiExecutionResult:
        self.skill.validate(plan)
        origin = urlsplit(plan.base_url)
        results = tuple(self._execute_scenario(origin.hostname or "", origin.port or 0, item) for item in plan.scenarios)
        passed = sum(item.status == "PASSED" for item in results)
        failed = sum(item.status == "FAILED" for item in results)
        errors = sum(item.status == "ERROR" for item in results)
        status = "ERROR" if errors else ("FAILED" if failed else "PASSED")
        report = ApiExecutionResult(
            plan_id=plan.plan_id,
            status=status,
            tests=len(results),
            passed=passed,
            failed=failed,
            errors=errors,
            scenarios=results,
        )
        report.validate()
        return report

    def _execute_scenario(self, host: str, port: int, scenario: ApiScenario) -> ApiScenarioResult:
        started = time.monotonic()
        connection = http.client.HTTPConnection(host, port, timeout=self.policy.timeout_seconds)
        body: bytes | None = None
        headers = {name: value for name, value in scenario.headers}
        if scenario.json_body is not None:
            body = json.dumps(scenario.json_body, allow_nan=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            connection.request(scenario.method, scenario.path, body=body, headers=headers)
            response = connection.getresponse()
            content = response.read(self.policy.max_response_bytes + 1)
            if len(content) > self.policy.max_response_bytes:
                return self._result(scenario, started, "ERROR", response.status, len(content), "RESPONSE_LIMIT_EXCEEDED")
            if response.status != scenario.assertion.expected_status:
                return self._result(scenario, started, "FAILED", response.status, len(content), "STATUS_MISMATCH")
            expected = scenario.assertion.expected_json_subset
            if expected is not None:
                try:
                    observed = json.loads(content.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return self._result(scenario, started, "FAILED", response.status, len(content), "INVALID_JSON_RESPONSE")
                if not _contains_subset(observed, expected):
                    return self._result(scenario, started, "FAILED", response.status, len(content), "JSON_SUBSET_MISMATCH")
            return self._result(scenario, started, "PASSED", response.status, len(content), None)
        except (OSError, http.client.HTTPException) as exc:
            return self._result(
                scenario,
                started,
                "ERROR",
                None,
                0,
                f"HTTP_EXECUTION_{type(exc).__name__.upper()}",
            )
        finally:
            connection.close()

    @staticmethod
    def _result(
        scenario: ApiScenario,
        started: float,
        status: str,
        observed_status: int | None,
        response_bytes: int,
        diagnostic_code: str | None,
    ) -> ApiScenarioResult:
        return ApiScenarioResult(
            scenario_id=scenario.scenario_id,
            status=status,
            observed_status=observed_status,
            duration_ms=max(0, round((time.monotonic() - started) * 1_000)),
            response_bytes=response_bytes,
            diagnostic_code=diagnostic_code,
        )

