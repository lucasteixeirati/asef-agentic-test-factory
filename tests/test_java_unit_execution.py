from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from asef.adapters.java_unit_compiler import JavaUnitTestCompiler
from asef.adapters.java_unit_execution import DockerJavaUnitExecutor, normalize_surefire_result
from asef.contracts import TestExecutionOutcome
from asef.java_unit_contracts import JavaUnitScenario, JavaUnitTestPlan


def plan(expected=5):
    return JavaUnitTestPlan("JAV-PLAN-001", (
        JavaUnitScenario("SCN-ADD", "Add values", "add", 2, 3, expected),
        JavaUnitScenario("SCN-ZERO", "Reject zero division", "divide", 1, 0, "ArithmeticException"),
    ))


class JavaUnitCompilerTests(unittest.TestCase):
    def test_compiler_is_deterministic_and_contains_no_model_controlled_structure(self):
        first = JavaUnitTestCompiler.compile(plan())
        second = JavaUnitTestCompiler.compile(plan())
        self.assertEqual(first, second)
        self.assertEqual(first.sha256, hashlib.sha256(first.source.encode()).hexdigest())
        self.assertEqual(first.test_names, ("case_001_scn_add", "case_002_scn_zero"))
        self.assertIn("assertThrows(ArithmeticException.class", first.source)

    def test_staging_reconciles_plan_compiled_source_and_fixture_manifest(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace, _ = DockerJavaUnitExecutor.stage(plan(), root)
            staged, artifact = DockerJavaUnitExecutor._validate_staged_inputs(workspace)
            self.assertEqual(staged, plan())
            (workspace / artifact.path).write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "reviewed plan"):
                DockerJavaUnitExecutor._validate_staged_inputs(workspace)

    def test_staging_rejects_manifest_allowlist_tamper(self):
        with TemporaryDirectory() as temporary:
            workspace, _ = DockerJavaUnitExecutor.stage(plan(), Path(temporary))
            manifest = workspace / "fixture-manifest.json"
            manifest.write_text('{"schema_version":"1.0.0","files":{}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest fields"):
                DockerJavaUnitExecutor._validate_staged_inputs(workspace)

    def test_surefire_normalizer_distinguishes_results_and_identity_tamper(self):
        names = ("case_001_scn_add",)
        def xml(failures=0, errors=0, name=names[0]):
            return f'<testsuite tests="1" failures="{failures}" errors="{errors}" skipped="0"><testcase name="{name}"/></testsuite>'
        cases = (
            (xml(), 0, False, TestExecutionOutcome.PASSED),
            (xml(failures=1), 1, False, TestExecutionOutcome.ASSERTION_FAILURE),
            (xml(errors=1), 1, False, TestExecutionOutcome.TEST_ERROR),
            (None, 1, False, TestExecutionOutcome.TOOL_ERROR),
            (None, 124, True, TestExecutionOutcome.INFRASTRUCTURE_ERROR),
            (xml(name="forged"), 0, False, TestExecutionOutcome.TOOL_ERROR),
        )
        for native, exit_code, infra, expected in cases:
            with self.subTest(expected=expected):
                self.assertIs(normalize_surefire_result(native, exit_code, names, infra)[-1], expected)


if __name__ == "__main__": unittest.main()
