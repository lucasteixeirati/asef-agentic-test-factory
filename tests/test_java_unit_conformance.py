from __future__ import annotations

import json
from pathlib import Path
import unittest

from asef.application.ports import ExecutionOutput
from asef.adapters.java_unit_execution import java_unit_functional_fingerprint
from asef.contracts import TestExecutionOutcome
from asef.java_unit_contracts import JavaUnitContractError, java_unit_plan_from_dict
from asef.skills.java_unit import JavaUnitPolicyError, JavaUnitSkill


ROOT = Path(__file__).resolve().parents[1]


class JavaUnitConformanceTests(unittest.TestCase):
    def manifest(self):
        return json.loads((ROOT / "examples/java-junit/conformance/manifest.json").read_text(encoding="utf-8"))

    def test_dataset_has_distinct_positive_negative_adversarial_and_security_cases(self):
        manifest = self.manifest()
        self.assertEqual((manifest["dataset_kind"], manifest["repetitions"]), ("conformance", 2))
        self.assertEqual({"positive", "negative", "adversarial", "security"}, {case["category"] for case in manifest["cases"]})
        for case in manifest["cases"]:
            if case["expected_outcome"] == "CONTRACT_REJECTED":
                with self.assertRaises(JavaUnitContractError): java_unit_plan_from_dict(case["plan"])
            elif case["expected_outcome"] == "POLICY_REJECTED":
                with self.assertRaises(JavaUnitPolicyError): JavaUnitSkill().validate(java_unit_plan_from_dict(case["plan"]))
            else:
                JavaUnitSkill().validate(java_unit_plan_from_dict(case["plan"]))

    def test_functional_fingerprint_excludes_volatile_execution_fields(self):
        common = dict(tests=1, passed=1, failed=0, errors=0, skipped=0, tool_id="maven-surefire",
                      tool_version="3.5.5", outcome=TestExecutionOutcome.PASSED)
        first = ExecutionOutput("sha256:" + "a" * 64, ("run",), 0, 10, "first", "", **common)
        second = ExecutionOutput("sha256:" + "b" * 64, ("run",), 0, 999, "second", "different", **common)
        self.assertEqual(java_unit_functional_fingerprint(first), java_unit_functional_fingerprint(second))

    def test_java_capability_does_not_pollute_neutral_core(self):
        for relative in ("src/asef/contracts.py", "src/asef/outcomes.py", "src/asef/runtime/budgets.py"):
            text = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertNotIn("java_unit", text)
            self.assertNotIn("maven", text)
            self.assertNotIn("junit", text)


if __name__ == "__main__": unittest.main()
