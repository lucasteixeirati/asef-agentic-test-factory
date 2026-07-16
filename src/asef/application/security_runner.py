from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..contracts import ContractValidationError, EvidenceRef
from ..security_contracts import (
    LoadedSecurityCase,
    LoadedSecurityDataset,
    SecurityCaseResult,
    SecurityCaseStatus,
    SecurityClassification,
    SecurityExecutionObservation,
    SecuritySuiteReport,
    security_result_fingerprint,
)


SECURITY_LIMITATIONS = (
    "Controles limitados ao perfil Python e ao ambiente registrado.",
    "O resultado não constitui certificação, pentest ou garantia de isolamento absoluto.",
    "Labels e ausência de órfãos validam o lifecycle gerenciado, não o daemon Docker.",
)


class SecurityDatasetPort(Protocol):
    def load(self, dataset_root: str | Path) -> LoadedSecurityDataset: ...
    def read_fixture(self, ref: str) -> str: ...


class SecurityExecutionPort(Protocol):
    def execute(
        self, loaded: LoadedSecurityCase, suite_dir: Path, fixture_text: str
    ) -> SecurityExecutionObservation: ...


class SecurityReportStorePort(Protocol):
    def validate_output_root(self, output_root: str | Path) -> Path: ...
    def create_suite(self, output_root: str | Path) -> tuple[str, Path]: ...
    def save_evidence(
        self, suite_dir: Path, case_id: str, facts: dict[str, object]
    ) -> EvidenceRef: ...
    def save_case_result(self, suite_dir: Path, result: SecurityCaseResult) -> Path: ...
    def save_suite(
        self, suite_dir: Path, report: SecuritySuiteReport
    ) -> tuple[Path, Path]: ...


@dataclass(slots=True, frozen=True)
class SecurityRunOutput:
    report: SecuritySuiteReport
    suite_dir: Path
    suite_json: Path
    suite_markdown: Path


class SecuritySuiteInfrastructureError(RuntimeError):
    pass


class SecuritySuiteRunner:
    def __init__(
        self,
        loader: SecurityDatasetPort,
        executor: SecurityExecutionPort,
        report_store: SecurityReportStorePort,
        *,
        asef_version: str,
        environment: str,
    ) -> None:
        self.loader = loader
        self.executor = executor
        self.report_store = report_store
        self.asef_version = asef_version
        self.environment = environment

    def run(
        self, dataset_root: str | Path, output_root: str | Path
    ) -> SecurityRunOutput:
        self.report_store.validate_output_root(output_root)
        dataset = self.loader.load(dataset_root)
        try:
            suite_id, suite_dir = self.report_store.create_suite(output_root)
        except (OSError, ContractValidationError) as exc:
            raise SecuritySuiteInfrastructureError(
                "cannot create security suite directory"
            ) from exc

        results: list[SecurityCaseResult] = []
        for loaded in dataset.cases:
            fixture = self.loader.read_fixture(loaded.spec.fixture_refs[0])
            try:
                observation = self.executor.execute(loaded, suite_dir, fixture)
            except (OSError, ValueError, RuntimeError) as exc:
                observation = SecurityExecutionObservation(
                    status=SecurityCaseStatus.ERROR,
                    classification=SecurityClassification.INFRASTRUCTURE_ERROR,
                    duration_ms=0,
                    facts={},
                    diagnostic_code="SECURITY_RUNNER_ERROR",
                    diagnostic=type(exc).__name__,
                )
            evidence_refs: tuple[EvidenceRef, ...] = ()
            if observation.status is SecurityCaseStatus.PASSED:
                evidence_refs = (
                    self.report_store.save_evidence(
                        suite_dir, loaded.spec.case_id, observation.facts
                    ),
                )
            fingerprint = security_result_fingerprint(
                case_id=loaded.spec.case_id,
                case_version=loaded.spec.version,
                status=observation.status,
                classification=observation.classification,
                facts=observation.facts,
                diagnostic_code=observation.diagnostic_code,
            )
            result = SecurityCaseResult(
                case_id=loaded.spec.case_id,
                case_version=loaded.spec.version,
                status=observation.status,
                classification=observation.classification,
                duration_ms=observation.duration_ms,
                semantic_fingerprint=fingerprint,
                evidence_refs=evidence_refs,
                facts=observation.facts,
                diagnostic_code=observation.diagnostic_code,
                diagnostic=observation.diagnostic,
            )
            self.report_store.save_case_result(suite_dir, result)
            results.append(result)

        report = SecuritySuiteReport(
            suite_id=suite_id,
            asef_version=self.asef_version,
            dataset_hash=dataset.dataset_hash,
            environment=self.environment,
            duration_ms=sum(item.duration_ms for item in results),
            results=tuple(results),
            passed=sum(item.status is SecurityCaseStatus.PASSED for item in results),
            failed=sum(item.status is SecurityCaseStatus.FAILED for item in results),
            errors=sum(item.status is SecurityCaseStatus.ERROR for item in results),
            unsupported=sum(
                item.status is SecurityCaseStatus.UNSUPPORTED for item in results
            ),
            limitations=SECURITY_LIMITATIONS,
        )
        try:
            suite_json, suite_markdown = self.report_store.save_suite(suite_dir, report)
        except (OSError, ContractValidationError) as exc:
            raise SecuritySuiteInfrastructureError(
                "cannot persist security suite report"
            ) from exc
        return SecurityRunOutput(report, suite_dir, suite_json, suite_markdown)
