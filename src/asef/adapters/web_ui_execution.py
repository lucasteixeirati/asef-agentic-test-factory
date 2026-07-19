from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from ..skills.web_ui import WebUiPolicy, WebUiSkill
from ..web_ui_contracts import (
    WebUiExecutionResult,
    WebUiScenarioResult,
    WebUiTestPlan,
    web_ui_execution_result_from_dict,
    web_ui_plan_from_dict,
)
from .docker import CommandExecutor, DockerPolicy, DockerRunner
from .web_ui_compiler import WebUiPlanCompiler
from .web_ui_toolchain import WEB_UI_IMAGE


MAX_RESULT_BYTES = 256 * 1024
MAX_SCREENSHOT_BYTES = 2 * 1024 * 1024
_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


class DockerWebUiExecutor:
    command = ("run",)

    def __init__(
        self,
        allowed_workspace_root: Path,
        executor: CommandExecutor = subprocess.run,
        *,
        image: str = WEB_UI_IMAGE,
        timeout_seconds: int = 90,
    ) -> None:
        self.allowed_workspace_root = allowed_workspace_root
        self.executor = executor
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.last_image_id: str | None = None

    @staticmethod
    def stage(plan: WebUiTestPlan, root: Path) -> tuple[Path, Path]:
        DockerWebUiExecutor._validate_policy(plan)
        artifact = WebUiPlanCompiler.compile(plan)
        workspace = root / "workspace"
        output = root / "output"
        generated = workspace / "generated"
        fixture = workspace / "fixture"
        screenshots = output / "screenshots"
        generated.mkdir(parents=True, exist_ok=False)
        fixture.mkdir(parents=True, exist_ok=False)
        screenshots.mkdir(parents=True, exist_ok=False)
        source_fixture = Path(__file__).resolve().parents[3] / "examples" / "web-ui"
        for name in ("index.html", "app.js", "styles.css", "conformance.html"):
            source = source_fixture / name
            if not source.is_file():
                raise OSError(f"packaged Web UI fixture asset is unavailable: {name}")
            shutil.copyfile(source, fixture / name)
        (workspace / "plan.json").write_text(
            json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (generated / "web-ui-plan.ts").write_text(
            artifact.source, encoding="utf-8", newline="\n"
        )
        native = output / "web-ui-result.json"
        native.write_text("", encoding="utf-8")
        native.chmod(0o666)
        screenshots.chmod(0o777)
        return workspace, output

    def execute(self, workspace: Path, output: Path) -> WebUiExecutionResult:
        plan = self._validate_staged_inputs(workspace)
        native = output / "web-ui-result.json"
        native.write_text("", encoding="utf-8")
        native.chmod(0o666)
        image_id = self._resolve_image_id()
        self.last_image_id = image_id
        result = DockerRunner(
            DockerPolicy(
                image=image_id,
                capability_id="web-ui-execution",
                allowed_workspace_root=self.allowed_workspace_root,
                cpus=1,
                memory="512m",
                pids_limit=128,
                timeout_seconds=self.timeout_seconds,
                stdout_limit_bytes=64 * 1024,
                stderr_limit_bytes=64 * 1024,
            ),
            self.executor,
        ).run(workspace, list(self.command), output_dir=output)
        if result.timed_out or not result.cleanup_succeeded:
            return self._infrastructure_result(plan)
        try:
            if not native.is_file() or not 0 < native.stat().st_size <= MAX_RESULT_BYTES:
                raise ValueError("missing or oversized Web UI result")
            raw = json.loads(native.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
            execution = web_ui_execution_result_from_dict(raw)
            if execution.plan_id != plan.plan_id:
                raise ValueError("Web UI result plan identity mismatch")
            expected_ids = tuple(item.scenario_id for item in plan.scenarios)
            if tuple(item.scenario_id for item in execution.scenarios) != expected_ids:
                raise ValueError("Web UI result scenario identities mismatch")
            self._validate_screenshots(execution, output)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return self._infrastructure_result(plan)
        if result.exit_code == 0 and execution.status == "PASSED":
            return execution
        if result.exit_code == 1 and execution.status != "PASSED":
            return execution
        return self._infrastructure_result(plan)

    @staticmethod
    def _validate_staged_inputs(workspace: Path) -> WebUiTestPlan:
        raw = json.loads((workspace / "plan.json").read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
        plan = web_ui_plan_from_dict(raw)
        DockerWebUiExecutor._validate_policy(plan)
        artifact = WebUiPlanCompiler.compile(plan)
        actual = (workspace / artifact.path).read_bytes()
        if hashlib.sha256(actual).hexdigest() != artifact.sha256 or actual != artifact.source.encode("utf-8"):
            raise ValueError("compiled Web UI artifact does not match the reviewed plan")
        return plan

    @staticmethod
    def _validate_policy(plan: WebUiTestPlan) -> None:
        WebUiSkill(WebUiPolicy(allowed_hosts=("127.0.0.1",), allowed_ports=(4173,))).validate(plan)

    @staticmethod
    def _validate_screenshots(result: WebUiExecutionResult, output: Path) -> None:
        referenced: set[Path] = set()
        for scenario in result.scenarios:
            if scenario.screenshot_ref is None:
                continue
            target = (output / scenario.screenshot_ref).resolve(strict=True)
            target.relative_to(output.resolve(strict=True))
            if not target.is_file() or not 8 <= target.stat().st_size <= MAX_SCREENSHOT_BYTES:
                raise ValueError("Web UI screenshot is missing or oversized")
            if target.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError("Web UI screenshot is not a PNG")
            referenced.add(target)
        existing = {item.resolve() for item in (output / "screenshots").glob("*.png") if item.is_file()}
        if existing != referenced:
            raise ValueError("unreferenced Web UI screenshot evidence")

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
            raise OSError(f"Web UI tool image {self.image!r} is unavailable or invalid")
        return image_id

    @staticmethod
    def _infrastructure_result(plan: WebUiTestPlan) -> WebUiExecutionResult:
        scenarios = tuple(
            WebUiScenarioResult(item.scenario_id, "ERROR", 0, "SANDBOX_EXECUTION_ERROR")
            for item in plan.scenarios
        )
        return WebUiExecutionResult(
            plan_id=plan.plan_id,
            status="ERROR",
            tests=len(scenarios),
            passed=0,
            failed=0,
            errors=len(scenarios),
            timeouts=0,
            policy_blocked=0,
            scenarios=scenarios,
        )


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key in Web UI execution input: {key}")
        value[key] = item
    return value


def web_ui_functional_fingerprint(result: WebUiExecutionResult) -> str:
    """Return a stable oracle fingerprint, excluding timing and private file names."""
    result.validate()
    functional = {
        "schema_version": result.schema_version,
        "plan_id": result.plan_id,
        "status": result.status,
        "counters": {
            "tests": result.tests,
            "passed": result.passed,
            "failed": result.failed,
            "errors": result.errors,
            "timeouts": result.timeouts,
            "policy_blocked": result.policy_blocked,
        },
        "scenarios": [
            {
                "scenario_id": item.scenario_id,
                "status": item.status,
                "diagnostic_code": item.diagnostic_code,
                "failed_step_id": item.failed_step_id,
                "has_private_screenshot": item.screenshot_ref is not None,
            }
            for item in result.scenarios
        ],
    }
    encoded = json.dumps(functional, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
