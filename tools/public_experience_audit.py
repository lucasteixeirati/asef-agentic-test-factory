from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from asef import alpha_run_report_from_dict
from jsonschema import Draft202012Validator


SCHEMA_VERSION = "1.0.0"
MARKDOWN_HEADINGS = (
    "# ASEF Alpha Run Report",
    "## Executive summary",
    "## Status and classification",
    "## Requirement",
    "## Analysis and traceability",
    "## Attempts and functional result",
    "## Oracle and human intervention",
    "## Quality capabilities",
    "## Budgets and usage",
    "## Evidence",
    "## Facts",
    "## Inferences",
    "## Recommendations",
    "## Limitations",
    "## How to interpret this result",
)


@dataclass(slots=True, frozen=True)
class AuditCheck:
    check_id: str
    passed: bool
    detail: str


@dataclass(slots=True, frozen=True)
class PublicExperienceAudit:
    run_id: str
    doctor_status: str
    run_status: str
    classification: str
    report_schema_version: str
    report_json_sha256: str
    report_markdown_sha256: str
    checks: tuple[AuditCheck, ...]
    schema_version: str = SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "passed": self.passed,
            "run_id": self.run_id,
            "doctor_status": self.doctor_status,
            "run_status": self.run_status,
            "classification": self.classification,
            "report_schema_version": self.report_schema_version,
            "report_json_sha256": self.report_json_sha256,
            "report_markdown_sha256": self.report_markdown_sha256,
            "checks": [asdict(item) for item in self.checks],
        }


def audit_public_experience(
    workspace: Path,
    doctor_stdout: Path,
    run_stdout: Path,
) -> PublicExperienceAudit:
    root = workspace.resolve()
    doctor = _read_json_object(doctor_stdout, "doctor stdout")
    cli = _read_json_object(run_stdout, "run stdout")
    checks: list[AuditCheck] = []

    doctor_ok = (
        doctor.get("status") in {"HEALTHY", "DEGRADED"}
        and doctor.get("classification") == "READY"
        and doctor.get("healthy") is True
    )
    checks.append(AuditCheck("doctor-ready", doctor_ok, "doctor must be HEALTHY/DEGRADED and READY"))

    run_id = _text(cli.get("run_id"), "run_id")
    run_dir = _contained(root, _text(cli.get("run_dir"), "run_dir"))
    report_json_path = _contained(root, _text(cli.get("report_json"), "report_json"))
    report_markdown_path = _contained(root, _text(cli.get("report_markdown"), "report_markdown"))
    checks.append(AuditCheck("run-dir-contained", run_dir.is_dir(), "run directory is contained and present"))
    checks.append(
        AuditCheck(
            "cli-terminal",
            cli.get("status") == "SUCCEEDED"
            and cli.get("classification") == "ACCEPTED"
            and cli.get("report_schema_version") == SCHEMA_VERSION,
            "CLI must return SUCCEEDED/ACCEPTED and report schema 1.0.0",
        )
    )

    state = _read_json_object(run_dir / "state.json", "state")
    manifest = _read_json_object(run_dir / "manifest.json", "manifest")
    report_payload = _read_json_object(report_json_path, "Alpha report")
    markdown = report_markdown_path.read_text(encoding="utf-8")
    report = alpha_run_report_from_dict(report_payload)

    checks.append(
        AuditCheck(
            "state-cli-reconcile",
            state.get("run_id") == run_id
            and state.get("status") == cli.get("status")
            and state.get("classification") == cli.get("classification"),
            "state identity and terminal must reconcile with CLI",
        )
    )
    checks.append(
        AuditCheck(
            "report-cli-reconcile",
            report.run_id == run_id
            and report.status.value == cli.get("status")
            and report.classification.value == cli.get("classification")
            and report.schema_version == cli.get("report_schema_version"),
            "report identity and terminal must reconcile with CLI",
        )
    )

    schema_text = files("asef").joinpath("schemas/alpha-run-report.schema.json").read_text(encoding="utf-8")
    schema = json.loads(schema_text, object_pairs_hook=_unique_object)
    Draft202012Validator.check_schema(schema)
    schema_errors = tuple(Draft202012Validator(schema).iter_errors(report_payload))
    schema_ok = (
        not schema_errors
        and
        schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
        and schema.get("additionalProperties") is False
        and schema.get("properties", {}).get("schema_version", {}).get("const") == SCHEMA_VERSION
        and set(schema.get("required", ())) == set(schema.get("properties", {}))
        and set(report_payload) == set(schema.get("required", ()))
    )
    checks.append(
        AuditCheck(
            "packaged-schema-contract",
            schema_ok,
            "packaged Draft 2020-12 schema must validate the report and match the strict runtime contract",
        )
    )

    report_json_hash = _sha256(report_json_path)
    report_markdown_hash = _sha256(report_markdown_path)
    reports = manifest.get("reports") if isinstance(manifest.get("reports"), dict) else {}
    json_ref = reports.get("json") if isinstance(reports.get("json"), dict) else {}
    markdown_ref = reports.get("markdown") if isinstance(reports.get("markdown"), dict) else {}
    manifest_ok = (
        reports.get("schema_version") == SCHEMA_VERSION
        and json_ref == {"relative_path": "report.json", "sha256": report_json_hash}
        and markdown_ref == {"relative_path": "report.md", "sha256": report_markdown_hash}
    )
    checks.append(AuditCheck("manifest-report-hashes", manifest_ok, "manifest report paths and hashes must reconcile"))

    positions = [markdown.find(heading) for heading in MARKDOWN_HEADINGS]
    markdown_ok = all(markdown.count(heading) == 1 for heading in MARKDOWN_HEADINGS)
    markdown_ok = markdown_ok and positions == sorted(positions)
    markdown_ok = markdown_ok and f"- Run: `{run_id}`" in markdown
    markdown_ok = markdown_ok and "- Status: `SUCCEEDED`" in markdown
    markdown_ok = markdown_ok and "- Classification: `ACCEPTED`" in markdown
    checks.append(
        AuditCheck(
            "markdown-parity",
            markdown_ok,
            "all normative sections and terminal identity must appear once in canonical order",
        )
    )

    required_files = (
        "context-snapshot.json",
        "state.json",
        "events.jsonl",
        "manifest.json",
        "report.json",
        "report.md",
    )
    checks.append(
        AuditCheck(
            "run-evidence-present",
            all((run_dir / item).is_file() for item in required_files),
            "snapshot, state, events, manifest and both reports must exist",
        )
    )

    return PublicExperienceAudit(
        run_id=run_id,
        doctor_status=str(doctor.get("status", "UNKNOWN")),
        run_status=str(cli.get("status", "UNKNOWN")),
        classification=str(cli.get("classification", "UNKNOWN")),
        report_schema_version=str(cli.get("report_schema_version", "UNKNOWN")),
        report_json_sha256=report_json_hash,
        report_markdown_sha256=report_markdown_hash,
        checks=tuple(checks),
    )


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{label} is not valid strict JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain an object")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _contained(root: Path, value: str) -> Path:
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("public experience path escapes the workspace") from exc
    if resolved.is_symlink():
        raise ValueError("public experience path cannot be a symlink")
    return resolved


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_audit(output: Path, audit: PublicExperienceAudit) -> None:
    output.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(audit.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (output / "public-experience-audit.json").write_text(json_text, encoding="utf-8", newline="\n")
    lines = [
        "# Public experience audit",
        "",
        f"- Result: `{'PASS' if audit.passed else 'FAIL'}`",
        f"- Doctor: `{audit.doctor_status}`",
        f"- Run: `{audit.run_status}` / `{audit.classification}`",
        f"- Report schema: `{audit.report_schema_version}`",
        "",
        "## Checks",
        "",
    ]
    lines.extend(
        f"- `{'PASS' if item.passed else 'FAIL'}` `{item.check_id}` — {item.detail}"
        for item in audit.checks
    )
    lines.append("")
    (output / "public-experience-audit.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _publish_verified_reports(workspace: Path, run_stdout: Path, output: Path) -> None:
    cli = _read_json_object(run_stdout, "run stdout")
    for field, filename in (("report_json", "report.json"), ("report_markdown", "report.md")):
        source = _contained(workspace, _text(cli.get(field), field))
        (output / filename).write_bytes(source.read_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit an installed ASEF public demo")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--doctor-stdout", type=Path, required=True)
    parser.add_argument("--run-stdout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        workspace = args.workspace.resolve()
        output = _contained(workspace, str(args.output))
        audit = audit_public_experience(workspace, args.doctor_stdout, args.run_stdout)
        _write_audit(output, audit)
        if audit.passed:
            _publish_verified_reports(workspace, args.run_stdout, output)
        print(json.dumps(audit.to_dict(), ensure_ascii=False, sort_keys=True))
        return 0 if audit.passed else 1
    except Exception as exc:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "passed": False, "error": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
