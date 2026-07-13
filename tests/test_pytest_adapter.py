from __future__ import annotations

import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from asef.adapters.pytest_execution import (
    PYTEST_IMAGE,
    PytestDockerAdapter,
    normalize_pytest_result,
)
from asef.context import QualityContext
from asef.contracts import SkeletonRunRequest, TestExecutionOutcome


IMAGE_ID = "sha256:" + "c" * 64


def snapshot():
    context = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
    return context.snapshot_for(
        SkeletonRunRequest(
            context_ref="examples/context/walking-skeleton-context.json",
            system_id="calculator-service",
            requested_skill="unit",
            requirement_title="test",
            requirement_description="test pytest adapter",
        )
    )


def junit(*, tests: int, failures: int = 0, errors: int = 0, skipped: int = 0) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<testsuites name="pytest tests">'
        f'<testsuite name="pytest" errors="{errors}" failures="{failures}" '
        f'skipped="{skipped}" tests="{tests}" time="0.01" />'
        "</testsuites>"
    )


class PytestNormalizerTests(unittest.TestCase):
    def test_distinguishes_pass_assertion_error_no_tests_and_infrastructure(self) -> None:
        cases = (
            (junit(tests=2), 0, False, TestExecutionOutcome.PASSED),
            (junit(tests=2, failures=1), 1, False, TestExecutionOutcome.ASSERTION_FAILURE),
            (junit(tests=1, errors=1), 2, False, TestExecutionOutcome.TEST_ERROR),
            (junit(tests=0), 5, False, TestExecutionOutcome.NO_TESTS),
            (None, 125, False, TestExecutionOutcome.INFRASTRUCTURE_ERROR),
            (None, 124, True, TestExecutionOutcome.INFRASTRUCTURE_ERROR),
        )
        for xml, exit_code, timed_out, expected in cases:
            with self.subTest(expected=expected):
                self.assertIs(normalize_pytest_result(xml, exit_code, timed_out).outcome, expected)

    def test_counts_are_aggregated_without_counting_nested_nodes_twice(self) -> None:
        xml = (
            '<testsuites><testsuite tests="2" failures="1" errors="0" skipped="0">'
            '<testcase name="one"/><testcase name="two"><failure/></testcase>'
            '</testsuite><testsuite tests="1" failures="0" errors="0" skipped="1" />'
            "</testsuites>"
        )
        result = normalize_pytest_result(xml, 1)
        self.assertEqual((result.tests, result.passed, result.failed, result.errors, result.skipped), (3, 1, 1, 0, 1))

    def test_malformed_or_active_xml_is_a_tool_error(self) -> None:
        for xml in (
            "<not-junit/>",
            "<!DOCTYPE x [<!ENTITY y 'z'>]><testsuites/>",
            '<testsuite tests="invalid"/>',
            '<testsuite tests="-1"/>',
            '<testsuite tests="1" failures="2"/>',
        ):
            with self.subTest(xml=xml):
                result = normalize_pytest_result(xml, 1)
                self.assertIs(result.outcome, TestExecutionOutcome.TOOL_ERROR)

    def test_direct_testsuite_and_tool_exit_codes_are_normalized(self) -> None:
        direct = '<testsuite tests="1" failures="0" errors="0" skipped="0"/>'
        self.assertIs(normalize_pytest_result(direct, 0).outcome, TestExecutionOutcome.PASSED)
        self.assertIs(normalize_pytest_result(direct, 3).outcome, TestExecutionOutcome.TOOL_ERROR)
        self.assertIs(normalize_pytest_result(direct, 99).outcome, TestExecutionOutcome.TOOL_ERROR)


class PytestDockerAdapterTests(unittest.TestCase):
    def test_resolves_immutable_image_runs_with_separate_output_and_cleans_capture(self) -> None:
        captured: list[list[str]] = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            (workspace / "tests_generated").mkdir(parents=True)

            def executor(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                captured.append(command)
                if command[:3] == ["docker", "image", "inspect"]:
                    return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
                junit_path = workspace.parent / "pytest-output/pytest-junit.xml"
                junit_path.write_text(junit(tests=2, skipped=1), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "1 passed, 1 skipped", "")

            result = PytestDockerAdapter(root, executor).execute(workspace, snapshot())
            self.assertEqual(result.image, IMAGE_ID)
            self.assertEqual(result.tool_id, "pytest")
            self.assertEqual((result.tests, result.passed, result.skipped), (2, 1, 1))
            self.assertIs(result.outcome, TestExecutionOutcome.PASSED)
            self.assertIsNotNone(result.raw_result_content)
            self.assertFalse((root / "pytest-output").exists())

        docker_run = captured[1]
        workspace_mount = next(item for item in docker_run if "dst=/workspace" in item)
        output_mount = next(item for item in docker_run if "dst=/asef-output" in item)
        self.assertIn("readonly", workspace_mount)
        self.assertNotIn("readonly", output_mount)
        self.assertIn("--network", docker_run)
        self.assertIn(IMAGE_ID, docker_run)

    def test_missing_or_mutable_image_identity_fails_before_container(self) -> None:
        def executor(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 1, "", "missing")

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(OSError, "unavailable"):
                PytestDockerAdapter(Path(directory), executor, image=PYTEST_IMAGE)._resolve_image_id()

    def test_wrong_profile_and_oversized_junit_fail_closed(self) -> None:
        wrong = replace(snapshot(), language_profile="node-typescript")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            with self.assertRaisesRegex(ValueError, "python-pytest"):
                PytestDockerAdapter(root).execute(workspace, wrong)

            result = root / "oversized.xml"
            result.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "exceeds"):
                PytestDockerAdapter._read_junit(result)


if __name__ == "__main__":
    unittest.main()
