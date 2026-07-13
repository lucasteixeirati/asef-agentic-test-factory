from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..application.ports import AnalysisResult, GeneratedArtifactResult
from ..contracts import SkeletonRunRequest, UnitTestArtifact


class RecordedAgentError(ValueError):
    pass


class RecordedAgentAdapter:
    """Replay two typed model outputs without giving cassettes control over the workflow."""

    def __init__(self, analysis_cassette: Path, artifact_cassette: Path) -> None:
        self.analysis_cassette = analysis_cassette
        self.artifact_cassette = artifact_cassette

    def analyze(self, request: SkeletonRunRequest) -> AnalysisResult:
        del request
        cassette = self._load(self.analysis_cassette, "wf001_analysis")
        output = cassette["output"]
        expected = {"behaviors", "risks", "scenarios", "clarification_required"}
        if set(output) != expected:
            raise RecordedAgentError("analysis cassette has an invalid output shape")
        for key in ("behaviors", "risks", "scenarios"):
            if not isinstance(output[key], list) or not output[key] or not all(
                isinstance(item, str) and item.strip() for item in output[key]
            ):
                raise RecordedAgentError(f"analysis cassette {key} must be non-empty strings")
        if not isinstance(output["clarification_required"], bool):
            raise RecordedAgentError("analysis clarification_required must be boolean")
        usage = cassette.get("usage", {})
        return AnalysisResult(
            behaviors=tuple(output["behaviors"]),
            risks=tuple(output["risks"]),
            scenarios=tuple(output["scenarios"]),
            clarification_required=output["clarification_required"],
            model=str(cassette.get("model", "recorded")),
            response_id=str(cassette.get("response_id", "cassette")),
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
        )

    def generate(
        self,
        request: SkeletonRunRequest,
        analysis: AnalysisResult,
    ) -> GeneratedArtifactResult:
        del request, analysis
        cassette = self._load(self.artifact_cassette, "wf001_unit_artifact")
        output = cassette["output"]
        if set(output) != {"relative_path", "content", "scenario_ids"}:
            raise RecordedAgentError("artifact cassette has an invalid output shape")
        if not isinstance(output["relative_path"], str) or not isinstance(output["content"], str):
            raise RecordedAgentError("artifact path and content must be strings")
        if not isinstance(output["scenario_ids"], list) or not all(
            isinstance(item, str) for item in output["scenario_ids"]
        ):
            raise RecordedAgentError("artifact scenario_ids must be a list of strings")
        try:
            artifact = UnitTestArtifact(
                relative_path=output["relative_path"],
                content=output["content"],
                scenario_ids=tuple(output["scenario_ids"]),
            )
        except (KeyError, TypeError) as exc:
            raise RecordedAgentError(f"artifact cassette violates the contract: {exc}") from exc
        usage = cassette.get("usage", {})
        return GeneratedArtifactResult(
            artifact=artifact,
            model=str(cassette.get("model", "recorded")),
            response_id=str(cassette.get("response_id", "cassette")),
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
        )

    @staticmethod
    def _load(path: Path, schema_name: str) -> dict[str, Any]:
        try:
            cassette = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RecordedAgentError(f"cannot load cassette {path}: {exc}") from exc
        if cassette.get("schema_name") != schema_name:
            raise RecordedAgentError(
                f"cassette schema mismatch: expected {schema_name}, got {cassette.get('schema_name')}"
            )
        if not isinstance(cassette.get("output"), dict):
            raise RecordedAgentError("cassette output must be an object")
        return cassette
