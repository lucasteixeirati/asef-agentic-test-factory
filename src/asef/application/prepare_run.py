from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from ..contracts import (
    ContextResolution,
    SkeletonRunRequest,
    SkeletonRunState,
    resolve_new_run_context,
)
from ..outcomes import RunStatus
from .ports import QualityContextPort, ResolvedQualityContext, RunStorePort


@dataclass(slots=True, frozen=True)
class PrepareRunResult:
    state: SkeletonRunState
    run_dir: Path
    context: ResolvedQualityContext


class PrepareRunService:
    """Validate and prepare WF-001 until the first agentic boundary."""

    def __init__(self, context_port: QualityContextPort, run_store: RunStorePort) -> None:
        self.context_port = context_port
        self.run_store = run_store

    def execute(self, request: SkeletonRunRequest) -> PrepareRunResult:
        state = SkeletonRunState(request=request)
        self._move(state, RunStatus.VALIDATING_INPUT, "run_received")
        request.validate()
        self._move(state, RunStatus.VALIDATING_CONTEXT, "request_valid")
        self._move(state, RunStatus.RESOLVING_CONTEXT, "context_reference_accepted")

        resolved = self.context_port.resolve(request)
        resolve_new_run_context(state, context_snapshot_ref="context-snapshot.json")

        self._move(state, RunStatus.INSPECTING_SUT, "context_resolved")
        state.facts["sut_manifest"] = {
            "repository_id": resolved.snapshot.repository_id,
            "language_profile": resolved.snapshot.language_profile,
            "authorized_files": list(resolved.authorized_files),
            "inspection": "scope_and_existence_validated",
        }
        self._move(state, RunStatus.ANALYZING_REQUIREMENT, "sut_inspection_complete")
        state.validate()
        run_dir = self.run_store.save_prepared(state, resolved.snapshot)
        return PrepareRunResult(state=state, run_dir=run_dir, context=resolved)

    @staticmethod
    def _move(state: SkeletonRunState, target: RunStatus, reason: str) -> None:
        source = state.status
        state.status = target
        state.record_event(
            "STATE_TRANSITION",
            source=source.value,
            target=target.value,
            reason=reason,
        )
        logging.getLogger("asef.workflow").info(
            "state_transition",
            extra={
                "run_id": state.run_id,
                "operation": reason,
                "component": "workflow",
                "status": target.value,
                "classification": state.classification.value,
            },
        )
