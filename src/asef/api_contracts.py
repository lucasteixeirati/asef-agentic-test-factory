from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit


class ApiContractError(ValueError):
    """An API plan or result violates the bounded REST contract."""


@dataclass(slots=True, frozen=True)
class ApiAssertion:
    expected_status: int
    expected_json_subset: dict[str, Any] | None = None

    def validate(self) -> None:
        if not 100 <= self.expected_status <= 599:
            raise ApiContractError("expected_status must be a valid HTTP status")
        if self.expected_json_subset is not None:
            if not isinstance(self.expected_json_subset, dict):
                raise ApiContractError("expected_json_subset must be an object")
            try:
                json.dumps(self.expected_json_subset, allow_nan=False)
            except (TypeError, ValueError) as exc:
                raise ApiContractError("expected_json_subset must be finite JSON") from exc


@dataclass(slots=True, frozen=True)
class ApiScenario:
    scenario_id: str
    description: str
    method: str
    path: str
    assertion: ApiAssertion
    headers: tuple[tuple[str, str], ...] = ()
    json_body: dict[str, Any] | None = None

    def validate(self) -> None:
        if not self.scenario_id.startswith("SCN-") or not self.description.strip():
            raise ApiContractError("scenario id and description are required")
        if self.method != self.method.upper() or not self.method.isalpha():
            raise ApiContractError("method must be an uppercase HTTP token")
        parsed = urlsplit(self.path)
        if (
            not self.path.startswith("/")
            or self.path.startswith("//")
            or parsed.scheme
            or parsed.netloc
            or parsed.fragment
            or "\r" in self.path
            or "\n" in self.path
        ):
            raise ApiContractError("scenario path must be a relative absolute-path without fragment")
        if len(self.path) > 2_048:
            raise ApiContractError("scenario path exceeds the 2048 character limit")
        names: set[str] = set()
        for name, value in self.headers:
            normalized = name.strip().lower()
            if (
                not normalized
                or normalized in names
                or not all(character.isalnum() or character in "-_" for character in normalized)
                or "\r" in value
                or "\n" in value
            ):
                raise ApiContractError("headers must be unique and free of control line breaks")
            names.add(normalized)
        if self.json_body is not None:
            if not isinstance(self.json_body, dict):
                raise ApiContractError("json_body must be an object")
            try:
                encoded = json.dumps(self.json_body, allow_nan=False).encode("utf-8")
            except (TypeError, ValueError) as exc:
                raise ApiContractError("json_body must be finite JSON") from exc
            if len(encoded) > 65_536:
                raise ApiContractError("json_body exceeds the 65536 byte limit")
        self.assertion.validate()


@dataclass(slots=True, frozen=True)
class ApiTestPlan:
    plan_id: str
    base_url: str
    scenarios: tuple[ApiScenario, ...]
    schema_version: str = "1.0.0"

    def validate(self) -> None:
        if self.schema_version != "1.0.0" or not self.plan_id.strip():
            raise ApiContractError("supported schema_version and plan_id are required")
        parsed = urlsplit(self.base_url)
        if (
            parsed.scheme != "http"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ApiContractError("base_url must be an HTTP origin without credentials, path, query or fragment")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ApiContractError("base_url contains an invalid port") from exc
        if port is None:
            raise ApiContractError("base_url must declare an explicit port")
        if not self.scenarios:
            raise ApiContractError("at least one API scenario is required")
        ids = [scenario.scenario_id for scenario in self.scenarios]
        if len(ids) != len(set(ids)):
            raise ApiContractError("scenario ids must be unique")
        for scenario in self.scenarios:
            scenario.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        scenarios: list[dict[str, Any]] = []
        for scenario in self.scenarios:
            item: dict[str, Any] = {
                "scenario_id": scenario.scenario_id,
                "description": scenario.description,
                "method": scenario.method,
                "path": scenario.path,
                "assertion": {
                    "expected_status": scenario.assertion.expected_status,
                },
            }
            if scenario.assertion.expected_json_subset is not None:
                item["assertion"]["expected_json_subset"] = scenario.assertion.expected_json_subset
            if scenario.headers:
                item["headers"] = dict(scenario.headers)
            if scenario.json_body is not None:
                item["json_body"] = scenario.json_body
            scenarios.append(item)
        return {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "base_url": self.base_url,
            "scenarios": scenarios,
        }


@dataclass(slots=True, frozen=True)
class ApiScenarioResult:
    scenario_id: str
    status: str
    observed_status: int | None
    duration_ms: int
    response_bytes: int
    diagnostic_code: str | None = None


@dataclass(slots=True, frozen=True)
class ApiExecutionResult:
    plan_id: str
    status: str
    tests: int
    passed: int
    failed: int
    errors: int
    scenarios: tuple[ApiScenarioResult, ...]
    schema_version: str = "1.0.0"

    def validate(self) -> None:
        if self.schema_version != "1.0.0" or self.status not in {"PASSED", "FAILED", "ERROR"}:
            raise ApiContractError("invalid API execution result header")
        if min(self.tests, self.passed, self.failed, self.errors) < 0:
            raise ApiContractError("API execution counts cannot be negative")
        if self.tests != len(self.scenarios) or self.tests != self.passed + self.failed + self.errors:
            raise ApiContractError("API execution counts do not reconcile")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "status": self.status,
            "tests": self.tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "scenarios": [
                {
                    "scenario_id": item.scenario_id,
                    "status": item.status,
                    "observed_status": item.observed_status,
                    "duration_ms": item.duration_ms,
                    "response_bytes": item.response_bytes,
                    "diagnostic_code": item.diagnostic_code,
                }
                for item in self.scenarios
            ],
        }


def api_plan_from_dict(raw: Any) -> ApiTestPlan:
    if not isinstance(raw, dict):
        raise ApiContractError("API plan root must be an object")
    allowed_root = {"schema_version", "plan_id", "base_url", "scenarios"}
    if set(raw) != allowed_root:
        raise ApiContractError("API plan root fields do not match schema 1.0.0")
    if not isinstance(raw["scenarios"], list):
        raise ApiContractError("scenarios must be an array")
    scenarios: list[ApiScenario] = []
    for item in raw["scenarios"]:
        if not isinstance(item, dict):
            raise ApiContractError("each scenario must be an object")
        required = {"scenario_id", "description", "method", "path", "assertion"}
        optional = {"headers", "json_body"}
        if not required.issubset(item) or set(item) - required - optional:
            raise ApiContractError("scenario fields do not match schema 1.0.0")
        assertion_raw = item["assertion"]
        if not isinstance(assertion_raw, dict) or set(assertion_raw) - {
            "expected_status",
            "expected_json_subset",
        } or "expected_status" not in assertion_raw:
            raise ApiContractError("assertion fields do not match schema 1.0.0")
        status = assertion_raw["expected_status"]
        if isinstance(status, bool) or not isinstance(status, int):
            raise ApiContractError("expected_status must be an integer")
        headers_raw = item.get("headers", {})
        if not isinstance(headers_raw, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in headers_raw.items()
        ):
            raise ApiContractError("headers must be a string map")
        string_fields = (item["scenario_id"], item["description"], item["method"], item["path"])
        if any(not isinstance(value, str) for value in string_fields):
            raise ApiContractError("scenario identity, description, method and path must be strings")
        scenarios.append(
            ApiScenario(
                scenario_id=item["scenario_id"],
                description=item["description"],
                method=item["method"],
                path=item["path"],
                headers=tuple(headers_raw.items()),
                json_body=item.get("json_body"),
                assertion=ApiAssertion(
                    expected_status=status,
                    expected_json_subset=assertion_raw.get("expected_json_subset"),
                ),
            )
        )
    if not all(isinstance(raw[field], str) for field in ("schema_version", "plan_id", "base_url")):
        raise ApiContractError("API plan header fields must be strings")
    plan = ApiTestPlan(
        schema_version=raw["schema_version"],
        plan_id=raw["plan_id"],
        base_url=raw["base_url"],
        scenarios=tuple(scenarios),
    )
    plan.validate()
    return plan
