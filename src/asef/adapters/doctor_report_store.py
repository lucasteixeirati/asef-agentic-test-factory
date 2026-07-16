from __future__ import annotations

import json
import os
import re
from pathlib import Path
from uuid import uuid4

from ..contracts import ContractValidationError
from ..security_contracts import DoctorReport


_REPORT_ID = re.compile(r"^doctor-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")


class DoctorReportStore:
    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def validate_output_root(self, output_root: str | Path) -> Path:
        path = Path(output_root)
        candidate = (
            (self.workspace_root / path).resolve()
            if not path.is_absolute()
            else path.resolve()
        )
        if not candidate.is_relative_to((self.workspace_root / ".asef").resolve()):
            raise ContractValidationError("doctor output must remain below .asef")
        return candidate

    def save_report(
        self, output_root: str | Path, report: DoctorReport
    ) -> tuple[Path, Path, Path]:
        report.validate()
        if not _REPORT_ID.fullmatch(report.report_id):
            raise ContractValidationError("invalid doctor report identity")
        root = self.validate_output_root(output_root)
        report_dir = root / report.report_id
        report_dir.mkdir(parents=True, exist_ok=False)
        json_path = report_dir / "report.json"
        markdown_path = report_dir / "report.md"
        self._write_once(
            json_path,
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
        )
        self._write_once(markdown_path, self._markdown(report))
        return report_dir, json_path, markdown_path

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
    def _markdown(report: DoctorReport) -> str:
        lines = [
            "# ASEF Doctor",
            "",
            f"- Report: `{report.report_id}`",
            f"- Status: `{report.status.value}`",
            f"- Healthy: `{report.healthy}`",
            f"- Profile: `{report.profile_id}`",
            f"- Mode: `{report.mode}`",
            f"- Environment: `{report.environment}`",
            "",
            "| Check | Status | Diagnóstico | Recomendação |",
            "|---|---|---|---|",
        ]
        for check in report.checks:
            recommendation = check.recommendation.value if check.recommendation else "-"
            lines.append(
                f"| {check.check_id} | {check.status.value} | "
                f"{check.diagnostic_code} | {recommendation} |"
            )
        lines.extend(
            (
                "",
                "O doctor é estritamente diagnóstico: não instala dependências, "
                "não inicia serviços, não faz pull/build e não executa provider.",
                "",
            )
        )
        return "\n".join(lines)
