from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..contracts import ContextSnapshot, SkeletonRunRequest, SkeletonRunState


@dataclass(slots=True, frozen=True)
class ResolvedQualityContext:
    snapshot: ContextSnapshot
    authorized_root: Path
    authorized_files: tuple[str, ...]


class QualityContextPort(Protocol):
    def resolve(self, request: SkeletonRunRequest) -> ResolvedQualityContext: ...


class RunStorePort(Protocol):
    def save_prepared(
        self,
        state: SkeletonRunState,
        snapshot: ContextSnapshot,
    ) -> Path: ...
