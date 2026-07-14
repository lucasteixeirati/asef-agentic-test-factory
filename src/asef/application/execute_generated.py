from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..contracts import NormalizedExecutionResult, SkeletonRunState, UnitTestArtifact
from .ports import ExecutionOutput, ResolvedQualityContext, RunStorePort, TestExecutionPort, WorkspacePort, WorkspaceResult


@dataclass(slots=True, frozen=True)
class GeneratedAttemptExecution:
    workspace: WorkspaceResult
    raw: ExecutionOutput
    normalized: NormalizedExecutionResult


class ExecuteGeneratedAttemptService:
    def __init__(self, workspace: WorkspacePort, executor: TestExecutionPort, run_store: RunStorePort) -> None:
        self.workspace = workspace
        self.executor = executor
        self.run_store = run_store

    def execute(
        self,
        state: SkeletonRunState,
        run_dir: Path,
        context: ResolvedQualityContext,
        artifact: UnitTestArtifact,
        attempt: int,
    ) -> GeneratedAttemptExecution:
        staged = self.workspace.stage_attempt(run_dir, context, artifact, attempt)
        raw = self.executor.execute(staged.workspace, context.snapshot)
        normalized = self.run_store.save_attempt_execution(state, raw, attempt, "generated")
        return GeneratedAttemptExecution(staged, raw, normalized)
