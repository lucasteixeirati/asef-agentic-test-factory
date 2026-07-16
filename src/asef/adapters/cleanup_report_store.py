from __future__ import annotations

import json
import os
import re
from pathlib import Path
from uuid import uuid4

from ..contracts import ContractValidationError
from ..security_contracts import CleanupReport


_CLEANUP_ID = re.compile(r"^cleanup-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")


class CleanupReportStore:
    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.output_root = self.workspace_root / ".asef" / "maintenance" / "cleanup"

    def save(self, report: CleanupReport) -> tuple[Path, Path]:
        report.validate()
        if not _CLEANUP_ID.fullmatch(report.cleanup_id):
            raise ContractValidationError("invalid cleanup identity")
        resolved = self.output_root.resolve()
        if not resolved.is_relative_to((self.workspace_root / ".asef").resolve()):
            raise ContractValidationError("cleanup report root escapes .asef")
        resolved.mkdir(parents=True, exist_ok=True)
        json_path = resolved / f"{report.cleanup_id}.json"
        markdown_path = resolved / f"{report.cleanup_id}.md"
        self._write_once(
            json_path,
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
        )
        self._write_once(markdown_path, self._markdown(report))
        return json_path, markdown_path

    @staticmethod
    def _write_once(path: Path, content: str) -> None:
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _markdown(report: CleanupReport) -> str:
        lines = [
            "# ASEF Cleanup",
            "",
            f"- Cleanup: `{report.cleanup_id}`",
            f"- Retention policy: `{report.policy_id}@{report.policy_version}`",
            f"- Mode: `{report.request.mode.value}`",
            f"- Kind: `{report.request.kind.value}`",
            f"- Older than days: {report.request.older_than_days}",
            f"- Plan SHA-256: `{report.plan_sha256}`",
            f"- Planned: {report.planned}",
            f"- Deleted: {report.deleted}",
            f"- Failed: {report.failed}",
            f"- Skipped: {report.skipped}",
            "",
            "| Target | Status | Reason | Bytes estimados |",
            "|---|---|---|---:|",
        ]
        for target in report.targets:
            lines.append(
                f"| `{_inline(target.target_ref)}` | {target.status.value} | "
                f"{target.reason_code} | {target.bytes_estimate} |"
            )
        lines.extend(
            (
                "",
                "Bytes são estimativas. ASEF não promete secure erase.",
                "",
            )
        )
        return "\n".join(lines)


def _inline(value: str) -> str:
    return (
        value.replace("|", "\\|")
        .replace("`", "\\`")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", " ")
        .replace("\r", " ")
    )
