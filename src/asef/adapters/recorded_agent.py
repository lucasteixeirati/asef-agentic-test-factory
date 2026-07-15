from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Sequence
from typing import Any

from ..application.ports import AnalysisResult, GeneratedArtifactResult, InvalidAgentOutputError
from ..contracts import SkeletonRunRequest, UnitTestArtifact
from ..evaluation_contracts import CorrectionFeedback


class RecordedAgentError(ValueError):
    pass


class RecordedAgentAdapter:
    """Replay two typed model outputs without giving cassettes control over the workflow."""

    def __init__(
        self,
        analysis_cassette: Path,
        artifact_cassette: Path | None,
        correction_cassettes: Sequence[Path] = (),
    ) -> None:
        self.analysis_cassette = analysis_cassette
        self.artifact_cassette = artifact_cassette
        self.correction_cassettes = tuple(correction_cassettes)
        if len(self.correction_cassettes) > 2:
            raise ValueError("recorded agent allows at most two correction cassettes")
        self._correction_index = 0

    def analyze(self, request: SkeletonRunRequest) -> AnalysisResult:
        del request
        cassette = self._load(self.analysis_cassette, "wf001_analysis")
        output = cassette["output"]
        expected = {"behaviors", "risks", "scenarios", "clarification_required"}
        if set(output) != expected:
            raise InvalidAgentOutputError("analysis cassette has an invalid output shape")
        for key in ("behaviors", "risks", "scenarios"):
            if not isinstance(output[key], list) or not output[key] or not all(
                isinstance(item, str) and item.strip() for item in output[key]
            ):
                raise InvalidAgentOutputError(f"analysis cassette {key} must be non-empty strings")
        if not isinstance(output["clarification_required"], bool):
            raise InvalidAgentOutputError("analysis clarification_required must be boolean")
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
        if self.artifact_cassette is None:
            raise RecordedAgentError("recorded artifact cassette was not declared")
        return self._artifact_result(self.artifact_cassette, "wf001_unit_artifact", attempt=1)

    def correct(
        self,
        request: SkeletonRunRequest,
        previous: UnitTestArtifact,
        feedback: CorrectionFeedback,
    ) -> GeneratedArtifactResult:
        del request, feedback
        if self._correction_index >= len(self.correction_cassettes):
            raise RecordedAgentError("recorded correction cassette sequence is exhausted")
        path = self.correction_cassettes[self._correction_index]
        self._correction_index += 1
        return self._artifact_result(
            path,
            "wf001_unit_correction",
            attempt=previous.attempt + 1,
        )

    def _artifact_result(
        self,
        path: Path,
        schema_name: str,
        *,
        attempt: int,
    ) -> GeneratedArtifactResult:
        cassette = self._load(path, schema_name)
        output = cassette["output"]
        if set(output) != {"relative_path", "content", "scenario_ids"}:
            raise InvalidAgentOutputError("artifact cassette has an invalid output shape")
        if not isinstance(output["relative_path"], str) or not isinstance(output["content"], str):
            raise InvalidAgentOutputError("artifact path and content must be strings")
        if not isinstance(output["scenario_ids"], list) or not all(
            isinstance(item, str) for item in output["scenario_ids"]
        ):
            raise InvalidAgentOutputError("artifact scenario_ids must be a list of strings")
        try:
            artifact = UnitTestArtifact(
                relative_path=output["relative_path"],
                content=output["content"],
                scenario_ids=tuple(output["scenario_ids"]),
                attempt=attempt,
            )
        except (KeyError, TypeError) as exc:
            raise InvalidAgentOutputError(f"artifact cassette violates the contract: {exc}") from exc
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
