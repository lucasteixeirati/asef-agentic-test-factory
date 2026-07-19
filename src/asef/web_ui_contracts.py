from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import urlsplit


class WebUiContractError(ValueError):
    """A declarative Web UI plan or result violates its bounded contract."""


_IDENTIFIER = re.compile(r"[A-Z0-9][A-Z0-9._-]{0,99}")


def _text(value: object, field: str, *, maximum: int = 500) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 for character in value)
    ):
        raise WebUiContractError(f"{field} must be bounded non-blank public text")
    return value


def _relative_path(value: object, field: str) -> str:
    path = _text(value, field, maximum=2_048)
    parsed = urlsplit(path)
    if (
        not path.startswith("/")
        or path.startswith("//")
        or parsed.scheme
        or parsed.netloc
        or parsed.fragment
        or "\\" in path
        or any(character.isspace() for character in path)
    ):
        raise WebUiContractError(
            f"{field} must be a relative absolute-path without fragment, whitespace or backslash"
        )
    return path


def _identifier(value: object, field: str, prefix: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix) or not _IDENTIFIER.fullmatch(value):
        raise WebUiContractError(
            f"{field} must start with {prefix} and contain only bounded uppercase identifier characters"
        )
    return value


@dataclass(slots=True, frozen=True)
class WebUiLocator:
    kind: str
    value: str
    name: str | None = None

    def validate(self) -> None:
        if self.kind not in {"role", "label", "test_id"}:
            raise WebUiContractError("locator kind must be role, label or test_id")
        _text(self.value, "locator value", maximum=100)
        if self.kind == "role":
            _text(self.name, "role locator name", maximum=200)
        elif self.name is not None:
            raise WebUiContractError("only role locators may declare a name")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        value: dict[str, object] = {"kind": self.kind, "value": self.value}
        if self.name is not None:
            value["name"] = self.name
        return value


@dataclass(slots=True, frozen=True)
class WebUiAction:
    action_id: str
    kind: str
    path: str | None = None
    locator: WebUiLocator | None = None
    value: str | None = None

    def validate(self) -> None:
        _identifier(self.action_id, "action_id", "ACT-")
        if self.kind not in {"goto", "click", "fill", "check", "uncheck"}:
            raise WebUiContractError("action kind is outside the closed vocabulary")
        if self.kind == "goto":
            _relative_path(self.path, "goto path")
            if self.locator is not None or self.value is not None:
                raise WebUiContractError("goto accepts only a relative path")
            return
        if self.path is not None or self.locator is None:
            raise WebUiContractError("element actions require a locator and no path")
        self.locator.validate()
        if self.kind == "fill":
            if not isinstance(self.value, str) or len(self.value) > 1_000 or any(
                ord(character) < 32 and character not in "\t" for character in self.value
            ):
                raise WebUiContractError("fill value must be bounded public text")
        elif self.value is not None:
            raise WebUiContractError("only fill actions may declare a value")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        value: dict[str, object] = {"action_id": self.action_id, "kind": self.kind}
        if self.path is not None:
            value["path"] = self.path
        if self.locator is not None:
            value["locator"] = self.locator.to_dict()
        if self.value is not None:
            value["value"] = self.value
        return value


@dataclass(slots=True, frozen=True)
class WebUiAssertion:
    assertion_id: str
    kind: str
    expected: str | bool
    locator: WebUiLocator | None = None

    def validate(self) -> None:
        _identifier(self.assertion_id, "assertion_id", "AST-")
        if self.kind not in {"url", "visible", "text", "value", "checked"}:
            raise WebUiContractError("assertion kind is outside the closed vocabulary")
        if self.kind == "url":
            _relative_path(self.expected, "expected URL")
            if self.locator is not None:
                raise WebUiContractError("URL assertion cannot declare a locator")
        else:
            if self.locator is None:
                raise WebUiContractError("element assertion requires a locator")
            self.locator.validate()
            if self.kind in {"visible", "checked"}:
                if not isinstance(self.expected, bool):
                    raise WebUiContractError("visible and checked assertions require a boolean")
            elif isinstance(self.expected, bool):
                raise WebUiContractError("text and value assertions require text")
            else:
                _text(self.expected, "assertion expected text", maximum=1_000)

    def to_dict(self) -> dict[str, object]:
        self.validate()
        value: dict[str, object] = {
            "assertion_id": self.assertion_id,
            "kind": self.kind,
            "expected": self.expected,
        }
        if self.locator is not None:
            value["locator"] = self.locator.to_dict()
        return value


@dataclass(slots=True, frozen=True)
class WebUiScenario:
    scenario_id: str
    description: str
    actions: tuple[WebUiAction, ...]
    assertions: tuple[WebUiAssertion, ...]

    def validate(self) -> None:
        _identifier(self.scenario_id, "scenario_id", "SCN-")
        _text(self.description, "scenario description")
        if not 1 <= len(self.actions) <= 30 or not 1 <= len(self.assertions) <= 20:
            raise WebUiContractError("scenario requires bounded actions and assertions")
        for item in (*self.actions, *self.assertions):
            item.validate()
        ids = [item.action_id for item in self.actions] + [item.assertion_id for item in self.assertions]
        if len(ids) != len(set(ids)):
            raise WebUiContractError("action and assertion ids must be unique within a scenario")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "scenario_id": self.scenario_id,
            "description": self.description,
            "actions": [item.to_dict() for item in self.actions],
            "assertions": [item.to_dict() for item in self.assertions],
        }


@dataclass(slots=True, frozen=True)
class WebUiTestPlan:
    plan_id: str
    base_url: str
    scenarios: tuple[WebUiScenario, ...]
    viewport_width: int = 1280
    viewport_height: int = 720
    schema_version: str = "1.0.0"

    def validate(self) -> None:
        if self.schema_version != "1.0.0":
            raise WebUiContractError("unsupported Web UI plan schema_version")
        _identifier(self.plan_id, "plan_id", "WEB-")
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
            raise WebUiContractError("base_url must be an HTTP origin without credentials or path")
        try:
            port = parsed.port
        except ValueError as exc:
            raise WebUiContractError("base_url contains an invalid port") from exc
        if port is None:
            raise WebUiContractError("base_url must declare an explicit port")
        if not 320 <= self.viewport_width <= 3_840 or not 240 <= self.viewport_height <= 2_160:
            raise WebUiContractError("viewport is outside the bounded range")
        if not 1 <= len(self.scenarios) <= 20:
            raise WebUiContractError("plan requires between 1 and 20 scenarios")
        for scenario in self.scenarios:
            scenario.validate()
        ids = [item.scenario_id for item in self.scenarios]
        if len(ids) != len(set(ids)):
            raise WebUiContractError("scenario ids must be unique")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "base_url": self.base_url,
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
            "scenarios": [item.to_dict() for item in self.scenarios],
        }


@dataclass(slots=True, frozen=True)
class WebUiScenarioResult:
    scenario_id: str
    status: str
    duration_ms: int
    diagnostic_code: str | None = None
    failed_step_id: str | None = None
    screenshot_ref: str | None = None

    def validate(self) -> None:
        _identifier(self.scenario_id, "result scenario_id", "SCN-")
        if self.status not in {
            "PASSED", "FAILED", "ERROR", "TIMEOUT", "POLICY_BLOCKED"
        }:
            raise WebUiContractError("invalid Web UI scenario result identity or status")
        if isinstance(self.duration_ms, bool) or not isinstance(self.duration_ms, int) or self.duration_ms < 0:
            raise WebUiContractError("scenario duration must be a non-negative integer")
        if self.status == "PASSED" and any(
            value is not None for value in (self.diagnostic_code, self.failed_step_id, self.screenshot_ref)
        ):
            raise WebUiContractError("passed scenario cannot contain failure evidence")
        if self.status != "PASSED" and not self.diagnostic_code:
            raise WebUiContractError("non-passing scenario requires a diagnostic")
        for value, field in (
            (self.diagnostic_code, "diagnostic_code"),
            (self.failed_step_id, "failed_step_id"),
            (self.screenshot_ref, "screenshot_ref"),
        ):
            if value is not None:
                _text(value, field, maximum=300)
        if self.failed_step_id is not None:
            if not (
                self.failed_step_id.startswith("ACT-")
                or self.failed_step_id.startswith("AST-")
            ):
                raise WebUiContractError("failed_step_id must identify an action or assertion")
            _identifier(
                self.failed_step_id,
                "failed_step_id",
                "ACT-" if self.failed_step_id.startswith("ACT-") else "AST-",
            )
        if self.screenshot_ref is not None and (
            self.screenshot_ref.startswith(("/", "\\"))
            or ".." in self.screenshot_ref.replace("\\", "/").split("/")
            or "\\" in self.screenshot_ref
            or not self.screenshot_ref.endswith(".png")
        ):
            raise WebUiContractError("screenshot_ref must be a contained POSIX relative PNG path")


@dataclass(slots=True, frozen=True)
class WebUiExecutionResult:
    plan_id: str
    status: str
    tests: int
    passed: int
    failed: int
    errors: int
    timeouts: int
    policy_blocked: int
    scenarios: tuple[WebUiScenarioResult, ...]
    schema_version: str = "1.0.0"

    def validate(self) -> None:
        allowed = {"PASSED", "FAILED", "ERROR", "TIMEOUT", "POLICY_BLOCKED"}
        if self.schema_version != "1.0.0" or self.status not in allowed:
            raise WebUiContractError("invalid Web UI execution result header")
        _identifier(self.plan_id, "result plan_id", "WEB-")
        counters = (self.tests, self.passed, self.failed, self.errors, self.timeouts, self.policy_blocked)
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counters):
            raise WebUiContractError("Web UI execution counters must be non-negative integers")
        if self.tests != len(self.scenarios) or self.tests != sum(counters[1:]) or self.tests == 0:
            raise WebUiContractError("Web UI execution counters do not reconcile")
        for scenario in self.scenarios:
            scenario.validate()
        if len({item.scenario_id for item in self.scenarios}) != len(self.scenarios):
            raise WebUiContractError("Web UI result scenario ids must be unique")
        observed = tuple(sum(item.status == status for item in self.scenarios) for status in (
            "PASSED", "FAILED", "ERROR", "TIMEOUT", "POLICY_BLOCKED"
        ))
        if observed != counters[1:]:
            raise WebUiContractError("Web UI counters do not match scenario statuses")
        expected = (
            "POLICY_BLOCKED" if self.policy_blocked else
            "ERROR" if self.errors else
            "TIMEOUT" if self.timeouts else
            "FAILED" if self.failed else "PASSED"
        )
        if self.status != expected:
            raise WebUiContractError("Web UI result status does not match counters")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "status": self.status,
            "tests": self.tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "timeouts": self.timeouts,
            "policy_blocked": self.policy_blocked,
            "scenarios": [
                {
                    "scenario_id": item.scenario_id,
                    "status": item.status,
                    "duration_ms": item.duration_ms,
                    "diagnostic_code": item.diagnostic_code,
                    "failed_step_id": item.failed_step_id,
                    "screenshot_ref": item.screenshot_ref,
                }
                for item in self.scenarios
            ],
        }


def _locator(raw: Any) -> WebUiLocator:
    if not isinstance(raw, dict) or not {"kind", "value"}.issubset(raw) or set(raw) - {"kind", "value", "name"}:
        raise WebUiContractError("locator fields do not match schema 1.0.0")
    locator = WebUiLocator(raw["kind"], raw["value"], raw.get("name"))
    locator.validate()
    return locator


def web_ui_plan_from_dict(raw: Any) -> WebUiTestPlan:
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "plan_id", "base_url", "viewport", "scenarios"}:
        raise WebUiContractError("Web UI plan root fields do not match schema 1.0.0")
    viewport = raw["viewport"]
    if not isinstance(viewport, dict) or set(viewport) != {"width", "height"}:
        raise WebUiContractError("viewport fields do not match schema 1.0.0")
    if any(isinstance(viewport[key], bool) or not isinstance(viewport[key], int) for key in viewport):
        raise WebUiContractError("viewport dimensions must be integers")
    if not isinstance(raw["scenarios"], list):
        raise WebUiContractError("scenarios must be an array")
    scenarios: list[WebUiScenario] = []
    for scenario_raw in raw["scenarios"]:
        if not isinstance(scenario_raw, dict) or set(scenario_raw) != {
            "scenario_id", "description", "actions", "assertions"
        }:
            raise WebUiContractError("scenario fields do not match schema 1.0.0")
        if not isinstance(scenario_raw["actions"], list) or not isinstance(scenario_raw["assertions"], list):
            raise WebUiContractError("actions and assertions must be arrays")
        actions: list[WebUiAction] = []
        for item in scenario_raw["actions"]:
            if not isinstance(item, dict) or not {"action_id", "kind"}.issubset(item) or set(item) - {
                "action_id", "kind", "path", "locator", "value"
            }:
                raise WebUiContractError("action fields do not match schema 1.0.0")
            actions.append(WebUiAction(
                item["action_id"], item["kind"], item.get("path"),
                _locator(item["locator"]) if "locator" in item else None, item.get("value"),
            ))
        assertions: list[WebUiAssertion] = []
        for item in scenario_raw["assertions"]:
            if not isinstance(item, dict) or set(item) - {"assertion_id", "kind", "expected", "locator"} or not {
                "assertion_id", "kind", "expected"
            }.issubset(item):
                raise WebUiContractError("assertion fields do not match schema 1.0.0")
            assertions.append(WebUiAssertion(
                item["assertion_id"], item["kind"], item["expected"],
                _locator(item["locator"]) if "locator" in item else None,
            ))
        scenario = WebUiScenario(
            scenario_raw["scenario_id"], scenario_raw["description"], tuple(actions), tuple(assertions)
        )
        scenario.validate()
        scenarios.append(scenario)
    plan = WebUiTestPlan(
        raw["plan_id"], raw["base_url"], tuple(scenarios), viewport["width"], viewport["height"], raw["schema_version"]
    )
    plan.validate()
    return plan


def web_ui_execution_result_from_dict(raw: Any) -> WebUiExecutionResult:
    expected = {
        "schema_version", "plan_id", "status", "tests", "passed", "failed",
        "errors", "timeouts", "policy_blocked", "scenarios",
    }
    if not isinstance(raw, dict) or set(raw) != expected:
        raise WebUiContractError("Web UI result root fields do not match schema 1.0.0")
    counter_names = ("tests", "passed", "failed", "errors", "timeouts", "policy_blocked")
    if any(isinstance(raw[name], bool) or not isinstance(raw[name], int) for name in counter_names):
        raise WebUiContractError("Web UI result counters must be integers")
    if not isinstance(raw["scenarios"], list):
        raise WebUiContractError("Web UI result scenarios must be an array")
    scenario_fields = {
        "scenario_id", "status", "duration_ms", "diagnostic_code",
        "failed_step_id", "screenshot_ref",
    }
    scenarios: list[WebUiScenarioResult] = []
    for item in raw["scenarios"]:
        if not isinstance(item, dict) or set(item) != scenario_fields:
            raise WebUiContractError("Web UI scenario result fields do not match schema 1.0.0")
        scenario = WebUiScenarioResult(
            scenario_id=item["scenario_id"],
            status=item["status"],
            duration_ms=item["duration_ms"],
            diagnostic_code=item["diagnostic_code"],
            failed_step_id=item["failed_step_id"],
            screenshot_ref=item["screenshot_ref"],
        )
        scenario.validate()
        scenarios.append(scenario)
    result = WebUiExecutionResult(
        schema_version=raw["schema_version"],
        plan_id=raw["plan_id"],
        status=raw["status"],
        tests=raw["tests"],
        passed=raw["passed"],
        failed=raw["failed"],
        errors=raw["errors"],
        timeouts=raw["timeouts"],
        policy_blocked=raw["policy_blocked"],
        scenarios=tuple(scenarios),
    )
    result.validate()
    return result
