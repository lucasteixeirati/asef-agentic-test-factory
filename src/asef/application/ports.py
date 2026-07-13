from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..contracts import (
    ContextSnapshot,
    NormalizedExecutionResult,
    SkeletonRunRequest,
    SkeletonRunState,
    TestExecutionOutcome,
    UnitTestArtifact,
)


class InvalidAgentOutputError(ValueError):
    """A provider response was received but violates the typed application contract."""


@dataclass(slots=True, frozen=True)
class ResolvedQualityContext:
    snapshot: ContextSnapshot
    authorized_root: Path
    authorized_files: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class AnalysisResult:
    behaviors: tuple[str, ...]
    risks: tuple[str, ...]
    scenarios: tuple[str, ...]
    clarification_required: bool
    model: str
    response_id: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(slots=True, frozen=True)
class GeneratedArtifactResult:
    artifact: UnitTestArtifact
    model: str
    response_id: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(slots=True, frozen=True)
class WorkspaceResult:
    workspace: Path
    copied_files: tuple[str, ...]
    generated_file: str


@dataclass(slots=True, frozen=True)
class ExecutionOutput:
    image: str
    command: tuple[str, ...]
    exit_code: int
    duration_ms: int
    stdout: str
    stderr: str
    tests: int | None
    passed: int | None
    failed: int | None
    errors: int | None = None
    skipped: int | None = None
    tool_id: str | None = None
    tool_version: str | None = None
    outcome: TestExecutionOutcome = TestExecutionOutcome.UNCLASSIFIED
    raw_result_content: str | None = None
    raw_result_filename: str | None = None
    raw_result_media_type: str | None = None
    timed_out: bool = False
    stdout_truncated: bool = False
    stderr_truncated: bool = False


class QualityContextPort(Protocol):
    def resolve(self, request: SkeletonRunRequest) -> ResolvedQualityContext: ...


class AgenticTestPort(Protocol):
    def analyze(self, request: SkeletonRunRequest) -> AnalysisResult: ...

    def generate(
        self,
        request: SkeletonRunRequest,
        analysis: AnalysisResult,
    ) -> GeneratedArtifactResult: ...


class WorkspacePort(Protocol):
    def stage(
        self,
        run_dir: Path,
        context: ResolvedQualityContext,
        artifact: UnitTestArtifact,
    ) -> WorkspaceResult: ...


class TestExecutionPort(Protocol):
    def execute(self, workspace: Path, snapshot: ContextSnapshot) -> ExecutionOutput: ...


class HumanCheckpointPort(Protocol):
    def pause(self, run_id: str, database: Path, payload: dict[str, object]) -> None: ...

    def resume(self, run_id: str, database: Path, answer: str) -> dict[str, object]: ...

    def cancel(self, run_id: str, database: Path, reason: str) -> dict[str, object]: ...


class RunStorePort(Protocol):
    def save_prepared(
        self,
        state: SkeletonRunState,
        snapshot: ContextSnapshot,
    ) -> Path: ...

    def save_state(self, state: SkeletonRunState) -> None: ...

    def load_state(self, run_id: str) -> SkeletonRunState: ...

    def load_snapshot(self, run_id: str) -> ContextSnapshot: ...

    def save_static_validation(
        self,
        state: SkeletonRunState,
        artifact: UnitTestArtifact,
        validation: dict[str, object],
    ) -> None: ...

    def save_execution(
        self,
        state: SkeletonRunState,
        output: ExecutionOutput,
    ) -> NormalizedExecutionResult: ...

    def save_report(
        self,
        state: SkeletonRunState,
        execution: NormalizedExecutionResult | None,
        evaluation: dict[str, object],
    ) -> str: ...
