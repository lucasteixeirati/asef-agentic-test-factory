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
from ..evaluation_contracts import CorrectionFeedback


class InvalidAgentOutputError(ValueError):
    """A provider response was received but violates the typed application contract."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = "unknown",
        model: str = "unknown",
        response_id: str = "unknown",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        estimated_cost_brl: float = 0.0,
        usage_observed: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.response_id = response_id
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.latency_ms = latency_ms
        self.estimated_cost_brl = estimated_cost_brl
        self.usage_observed = usage_observed


class ProviderError(RuntimeError):
    """Base error normalized at the provider boundary."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.provider = "unknown"
        self.model = "unknown"
        self.response_id = "unknown"
        self.input_tokens = 0
        self.output_tokens = 0
        self.latency_ms = 0
        self.estimated_cost_brl = 0.0
        self.usage_observed = False


class ProviderTransientError(ProviderError):
    """A provider failure that may consume an authorized retry."""


class ProviderPermanentError(ProviderError):
    """A provider failure that must not be retried automatically."""


class ProviderRefusalError(ProviderPermanentError):
    """The provider explicitly refused the requested structured output."""


class ProviderEvidenceError(ProviderPermanentError):
    """The response arrived, but explicitly requested local provider evidence could not persist."""


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
    provider: str = "recorded"
    latency_ms: int = 0
    estimated_cost_brl: float = 0.0


@dataclass(slots=True, frozen=True)
class GeneratedArtifactResult:
    artifact: UnitTestArtifact
    model: str
    response_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = "recorded"
    latency_ms: int = 0
    estimated_cost_brl: float = 0.0


@dataclass(slots=True, frozen=True)
class WorkspaceResult:
    workspace: Path
    copied_files: tuple[str, ...]
    generated_file: str


@dataclass(slots=True, frozen=True)
class OracleWorkspaceResult:
    workspace: Path
    copied_files: tuple[str, ...]
    oracle_file: str
    oracle_sha256: str


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


class TestCorrectionPort(Protocol):
    def correct(
        self,
        request: SkeletonRunRequest,
        previous: UnitTestArtifact,
        feedback: CorrectionFeedback,
    ) -> GeneratedArtifactResult: ...


class WorkspacePort(Protocol):
    def stage(
        self,
        run_dir: Path,
        context: ResolvedQualityContext,
        artifact: UnitTestArtifact,
    ) -> WorkspaceResult: ...

    def stage_attempt(
        self,
        run_dir: Path,
        context: ResolvedQualityContext,
        artifact: UnitTestArtifact,
        attempt: int,
    ) -> WorkspaceResult: ...


class OracleWorkspacePort(Protocol):
    def stage_oracle(
        self,
        run_dir: Path,
        context: ResolvedQualityContext,
        oracle_ref: str,
    ) -> OracleWorkspaceResult: ...


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

    def save_attempt_execution(
        self,
        state: SkeletonRunState,
        output: ExecutionOutput,
        attempt: int,
        role: str,
    ) -> NormalizedExecutionResult: ...

    def save_attempt_evaluation(
        self,
        state: SkeletonRunState,
        evaluation: dict[str, object],
        attempt: int,
    ) -> EvidenceRef: ...

    def save_attempt_artifact(
        self,
        state: SkeletonRunState,
        artifact: UnitTestArtifact,
        metadata: dict[str, object],
    ) -> tuple[EvidenceRef, EvidenceRef]: ...

    def save_oracle_evidence(
        self,
        state: SkeletonRunState,
        oracle_ref: str,
        content: bytes,
        sha256: str,
    ) -> tuple[EvidenceRef, EvidenceRef]: ...

    def save_report(
        self,
        state: SkeletonRunState,
        execution: NormalizedExecutionResult | None,
        evaluation: dict[str, object],
    ) -> str: ...
