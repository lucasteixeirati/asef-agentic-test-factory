from __future__ import annotations

import hashlib
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
from asef.adapters.quality_store import QualityEvidenceStore
from asef.adapters.workspace import EphemeralWorkspaceAdapter
from asef.application.ports import ResolvedQualityContext
from asef.application.quality_evaluation import QualityEvaluationService
from asef.context import QualityContext
from asef.contracts import SkeletonRunRequest, SkeletonRunState, UnitTestArtifact
from asef.evaluation_contracts import QualityCapability, QualityCapabilityRequest
from asef.outcomes import RunClassification, RunStatus


class RecordingRunStore:
    def __init__(self) -> None:
        self.saved = 0
        self.reports = 0

    def save_state(self, state: SkeletonRunState) -> None:
        self.saved += 1

    def save_report(self, state, execution, evaluation) -> str:
        self.reports += 1
        self.report_quality = state.facts.get("quality")
        return "report.md"


@unittest.skipUnless(
    os.environ.get("ASEF_RUN_DOCKER_TESTS") == "1"
    and os.environ.get("ASEF_RUN_QUALITY_DOCKER_TESTS") == "1",
    "quality Docker tests disabled",
)
class QualityEvaluationDockerIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(".asef") / f"quality-evaluation-{uuid4().hex}"
        self.root.mkdir(parents=True)
        self.source = Path("examples/python-alpha/reference_sut/src").resolve(strict=True)
        self.before = self._source_hashes()

    def tearDown(self) -> None:
        if os.environ.get("ASEF_KEEP_QUALITY_EVIDENCE") != "1":
            shutil.rmtree(self.root, ignore_errors=True)

    def _source_hashes(self) -> dict[str, str]:
        return {
            path.relative_to(self.source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.source.rglob("*.py"))
        }

    @staticmethod
    def _request() -> SkeletonRunRequest:
        return SkeletonRunRequest(
            context_ref="examples/context/python-alpha-smoke-context.json",
            system_id="alpha-reference-sut",
            requested_skill="unit",
            requirement_title="reference quality baseline",
            requirement_description="exercise accepted reference behavior with quality evidence",
        )

    def test_accepted_reference_run_is_enriched_with_persisted_quality_evidence(self) -> None:
        request = self._request()
        state = SkeletonRunState(request)
        state.status = RunStatus.SUCCEEDED
        state.classification = RunClassification.ACCEPTED
        state.facts["latest_evaluation"] = {"action": "ACCEPT", "conclusion": "accepted"}
        run_dir = self.root / state.run_id
        run_dir.mkdir()
        quality_context = QualityContext.load(Path(request.context_ref))
        context = ResolvedQualityContext(
            quality_context.snapshot_for(request),
            self.source,
            (
                "reference_sut/__init__.py",
                "reference_sut/arithmetic.py",
                "reference_sut/text.py",
            ),
        )
        artifact = UnitTestArtifact(
            relative_path="tests_generated/test_quality_baseline.py",
            content=(
                "import pytest\n"
                "from reference_sut.arithmetic import add, divide\n"
                "from reference_sut.text import normalize_whitespace\n\n"
                "def test_add(): assert add(2, 3) == 5\n"
                "def test_divide(): assert divide(8, 2) == 4\n"
                "def test_divide_by_zero():\n"
                "    with pytest.raises(ValueError): divide(1, 0)\n"
                "def test_normalize(): assert normalize_whitespace(' a   b ') == 'a b'\n"
            ),
            scenario_ids=("add", "divide", "divide-zero", "normalize"),
        )
        requests = (
            QualityCapabilityRequest(
                QualityCapability.COVERAGE,
                "coverage.py",
                COVERAGE_VERSION,
                ("reference_sut",),
                ("tests_generated",),
                120,
                QUALITY_IMAGE,
            ),
            QualityCapabilityRequest(
                QualityCapability.MUTATION,
                "mutmut",
                MUTMUT_VERSION,
                ("reference_sut",),
                ("tests_generated",),
                180,
                QUALITY_IMAGE,
                max_mutants=8,
            ),
        )
        run_store = RecordingRunStore()

        result = QualityEvaluationService(
            EphemeralWorkspaceAdapter(),
            PythonQualityDockerAdapter(Path(".asef")),
            QualityEvidenceStore(self.root),
            run_store,
        ).execute(state, run_dir, context, artifact, requests)

        self.assertTrue(result.report.complete)
        self.assertEqual(len(result.observations), 2)
        self.assertTrue(all(observation.result is not None for observation in result.observations))
        self.assertEqual(
            (state.status, state.classification),
            (RunStatus.SUCCEEDED, RunClassification.ACCEPTED),
        )
        self.assertEqual(run_store.saved, 1)
        self.assertEqual(run_store.reports, 1)
        self.assertTrue(run_store.report_quality["complete"])
        self.assertTrue((run_dir / "quality/coverage/observation.json").is_file())
        self.assertTrue((run_dir / "quality/mutation/observation.json").is_file())
        self.assertTrue((run_dir / "quality/quality-evaluation.json").is_file())
        self.assertFalse((run_dir / "quality-workspace").exists())
        self.assertEqual(self._source_hashes(), self.before)


if __name__ == "__main__":
    unittest.main()
