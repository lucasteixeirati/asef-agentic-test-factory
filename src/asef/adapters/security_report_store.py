from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ..contracts import ContractValidationError, EvidenceRef
from ..security_contracts import SecurityCaseResult, SecuritySuiteReport


_SUITE_ID = re.compile(r"^security-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")


class SecurityReportStore:
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
            raise ContractValidationError("security output must remain below .asef")
        return candidate

    def create_suite(self, output_root: str | Path) -> tuple[str, Path]:
        root = self.validate_output_root(output_root)
        suite_id = f"security-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
        suite_dir = root / suite_id
        suite_dir.mkdir(parents=True, exist_ok=False)
        return suite_id, suite_dir

    def save_evidence(
        self, suite_dir: Path, case_id: str, facts: dict[str, object]
    ) -> EvidenceRef:
        path = self._inside_suite(suite_dir, Path("evidence") / case_id / "facts.json")
        self._write_json_once(path, {"schema_version": "1.0.0", "facts": facts})
        return EvidenceRef(
            "security-facts",
            path.relative_to(suite_dir).as_posix(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )

    def save_case_result(self, suite_dir: Path, result: SecurityCaseResult) -> Path:
        result.validate()
        path = self._inside_suite(
            suite_dir, Path("results") / f"{result.case_id}.json"
        )
        self._write_json_once(path, result.to_dict())
        return path

    def save_suite(
        self, suite_dir: Path, report: SecuritySuiteReport
    ) -> tuple[Path, Path]:
        report.validate()
        json_path = self._inside_suite(suite_dir, Path("suite.json"))
        md_path = self._inside_suite(suite_dir, Path("suite.md"))
        self._write_json_once(json_path, report.to_dict())
        self._write_text_once(md_path, self._markdown(report))
        return json_path, md_path

    def _inside_suite(self, suite_dir: Path, relative: Path) -> Path:
        suite = suite_dir.resolve()
        if not _SUITE_ID.fullmatch(suite.name):
            raise ContractValidationError("invalid security suite identity")
        if not suite.is_relative_to((self.workspace_root / ".asef").resolve()):
            raise ContractValidationError("security suite escapes .asef")
        candidate = (suite / relative).resolve()
        if not candidate.is_relative_to(suite):
            raise ContractValidationError("security report path escapes suite")
        return candidate

    @staticmethod
    def _write_json_once(path: Path, value: dict[str, object]) -> None:
        SecurityReportStore._write_text_once(
            path,
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )

    @staticmethod
    def _write_text_once(path: Path, content: str) -> None:
        if path.exists():
            raise FileExistsError(f"security report already exists: {path.name}")
        path.parent.mkdir(parents=True, exist_ok=True)
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
    def _markdown(report: SecuritySuiteReport) -> str:
        lines = [
            "# ASEF Security Suite",
            "",
            f"- Suite: `{report.suite_id}`",
            f"- Dataset SHA-256: `{report.dataset_hash}`",
            f"- Total: {len(report.results)}",
            f"- Passed: {report.passed}",
            f"- Failed: {report.failed}",
            f"- Errors: {report.errors}",
            f"- Unsupported: {report.unsupported}",
            f"- Accepted: `{report.accepted}`",
            "",
            "| Caso | Status | Classificação | Diagnóstico |",
            "|---|---|---|---|",
        ]
        for result in report.results:
            diagnostic = result.diagnostic_code or "-"
            lines.append(
                f"| {result.case_id} | {result.status.value} | "
                f"{result.classification.value} | {diagnostic} |"
            )
        lines.extend(("", "## Limitações", ""))
        lines.extend(f"- {item}" for item in report.limitations)
        return "\n".join(lines) + "\n"
