from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from time import perf_counter
from typing import Any

from ..application.ports import QualityExecutionOutput
from ..evaluation_contracts import (
    QualityCapability,
    QualityCapabilityRequest,
    QualityCapabilityStatus,
)
from ..observability import sanitize_text
from .docker import CommandExecutor, DockerPolicy, DockerRunner


QUALITY_IMAGE = "asef/python-quality:coverage-7.10.7-mutmut-3.6.0"
COVERAGE_VERSION = "7.10.7"
MUTMUT_VERSION = "3.6.0"
MAX_NATIVE_BYTES = 4 * 1024 * 1024
MAX_DRIVER_BYTES = 256 * 1024
_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_DRIVER_FIELDS = {
    "schema_version",
    "capability",
    "tool_id",
    "tool_version",
    "status",
    "diagnostic_code",
    "diagnostic",
    "scope",
    "test_paths",
    "pytest_exit_code",
    "native_result",
    "discovered",
    "admitted",
    "deferred",
}


class PythonQualityDockerAdapter:
    def __init__(
        self,
        allowed_workspace_root: Path,
        executor: CommandExecutor = subprocess.run,
        *,
        image: str = QUALITY_IMAGE,
    ) -> None:
        self.allowed_workspace_root = allowed_workspace_root
        self.executor = executor
        self.image = image

    def execute(
        self,
        workspace: Path,
        request: QualityCapabilityRequest,
    ) -> QualityExecutionOutput:
        request.validate()
        if request.execution_environment_ref != self.image:
            raise ValueError("quality request execution environment differs from adapter image")
        expected_tool = "coverage.py" if request.capability is QualityCapability.COVERAGE else "mutmut"
        expected_version = (
            COVERAGE_VERSION if request.capability is QualityCapability.COVERAGE else MUTMUT_VERSION
        )
        if (request.tool_id, request.tool_version) != (expected_tool, expected_version):
            raise ValueError("quality request tool identity differs from the pinned adapter")

        image_id = self._resolve_image_id()
        output_dir = workspace.parent / f"quality-{request.capability.value}-output"
        output_dir.mkdir(mode=0o755, parents=False, exist_ok=False)
        driver_path = output_dir / "driver-result.json"
        native_path = output_dir / (
            "native-coverage.json"
            if request.capability is QualityCapability.COVERAGE
            else "native-mutation.json"
        )
        for path in (driver_path, native_path):
            path.write_text("", encoding="utf-8")
            path.chmod(0o666)

        command = self._command(request)
        started = perf_counter()
        try:
            runner = DockerRunner(
                DockerPolicy(
                    image=image_id,
                    allowed_workspace_root=self.allowed_workspace_root,
                    cpus=1,
                    memory=(
                        "256m" if request.capability is QualityCapability.COVERAGE else "512m"
                    ),
                    pids_limit=(
                        64 if request.capability is QualityCapability.COVERAGE else 128
                    ),
                    timeout_seconds=request.timeout_seconds,
                    stdout_limit_bytes=256 * 1024,
                    stderr_limit_bytes=256 * 1024,
                ),
                self.executor,
            )
            result = runner.run(workspace, list(command), output_dir=output_dir)
            duration_ms = max(0, round((perf_counter() - started) * 1000))
            native_content = self._read_bounded(native_path, MAX_NATIVE_BYTES)
            driver_content = self._read_bounded(driver_path, MAX_DRIVER_BYTES)
            driver = normalize_driver_result(driver_content, request)
            normalization_error: str | None = None
            try:
                normalized = (
                    normalize_coverage_native(native_content, expected_version)
                    if request.capability is QualityCapability.COVERAGE and native_content is not None
                    else normalize_mutation_native(
                        native_content, request.max_mutants or 0, expected_version
                    )
                    if request.capability is QualityCapability.MUTATION and native_content is not None
                    else None
                )
            except ValueError as exc:
                normalized = None
                normalization_error = str(exc)
            if result.timed_out:
                status = QualityCapabilityStatus.BUDGET_EXHAUSTED
                diagnostic_code = "QUALITY_TIME_BUDGET_EXHAUSTED"
                diagnostic = "Quality execution stopped at the configured wall-time budget"
            elif normalization_error is not None:
                status = QualityCapabilityStatus.FAILED
                diagnostic_code = "QUALITY_NATIVE_RESULT_INVALID"
                diagnostic = normalization_error[:500]
            elif driver is None:
                status = QualityCapabilityStatus.FAILED
                diagnostic_code = "QUALITY_DRIVER_RESULT_MISSING"
                diagnostic = "Quality driver did not produce a valid structured result"
            else:
                status = QualityCapabilityStatus(driver["status"])
                diagnostic_code = driver.get("diagnostic_code")
                diagnostic = driver.get("diagnostic")
            return QualityExecutionOutput(
                request=request,
                capability=request.capability,
                status=status,
                image=image_id,
                command=command,
                tool_id=expected_tool,
                tool_version=expected_version,
                duration_ms=duration_ms,
                exit_code=result.exit_code,
                native_result_content=native_content,
                driver_result_content=driver_content,
                normalized=normalized,
                stdout=sanitize_text(result.stdout),
                stderr=sanitize_text(result.stderr),
                diagnostic_code=diagnostic_code,
                diagnostic=diagnostic,
                timed_out=result.timed_out,
                stdout_truncated=result.stdout_truncated,
                stderr_truncated=result.stderr_truncated,
            )
        finally:
            for path in (driver_path, native_path):
                try:
                    path.chmod(0o600)
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
            try:
                output_dir.rmdir()
            except OSError:
                pass

    @staticmethod
    def _command(request: QualityCapabilityRequest) -> tuple[str, ...]:
        if request.capability is QualityCapability.COVERAGE:
            values: list[str] = ["coverage"]
            for path in request.scope:
                values.extend(("--source", path))
            for path in request.test_paths:
                values.extend(("--tests", path))
            return tuple(values)
        values = ["mutation"]
        for path in request.scope:
            values.extend(("--source", path))
        for path in request.test_paths:
            values.extend(("--tests", path))
        values.extend(("--max-mutants", str(request.max_mutants)))
        return tuple(values)

    def _resolve_image_id(self) -> str:
        completed = self.executor(
            ["docker", "image", "inspect", self.image, "--format", "{{.Id}}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        image_id = completed.stdout.strip().lower()
        if completed.returncode != 0 or not _IMAGE_ID.fullmatch(image_id):
            raise OSError(
                f"quality tool image {self.image!r} is unavailable or has an invalid image ID"
            )
        return image_id

    @staticmethod
    def _read_bounded(path: Path, max_bytes: int) -> str | None:
        if not path.is_file() or path.stat().st_size == 0:
            return None
        if path.stat().st_size > max_bytes:
            raise ValueError(f"quality result exceeds {max_bytes} bytes")
        return path.read_text(encoding="utf-8", errors="strict")


def normalize_driver_result(
    content: str | None,
    request: QualityCapabilityRequest,
) -> dict[str, Any] | None:
    if content is None:
        return None
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict) or set(value) - _DRIVER_FIELDS:
        return None
    required = {
        "schema_version",
        "capability",
        "tool_id",
        "tool_version",
        "status",
        "diagnostic_code",
        "diagnostic",
        "native_result",
    }
    if not required.issubset(value) or value["schema_version"] != "1.0.0":
        return None
    if (
        value["capability"] != request.capability.value
        or value["tool_id"] != request.tool_id
        or value["tool_version"] != request.tool_version
    ):
        return None
    try:
        QualityCapabilityStatus(value["status"])
    except (TypeError, ValueError):
        return None
    for name in ("diagnostic_code", "diagnostic", "native_result"):
        if value[name] is not None and not isinstance(value[name], str):
            return None
    return value


def normalize_coverage_native(content: str, tool_version: str) -> dict[str, object]:
    value = _json_object(content, "coverage")
    meta = value.get("meta")
    totals = value.get("totals")
    if not isinstance(meta, dict) or not isinstance(totals, dict):
        raise ValueError("coverage JSON requires meta and totals objects")
    if meta.get("version") != tool_version or meta.get("branch_coverage") is not True:
        raise ValueError("coverage JSON tool version or branch mode differs from request")
    names = (
        "covered_lines",
        "num_statements",
        "covered_branches",
        "num_branches",
        "excluded_lines",
    )
    counts = {name: _non_negative_int(totals.get(name), f"coverage {name}") for name in names}
    if counts["covered_lines"] > counts["num_statements"]:
        raise ValueError("coverage covered_lines exceeds num_statements")
    if counts["covered_branches"] > counts["num_branches"]:
        raise ValueError("coverage covered_branches exceeds num_branches")
    return {
        "lines_covered": counts["covered_lines"],
        "lines_total": counts["num_statements"],
        "branches_covered": counts["covered_branches"],
        "branches_total": counts["num_branches"],
        "excluded_lines": counts["excluded_lines"],
    }


def normalize_mutation_native(
    content: str,
    max_mutants: int,
    tool_version: str,
) -> dict[str, object]:
    value = _json_object(content, "mutation")
    if (
        value.get("schema_version") != "1.0.0"
        or value.get("tool_id") != "mutmut"
        or value.get("tool_version") != tool_version
        or value.get("max_mutants") != max_mutants
    ):
        raise ValueError("mutation result identity or budget differs from request")
    names = (
        "mutants_total",
        "admitted",
        "deferred",
        "killed",
        "survived",
        "invalid",
        "timed_out",
        "not_run",
    )
    counts = {name: _non_negative_int(value.get(name), f"mutation {name}") for name in names}
    if counts["admitted"] > max_mutants:
        raise ValueError("mutation admitted count exceeds max_mutants")
    if counts["admitted"] + counts["deferred"] != counts["mutants_total"]:
        raise ValueError("mutation admission counts do not reconcile")
    outcomes = sum(counts[name] for name in ("killed", "survived", "invalid", "timed_out", "not_run"))
    if outcomes != counts["mutants_total"]:
        raise ValueError("mutation outcome counts do not reconcile")
    if sum(counts[name] for name in ("killed", "survived", "invalid", "timed_out")) > max_mutants:
        raise ValueError("mutation processed count exceeds max_mutants")
    mutants = value.get("mutants")
    if not isinstance(mutants, list) or len(mutants) != counts["mutants_total"]:
        raise ValueError("mutation per-mutant evidence does not reconcile")
    return {name: counts[name] for name in names}


def _json_object(content: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} result is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} result must be an object")
    return value


def _non_negative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value
