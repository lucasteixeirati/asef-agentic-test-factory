from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from asef.adapters.recorded_agent import RecordedAgentAdapter, RecordedAgentError
from asef.application.ports import AnalysisResult, InvalidAgentOutputError
from asef.contracts import SkeletonRunRequest


def request() -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title="Add integers",
        requirement_description="Return the arithmetic sum",
    )


ANALYSIS = AnalysisResult(
    behaviors=("sum",),
    risks=("negative values",),
    scenarios=("two integers",),
    clarification_required=False,
    model="recorded",
    response_id="analysis-1",
)


class RecordedAgentAdversarialTests(unittest.TestCase):
    def test_invalid_json_and_schema_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = root / "invalid.json"
            invalid.write_text("{", encoding="utf-8")
            valid_artifact = self._cassette(root / "artifact.json", "wf001_unit_artifact", {})
            with self.assertRaisesRegex(RecordedAgentError, "cannot load cassette"):
                RecordedAgentAdapter(invalid, valid_artifact).analyze(request())

            mismatch = self._cassette(root / "mismatch.json", "another_schema", {})
            with self.assertRaisesRegex(RecordedAgentError, "schema mismatch"):
                RecordedAgentAdapter(mismatch, valid_artifact).analyze(request())

    def test_analysis_requires_exact_shape_and_typed_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = self._cassette(root / "artifact.json", "wf001_unit_artifact", {})
            cases = (
                ({"behaviors": [], "risks": ["r"], "scenarios": ["s"], "clarification_required": False}, "behaviors"),
                ({"behaviors": ["b"], "risks": ["r"], "scenarios": ["s"], "clarification_required": "no"}, "must be boolean"),
                ({"behaviors": ["b"], "risks": ["r"], "scenarios": ["s"], "clarification_required": False, "extra": True}, "invalid output shape"),
            )
            for index, (output, message) in enumerate(cases):
                with self.subTest(index=index):
                    analysis = self._cassette(
                        root / f"analysis-{index}.json", "wf001_analysis", output
                    )
                    with self.assertRaisesRegex(InvalidAgentOutputError, message):
                        RecordedAgentAdapter(analysis, artifact).analyze(request())

    def test_artifact_requires_safe_typed_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = self._cassette(root / "analysis.json", "wf001_analysis", {})
            cases = (
                ({"relative_path": 7, "content": "x", "scenario_ids": []}, "must be strings"),
                ({"relative_path": "test_x.py", "content": "x", "scenario_ids": "SCN-001"}, "list of strings"),
                ({"relative_path": "test_x.py", "content": "x", "scenario_ids": [], "extra": True}, "invalid output shape"),
            )
            for index, (output, message) in enumerate(cases):
                with self.subTest(index=index):
                    artifact = self._cassette(
                        root / f"artifact-{index}.json", "wf001_unit_artifact", output
                    )
                    with self.assertRaisesRegex(InvalidAgentOutputError, message):
                        RecordedAgentAdapter(analysis, artifact).generate(request(), ANALYSIS)

    def test_non_object_output_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cassette.json"
            path.write_text(
                json.dumps({"schema_name": "wf001_analysis", "output": []}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RecordedAgentError, "output must be an object"):
                RecordedAgentAdapter(path, path).analyze(request())

    @staticmethod
    def _cassette(path: Path, schema: str, output: object) -> Path:
        path.write_text(
            json.dumps({"schema_name": schema, "output": output}),
            encoding="utf-8",
        )
        return path
