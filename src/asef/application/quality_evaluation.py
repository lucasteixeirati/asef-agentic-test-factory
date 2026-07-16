from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from ..contracts import SkeletonRunState, UnitTestArtifact
from ..evaluation_contracts import (
    QualityCapabilityObservation,
    QualityCapabilityRequest,
    QualityCapabilityStatus,
    QualityEvaluationReport,
)
from ..outcomes import RunClassification, RunStatus
from .ports import (
    QualityEvidenceStorePort,
    QualityExecutionOutput,
    QualityExecutionPort,
    ResolvedQualityContext,
    RunStorePort,
    WorkspacePort,
)


@dataclass(slots=True, frozen=True)
class QualityEvaluationOutput:
    report: QualityEvaluationReport
    observations: tuple[QualityCapabilityObservation, ...]


class QualityEvaluationService:
    def __init__(
        self,
        workspace: WorkspacePort,
        executor: QualityExecutionPort,
        evidence_store: QualityEvidenceStorePort,
        run_store: RunStorePort,
    ) -> None:
        self.workspace = workspace
        self.executor = executor
        self.evidence_store = evidence_store
        self.run_store = run_store

    def execute(
        self,
        state: SkeletonRunState,
        run_dir: Path,
        context: ResolvedQualityContext,
        artifact: UnitTestArtifact,
        requests: tuple[QualityCapabilityRequest, ...],
    ) -> QualityEvaluationOutput:
        if state.status is not RunStatus.SUCCEEDED or state.classification is not RunClassification.ACCEPTED:
            raise ValueError("quality evaluation requires a functionally accepted run")
        if not requests:
            raise ValueError("quality evaluation requires at least one capability request")
        capabilities = [request.capability for request in requests]
        if len(capabilities) != len(set(capabilities)):
            raise ValueError("quality evaluation capability requests must be unique")
        for request in requests:
            request.validate()

        staged = self.workspace.stage_quality(run_dir, context, artifact)
        observations: list[QualityCapabilityObservation] = []
        started = perf_counter()
        try:
            for request in requests:
                try:
                    output = self.executor.execute(staged.workspace, request)
                except OSError:
                    output = self._unavailable(request)
                except (ValueError, RuntimeError) as exc:
                    output = self._failed(request, str(exc))
                observation, refs = self.evidence_store.save_execution(state, output)
                observations.append(observation)
                state.evidence_refs.extend(ref for ref in refs if ref not in state.evidence_refs)
            duration_ms = max(0, round((perf_counter() - started) * 1000))
            report = QualityEvaluationReport(
                tuple(observations),
                duration_ms,
                ("quality signals are evidence, not universal acceptance thresholds",),
            )
            report_ref = self.evidence_store.save_evaluation(state, report)
            state.evidence_refs.append(report_ref)
            state.facts["quality"] = report.to_dict()
            self.run_store.save_state(state)
            functional_evaluation = state.facts.get("latest_evaluation")
            if isinstance(functional_evaluation, dict):
                self.run_store.save_report(state, None, functional_evaluation)
            return QualityEvaluationOutput(report, tuple(observations))
        finally:
            shutil.rmtree(staged.workspace, ignore_errors=True)

    @staticmethod
    def _unavailable(request: QualityCapabilityRequest) -> QualityExecutionOutput:
        return QualityExecutionOutput(
            request=request,
            capability=request.capability,
            status=QualityCapabilityStatus.UNAVAILABLE,
            image=request.execution_environment_ref,
            command=(),
            tool_id=request.tool_id,
            tool_version=request.tool_version,
            duration_ms=0,
            exit_code=127,
            native_result_content=None,
            driver_result_content=None,
            normalized=None,
            stdout="",
            stderr="",
            diagnostic_code="QUALITY_TOOL_UNAVAILABLE",
            diagnostic="The configured quality execution environment is unavailable",
        )

    @staticmethod
    def _failed(request: QualityCapabilityRequest, message: str) -> QualityExecutionOutput:
        sanitized = message.replace("\x00", "")
        lowered = sanitized.lower()
        if any(marker in lowered for marker in ("api_key=", "api-key=", "token=", "password=", "secret=")):
            sanitized = "Quality execution failed; sensitive diagnostic was suppressed"
        return QualityExecutionOutput(
            request=request,
            capability=request.capability,
            status=QualityCapabilityStatus.FAILED,
            image=request.execution_environment_ref,
            command=(),
            tool_id=request.tool_id,
            tool_version=request.tool_version,
            duration_ms=0,
            exit_code=7,
            native_result_content=None,
            driver_result_content=None,
            normalized=None,
            stdout="",
            stderr="",
            diagnostic_code="QUALITY_EXECUTION_FAILED",
            diagnostic=(sanitized[:500] or "Quality execution failed"),
        )
