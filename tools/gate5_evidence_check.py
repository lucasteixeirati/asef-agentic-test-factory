from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "1.0.0"
EXPECTED_GATE_IDS = tuple(f"G5-{index:02d}" for index in range(1, 21))
EXPECTED_JOBS = {
    "core",
    "framework-spikes",
    "docker-security",
    "alpha-smoke",
    "quality-capabilities",
    "alpha-security",
    "public-experience",
}
EXPECTED_TAGGED_COMMIT = "ddeeb3a0e309a8acdaba14802cbf62649b0d438c"
EXPECTED_IMPLEMENTATION_COMMIT = "9739c1e5e524895eceefd59967abb515a78b7029"
EXPECTED_ASSETS = {
    "wheel": (
        "asef_agentic_test_factory-0.1.0a6-py3-none-any.whl",
        167571,
        "sha256:0b40e6597acb1064c15122a7ac96934e7b1e3f62df64bf5ff1dedcd62831ff72",
    ),
    "sdist": (
        "asef_agentic_test_factory-0.1.0a6.tar.gz",
        497111,
        "sha256:b2963ce50ddcb4bf52080510fdc55656a9ab7cd42ff66ce3008c76fac2f46289",
    ),
}
INITIAL_GATE_STATES = {"MET", "MET_WITH_RESIDUAL_RISK", "PARTIAL", "BLOCKED", "NOT_MET"}
TASK_IDS = tuple(f"EXT-{index:02d}" for index in range(1, 9))
TASK_STATES = {
    "COMPLETED_INDEPENDENTLY",
    "COMPLETED_WITH_RECOVERY",
    "COMPLETED_WITH_INTERVENTION",
    "FAILED",
    "ENVIRONMENT_BLOCKED",
    "NOT_ATTEMPTED",
}
SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
FORBIDDEN_RESULT_KEYS = {
    "name",
    "email",
    "employer",
    "company",
    "username",
    "ip",
    "address",
    "raw_terminal",
    "recording",
}
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_PARTICIPANT = re.compile(r"^P[0-9]{2}$")


@dataclass(slots=True, frozen=True)
class Finding:
    code: str
    path: str
    detail: str


@dataclass(slots=True, frozen=True)
class EvidenceAudit:
    inventory: str
    findings: tuple[Finding, ...]
    checked_criteria: int
    checked_evidence: int
    schema_version: str = SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "passed": self.passed,
            "inventory": self.inventory,
            "checked_criteria": self.checked_criteria,
            "checked_evidence": self.checked_evidence,
            "findings": [asdict(item) for item in self.findings],
        }


class Gate5EvidenceChecker:
    def __init__(self, root: Path, inventory: Path | None = None) -> None:
        self.root = root.resolve()
        self.inventory = inventory or Path("docs/project/gates/gate-05-evidence-inventory.json")
        self.findings: list[Finding] = []
        self.checked_evidence = 0

    def run(self) -> EvidenceAudit:
        payload = self._load_inventory()
        if payload is not None:
            self._check_metadata(payload)
            self._check_release(payload.get("release"))
            self._check_ci(payload.get("ci_runs"))
            self._check_protocol(payload.get("external_evaluation"))
            self._check_criteria(payload.get("criteria"))
            self._check_decision(payload.get("decision"), payload.get("criteria"))
        return EvidenceAudit(
            inventory=self.inventory.as_posix(),
            findings=tuple(sorted(self.findings, key=lambda item: (item.path, item.code, item.detail))),
            checked_criteria=len(payload.get("criteria", [])) if isinstance(payload, dict) else 0,
            checked_evidence=self.checked_evidence,
        )

    def _load_inventory(self) -> dict[str, Any] | None:
        path = self.root / self.inventory
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            self._add("INVENTORY_UNREADABLE", self.inventory.as_posix(), type(exc).__name__)
            return None
        if not isinstance(payload, dict):
            self._add("INVENTORY_TYPE", self.inventory.as_posix(), "root must be an object")
            return None
        return payload

    def _check_metadata(self, payload: dict[str, Any]) -> None:
        if payload.get("schema_version") != SCHEMA_VERSION:
            self._add("SCHEMA_VERSION", "schema_version", f"expected {SCHEMA_VERSION}")
        if payload.get("gate_id") != "G5":
            self._add("GATE_ID", "gate_id", "expected G5")
        if payload.get("phase") != "INVENTORY":
            self._add("PHASE", "phase", "5.9.1 inventory must remain INVENTORY")

    def _check_release(self, release: object) -> None:
        if not isinstance(release, dict):
            self._add("RELEASE_TYPE", "release", "must be an object")
            return
        if release.get("version") != "0.1.0a6" or release.get("tag") != "v0.1.0a6":
            self._add("RELEASE_IDENTITY", "release", "expected frozen release v0.1.0a6")
        if release.get("tagged_commit") != EXPECTED_TAGGED_COMMIT:
            self._add("RELEASE_COMMIT", "release.tagged_commit", "frozen tag commit diverged")
        if release.get("implementation_commit") != EXPECTED_IMPLEMENTATION_COMMIT:
            self._add("IMPLEMENTATION_COMMIT", "release.implementation_commit", "frozen commit diverged")
        assets = release.get("assets")
        if not isinstance(assets, list) or len(assets) != 2:
            self._add("RELEASE_ASSETS", "release.assets", "expected exactly wheel and sdist")
            return
        roles: set[str] = set()
        names: set[str] = set()
        for index, asset in enumerate(assets):
            path = f"release.assets[{index}]"
            if not isinstance(asset, dict):
                self._add("ASSET_TYPE", path, "must be an object")
                continue
            role = asset.get("role")
            name = asset.get("name")
            digest = asset.get("digest")
            size = asset.get("size")
            if role not in {"wheel", "sdist"} or role in roles:
                self._add("ASSET_ROLE", f"{path}.role", str(role))
            roles.add(str(role))
            if not isinstance(name, str) or not name or name in names:
                self._add("ASSET_NAME", f"{path}.name", str(name))
            names.add(str(name))
            if not _SHA256.fullmatch(str(digest)):
                self._add("ASSET_DIGEST", f"{path}.digest", "expected sha256:<64 lowercase hex>")
            if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
                self._add("ASSET_SIZE", f"{path}.size", "expected positive integer")
            if not str(asset.get("url", "")).startswith("https://github.com/"):
                self._add("ASSET_URL", f"{path}.url", "expected GitHub HTTPS URL")
            expected = EXPECTED_ASSETS.get(str(role))
            if expected is not None and (name, size, digest) != expected:
                self._add("ASSET_FROZEN_DIVERGENCE", path, f"expected {expected[0]}")
        if roles != {"wheel", "sdist"}:
            self._add("ASSET_ROLES", "release.assets", "wheel and sdist roles are mandatory")

    def _check_ci(self, runs: object) -> None:
        if not isinstance(runs, list) or not runs:
            self._add("CI_RUNS", "ci_runs", "at least one successful seven-job run is required")
            return
        identifiers: set[int] = set()
        for index, run in enumerate(runs):
            path = f"ci_runs[{index}]"
            if not isinstance(run, dict):
                self._add("CI_RUN_TYPE", path, "must be an object")
                continue
            identifier = run.get("id")
            if not isinstance(identifier, int) or isinstance(identifier, bool) or identifier in identifiers:
                self._add("CI_RUN_ID", f"{path}.id", str(identifier))
            if isinstance(identifier, int):
                identifiers.add(identifier)
            if run.get("conclusion") != "success":
                self._add("CI_CONCLUSION", f"{path}.conclusion", str(run.get("conclusion")))
            if not _COMMIT.fullmatch(str(run.get("head_sha", ""))):
                self._add("CI_HEAD_SHA", f"{path}.head_sha", "expected full lowercase SHA")
            jobs = run.get("jobs")
            if not isinstance(jobs, list) or set(jobs) != EXPECTED_JOBS or len(jobs) != len(EXPECTED_JOBS):
                self._add("CI_JOBS", f"{path}.jobs", "expected the seven canonical jobs exactly once")
            if not str(run.get("url", "")).startswith("https://github.com/"):
                self._add("CI_URL", f"{path}.url", "expected GitHub HTTPS URL")

    def _check_protocol(self, external: object) -> None:
        if not isinstance(external, dict):
            self._add("EXTERNAL_TYPE", "external_evaluation", "must be an object")
            return
        if external.get("status") != "NOT_STARTED":
            self._add("EXTERNAL_STATUS", "external_evaluation.status", "5.9.1 must not claim a session")
        if external.get("results") != []:
            self._add("EXTERNAL_RESULTS", "external_evaluation.results", "must be empty in 5.9.1")
        for field, headings in (
            (
                "protocol",
                ("## Escopo e versão congelada", "## Regras do facilitador", "## Tarefas", "## Rubrica congelada"),
            ),
            (
                "template",
                ("## Controle da sessão", "## Elegibilidade e consentimento", "## Tarefas", "## Findings"),
            ),
            (
                "participant_kit",
                ("## Condição para liberação", "## Material que será entregue", "## Cartões de tarefa"),
            ),
            (
                "facilitator_checklist",
                ("## Antes de recrutar ou agendar", "## Consentimento", "## Antes de publicar"),
            ),
        ):
            relative = external.get(field)
            path = f"external_evaluation.{field}"
            resolved = self._safe_file(relative, path)
            if resolved is None:
                continue
            try:
                text = resolved.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                self._add("EXTERNAL_DOCUMENT_UNREADABLE", path, type(exc).__name__)
                continue
            for heading in headings:
                if heading not in text:
                    self._add("EXTERNAL_HEADING", path, heading)
        self._check_preflight(external.get("preflight"))

    def _check_preflight(self, relative: object) -> None:
        resolved = self._safe_file(relative, "external_evaluation.preflight")
        if resolved is None:
            return
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            self._add("PREFLIGHT_UNREADABLE", "external_evaluation.preflight", type(exc).__name__)
            return
        if not isinstance(payload, dict):
            self._add("PREFLIGHT_TYPE", "external_evaluation.preflight", "must be an object")
            return
        if payload.get("schema_version") != SCHEMA_VERSION:
            self._add("PREFLIGHT_SCHEMA", "preflight.schema_version", f"expected {SCHEMA_VERSION}")
        if payload.get("preflight_id") != "ASEF-PF-20260717-592":
            self._add("PREFLIGHT_ID", "preflight.preflight_id", "unexpected identifier")
        status = payload.get("status")
        readiness = payload.get("readiness")
        if status not in {"READY", "BLOCKED"}:
            self._add("PREFLIGHT_STATUS", "preflight.status", str(status))
        if readiness not in {"READY", "NOT_READY"}:
            self._add("PREFLIGHT_READINESS", "preflight.readiness", str(readiness))
        target = payload.get("target_release")
        if not isinstance(target, dict) or target.get("tag") != "v0.1.0a6":
            self._add("PREFLIGHT_RELEASE", "preflight.target_release", "expected v0.1.0a6")
        elif any(
            target.get(field) is not True
            for field in (
                "assets_downloaded_from_github_release",
                "wheel_digest_verified",
                "sdist_digest_verified",
            )
        ):
            self._add("PREFLIGHT_ASSETS", "preflight.target_release", "all asset assertions must be true")
        journey = payload.get("installed_journey")
        if not isinstance(journey, dict):
            self._add("PREFLIGHT_JOURNEY", "preflight.installed_journey", "must be an object")
        else:
            if journey.get("installed_version") != "0.1.0a6":
                self._add("PREFLIGHT_INSTALLED_VERSION", "preflight.installed_journey", "expected 0.1.0a6")
            for field in (
                "outside_checkout",
                "empty_session_directory",
                "wheel_installed_without_dependencies",
                "pytest_image_built_from_published_sdist",
                "openai_api_key_absent",
            ):
                if journey.get(field) is not True:
                    self._add("PREFLIGHT_JOURNEY_ASSERTION", f"preflight.installed_journey.{field}", "must be true")
            doctor = journey.get("doctor")
            if not isinstance(doctor, dict) or (
                doctor.get("classification") != "READY"
                or doctor.get("status") not in {"HEALTHY", "DEGRADED"}
                or doctor.get("exit_code") != 0
            ):
                self._add("PREFLIGHT_DOCTOR", "preflight.installed_journey.doctor", "doctor must be ready")
            demo = journey.get("demo")
            if not isinstance(demo, dict) or (
                demo.get("status") != "SUCCEEDED"
                or demo.get("classification") != "ACCEPTED"
                or demo.get("exit_code") != 0
            ):
                self._add("PREFLIGHT_DEMO", "preflight.installed_journey.demo", "demo must be accepted")
            audit = journey.get("public_experience_audit")
            if not isinstance(audit, dict) or (
                audit.get("passed") is not True
                or audit.get("passed_checks") != 9
                or audit.get("total_checks") != 9
            ):
                self._add("PREFLIGHT_AUDIT", "preflight.installed_journey.public_experience_audit", "expected 9/9")
            cleanup = journey.get("cleanup")
            if not isinstance(cleanup, dict) or (
                cleanup.get("classification") != "DRY_RUN_COMPLETE"
                or cleanup.get("mode") != "DRY_RUN"
                or cleanup.get("exit_code") != 0
            ):
                self._add("PREFLIGHT_CLEANUP", "preflight.installed_journey.cleanup", "expected dry-run complete")
            if journey.get("secret_scan") != "PASS" or journey.get("managed_containers_after_run") != 0:
                self._add("PREFLIGHT_HYGIENE", "preflight.installed_journey", "scanner/orphan check failed")
        documentation = payload.get("documentation_consistency")
        findings = payload.get("findings")
        documentation_status = documentation.get("status") if isinstance(documentation, dict) else None
        finding_items = findings if isinstance(findings, list) else []
        if status == "READY" and (
            readiness != "READY" or documentation_status != "PASS" or finding_items
        ):
            self._add("PREFLIGHT_READY_CONTRADICTION", "preflight", "READY requires consistent docs and no findings")
        if status == "BLOCKED" and (
            readiness != "NOT_READY" or not finding_items
        ):
            self._add("PREFLIGHT_BLOCKED_CONTRADICTION", "preflight", "BLOCKED requires NOT_READY and findings")
        if documentation_status == "FAIL" and not any(
            isinstance(item, dict)
            and item.get("severity") in {"CRITICAL", "HIGH"}
            and item.get("state") == "OPEN"
            for item in finding_items
        ):
            self._add("PREFLIGHT_DOC_FINDING", "preflight.findings", "failed docs require an open CRITICAL/HIGH finding")

    def _check_criteria(self, criteria: object) -> None:
        if not isinstance(criteria, list):
            self._add("CRITERIA_TYPE", "criteria", "must be an array")
            return
        identifiers = [item.get("id") for item in criteria if isinstance(item, dict)]
        if tuple(identifiers) != EXPECTED_GATE_IDS:
            self._add("CRITERIA_IDS", "criteria", "expected ordered unique G5-01 through G5-20")
        for index, criterion in enumerate(criteria):
            path = f"criteria[{index}]"
            if not isinstance(criterion, dict):
                self._add("CRITERION_TYPE", path, "must be an object")
                continue
            if criterion.get("status") not in INITIAL_GATE_STATES:
                self._add("CRITERION_STATUS", f"{path}.status", str(criterion.get("status")))
            summary = criterion.get("summary")
            if not isinstance(summary, str) or not summary.strip():
                self._add("CRITERION_SUMMARY", f"{path}.summary", "must be non-empty")
            evidence = criterion.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                self._add("CRITERION_EVIDENCE", f"{path}.evidence", "at least one primary path is required")
                continue
            for evidence_index, relative in enumerate(evidence):
                evidence_path = f"{path}.evidence[{evidence_index}]"
                if self._safe_file(relative, evidence_path) is not None:
                    self.checked_evidence += 1

    def _check_decision(self, decision: object, criteria: object) -> None:
        if not isinstance(decision, dict):
            self._add("DECISION_TYPE", "decision", "must be an object")
            return
        if decision.get("status") != "PENDING_HUMAN":
            self._add("DECISION_STATUS", "decision.status", "must remain PENDING_HUMAN in 5.9.1")
        recommendation = decision.get("technical_recommendation")
        if recommendation != "NOT_READY":
            self._add("DECISION_RECOMMENDATION", "decision.technical_recommendation", "must remain NOT_READY")
        if isinstance(criteria, list) and any(
            isinstance(item, dict) and item.get("status") in {"PARTIAL", "BLOCKED", "NOT_MET"}
            for item in criteria
        ) and recommendation in {"APPROVE", "APPROVE_WITH_CONDITIONS"}:
            self._add("DECISION_CONTRADICTION", "decision", "open criteria cannot recommend approval")

    def _safe_file(self, relative: object, path: str) -> Path | None:
        if not isinstance(relative, str) or not relative:
            self._add("EVIDENCE_PATH", path, "must be a non-empty repository-relative path")
            return None
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts or "\\" in relative:
            self._add("EVIDENCE_PATH_UNSAFE", path, relative)
            return None
        resolved = (self.root / pure).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError:
            self._add("EVIDENCE_PATH_OUTSIDE", path, relative)
            return None
        if not resolved.is_file():
            self._add("EVIDENCE_PATH_MISSING", path, relative)
            return None
        return resolved

    def _add(self, code: str, path: str, detail: str) -> None:
        self.findings.append(Finding(code, path, detail[:300]))


def _forbidden_key_paths(value: object, prefix: str = "result") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}"
            if str(key).lower() in FORBIDDEN_RESULT_KEYS:
                found.append(path)
            found.extend(_forbidden_key_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_forbidden_key_paths(child, f"{prefix}[{index}]"))
    return tuple(found)


def validate_external_result_payload(payload: object) -> tuple[Finding, ...]:
    findings: list[Finding] = []

    def add(code: str, path: str, detail: str) -> None:
        findings.append(Finding(code, path, detail[:300]))

    if not isinstance(payload, dict):
        return (Finding("RESULT_TYPE", "result", "must be an object"),)
    forbidden = sorted(_forbidden_key_paths(payload))
    if forbidden:
        add("RESULT_FORBIDDEN_KEYS", "result", ", ".join(forbidden))
    if payload.get("schema_version") != SCHEMA_VERSION:
        add("RESULT_SCHEMA_VERSION", "schema_version", f"expected {SCHEMA_VERSION}")
    if payload.get("protocol_version") != "1.0.0":
        add("RESULT_PROTOCOL_VERSION", "protocol_version", "expected 1.0.0")
    if not _PARTICIPANT.fullmatch(str(payload.get("participant_id", ""))):
        add("RESULT_PARTICIPANT", "participant_id", "expected anonymized PNN identifier")
    if payload.get("consent_obtained") is not True:
        add("RESULT_CONSENT", "consent_obtained", "must be true before publication")
    session_status = payload.get("session_status")
    if session_status not in {"VALID", "INFORMATIVE", "ENVIRONMENT_BLOCKED", "WITHDRAWN", "INVALID"}:
        add("RESULT_SESSION_STATUS", "session_status", "invalid status")
    eligibility = payload.get("eligibility")
    if not isinstance(eligibility, dict) or any(
        eligibility.get(field) is not True
        for field in ("qe_experience", "external_to_authoring", "no_individual_briefing")
    ):
        add("RESULT_ELIGIBILITY", "eligibility", "all eligibility assertions must be true")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        add("RESULT_TASKS", "tasks", "must be an array")
    else:
        task_ids = [item.get("id") for item in tasks if isinstance(item, dict)]
        if tuple(task_ids) != TASK_IDS:
            add("RESULT_TASK_IDS", "tasks", "expected ordered unique EXT-01 through EXT-08")
        for index, task in enumerate(tasks):
            if not isinstance(task, dict):
                add("RESULT_TASK_TYPE", f"tasks[{index}]", "must be an object")
                continue
            if task.get("state") not in TASK_STATES:
                add("RESULT_TASK_STATE", f"tasks[{index}].state", str(task.get("state")))
    findings_payload = payload.get("findings")
    if not isinstance(findings_payload, list):
        add("RESULT_FINDINGS", "findings", "must be an array")
    else:
        for index, finding in enumerate(findings_payload):
            if not isinstance(finding, dict) or finding.get("severity") not in SEVERITIES:
                add("RESULT_FINDING_SEVERITY", f"findings[{index}].severity", "invalid severity")
            if not isinstance(finding, dict) or finding.get("state") not in {
                "OPEN",
                "FIXED",
                "ACCEPTED_RISK",
                "OUT_OF_SCOPE",
            }:
                add("RESULT_FINDING_STATE", f"findings[{index}].state", "invalid finding state")
    privacy = payload.get("privacy")
    if not isinstance(privacy, dict) or any(
        privacy.get(field) is not True
        for field in ("pii_removed", "material_raw_not_versioned", "review_or_withdrawal_honored")
    ):
        add("RESULT_PRIVACY", "privacy", "all privacy assertions must be true")
    if session_status == "VALID":
        task_items = tasks if isinstance(tasks, list) else []
        task_map = {
            item.get("id"): item.get("state")
            for item in task_items
            if isinstance(item, dict)
        }
        allowed_central = {"COMPLETED_INDEPENDENTLY", "COMPLETED_WITH_RECOVERY"}
        if any(task_map.get(task_id) not in allowed_central for task_id in TASK_IDS[2:7]):
            add("RESULT_VALIDITY_TASKS", "tasks", "VALID requires EXT-03 through EXT-07 without intervention")
        if payload.get("interpretation_correct") is not True:
            add("RESULT_VALIDITY_INTERPRETATION", "interpretation_correct", "VALID requires true")
        if isinstance(findings_payload, list) and any(
            isinstance(item, dict)
            and item.get("severity") in {"CRITICAL", "HIGH"}
            and item.get("state") == "OPEN"
            for item in findings_payload
        ):
            add("RESULT_VALIDITY_FINDINGS", "findings", "VALID cannot retain open CRITICAL/HIGH findings")
    return tuple(sorted(findings, key=lambda item: (item.path, item.code, item.detail)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the mechanical Gate 5 evidence inventory offline")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("docs/project/gates/gate-05-evidence-inventory.json"),
    )
    args = parser.parse_args(argv)
    audit = Gate5EvidenceChecker(args.root, args.inventory).run()
    print(json.dumps(audit.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if audit.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
