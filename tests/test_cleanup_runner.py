from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

from asef.adapters.cleanup_executor import CleanupExecutor
from asef.adapters.cleanup_report_store import CleanupReportStore
from asef.application.cleanup_runner import CleanupRunner
from asef.cli import main
from asef.ephemeral_cleanup import cleanup_ephemeral_directory
from asef.security_contracts import (
    CleanupKind,
    CleanupMode,
    CleanupRequest,
    CleanupTargetStatus,
)


NOW = datetime(2026, 7, 16, 15, 0, tzinfo=UTC)


def _smoke_fixture(root: Path, stamp: str = "20200101T000000Z") -> Path:
    suite_id = f"smoke-{stamp}-aaaaaaaa"
    suite = root / ".asef" / "smoke" / suite_id
    suite.mkdir(parents=True)
    (suite / "suite.json").write_text(
        json.dumps({"suite_id": suite_id, "schema_version": "1.0.0"}),
        encoding="utf-8",
    )
    (suite / "evidence.txt").write_text("public evidence", encoding="utf-8")
    return suite


class CleanupExecutorTests(unittest.TestCase):
    def test_dry_run_plans_old_valid_suite_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suite = _smoke_fixture(root)
            report = CleanupExecutor(
                root, now=lambda: NOW, recursive_apply_supported=False
            ).execute(CleanupRequest(CleanupKind.SMOKE, 7))
            self.assertTrue(suite.exists())
        self.assertEqual(report.planned, 1)
        self.assertEqual(report.deleted, 0)
        self.assertEqual(report.targets[0].reason_code, "TARGET_ELIGIBLE")

    def test_apply_refuses_recursive_deletion_when_profile_is_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suite = _smoke_fixture(root)
            report = CleanupExecutor(
                root, now=lambda: NOW, recursive_apply_supported=False
            ).execute(
                CleanupRequest(CleanupKind.SMOKE, 7, CleanupMode.APPLY)
            )
            self.assertTrue(suite.exists())
        self.assertEqual(report.failed, 1)
        self.assertEqual(
            report.targets[0].reason_code, "RECURSIVE_APPLY_UNSUPPORTED"
        )

    def test_supported_profile_deletes_only_revalidated_controlled_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suite = _smoke_fixture(root)
            report = CleanupExecutor(
                root, now=lambda: NOW, recursive_apply_supported=True
            ).execute(
                CleanupRequest(CleanupKind.SMOKE, 7, CleanupMode.APPLY)
            )
            self.assertFalse(suite.exists())
        self.assertEqual(report.deleted, 1)
        self.assertEqual(report.targets[0].reason_code, "TARGET_DELETED")

    def test_identity_change_between_plan_and_apply_fails_closed(self) -> None:
        class MutatingExecutor(CleanupExecutor):
            def _apply(self, target):  # type: ignore[no-untyped-def]
                path = self.workspace_root / Path(target.target_ref)
                (path / "changed-after-plan.txt").write_text("changed", encoding="utf-8")
                return super()._apply(target)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suite = _smoke_fixture(root)
            report = MutatingExecutor(
                root, now=lambda: NOW, recursive_apply_supported=True
            ).execute(
                CleanupRequest(CleanupKind.SMOKE, 7, CleanupMode.APPLY)
            )
            self.assertTrue(suite.exists())
        self.assertEqual(report.failed, 1)
        self.assertEqual(
            report.targets[0].reason_code, "TARGET_REVALIDATION_FAILED"
        )

    def test_malformed_and_too_new_targets_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            malformed = root / ".asef" / "smoke" / "unknown"
            malformed.mkdir(parents=True)
            _smoke_fixture(root, "20260716T145959Z")
            report = CleanupExecutor(root, now=lambda: NOW).execute(
                CleanupRequest(CleanupKind.SMOKE, 7)
            )
        self.assertEqual(report.skipped, 2)
        self.assertEqual(
            {item.reason_code for item in report.targets},
            {"MANIFEST_INVALID", "TARGET_TOO_NEW"},
        )

    def test_old_rotated_log_file_can_be_applied_without_directory_removal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / ".asef" / "logs" / "asef.jsonl.1"
            log.parent.mkdir(parents=True)
            log.write_text(
                json.dumps({"timestamp": "2020-01-01T00:00:00+00:00"}) + "\n",
                encoding="utf-8",
            )
            report = CleanupExecutor(
                root, now=lambda: NOW, recursive_apply_supported=False
            ).execute(
                CleanupRequest(CleanupKind.LOGS, 7, CleanupMode.APPLY)
            )
            self.assertFalse(log.exists())
        self.assertEqual(report.deleted, 1)

    def test_linked_target_is_skipped_and_external_target_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            marker = outside / "marker.txt"
            marker.write_text("preserve", encoding="utf-8")
            suites = root / ".asef" / "smoke"
            suites.mkdir(parents=True)
            link = suites / "smoke-20200101T000000Z-aaaaaaaa"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("host does not allow symbolic link fixture")
            report = CleanupExecutor(
                root, now=lambda: NOW, recursive_apply_supported=True
            ).execute(
                CleanupRequest(CleanupKind.SMOKE, 7, CleanupMode.APPLY)
            )
            self.assertTrue(marker.exists())
            self.assertTrue(link.exists())
        self.assertEqual(report.skipped, 1)
        self.assertEqual(report.targets[0].reason_code, "SYMBOLIC_LINK")

    def test_container_cleanup_uses_managed_label_and_exact_id(self) -> None:
        container_id = "a" * 64
        inspect_payload = json.dumps(
            {
                "id": container_id,
                "created": "2020-01-01T00:00:00Z",
                "managed": "true",
            }
        )
        commands: list[list[str]] = []

        def docker(
            command: list[str], **_: object
        ) -> subprocess.CompletedProcess[str]:
            commands.append(command)
            if command[:2] == ["docker", "ps"]:
                return subprocess.CompletedProcess(command, 0, container_id, "")
            if command[:2] == ["docker", "inspect"] and "--format" in command:
                return subprocess.CompletedProcess(command, 0, inspect_payload, "")
            if command[:3] == ["docker", "rm", "-f"]:
                return subprocess.CompletedProcess(command, 0, container_id, "")
            if command[:2] == ["docker", "inspect"]:
                return subprocess.CompletedProcess(command, 1, "", "")
            raise AssertionError(command)

        with tempfile.TemporaryDirectory() as directory:
            report = CleanupExecutor(
                Path(directory), docker, now=lambda: NOW
            ).execute(
                CleanupRequest(CleanupKind.CONTAINERS, 7, CleanupMode.APPLY)
            )
        self.assertEqual(report.deleted, 1)
        self.assertIn("label=com.asef.managed=true", commands[0])
        self.assertIn(["docker", "rm", "-f", container_id], commands)

    def test_all_does_not_plan_overlapping_run_and_quality_targets(self) -> None:
        run_id = "12345678-1234-4123-8123-123456789abc"

        def no_containers(
            command: list[str], **_: object
        ) -> subprocess.CompletedProcess[str]:
            self.assertEqual(command[:3], ["docker", "ps", "--no-trunc"])
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / ".asef" / "runs" / run_id
            quality = run / "quality" / "coverage"
            quality.mkdir(parents=True)
            (quality / "result.json").write_text("{}", encoding="utf-8")
            (run / "state.json").write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "created_at": "2020-01-01T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            report = CleanupExecutor(
                root, no_containers, now=lambda: NOW
            ).execute(CleanupRequest(CleanupKind.ALL, 7))
        refs = [item.target_ref for item in report.targets]
        self.assertIn(f".asef/runs/{run_id}", refs)
        self.assertNotIn(f".asef/runs/{run_id}/quality", refs)


class CleanupRunnerTests(unittest.TestCase):
    def test_runner_persists_tombstone_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _smoke_fixture(root)
            output = CleanupRunner(
                CleanupExecutor(root, now=lambda: NOW),
                CleanupReportStore(root),
            ).run(CleanupRequest(CleanupKind.SMOKE, 7))
            payload = json.loads(output.report_json.read_text(encoding="utf-8"))
            markdown = output.report_markdown.read_text(encoding="utf-8")
        self.assertEqual(payload["planned"], 1)
        self.assertIn("# ASEF Cleanup", markdown)
        self.assertIn("secure erase", markdown)

    def test_cli_is_dry_run_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suite = _smoke_fixture(root)
            previous = Path.cwd()
            stdout, stderr = StringIO(), StringIO()
            try:
                os.chdir(root)
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = main(
                        ["cleanup", "--kind", "smoke", "--older-than-days", "7"]
                    )
            finally:
                os.chdir(previous)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(suite.exists())
        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"], CleanupMode.DRY_RUN.value)
        self.assertEqual(stderr.getvalue(), "")

    def test_common_ephemeral_cleanup_reports_unsafe_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            run = root / "run"
            run.mkdir()
            link = run / "workspace"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("host does not allow symbolic link fixture")
            observation = cleanup_ephemeral_directory(
                run, link, "generated-workspace"
            )
            self.assertFalse(observation.removed)
            self.assertEqual(
                observation.diagnostic_code, "TARGET_SYMBOLIC_LINK"
            )
            self.assertTrue(outside.exists())


if __name__ == "__main__":
    unittest.main()
