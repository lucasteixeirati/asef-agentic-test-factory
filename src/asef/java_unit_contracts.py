from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


class JavaUnitContractError(ValueError):
    """A bounded Java unit plan violates its public contract."""


_ID = re.compile(r"[A-Z0-9][A-Z0-9._-]{0,99}")
_INT_MIN, _INT_MAX = -(2**31), 2**31 - 1


def _text(value: object, field: str, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise JavaUnitContractError(f"{field} must be bounded non-blank public text")
    return value


def _identifier(value: object, field: str, prefix: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix) or not _ID.fullmatch(value):
        raise JavaUnitContractError(f"{field} must be a bounded {prefix} identifier")
    return value


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not _INT_MIN <= value <= _INT_MAX:
        raise JavaUnitContractError(f"{field} must be a signed 32-bit integer")
    return value


@dataclass(slots=True, frozen=True)
class JavaUnitScenario:
    scenario_id: str
    description: str
    operation: str
    left: int
    right: int
    expected: int | str

    def validate(self) -> None:
        _identifier(self.scenario_id, "scenario_id", "SCN-")
        _text(self.description, "scenario description")
        if self.operation not in {"add", "subtract", "multiply", "divide"}:
            raise JavaUnitContractError("operation is outside the closed vocabulary")
        _integer(self.left, "left")
        _integer(self.right, "right")
        if self.operation in {"add", "subtract", "multiply"}:
            operation = {
                "add": lambda: self.left + self.right,
                "subtract": lambda: self.left - self.right,
                "multiply": lambda: self.left * self.right,
            }[self.operation]
            if not _INT_MIN <= operation() <= _INT_MAX:
                raise JavaUnitContractError("scenario operation would overflow a signed 32-bit integer")
        if self.operation == "divide" and self.left == _INT_MIN and self.right == -1:
            raise JavaUnitContractError("scenario division would overflow a signed 32-bit integer")
        if self.expected == "ArithmeticException":
            if self.operation != "divide" or self.right != 0:
                raise JavaUnitContractError("ArithmeticException is valid only for division by zero")
        else:
            _integer(self.expected, "expected")
            if self.operation == "divide" and self.right == 0:
                raise JavaUnitContractError("division by zero requires ArithmeticException")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {"scenario_id": self.scenario_id, "description": self.description, "operation": self.operation,
                "left": self.left, "right": self.right, "expected": self.expected}


@dataclass(slots=True, frozen=True)
class JavaUnitTestPlan:
    plan_id: str
    scenarios: tuple[JavaUnitScenario, ...]
    fixture_id: str = "JAVA-CALCULATOR-001"
    schema_version: str = "1.0.0"

    def validate(self) -> None:
        if self.schema_version != "1.0.0" or self.fixture_id != "JAVA-CALCULATOR-001":
            raise JavaUnitContractError("unsupported Java unit plan schema or fixture")
        _identifier(self.plan_id, "plan_id", "JAV-")
        if not 1 <= len(self.scenarios) <= 20:
            raise JavaUnitContractError("plan requires between 1 and 20 scenarios")
        for item in self.scenarios:
            item.validate()
        if len({item.scenario_id for item in self.scenarios}) != len(self.scenarios):
            raise JavaUnitContractError("scenario ids must be unique")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {"schema_version": self.schema_version, "plan_id": self.plan_id, "fixture_id": self.fixture_id,
                "scenarios": [item.to_dict() for item in self.scenarios]}


def java_unit_plan_from_dict(raw: Any) -> JavaUnitTestPlan:
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "plan_id", "fixture_id", "scenarios"}:
        raise JavaUnitContractError("Java unit plan root fields do not match schema 1.0.0")
    if not isinstance(raw["scenarios"], list):
        raise JavaUnitContractError("scenarios must be an array")
    scenarios = []
    fields = {"scenario_id", "description", "operation", "left", "right", "expected"}
    for value in raw["scenarios"]:
        if not isinstance(value, dict) or set(value) != fields:
            raise JavaUnitContractError("Java unit scenario fields do not match schema 1.0.0")
        scenario = JavaUnitScenario(**value)
        scenario.validate()
        scenarios.append(scenario)
    plan = JavaUnitTestPlan(raw["plan_id"], tuple(scenarios), raw["fixture_id"], raw["schema_version"])
    plan.validate()
    return plan
