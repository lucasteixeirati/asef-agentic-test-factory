from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..contracts import SkeletonRunRequest, SkeletonRunState, UnitTestArtifact
from ..evaluation_contracts import (
    EvaluationAction,
    QualityCapabilityRequest,
    QualityEvaluationReport,
)
from ..ephemeral_cleanup import cleanup_ephemeral_directory
from ..outcomes import RunClassification, RunStatus
from .alpha_evaluation import AlphaEvaluationCoordinator
from .generate_unit import GenerateUnitTestService
from .ports import ResolvedQualityContext
from .quality_evaluation import QualityEvaluationService


@dataclass(slots=True, frozen=True)
class AlphaCaseRunResult:
    state: SkeletonRunState
    run_dir: Path
    context: ResolvedQualityContext
    artifact: UnitTestArtifact | None
    attempts_executed: int
    terminal_action: EvaluationAction | None
    quality_report: QualityEvaluationReport | None = None


class RunAlphaCaseService:
    """Compose generation and combined evaluation without duplicating workflow rules."""

    def __init__(
        self,
        generation: GenerateUnitTestService,
        evaluation: AlphaEvaluationCoordinator,
        quality: QualityEvaluationService | None = None,
    ) -> None:
        self.generation = generation
        self.evaluation = evaluation
        self.quality = quality

    def execute(
        self,
        request: SkeletonRunRequest,
        oracle_ref: str | None,
        quality_requests: tuple[QualityCapabilityRequest, ...] = (),
    ) -> AlphaCaseRunResult:
        generated = self.generation.execute(request)
        if generated.artifact is None or generated.workspace is None:
            return AlphaCaseRunResult(
                generated.state,
                generated.run_dir,
                generated.context,
                generated.artifact,
                0,
                None,
                None,
            )

        workspace = generated.workspace.workspace.resolve()
        run_dir = generated.run_dir.resolve()
        if not workspace.is_relative_to(run_dir):
            raise ValueError("initial Alpha workspace escapes its run directory")
        cleanup = cleanup_ephemeral_directory(
            run_dir, workspace, "initial-generation-workspace"
        )
        generated.state.facts["workspace"] = {
            **generated.state.facts.get("workspace", {}),
            "ephemeral_removed_before_evaluation": cleanup.removed,
            "cleanup_diagnostic_code": cleanup.diagnostic_code,
        }
        if not cleanup.removed:
            raise OSError("initial generation workspace cleanup failed")

        evaluated = self.evaluation.execute(
            generated.state,
            generated.run_dir,
            generated.context,
            generated.artifact,
            oracle_ref,
        )
        latest = evaluated.state.facts.get("latest_evaluation")
        action = None
        if isinstance(latest, dict) and isinstance(latest.get("action"), str):
            action = EvaluationAction(latest["action"])
        quality_report = None
        if (
            quality_requests
            and evaluated.state.status is RunStatus.SUCCEEDED
            and evaluated.state.classification is RunClassification.ACCEPTED
        ):
            if self.quality is None:
                raise ValueError("quality capabilities were requested but no quality service is configured")
            quality_report = self.quality.execute(
                evaluated.state,
                generated.run_dir,
                generated.context,
                evaluated.artifact,
                quality_requests,
            ).report
        return AlphaCaseRunResult(
            evaluated.state,
            generated.run_dir,
            generated.context,
            evaluated.artifact,
            evaluated.attempts_executed,
            action,
            quality_report,
        )
