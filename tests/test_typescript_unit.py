from __future__ import annotations
import unittest
import json
from pathlib import Path
from asef.adapters.typescript_unit_compiler import TypeScriptUnitTestCompiler
from asef.adapters.typescript_unit_execution import normalize_node_tap
from asef.contracts import TestExecutionOutcome
from asef.java_unit_contracts import JavaUnitScenario, JavaUnitTestPlan

class TypeScriptUnitTests(unittest.TestCase):
    def plan(self, expected=5):
        return JavaUnitTestPlan("JAV-TS-001", (JavaUnitScenario("SCN-ADD", "Add", "add", 2, 3, expected),))

    def test_same_declarative_intention_compiles_deterministically_to_typescript(self):
        artifact = TypeScriptUnitTestCompiler.compile(self.plan())
        self.assertEqual(artifact, TypeScriptUnitTestCompiler.compile(self.plan()))
        self.assertEqual(("case_001_scn_add",), artifact.test_names)
        self.assertNotIn("eval", artifact.source)

    def test_tap_normalizer_distinguishes_pass_failure_infrastructure_and_tamper(self):
        names = ("case_001_scn_add",)
        cases = (
            ("TAP version 13\nok 1 - case_001_scn_add\n1..1\n", 0, False, TestExecutionOutcome.PASSED),
            ("TAP version 13\nnot ok 1 - case_001_scn_add\n1..1\n", 1, False, TestExecutionOutcome.ASSERTION_FAILURE),
            (None, 124, True, TestExecutionOutcome.INFRASTRUCTURE_ERROR),
            ("ok 1 - forged\n", 0, False, TestExecutionOutcome.TOOL_ERROR),
        )
        for tap, code, timeout, expected in cases:
                with self.subTest(expected=expected): self.assertIs(normalize_node_tap(tap, code, names, timeout)[-1], expected)

    def test_metamorphic_relations_are_valid_and_stratified(self):
        root = Path(__file__).resolve().parents[1]
        dataset = json.loads((root / "examples/multilanguage-arithmetic-metamorphic.json").read_text(encoding="utf-8"))
        self.assertEqual(("metamorphic", 3), (dataset["dataset_kind"], len(dataset["relations"])))
        for relation in dataset["relations"]:
            left, right = relation["left"], relation["right"]
            if relation["relation_id"] == "MR-ADD-COMMUTATIVE": self.assertEqual(left + right, right + left)
            elif relation["relation_id"] == "MR-SUB-INVERSE": self.assertEqual((left - right) + right, left)
            else: self.assertEqual(left * right, 0)

if __name__ == "__main__": unittest.main()
