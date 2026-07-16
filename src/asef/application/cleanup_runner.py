from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..contracts import ContractValidationError
from ..security_contracts import CleanupReport, CleanupRequest


class CleanupExecutionPort(Protocol):
    def execute(self, request: CleanupRequest) -> CleanupReport: ...


class CleanupReportStorePort(Protocol):
    def save(self, report: CleanupReport) -> tuple[Path, Path]: ...


@dataclass(slots=True, frozen=True)
class CleanupRunOutput:
    report: CleanupReport
    report_json: Path
    report_markdown: Path


class CleanupInfrastructureError(RuntimeError):
    pass


class CleanupRunner:
    def __init__(
        self,
        executor: CleanupExecutionPort,
        report_store: CleanupReportStorePort,
    ) -> None:
        self.executor = executor
        self.report_store = report_store

    def run(self, request: CleanupRequest) -> CleanupRunOutput:
        request.validate()
        try:
            report = self.executor.execute(request)
            report.validate()
            report_json, report_markdown = self.report_store.save(report)
        except (OSError, ValueError, RuntimeError, ContractValidationError) as exc:
            raise CleanupInfrastructureError("cleanup execution failed") from exc
        return CleanupRunOutput(report, report_json, report_markdown)
