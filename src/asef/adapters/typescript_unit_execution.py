from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from time import perf_counter

from ..application.ports import ExecutionOutput
from ..contracts import TestExecutionOutcome
from ..java_unit_contracts import JavaUnitTestPlan, java_unit_plan_from_dict
from ..skills.java_unit import JavaUnitSkill
from .docker import CommandExecutor, DockerPolicy, DockerRunner
from .typescript_unit_compiler import TypeScriptUnitTestCompiler
from .web_ui_toolchain import WEB_UI_IMAGE, NODE_VERSION


class DockerTypeScriptUnitExecutor:
    def __init__(self, allowed_workspace_root: Path, executor: CommandExecutor = subprocess.run,
                 *, image: str = WEB_UI_IMAGE, timeout_seconds: int = 60) -> None:
        self.allowed_workspace_root, self.executor, self.image = allowed_workspace_root, executor, image
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def stage(plan: JavaUnitTestPlan, root: Path) -> tuple[Path, Path]:
        JavaUnitSkill().validate(plan); artifact = TypeScriptUnitTestCompiler.compile(plan)
        workspace, output = root / "workspace", root / "output"
        (workspace / "generated").mkdir(parents=True, exist_ok=False); output.mkdir(parents=True, exist_ok=False)
        (workspace / artifact.path).write_text(artifact.source, encoding="utf-8", newline="\n")
        (workspace / "plan.json").write_text(json.dumps(plan.to_dict(), sort_keys=True), encoding="utf-8")
        output.chmod(0o777); return workspace, output

    def execute(self, workspace: Path, output: Path) -> ExecutionOutput:
        raw = json.loads((workspace / "plan.json").read_text(encoding="utf-8"))
        plan = java_unit_plan_from_dict(raw); artifact = TypeScriptUnitTestCompiler.compile(plan)
        actual = (workspace / artifact.path).read_bytes()
        if actual != artifact.source.encode() or hashlib.sha256(actual).hexdigest() != artifact.sha256:
            raise ValueError("compiled TypeScript artifact does not match reviewed plan")
        inspected = self.executor(["docker", "image", "inspect", self.image, "--format", "{{.Id}}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15, check=False)
        image_id = inspected.stdout.strip().lower()
        if inspected.returncode or not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id): raise OSError("TypeScript unit image unavailable")
        started = perf_counter()
        container = DockerRunner(DockerPolicy(image_id, self.allowed_workspace_root, cpus=1, memory="256m",
            pids_limit=64, timeout_seconds=self.timeout_seconds, capability_id="typescript-unit"), self.executor).run(
                workspace, ["unit-run"], output_dir=output)
        duration = max(0, round((perf_counter() - started) * 1000))
        tap_path = output / "node-unit.tap"
        tap = tap_path.read_text(encoding="utf-8") if tap_path.is_file() and tap_path.stat().st_size <= 1024 * 1024 else None
        tests, passed, failed, outcome = normalize_node_tap(tap, container.exit_code, artifact.test_names, container.timed_out)
        return ExecutionOutput(image_id, ("unit-run",), container.exit_code, duration, container.stdout, container.stderr,
            tests, passed, failed, 0 if tests is not None else None, 0 if tests is not None else None,
            "node-test", NODE_VERSION, outcome, tap, "node-unit.tap" if tap else None,
            "application/tap" if tap else None, container.timed_out, container.stdout_truncated, container.stderr_truncated)


def normalize_node_tap(tap: str | None, exit_code: int, expected_names: tuple[str, ...], timed_out: bool = False):
    if timed_out or exit_code in {124, 125, 126, 127, 137}: return None, None, None, TestExecutionOutcome.INFRASTRUCTURE_ERROR
    if not tap: return None, None, None, TestExecutionOutcome.TOOL_ERROR
    observed = re.findall(r"^(?:ok|not ok) \d+ - (case_[a-z0-9_]+)$", tap, re.MULTILINE)
    failed = len(re.findall(r"^not ok \d+ - case_[a-z0-9_]+$", tap, re.MULTILINE))
    if len(observed) != len(expected_names) or set(observed) != set(expected_names):
        return None, None, None, TestExecutionOutcome.TOOL_ERROR
    tests, passed = len(observed), len(observed) - failed
    outcome = TestExecutionOutcome.PASSED if failed == 0 and exit_code == 0 else (
        TestExecutionOutcome.ASSERTION_FAILURE if failed and exit_code == 1 else TestExecutionOutcome.TOOL_ERROR)
    return tests, passed, failed, outcome
