from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ..api_contracts import ApiExecutionResult


@dataclass(slots=True, frozen=True)
class ApiReportPaths:
    report_id: str
    report_json: Path
    report_markdown: Path


class ApiReportStore:
    def save(
        self,
        output_root: Path,
        result: ApiExecutionResult,
        *,
        asef_version: str,
        run_id: str | None = None,
        classification: str | None = None,
        generation_mode: str = "supplied-plan",
    ) -> ApiReportPaths:
        output_root.mkdir(parents=True, exist_ok=True)
        report_id = run_id or f"api-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
        report_json = output_root / ("report.json" if run_id else f"{report_id}.json")
        report_markdown = output_root / ("report.md" if run_id else f"{report_id}.md")
        limitations = [
            "This report does not approve an API for production.",
            "The 6.3 slice currently accepts loopback HTTP targets only.",
            "Execution currently uses the bounded host adapter; Docker proof is fixture-only.",
        ]
        payload = {
            "report_schema_version": "1.0.0",
            "report_id": report_id,
            "run_id": run_id,
            "asef_version": asef_version,
            "skill_id": "backend-api",
            "support_level": "experimental-under-development",
            "network_scope": "loopback-only",
            "generation_mode": generation_mode,
            "classification": classification,
            "result": result.to_dict(),
            "limitations": limitations,
        }
        report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rows = "\n".join(
            f"| `{item.scenario_id}` | {item.status} | {item.observed_status if item.observed_status is not None else '—'} | {item.diagnostic_code or '—'} |"
            for item in result.scenarios
        )
        report_markdown.write_text(
            "\n".join(
                (
                    f"# API run `{report_id}`",
                    "",
                    f"- ASEF: `{asef_version}`",
                    f"- Run: `{run_id or 'standalone'}`",
                    "- Skill: `backend-api`",
                    "- Support: `experimental-under-development`",
                    "- Network: `loopback-only`",
                    f"- Plan: `{result.plan_id}`",
                    f"- Generation: `{generation_mode}`",
                    f"- Classification: `{classification or 'not-recorded'}`",
                    f"- Result: `{result.status}` ({result.passed}/{result.tests} passed)",
                    "",
                    "| Scenario | Result | HTTP | Diagnostic |",
                    "|---|---|---:|---|",
                    rows,
                    "",
                    "## Limitations",
                    "",
                    "- This report does not approve an API for production.",
                    "- The 6.3 slice currently accepts loopback HTTP targets only.",
                    "- Execution currently uses the bounded host adapter; Docker proof is fixture-only.",
                    "",
                )
            ),
            encoding="utf-8",
        )
        return ApiReportPaths(report_id, report_json, report_markdown)
