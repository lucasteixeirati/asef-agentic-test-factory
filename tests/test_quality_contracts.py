from __future__ import annotations

import unittest
from dataclasses import replace

from asef.contracts import ContractValidationError, EvidenceRef
from asef.evaluation_contracts import (
    CoverageResult,
    MutationResult,
    MutationAdmission,
    QualityCapability,
    QualityCapabilityObservation,
    QualityCapabilityRequest,
    QualityCapabilityStatus,
    QualityEvaluationReport,
    admit_mutants,
)


RAW = EvidenceRef("quality-native", "quality/native.json", "a" * 64)
STDOUT = EvidenceRef("stdout", "quality/stdout.txt", "b" * 64)


def coverage_result() -> CoverageResult:
    return CoverageResult(
        tool_id="coverage.py",
        tool_version="7.10.7",
        scope=("src/reference_sut",),
        lines_covered=8,
        lines_total=10,
        branches_covered=2,
        branches_total=4,
        duration_ms=25,
        raw_result_ref=RAW,
    )


class QualityCapabilityRequestTests(unittest.TestCase):
    def test_coverage_request_is_neutral_and_serializable(self) -> None:
        request = QualityCapabilityRequest(
            capability=QualityCapability.COVERAGE,
            tool_id="coverage.py",
            tool_version="7.10.7",
            scope=("src/reference_sut",),
            test_paths=("tests_generated",),
            timeout_seconds=60,
            execution_environment_ref="python-quality@sha256:fixture",
        )
        self.assertEqual(request.to_dict()["capability"], "coverage")

    def test_mutation_requires_count_budget_and_coverage_rejects_it(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "requires positive"):
            QualityCapabilityRequest(
                QualityCapability.MUTATION,
                "mutmut",
                "3.6.0",
                ("src",),
                ("tests",),
                60,
                "quality-image",
            ).validate()
        with self.assertRaisesRegex(ContractValidationError, "cannot declare"):
            QualityCapabilityRequest(
                QualityCapability.COVERAGE,
                "coverage.py",
                "7.10.7",
                ("src",),
                ("tests",),
                60,
                "quality-image",
                max_mutants=2,
            ).validate()

    def test_paths_are_canonical_contained_and_unique(self) -> None:
        for scope in (("../src",), ("src\\package",), ("src", "src")):
            with self.subTest(scope=scope), self.assertRaises(ContractValidationError):
                QualityCapabilityRequest(
                    QualityCapability.COVERAGE,
                    "coverage.py",
                    "7.10.7",
                    scope,
                    ("tests",),
                    60,
                    "quality-image",
                ).validate()

    def test_request_rejects_invalid_headers_environment_and_schema(self) -> None:
        valid = QualityCapabilityRequest(
            QualityCapability.COVERAGE,
            "coverage.py",
            "7.10.7",
            ("src",),
            ("tests",),
            60,
            "quality-image",
        )
        invalid = (
            replace(valid, schema_version="2.0.0"),
            replace(valid, capability="coverage"),  # type: ignore[arg-type]
            replace(valid, tool_id=""),
            replace(valid, timeout_seconds=0),
            replace(valid, execution_environment_ref=" "),
            replace(valid, execution_environment_ref="image\x00bad"),
            replace(valid, execution_environment_ref="token=value"),
            replace(valid, execution_environment_ref="x" * 301),
            replace(valid, scope=()),
            replace(valid, scope=(".",)),
        )
        for request in invalid:
            with self.subTest(request=request), self.assertRaises(ContractValidationError):
                request.validate()

        for sensitive in ("src/api_key=value", "tests/sk-" + "a" * 24):
            with self.subTest(sensitive=sensitive), self.assertRaisesRegex(
                ContractValidationError, "sensitive"
            ):
                QualityCapabilityRequest(
                    QualityCapability.COVERAGE,
                    "coverage.py",
                    "7.10.7",
                    (sensitive,),
                    ("tests",),
                    30,
                    "quality-image",
                ).validate()


class MutationAdmissionTests(unittest.TestCase):
    def test_admission_is_deterministic_and_happens_before_execution(self) -> None:
        admission = admit_mutants(("z__mutmut_1", "a__mutmut_2", "a__mutmut_1"), 2)
        self.assertEqual(admission.admitted, ("a__mutmut_1", "a__mutmut_2"))
        self.assertEqual(admission.deferred, ("z__mutmut_1",))
        self.assertEqual(admission.to_dict()["max_mutants"], 2)

    def test_admission_rejects_duplicates_empty_names_and_non_positive_budget(self) -> None:
        for names, budget in (
            (("same", "same"), 1),
            (("",), 1),
            (("one",), 0),
        ):
            with self.subTest(names=names, budget=budget), self.assertRaises(
                ContractValidationError
            ):
                admit_mutants(names, budget)

    def test_mutation_result_reconciles_discovered_but_deferred_mutants(self) -> None:
        result = MutationResult(
            "mutmut",
            "3.6.0",
            ("src",),
            10,
            2,
            1,
            0,
            0,
            7,
            100,
            3,
            60,
            RAW,
        )
        result.validate()
        self.assertEqual(result.mutation_score, 66.67)

        with self.assertRaisesRegex(ContractValidationError, "processed mutants"):
            MutationResult(
                "mutmut", "3.6.0", ("src",), 10, 3, 1, 0, 0, 6, 100, 3, 60, RAW
            ).validate()

    def test_admission_contract_rejects_noncanonical_or_incoherent_partitions(self) -> None:
        invalid = (
            MutationAdmission(("a",), ("a",), (), 0),
            MutationAdmission((), (), (), 1),
            MutationAdmission(("a", "a"), ("a",), ("a",), 1),
            MutationAdmission(("a\n",), ("a\n",), (), 1),
            MutationAdmission(("b", "a"), ("b",), ("a",), 1),
            MutationAdmission(("a", "b"), ("a", "b"), (), 1),
            MutationAdmission(("a", "b"), ("a",), (), 1),
        )
        for admission in invalid:
            with self.subTest(admission=admission), self.assertRaises(ContractValidationError):
                admission.validate()


class QualityObservationTests(unittest.TestCase):
    def test_completed_observation_requires_matching_typed_result_and_raw_evidence(self) -> None:
        result = coverage_result()
        observation = QualityCapabilityObservation(
            capability=QualityCapability.COVERAGE,
            status=QualityCapabilityStatus.COMPLETED,
            tool_id="coverage.py",
            tool_version="7.10.7",
            scope=("src/reference_sut",),
            duration_ms=25,
            result=result,
            raw_result_ref=RAW,
            stdout_ref=STDOUT,
        )
        self.assertEqual(observation.to_dict()["result"]["line_percent"], 80.0)

        with self.assertRaisesRegex(ContractValidationError, "differs from result"):
            QualityCapabilityObservation(
                QualityCapability.COVERAGE,
                QualityCapabilityStatus.COMPLETED,
                "coverage.py",
                "7.10.7",
                ("src/reference_sut",),
                26,
                result=result,
                raw_result_ref=RAW,
            ).validate()

    def test_unavailable_does_not_fabricate_metrics(self) -> None:
        unavailable = QualityCapabilityObservation(
            capability=QualityCapability.MUTATION,
            status=QualityCapabilityStatus.UNAVAILABLE,
            tool_id="mutmut",
            tool_version="3.6.0",
            scope=("src/reference_sut",),
            duration_ms=0,
            diagnostic_code="TOOL_IMAGE_UNAVAILABLE",
            diagnostic="The configured quality image is unavailable",
        )
        value = unavailable.to_dict()
        self.assertIsNone(value["result"])

        with self.assertRaisesRegex(ContractValidationError, "cannot contain metrics"):
            QualityCapabilityObservation(
                QualityCapability.MUTATION,
                QualityCapabilityStatus.UNAVAILABLE,
                "mutmut",
                "3.6.0",
                ("src",),
                100,
                result=MutationResult(
                    "mutmut", "3.6.0", ("src",), 1, 1, 0, 0, 0, 0, 100, 1, 60, RAW
                ),
                raw_result_ref=RAW,
                diagnostic_code="TOOL_UNAVAILABLE",
                diagnostic="Tool unavailable",
            ).validate()

    def test_partial_requires_diagnostic_and_report_is_not_complete(self) -> None:
        complete = QualityCapabilityObservation(
            QualityCapability.COVERAGE,
            QualityCapabilityStatus.COMPLETED,
            "coverage.py",
            "7.10.7",
            ("src/reference_sut",),
            25,
            result=coverage_result(),
            raw_result_ref=RAW,
        )
        partial = QualityCapabilityObservation(
            QualityCapability.MUTATION,
            QualityCapabilityStatus.BUDGET_EXHAUSTED,
            "mutmut",
            "3.6.0",
            ("src/reference_sut",),
            60_000,
            diagnostic_code="MUTATION_TIME_BUDGET_EXHAUSTED",
            diagnostic="Mutation stopped at the configured wall-time budget",
        )
        report = QualityEvaluationReport((complete, partial), 60_025)
        self.assertFalse(report.complete)
        self.assertFalse(report.to_dict()["complete"])

        with self.assertRaisesRegex(ContractValidationError, "requires diagnostic"):
            QualityCapabilityObservation(
                QualityCapability.MUTATION,
                QualityCapabilityStatus.PARTIAL,
                "mutmut",
                "3.6.0",
                ("src",),
                1,
            ).validate()

    def test_report_rejects_duplicate_capabilities(self) -> None:
        observation = QualityCapabilityObservation(
            QualityCapability.COVERAGE,
            QualityCapabilityStatus.COMPLETED,
            "coverage.py",
            "7.10.7",
            ("src/reference_sut",),
            25,
            result=coverage_result(),
            raw_result_ref=RAW,
        )
        with self.assertRaisesRegex(ContractValidationError, "unique"):
            QualityEvaluationReport((observation, observation), 50).validate()

    def test_observation_rejects_invalid_identity_status_diagnostics_and_evidence(self) -> None:
        valid = QualityCapabilityObservation(
            QualityCapability.COVERAGE,
            QualityCapabilityStatus.COMPLETED,
            "coverage.py",
            "7.10.7",
            ("src/reference_sut",),
            25,
            result=coverage_result(),
            raw_result_ref=RAW,
        )
        mutation = MutationResult(
            "mutmut", "3.6.0", ("src/reference_sut",), 1, 1, 0, 0, 0, 0, 25, 1, 60, RAW
        )
        invalid = (
            replace(valid, schema_version="2.0.0"),
            replace(valid, capability="coverage"),  # type: ignore[arg-type]
            replace(valid, status="COMPLETED"),  # type: ignore[arg-type]
            replace(valid, tool_version=""),
            replace(valid, scope=()),
            replace(valid, duration_ms=-1),
            replace(valid, result=None),
            replace(valid, result=mutation),
            replace(valid, raw_result_ref=STDOUT),
            replace(valid, limitations=("same", "same")),
        )
        for observation in invalid:
            with self.subTest(observation=observation), self.assertRaises(
                ContractValidationError
            ):
                observation.validate()

        incomplete = replace(
            valid,
            status=QualityCapabilityStatus.PARTIAL,
            diagnostic_code="bad-code",
            diagnostic="partial",
        )
        with self.assertRaisesRegex(ContractValidationError, "diagnostic_code"):
            incomplete.validate()
        with self.assertRaisesRegex(ContractValidationError, "sensitive"):
            replace(
                incomplete,
                diagnostic_code="PARTIAL_RESULT",
                diagnostic="secret=value",
            ).validate()

    def test_report_rejects_empty_invalid_schema_duration_and_limitations(self) -> None:
        for report in (
            QualityEvaluationReport((), 0),
            QualityEvaluationReport((), 0, schema_version="2.0.0"),
        ):
            with self.subTest(report=report), self.assertRaises(ContractValidationError):
                report.validate()

        observation = QualityCapabilityObservation(
            QualityCapability.COVERAGE,
            QualityCapabilityStatus.COMPLETED,
            "coverage.py",
            "7.10.7",
            ("src/reference_sut",),
            25,
            result=coverage_result(),
            raw_result_ref=RAW,
        )
        for report in (
            QualityEvaluationReport((observation,), -1),
            QualityEvaluationReport((observation,), 25, ("same", "same")),
        ):
            with self.subTest(report=report), self.assertRaises(ContractValidationError):
                report.validate()


if __name__ == "__main__":
    unittest.main()
