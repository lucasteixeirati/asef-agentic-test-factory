from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "1.0.0"
EXPECTED_INVENTORY_REVISION = "1.5.0"
EXPECTED_EXTERNAL_PROTOCOL_VERSION = "1.0.1"
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
EXPECTED_RELEASE_VERSION = "0.1.0a7"
EXPECTED_RELEASE_TAG = "v0.1.0a7"
EXPECTED_PREFLIGHT_ID = "ASEF-PF-20260718-A7"
EXPECTED_TAGGED_COMMIT = "79fbeb0dbbef39799801b86cebd59f8b55edaa0a"
EXPECTED_IMPLEMENTATION_COMMIT = "58ea802bdc912f906e9cffcf7646424e8c66e6ed"
EXPECTED_FINAL_COMMIT = "2e7655eb51876ff0bff8fdbd87442dc812c53077"
EXPECTED_FINAL_CI = 29654457005
EXPECTED_ASSETS = {
    "wheel": (
        "asef_agentic_test_factory-0.1.0a7-py3-none-any.whl",
        167638,
        "sha256:f492e1ca693a307991d805f91bf5283d89c1867e52121e7eb26ed13a1c06f9ad",
    ),
    "sdist": (
        "asef_agentic_test_factory-0.1.0a7.tar.gz",
        536458,
        "sha256:d6b111b7b07f8029a703f4ae59e8a628406e5fe149a1cb6617937608eefa55af",
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
            self._check_internal_evaluation(payload.get("internal_evaluation"))
            self._check_criteria(payload.get("criteria"))
            self._check_decision(
                payload.get("decision"),
                payload.get("criteria"),
                payload.get("external_evaluation"),
                payload.get("internal_evaluation"),
                payload.get("phase"),
            )
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
        if payload.get("inventory_revision") != EXPECTED_INVENTORY_REVISION:
            self._add(
                "INVENTORY_REVISION",
                "inventory_revision",
                f"expected {EXPECTED_INVENTORY_REVISION}",
            )
        if payload.get("gate_id") != "G5":
            self._add("GATE_ID", "gate_id", "expected G5")
        if payload.get("phase") not in {
            "INVENTORY",
            "PREFLIGHT_READY",
            "INTERNAL_EVALUATED",
            "EXTERNAL_EVALUATED",
            "FINAL",
        }:
            self._add("PHASE", "phase", "unexpected Gate 5 evidence phase")

    def _check_release(self, release: object) -> None:
        if not isinstance(release, dict):
            self._add("RELEASE_TYPE", "release", "must be an object")
            return
        if (
            release.get("version") != EXPECTED_RELEASE_VERSION
            or release.get("tag") != EXPECTED_RELEASE_TAG
        ):
            self._add("RELEASE_IDENTITY", "release", f"expected frozen release {EXPECTED_RELEASE_TAG}")
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
        final_ci_found = False
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
            if identifier == EXPECTED_FINAL_CI and run.get("head_sha") == EXPECTED_FINAL_COMMIT:
                final_ci_found = True
            if run.get("conclusion") != "success":
                self._add("CI_CONCLUSION", f"{path}.conclusion", str(run.get("conclusion")))
            if not _COMMIT.fullmatch(str(run.get("head_sha", ""))):
                self._add("CI_HEAD_SHA", f"{path}.head_sha", "expected full lowercase SHA")
            jobs = run.get("jobs")
            if not isinstance(jobs, list) or set(jobs) != EXPECTED_JOBS or len(jobs) != len(EXPECTED_JOBS):
                self._add("CI_JOBS", f"{path}.jobs", "expected the seven canonical jobs exactly once")
            if not str(run.get("url", "")).startswith("https://github.com/"):
                self._add("CI_URL", f"{path}.url", "expected GitHub HTTPS URL")
        if not final_ci_found:
            self._add("FINAL_CI", "ci_runs", "final candidate CI/commit pair is missing")

    def _check_protocol(self, external: object) -> None:
        if not isinstance(external, dict):
            self._add("EXTERNAL_TYPE", "external_evaluation", "must be an object")
            return
        status = external.get("status")
        if status not in {"NOT_STARTED", "READY_FOR_SESSION", "COMPLETED", "BLOCKED", "DEFERRED"}:
            self._add("EXTERNAL_STATUS", "external_evaluation.status", str(status))
        results = external.get("results")
        if not isinstance(results, list):
            self._add("EXTERNAL_RESULTS", "external_evaluation.results", "must be an array")
        elif status in {"NOT_STARTED", "READY_FOR_SESSION", "DEFERRED"} and results:
            self._add("EXTERNAL_RESULTS", "external_evaluation.results", "must be empty before a session")
        elif status == "COMPLETED" and not results:
            self._add("EXTERNAL_RESULTS", "external_evaluation.results", "completed session requires a result")
        elif status in {"COMPLETED", "BLOCKED"}:
            for index, relative in enumerate(results):
                path = f"external_evaluation.results[{index}]"
                resolved = self._safe_file(relative, path)
                if resolved is None:
                    continue
                try:
                    result_payload = json.loads(resolved.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    self._add("EXTERNAL_RESULT_UNREADABLE", path, type(exc).__name__)
                    continue
                self.findings.extend(validate_external_result_payload(result_payload))
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
            if field == "protocol":
                frozen_tokens = (
                    f"**Versão:** `{EXPECTED_EXTERNAL_PROTOCOL_VERSION}`",
                    EXPECTED_RELEASE_TAG,
                    EXPECTED_TAGGED_COMMIT,
                    EXPECTED_ASSETS["wheel"][2].removeprefix("sha256:"),
                    EXPECTED_ASSETS["sdist"][2].removeprefix("sha256:"),
                )
                for token in frozen_tokens:
                    if token not in text:
                        self._add("EXTERNAL_PROTOCOL_FROZEN", path, f"missing {token}")
        if external.get("protocol_version") != EXPECTED_EXTERNAL_PROTOCOL_VERSION:
            self._add(
                "EXTERNAL_PROTOCOL_VERSION",
                "external_evaluation.protocol_version",
                f"expected {EXPECTED_EXTERNAL_PROTOCOL_VERSION}",
            )
        self._check_preflight(external.get("preflight"))

    def _check_internal_evaluation(self, internal: object) -> None:
        if not isinstance(internal, dict):
            self._add("INTERNAL_TYPE", "internal_evaluation", "must be an object")
            return
        status = internal.get("status")
        if status not in {"READY_FOR_SESSION", "IN_PROGRESS", "COMPLETED", "BLOCKED"}:
            self._add("INTERNAL_STATUS", "internal_evaluation.status", str(status))
        if internal.get("participant_id") != "I01":
            self._add("INTERNAL_PARTICIPANT", "internal_evaluation.participant_id", "expected I01")
        if internal.get("participant_role") != "AUTHOR_MAINTAINER":
            self._add("INTERNAL_ROLE", "internal_evaluation.participant_role", "must disclose author role")
        if internal.get("consent_obtained") is not True:
            self._add("INTERNAL_CONSENT", "internal_evaluation.consent_obtained", "must be true")
        if internal.get("channel") != "DEVELOPMENT_CHAT":
            self._add("INTERNAL_CHANNEL", "internal_evaluation.channel", "unexpected channel")
        results = internal.get("results")
        if not isinstance(results, list):
            self._add("INTERNAL_RESULTS", "internal_evaluation.results", "must be an array")
        elif status in {"READY_FOR_SESSION", "IN_PROGRESS"} and results:
            self._add("INTERNAL_RESULTS", "internal_evaluation.results", "must be empty before completion")
        elif status == "COMPLETED" and not results:
            self._add("INTERNAL_RESULTS", "internal_evaluation.results", "completed session requires a result")
        elif status == "COMPLETED":
            for index, relative in enumerate(results):
                path = f"internal_evaluation.results[{index}]"
                result_file = self._safe_file(relative, path)
                if result_file is None:
                    continue
                try:
                    result_payload = json.loads(result_file.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    self._add("INTERNAL_RESULT_UNREADABLE", path, type(exc).__name__)
                    continue
                self.findings.extend(validate_internal_result_payload(result_payload))
        resolved = self._safe_file(internal.get("protocol"), "internal_evaluation.protocol")
        if resolved is None:
            return
        try:
            text = resolved.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            self._add("INTERNAL_PROTOCOL_UNREADABLE", "internal_evaluation.protocol", type(exc).__name__)
            return
        for heading in (
            "## Natureza e limite da evidência",
            "## Consentimento e canal",
            "## Escopo congelado",
            "## Regras do facilitador",
            "## Uso no Gate 5",
        ):
            if heading not in text:
                self._add("INTERNAL_HEADING", "internal_evaluation.protocol", heading)
        for token in (EXPECTED_RELEASE_TAG, EXPECTED_TAGGED_COMMIT, "INFORMATIVE_INTERNAL"):
            if token not in text:
                self._add("INTERNAL_PROTOCOL_FROZEN", "internal_evaluation.protocol", f"missing {token}")
        if status == "COMPLETED":
            self._safe_file(internal.get("summary"), "internal_evaluation.summary")

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
        if payload.get("postflight_id", payload.get("preflight_id")) != EXPECTED_PREFLIGHT_ID:
            self._add("PREFLIGHT_ID", "preflight.preflight_id", "unexpected identifier")
        status = payload.get("status")
        readiness = payload.get("readiness")
        if status not in {"READY", "BLOCKED"}:
            self._add("PREFLIGHT_STATUS", "preflight.status", str(status))
        if readiness not in {"READY", "NOT_READY"}:
            self._add("PREFLIGHT_READINESS", "preflight.readiness", str(readiness))
        target = payload.get("target_release")
        if not isinstance(target, dict) or target.get("tag") != EXPECTED_RELEASE_TAG:
            self._add("PREFLIGHT_RELEASE", "preflight.target_release", f"expected {EXPECTED_RELEASE_TAG}")
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
            if journey.get("installed_version") != EXPECTED_RELEASE_VERSION:
                self._add(
                    "PREFLIGHT_INSTALLED_VERSION",
                    "preflight.installed_journey",
                    f"expected {EXPECTED_RELEASE_VERSION}",
                )
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

    def _check_decision(
        self,
        decision: object,
        criteria: object,
        external: object,
        internal: object,
        phase: object,
    ) -> None:
        if not isinstance(decision, dict):
            self._add("DECISION_TYPE", "decision", "must be an object")
            return
        status = decision.get("status")
        if status not in {"PENDING_HUMAN", "APPROVED_WITH_CONDITIONS", "REJECTED_BLOCKED"}:
            self._add("DECISION_STATUS", "decision.status", "unexpected human decision state")
        recommendation = decision.get("technical_recommendation")
        if phase != "FINAL" and recommendation != "NOT_READY":
            self._add("DECISION_RECOMMENDATION", "decision.technical_recommendation", "must remain NOT_READY before FINAL")
        if phase == "FINAL" and recommendation not in {"APPROVE_WITH_CONDITIONS", "REJECT_BLOCK"}:
            self._add("DECISION_RECOMMENDATION", "decision.technical_recommendation", "unexpected FINAL recommendation")
        conditions = decision.get("conditions")
        if recommendation == "APPROVE_WITH_CONDITIONS" and (
            not isinstance(conditions, list)
            or not conditions
            or any(not isinstance(item, str) or not item.strip() for item in conditions)
        ):
            self._add("DECISION_CONDITIONS", "decision.conditions", "non-empty conditions are required")
        if isinstance(criteria, list) and any(
            isinstance(item, dict) and item.get("status") in {"PARTIAL", "BLOCKED", "NOT_MET"}
            for item in criteria
        ) and recommendation in {"APPROVE", "APPROVE_WITH_CONDITIONS"}:
            self._add("DECISION_CONTRADICTION", "decision", "open criteria cannot recommend approval")
        external_status = external.get("status") if isinstance(external, dict) else None
        internal_status = internal.get("status") if isinstance(internal, dict) else None
        if external_status != "COMPLETED" and recommendation == "APPROVE":
            self._add(
                "DECISION_EXTERNAL_CONTRADICTION",
                "decision",
                "unconditional approval requires completed external evaluation",
            )
        if external_status == "DEFERRED" and recommendation == "APPROVE_WITH_CONDITIONS" and internal_status != "COMPLETED":
            self._add(
                "DECISION_INTERNAL_CONTRADICTION",
                "decision",
                "deferred external evaluation requires completed internal evidence for conditional recommendation",
            )
        if status == "APPROVED_WITH_CONDITIONS" and recommendation != "APPROVE_WITH_CONDITIONS":
            self._add("DECISION_STATUS_CONTRADICTION", "decision", "human decision and recommendation diverge")

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
    if payload.get("protocol_version") != EXPECTED_EXTERNAL_PROTOCOL_VERSION:
        add(
            "RESULT_PROTOCOL_VERSION",
            "protocol_version",
            f"expected {EXPECTED_EXTERNAL_PROTOCOL_VERSION}",
        )
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


def validate_internal_result_payload(payload: object) -> tuple[Finding, ...]:
    findings: list[Finding] = []

    def add(code: str, path: str, detail: str) -> None:
        findings.append(Finding(code, path, detail[:300]))

    if not isinstance(payload, dict):
        return (Finding("INTERNAL_RESULT_TYPE", "internal_result", "must be an object"),)
    forbidden = sorted(_forbidden_key_paths(payload, "internal_result"))
    if forbidden:
        add("INTERNAL_RESULT_FORBIDDEN_KEYS", "internal_result", ", ".join(forbidden))
    if payload.get("schema_version") != SCHEMA_VERSION:
        add("INTERNAL_RESULT_SCHEMA", "schema_version", f"expected {SCHEMA_VERSION}")
    if payload.get("protocol_version") != "1.0.0":
        add("INTERNAL_RESULT_PROTOCOL", "protocol_version", "expected 1.0.0")
    if payload.get("result_id") != "ASEF-INT-20260718-I01":
        add("INTERNAL_RESULT_ID", "result_id", "unexpected result identifier")
    if payload.get("participant_id") != "I01" or payload.get("participant_role") != "AUTHOR_MAINTAINER":
        add("INTERNAL_RESULT_PARTICIPANT", "participant_id", "author role must remain explicit")
    if payload.get("consent_obtained") is not True:
        add("INTERNAL_RESULT_CONSENT", "consent_obtained", "must be true")
    if payload.get("session_status") != "INFORMATIVE_INTERNAL":
        add("INTERNAL_RESULT_STATUS", "session_status", "must be INFORMATIVE_INTERNAL")
    release = payload.get("release")
    if not isinstance(release, dict) or (
        release.get("tag") != EXPECTED_RELEASE_TAG
        or release.get("commit") != EXPECTED_TAGGED_COMMIT
        or release.get("wheel_digest_verified") is not True
        or release.get("sdist_digest_verified") is not True
    ):
        add("INTERNAL_RESULT_RELEASE", "release", "frozen a7 identity/digests are required")
    independence = payload.get("independence")
    if not isinstance(independence, dict) or (
        independence.get("external_to_authoring") is not False
        or independence.get("unaided") is not False
        or independence.get("external_feedback_deferred") is not True
    ):
        add("INTERNAL_RESULT_INDEPENDENCE", "independence", "internal bias must remain explicit")
    assistance = payload.get("ai_assistance")
    if not isinstance(assistance, dict) or assistance.get("used") is not True:
        add("INTERNAL_RESULT_AI", "ai_assistance", "AI assistance must be disclosed")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or tuple(
        item.get("id") for item in tasks if isinstance(item, dict)
    ) != TASK_IDS:
        add("INTERNAL_RESULT_TASK_IDS", "tasks", "expected ordered EXT-01 through EXT-08")
    elif any(
        not isinstance(item, dict)
        or item.get("state") not in TASK_STATES
        or not str(item.get("summary", "")).strip()
        for item in tasks
    ):
        add("INTERNAL_RESULT_TASK", "tasks", "task state and summary are required")
    result_findings = payload.get("findings")
    if not isinstance(result_findings, list):
        add("INTERNAL_RESULT_FINDINGS", "findings", "must be an array")
    else:
        for index, item in enumerate(result_findings):
            if not isinstance(item, dict) or item.get("severity") not in SEVERITIES:
                add("INTERNAL_RESULT_FINDING_SEVERITY", f"findings[{index}]", "invalid severity")
            if not isinstance(item, dict) or item.get("state") not in {
                "OPEN",
                "FIXED",
                "ACCEPTED_RISK",
                "OUT_OF_SCOPE",
            }:
                add("INTERNAL_RESULT_FINDING_STATE", f"findings[{index}]", "invalid state")
    privacy = payload.get("privacy")
    if not isinstance(privacy, dict) or any(value is not True for value in privacy.values()) or not privacy:
        add("INTERNAL_RESULT_PRIVACY", "privacy", "all privacy assertions must be true")
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
