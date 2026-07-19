from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlsplit

from ..web_ui_contracts import WebUiTestPlan


class WebUiPolicyError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class WebUiPolicy:
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "::1")
    allowed_ports: tuple[int, ...] = ()
    max_scenarios: int = 20
    max_actions_per_scenario: int = 30
    max_assertions_per_scenario: int = 20
    max_scenario_seconds: int = 30

    def validate(self) -> None:
        if not self.allowed_hosts:
            raise WebUiPolicyError("at least one allowed host is required")
        for host in self.allowed_hosts:
            try:
                if not ipaddress.ip_address(host).is_loopback:
                    raise WebUiPolicyError("Stage 6.4.1 accepts literal loopback hosts only")
            except ValueError as exc:
                raise WebUiPolicyError("allowed hosts must be literal loopback addresses") from exc
        if not self.allowed_ports:
            raise WebUiPolicyError("at least one explicitly allowed fixture port is required")
        if any(isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65_535 for port in self.allowed_ports):
            raise WebUiPolicyError("allowed ports must be valid TCP ports")
        if len(self.allowed_ports) != len(set(self.allowed_ports)):
            raise WebUiPolicyError("allowed ports must be unique")
        if not 1 <= self.max_scenarios <= 20:
            raise WebUiPolicyError("max_scenarios must be between 1 and 20")
        if not 1 <= self.max_actions_per_scenario <= 30:
            raise WebUiPolicyError("max_actions_per_scenario must be between 1 and 30")
        if not 1 <= self.max_assertions_per_scenario <= 20:
            raise WebUiPolicyError("max_assertions_per_scenario must be between 1 and 20")
        if not 1 <= self.max_scenario_seconds <= 120:
            raise WebUiPolicyError("max_scenario_seconds must be between 1 and 120")


class WebUiSkill:
    sensitive_names = frozenset({
        "access_token", "api_key", "apikey", "authorization", "credit_card", "password",
        "private_key", "secret", "token",
    })

    def __init__(self, policy: WebUiPolicy | None = None) -> None:
        self.policy = policy or WebUiPolicy()
        self.policy.validate()

    def validate(self, plan: WebUiTestPlan) -> dict[str, object]:
        try:
            plan.validate()
        except ValueError as exc:
            raise WebUiPolicyError(f"Web UI plan contract violation: {exc}") from exc
        parsed = urlsplit(plan.base_url)
        host = parsed.hostname or ""
        if host not in self.policy.allowed_hosts:
            raise WebUiPolicyError("Web UI host is outside the explicit loopback allowlist")
        if self.policy.allowed_ports and parsed.port not in self.policy.allowed_ports:
            raise WebUiPolicyError("Web UI port is outside the explicit allowlist")
        if len(plan.scenarios) > self.policy.max_scenarios:
            raise WebUiPolicyError("Web UI plan exceeds the scenario budget")
        for scenario in plan.scenarios:
            if len(scenario.actions) > self.policy.max_actions_per_scenario:
                raise WebUiPolicyError("Web UI scenario exceeds the action budget")
            if len(scenario.assertions) > self.policy.max_assertions_per_scenario:
                raise WebUiPolicyError("Web UI scenario exceeds the assertion budget")
            values: list[str] = [scenario.description]
            for action in scenario.actions:
                if action.path is not None:
                    self._validate_path(action.path)
                if action.locator is not None:
                    values.extend(filter(None, (action.locator.value, action.locator.name)))
                if action.value is not None:
                    values.append(action.value)
            for assertion in scenario.assertions:
                if assertion.kind == "url":
                    self._validate_path(str(assertion.expected))
                if assertion.locator is not None:
                    values.extend(filter(None, (assertion.locator.value, assertion.locator.name)))
                if isinstance(assertion.expected, str):
                    values.append(assertion.expected)
            if any(self._contains_sensitive_marker(value) for value in values):
                raise WebUiPolicyError("sensitive data markers are forbidden in a Web UI plan")
        return {
            "schema_version": "1.0.0",
            "status": "PASSED",
            "skill_id": "web-ui",
            "plan_id": plan.plan_id,
            "host": host,
            "port": parsed.port,
            "scenarios": len(plan.scenarios),
            "network_scope": "loopback-only",
            "browser_scope": "chromium-planned",
            "screenshots_publishable": False,
        }

    def _validate_path(self, path: str) -> None:
        query_names = {name.lower() for name, _ in parse_qsl(urlsplit(path).query)}
        if query_names & self.sensitive_names:
            raise WebUiPolicyError("sensitive query parameters are forbidden in Web UI navigation")

    def _contains_sensitive_marker(self, value: str) -> bool:
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in self.sensitive_names:
            return True
        if any(
            f"{name}=" in normalized or f"{name}:" in normalized
            for name in self.sensitive_names
        ):
            return True
        words = set(re.findall(r"[a-z0-9]+", normalized))
        return bool(words & self.sensitive_names)
