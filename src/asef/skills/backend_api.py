from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit
from urllib.parse import parse_qsl

from ..api_contracts import ApiContractError, ApiTestPlan


class BackendApiPolicyError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class BackendApiPolicy:
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "::1")
    allowed_ports: tuple[int, ...] = ()
    allowed_methods: tuple[str, ...] = ("GET", "HEAD", "OPTIONS")
    max_scenarios: int = 20
    max_response_bytes: int = 1_048_576
    timeout_seconds: float = 5.0

    def validate(self) -> None:
        if not self.allowed_hosts or any(not host.strip() for host in self.allowed_hosts):
            raise BackendApiPolicyError("at least one allowed host is required")
        for host in self.allowed_hosts:
            try:
                if not ipaddress.ip_address(host).is_loopback:
                    raise BackendApiPolicyError("the Stage 6.3 policy accepts loopback hosts only")
            except ValueError as exc:
                raise BackendApiPolicyError("allowed hosts must be literal loopback addresses") from exc
        if any(not 1 <= port <= 65_535 for port in self.allowed_ports):
            raise BackendApiPolicyError("allowed ports must be valid TCP ports")
        if not self.allowed_methods or any(method != method.upper() for method in self.allowed_methods):
            raise BackendApiPolicyError("allowed methods must be uppercase")
        if not 1 <= self.max_scenarios <= 100:
            raise BackendApiPolicyError("max_scenarios must be between 1 and 100")
        if not 1 <= self.max_response_bytes <= 10_485_760:
            raise BackendApiPolicyError("max_response_bytes is outside the supported range")
        if not 0 < self.timeout_seconds <= 30:
            raise BackendApiPolicyError("timeout_seconds must be between 0 and 30")


class BackendApiSkill:
    sensitive_headers = frozenset(
        {"authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key"}
    )
    transport_headers = frozenset(
        {"connection", "content-length", "host", "te", "trailer", "transfer-encoding", "upgrade"}
    )
    sensitive_names = frozenset(
        {"access_token", "api_key", "apikey", "authorization", "password", "secret", "token"}
    )

    def __init__(self, policy: BackendApiPolicy | None = None) -> None:
        self.policy = policy or BackendApiPolicy()
        self.policy.validate()

    def validate(self, plan: ApiTestPlan) -> dict[str, object]:
        try:
            plan.validate()
        except ApiContractError as exc:
            raise BackendApiPolicyError(f"API plan contract violation: {exc}") from exc
        parsed = urlsplit(plan.base_url)
        host = parsed.hostname or ""
        if host not in self.policy.allowed_hosts:
            raise BackendApiPolicyError("API host is outside the explicit loopback allowlist")
        if self.policy.allowed_ports and parsed.port not in self.policy.allowed_ports:
            raise BackendApiPolicyError("API port is outside the explicit allowlist")
        if len(plan.scenarios) > self.policy.max_scenarios:
            raise BackendApiPolicyError("API plan exceeds the scenario budget")
        for scenario in plan.scenarios:
            if scenario.method not in self.policy.allowed_methods:
                raise BackendApiPolicyError(f"HTTP method is not allowed: {scenario.method}")
            headers = {name.strip().lower() for name, _ in scenario.headers}
            blocked = headers & self.sensitive_headers
            if blocked:
                raise BackendApiPolicyError(
                    f"persisted sensitive headers are forbidden: {sorted(blocked)}"
                )
            transport = headers & self.transport_headers
            if transport:
                raise BackendApiPolicyError(
                    f"caller-controlled transport headers are forbidden: {sorted(transport)}"
                )
            query_names = {name.lower() for name, _ in parse_qsl(urlsplit(scenario.path).query)}
            if query_names & self.sensitive_names:
                raise BackendApiPolicyError("sensitive query parameters cannot be persisted in an API plan")
            if self._contains_sensitive_key(scenario.json_body):
                raise BackendApiPolicyError("sensitive JSON fields cannot be persisted in an API plan")
            if scenario.json_body is not None and scenario.method in {"GET", "HEAD"}:
                raise BackendApiPolicyError(f"JSON body is forbidden for {scenario.method}")
        return {
            "schema_version": "1.0.0",
            "status": "PASSED",
            "skill_id": "backend-api",
            "plan_id": plan.plan_id,
            "host": host,
            "port": parsed.port,
            "methods": sorted({scenario.method for scenario in plan.scenarios}),
            "scenarios": len(plan.scenarios),
            "network_scope": "loopback-only",
        }

    @classmethod
    def _contains_sensitive_key(cls, value: Any) -> bool:
        if isinstance(value, dict):
            return any(
                str(key).lower() in cls.sensitive_names or cls._contains_sensitive_key(item)
                for key, item in value.items()
            )
        if isinstance(value, list):
            return any(cls._contains_sensitive_key(item) for item in value)
        return False
