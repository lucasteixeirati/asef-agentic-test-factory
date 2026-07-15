from __future__ import annotations

import json
import os
from pathlib import Path
from typing import NoReturn
from uuid import uuid4

from ..application.alpha_evaluation import AlphaEvaluationCoordinator
from ..application.correct_test import CorrectionLoopController
from ..application.execute_generated import ExecuteGeneratedAttemptService
from ..application.execute_oracle import ExecuteOracleService
from ..application.generate_unit import GenerateUnitTestService
from ..application.prepare_run import PrepareRunService
from ..application.run_alpha_case import AlphaCaseRunResult, RunAlphaCaseService
from ..contracts import ContextSnapshot, SkeletonRunRequest
from ..smoke_contracts import LoadedSmokeCase, SmokeExecutorKind
from ..skills.unit import UnitSkill
from .context_file import FileQualityContextAdapter
from .oracle_workspace import IsolatedOracleWorkspaceAdapter
from .pytest_execution import PytestDockerAdapter
from .recorded_agent import RecordedAgentAdapter
from .run_store import JsonRunStore
from .workspace import EphemeralWorkspaceAdapter


class InjectedDockerUnavailableAdapter:
    def execute(self, workspace: Path, snapshot: ContextSnapshot) -> NoReturn:
        del workspace, snapshot
        raise OSError("declared smoke fault injection: Docker unavailable")


class UnexpectedSmokeExecutionAdapter:
    def execute(self, workspace: Path, snapshot: ContextSnapshot) -> NoReturn:
        del workspace, snapshot
        raise RuntimeError("NOT_REACHED smoke executor was invoked")


class SmokeCheckpointRecorder:
    """Persist a pause request without answering or requiring the optional workflow engine."""

    def __init__(self, allowed_root: Path) -> None:
        self.allowed_root = allowed_root.resolve()

    def pause(self, run_id: str, database: Path, payload: dict[str, object]) -> None:
        target = database.resolve()
        if not target.is_relative_to(self.allowed_root) or not run_id.strip():
            raise ValueError("smoke checkpoint escapes its authorized run root")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        content = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    def resume(self, run_id: str, database: Path, answer: str) -> dict[str, object]:
        del run_id, database, answer
        raise ValueError("smoke checkpoints are evidence-only and cannot be resumed")

    def cancel(self, run_id: str, database: Path, reason: str) -> dict[str, object]:
        del run_id, database, reason
        raise ValueError("smoke checkpoints are evidence-only and cannot be cancelled")


class SmokeCaseExecutorAdapter:
    def __init__(self, workspace_root: Path | None = None, *, timeout_seconds: int = 60) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.timeout_seconds = timeout_seconds

    def execute(
        self,
        loaded: LoadedSmokeCase,
        request: SkeletonRunRequest,
    ) -> AlphaCaseRunResult:
        output_root = self._inside_workspace(Path(request.output_root_ref))
        store = JsonRunStore(output_root)
        workspace = EphemeralWorkspaceAdapter()
        skill = UnitSkill({"reference_sut", "unittest"})
        cassettes = tuple(self._inside_workspace(Path(ref)) for ref in loaded.demo.artifact_cassette_refs)
        agent = RecordedAgentAdapter(
            self._inside_workspace(Path(loaded.demo.analysis_cassette_ref)),
            cassettes[0] if cassettes else None,
            cassettes[1:],
        )
        generation = GenerateUnitTestService(
            PrepareRunService(FileQualityContextAdapter(self.workspace_root), store),
            agent,
            skill,
            workspace,
            store,
            checkpoint=None,
        )
        if loaded.demo.executor is SmokeExecutorKind.INJECTED_DOCKER_UNAVAILABLE:
            executor = InjectedDockerUnavailableAdapter()
        elif loaded.demo.executor is SmokeExecutorKind.NOT_REACHED:
            executor = UnexpectedSmokeExecutionAdapter()
        else:
            executor = PytestDockerAdapter(output_root, timeout_seconds=self.timeout_seconds)
        checkpoint = SmokeCheckpointRecorder(output_root)
        coordinator = AlphaEvaluationCoordinator(
            ExecuteGeneratedAttemptService(workspace, executor, store),
            ExecuteOracleService(
                IsolatedOracleWorkspaceAdapter(self.workspace_root),
                executor,
                store,
            ),
            CorrectionLoopController(agent, skill),
            store,
            checkpoint,
        )
        return RunAlphaCaseService(generation, coordinator).execute(
            request,
            loaded.case.oracle_ref,
        )

    def _inside_workspace(self, path: Path) -> Path:
        candidate = (self.workspace_root / path).resolve() if not path.is_absolute() else path.resolve()
        if not candidate.is_relative_to(self.workspace_root):
            raise ValueError("smoke execution path escapes the workspace")
        return candidate
