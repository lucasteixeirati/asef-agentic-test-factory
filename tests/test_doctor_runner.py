from __future__ import annotations

import ast
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from asef.adapters.doctor_check_executor import DoctorCheckExecutor
from asef.adapters.doctor_report_store import DoctorReportStore
from asef.application.doctor_runner import DoctorRequest, DoctorRunner
from asef.cli import main
from asef.security_contracts import (
    DOCTOR_CHECK_IDS,
    DoctorAggregateStatus,
    DoctorCategory,
    DoctorCheck,
    DoctorCheckStatus,
)


_IMAGE_ID = "sha256:" + ("a" * 64)


class _HealthyDocker:
    def __init__(self, *, managed: str = "") -> None:
        self.commands: list[list[str]] = []
        self.managed = managed

    def __call__(
        self, command: list[str], **_: object
    ) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        if command == ["docker", "--version"]:
            return subprocess.CompletedProcess(command, 0, "Docker version 28.1.1\n", "")
        if command[:3] == ["docker", "info", "--format"]:
            payload = {
                "server_version": "28.1.1",
                "os_type": "linux",
                "architecture": "amd64",
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
        if command[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(command, 0, _IMAGE_ID + "\n", "")
        if command[:2] == ["docker", "ps"]:
            return subprocess.CompletedProcess(command, 0, self.managed, "")
        raise AssertionError(command)


class DoctorExecutorTests(unittest.TestCase):
    def test_demo_checks_are_typed_allowlisted_and_do_not_mutate_host(self) -> None:
        docker = _HealthyDocker()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checks = DoctorCheckExecutor(
                docker,
                distribution_version=lambda _: "0.1.0a4",
                environ={},
                workspace_root=root,
            ).execute(DoctorRequest("demo", Path(".asef/doctor")))

        self.assertEqual(tuple(item.check_id for item in checks), DOCTOR_CHECK_IDS)
        self.assertTrue(
            all(
                item.status is DoctorCheckStatus.PASS
                for item in checks
                if item.required
            )
        )
        self.assertIs(
            next(item for item in checks if item.check_id == "context").status,
            DoctorCheckStatus.SKIP,
        )
        self.assertIs(
            next(
                item for item in checks if item.check_id == "live-key-presence"
            ).status,
            DoctorCheckStatus.SKIP,
        )
        flattened = json.dumps([item.to_dict() for item in checks])
        self.assertNotIn("OPENAI_API_KEY", flattened)
        self.assertFalse(any(command[:2] == ["docker", "pull"] for command in docker.commands))
        self.assertFalse(any(command[:2] == ["docker", "build"] for command in docker.commands))

    def test_missing_cli_daemon_and_images_are_distinct_requirement_failures(self) -> None:
        def missing(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            raise FileNotFoundError(command[0])

        with tempfile.TemporaryDirectory() as directory:
            checks = DoctorCheckExecutor(
                missing,
                distribution_version=lambda _: "0.1.0a4",
                workspace_root=Path(directory),
            ).execute(DoctorRequest("demo", Path(".asef/doctor")))
        by_id = {item.check_id: item for item in checks}
        self.assertEqual(by_id["docker-cli"].diagnostic_code, "DOCKER_CLI_MISSING")
        self.assertEqual(by_id["docker-daemon"].diagnostic_code, "DOCKER_CLI_MISSING")
        self.assertEqual(by_id["pytest-image"].diagnostic_code, "PYTEST_IMAGE_MISSING")
        self.assertEqual(by_id["quality-image"].diagnostic_code, "QUALITY_IMAGE_MISSING")
        self.assertFalse(by_id["quality-image"].required)
        self.assertIs(by_id["quality-image"].status, DoctorCheckStatus.WARN)
        self.assertIs(by_id["managed-containers"].status, DoctorCheckStatus.SKIP)

    def test_demo_is_degraded_not_blocked_when_only_optional_quality_image_is_missing(self) -> None:
        class PytestOnlyDocker(_HealthyDocker):
            def __call__(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if command[:3] == ["docker", "image", "inspect"] and "python-quality" in command[-1]:
                    self.commands.append(command)
                    return subprocess.CompletedProcess(command, 1, "", "")
                return super().__call__(command, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            checks = DoctorCheckExecutor(
                PytestOnlyDocker(),
                distribution_version=lambda _: "0.1.0a5",
                environ={},
                workspace_root=Path(directory),
            ).execute(DoctorRequest("demo", Path(".asef/doctor")))
            report = DoctorRunner(
                type("Checks", (), {"execute": lambda self, _: checks})(),
                DoctorReportStore(Path(directory)),
                asef_version="0.1.0a5",
                python_version="3.13.5",
                environment="linux-amd64",
            ).run(DoctorRequest("demo", Path(".asef/doctor"))).report

        quality = next(item for item in checks if item.check_id == "quality-image")
        self.assertIs(quality.status, DoctorCheckStatus.WARN)
        self.assertFalse(quality.required)
        self.assertTrue(report.healthy)
        self.assertIs(report.status, DoctorAggregateStatus.DEGRADED)

    def test_raw_docker_output_and_live_key_value_are_never_persisted(self) -> None:
        sentinel = "sk-proj-" + ("SENSITIVE" * 4)

        def failing_daemon(
            command: list[str], **_: object
        ) -> subprocess.CompletedProcess[str]:
            if command == ["docker", "--version"]:
                return subprocess.CompletedProcess(command, 0, "Docker version 28.1.1", "")
            if command[:3] == ["docker", "info", "--format"]:
                return subprocess.CompletedProcess(command, 1, "", sentinel)
            if command[:3] == ["docker", "image", "inspect"]:
                return subprocess.CompletedProcess(command, 1, "", sentinel)
            if command[:2] == ["docker", "ps"]:
                return subprocess.CompletedProcess(command, 1, "", sentinel)
            raise AssertionError(command)

        with tempfile.TemporaryDirectory() as directory:
            checks = DoctorCheckExecutor(
                failing_daemon,
                distribution_version=lambda _: "0.1.0a4",
                environ={"OPENAI_API_KEY": sentinel},
                workspace_root=Path(directory),
            ).execute(DoctorRequest("live", Path(".asef/doctor")))
        serialized = json.dumps([item.to_dict() for item in checks])
        self.assertNotIn(sentinel, serialized)
        live = next(item for item in checks if item.check_id == "live-key-presence")
        self.assertEqual(live.facts, {"present": True})
        self.assertIs(live.status, DoctorCheckStatus.PASS)

    def test_managed_containers_warn_by_exact_label_count(self) -> None:
        docker = _HealthyDocker(managed="one\ntwo\n")
        with tempfile.TemporaryDirectory() as directory:
            checks = DoctorCheckExecutor(
                docker,
                distribution_version=lambda _: "0.1.0a4",
                workspace_root=Path(directory),
            ).execute(DoctorRequest("demo", Path(".asef/doctor")))
        managed = next(item for item in checks if item.check_id == "managed-containers")
        self.assertIs(managed.status, DoctorCheckStatus.WARN)
        self.assertEqual(managed.facts, {"count": 2})
        command = next(item for item in docker.commands if item[:2] == ["docker", "ps"])
        self.assertIn("label=com.asef.managed=true", command)

    def test_invalid_explicit_context_is_blocking_without_reflecting_path(self) -> None:
        docker = _HealthyDocker()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = root / "private-context-name.json"
            context.write_text("{}", encoding="utf-8")
            checks = DoctorCheckExecutor(
                docker,
                distribution_version=lambda _: "0.1.0a4",
                workspace_root=root,
            ).execute(
                DoctorRequest("demo", Path(".asef/doctor"), context_ref=context)
            )
        check = next(item for item in checks if item.check_id == "context")
        self.assertTrue(check.required)
        self.assertIs(check.status, DoctorCheckStatus.FAIL)
        self.assertNotIn(context.name, json.dumps(check.to_dict()))

    def test_malformed_allowlisted_docker_field_is_not_persisted(self) -> None:
        sentinel = "sk-proj-" + ("SENSITIVE" * 4)

        def malformed(
            command: list[str], **_: object
        ) -> subprocess.CompletedProcess[str]:
            if command == ["docker", "--version"]:
                return subprocess.CompletedProcess(command, 0, "Docker version 28.1.1", "")
            if command[:3] == ["docker", "info", "--format"]:
                payload = {
                    "server_version": sentinel,
                    "os_type": "linux",
                    "architecture": "amd64",
                }
                return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
            if command[:3] == ["docker", "image", "inspect"]:
                return subprocess.CompletedProcess(command, 0, _IMAGE_ID, "")
            if command[:2] == ["docker", "ps"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            raise AssertionError(command)

        with tempfile.TemporaryDirectory() as directory:
            checks = DoctorCheckExecutor(
                malformed,
                distribution_version=lambda _: "0.1.0a4",
                workspace_root=Path(directory),
            ).execute(DoctorRequest("demo", Path(".asef/doctor")))
        serialized = json.dumps([item.to_dict() for item in checks])
        self.assertNotIn(sentinel, serialized)
        daemon = next(item for item in checks if item.check_id == "docker-daemon")
        self.assertEqual(daemon.diagnostic_code, "DOCKER_INFO_INVALID")

    def test_internal_check_error_is_distinct_from_missing_requirement(self) -> None:
        def internal_error(
            command: list[str], **_: object
        ) -> subprocess.CompletedProcess[str]:
            if command == ["docker", "--version"]:
                return subprocess.CompletedProcess(command, 0, "Docker version 28.1.1", "")
            if command[:3] == ["docker", "info", "--format"]:
                raise RuntimeError("raw internal detail")
            if command[:3] == ["docker", "image", "inspect"]:
                return subprocess.CompletedProcess(command, 0, _IMAGE_ID, "")
            if command[:2] == ["docker", "ps"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            raise AssertionError(command)

        with tempfile.TemporaryDirectory() as directory:
            checks = DoctorCheckExecutor(
                internal_error,
                distribution_version=lambda _: "0.1.0a4",
                workspace_root=Path(directory),
            ).execute(DoctorRequest("demo", Path(".asef/doctor")))
        daemon = next(item for item in checks if item.check_id == "docker-daemon")
        self.assertIs(daemon.status, DoctorCheckStatus.FAIL)
        self.assertEqual(daemon.diagnostic_code, "DOCTOR_CHECK_FAILED")
        self.assertNotIn("raw internal detail", json.dumps(daemon.to_dict()))


class _FakeChecks:
    def execute(self, _: DoctorRequest) -> tuple[DoctorCheck, ...]:
        return (
            DoctorCheck(
                check_id="python-version",
                category=DoctorCategory.RUNTIME,
                required=True,
                status=DoctorCheckStatus.PASS,
                diagnostic_code="PYTHON_VERSION_SUPPORTED",
                summary="Python runtime is supported.",
                duration_ms=1,
                timeout_ms=5000,
                facts={
                    "major": 3,
                    "minor": 13,
                    "micro": 5,
                    "implementation": "CPython",
                },
            ),
        )


class _BlockedChecks:
    def execute(self, _: DoctorRequest) -> tuple[DoctorCheck, ...]:
        return (
            DoctorCheck(
                check_id="python-version",
                category=DoctorCategory.RUNTIME,
                required=True,
                status=DoctorCheckStatus.FAIL,
                diagnostic_code="PYTHON_VERSION_UNSUPPORTED",
                summary="Python 3.13 or newer is required.",
                duration_ms=1,
                timeout_ms=5000,
                facts={
                    "major": 3,
                    "minor": 12,
                    "micro": 0,
                    "implementation": "CPython",
                },
            ),
        )


class DoctorRunnerTests(unittest.TestCase):
    def test_runner_persists_json_and_markdown_below_asef(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = DoctorRunner(
                _FakeChecks(),
                DoctorReportStore(root),
                asef_version="0.1.0a4",
                python_version="3.13.5",
                environment="windows-amd64",
            ).run(DoctorRequest("demo", Path(".asef/doctor")))
            payload = json.loads(output.report_json.read_text(encoding="utf-8"))
            markdown = output.report_markdown.read_text(encoding="utf-8")
        self.assertEqual(payload["status"], DoctorAggregateStatus.HEALTHY.value)
        self.assertIn("# ASEF Doctor", markdown)
        self.assertTrue(output.report_dir.is_relative_to(root / ".asef"))

    def test_application_runner_does_not_import_adapters_or_subprocess(self) -> None:
        source = Path("src/asef/application/doctor_runner.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        self.assertFalse(any("adapter" in item for item in imports))
        self.assertNotIn("subprocess", imports)

    def test_cli_returns_zero_for_ready_and_seven_for_blocked_report(self) -> None:
        for fake, expected, status in (
            (_FakeChecks(), 0, DoctorAggregateStatus.HEALTHY.value),
            (_BlockedChecks(), 7, DoctorAggregateStatus.BLOCKED.value),
        ):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                previous = Path.cwd()
                stdout, stderr = StringIO(), StringIO()
                try:
                    os.chdir(directory)
                    with (
                        patch("asef.cli.DoctorCheckExecutor", return_value=fake),
                        redirect_stdout(stdout),
                        redirect_stderr(stderr),
                    ):
                        code = main(["doctor", "--output", ".asef/doctor"])
                finally:
                    os.chdir(previous)
                payload = json.loads(stdout.getvalue())
                self.assertEqual(code, expected)
                self.assertEqual(payload["status"], status)
                self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
