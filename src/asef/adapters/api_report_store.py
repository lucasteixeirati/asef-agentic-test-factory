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
    ) -> ApiReportPaths:
        output_root.mkdir(parents=True, exist_ok=True)
        report_id = f"api-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
        report_json = output_root / f"{report_id}.json"
        report_markdown = output_root / f"{report_id}.md"
        payload = {
            "report_schema_version": "1.0.0",
            "report_id": report_id,
            "asef_version": asef_version,
            "skill_id": "backend-api",
            "support_level": "experimental-under-development",
            "network_scope": "loopback-only",
            "result": result.to_dict(),
            "limitations": [
                "This report does not approve an API for production.",
                "The 6.3 slice currently accepts loopback HTTP targets only.",
                "The plan was supplied as JSON; natural-language generation is not included yet.",
            ],
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
                    "- Skill: `backend-api`",
                    "- Support: `experimental-under-development`",
                    "- Network: `loopback-only`",
                    f"- Plan: `{result.plan_id}`",
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
                    "- Natural-language plan generation is not included yet.",
                    "",
                )
            ),
            encoding="utf-8",
        )
        return ApiReportPaths(report_id, report_json, report_markdown)
