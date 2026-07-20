from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import subprocess

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

    def test_surefire_identity_allows_runtime_order_but_rejects_duplicates(self):
        names = ("case_001_a", "case_002_b")
        shuffled = '<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase name="case_002_b"/><testcase name="case_001_a"/></testsuite>'
        duplicate = '<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase name="case_001_a"/><testcase name="case_001_a"/></testsuite>'
        self.assertIs(normalize_surefire_result(shuffled, 0, names)[-1], TestExecutionOutcome.PASSED)
        self.assertIs(normalize_surefire_result(duplicate, 0, names)[-1], TestExecutionOutcome.TOOL_ERROR)

    def test_executor_resolves_image_runs_hardened_and_reads_single_native_report(self):
        image_id = "sha256:" + "c" * 64
        captured = []
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace, output = DockerJavaUnitExecutor.stage(plan(), root)
            artifact = JavaUnitTestCompiler.compile(plan())
            native = (
                '<testsuite tests="2" failures="0" errors="0" skipped="0">'
                + "".join(f'<testcase name="{name}"/>' for name in reversed(artifact.test_names))
                + "</testsuite>"
            )
            def executor(command, **kwargs):
                del kwargs
                captured.append(command)
                if command[:3] == ["docker", "image", "inspect"]:
                    return subprocess.CompletedProcess(command, 0, image_id + "\n", "")
                if command[:3] == ["docker", "ps", "-aq"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                spec = next(item for item in command if "dst=/asef-output" in item)
                output_path = Path(spec.split("src=", 1)[1].split(",dst=", 1)[0])
                (output_path / "surefire/TEST-generated.xml").write_text(native, encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "BUILD SUCCESS", "")
            adapter = DockerJavaUnitExecutor(root, executor)
            result = adapter.execute(workspace, output)
        self.assertIs(result.outcome, TestExecutionOutcome.PASSED)
        self.assertEqual((result.image, result.tests, result.tool_version), (image_id, 2, "3.5.5"))
        docker_run = next(command for command in captured if command[:2] == ["docker", "run"])
        self.assertIn("none", docker_run)
        self.assertIn("--read-only", docker_run)

    def test_executor_rejects_invalid_image_and_output_allowlist(self):
        def missing(command, **kwargs):
            del kwargs
            return subprocess.CompletedProcess(command, 1, "", "missing")
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(OSError): DockerJavaUnitExecutor(root, missing)._resolve_image_id()
            report = root / "reports"; report.mkdir()
            (report / "unexpected.txt").write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "allowlist"):
                DockerJavaUnitExecutor._read_single_report(report)


if __name__ == "__main__": unittest.main()
