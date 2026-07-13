from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from asef.application.ports import ExecutionOutput
from asef.cli import main


Path(".asef").mkdir(exist_ok=True)


class SuccessfulExecution:
    def execute(self, workspace: Path, snapshot: object) -> ExecutionOutput:
        del workspace, snapshot
        return ExecutionOutput(
            image="python@sha256:" + "a" * 64,
            command=("python", "-B", "-m", "unittest"),
            exit_code=0,
            duration_ms=10,
            stdout="",
            stderr="Ran 4 tests in 0.001s\n\nOK\n",
            tests=4,
            passed=4,
            failed=0,
        )


class MissingDockerExecution:
    def execute(self, workspace: Path, snapshot: object) -> ExecutionOutput:
        del workspace, snapshot
        raise FileNotFoundError("docker unavailable")


class FailedTestExecution:
    def execute(self, workspace: Path, snapshot: object) -> ExecutionOutput:
        del workspace, snapshot
        return ExecutionOutput(
            image="python@sha256:" + "a" * 64,
            command=("python", "-B", "-m", "unittest"),
            exit_code=1,
            duration_ms=10,
            stdout="",
            stderr="Ran 4 tests in 0.001s\n\nFAILED (failures=1)\n",
            tests=4,
            passed=3,
            failed=1,
        )


def invoke(arguments: list[str]) -> tuple[int, dict, str]:
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(arguments)
    return code, json.loads(stdout.getvalue()), stderr.getvalue()


class PublicExitCodeMatrixTests(unittest.TestCase):
    def test_installed_cli_defaults_work_outside_repository_tree(self) -> None:
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as directory, patch(
            "asef.cli.DockerUnitTestAdapter", return_value=SuccessfulExecution()
        ):
            try:
                os.chdir(directory)
                code, payload, stderr = invoke(["run"])
                self.assertEqual((code, payload["status"]), (0, "SUCCEEDED"))
                self.assertEqual(stderr, "")
                self.assertTrue(Path(payload["report_path"]).is_file())
                self.assertTrue(Path(".asef/demo/v1/context.json").is_file())
            finally:
                os.chdir(original)

    def test_exit_zero_for_accepted_run(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory, patch(
            "asef.cli.DockerUnitTestAdapter", return_value=SuccessfulExecution()
        ):
            code, payload, _ = invoke(["run", "--output", directory])
            self.assertEqual((code, payload["status"]), (0, "SUCCEEDED"))

    def test_ws003_invalid_context_returns_two_before_run(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            code, payload, stderr = invoke(
                ["run", "--context", "missing-context.json", "--output", directory]
            )
            self.assertEqual(code, 2)
            self.assertEqual(payload["classification"], "INPUT_OR_CONTEXT_ERROR")
            self.assertIn("does not exist", stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_functional_failure_returns_four(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory, patch(
            "asef.cli.DockerUnitTestAdapter", return_value=FailedTestExecution()
        ):
            code, payload, _ = invoke(["run", "--output", directory])
            self.assertEqual(code, 4)
            self.assertEqual(payload["classification"], "TEST_FAILURE")

    def test_ws004_path_escape_returns_five_without_workspace(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            code, payload, _ = invoke(
                [
                    "generate",
                    "--output",
                    directory,
                    "--artifact-cassette",
                    "tests/fixtures/cassettes/wf001_unit_artifact_path_escape.json",
                ]
            )
            self.assertEqual(code, 5)
            self.assertEqual(payload["status"], "POLICY_BLOCKED")
            run_dir = Path(payload["run_dir"])
            self.assertFalse((run_dir / "workspace").exists())

    def test_ws005_repeated_invalid_output_returns_six(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            code, payload, _ = invoke(
                [
                    "generate",
                    "--output",
                    directory,
                    "--artifact-cassette",
                    "tests/fixtures/cassettes/wf001_unit_artifact_invalid_shape.json",
                ]
            )
            self.assertEqual(code, 6)
            self.assertEqual(payload["status"], "BUDGET_EXHAUSTED")
            state = json.loads((Path(payload["run_dir"]) / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["usage"]["provider_retries"], 1)
            self.assertEqual(state["usage"]["model_calls"], 3)
            self.assertEqual(len(state["errors"]), 2)

    def test_ws006_missing_docker_returns_seven_with_report(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory, patch(
            "asef.cli.DockerUnitTestAdapter", return_value=MissingDockerExecution()
        ):
            code, payload, _ = invoke(["run", "--output", directory])
            self.assertEqual(code, 7)
            self.assertEqual(payload["classification"], "INFRASTRUCTURE_ERROR")
            self.assertTrue(Path(payload["report_path"]).is_file())


if __name__ == "__main__":
    unittest.main()
