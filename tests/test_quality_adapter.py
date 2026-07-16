from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from asef.adapters.quality_execution import (
    COVERAGE_VERSION,
    MUTMUT_VERSION,
    QUALITY_IMAGE,
    PythonQualityDockerAdapter,
    normalize_coverage_native,
    normalize_driver_result,
    normalize_mutation_native,
)
from asef.evaluation_contracts import (
    QualityCapability,
    QualityCapabilityRequest,
    QualityCapabilityStatus,
)


IMAGE_ID = "sha256:" + "d" * 64


def request(capability: QualityCapability) -> QualityCapabilityRequest:
    return QualityCapabilityRequest(
        capability=capability,
        tool_id="coverage.py" if capability is QualityCapability.COVERAGE else "mutmut",
        tool_version=COVERAGE_VERSION if capability is QualityCapability.COVERAGE else MUTMUT_VERSION,
        scope=("src/quality_fixture",),
        test_paths=("tests",),
        timeout_seconds=60,
        execution_environment_ref=QUALITY_IMAGE,
        max_mutants=3 if capability is QualityCapability.MUTATION else None,
    )


def coverage_native() -> str:
    return json.dumps(
        {
            "meta": {"version": COVERAGE_VERSION, "branch_coverage": True},
            "totals": {
                "covered_lines": 4,
                "num_statements": 5,
                "covered_branches": 1,
                "num_branches": 2,
                "excluded_lines": 0,
            },
        }
    )


def mutation_native() -> str:
    mutants = [
        {"name": "a", "native_status": "killed"},
        {"name": "b", "native_status": "survived"},
        {"name": "c", "native_status": "not checked"},
    ]
    return json.dumps(
        {
            "schema_version": "1.0.0",
            "tool_id": "mutmut",
            "tool_version": MUTMUT_VERSION,
            "max_mutants": 3,
            "mutants_total": 3,
            "admitted": 2,
            "deferred": 1,
            "killed": 1,
            "survived": 1,
            "invalid": 0,
            "timed_out": 0,
            "not_run": 1,
            "mutants": mutants,
        }
    )


class QualityNormalizerTests(unittest.TestCase):
    def test_coverage_uses_native_line_and_branch_totals(self) -> None:
        self.assertEqual(
            normalize_coverage_native(coverage_native(), COVERAGE_VERSION),
            {
                "lines_covered": 4,
                "lines_total": 5,
                "branches_covered": 1,
                "branches_total": 2,
                "excluded_lines": 0,
            },
        )

    def test_mutation_reconciles_admission_outcomes_and_per_mutant_evidence(self) -> None:
        result = normalize_mutation_native(mutation_native(), 3, MUTMUT_VERSION)
        self.assertEqual((result["mutants_total"], result["admitted"], result["not_run"]), (3, 2, 1))

    def test_native_results_fail_closed_on_malformed_or_inconsistent_counts(self) -> None:
        invalid_coverage = json.loads(coverage_native())
        invalid_coverage["totals"]["covered_lines"] = 6
        invalid_mutation = json.loads(mutation_native())
        invalid_mutation["killed"] = 2
        for callback, content in (
            (lambda value: normalize_coverage_native(value, COVERAGE_VERSION), "[]"),
            (lambda value: normalize_coverage_native(value, COVERAGE_VERSION), json.dumps(invalid_coverage)),
            (lambda value: normalize_mutation_native(value, 3, MUTMUT_VERSION), json.dumps(invalid_mutation)),
        ):
            with self.subTest(content=content), self.assertRaises(ValueError):
                callback(content)

    def test_driver_result_requires_identity_schema_and_known_status(self) -> None:
        requested = request(QualityCapability.COVERAGE)
        valid = {
            "schema_version": "1.0.0",
            "capability": "coverage",
            "tool_id": "coverage.py",
            "tool_version": COVERAGE_VERSION,
            "status": "COMPLETED",
            "diagnostic_code": None,
            "diagnostic": None,
            "native_result": "native-coverage.json",
        }
        self.assertEqual(normalize_driver_result(json.dumps(valid), requested), valid)
        for changed in (
            {**valid, "schema_version": "2.0.0"},
            {**valid, "capability": "mutation"},
            {**valid, "status": "SUCCESS"},
            {**valid, "extra": True},
        ):
            with self.subTest(changed=changed):
                self.assertIsNone(normalize_driver_result(json.dumps(changed), requested))


class PythonQualityDockerAdapterTests(unittest.TestCase):
    def test_coverage_runs_by_image_id_with_readonly_source_and_separate_output(self) -> None:
        captured: list[list[str]] = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            (workspace / "src/quality_fixture").mkdir(parents=True)
            (workspace / "tests").mkdir()

            def executor(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                captured.append(command)
                if command[:3] == ["docker", "image", "inspect"]:
                    return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
                output = root / "quality-coverage-output"
                (output / "native-coverage.json").write_text(coverage_native(), encoding="utf-8")
                (output / "driver-result.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "1.0.0",
                            "capability": "coverage",
                            "tool_id": "coverage.py",
                            "tool_version": COVERAGE_VERSION,
                            "status": "COMPLETED",
                            "diagnostic_code": None,
                            "diagnostic": None,
                            "scope": ["src/quality_fixture"],
                            "test_paths": ["tests"],
                            "pytest_exit_code": 0,
                            "native_result": "native-coverage.json",
                        }
                    ),
                    encoding="utf-8",
                )
                secret = "sk-" + "a" * 24
                return subprocess.CompletedProcess(
                    command, 0, f"2 passed api_key={secret}", f"token={secret}"
                )

            output = PythonQualityDockerAdapter(root, executor).execute(
                workspace, request(QualityCapability.COVERAGE)
            )
            self.assertIs(output.status, QualityCapabilityStatus.COMPLETED)
            self.assertEqual(output.normalized["branches_total"], 2)
            self.assertNotIn("a" * 24, output.stdout + output.stderr)
            self.assertIn("[REDACTED]", output.stdout + output.stderr)
            self.assertFalse((root / "quality-coverage-output").exists())

        run = captured[1]
        self.assertIn(IMAGE_ID, run)
        self.assertIn("coverage", run)
        self.assertIn("readonly", next(item for item in run if "dst=/workspace" in item))
        self.assertNotIn("readonly", next(item for item in run if "dst=/asef-output" in item))

    def test_request_identity_must_match_pinned_adapter_before_container(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            changed = QualityCapabilityRequest(
                QualityCapability.COVERAGE,
                "coverage.py",
                "7.99.0",
                ("src",),
                ("tests",),
                10,
                QUALITY_IMAGE,
            )
            with self.assertRaisesRegex(ValueError, "tool identity"):
                PythonQualityDockerAdapter(root).execute(workspace, changed)

    def test_malformed_native_result_is_returned_as_failed_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()

            def executor(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                if command[:3] == ["docker", "image", "inspect"]:
                    return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
                output = root / "quality-coverage-output"
                (output / "native-coverage.json").write_text('{"invalid": true}', encoding="utf-8")
                (output / "driver-result.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "1.0.0",
                            "capability": "coverage",
                            "tool_id": "coverage.py",
                            "tool_version": COVERAGE_VERSION,
                            "status": "COMPLETED",
                            "diagnostic_code": None,
                            "diagnostic": None,
                            "native_result": "native-coverage.json",
                        }
                    ),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command, 0, "", "")

            output = PythonQualityDockerAdapter(root, executor).execute(
                workspace, request(QualityCapability.COVERAGE)
            )
            self.assertIs(output.status, QualityCapabilityStatus.FAILED)
            self.assertEqual(output.diagnostic_code, "QUALITY_NATIVE_RESULT_INVALID")
            self.assertEqual(output.native_result_content, '{"invalid": true}')
            self.assertIsNone(output.normalized)

    def test_timeout_is_bounded_and_container_cleanup_is_requested(self) -> None:
        commands: list[list[str]] = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()

            def executor(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                commands.append(command)
                if command[:3] == ["docker", "image", "inspect"]:
                    return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
                if command[:3] == ["docker", "rm", "-f"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                raise subprocess.TimeoutExpired(command, 60, output="partial", stderr="late")

            output = PythonQualityDockerAdapter(root, executor).execute(
                workspace, request(QualityCapability.COVERAGE)
            )
            self.assertIs(output.status, QualityCapabilityStatus.BUDGET_EXHAUSTED)
            self.assertTrue(output.timed_out)
            self.assertEqual(output.exit_code, 124)
            self.assertEqual((output.stdout, output.stderr), ("partial", "late"))
            self.assertTrue(any(command[:3] == ["docker", "rm", "-f"] for command in commands))


if __name__ == "__main__":
    unittest.main()
