from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..contracts import ContextSnapshot, EvidenceRef, NormalizedExecutionResult, SkeletonRunState
from .ports import OracleWorkspacePort, OracleWorkspaceResult, ResolvedQualityContext, RunStorePort, TestExecutionPort


@dataclass(slots=True, frozen=True)
class OracleExecutionResult:
    workspace: OracleWorkspaceResult
    execution: NormalizedExecutionResult
    evidence_refs: tuple[EvidenceRef, EvidenceRef]


class ExecuteOracleService:
    def __init__(
        self,
        workspace: OracleWorkspacePort,
        executor: TestExecutionPort,
        run_store: RunStorePort,
    ) -> None:
        self.workspace = workspace
        self.executor = executor
        self.run_store = run_store

    def execute(
        self,
        state: SkeletonRunState,
        run_dir: Path,
        context: ResolvedQualityContext,
        snapshot: ContextSnapshot,
        oracle_ref: str,
        attempt: int,
    ) -> OracleExecutionResult:
        staged = self.workspace.stage_oracle(run_dir, context, oracle_ref)
        oracle_path = staged.workspace / staged.oracle_file
        evidence_refs = self.run_store.save_oracle_evidence(
            state,
            oracle_ref,
            oracle_path.read_bytes(),
            staged.oracle_sha256,
        )
        state.evidence_refs.extend(evidence_refs)
        state.facts["oracle"] = {
            "oracle_ref": oracle_ref,
            "sha256": staged.oracle_sha256,
            "prompt_isolated": True,
        }
        raw = self.executor.execute(staged.workspace, snapshot)
        execution = self.run_store.save_attempt_execution(state, raw, attempt, "oracle")
        return OracleExecutionResult(staged, execution, evidence_refs)
