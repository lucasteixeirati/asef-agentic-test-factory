from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ..api_contracts import (
    ApiExecutionResult,
    ApiScenarioResult,
    api_execution_result_from_dict,
    api_plan_from_dict,
    ApiTestPlan,
)
from ..languages import get_language_profile
from .docker import CommandExecutor, DockerPolicy, DockerRunner


class DockerApiFixtureExecutor:
    """Conformance-only executor for a fixture living inside a networkless container."""

    command = (
        "python",
        "-B",
        "/workspace/driver.py",
        "/workspace/plan.json",
        "/asef-output/api-result.json",
    )

    def __init__(
        self,
        allowed_workspace_root: Path,
        executor: CommandExecutor = subprocess.run,
        *,
        timeout_seconds: int = 30,
    ) -> None:
        self.allowed_workspace_root = allowed_workspace_root
        self.executor = executor
        self.timeout_seconds = timeout_seconds

    def execute(self, workspace: Path, output_dir: Path) -> ApiExecutionResult:
        plan = api_plan_from_dict(json.loads((workspace / "plan.json").read_text(encoding="utf-8")))
        runner = DockerRunner(
            DockerPolicy(
                image=get_language_profile("python-pytest").image,
                capability_id="backend-api-fixture",
                allowed_workspace_root=self.allowed_workspace_root,
                cpus=1,
                memory="128m",
                pids_limit=32,
                timeout_seconds=self.timeout_seconds,
                stdout_limit_bytes=32 * 1024,
                stderr_limit_bytes=32 * 1024,
            ),
            self.executor,
        )
        native_path = output_dir / "api-result.json"
        native_path.unlink(missing_ok=True)
        container = runner.run(workspace, list(self.command), output_dir=output_dir)
        if container.exit_code != 0 or not native_path.is_file():
            return self._infrastructure_result(plan.plan_id, tuple(item.scenario_id for item in plan.scenarios))
        try:
            return api_execution_result_from_dict(json.loads(native_path.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return self._infrastructure_result(plan.plan_id, tuple(item.scenario_id for item in plan.scenarios))

    @staticmethod
    def stage(plan: ApiTestPlan, root: Path) -> tuple[Path, Path]:
        plan.validate()
        workspace = root / "workspace"
        output = root / "output"
        workspace.mkdir(parents=True, exist_ok=False)
        output.mkdir(parents=True, exist_ok=False)
        source = Path(__file__).resolve().parents[1] / "fixtures" / "api_fixture_driver.py"
        if not source.is_file():
            raise OSError("packaged API fixture driver is unavailable")
        shutil.copyfile(source, workspace / "driver.py")
        (workspace / "plan.json").write_text(
            json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return workspace, output

    @staticmethod
    def _infrastructure_result(plan_id: str, scenario_ids: tuple[str, ...]) -> ApiExecutionResult:
        return ApiExecutionResult(
            plan_id=plan_id,
            status="ERROR",
            tests=len(scenario_ids),
            passed=0,
            failed=0,
            errors=len(scenario_ids),
            scenarios=tuple(
                ApiScenarioResult(item, "ERROR", None, 0, 0, "SANDBOX_EXECUTION_ERROR")
                for item in scenario_ids
            ),
        )
