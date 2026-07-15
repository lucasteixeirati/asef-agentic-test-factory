from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ..contracts import ContractValidationError
from ..smoke_contracts import SmokeCaseResult, SmokeSuiteReport


_SUITE_ID = re.compile(r"^smoke-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")


class SmokeReportStore:
    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def validate_output_root(self, output_root: str | Path) -> Path:
        path = Path(output_root)
        candidate = (self.workspace_root / path).resolve() if not path.is_absolute() else path.resolve()
        allowed = (self.workspace_root / ".asef").resolve()
        if not candidate.is_relative_to(allowed):
            raise ContractValidationError("smoke output must remain under the workspace .asef directory")
        return candidate

    def create_suite(self, output_root: str | Path) -> tuple[str, Path]:
        root = self.validate_output_root(output_root)
        suite_id = f"smoke-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
        suite_dir = root / suite_id
        suite_dir.mkdir(parents=True, exist_ok=False)
        return suite_id, suite_dir

    def save_case_result(self, suite_dir: Path, result: SmokeCaseResult) -> Path:
        result.validate()
        relative = Path("results") / f"repetition-{result.repetition:03d}" / f"{result.case_id}.json"
        path = self._inside_suite(suite_dir, relative)
        self._write_json_once(path, result.to_dict())
        return path

    def save_suite(self, suite_dir: Path, report: SmokeSuiteReport) -> tuple[Path, Path]:
        report.validate()
        json_path = self._inside_suite(suite_dir, Path("suite.json"))
        markdown_path = self._inside_suite(suite_dir, Path("suite.md"))
        self._write_json_once(json_path, report.to_dict())
        self._write_text_once(markdown_path, self._markdown(report))
        return json_path, markdown_path

    def relative_to_workspace(self, path: Path) -> str:
        resolved = path.resolve()
        if not resolved.is_relative_to(self.workspace_root):
            raise ContractValidationError("smoke path escapes the workspace")
        return resolved.relative_to(self.workspace_root).as_posix()

    def _inside_suite(self, suite_dir: Path, relative: Path) -> Path:
        resolved_suite = suite_dir.resolve()
        if not _SUITE_ID.fullmatch(resolved_suite.name):
            raise ContractValidationError("invalid smoke suite directory identity")
        if not resolved_suite.is_relative_to((self.workspace_root / ".asef").resolve()):
            raise ContractValidationError("smoke suite directory escapes workspace .asef")
        candidate = (resolved_suite / relative).resolve()
        if not candidate.is_relative_to(resolved_suite):
            raise ContractValidationError("smoke report path escapes its suite")
        return candidate

    @staticmethod
    def _write_json_once(path: Path, value: dict[str, object]) -> None:
        content = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        SmokeReportStore._write_text_once(path, content)

    @staticmethod
    def _write_text_once(path: Path, content: str) -> None:
        if path.exists():
            raise FileExistsError(f"smoke report already exists: {path.name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError as exc:
                raise FileExistsError(f"smoke report already exists: {path.name}") from exc
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _markdown(report: SmokeSuiteReport) -> str:
        lines = [
            "# ASEF Smoke Suite",
            "",
            f"- Suite: `{_inline(report.suite_id)}`",
            f"- ASEF: `{_inline(report.asef_version)}`",
            f"- Dataset SHA-256: `{report.dataset_hash}`",
            f"- Repetições: {report.repeat}",
            f"- Total: {report.total}",
            f"- Matched: {report.matched}",
            f"- Mismatched: {report.mismatched}",
            f"- Runner errors: {report.runner_errors}",
            "",
            "| Repetição | Caso | Comparação | Status | Classificação | Ação |",
            "|---:|---|---|---|---|---|",
        ]
        for result in report.results:
            actual = result.actual
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(result.repetition),
                        _cell(result.case_id),
                        _cell(result.comparison.value),
                        _cell(actual.status.value if actual else "-") ,
                        _cell(actual.classification.value if actual else "-"),
                        _cell(actual.action.value if actual else "-"),
                    )
                )
                + " |"
            )
        lines.extend(("", "## Limitações", ""))
        lines.extend(f"- {_inline(item)}" for item in report.limitations)
        return "\n".join(lines) + "\n"


def _inline(value: str) -> str:
    return " ".join(value.replace("`", "'").replace("|", "/").split())


def _cell(value: str) -> str:
    return _inline(value)
