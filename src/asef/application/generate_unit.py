from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..contracts import EvidenceRef, SkeletonRunRequest, SkeletonRunState, UnitTestArtifact
from ..outcomes import RunClassification, RunStatus
from ..skills.unit import UnitSkill, UnitSkillPolicyError
from .ports import AgenticTestPort, RunStorePort, WorkspacePort, WorkspaceResult
from .prepare_run import PrepareRunService


@dataclass(slots=True, frozen=True)
class GenerateUnitResult:
    state: SkeletonRunState
    run_dir: Path
    artifact: UnitTestArtifact | None = None
    workspace: WorkspaceResult | None = None


class GenerateUnitTestService:
    """Continue a freshly prepared run through deterministic static validation."""

    def __init__(
        self,
        prepare_service: PrepareRunService,
        agent: AgenticTestPort,
        skill: UnitSkill,
        workspace: WorkspacePort,
        run_store: RunStorePort,
    ) -> None:
        self.prepare_service = prepare_service
        self.agent = agent
        self.skill = skill
        self.workspace = workspace
        self.run_store = run_store

    def execute(self, request: SkeletonRunRequest) -> GenerateUnitResult:
        prepared = self.prepare_service.execute(request)
        state = prepared.state
        analysis = self.agent.analyze(request)
        self._record_usage(state, analysis.input_tokens, analysis.output_tokens)
        state.facts["analysis"] = {
            "behaviors": list(analysis.behaviors),
            "risks": list(analysis.risks),
            "scenarios": list(analysis.scenarios),
            "model": analysis.model,
            "response_id": analysis.response_id,
            "recorded": True,
        }
        if analysis.clarification_required:
            PrepareRunService._move(
                state, RunStatus.WAITING_FOR_CLARIFICATION, "recorded_analysis_requires_clarification"
            )
            state.classification = RunClassification.WAITING_HUMAN
            self.run_store.save_state(state)
            return GenerateUnitResult(state, prepared.run_dir)

        PrepareRunService._move(state, RunStatus.ANALYZING_RISK, "analysis_complete")
        PrepareRunService._move(state, RunStatus.DESIGNING_SCENARIOS, "risks_identified")
        state.facts["test_design"] = {
            "scenario_ids": [f"SCN-{index:03d}" for index, _ in enumerate(analysis.scenarios, 1)],
            "scenario_count": len(analysis.scenarios),
        }
        PrepareRunService._move(state, RunStatus.GENERATING_TESTS, "design_ready")
        generated = self.agent.generate(request, analysis)
        self._record_usage(state, generated.input_tokens, generated.output_tokens)
        artifact = generated.artifact
        state.attempts["test_generation"] = 1

        try:
            expected_scenarios = set(state.facts["test_design"]["scenario_ids"])
            if set(artifact.scenario_ids) != expected_scenarios:
                raise UnitSkillPolicyError(
                    "artifact scenario_ids must exactly match the approved test design"
                )
            validation = self.skill.validate(artifact)
        except UnitSkillPolicyError as exc:
            validation = {
                "schema_version": "1.0.0",
                "status": "POLICY_BLOCKED",
                "skill_id": "unit",
                "message": str(exc),
                "artifact_sha256": artifact.content_sha256,
            }
            state.errors.append({"type": "POLICY_VIOLATION", "message": str(exc)})
            state.classification = RunClassification.POLICY_VIOLATION
            PrepareRunService._move(state, RunStatus.POLICY_BLOCKED, "unit_skill_policy_violation")
            self.run_store.save_static_validation(state, artifact, validation)
            return GenerateUnitResult(state, prepared.run_dir, artifact)

        PrepareRunService._move(state, RunStatus.STATIC_VALIDATION, "artifact_policy_passed")
        workspace = self.workspace.stage(prepared.run_dir, prepared.context, artifact)
        artifact_ref = f"artifacts/attempt-{artifact.attempt:03d}/{artifact.relative_path}"
        state.evidence_refs.append(
            EvidenceRef(kind="unit_test_artifact", relative_path=artifact_ref, sha256=artifact.content_sha256)
        )
        state.facts["artifact"] = {
            "relative_path": artifact_ref,
            "sha256": artifact.content_sha256,
            "scenario_ids": list(artifact.scenario_ids),
            "model": generated.model,
            "response_id": generated.response_id,
        }
        state.facts["workspace"] = {
            "ref": "workspace",
            "copied_files": list(workspace.copied_files),
            "generated_file": workspace.generated_file,
            "sut_original_modified": False,
        }
        state.validate()
        self.run_store.save_static_validation(state, artifact, validation)
        return GenerateUnitResult(state, prepared.run_dir, artifact, workspace)

    @staticmethod
    def _record_usage(state: SkeletonRunState, input_tokens: int, output_tokens: int) -> None:
        state.usage.model_calls += 1
        state.usage.input_tokens += input_tokens
        state.usage.output_tokens += output_tokens
        state.validate()
