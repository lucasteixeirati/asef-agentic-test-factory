from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from asef.adapters.quality_execution import COVERAGE_VERSION, QUALITY_IMAGE
from asef.adapters.quality_store import QualityEvidenceStore
from asef.adapters.workspace import EphemeralWorkspaceAdapter
from asef.application.ports import QualityExecutionOutput, ResolvedQualityContext
from asef.application.quality_evaluation import QualityEvaluationService
from asef.context import QualityContext
from asef.contracts import SkeletonRunRequest, SkeletonRunState, UnitTestArtifact
from asef.evaluation_contracts import (
    QualityCapability,
    QualityCapabilityRequest,
    QualityCapabilityStatus,
    QualityEvaluationReport,
)
from asef.outcomes import RunClassification, RunStatus


def run_request() -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="examples/context/walking-skeleton-context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title="quality evidence",
        requirement_description="persist coverage and mutation evidence",
    )


def quality_request() -> QualityCapabilityRequest:
    return QualityCapabilityRequest(
        QualityCapability.COVERAGE,
        "coverage.py",
        COVERAGE_VERSION,
        ("src",),
        ("tests_generated",),
        60,
        QUALITY_IMAGE,
    )


def native_coverage() -> str:
    return json.dumps(
        {
            "meta": {"version": COVERAGE_VERSION, "branch_coverage": True},
            "totals": {
                "covered_lines": 3,
                "num_statements": 4,
                "covered_branches": 1,
                "num_branches": 2,
                "excluded_lines": 0,
            },
        }
    )


def execution(request: QualityCapabilityRequest | None = None) -> QualityExecutionOutput:
    requested = request or quality_request()
    return QualityExecutionOutput(
        request=requested,
        capability=requested.capability,
        status=QualityCapabilityStatus.COMPLETED,
        image="sha256:" + "a" * 64,
        command=("coverage",),
        tool_id=requested.tool_id,
        tool_version=requested.tool_version,
        duration_ms=25,
        exit_code=0,
        native_result_content=native_coverage(),
        driver_result_content='{"status":"COMPLETED"}',
        normalized={
            "lines_covered": 3,
            "lines_total": 4,
            "branches_covered": 1,
            "branches_total": 2,
            "excluded_lines": 0,
        },
        stdout="1 passed\n",
        stderr="",
    )


def accepted_state() -> SkeletonRunState:
    state = SkeletonRunState(run_request())
    state.status = RunStatus.SUCCEEDED
    state.classification = RunClassification.ACCEPTED
    return state


class QualityEvidenceStoreTests(unittest.TestCase):
    def test_persists_native_normalized_and_observation_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = accepted_state()
            (root / state.run_id).mkdir()
            store = QualityEvidenceStore(root)
            observation, refs = store.save_execution(state, execution())
            self.assertIs(observation.status, QualityCapabilityStatus.COMPLETED)
            self.assertEqual(observation.result.line_percent, 75.0)
            self.assertEqual(observation.result.branch_percent, 50.0)
            self.assertEqual(len(refs), 6)
            self.assertTrue((root / state.run_id / "quality/coverage/observation.json").is_file())
            with self.assertRaises(FileExistsError):
                store.save_execution(state, execution())

    def test_unavailable_observation_has_no_fabricated_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = accepted_state()
            (root / state.run_id).mkdir()
            output = execution()
            output = QualityExecutionOutput(
                **{
                    **{field: getattr(output, field) for field in output.__dataclass_fields__},
                    "status": QualityCapabilityStatus.UNAVAILABLE,
                    "native_result_content": None,
                    "driver_result_content": None,
                    "normalized": None,
                    "diagnostic_code": "QUALITY_TOOL_UNAVAILABLE",
                    "diagnostic": "Quality tool unavailable",
                }
            )
            observation, _ = QualityEvidenceStore(root).save_execution(state, output)
            self.assertIsNone(observation.result)
            report = QualityEvaluationReport((observation,), 0)
            self.assertFalse(report.complete)


class FakeExecutor:
    def execute(self, workspace, request):
        self.workspace = workspace
        return execution(request)


class UnavailableExecutor:
    def execute(self, workspace, request):
        raise OSError("docker is unavailable")


class FailedExecutor:
    def execute(self, workspace, request):
        raise RuntimeError("token=do-not-persist")


class FakeRunStore:
    def __init__(self) -> None:
        self.saved = 0
        self.reports = 0

    def save_state(self, state) -> None:
        self.saved += 1

    def save_report(self, state, execution, evaluation) -> str:
        self.reports += 1
        self.report_quality = state.facts.get("quality")
        return "report.md"


class QualityEvaluationServiceTests(unittest.TestCase):
    def test_accepted_run_is_enriched_without_changing_functional_classification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "src.py").write_text("VALUE = 1\n", encoding="utf-8")
            state = accepted_state()
            state.facts["latest_evaluation"] = {"action": "ACCEPT", "conclusion": "accepted"}
            run_dir = root / state.run_id
            run_dir.mkdir()
            quality = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
            context = ResolvedQualityContext(
                quality.snapshot_for(run_request()), source, ("src.py",)
            )
            artifact = UnitTestArtifact(
                relative_path="tests_generated/test_value.py",
                content="def test_value(): assert 1 == 1\n",
                scenario_ids=("value",),
                attempt=1,
            )
            run_store = FakeRunStore()
            executor = FakeExecutor()
            result = QualityEvaluationService(
                EphemeralWorkspaceAdapter(),
                executor,
                QualityEvidenceStore(root),
                run_store,
            ).execute(state, run_dir, context, artifact, (quality_request(),))

            self.assertTrue(result.report.complete)
            self.assertEqual((state.status, state.classification), (RunStatus.SUCCEEDED, RunClassification.ACCEPTED))
            self.assertIn("quality", state.facts)
            self.assertGreaterEqual(len(state.evidence_refs), 7)
            self.assertEqual(run_store.saved, 1)
            self.assertEqual(run_store.reports, 1)
            self.assertTrue(run_store.report_quality["complete"])
            self.assertFalse((run_dir / "quality-workspace").exists())

    def test_quality_evaluation_rejects_unaccepted_or_duplicate_requests(self) -> None:
        state = accepted_state()
        state.classification = RunClassification.TEST_FAILURE
        service = QualityEvaluationService(None, None, None, None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "accepted"):
            service.execute(state, Path("."), None, None, (quality_request(),))  # type: ignore[arg-type]

        state.classification = RunClassification.ACCEPTED
        with self.assertRaisesRegex(ValueError, "unique"):
            service.execute(
                state,
                Path("."),
                None,  # type: ignore[arg-type]
                None,  # type: ignore[arg-type]
                (quality_request(), quality_request()),
            )

    def test_unavailable_and_failed_tools_are_explicit_and_do_not_change_acceptance(self) -> None:
        for executor, expected, diagnostic in (
            (UnavailableExecutor(), QualityCapabilityStatus.UNAVAILABLE, "QUALITY_TOOL_UNAVAILABLE"),
            (FailedExecutor(), QualityCapabilityStatus.FAILED, "QUALITY_EXECUTION_FAILED"),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "source"
                source.mkdir()
                (source / "src.py").write_text("VALUE = 1\n", encoding="utf-8")
                state = accepted_state()
                run_dir = root / state.run_id
                run_dir.mkdir()
                quality = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
                context = ResolvedQualityContext(
                    quality.snapshot_for(run_request()), source, ("src.py",)
                )
                artifact = UnitTestArtifact(
                    "tests_generated/test_value.py",
                    "def test_value(): assert 1 == 1\n",
                    ("value",),
                )
                result = QualityEvaluationService(
                    EphemeralWorkspaceAdapter(), executor, QualityEvidenceStore(root), FakeRunStore()
                ).execute(state, run_dir, context, artifact, (quality_request(),))
                observation = result.observations[0]
                self.assertIs(observation.status, expected)
                self.assertEqual(observation.diagnostic_code, diagnostic)
                self.assertIsNone(observation.result)
                self.assertFalse(result.report.complete)
                self.assertEqual(
                    (state.status, state.classification),
                    (RunStatus.SUCCEEDED, RunClassification.ACCEPTED),
                )
                if expected is QualityCapabilityStatus.FAILED:
                    self.assertNotIn("do-not-persist", observation.diagnostic or "")


if __name__ == "__main__":
    unittest.main()
