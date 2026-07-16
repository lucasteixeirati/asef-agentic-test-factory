from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from asef.adapters.cleanup_executor import CleanupExecutor
from asef.security_contracts import (
    CleanupKind,
    CleanupMode,
    CleanupRequest,
    characterize_filesystem_safety,
)


RUN = (
    sys.platform.startswith("linux")
    and os.environ.get("ASEF_RUN_SECURITY_CLEANUP_TESTS") == "1"
)


@unittest.skipUnless(RUN, "Linux security cleanup tests disabled")
class LinuxCleanupIntegrationTests(unittest.TestCase):
    def test_real_recursive_apply_deletes_only_the_controlled_suite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suite_id = "smoke-20200101T000000Z-aaaaaaaa"
            suite = root / ".asef" / "smoke" / suite_id
            suite.mkdir(parents=True)
            (suite / "suite.json").write_text(
                json.dumps({"suite_id": suite_id, "schema_version": "1.0.0"}),
                encoding="utf-8",
            )
            (suite / "evidence.txt").write_text("controlled", encoding="utf-8")
            profile = characterize_filesystem_safety()
            self.assertTrue(profile.recursive_apply_supported, profile.to_dict())
            report = CleanupExecutor(
                root,
                now=lambda: datetime(2026, 7, 16, tzinfo=UTC),
            ).execute(
                CleanupRequest(CleanupKind.SMOKE, 7, CleanupMode.APPLY)
            )
            self.assertFalse(suite.exists())
        self.assertEqual(report.deleted, 1)
        self.assertEqual(report.failed, 0)

    def test_real_symlink_is_skipped_and_external_target_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suite_id = "smoke-20200101T000000Z-bbbbbbbb"
            external = root / "external"
            external.mkdir()
            marker = external / "marker.txt"
            marker.write_text("preserve", encoding="utf-8")
            (external / "suite.json").write_text(
                json.dumps({"suite_id": suite_id, "schema_version": "1.0.0"}),
                encoding="utf-8",
            )
            suites = root / ".asef" / "smoke"
            suites.mkdir(parents=True)
            link = suites / suite_id
            link.symlink_to(external, target_is_directory=True)
            report = CleanupExecutor(
                root,
                now=lambda: datetime(2026, 7, 16, tzinfo=UTC),
            ).execute(
                CleanupRequest(CleanupKind.SMOKE, 7, CleanupMode.APPLY)
            )
            self.assertTrue(link.is_symlink())
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")
        self.assertEqual(report.skipped, 1)
        self.assertEqual(report.targets[0].reason_code, "SYMBOLIC_LINK")


if __name__ == "__main__":
    unittest.main()
