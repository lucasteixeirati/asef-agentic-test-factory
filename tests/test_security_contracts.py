from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from asef.contracts import ContractValidationError, EvidenceRef
from asef.security_contracts import (
    SECURITY_CASE_IDS,
    CleanupKind,
    CleanupMode,
    CleanupReport,
    CleanupRequest,
    CleanupTargetObservation,
    CleanupTargetStatus,
    DoctorAggregateStatus,
    DoctorCategory,
    DoctorCheck,
    DoctorCheckStatus,
    DoctorRecommendation,
    DoctorReport,
    FilesystemSafetyProfile,
    FilesystemTargetStatus,
    RetentionClass,
    RetentionMode,
    RetentionPolicy,
    RetentionRule,
    SecurityCaseResult,
    SecurityCaseStatus,
    SecurityClassification,
    SecurityExecutorKind,
    SecurityExpectedOutcome,
    SecuritySuiteReport,
    characterize_filesystem_safety,
    cleanup_plan_fingerprint,
    default_retention_policy,
    inspect_filesystem_target,
    security_case_spec_from_dict,
    security_result_fingerprint,
    semantic_security_fingerprint,
)


EVIDENCE = EvidenceRef("security-fact", "security/fact.json", "a" * 64)


def valid_security_spec(case_id: str = "SEC-001") -> dict[str, object]:
    index = SECURITY_CASE_IDS.index(case_id)
    return {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "version": "1.0.0",
        "control": "Exercise one bounded ASEF security control",
        "executor": tuple(SecurityExecutorKind)[index].value,
        "fixture_refs": [f"datasets/security/{case_id}/fixture.txt"],
        "preconditions": ["Reference environment is available"],
        "expected_outcome": tuple(SecurityExpectedOutcome)[index].value,
        "limitations": ["This result is not a security certification"],
    }


def passed_result(case_id: str) -> SecurityCaseResult:
    facts = {"control_observed": True}
    fingerprint = security_result_fingerprint(
        case_id=case_id,
        case_version="1.0.0",
        status=SecurityCaseStatus.PASSED,
        classification=SecurityClassification.CONTROL_ENFORCED,
        facts=facts,
        diagnostic_code=None,
    )
    return SecurityCaseResult(
        case_id=case_id,
        case_version="1.0.0",
        status=SecurityCaseStatus.PASSED,
        classification=SecurityClassification.CONTROL_ENFORCED,
        duration_ms=10,
        semantic_fingerprint=fingerprint,
        evidence_refs=(EVIDENCE,),
        facts=facts,
    )


class SecurityDatasetContractTests(unittest.TestCase):
    def test_case_spec_uses_closed_executor_and_outcome_matrix(self) -> None:
        spec = security_case_spec_from_dict(valid_security_spec("SEC-010"))
        self.assertIs(spec.executor, SecurityExecutorKind.AGENT_BOUNDARY)
        self.assertIs(
            spec.expected_outcome,
            SecurityExpectedOutcome.HOST_AUTHORITY_PRESERVED,
        )
        self.assertEqual(spec.to_dict()["case_id"], "SEC-010")

    def test_case_spec_rejects_unknown_fields_traversal_and_matrix_changes(self) -> None:
        value = valid_security_spec()
        value["command"] = ["docker", "run"]
        with self.assertRaisesRegex(ContractValidationError, "unknown fields"):
            security_case_spec_from_dict(value)

        value = valid_security_spec()
        value["fixture_refs"] = ["../outside"]
        with self.assertRaisesRegex(ContractValidationError, "contained"):
            security_case_spec_from_dict(value)

        value = valid_security_spec()
        value["executor"] = "DOCKER_NETWORK"
        with self.assertRaisesRegex(ContractValidationError, "closed SEC matrix"):
            security_case_spec_from_dict(value)

        value = valid_security_spec()
        value["preconditions"] = "not-an-array"
        with self.assertRaisesRegex(ContractValidationError, "array of strings"):
            security_case_spec_from_dict(value)

    def test_case_spec_rejects_invalid_identity_text_lists_and_refs(self) -> None:
        valid = security_case_spec_from_dict(valid_security_spec())
        invalid = (
            replace(valid, schema_version="2.0.0"),
            replace(valid, case_id="SEC-013"),
            replace(valid, version="1.0"),
            replace(valid, control=""),
            replace(valid, executor="HOST_ENVIRONMENT"),  # type: ignore[arg-type]
            replace(valid, expected_outcome="SECRET_ABSENT"),  # type: ignore[arg-type]
            replace(valid, preconditions=()),
            replace(valid, preconditions=("same", "same")),
            replace(valid, limitations=()),
            replace(valid, fixture_refs=("fixture", "fixture")),
            replace(valid, fixture_refs=("C:\\fixture",)),
        )
        for spec in invalid:
            with self.subTest(spec=spec), self.assertRaises(ContractValidationError):
                spec.validate()

    def test_result_status_requires_matching_classification_and_evidence(self) -> None:
        passed_result("SEC-001").validate()
        with self.assertRaisesRegex(ContractValidationError, "requires evidence"):
            replace(passed_result("SEC-001"), evidence_refs=()).validate()
        with self.assertRaisesRegex(ContractValidationError, "do not reconcile"):
            replace(
                passed_result("SEC-001"),
                classification=SecurityClassification.CONTROL_FAILED,
            ).validate()

        failed = replace(
            passed_result("SEC-001"),
            status=SecurityCaseStatus.FAILED,
            classification=SecurityClassification.CONTROL_FAILED,
            diagnostic_code="CONTROL_NOT_ENFORCED",
            diagnostic="The expected control was not observed",
        )
        failed = replace(
            failed,
            semantic_fingerprint=security_result_fingerprint(
                case_id=failed.case_id,
                case_version=failed.case_version,
                status=failed.status,
                classification=failed.classification,
                facts=failed.facts or {},
                diagnostic_code=failed.diagnostic_code,
            ),
        )
        failed.validate()

    def test_result_rejects_invalid_headers_diagnostics_and_pass_diagnostics(self) -> None:
        valid = passed_result("SEC-001")
        invalid = (
            replace(valid, schema_version="2.0.0"),
            replace(valid, case_id="SEC-999"),
            replace(valid, case_version="v1"),
            replace(valid, status="PASSED"),  # type: ignore[arg-type]
            replace(valid, classification="CONTROL_ENFORCED"),  # type: ignore[arg-type]
            replace(valid, duration_ms=True),  # type: ignore[arg-type]
            replace(valid, duration_ms=-1),
            replace(valid, semantic_fingerprint="invalid"),
            replace(valid, diagnostic_code="UNEXPECTED", diagnostic="Unexpected"),
        )
        for result in invalid:
            with self.subTest(result=result), self.assertRaises(ContractValidationError):
                result.validate()

        failed = replace(
            valid,
            status=SecurityCaseStatus.FAILED,
            classification=SecurityClassification.CONTROL_FAILED,
            evidence_refs=(),
        )
        for result in (
            failed,
            replace(failed, diagnostic_code="bad", diagnostic="Failure"),
            replace(failed, diagnostic_code="CONTROL_FAILED", diagnostic=""),
        ):
            with self.subTest(result=result), self.assertRaises(ContractValidationError):
                result.validate()

    def test_result_rejects_sensitive_or_oversized_public_facts(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "sensitive"):
            replace(
                passed_result("SEC-001"),
                facts={"detail": "api_key=value"},
            ).validate()
        with self.assertRaisesRegex(ContractValidationError, "oversized"):
            replace(
                passed_result("SEC-001"),
                facts={"detail": "x" * 501},
            ).validate()
        with self.assertRaisesRegex(ContractValidationError, "non-finite"):
            replace(
                passed_result("SEC-001"),
                facts={"ratio": float("nan")},
            ).validate()
        with self.assertRaisesRegex(ContractValidationError, "does not reconcile"):
            replace(
                passed_result("SEC-001"),
                semantic_fingerprint="f" * 64,
            ).validate()

    def test_suite_requires_twelve_ordered_results_and_zero_unsupported_for_acceptance(self) -> None:
        results = tuple(passed_result(case_id) for case_id in SECURITY_CASE_IDS)
        report = SecuritySuiteReport(
            suite_id="security-suite-001",
            asef_version="0.1.0a4",
            dataset_hash="b" * 64,
            environment="windows-python-3.13",
            duration_ms=120,
            results=results,
            passed=12,
            failed=0,
            errors=0,
            unsupported=0,
            limitations=("Reference-profile controls only",),
        )
        self.assertTrue(report.to_dict()["accepted"])

        unsupported = replace(
            results[3],
            status=SecurityCaseStatus.UNSUPPORTED,
            classification=SecurityClassification.UNSUPPORTED_PRIMITIVE,
            evidence_refs=(),
            diagnostic_code="LINK_PRIMITIVE_UNAVAILABLE",
            diagnostic="The required link primitive is unavailable",
        )
        unsupported = replace(
            unsupported,
            semantic_fingerprint=security_result_fingerprint(
                case_id=unsupported.case_id,
                case_version=unsupported.case_version,
                status=unsupported.status,
                classification=unsupported.classification,
                facts=unsupported.facts or {},
                diagnostic_code=unsupported.diagnostic_code,
            ),
        )
        changed = results[:3] + (unsupported,) + results[4:]
        partial = replace(report, results=changed, passed=11, unsupported=1)
        self.assertFalse(partial.to_dict()["accepted"])

        with self.assertRaisesRegex(ContractValidationError, "ordered"):
            replace(report, results=tuple(reversed(results))).validate()

    def test_suite_rejects_invalid_headers_counts_and_limitations(self) -> None:
        results = tuple(passed_result(case_id) for case_id in SECURITY_CASE_IDS)
        report = SecuritySuiteReport(
            "security-suite-001",
            "0.1.0a4",
            "b" * 64,
            "test",
            10,
            results,
            12,
            0,
            0,
            0,
            ("Reference controls only",),
        )
        invalid = (
            replace(report, schema_version="2.0.0"),
            replace(report, suite_id=""),
            replace(report, dataset_hash="bad"),
            replace(report, duration_ms=True),  # type: ignore[arg-type]
            replace(report, duration_ms=-1),
            replace(report, results=results[:-1], passed=11),
            replace(report, passed=11, failed=1),
            replace(report, limitations=()),
            replace(report, limitations=("same", "same")),
        )
        for candidate in invalid:
            with self.subTest(candidate=candidate), self.assertRaises(ContractValidationError):
                candidate.validate()


class DoctorContractTests(unittest.TestCase):
    def test_report_derives_health_from_required_failures(self) -> None:
        passing = DoctorCheck(
            check_id="python-version",
            category=DoctorCategory.RUNTIME,
            required=True,
            status=DoctorCheckStatus.PASS,
            diagnostic_code="PYTHON_VERSION_SUPPORTED",
            summary="Python 3.13 is supported",
            duration_ms=1,
            timeout_ms=1000,
            facts={"major": 3, "minor": 13},
        )
        warning = DoctorCheck(
            check_id="managed-containers",
            category=DoctorCategory.MAINTENANCE,
            required=False,
            status=DoctorCheckStatus.WARN,
            diagnostic_code="MANAGED_CONTAINERS_FOUND",
            summary="Managed containers require operator review",
            duration_ms=1,
            timeout_ms=1000,
            recommendation=DoctorRecommendation.REVIEW_MANAGED_CONTAINERS,
        )
        report = DoctorReport(
            report_id="doctor-001",
            asef_version="0.1.0a4",
            python_version="3.13.5",
            profile_id="python-pytest",
            mode="demo",
            environment="test-environment",
            duration_ms=10,
            checks=(passing, warning),
        )
        self.assertEqual(report.to_dict()["status"], "DEGRADED")
        self.assertTrue(report.to_dict()["healthy"])

        failed = replace(
            passing,
            status=DoctorCheckStatus.FAIL,
            diagnostic_code="PYTHON_VERSION_UNSUPPORTED",
            summary="Python version is unsupported",
            recommendation=DoctorRecommendation.USE_PYTHON_313,
        )
        blocked = replace(report, checks=(failed, warning)).to_dict()
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertFalse(blocked["healthy"])

        optional_failure = replace(failed, required=False)
        self.assertIs(
            replace(report, checks=(passing, optional_failure)).status,
            DoctorAggregateStatus.BLOCKED,
        )

    def test_doctor_recommendations_are_allowlisted_and_output_is_sanitized(self) -> None:
        valid = DoctorCheck(
            "docker-daemon",
            DoctorCategory.DOCKER,
            True,
            DoctorCheckStatus.FAIL,
            "DOCKER_DAEMON_UNAVAILABLE",
            "Docker daemon is unavailable",
            1,
            1000,
            DoctorRecommendation.START_DOCKER_DAEMON,
        )
        valid.validate()
        with self.assertRaisesRegex(ContractValidationError, "allowlisted"):
            replace(valid, recommendation="run reflected error text").validate()  # type: ignore[arg-type]
        with self.assertRaisesRegex(ContractValidationError, "sensitive"):
            replace(valid, summary="token=value").validate()
        with self.assertRaisesRegex(ContractValidationError, "cannot expose"):
            replace(valid, summary="Failure at C:\\private\\config").validate()
        with self.assertRaisesRegex(ContractValidationError, "cannot recommend"):
            replace(
                valid,
                status=DoctorCheckStatus.PASS,
                diagnostic_code="DOCKER_DAEMON_AVAILABLE",
            ).validate()

    def test_required_check_cannot_be_skipped_and_ids_are_unique(self) -> None:
        check = DoctorCheck(
            "docker-cli",
            DoctorCategory.DOCKER,
            True,
            DoctorCheckStatus.SKIP,
            "DOCKER_CHECK_SKIPPED",
            "Docker check was skipped",
            1,
            1000,
        )
        with self.assertRaisesRegex(ContractValidationError, "cannot be skipped"):
            check.validate()

        optional = replace(check, required=False)
        report = DoctorReport(
            "doctor-001",
            "0.1.0a4",
            "3.13.5",
            "python-pytest",
            "demo",
            "test",
            1,
            (optional, optional),
        )
        with self.assertRaisesRegex(ContractValidationError, "duplicate"):
            report.validate()

    def test_doctor_rejects_invalid_check_and_report_headers(self) -> None:
        check = DoctorCheck(
            "docker-cli",
            DoctorCategory.DOCKER,
            True,
            DoctorCheckStatus.PASS,
            "DOCKER_CLI_AVAILABLE",
            "Docker CLI is available",
            1,
            1000,
        )
        invalid_checks = (
            replace(check, schema_version="2.0.0"),
            replace(check, check_id="INVALID_ID"),
            replace(check, category="DOCKER"),  # type: ignore[arg-type]
            replace(check, required=1),  # type: ignore[arg-type]
            replace(check, status="PASS"),  # type: ignore[arg-type]
            replace(check, duration_ms=True),  # type: ignore[arg-type]
            replace(check, duration_ms=-1),
            replace(check, timeout_ms=0),
            replace(check, diagnostic_code="bad-code"),
            replace(check, facts={"BadKey": True}),
        )
        for candidate in invalid_checks:
            with self.subTest(candidate=candidate), self.assertRaises(ContractValidationError):
                candidate.validate()

        report = DoctorReport(
            "doctor-001",
            "0.1.0a4",
            "3.13.5",
            "python-pytest",
            "demo",
            "test",
            1,
            (check,),
        )
        invalid_reports = (
            replace(report, schema_version="2.0.0"),
            replace(report, report_id=""),
            replace(report, asef_version=""),
            replace(report, python_version=""),
            replace(report, profile_id=""),
            replace(report, mode="repair"),
            replace(report, duration_ms=True),  # type: ignore[arg-type]
            replace(report, duration_ms=-1),
            replace(report, checks=()),
        )
        for candidate in invalid_reports:
            with self.subTest(candidate=candidate), self.assertRaises(ContractValidationError):
                candidate.validate()


class RetentionAndCleanupContractTests(unittest.TestCase):
    def test_default_policy_freezes_conservative_retention(self) -> None:
        policy = default_retention_policy()
        value = policy.to_dict()
        rules = {item["artifact_class"]: item for item in value["rules"]}
        self.assertEqual(rules["EPHEMERAL"]["mode"], "IMMEDIATE")
        self.assertEqual(rules["FINAL_EVIDENCE"]["mode"], "EXPLICIT")
        self.assertEqual(rules["OPERATIONAL_LOG"]["max_bytes"], 1_048_576)
        self.assertEqual(rules["OPERATIONAL_LOG"]["backup_count"], 2)
        self.assertEqual(rules["CI_REPORT"]["max_age_days"], 7)
        self.assertTrue(rules["DEBUG_EVIDENCE"]["sanitized_only"])
        self.assertFalse(value["secure_erase_claimed"])

    def test_retention_rejects_missing_classes_secure_erase_and_automatic_evidence_deletion(self) -> None:
        policy = default_retention_policy()
        with self.assertRaisesRegex(ContractValidationError, "every class"):
            replace(policy, rules=policy.rules[:-1]).validate()
        with self.assertRaisesRegex(ContractValidationError, "secure erase"):
            replace(policy, secure_erase_claimed=True).validate()
        with self.assertRaisesRegex(ContractValidationError, "must remain explicit"):
            replace(policy, automatic_final_evidence_cleanup=True).validate()
        with self.assertRaisesRegex(ContractValidationError, "sanitization"):
            replace(
                policy,
                rules=tuple(
                    replace(rule, sanitized_only=False)
                    if rule.artifact_class is RetentionClass.CI_REPORT
                    else rule
                    for rule in policy.rules
                ),
            ).validate()

    def test_cleanup_is_dry_run_by_default_and_root_is_fixed(self) -> None:
        request = CleanupRequest(CleanupKind.RUNS, older_than_days=7)
        self.assertIs(request.mode, CleanupMode.DRY_RUN)
        self.assertEqual(request.to_dict()["root_ref"], ".asef")
        for invalid in (
            replace(request, older_than_days=0),
            replace(request, older_than_days=True),  # type: ignore[arg-type]
            replace(request, root_ref="."),
            replace(request, kind="runs"),  # type: ignore[arg-type]
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ContractValidationError):
                invalid.validate()

    def test_cleanup_report_reconciles_tombstone_and_dry_run_cannot_delete(self) -> None:
        request = CleanupRequest(CleanupKind.RUNS, 7)
        target = CleanupTargetObservation(
            ".asef/runs/run-001",
            "c" * 64,
            CleanupTargetStatus.PLANNED,
            "TARGET_ELIGIBLE",
            100,
        )
        report = CleanupReport(
            cleanup_id="cleanup-001",
            request=request,
            plan_sha256=cleanup_plan_fingerprint(request, (target,)),
            targets=(target,),
            planned=1,
            deleted=0,
            failed=0,
            skipped=0,
        )
        report.validate()
        with self.assertRaisesRegex(ContractValidationError, "dry-run"):
            replace(
                report,
                targets=(replace(target, status=CleanupTargetStatus.DELETED),),
                planned=0,
                deleted=1,
            ).validate()
        with self.assertRaisesRegex(ContractValidationError, "below .asef"):
            replace(target, target_ref="runs/run-001").validate()

    def test_retention_rule_shapes_are_explicit(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "requires bytes"):
            RetentionRule(
                RetentionClass.OPERATIONAL_LOG,
                RetentionMode.ROTATING,
            ).validate()
        with self.assertRaisesRegex(ContractValidationError, "positive age"):
            RetentionRule(
                RetentionClass.CI_REPORT,
                RetentionMode.MANAGED,
                max_age_days=0,
            ).validate()

    def test_retention_rejects_invalid_policy_and_rule_headers(self) -> None:
        policy = default_retention_policy()
        invalid_policies = (
            replace(policy, schema_version="2.0.0"),
            replace(policy, policy_id="INVALID"),
            replace(policy, version="1"),
            replace(
                policy,
                rules=policy.rules + (policy.rules[0],),
            ),
            replace(
                policy,
                rules=tuple(
                    replace(rule, mode=RetentionMode.EXPLICIT)
                    if rule.artifact_class is RetentionClass.EPHEMERAL
                    else rule
                    for rule in policy.rules
                ),
            ),
            replace(
                policy,
                rules=tuple(
                    replace(rule, max_bytes=2_000_000)
                    if rule.artifact_class is RetentionClass.OPERATIONAL_LOG
                    else rule
                    for rule in policy.rules
                ),
            ),
            replace(
                policy,
                rules=tuple(
                    replace(rule, mode=RetentionMode.MANAGED, max_age_days=7)
                    if rule.artifact_class is RetentionClass.LIVE_CASSETTE
                    else rule
                    for rule in policy.rules
                ),
            ),
            replace(
                policy,
                rules=tuple(
                    replace(rule, mode=RetentionMode.IMMEDIATE)
                    if rule.artifact_class is RetentionClass.FINAL_EVIDENCE
                    else rule
                    for rule in policy.rules
                ),
            ),
            replace(
                policy,
                rules=tuple(
                    replace(rule, max_age_days=8)
                    if rule.artifact_class is RetentionClass.CI_REPORT
                    else rule
                    for rule in policy.rules
                ),
            ),
            replace(
                policy,
                rules=tuple(
                    replace(rule, mode=RetentionMode.IMMEDIATE)
                    if rule.artifact_class is RetentionClass.CLEANUP_TOMBSTONE
                    else rule
                    for rule in policy.rules
                ),
            ),
        )
        for candidate in invalid_policies:
            with self.subTest(candidate=candidate), self.assertRaises(ContractValidationError):
                candidate.validate()

        invalid_rules = (
            RetentionRule("EPHEMERAL", RetentionMode.IMMEDIATE),  # type: ignore[arg-type]
            RetentionRule(RetentionClass.EPHEMERAL, "IMMEDIATE"),  # type: ignore[arg-type]
            RetentionRule(RetentionClass.EPHEMERAL, RetentionMode.IMMEDIATE, max_age_days=1),
            RetentionRule(
                RetentionClass.CI_REPORT,
                RetentionMode.MANAGED,
                max_age_days=7,
                publishable=True,
                sanitized_only=False,
            ),
            RetentionRule(
                RetentionClass.OPERATIONAL_LOG,
                RetentionMode.ROTATING,
                max_bytes=True,  # type: ignore[arg-type]
                backup_count=2,
            ),
        )
        for candidate in invalid_rules:
            with self.subTest(candidate=candidate), self.assertRaises(ContractValidationError):
                candidate.validate()

    def test_cleanup_observation_and_report_fail_closed(self) -> None:
        target = CleanupTargetObservation(
            ".asef/runs/run-001",
            "c" * 64,
            CleanupTargetStatus.PLANNED,
            "TARGET_ELIGIBLE",
        )
        invalid_targets = (
            replace(target, target_ref="../outside"),
            replace(target, identity_sha256="bad"),
            replace(target, status="PLANNED"),  # type: ignore[arg-type]
            replace(target, reason_code="bad-code"),
            replace(target, bytes_estimate=True),  # type: ignore[arg-type]
            replace(target, bytes_estimate=-1),
        )
        for candidate in invalid_targets:
            with self.subTest(candidate=candidate), self.assertRaises(ContractValidationError):
                candidate.validate()

        report = CleanupReport(
            "cleanup-001",
            CleanupRequest(CleanupKind.RUNS, 7, CleanupMode.APPLY),
            "",
            (target,),
            1,
            0,
            0,
            0,
        )
        report = replace(
            report,
            plan_sha256=cleanup_plan_fingerprint(report.request, report.targets),
        )
        invalid_reports = (
            replace(report, schema_version="2.0.0"),
            replace(report, cleanup_id=""),
            replace(report, policy_id="unknown-policy"),
            replace(report, policy_version="1"),
            replace(report, policy_version="1.1.0"),
            replace(report, plan_sha256="bad"),
            replace(report, plan_sha256="e" * 64),
            replace(report, targets=(target, target), planned=2),
            replace(report, planned=0, failed=1),
        )
        for candidate in invalid_reports:
            with self.subTest(candidate=candidate), self.assertRaises(ContractValidationError):
                candidate.validate()


class FilesystemSafetyCharacterizationTests(unittest.TestCase):
    def test_runtime_profile_is_internally_consistent(self) -> None:
        profile = characterize_filesystem_safety()
        profile.validate()
        expected = (
            profile.rmtree_avoids_symlink_attacks
            and profile.dir_fd_removal_available
            and profile.follow_symlink_stat_available
            and (
                profile.platform.lower() != "windows"
                or profile.junction_detection_available
            )
        )
        self.assertEqual(profile.recursive_apply_supported, expected)
        if not expected:
            self.assertEqual(profile.diagnostic_code, "RECURSIVE_APPLY_DRY_RUN_ONLY")

    def test_profile_cannot_overclaim_recursive_apply_support(self) -> None:
        profile = FilesystemSafetyProfile(
            platform="Windows",
            python_version="3.13.0",
            junction_detection_available=True,
            rmtree_avoids_symlink_attacks=False,
            dir_fd_removal_available=False,
            follow_symlink_stat_available=True,
            recursive_apply_supported=True,
            diagnostic_code="RECURSIVE_APPLY_SUPPORTED",
        )
        with self.assertRaisesRegex(ContractValidationError, "differs"):
            profile.validate()

    def test_profile_rejects_invalid_schema_text_flags_and_diagnostic(self) -> None:
        profile = characterize_filesystem_safety()
        invalid = (
            replace(profile, schema_version="2.0.0"),
            replace(profile, platform=""),
            replace(profile, python_version=""),
            replace(profile, junction_detection_available=1),  # type: ignore[arg-type]
            replace(profile, diagnostic_code="bad-code"),
        )
        for candidate in invalid:
            with self.subTest(candidate=candidate), self.assertRaises(ContractValidationError):
                candidate.validate()

    def test_target_inspection_rejects_root_outside_file_and_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            safe = root / "safe"
            safe.mkdir()
            file_target = root / "file.txt"
            file_target.write_text("fixture", encoding="utf-8")
            outside = Path(directory) / "outside"
            outside.mkdir()
            self.assertIs(
                inspect_filesystem_target(root, safe),
                FilesystemTargetStatus.SAFE_DIRECTORY,
            )
            self.assertIs(
                inspect_filesystem_target(root, root),
                FilesystemTargetStatus.ROOT_TARGET,
            )
            self.assertIs(
                inspect_filesystem_target(root, outside),
                FilesystemTargetStatus.OUTSIDE_ROOT,
            )
            self.assertIs(
                inspect_filesystem_target(root, file_target),
                FilesystemTargetStatus.NOT_DIRECTORY,
            )
            self.assertIs(
                inspect_filesystem_target(root, root / "missing"),
                FilesystemTargetStatus.MISSING,
            )

    def test_target_inspection_detects_real_symbolic_link_when_host_allows_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            root.mkdir()
            outside = base / "outside"
            outside.mkdir()
            link = root / "link"
            try:
                os.symlink(outside, link, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("host does not allow creation of a symbolic link fixture")
            self.assertIs(
                inspect_filesystem_target(root, link),
                FilesystemTargetStatus.SYMBOLIC_LINK,
            )
            self.assertTrue(outside.exists())

    def test_target_inspection_rejects_a_linked_root_when_host_allows_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            real_root = base / "real-root"
            real_root.mkdir()
            child = real_root / "child"
            child.mkdir()
            linked_root = base / "linked-root"
            try:
                os.symlink(real_root, linked_root, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("host does not allow creation of a symbolic link fixture")
            self.assertIs(
                inspect_filesystem_target(linked_root, linked_root / "child"),
                FilesystemTargetStatus.SYMBOLIC_LINK,
            )


if __name__ == "__main__":
    unittest.main()
