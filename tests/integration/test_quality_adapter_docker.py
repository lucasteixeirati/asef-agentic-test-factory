from __future__ import annotations

import hashlib
import json
import os
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from asef.adapters.quality_execution import (
    COVERAGE_VERSION,
    MUTMUT_VERSION,
    QUALITY_IMAGE,
    PythonQualityDockerAdapter,
)
from asef.evaluation_contracts import (
    QualityCapability,
    QualityCapabilityRequest,
    QualityCapabilityStatus,
)


@unittest.skipUnless(
    os.environ.get("ASEF_RUN_DOCKER_TESTS") == "1"
    and os.environ.get("ASEF_RUN_QUALITY_DOCKER_TESTS") == "1",
    "quality Docker tests disabled",
)
class QualityAdapterDockerIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(".asef") / f"quality-adapter-{uuid4().hex}"
        self.workspace = self.root / "workspace"
        shutil.copytree("examples/python-alpha/quality_conformance", self.workspace)
        self.manifest = json.loads((self.workspace / "manifest.json").read_text(encoding="utf-8"))
        self.before = self._hashes()

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _hashes(self) -> dict[str, str]:
        return {
            path.relative_to(self.workspace).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.workspace.rglob("*"))
            if path.is_file()
        }

    def request(self, capability: QualityCapability) -> QualityCapabilityRequest:
        return QualityCapabilityRequest(
            capability=capability,
            tool_id="coverage.py" if capability is QualityCapability.COVERAGE else "mutmut",
            tool_version=COVERAGE_VERSION if capability is QualityCapability.COVERAGE else MUTMUT_VERSION,
            scope=("src/quality_fixture",),
            test_paths=("tests",),
            timeout_seconds=120,
            execution_environment_ref=QUALITY_IMAGE,
            max_mutants=3 if capability is QualityCapability.MUTATION else None,
        )

    def test_coverage_normalizes_known_fixture_without_modifying_source(self) -> None:
        result = PythonQualityDockerAdapter(Path(".asef")).execute(
            self.workspace, self.request(QualityCapability.COVERAGE)
        )
        self.assertIs(
            result.status,
            QualityCapabilityStatus.COMPLETED,
            (result.diagnostic_code, result.diagnostic, result.stdout, result.stderr),
        )
        expected = dict(self.manifest["coverage"])
        expected.pop("tool_version")
        self.assertEqual(result.normalized, expected)
        self.assertEqual(self._hashes(), self.before)

    def test_mutation_admits_at_most_budget_and_preserves_deferred_mutants(self) -> None:
        result = PythonQualityDockerAdapter(Path(".asef")).execute(
            self.workspace, self.request(QualityCapability.MUTATION)
        )
        self.assertIs(
            result.status,
            QualityCapabilityStatus.COMPLETED,
            (result.diagnostic_code, result.diagnostic, result.stdout, result.stderr),
        )
        expected = dict(self.manifest["mutation"])
        expected.pop("tool_version")
        expected.pop("max_mutants")
        self.assertEqual(result.normalized, expected)
        self.assertEqual(
            result.normalized["admitted"] + result.normalized["deferred"],
            result.normalized["mutants_total"],
        )
        self.assertEqual(self._hashes(), self.before)


if __name__ == "__main__":
    unittest.main()
