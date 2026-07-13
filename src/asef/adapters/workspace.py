from __future__ import annotations

import hashlib
import shutil
from pathlib import Path, PurePosixPath

from ..application.ports import ResolvedQualityContext, WorkspaceResult
from ..contracts import UnitTestArtifact


class EphemeralWorkspaceAdapter:
    def stage(
        self,
        run_dir: Path,
        context: ResolvedQualityContext,
        artifact: UnitTestArtifact,
    ) -> WorkspaceResult:
        workspace = run_dir / "workspace"
        workspace.mkdir(parents=True, exist_ok=False)
        copied: list[str] = []
        source_hashes: dict[Path, str] = {}
        for relative in context.authorized_files:
            source = (context.authorized_root / relative).resolve(strict=True)
            if not source.is_relative_to(context.authorized_root.resolve(strict=True)):
                raise ValueError("authorized source escapes repository root")
            source_hashes[source] = self._sha256(source)
            destination = workspace / PurePosixPath(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            if self._sha256(destination) != source_hashes[source]:
                raise RuntimeError(f"workspace copy hash mismatch: {relative}")
            copied.append(relative)
        generated = workspace / PurePosixPath(artifact.relative_path)
        generated.parent.mkdir(parents=True, exist_ok=True)
        generated.write_text(artifact.content, encoding="utf-8")
        for source, before in source_hashes.items():
            if self._sha256(source) != before:
                raise RuntimeError(f"source changed while staging workspace: {source.name}")
        return WorkspaceResult(workspace, tuple(copied), artifact.relative_path)

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
