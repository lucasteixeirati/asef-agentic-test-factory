from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from enum import Enum, StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

from .contracts import ContractValidationError, EvidenceRef


SECURITY_SCHEMA_VERSION = "1.0.0"
SECURITY_CASE_IDS = tuple(f"SEC-{number:03d}" for number in range(1, 13))
MAINTENANCE_SCHEMA_VERSION = "1.0.0"
MAX_PUBLIC_TEXT_CHARS = 500
MAX_FACTS_BYTES = 8 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
DOCTOR_CHECK_IDS = (
    "python-version",
    "asef-package",
    "host-profile",
    "output-root",
    "docker-cli",
    "docker-daemon",
    "docker-linux-engine",
    "pytest-image",
    "quality-image",
    "context",
    "live-key-presence",
    "managed-containers",
)
_DOCTOR_FACT_KEYS = {
    "python-version": {"major", "minor", "micro", "implementation"},
    "asef-package": {"distribution", "version"},
    "host-profile": {"os", "architecture", "supported"},
    "output-root": {"contained", "writable", "probe_removed"},
    "docker-cli": {"available", "version"},
    "docker-daemon": {"available", "server_version"},
    "docker-linux-engine": {"os_type", "architecture"},
    "pytest-image": {"available", "image_id"},
    "quality-image": {"available", "image_id"},
    "context": {"valid", "system_id", "skill_id"},
    "live-key-presence": {"present"},
    "managed-containers": {"count"},
}


class SecurityExecutorKind(StrEnum):
    HOST_ENVIRONMENT = "HOST_ENVIRONMENT"
    DOCKER_NETWORK = "DOCKER_NETWORK"
    PATH_CONTAINMENT = "PATH_CONTAINMENT"
    FILESYSTEM_LINK = "FILESYSTEM_LINK"
    DOCKER_PIDS = "DOCKER_PIDS"
    DOCKER_MEMORY = "DOCKER_MEMORY"
    DOCKER_TIMEOUT = "DOCKER_TIMEOUT"
    DOCKER_OUTPUT = "DOCKER_OUTPUT"
    STATIC_POLICY = "STATIC_POLICY"
    AGENT_BOUNDARY = "AGENT_BOUNDARY"
    DOCKER_SOCKET = "DOCKER_SOCKET"
    ARTIFACT_CONTRACT = "ARTIFACT_CONTRACT"


class SecurityExpectedOutcome(StrEnum):
    SECRET_ABSENT = "SECRET_ABSENT"
    NETWORK_BLOCKED = "NETWORK_BLOCKED"
    PATH_REJECTED = "PATH_REJECTED"
    LINK_REJECTED = "LINK_REJECTED"
    PID_LIMIT_ENFORCED = "PID_LIMIT_ENFORCED"
    MEMORY_LIMIT_ENFORCED = "MEMORY_LIMIT_ENFORCED"
    TIMEOUT_ENFORCED = "TIMEOUT_ENFORCED"
    OUTPUT_TRUNCATED = "OUTPUT_TRUNCATED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    HOST_AUTHORITY_PRESERVED = "HOST_AUTHORITY_PRESERVED"
    DOCKER_SOCKET_ABSENT = "DOCKER_SOCKET_ABSENT"
    ARTIFACT_SIZE_BLOCKED = "ARTIFACT_SIZE_BLOCKED"


_SECURITY_CASE_MATRIX = {
    "SEC-001": (
        SecurityExecutorKind.HOST_ENVIRONMENT,
        SecurityExpectedOutcome.SECRET_ABSENT,
    ),
    "SEC-002": (
        SecurityExecutorKind.DOCKER_NETWORK,
        SecurityExpectedOutcome.NETWORK_BLOCKED,
    ),
    "SEC-003": (
        SecurityExecutorKind.PATH_CONTAINMENT,
        SecurityExpectedOutcome.PATH_REJECTED,
    ),
    "SEC-004": (
        SecurityExecutorKind.FILESYSTEM_LINK,
        SecurityExpectedOutcome.LINK_REJECTED,
    ),
    "SEC-005": (
        SecurityExecutorKind.DOCKER_PIDS,
        SecurityExpectedOutcome.PID_LIMIT_ENFORCED,
    ),
    "SEC-006": (
        SecurityExecutorKind.DOCKER_MEMORY,
        SecurityExpectedOutcome.MEMORY_LIMIT_ENFORCED,
    ),
    "SEC-007": (
        SecurityExecutorKind.DOCKER_TIMEOUT,
        SecurityExpectedOutcome.TIMEOUT_ENFORCED,
    ),
    "SEC-008": (
        SecurityExecutorKind.DOCKER_OUTPUT,
        SecurityExpectedOutcome.OUTPUT_TRUNCATED,
    ),
    "SEC-009": (
        SecurityExecutorKind.STATIC_POLICY,
        SecurityExpectedOutcome.POLICY_BLOCKED,
    ),
    "SEC-010": (
        SecurityExecutorKind.AGENT_BOUNDARY,
        SecurityExpectedOutcome.HOST_AUTHORITY_PRESERVED,
    ),
    "SEC-011": (
        SecurityExecutorKind.DOCKER_SOCKET,
        SecurityExpectedOutcome.DOCKER_SOCKET_ABSENT,
    ),
    "SEC-012": (
        SecurityExecutorKind.ARTIFACT_CONTRACT,
        SecurityExpectedOutcome.ARTIFACT_SIZE_BLOCKED,
    ),
}


class SecurityCaseStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    UNSUPPORTED = "UNSUPPORTED"


class SecurityClassification(StrEnum):
    CONTROL_ENFORCED = "CONTROL_ENFORCED"
    CONTROL_FAILED = "CONTROL_FAILED"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    UNSUPPORTED_PRIMITIVE = "UNSUPPORTED_PRIMITIVE"


_STATUS_CLASSIFICATIONS = {
    SecurityCaseStatus.PASSED: SecurityClassification.CONTROL_ENFORCED,
    SecurityCaseStatus.FAILED: SecurityClassification.CONTROL_FAILED,
    SecurityCaseStatus.ERROR: SecurityClassification.INFRASTRUCTURE_ERROR,
    SecurityCaseStatus.UNSUPPORTED: SecurityClassification.UNSUPPORTED_PRIMITIVE,
}


@dataclass(slots=True, frozen=True)
class SecurityCaseSpec:
    case_id: str
    version: str
    control: str
    executor: SecurityExecutorKind
    fixture_refs: tuple[str, ...]
    preconditions: tuple[str, ...]
    expected_outcome: SecurityExpectedOutcome
    limitations: tuple[str, ...]
    schema_version: str = SECURITY_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != SECURITY_SCHEMA_VERSION:
            raise ContractValidationError("unsupported security case schema")
        if self.case_id not in SECURITY_CASE_IDS:
            raise ContractValidationError("security case_id must be SEC-001 through SEC-012")
        _validate_semver(self.version, "security case version")
        _validate_public_text(self.control, "security control")
        if not isinstance(self.executor, SecurityExecutorKind):
            raise ContractValidationError("security executor must be a typed enum")
        if not isinstance(self.expected_outcome, SecurityExpectedOutcome):
            raise ContractValidationError("security expected outcome must be a typed enum")
        expected = _SECURITY_CASE_MATRIX[self.case_id]
        if (self.executor, self.expected_outcome) != expected:
            raise ContractValidationError(
                "security case executor/outcome differs from the closed SEC matrix"
            )
        _validate_unique_text(self.preconditions, "security preconditions", required=True)
        _validate_unique_text(self.limitations, "security limitations", required=True)
        if len(self.fixture_refs) != len(set(self.fixture_refs)):
            raise ContractValidationError("security fixture refs must be unique")
        for ref in self.fixture_refs:
            _validate_repo_ref(ref)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


@dataclass(slots=True, frozen=True)
class LoadedSecurityCase:
    spec: SecurityCaseSpec
    directory_ref: str


@dataclass(slots=True, frozen=True)
class LoadedSecurityDataset:
    root_ref: str
    version: str
    cases: tuple[LoadedSecurityCase, ...]
    dataset_hash: str
    loaded_bytes: int


@dataclass(slots=True, frozen=True)
class SecurityExecutionObservation:
    status: SecurityCaseStatus
    classification: SecurityClassification
    duration_ms: int
    facts: dict[str, object]
    diagnostic_code: str | None = None
    diagnostic: str | None = None


@dataclass(slots=True, frozen=True)
class SecurityCaseResult:
    case_id: str
    case_version: str
    status: SecurityCaseStatus
    classification: SecurityClassification
    duration_ms: int
    semantic_fingerprint: str
    evidence_refs: tuple[EvidenceRef, ...] = ()
    facts: dict[str, Any] | None = None
    diagnostic_code: str | None = None
    diagnostic: str | None = None
    schema_version: str = SECURITY_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != SECURITY_SCHEMA_VERSION:
            raise ContractValidationError("unsupported security result schema")
        if self.case_id not in SECURITY_CASE_IDS:
            raise ContractValidationError("invalid security result case_id")
        _validate_semver(self.case_version, "security result case version")
        if not isinstance(self.status, SecurityCaseStatus):
            raise ContractValidationError("security result status must be a typed enum")
        if not isinstance(self.classification, SecurityClassification):
            raise ContractValidationError("security classification must be a typed enum")
        if _STATUS_CLASSIFICATIONS[self.status] is not self.classification:
            raise ContractValidationError("security status and classification do not reconcile")
        if isinstance(self.duration_ms, bool) or not isinstance(self.duration_ms, int):
            raise ContractValidationError("security duration must be an integer")
        if self.duration_ms < 0:
            raise ContractValidationError("security duration cannot be negative")
        _validate_sha256(self.semantic_fingerprint, "security semantic fingerprint")
        for ref in self.evidence_refs:
            ref.validate()
        if self.facts is not None and not isinstance(self.facts, dict):
            raise ContractValidationError("security facts must be an object")
        facts = self.facts or {}
        _validate_public_structure(facts, "security facts")
        if self.status is SecurityCaseStatus.PASSED:
            if not self.evidence_refs:
                raise ContractValidationError("passed security result requires evidence")
            if self.diagnostic_code is not None or self.diagnostic is not None:
                raise ContractValidationError("passed security result cannot contain a diagnostic")
        else:
            _validate_diagnostic(self.diagnostic_code, self.diagnostic, "security result")
        expected_fingerprint = security_result_fingerprint(
            case_id=self.case_id,
            case_version=self.case_version,
            status=self.status,
            classification=self.classification,
            facts=facts,
            diagnostic_code=self.diagnostic_code,
        )
        if self.semantic_fingerprint != expected_fingerprint:
            raise ContractValidationError(
                "security semantic fingerprint does not reconcile with semantic facts"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


@dataclass(slots=True, frozen=True)
class SecuritySuiteReport:
    suite_id: str
    asef_version: str
    dataset_hash: str
    environment: str
    duration_ms: int
    results: tuple[SecurityCaseResult, ...]
    passed: int
    failed: int
    errors: int
    unsupported: int
    limitations: tuple[str, ...]
    schema_version: str = SECURITY_SCHEMA_VERSION

    @property
    def accepted(self) -> bool:
        return (
            self.passed == len(SECURITY_CASE_IDS)
            and self.failed == 0
            and self.errors == 0
            and self.unsupported == 0
        )

    def validate(self) -> None:
        if self.schema_version != SECURITY_SCHEMA_VERSION:
            raise ContractValidationError("unsupported security suite schema")
        for value, label in (
            (self.suite_id, "security suite_id"),
            (self.asef_version, "security ASEF version"),
            (self.environment, "security environment"),
        ):
            _validate_public_text(value, label)
        _validate_sha256(self.dataset_hash, "security dataset hash")
        if isinstance(self.duration_ms, bool) or not isinstance(self.duration_ms, int):
            raise ContractValidationError("security suite duration must be an integer")
        if self.duration_ms < 0:
            raise ContractValidationError("security suite duration cannot be negative")
        if len(self.results) != len(SECURITY_CASE_IDS):
            raise ContractValidationError("security suite must contain exactly twelve results")
        for result in self.results:
            result.validate()
        identities = tuple(result.case_id for result in self.results)
        if identities != SECURITY_CASE_IDS:
            raise ContractValidationError(
                "security suite results must be ordered SEC-001 through SEC-012"
            )
        actual = {
            status: sum(result.status is status for result in self.results)
            for status in SecurityCaseStatus
        }
        if (self.passed, self.failed, self.errors, self.unsupported) != (
            actual[SecurityCaseStatus.PASSED],
            actual[SecurityCaseStatus.FAILED],
            actual[SecurityCaseStatus.ERROR],
            actual[SecurityCaseStatus.UNSUPPORTED],
        ):
            raise ContractValidationError("security suite counters do not reconcile")
        _validate_unique_text(self.limitations, "security suite limitations", required=True)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = _primitive(asdict(self))
        value["accepted"] = self.accepted
        value["total"] = len(self.results)
        return value


def security_case_spec_from_dict(value: dict[str, Any]) -> SecurityCaseSpec:
    _reject_unknown(
        value,
        {
            "schema_version",
            "case_id",
            "version",
            "control",
            "executor",
            "fixture_refs",
            "preconditions",
            "expected_outcome",
            "limitations",
        },
        "security case",
    )
    try:
        spec = SecurityCaseSpec(
            case_id=value["case_id"],
            version=value["version"],
            control=value["control"],
            executor=SecurityExecutorKind(value["executor"]),
            fixture_refs=_string_tuple(value.get("fixture_refs", ()), "fixture_refs"),
            preconditions=_string_tuple(value["preconditions"], "preconditions"),
            expected_outcome=SecurityExpectedOutcome(value["expected_outcome"]),
            limitations=_string_tuple(value["limitations"], "limitations"),
            schema_version=value.get("schema_version", SECURITY_SCHEMA_VERSION),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractValidationError(f"security case is invalid: {exc}") from exc
    spec.validate()
    return spec


class DoctorCategory(StrEnum):
    RUNTIME = "RUNTIME"
    PACKAGE = "PACKAGE"
    HOST = "HOST"
    FILESYSTEM = "FILESYSTEM"
    DOCKER = "DOCKER"
    CONTEXT = "CONTEXT"
    LIVE = "LIVE"
    MAINTENANCE = "MAINTENANCE"


class DoctorCheckStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


class DoctorAggregateStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"


class DoctorRecommendation(StrEnum):
    USE_PYTHON_313 = "USE_PYTHON_313"
    REINSTALL_ASEF_PACKAGE = "REINSTALL_ASEF_PACKAGE"
    USE_SUPPORTED_HOST = "USE_SUPPORTED_HOST"
    FIX_OUTPUT_ROOT = "FIX_OUTPUT_ROOT"
    INSTALL_DOCKER_CLI = "INSTALL_DOCKER_CLI"
    START_DOCKER_DAEMON = "START_DOCKER_DAEMON"
    USE_DOCKER_LINUX_ENGINE = "USE_DOCKER_LINUX_ENGINE"
    BUILD_PYTEST_IMAGE = "BUILD_PYTEST_IMAGE"
    BUILD_QUALITY_IMAGE = "BUILD_QUALITY_IMAGE"
    FIX_CONTEXT = "FIX_CONTEXT"
    CONFIGURE_LIVE_KEY = "CONFIGURE_LIVE_KEY"
    REVIEW_MANAGED_CONTAINERS = "REVIEW_MANAGED_CONTAINERS"


@dataclass(slots=True, frozen=True)
class DoctorCheck:
    check_id: str
    category: DoctorCategory
    required: bool
    status: DoctorCheckStatus
    diagnostic_code: str
    summary: str
    duration_ms: int
    timeout_ms: int
    recommendation: DoctorRecommendation | None = None
    facts: dict[str, Any] | None = None
    schema_version: str = MAINTENANCE_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != MAINTENANCE_SCHEMA_VERSION:
            raise ContractValidationError("unsupported doctor check schema")
        if self.check_id not in DOCTOR_CHECK_IDS:
            raise ContractValidationError("doctor check_id is not in the initial allowlist")
        if not isinstance(self.category, DoctorCategory):
            raise ContractValidationError("doctor category must be a typed enum")
        if not isinstance(self.required, bool):
            raise ContractValidationError("doctor required flag must be boolean")
        if not isinstance(self.status, DoctorCheckStatus):
            raise ContractValidationError("doctor status must be a typed enum")
        if self.recommendation is not None and not isinstance(
            self.recommendation, DoctorRecommendation
        ):
            raise ContractValidationError("doctor recommendation must be allowlisted")
        if self.status is DoctorCheckStatus.PASS and self.recommendation is not None:
            raise ContractValidationError("passing doctor check cannot recommend remediation")
        if self.status is DoctorCheckStatus.SKIP and self.required:
            raise ContractValidationError("required doctor check cannot be skipped")
        if (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, int)
            or self.duration_ms < 0
        ):
            raise ContractValidationError("doctor duration_ms must be non-negative")
        if (
            isinstance(self.timeout_ms, bool)
            or not isinstance(self.timeout_ms, int)
            or self.timeout_ms < 1
        ):
            raise ContractValidationError("doctor timeout_ms must be positive")
        if not _IDENTIFIER.fullmatch(self.diagnostic_code):
            raise ContractValidationError("doctor diagnostic_code is invalid")
        _validate_public_text(self.summary, "doctor summary")
        if self.facts is not None and not isinstance(self.facts, dict):
            raise ContractValidationError("doctor facts must be an object")
        facts = self.facts or {}
        extras = set(facts) - _DOCTOR_FACT_KEYS[self.check_id]
        if extras:
            raise ContractValidationError(
                f"doctor facts are not allowlisted for {self.check_id}: {sorted(extras)}"
            )
        _validate_public_structure(facts, "doctor facts")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


@dataclass(slots=True, frozen=True)
class DoctorReport:
    report_id: str
    asef_version: str
    python_version: str
    profile_id: str
    mode: str
    environment: str
    duration_ms: int
    checks: tuple[DoctorCheck, ...]
    schema_version: str = MAINTENANCE_SCHEMA_VERSION

    @property
    def status(self) -> DoctorAggregateStatus:
        if any(check.status is DoctorCheckStatus.FAIL for check in self.checks):
            return DoctorAggregateStatus.BLOCKED
        if any(
            check.status in {DoctorCheckStatus.WARN, DoctorCheckStatus.SKIP}
            for check in self.checks
        ):
            return DoctorAggregateStatus.DEGRADED
        return DoctorAggregateStatus.HEALTHY

    @property
    def healthy(self) -> bool:
        return self.status is not DoctorAggregateStatus.BLOCKED

    def validate(self) -> None:
        if self.schema_version != MAINTENANCE_SCHEMA_VERSION:
            raise ContractValidationError("unsupported doctor report schema")
        _validate_public_text(self.report_id, "doctor report_id")
        _validate_public_text(self.asef_version, "doctor ASEF version")
        _validate_public_text(self.python_version, "doctor Python version")
        _validate_public_text(self.profile_id, "doctor profile_id")
        _validate_public_text(self.environment, "doctor environment")
        if self.mode not in {"demo", "live"}:
            raise ContractValidationError("doctor mode must be demo or live")
        if isinstance(self.duration_ms, bool) or not isinstance(self.duration_ms, int):
            raise ContractValidationError("doctor duration must be an integer")
        if self.duration_ms < 0:
            raise ContractValidationError("doctor duration cannot be negative")
        if not self.checks:
            raise ContractValidationError("doctor report requires checks")
        for check in self.checks:
            check.validate()
        identities = [check.check_id for check in self.checks]
        if len(identities) != len(set(identities)):
            raise ContractValidationError("doctor report contains duplicate checks")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = _primitive(asdict(self))
        value["status"] = self.status.value
        value["healthy"] = self.healthy
        return value


class RetentionClass(StrEnum):
    EPHEMERAL = "EPHEMERAL"
    FINAL_EVIDENCE = "FINAL_EVIDENCE"
    OPERATIONAL_LOG = "OPERATIONAL_LOG"
    LIVE_CASSETTE = "LIVE_CASSETTE"
    CI_REPORT = "CI_REPORT"
    DEBUG_EVIDENCE = "DEBUG_EVIDENCE"
    CLEANUP_TOMBSTONE = "CLEANUP_TOMBSTONE"


class RetentionMode(StrEnum):
    IMMEDIATE = "IMMEDIATE"
    EXPLICIT = "EXPLICIT"
    ROTATING = "ROTATING"
    MANAGED = "MANAGED"


@dataclass(slots=True, frozen=True)
class RetentionRule:
    artifact_class: RetentionClass
    mode: RetentionMode
    max_age_days: int | None = None
    max_bytes: int | None = None
    backup_count: int | None = None
    publishable: bool = False
    sanitized_only: bool = False

    def validate(self) -> None:
        if not isinstance(self.artifact_class, RetentionClass):
            raise ContractValidationError("retention artifact_class must be typed")
        if not isinstance(self.mode, RetentionMode):
            raise ContractValidationError("retention mode must be typed")
        for value, label in (
            (self.max_age_days, "retention max_age_days"),
            (self.max_bytes, "retention max_bytes"),
            (self.backup_count, "retention backup_count"),
        ):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ContractValidationError(f"{label} must be a non-negative integer")
        if not isinstance(self.publishable, bool) or not isinstance(self.sanitized_only, bool):
            raise ContractValidationError("retention flags must be booleans")
        if self.mode is RetentionMode.IMMEDIATE and any(
            value is not None for value in (self.max_age_days, self.max_bytes, self.backup_count)
        ):
            raise ContractValidationError("immediate retention cannot declare time or size limits")
        if self.mode is RetentionMode.ROTATING and (
            self.max_bytes is None or self.max_bytes < 1 or self.backup_count is None
        ):
            raise ContractValidationError("rotating retention requires bytes and backup count")
        if self.mode is RetentionMode.MANAGED and (
            self.max_age_days is None or self.max_age_days < 1
        ):
            raise ContractValidationError("managed retention requires a positive age")
        if self.publishable and not self.sanitized_only:
            raise ContractValidationError("publishable retention must require sanitization")


@dataclass(slots=True, frozen=True)
class RetentionPolicy:
    policy_id: str
    version: str
    rules: tuple[RetentionRule, ...]
    secure_erase_claimed: bool = False
    automatic_final_evidence_cleanup: bool = False
    schema_version: str = MAINTENANCE_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != MAINTENANCE_SCHEMA_VERSION:
            raise ContractValidationError("unsupported retention policy schema")
        if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", self.policy_id):
            raise ContractValidationError("retention policy_id is invalid")
        _validate_semver(self.version, "retention policy version")
        if self.secure_erase_claimed:
            raise ContractValidationError("ASEF retention policy cannot claim secure erase")
        if self.automatic_final_evidence_cleanup:
            raise ContractValidationError("final evidence cleanup must remain explicit")
        for rule in self.rules:
            rule.validate()
        classes = [rule.artifact_class for rule in self.rules]
        if len(classes) != len(set(classes)) or set(classes) != set(RetentionClass):
            raise ContractValidationError("retention policy must define every class exactly once")
        indexed = {rule.artifact_class: rule for rule in self.rules}
        if indexed[RetentionClass.EPHEMERAL].mode is not RetentionMode.IMMEDIATE:
            raise ContractValidationError("ephemeral resources require immediate retention")
        if indexed[RetentionClass.FINAL_EVIDENCE].mode is not RetentionMode.EXPLICIT:
            raise ContractValidationError("final evidence retention must be explicit")
        operational = indexed[RetentionClass.OPERATIONAL_LOG]
        if (
            operational.mode is not RetentionMode.ROTATING
            or operational.max_bytes != 1_048_576
            or operational.backup_count != 2
        ):
            raise ContractValidationError(
                "operational log retention must be 1 MiB with two backups"
            )
        live = indexed[RetentionClass.LIVE_CASSETTE]
        if live.mode is not RetentionMode.EXPLICIT or live.publishable:
            raise ContractValidationError("live cassettes cannot be automatically publishable")
        ci_report = indexed[RetentionClass.CI_REPORT]
        if (
            ci_report.mode is not RetentionMode.MANAGED
            or ci_report.max_age_days != 7
            or not ci_report.publishable
            or not ci_report.sanitized_only
        ):
            raise ContractValidationError(
                "CI report retention must be managed for seven sanitized days"
            )
        debug = indexed[RetentionClass.DEBUG_EVIDENCE]
        if debug.mode is not RetentionMode.EXPLICIT or not debug.sanitized_only:
            raise ContractValidationError("debug evidence must be sanitized")
        if indexed[RetentionClass.CLEANUP_TOMBSTONE].mode is not RetentionMode.EXPLICIT:
            raise ContractValidationError("cleanup tombstones must be explicitly retained")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


def default_retention_policy() -> RetentionPolicy:
    policy = RetentionPolicy(
        policy_id="asef-local-retention",
        version="1.0.0",
        rules=(
            RetentionRule(RetentionClass.EPHEMERAL, RetentionMode.IMMEDIATE),
            RetentionRule(RetentionClass.FINAL_EVIDENCE, RetentionMode.EXPLICIT),
            RetentionRule(
                RetentionClass.OPERATIONAL_LOG,
                RetentionMode.ROTATING,
                max_bytes=1_048_576,
                backup_count=2,
            ),
            RetentionRule(RetentionClass.LIVE_CASSETTE, RetentionMode.EXPLICIT),
            RetentionRule(
                RetentionClass.CI_REPORT,
                RetentionMode.MANAGED,
                max_age_days=7,
                publishable=True,
                sanitized_only=True,
            ),
            RetentionRule(
                RetentionClass.DEBUG_EVIDENCE,
                RetentionMode.EXPLICIT,
                sanitized_only=True,
            ),
            RetentionRule(RetentionClass.CLEANUP_TOMBSTONE, RetentionMode.EXPLICIT),
        ),
    )
    policy.validate()
    return policy


class CleanupKind(StrEnum):
    RUNS = "runs"
    SMOKE = "smoke"
    SECURITY = "security"
    QUALITY = "quality"
    DOCTOR = "doctor"
    LOGS = "logs"
    CONTAINERS = "containers"
    ALL = "all"


class CleanupMode(StrEnum):
    DRY_RUN = "DRY_RUN"
    APPLY = "APPLY"


class CleanupTargetStatus(StrEnum):
    PLANNED = "PLANNED"
    DELETED = "DELETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass(slots=True, frozen=True)
class CleanupRequest:
    kind: CleanupKind
    older_than_days: int
    mode: CleanupMode = CleanupMode.DRY_RUN
    root_ref: str = ".asef"
    schema_version: str = MAINTENANCE_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != MAINTENANCE_SCHEMA_VERSION:
            raise ContractValidationError("unsupported cleanup request schema")
        if not isinstance(self.kind, CleanupKind):
            raise ContractValidationError("cleanup kind must be a typed enum")
        if not isinstance(self.mode, CleanupMode):
            raise ContractValidationError("cleanup mode must be a typed enum")
        if (
            isinstance(self.older_than_days, bool)
            or not isinstance(self.older_than_days, int)
            or self.older_than_days < 1
        ):
            raise ContractValidationError("cleanup older_than_days must be at least one")
        if self.root_ref != ".asef":
            raise ContractValidationError("cleanup root is fixed at .asef")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


@dataclass(slots=True, frozen=True)
class CleanupTargetObservation:
    target_ref: str
    identity_sha256: str
    status: CleanupTargetStatus
    reason_code: str
    bytes_estimate: int = 0

    def validate(self) -> None:
        _validate_repo_ref(self.target_ref)
        if not self.target_ref.startswith(".asef/"):
            raise ContractValidationError("cleanup target must remain below .asef")
        _validate_sha256(self.identity_sha256, "cleanup target identity")
        if not isinstance(self.status, CleanupTargetStatus):
            raise ContractValidationError("cleanup target status must be typed")
        if not _IDENTIFIER.fullmatch(self.reason_code):
            raise ContractValidationError("cleanup reason_code is invalid")
        if (
            isinstance(self.bytes_estimate, bool)
            or not isinstance(self.bytes_estimate, int)
            or self.bytes_estimate < 0
        ):
            raise ContractValidationError("cleanup bytes estimate must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


@dataclass(slots=True, frozen=True)
class CleanupReport:
    cleanup_id: str
    request: CleanupRequest
    plan_sha256: str
    targets: tuple[CleanupTargetObservation, ...]
    planned: int
    deleted: int
    failed: int
    skipped: int
    policy_id: str = "asef-local-retention"
    policy_version: str = "1.0.0"
    schema_version: str = MAINTENANCE_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != MAINTENANCE_SCHEMA_VERSION:
            raise ContractValidationError("unsupported cleanup report schema")
        _validate_public_text(self.cleanup_id, "cleanup_id")
        if self.policy_id != "asef-local-retention":
            raise ContractValidationError("cleanup report retention policy is invalid")
        _validate_semver(self.policy_version, "cleanup report policy version")
        if self.policy_version != "1.0.0":
            raise ContractValidationError("cleanup report retention policy version is unsupported")
        self.request.validate()
        _validate_sha256(self.plan_sha256, "cleanup plan hash")
        for target in self.targets:
            target.validate()
        refs = [target.target_ref for target in self.targets]
        if len(refs) != len(set(refs)):
            raise ContractValidationError("cleanup report contains duplicate targets")
        actual = {
            status: sum(target.status is status for target in self.targets)
            for status in CleanupTargetStatus
        }
        if (self.planned, self.deleted, self.failed, self.skipped) != (
            actual[CleanupTargetStatus.PLANNED],
            actual[CleanupTargetStatus.DELETED],
            actual[CleanupTargetStatus.FAILED],
            actual[CleanupTargetStatus.SKIPPED],
        ):
            raise ContractValidationError("cleanup report counters do not reconcile")
        if self.request.mode is CleanupMode.DRY_RUN and self.deleted:
            raise ContractValidationError("cleanup dry-run cannot report deleted targets")
        expected_plan = cleanup_plan_fingerprint(self.request, self.targets)
        if self.plan_sha256 != expected_plan:
            raise ContractValidationError("cleanup plan hash does not reconcile with targets")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


class FilesystemTargetStatus(StrEnum):
    SAFE_DIRECTORY = "SAFE_DIRECTORY"
    MISSING = "MISSING"
    OUTSIDE_ROOT = "OUTSIDE_ROOT"
    ROOT_TARGET = "ROOT_TARGET"
    NOT_DIRECTORY = "NOT_DIRECTORY"
    SYMBOLIC_LINK = "SYMBOLIC_LINK"
    JUNCTION = "JUNCTION"


@dataclass(slots=True, frozen=True)
class FilesystemSafetyProfile:
    platform: str
    python_version: str
    junction_detection_available: bool
    rmtree_avoids_symlink_attacks: bool
    dir_fd_removal_available: bool
    follow_symlink_stat_available: bool
    recursive_apply_supported: bool
    diagnostic_code: str
    schema_version: str = MAINTENANCE_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != MAINTENANCE_SCHEMA_VERSION:
            raise ContractValidationError("unsupported filesystem safety profile schema")
        _validate_public_text(self.platform, "filesystem platform")
        _validate_public_text(self.python_version, "filesystem Python version")
        for value in (
            self.junction_detection_available,
            self.rmtree_avoids_symlink_attacks,
            self.dir_fd_removal_available,
            self.follow_symlink_stat_available,
            self.recursive_apply_supported,
        ):
            if not isinstance(value, bool):
                raise ContractValidationError("filesystem capability flags must be booleans")
        if not _IDENTIFIER.fullmatch(self.diagnostic_code):
            raise ContractValidationError("filesystem diagnostic_code is invalid")
        expected_support = (
            self.rmtree_avoids_symlink_attacks
            and self.dir_fd_removal_available
            and self.follow_symlink_stat_available
            and (
                self.platform.lower() != "windows"
                or self.junction_detection_available
            )
        )
        if self.recursive_apply_supported != expected_support:
            raise ContractValidationError(
                "filesystem recursive apply support differs from required primitives"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _primitive(asdict(self))


def characterize_filesystem_safety() -> FilesystemSafetyProfile:
    system = platform.system() or "unknown"
    rmtree_safe = bool(getattr(shutil.rmtree, "avoids_symlink_attacks", False))
    junctions = hasattr(Path("."), "is_junction")
    dir_fd = os.rmdir in os.supports_dir_fd
    follow_stat = os.stat in os.supports_follow_symlinks
    apply_supported = rmtree_safe and dir_fd and follow_stat and (
        system.lower() != "windows" or junctions
    )
    profile = FilesystemSafetyProfile(
        platform=system,
        python_version=platform.python_version() or sys.version.split()[0],
        junction_detection_available=junctions,
        rmtree_avoids_symlink_attacks=rmtree_safe,
        dir_fd_removal_available=dir_fd,
        follow_symlink_stat_available=follow_stat,
        recursive_apply_supported=apply_supported,
        diagnostic_code=(
            "RECURSIVE_APPLY_SUPPORTED"
            if apply_supported
            else "RECURSIVE_APPLY_DRY_RUN_ONLY"
        ),
    )
    profile.validate()
    return profile


def inspect_filesystem_target(root: Path, target: Path) -> FilesystemTargetStatus:
    root_absolute = root.absolute()
    target_absolute = target.absolute()
    try:
        target_absolute.relative_to(root_absolute)
    except ValueError:
        return FilesystemTargetStatus.OUTSIDE_ROOT
    if target_absolute == root_absolute:
        return FilesystemTargetStatus.ROOT_TARGET
    if root_absolute.is_symlink():
        return FilesystemTargetStatus.SYMBOLIC_LINK
    if hasattr(root_absolute, "is_junction") and root_absolute.is_junction():
        return FilesystemTargetStatus.JUNCTION
    if not target_absolute.exists() and not target_absolute.is_symlink():
        return FilesystemTargetStatus.MISSING
    relative = target_absolute.relative_to(root_absolute)
    current = root_absolute
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return FilesystemTargetStatus.SYMBOLIC_LINK
        if hasattr(current, "is_junction") and current.is_junction():
            return FilesystemTargetStatus.JUNCTION
    if not target_absolute.is_dir():
        return FilesystemTargetStatus.NOT_DIRECTORY
    try:
        resolved_root = root_absolute.resolve(strict=True)
        resolved_target = target_absolute.resolve(strict=True)
        resolved_target.relative_to(resolved_root)
    except (OSError, ValueError):
        return FilesystemTargetStatus.OUTSIDE_ROOT
    return FilesystemTargetStatus.SAFE_DIRECTORY


def semantic_security_fingerprint(value: dict[str, Any]) -> str:
    _validate_public_structure(value, "security fingerprint input")
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def security_result_fingerprint(
    *,
    case_id: str,
    case_version: str,
    status: SecurityCaseStatus,
    classification: SecurityClassification,
    facts: dict[str, Any],
    diagnostic_code: str | None,
) -> str:
    return semantic_security_fingerprint(
        {
            "case_id": case_id,
            "case_version": case_version,
            "status": status.value,
            "classification": classification.value,
            "facts": facts,
            "diagnostic_code": diagnostic_code,
        }
    )


def cleanup_plan_fingerprint(
    request: CleanupRequest,
    targets: tuple[CleanupTargetObservation, ...],
) -> str:
    request.validate()
    for target in targets:
        target.validate()
    return semantic_security_fingerprint(
        {
            "kind": request.kind.value,
            "older_than_days": request.older_than_days,
            "root_ref": request.root_ref,
            "targets": [
                {
                    "target_ref": target.target_ref,
                    "identity_sha256": target.identity_sha256,
                    "bytes_estimate": target.bytes_estimate,
                }
                for target in targets
            ],
        }
    )


def _validate_semver(value: str, label: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ContractValidationError(f"{label} must use numeric major.minor.patch")


def _validate_repo_ref(value: str) -> None:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ContractValidationError("security/maintenance refs must be POSIX relative paths")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path == PurePosixPath("."):
        raise ContractValidationError("security/maintenance refs must remain contained")
    if path.as_posix() != value:
        raise ContractValidationError("security/maintenance refs must be canonical")


def _validate_public_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_PUBLIC_TEXT_CHARS:
        raise ContractValidationError(
            f"{label} must contain between 1 and {MAX_PUBLIC_TEXT_CHARS} characters"
        )
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ContractValidationError(f"{label} contains control characters")
    lowered = value.lower()
    if any(marker in lowered for marker in ("api_key=", "password=", "token=", "secret=")):
        raise ContractValidationError(f"{label} contains a sensitive marker")
    if (
        "file://" in lowered
        or "traceback (" in lowered
        or re.search(r"(?:^|\s)(?:[a-zA-Z]:[\\/]|/[^\s]+|\\\\[^\s]+)", value)
    ):
        raise ContractValidationError(f"{label} cannot expose an absolute path")


def _string_tuple(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or any(
        not isinstance(item, str) for item in value
    ):
        raise ContractValidationError(f"security {label} must be an array of strings")
    return tuple(value)


def _validate_unique_text(values: tuple[str, ...], label: str, *, required: bool) -> None:
    if required and not values:
        raise ContractValidationError(f"{label} cannot be empty")
    if len(values) != len(set(values)):
        raise ContractValidationError(f"{label} must be unique")
    for value in values:
        _validate_public_text(value, label)


def _validate_public_structure(value: Any, label: str) -> None:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ContractValidationError(f"{label} must be JSON serializable") from exc
    if len(encoded.encode("utf-8")) > MAX_FACTS_BYTES:
        raise ContractValidationError(f"{label} exceeds {MAX_FACTS_BYTES} bytes")

    def visit(item: Any) -> None:
        if item is None or isinstance(item, (bool, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ContractValidationError(f"{label} contains a non-finite number")
            return
        if isinstance(item, str):
            if len(item) > MAX_PUBLIC_TEXT_CHARS:
                raise ContractValidationError(f"{label} contains oversized text")
            if item:
                _validate_public_text(item, label)
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", key):
                    raise ContractValidationError(f"{label} contains an invalid fact key")
                visit(child)
            return
        raise ContractValidationError(f"{label} contains a non-primitive value")

    visit(value)


def _validate_diagnostic(code: str | None, message: str | None, label: str) -> None:
    if code is None or message is None:
        raise ContractValidationError(f"{label} requires diagnostic code and message")
    if not _IDENTIFIER.fullmatch(code):
        raise ContractValidationError(f"{label} diagnostic code is invalid")
    _validate_public_text(message, f"{label} diagnostic")


def _validate_sha256(value: str, label: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ContractValidationError(f"{label} must be a lowercase SHA-256")


def _reject_unknown(value: dict[str, Any], allowed: set[str], label: str) -> None:
    extras = set(value) - allowed
    if extras:
        raise ContractValidationError(f"{label} contains unknown fields: {sorted(extras)}")


def _primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_primitive(item) for item in value]
    return value
