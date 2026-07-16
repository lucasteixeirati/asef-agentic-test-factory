from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from .security_contracts import FilesystemTargetStatus, inspect_filesystem_target


@dataclass(slots=True, frozen=True)
class EphemeralCleanupObservation:
    role: str
    existed: bool
    removed: bool
    diagnostic_code: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def cleanup_ephemeral_directory(
    root: Path, target: Path, role: str
) -> EphemeralCleanupObservation:
    if not role or len(role) > 64:
        raise ValueError("ephemeral cleanup role is invalid")
    root_absolute = root.absolute()
    target_absolute = target.absolute()
    if not target_absolute.exists() and not target_absolute.is_symlink():
        return EphemeralCleanupObservation(role, False, True, "TARGET_ABSENT")
    safety = inspect_filesystem_target(root_absolute, target_absolute)
    if safety is not FilesystemTargetStatus.SAFE_DIRECTORY:
        return EphemeralCleanupObservation(
            role, True, False, f"TARGET_{safety.value}"
        )
    try:
        shutil.rmtree(target_absolute)
    except OSError:
        return EphemeralCleanupObservation(role, True, False, "CLEANUP_FAILED")
    removed = not target_absolute.exists() and not target_absolute.is_symlink()
    return EphemeralCleanupObservation(
        role,
        True,
        removed,
        "TARGET_REMOVED" if removed else "CLEANUP_RESIDUAL",
    )
