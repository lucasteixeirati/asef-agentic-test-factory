from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from ..application.build_alpha_report import BuildAlphaReportService
from ..contracts import ContextSnapshot, SkeletonRunState
from ..report_contracts import REPORT_SCHEMA_VERSION, alpha_run_report_from_dict
from .alpha_report_markdown import AlphaReportMarkdownRenderer
from .report_evidence import ReportEvidenceVerifier


@dataclass(slots=True, frozen=True)
class AlphaReportPaths:
    report_json: str = "report.json"
    report_markdown: str = "report.md"
    schema_version: str = REPORT_SCHEMA_VERSION


class AlphaReportStore:
    def __init__(
        self,
        builder: BuildAlphaReportService | None = None,
        verifier: ReportEvidenceVerifier | None = None,
        renderer: AlphaReportMarkdownRenderer | None = None,
    ) -> None:
        self.builder = builder or BuildAlphaReportService()
        self.verifier = verifier or ReportEvidenceVerifier()
        self.renderer = renderer or AlphaReportMarkdownRenderer()

    def save(
        self,
        run_dir: Path,
        state: SkeletonRunState,
        snapshot: ContextSnapshot,
        evaluation: Mapping[str, object],
    ) -> AlphaReportPaths:
        evidence = self.verifier.verify(run_dir, state)
        report = self.builder.build(state, snapshot, evaluation, evidence)
        payload = report.to_dict()
        markdown = self.renderer.render(report)
        json_content = json.dumps(
            payload, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"

        json_path = run_dir / "report.json"
        markdown_path = run_dir / "report.md"
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest.json must contain an object")
        if "reports" in manifest:
            self._verify_manifest(run_dir, manifest)
        manifest["reports"] = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "json": {
                "relative_path": "report.json",
                "sha256": self._content_sha256(json_content),
            },
            "markdown": {
                "relative_path": "report.md",
                "sha256": self._content_sha256(markdown),
            },
        }
        manifest_content = (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        self._replace_transaction(
            (
                (json_path, json_content),
                (markdown_path, markdown),
                (manifest_path, manifest_content),
            )
        )

        persisted = json.loads(json_path.read_text(encoding="utf-8"))
        alpha_run_report_from_dict(persisted)
        if markdown_path.read_text(encoding="utf-8") != markdown:
            raise OSError("persisted Alpha report Markdown differs from rendered content")
        self._verify_manifest(run_dir, manifest)
        return AlphaReportPaths()

    @staticmethod
    def _verify_manifest(run_dir: Path, manifest: Mapping[str, Any]) -> None:
        reports = manifest.get("reports")
        if not isinstance(reports, Mapping):
            raise ValueError("manifest report references are missing")
        for key in ("json", "markdown"):
            item = reports.get(key)
            if not isinstance(item, Mapping):
                raise ValueError("manifest report reference is invalid")
            relative_path = item.get("relative_path")
            expected_hash = item.get("sha256")
            if relative_path not in {"report.json", "report.md"}:
                raise ValueError("manifest report path is invalid")
            actual = AlphaReportStore._sha256(run_dir / str(relative_path))
            if actual != expected_hash:
                raise OSError("manifest report hash does not reconcile")

    @classmethod
    def _replace_transaction(
        cls, entries: tuple[tuple[Path, str], ...]
    ) -> None:
        temporary: list[tuple[Path, Path]] = []
        previous = {
            path: path.read_bytes() if path.exists() else None for path, _ in entries
        }
        try:
            for path, content in entries:
                candidate = path.with_name(f".tmp-report-{uuid4().hex[:8]}")
                candidate.write_text(content, encoding="utf-8", newline="\n")
                temporary.append((path, candidate))
            for path, candidate in temporary:
                candidate.replace(path)
        except BaseException:
            for path, original in previous.items():
                try:
                    if original is None:
                        path.unlink(missing_ok=True)
                    else:
                        restore = path.with_name(f".tmp-restore-{uuid4().hex[:8]}")
                        restore.write_bytes(original)
                        restore.replace(path)
                except OSError:
                    pass
            raise
        finally:
            for _, candidate in temporary:
                candidate.unlink(missing_ok=True)

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _content_sha256(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
