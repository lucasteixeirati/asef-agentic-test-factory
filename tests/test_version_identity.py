from __future__ import annotations

import tomllib
import unittest
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest.mock import patch

from asef.application.build_alpha_report import BuildAlphaReportService
from asef.cli import _package_version


ROOT = Path(__file__).resolve().parents[1]


class VersionIdentityTests(unittest.TestCase):
    def test_source_tree_fallbacks_match_package_metadata(self) -> None:
        expected = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        with patch("asef.cli.metadata.version", side_effect=PackageNotFoundError):
            self.assertEqual(_package_version(), expected)
        with patch("asef.application.build_alpha_report.version", side_effect=PackageNotFoundError):
            self.assertEqual(BuildAlphaReportService._asef_version(), expected)


if __name__ == "__main__":
    unittest.main()
