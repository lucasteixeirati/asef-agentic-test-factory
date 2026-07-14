from __future__ import annotations

import hashlib
import shutil
from pathlib import Path, PurePosixPath

from ..application.ports import OracleWorkspaceResult, ResolvedQualityContext


class IsolatedOracleWorkspaceAdapter:
    """Materialize a curated oracle only after generation has finished."""

    oracle_destination = "tests_generated/test_oracle.py"

    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root.resolve(strict=True)

    def stage_oracle(
        self,
        run_dir: Path,
        context: ResolvedQualityContext,
        oracle_ref: str,
    ) -> OracleWorkspaceResult:
        oracle_source = self._repository_file(oracle_ref)
        authorized_root = context.authorized_root.resolve(strict=True)
        if oracle_source.is_relative_to(authorized_root):
            raise ValueError("oracle must remain outside the generation-authorized SUT root")

        workspace = run_dir / "oracle-workspace"
        workspace.mkdir(parents=True, exist_ok=False)
        copied: list[str] = []
        source_hashes: dict[Path, str] = {}
        for relative in context.authorized_files:
            source = (authorized_root / PurePosixPath(relative)).resolve(strict=True)
            if not source.is_relative_to(authorized_root):
                raise ValueError("authorized source escapes repository root")
            source_hashes[source] = self._sha256(source)
            destination = workspace / PurePosixPath(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            if self._sha256(destination) != source_hashes[source]:
                raise RuntimeError(f"oracle workspace copy hash mismatch: {relative}")
            copied.append(relative)

        oracle_hash = self._sha256(oracle_source)
        destination = workspace / self.oracle_destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(oracle_source, destination)
        if self._sha256(destination) != oracle_hash:
            raise RuntimeError("oracle workspace copy hash mismatch")
        for source, before in source_hashes.items():
            if self._sha256(source) != before:
                raise RuntimeError(f"source changed while staging oracle workspace: {source.name}")
        return OracleWorkspaceResult(
            workspace=workspace,
            copied_files=tuple(copied),
            oracle_file=self.oracle_destination,
            oracle_sha256=oracle_hash,
        )

    def _repository_file(self, relative: str) -> Path:
        if not relative or "\\" in relative:
            raise ValueError("oracle_ref must be a non-empty POSIX path")
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("oracle_ref must remain inside the repository")
        resolved = (self.repository_root / path).resolve(strict=True)
        if not resolved.is_relative_to(self.repository_root) or not resolved.is_file():
            raise ValueError("oracle_ref must identify a repository file")
        return resolved

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
