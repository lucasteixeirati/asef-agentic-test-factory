from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from xml.etree import ElementTree

from ..application.ports import ExecutionOutput
from ..contracts import ContextSnapshot, TestExecutionOutcome
from .docker import CommandExecutor, DockerPolicy, DockerRunner


PYTEST_IMAGE = "asef/python-pytest:8.3.3"
PYTEST_VERSION = "8.3.3"
MAX_JUNIT_BYTES = 2 * 1024 * 1024
_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(slots=True, frozen=True)
class PytestSummary:
    tests: int | None
    passed: int | None
    failed: int | None
    errors: int | None
    skipped: int | None
    outcome: TestExecutionOutcome


class PytestDockerAdapter:
    command = (
        "python",
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "--basetemp=/tmp/asef-pytest",
        "--junitxml=/asef-output/pytest-junit.xml",
        "tests_generated",
    )

    def __init__(
        self,
        allowed_workspace_root: Path,
        executor: CommandExecutor = subprocess.run,
        *,
        image: str = PYTEST_IMAGE,
        timeout_seconds: int = 60,
    ) -> None:
        self.allowed_workspace_root = allowed_workspace_root
        self.executor = executor
        self.image = image
        self.timeout_seconds = timeout_seconds

    def execute(self, workspace: Path, snapshot: ContextSnapshot) -> ExecutionOutput:
        if snapshot.language_profile != "python-pytest":
            raise ValueError("pytest adapter requires the python-pytest language profile")
        image_id = self._resolve_image_id()
        output_dir = workspace.parent / "pytest-output"
        output_dir.mkdir(mode=0o755, parents=False, exist_ok=False)
        junit_path = output_dir / "pytest-junit.xml"
        junit_path.write_text("", encoding="utf-8")
        try:
            junit_path.chmod(0o666)
            runner = DockerRunner(
                DockerPolicy(
                    image=image_id,
                    allowed_workspace_root=self.allowed_workspace_root,
                    cpus=1,
                    memory="256m",
                    pids_limit=64,
                    timeout_seconds=self.timeout_seconds,
                    stdout_limit_bytes=256 * 1024,
                    stderr_limit_bytes=256 * 1024,
                ),
                self.executor,
            )
            started = perf_counter()
            result = runner.run(workspace, list(self.command), output_dir=output_dir)
            duration_ms = max(0, round((perf_counter() - started) * 1000))
            raw_result = self._read_junit(junit_path)
            summary = normalize_pytest_result(raw_result, result.exit_code, result.timed_out)
            return ExecutionOutput(
                image=image_id,
                command=self.command,
                exit_code=result.exit_code,
                duration_ms=duration_ms,
                stdout=result.stdout,
                stderr=result.stderr,
                tests=summary.tests,
                passed=summary.passed,
                failed=summary.failed,
                errors=summary.errors,
                skipped=summary.skipped,
                tool_id="pytest",
                tool_version=PYTEST_VERSION,
                outcome=summary.outcome,
                raw_result_content=raw_result,
                raw_result_filename="pytest-junit.xml" if raw_result is not None else None,
                raw_result_media_type="application/junit+xml" if raw_result is not None else None,
                timed_out=result.timed_out,
                stdout_truncated=result.stdout_truncated,
                stderr_truncated=result.stderr_truncated,
            )
        finally:
            try:
                junit_path.chmod(0o600)
                junit_path.unlink(missing_ok=True)
                output_dir.rmdir()
            except OSError:
                pass

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
                f"pytest tool image {self.image!r} is unavailable or has an invalid image ID"
            )
        return image_id

    @staticmethod
    def _read_junit(path: Path) -> str | None:
        if not path.is_file() or path.stat().st_size == 0:
            return None
        if path.stat().st_size > MAX_JUNIT_BYTES:
            raise ValueError(f"pytest JUnit result exceeds {MAX_JUNIT_BYTES} bytes")
        return path.read_text(encoding="utf-8", errors="strict")


def normalize_pytest_result(
    junit_xml: str | None,
    exit_code: int,
    timed_out: bool = False,
) -> PytestSummary:
    if timed_out or exit_code in {124, 125, 126, 127, 137}:
        return PytestSummary(None, None, None, None, None, TestExecutionOutcome.INFRASTRUCTURE_ERROR)
    if junit_xml is None:
        outcome = TestExecutionOutcome.NO_TESTS if exit_code == 5 else TestExecutionOutcome.TOOL_ERROR
        counts = (0, 0, 0, 0, 0) if exit_code == 5 else (None,) * 5
        return PytestSummary(*counts, outcome)

    try:
        tests, failed, errors, skipped = _parse_junit_counts(junit_xml)
    except (ElementTree.ParseError, ValueError):
        return PytestSummary(None, None, None, None, None, TestExecutionOutcome.TOOL_ERROR)
    passed = tests - failed - errors - skipped
    if passed < 0:
        return PytestSummary(None, None, None, None, None, TestExecutionOutcome.TOOL_ERROR)

    if exit_code == 5 or tests == 0:
        outcome = TestExecutionOutcome.NO_TESTS
    elif errors > 0 or exit_code == 2:
        outcome = TestExecutionOutcome.TEST_ERROR
    elif failed > 0 or exit_code == 1:
        outcome = TestExecutionOutcome.ASSERTION_FAILURE
    elif exit_code in {3, 4}:
        outcome = TestExecutionOutcome.TOOL_ERROR
    elif exit_code == 0:
        outcome = TestExecutionOutcome.PASSED
    else:
        outcome = TestExecutionOutcome.TOOL_ERROR
    return PytestSummary(tests, passed, failed, errors, skipped, outcome)


def _parse_junit_counts(value: str) -> tuple[int, int, int, int]:
    if "<!DOCTYPE" in value.upper() or "<!ENTITY" in value.upper():
        raise ValueError("DTD and entities are not accepted in JUnit evidence")
    root = ElementTree.fromstring(value)
    if root.tag == "testsuite":
        suites = [root]
    elif root.tag == "testsuites":
        suites = [child for child in root if child.tag == "testsuite"]
    else:
        raise ValueError("JUnit root must be testsuite or testsuites")
    if not suites:
        raise ValueError("JUnit result contains no testsuite")
    return tuple(
        sum(_non_negative_int(suite.get(attribute, "0"), attribute) for suite in suites)
        for attribute in ("tests", "failures", "errors", "skipped")
    )  # type: ignore[return-value]


def _non_negative_int(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"JUnit {label} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"JUnit {label} cannot be negative")
    return parsed
