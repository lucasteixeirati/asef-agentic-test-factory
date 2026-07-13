from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from asef.adapters.context_file import FileQualityContextAdapter
from asef.adapters.run_store import JsonRunStore
from asef.application.prepare_run import PrepareRunService
from asef.cli import main
from asef.context import ContextValidationError
from asef.contracts import ContextResolution, SkeletonRunRequest
from asef.outcomes import RunStatus


CONTEXT = "examples/context/walking-skeleton-context.json"
Path(".asef").mkdir(exist_ok=True)


def request(**overrides: object) -> SkeletonRunRequest:
    values = {
        "context_ref": CONTEXT,
        "system_id": "calculator-service",
        "requested_skill": "unit",
        "requirement_title": "Add integers",
        "requirement_description": "Return the arithmetic sum of two integers",
    }
    values.update(overrides)
    return SkeletonRunRequest(**values)


class PrepareRunServiceTests(unittest.TestCase):
    def test_prepares_state_snapshot_and_manifest_at_agentic_boundary(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            result = PrepareRunService(
                FileQualityContextAdapter(), JsonRunStore(Path(directory))
            ).execute(request())
            self.assertEqual(result.state.status, RunStatus.ANALYZING_REQUIREMENT)
            self.assertEqual(result.state.context_resolution, ContextResolution.RESOLVED)
            self.assertEqual(
                result.state.facts["sut_manifest"]["authorized_files"], ["calculator.py"]
            )
            self.assertEqual(result.state.classification.value, "UNCLASSIFIED")
            self.assertTrue((result.run_dir / "state.json").is_file())
            self.assertTrue((result.run_dir / "context-snapshot.json").is_file())
            events = (result.run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(json.loads(events[0])["target"], "VALIDATING_INPUT")
            self.assertEqual(json.loads(events[-1])["target"], "ANALYZING_REQUIREMENT")
            manifest = json.loads((result.run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "ANALYZING_REQUIREMENT")

    def test_unknown_system_fails_before_creating_run_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            root = Path(directory)
            service = PrepareRunService(FileQualityContextAdapter(), JsonRunStore(root))
            with self.assertRaisesRegex(ContextValidationError, "unknown system_id"):
                service.execute(request(system_id="missing"))
            self.assertEqual(list(root.iterdir()), [])

    def test_missing_authorized_sut_file_is_rejected(self) -> None:
        adapter = FileQualityContextAdapter()
        context = json.loads(Path(CONTEXT).read_text(encoding="utf-8"))
        context["repositories"][0]["read_scope"] = ["missing.py"]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            context_path = Path(directory) / "context.json"
            context_path.write_text(json.dumps(context), encoding="utf-8")
            with self.assertRaisesRegex(ContextValidationError, "authorized file does not exist"):
                adapter.resolve(request(context_ref=context_path.relative_to(Path.cwd()).as_posix()))

    def test_application_core_has_no_framework_or_filesystem_adapter_imports(self) -> None:
        source = Path("src/asef/application/prepare_run.py").read_text(encoding="utf-8").lower()
        for forbidden in ("langgraph", "openai", "docker", "pydantic_ai", "jsonrunstore"):
            self.assertNotIn(forbidden, source)


class PublicCliTests(unittest.TestCase):
    def test_output_outside_asef_is_rejected_before_run_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(["prepare", "--output", directory])
            self.assertEqual(code, 2)
            self.assertIn("inside the .asef directory", stderr.getvalue())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_prepare_command_returns_machine_readable_result(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(["prepare", "--output", directory])
            payload = json.loads(stdout.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "ANALYZING_REQUIREMENT")
            self.assertEqual(payload["ready_for"], "requirement_analysis")
            self.assertEqual(stderr.getvalue(), "")

    def test_prepare_command_maps_context_error_to_exit_two(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(["prepare", "--system", "missing", "--output", directory])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(stdout.getvalue())["status"], "REJECTED")
            self.assertIn("unknown system_id", stderr.getvalue())
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
