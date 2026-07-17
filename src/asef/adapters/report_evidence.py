from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path, PurePosixPath

from ..contracts import ContractValidationError, EvidenceRef, SkeletonRunState
from ..report_contracts import EvidenceIntegrityStatus, ReportEvidence


_PUBLISHABLE_KINDS = {
    "combined_oracle_evaluation",
    "quality_evaluation",
    "quality_report",
}


class _UnsafeEvidenceLink(ValueError):
    pass


class ReportEvidenceVerifier:
    """Verify report references below one run without following reparse points."""

    def verify(self, run_dir: Path, state: SkeletonRunState) -> tuple[ReportEvidence, ...]:
        root = run_dir.resolve(strict=True)
        context_path = run_dir / (state.context_snapshot_ref or "context-snapshot.json")
        if not context_path.is_file():
            raise ContractValidationError("persisted context snapshot is missing")
        refs = [
            EvidenceRef(
                "context_snapshot",
                context_path.relative_to(run_dir).as_posix(),
                self._sha256(context_path),
                "1.0.0",
            ),
            *state.evidence_refs,
        ]
        unique: dict[str, EvidenceRef] = {}
        for ref in refs:
            ref.validate()
            existing = unique.get(ref.relative_path)
            if existing is not None and existing != ref:
                raise ContractValidationError(
                    "duplicate report evidence path has inconsistent metadata"
                )
            unique[ref.relative_path] = ref

        observations: list[ReportEvidence] = []
        for index, ref in enumerate(
            sorted(unique.values(), key=lambda item: item.relative_path), 1
        ):
            try:
                path = self._contained_path(run_dir, root, ref.relative_path)
            except _UnsafeEvidenceLink:
                path = None
                integrity = EvidenceIntegrityStatus.MISMATCH
            else:
                integrity = EvidenceIntegrityStatus.MISSING
            if path is not None:
                integrity = (
                    EvidenceIntegrityStatus.VERIFIED
                    if self._sha256(path) == ref.sha256
                    else EvidenceIntegrityStatus.MISMATCH
                )
            safe_to_publish = (
                integrity is EvidenceIntegrityStatus.VERIFIED
                and ref.kind in _PUBLISHABLE_KINDS
            )
            observations.append(
                ReportEvidence(
                    "EV-CONTEXT" if ref.kind == "context_snapshot" else f"EV-{index:03d}",
                    ref.kind.replace("_", "-"),
                    ref.relative_path,
                    ref.sha256,
                    ref.schema_version,
                    integrity,
                    safe_to_publish,
                    safe_to_publish,
                )
            )
        if len({item.evidence_id for item in observations}) != len(observations):
            raise ContractValidationError("report evidence identities are not unique")
        return tuple(observations)

    @staticmethod
    def _contained_path(run_dir: Path, root: Path, relative_path: str) -> Path | None:
        relative = PurePosixPath(relative_path)
        if (
            not relative_path
            or "\\" in relative_path
            or relative.is_absolute()
            or relative.as_posix() != relative_path
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise ContractValidationError("report evidence path is not canonical and contained")
        current = run_dir
        for part in relative.parts:
            current = current / part
            if not current.exists():
                return None
            metadata = os.lstat(current)
            attributes = getattr(metadata, "st_file_attributes", 0)
            reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            if stat.S_ISLNK(metadata.st_mode) or (reparse and attributes & reparse):
                raise _UnsafeEvidenceLink(
                    "report evidence cannot traverse a link or junction"
                )
        resolved = current.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise _UnsafeEvidenceLink("report evidence escapes the run directory")
        if not resolved.is_file():
            raise ContractValidationError("report evidence must reference a regular file")
        return resolved

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
