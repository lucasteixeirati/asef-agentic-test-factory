from __future__ import annotations

import re
from dataclasses import dataclass

from ..java_unit_contracts import JavaUnitContractError, JavaUnitTestPlan


class JavaUnitPolicyError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class JavaUnitPolicy:
    max_scenarios: int = 20

    def validate(self) -> None:
        if isinstance(self.max_scenarios, bool) or not 1 <= self.max_scenarios <= 20:
            raise JavaUnitPolicyError("max_scenarios must be between 1 and 20")


class JavaUnitSkill:
    sensitive_names = frozenset(
        {"access_token", "api_key", "apikey", "authorization", "password", "private_key", "secret", "token"}
    )

    def __init__(self, policy: JavaUnitPolicy | None = None) -> None:
        self.policy = policy or JavaUnitPolicy()
        self.policy.validate()

    def validate(self, plan: JavaUnitTestPlan) -> dict[str, object]:
        try:
            plan.validate()
        except JavaUnitContractError as exc:
            raise JavaUnitPolicyError(f"Java unit plan contract violation: {exc}") from exc
        if len(plan.scenarios) > self.policy.max_scenarios:
            raise JavaUnitPolicyError("Java unit plan exceeds the scenario budget")
        if any(self._contains_sensitive_marker(item.description) for item in plan.scenarios):
            raise JavaUnitPolicyError("sensitive data markers are forbidden in a Java unit plan")
        return {
            "schema_version": "1.0.0",
            "status": "PASSED",
            "skill_id": "java-unit",
            "plan_id": plan.plan_id,
            "fixture_id": plan.fixture_id,
            "scenarios": len(plan.scenarios),
            "language": "java",
            "build_system": "maven",
            "test_framework": "junit-jupiter",
            "network_scope": "none",
        }

    def _contains_sensitive_marker(self, value: str) -> bool:
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in self.sensitive_names:
            return True
        if any(f"{name}=" in normalized or f"{name}:" in normalized for name in self.sensitive_names):
            return True
        words = set(re.findall(r"[a-z0-9]+", normalized))
        return bool(words & self.sensitive_names)
