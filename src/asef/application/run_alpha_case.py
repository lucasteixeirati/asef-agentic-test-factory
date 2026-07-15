from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from ..contracts import SkeletonRunRequest, SkeletonRunState, UnitTestArtifact
from ..evaluation_contracts import EvaluationAction
from .alpha_evaluation import AlphaEvaluationCoordinator
from .generate_unit import GenerateUnitTestService
from .ports import ResolvedQualityContext


@dataclass(slots=True, frozen=True)
class AlphaCaseRunResult:
    state: SkeletonRunState
    run_dir: Path
    context: ResolvedQualityContext
    artifact: UnitTestArtifact | None
    attempts_executed: int
    terminal_action: EvaluationAction | None


class RunAlphaCaseService:
    """Compose generation and combined evaluation without duplicating workflow rules."""

    def __init__(
        self,
        generation: GenerateUnitTestService,
        evaluation: AlphaEvaluationCoordinator,
    ) -> None:
        self.generation = generation
        self.evaluation = evaluation

    def execute(
        self,
        request: SkeletonRunRequest,
        oracle_ref: str | None,
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
            )

        workspace = generated.workspace.workspace.resolve()
        run_dir = generated.run_dir.resolve()
        if not workspace.is_relative_to(run_dir):
            raise ValueError("initial Alpha workspace escapes its run directory")
        shutil.rmtree(workspace, ignore_errors=True)
        generated.state.facts["workspace"] = {
            **generated.state.facts.get("workspace", {}),
            "ephemeral_removed_before_evaluation": True,
        }

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
        return AlphaCaseRunResult(
            evaluated.state,
            generated.run_dir,
            generated.context,
            evaluated.artifact,
            evaluated.attempts_executed,
            action,
        )
