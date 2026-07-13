from __future__ import annotations

import re
import subprocess
from pathlib import Path
from time import perf_counter

from ..application.ports import ExecutionOutput
from ..contracts import ContextSnapshot
from .docker import CommandExecutor, DockerPolicy, DockerRunner


_RAN = re.compile(r"Ran (\d+) tests? in")
_FAILED = re.compile(r"FAILED \((?:failures=(\d+))?(?:, )?(?:errors=(\d+))?")


class DockerUnitTestAdapter:
    command = ("python", "-B", "-m", "unittest", "discover", "-s", "tests_generated", "-v")

    def __init__(
        self,
        allowed_workspace_root: Path,
        executor: CommandExecutor = subprocess.run,
        *,
        timeout_seconds: int = 60,
    ) -> None:
        self.allowed_workspace_root = allowed_workspace_root
        self.executor = executor
        self.timeout_seconds = timeout_seconds

    def execute(self, workspace: Path, snapshot: ContextSnapshot) -> ExecutionOutput:
        runner = DockerRunner(
            DockerPolicy(
                image=snapshot.image,
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
        result = runner.run(workspace, list(self.command))
        duration_ms = max(0, round((perf_counter() - started) * 1000))
        combined = f"{result.stdout}\n{result.stderr}"
        tests = self._count_tests(combined)
        failed = self._count_failures(combined, result.exit_code, tests)
        passed = tests - failed if tests is not None and failed is not None else None
        return ExecutionOutput(
            image=snapshot.image,
            command=self.command,
            exit_code=result.exit_code,
            duration_ms=duration_ms,
            stdout=result.stdout,
            stderr=result.stderr,
            tests=tests,
            passed=passed,
            failed=failed,
            timed_out=result.timed_out,
            stdout_truncated=result.stdout_truncated,
            stderr_truncated=result.stderr_truncated,
        )

    @staticmethod
    def _count_tests(output: str) -> int | None:
        matches = _RAN.findall(output)
        return int(matches[-1]) if matches else None

    @staticmethod
    def _count_failures(output: str, exit_code: int, tests: int | None) -> int | None:
        if tests is None:
            return None
        if exit_code == 0 and "OK" in output:
            return 0
        match = _FAILED.search(output)
        if not match:
            return tests if exit_code else 0
        return min(tests, sum(int(value or 0) for value in match.groups()))
