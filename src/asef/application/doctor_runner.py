from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from ..contracts import ContractValidationError
from ..security_contracts import DoctorCheck, DoctorReport


@dataclass(slots=True, frozen=True)
class DoctorRequest:
    mode: str
    output_root: Path
    context_ref: Path | None = None
    profile_id: str = "python-pytest"

    def validate(self) -> None:
        if self.mode not in {"demo", "live"}:
            raise ContractValidationError("doctor mode must be demo or live")
        if self.profile_id != "python-pytest":
            raise ContractValidationError("doctor currently supports only python-pytest")


class DoctorCheckPort(Protocol):
    def execute(self, request: DoctorRequest) -> tuple[DoctorCheck, ...]: ...


class DoctorReportStorePort(Protocol):
    def validate_output_root(self, output_root: str | Path) -> Path: ...
    def save_report(
        self, output_root: str | Path, report: DoctorReport
    ) -> tuple[Path, Path, Path]: ...


@dataclass(slots=True, frozen=True)
class DoctorRunOutput:
    report: DoctorReport
    report_dir: Path
    report_json: Path
    report_markdown: Path


class DoctorInfrastructureError(RuntimeError):
    pass


class DoctorRunner:
    def __init__(
        self,
        checks: DoctorCheckPort,
        report_store: DoctorReportStorePort,
        *,
        asef_version: str,
        python_version: str,
        environment: str,
    ) -> None:
        self.checks = checks
        self.report_store = report_store
        self.asef_version = asef_version
        self.python_version = python_version
        self.environment = environment

    def run(self, request: DoctorRequest) -> DoctorRunOutput:
        request.validate()
        self.report_store.validate_output_root(request.output_root)
        started = perf_counter()
        try:
            checks = self.checks.execute(request)
        except (OSError, ValueError, RuntimeError) as exc:
            raise DoctorInfrastructureError("cannot execute doctor checks") from exc
        report = DoctorReport(
            report_id=f"doctor-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}",
            asef_version=self.asef_version,
            python_version=self.python_version,
            profile_id=request.profile_id,
            mode=request.mode,
            environment=self.environment,
            duration_ms=max(0, round((perf_counter() - started) * 1000)),
            checks=checks,
        )
        report.validate()
        try:
            report_dir, report_json, report_markdown = self.report_store.save_report(
                request.output_root, report
            )
        except (OSError, ContractValidationError) as exc:
            raise DoctorInfrastructureError("cannot persist doctor report") from exc
        return DoctorRunOutput(report, report_dir, report_json, report_markdown)
