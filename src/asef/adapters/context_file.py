from __future__ import annotations

from pathlib import Path

from ..application.ports import ResolvedQualityContext
from ..context import ContextValidationError, QualityContext
from ..contracts import SkeletonRunRequest


class FileQualityContextAdapter:
    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def resolve(self, request: SkeletonRunRequest) -> ResolvedQualityContext:
        context_path = self._inside_workspace(Path(request.context_ref))
        if not context_path.is_file():
            raise ContextValidationError(f"context file does not exist: {request.context_ref}")
        context = QualityContext.load(context_path)
        snapshot = context.snapshot_for(request)
        repositories = {item["id"]: item for item in context.data["repositories"]}
        repository = repositories[snapshot.repository_id]
        repository_ref = str(repository.get("repository_ref", ""))
        if not repository_ref.startswith("workspace:"):
            raise ContextValidationError("walking skeleton requires a workspace repository_ref")
        authorized_root = self._inside_workspace(Path(repository_ref.removeprefix("workspace:")))
        if not authorized_root.is_dir():
            raise ContextValidationError(f"authorized repository does not exist: {repository_ref}")
        authorized_files = tuple(snapshot.read_scopes)
        for relative in authorized_files:
            if any(marker in relative for marker in ("*", "?", "[")):
                raise ContextValidationError("walking skeleton read scopes must name concrete files")
            candidate = (authorized_root / relative).resolve()
            if not candidate.is_relative_to(authorized_root) or not candidate.is_file():
                raise ContextValidationError(f"authorized file does not exist: {relative}")
        return ResolvedQualityContext(snapshot, authorized_root, authorized_files)

    def _inside_workspace(self, path: Path) -> Path:
        candidate = (self.workspace_root / path).resolve() if not path.is_absolute() else path.resolve()
        if not candidate.is_relative_to(self.workspace_root):
            raise ContextValidationError("path escapes the ASEF workspace")
        return candidate
