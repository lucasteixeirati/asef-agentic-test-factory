from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

from jsonschema import Draft202012Validator

from asef.contracts import ContractValidationError
from asef.outcomes import RunClassification, RunStatus
from asef.report_contracts import (
    REPORT_SCHEMA_VERSION,
    AlphaRunReport,
    EvidenceIntegrityStatus,
    LimitationSeverity,
    QualityObservationStatus,
    ReportArtifact,
    ReportAttempt,
    ReportEvidence,
    ReportFact,
    ReportFactCategory,
    ReportFactSource,
    ReportFunctionalResult,
    ReportInference,
    ReportInferenceKind,
    ReportLimitation,
    ReportObservationStatus,
    ReportPolicyAndBudgets,
    ReportQualityObservation,
    ReportRecommendation,
    ReportRecommendationCode,
    ReportRequirement,
    ReportSupportLevel,
    ReportTraceLink,
    ReportTraceNode,
    ReportUsage,
    TraceLinkKind,
    TraceNodeKind,
    alpha_run_report_from_dict,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "src" / "asef" / "schemas" / "alpha-run-report.schema.json"


def valid_report() -> AlphaRunReport:
    evidence = (
        ReportEvidence(
            "EV-STATE",
            "run-state",
            "state.json",
            "a" * 64,
            "1.3.0",
            EvidenceIntegrityStatus.VERIFIED,
            True,
            True,
        ),
        ReportEvidence(
            "EV-ARTIFACT",
            "unit-test-artifact",
            "artifacts/attempt-001/tests_generated/test_unit.py",
            "b" * 64,
            "1.0.0",
            EvidenceIntegrityStatus.VERIFIED,
            False,
            False,
        ),
        ReportEvidence(
            "EV-EXECUTION",
            "normalized-execution",
            "attempts/001/generated/execution.json",
            "c" * 64,
            "1.1.0",
            EvidenceIntegrityStatus.VERIFIED,
            True,
            True,
        ),
    )
    nodes = (
        ReportTraceNode("REQ-001", TraceNodeKind.REQUIREMENT, "Add two signed integers"),
        ReportTraceNode("BEH-001", TraceNodeKind.BEHAVIOR, "Return the arithmetic sum"),
        ReportTraceNode("RSK-001", TraceNodeKind.RISK, "Boundary inputs can be mishandled"),
        ReportTraceNode("SCN-001", TraceNodeKind.SCENARIO, "Add two positive integers"),
        ReportTraceNode(
            "ART-ATTEMPT-001",
            TraceNodeKind.ARTIFACT,
            "Generated unit test artifact",
            ("EV-ARTIFACT",),
        ),
        ReportTraceNode(
            "EXEC-ATTEMPT-001-generated",
            TraceNodeKind.EXECUTION,
            "Generated test execution",
            ("EV-EXECUTION",),
        ),
    )
    links = (
        ReportTraceLink("REQ-001", "BEH-001", TraceLinkKind.DERIVED_FROM_REQUIREMENT),
        ReportTraceLink("REQ-001", "RSK-001", TraceLinkKind.DERIVED_FROM_REQUIREMENT),
        ReportTraceLink("REQ-001", "SCN-001", TraceLinkKind.DERIVED_FROM_REQUIREMENT),
        ReportTraceLink("ART-ATTEMPT-001", "SCN-001", TraceLinkKind.COVERS_SCENARIO),
        ReportTraceLink(
            "EXEC-ATTEMPT-001-generated",
            "ART-ATTEMPT-001",
            TraceLinkKind.EXECUTES_ARTIFACT,
        ),
    )
    facts = (
        ReportFact(
            "FACT-EXECUTION-PASSED",
            ReportFactCategory.EXECUTION,
            "EXECUTION_PASSED",
            True,
            ReportFactSource.EXECUTION,
            ReportObservationStatus.OBSERVED,
            "attempts/001/generated/execution.json",
            ("EV-EXECUTION",),
        ),
    )
    inferences = (
        ReportInference(
            "INF-FUNCTIONAL-ACCEPTED",
            ReportInferenceKind.FUNCTIONAL_RESULT,
            "GENERATED_TESTS_ACCEPTED",
            "The generated tests satisfied the deterministic acceptance rule",
            ("FACT-EXECUTION-PASSED",),
            ("EV-EXECUTION",),
        ),
    )
    limitations = (
        ReportLimitation(
            "REFERENCE_PROFILE_ONLY",
            LimitationSeverity.INFO,
            "The result applies only to the bounded Python reference profile",
        ),
        ReportLimitation(
            "QUALITY_NOT_REQUESTED",
            LimitationSeverity.INFO,
            "Quality capabilities were not requested for this run",
        ),
        ReportLimitation(
            "NOT_SAFE_FOR_PRODUCTION",
            LimitationSeverity.WARNING,
            "The experimental runtime is not approved for production workloads",
        ),
    )
    return AlphaRunReport(
        report_id="run-001",
        asef_version="0.1.0a6",
        run_id="run-001",
        workflow_id="WF-001",
        workflow_version="0.1.0-alpha",
        status=RunStatus.SUCCEEDED,
        classification=RunClassification.ACCEPTED,
        terminal=True,
        execution_mode="demo",
        language_profile="python-pytest",
        support_level=ReportSupportLevel.EXPERIMENTAL,
        context_snapshot_ref="context-snapshot.json",
        report_generated_from_state_schema="1.3.0",
        requirement=ReportRequirement(
            "REQ-001", "Signed integer addition", "Add two signed integers"
        ),
        traceability_nodes=nodes,
        traceability_links=links,
        artifacts=(
            ReportArtifact(
                "ART-ATTEMPT-001",
                "artifacts/attempt-001/tests_generated/test_unit.py",
                "b" * 64,
                ("SCN-001",),
                1,
                ("EV-ARTIFACT",),
            ),
        ),
        attempts=(
            ReportAttempt(
                1,
                "ART-ATTEMPT-001",
                "EXEC-ATTEMPT-001-generated",
                None,
                "PASSED",
                ("EV-EXECUTION",),
            ),
        ),
        functional_result=ReportFunctionalResult(
            True,
            "GENERATED_TESTS_ACCEPTED",
            1,
            1,
            0,
            0,
            0,
            ("INF-FUNCTIONAL-ACCEPTED",),
            ("EV-EXECUTION",),
        ),
        quality=(
            ReportQualityObservation(
                "coverage",
                QualityObservationStatus.NOT_REQUESTED,
                False,
                (),
                (),
                ("QUALITY_NOT_REQUESTED",),
            ),
        ),
        human_interventions=(),
        policy_and_budgets=ReportPolicyAndBudgets(4, 2, 20_000, 4_000, 120, 0.0),
        usage=ReportUsage(2, 0, 0, 100, 50, 1_000, 0.0),
        evidence=evidence,
        facts=facts,
        inferences=inferences,
        recommendations=(
            ReportRecommendation(
                "REC-NOT-PRODUCTION",
                ReportRecommendationCode.DO_NOT_USE_IN_PRODUCTION,
                "run-001",
                "Do not use this experimental result as production approval",
                False,
                (),
                ("NOT_SAFE_FOR_PRODUCTION",),
            ),
        ),
        limitations=limitations,
    )


class AlphaRunReportContractTests(unittest.TestCase):
    def test_valid_report_round_trips_through_strict_parser(self) -> None:
        report = valid_report()
        payload = report.to_dict()
        restored = alpha_run_report_from_dict(payload)

        self.assertEqual(restored.to_dict(), payload)
        self.assertEqual(payload["schema_version"], REPORT_SCHEMA_VERSION)
        self.assertIs(restored.status, RunStatus.SUCCEEDED)
        self.assertIs(restored.support_level, ReportSupportLevel.EXPERIMENTAL)

    def test_parser_rejects_unknown_missing_and_mistyped_fields(self) -> None:
        payload = valid_report().to_dict()
        payload["command"] = ["docker", "run"]
        with self.assertRaisesRegex(ContractValidationError, "unknown fields"):
            alpha_run_report_from_dict(payload)

        payload = valid_report().to_dict()
        del payload["facts"]
        with self.assertRaisesRegex(ContractValidationError, "missing fields"):
            alpha_run_report_from_dict(payload)

        payload = valid_report().to_dict()
        payload["usage"]["model_calls"] = True
        with self.assertRaisesRegex(ContractValidationError, "must be an integer"):
            alpha_run_report_from_dict(payload)

    def test_parser_rejects_malformed_nested_publication_fields(self) -> None:
        mutations = (
            ("attempt oracle", lambda payload: payload["attempts"][0].__setitem__("oracle_execution_id", 2)),
            ("fact source", lambda payload: payload["facts"][0].__setitem__("source_ref", 2)),
            ("fact scalar", lambda payload: payload["facts"][0].__setitem__("value", {"raw": "private"})),
            ("inference uncertainty", lambda payload: payload["inferences"][0].__setitem__("uncertainty", 2)),
            ("nested object", lambda payload: payload["evidence"].__setitem__(0, "not-an-object")),
            ("string array", lambda payload: payload["facts"][0].__setitem__("evidence_ids", [2])),
        )
        for label, mutate in mutations:
            payload = valid_report().to_dict()
            mutate(payload)
            with self.subTest(label=label), self.assertRaises(ContractValidationError):
                alpha_run_report_from_dict(payload)

    def test_terminal_status_classification_and_acceptance_reconcile(self) -> None:
        report = valid_report()
        invalid = (
            replace(report, terminal=False),
            replace(report, classification=RunClassification.TEST_FAILURE),
            replace(report, functional_result=None),
            replace(report, artifacts=()),
            replace(
                report,
                functional_result=replace(report.functional_result, accepted=False),
            ),
        )
        for candidate in invalid:
            with self.subTest(candidate=candidate), self.assertRaises(ContractValidationError):
                candidate.validate()

    def test_traceability_rejects_unknown_and_fabricated_links(self) -> None:
        report = valid_report()
        fabricated = ReportTraceLink(
            "RSK-001", "SCN-001", TraceLinkKind.DERIVED_FROM_REQUIREMENT
        )
        with self.assertRaisesRegex(ContractValidationError, "inconsistent"):
            replace(report, traceability_links=report.traceability_links + (fabricated,)).validate()

        unknown = replace(
            report.traceability_links[0], target_id="BEH-999"
        )
        with self.assertRaisesRegex(ContractValidationError, "unknown node"):
            replace(report, traceability_links=(unknown,) + report.traceability_links[1:]).validate()

        bad_artifact = replace(report.artifacts[0], scenario_ids=("SCN-999",))
        with self.assertRaisesRegex(ContractValidationError, "unknown ids"):
            replace(report, artifacts=(bad_artifact,)).validate()

    def test_inference_and_recommendation_references_are_closed(self) -> None:
        report = valid_report()
        inference = replace(report.inferences[0], basis_fact_ids=("FACT-UNKNOWN",))
        with self.assertRaisesRegex(ContractValidationError, "unknown ids"):
            replace(report, inferences=(inference,)).validate()

        recommendation = replace(
            report.recommendations[0],
            related_inference_ids=(),
            limitation_codes=(),
        )
        with self.assertRaisesRegex(ContractValidationError, "requires an inference"):
            replace(report, recommendations=(recommendation,)).validate()

        payload = report.to_dict()
        payload["recommendations"][0]["recommendation_code"] = "CALL_PROVIDER_AGAIN"
        with self.assertRaisesRegex(ContractValidationError, "invalid Alpha report"):
            alpha_run_report_from_dict(payload)

    def test_evidence_is_contained_sanitized_and_integrity_is_explicit(self) -> None:
        report = valid_report()
        for path in ("../state.json", "C:/state.json", "state\\report.json", "a//b"):
            with self.subTest(path=path), self.assertRaises(ContractValidationError):
                replace(report.evidence[0], relative_path=path).validate()

        with self.assertRaisesRegex(ContractValidationError, "must be sanitized"):
            replace(report.evidence[0], sanitized=False).validate()

        missing = replace(
            report.evidence[0],
            integrity_status=EvidenceIntegrityStatus.MISSING,
            publishable=False,
        )
        with self.assertRaisesRegex(ContractValidationError, "requires EVIDENCE_INTEGRITY_FAILURE"):
            replace(report, evidence=(missing,) + report.evidence[1:]).validate()

        integrity_limitation = ReportLimitation(
            "EVIDENCE_INTEGRITY_FAILURE",
            LimitationSeverity.BLOCKING,
            "One evidence reference could not be verified",
        )
        replace(
            report,
            evidence=(missing,) + report.evidence[1:],
            limitations=report.limitations + (integrity_limitation,),
        ).validate()

    def test_public_text_and_scalars_reject_sensitive_or_non_finite_values(self) -> None:
        report = valid_report()
        sensitive = replace(
            report.limitations[0], statement="api_key=not-a-public-value"
        )
        with self.assertRaisesRegex(ContractValidationError, "sensitive"):
            replace(report, limitations=(sensitive,) + report.limitations[1:]).validate()

        invalid_fact = replace(report.facts[0], value=float("nan"))
        with self.assertRaisesRegex(ContractValidationError, "finite"):
            replace(report, facts=(invalid_fact,)).validate()

        unobserved = replace(
            report.facts[0],
            observation_status=ReportObservationStatus.NOT_OBSERVED,
        )
        with self.assertRaisesRegex(ContractValidationError, "cannot carry"):
            replace(report, facts=(unobserved,)).validate()

    def test_attempt_ids_and_functional_counters_reconcile(self) -> None:
        report = valid_report()
        attempt = replace(
            report.attempts[0], oracle_execution_id="EXEC-ATTEMPT-002-oracle"
        )
        with self.assertRaisesRegex(ContractValidationError, "does not reconcile"):
            replace(report, attempts=(attempt,)).validate()

        functional = replace(report.functional_result, tests=2)
        with self.assertRaisesRegex(ContractValidationError, "counters do not reconcile"):
            replace(report, functional_result=functional).validate()

        accepted_with_skips = replace(
            report.functional_result,
            tests=2,
            passed=1,
            skipped=1,
        )
        with self.assertRaisesRegex(ContractValidationError, "must fully pass"):
            replace(report, functional_result=accepted_with_skips).validate()

    def test_trace_ids_links_attempts_and_capabilities_are_unique_and_complete(self) -> None:
        report = valid_report()
        missing_link = tuple(
            link
            for link in report.traceability_links
            if link.kind is not TraceLinkKind.COVERS_SCENARIO
        )
        with self.assertRaisesRegex(ContractValidationError, "lacks a trace link"):
            replace(report, traceability_links=missing_link).validate()

        missing_execution = tuple(
            node
            for node in report.traceability_nodes
            if node.kind is not TraceNodeKind.EXECUTION
        )
        links_without_execution = tuple(
            link
            for link in report.traceability_links
            if link.kind is not TraceLinkKind.EXECUTES_ARTIFACT
        )
        with self.assertRaisesRegex(ContractValidationError, "lacks generated execution"):
            replace(
                report,
                traceability_nodes=missing_execution,
                traceability_links=links_without_execution,
            ).validate()

        duplicate_attempt = report.attempts + (report.attempts[0],)
        with self.assertRaisesRegex(ContractValidationError, "attempts must be unique"):
            replace(report, attempts=duplicate_attempt).validate()

        duplicate_quality = report.quality + (report.quality[0],)
        with self.assertRaisesRegex(ContractValidationError, "capabilities must be unique"):
            replace(report, quality=duplicate_quality).validate()

        gap = replace(report.traceability_nodes[3], node_id="SCN-002")
        nodes = report.traceability_nodes[:3] + (gap,) + report.traceability_nodes[4:]
        links = tuple(
            replace(link, target_id="SCN-002")
            if link.target_id == "SCN-001"
            else link
            for link in report.traceability_links
        )
        artifact = replace(report.artifacts[0], scenario_ids=("SCN-002",))
        with self.assertRaisesRegex(ContractValidationError, "must be contiguous"):
            replace(
                report,
                traceability_nodes=nodes,
                traceability_links=links,
                artifacts=(artifact,),
            ).validate()

    def test_publishable_evidence_must_be_verified_and_observed_fact_has_value(self) -> None:
        report = valid_report()
        unchecked = replace(
            report.evidence[0], integrity_status=EvidenceIntegrityStatus.NOT_CHECKED
        )
        with self.assertRaisesRegex(ContractValidationError, "must be verified"):
            unchecked.validate()

        empty_fact = replace(report.facts[0], value=None)
        with self.assertRaisesRegex(ContractValidationError, "requires a value"):
            replace(report, facts=(empty_fact,)).validate()

    def test_schema_is_packaged_strict_and_aligned_with_public_enums(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(valid_report().to_dict())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], REPORT_SCHEMA_VERSION)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        self.assertEqual(
            set(schema["properties"]["status"]["enum"]),
            {item.value for item in RunStatus},
        )
        self.assertEqual(
            set(schema["properties"]["classification"]["enum"]),
            {item.value for item in RunClassification},
        )
        self.assertEqual(
            set(schema["$defs"]["recommendation"]["properties"]["recommendation_code"]["enum"]),
            {item.value for item in ReportRecommendationCode},
        )

    def test_contract_module_remains_framework_and_tooling_neutral(self) -> None:
        source = (ROOT / "src" / "asef" / "report_contracts.py").read_text(
            encoding="utf-8"
        )
        for forbidden in (
            "import docker",
            "import openai",
            "import pytest",
            "import coverage",
            "import mutmut",
            "import langgraph",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
