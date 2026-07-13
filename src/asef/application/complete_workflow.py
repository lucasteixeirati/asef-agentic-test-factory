from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..contracts import NormalizedExecutionResult, SkeletonRunRequest, SkeletonRunState
from ..outcomes import RunClassification, RunStatus
from .generate_unit import GenerateUnitTestService
from .ports import RunStorePort, TestExecutionPort
from .prepare_run import PrepareRunService


@dataclass(slots=True, frozen=True)
class CompleteWorkflowResult:
    state: SkeletonRunState
    run_dir: Path
    report_path: str | None
    execution: NormalizedExecutionResult | None = None


class CompleteWorkflowService:
    def __init__(
        self,
        generation_service: GenerateUnitTestService,
        executor: TestExecutionPort,
        run_store: RunStorePort,
    ) -> None:
        self.generation_service = generation_service
        self.executor = executor
        self.run_store = run_store

    def execute(self, request: SkeletonRunRequest) -> CompleteWorkflowResult:
        generated = self.generation_service.execute(request)
        state = generated.state
        if generated.workspace is None:
            return CompleteWorkflowResult(state, generated.run_dir, None)

        PrepareRunService._move(state, RunStatus.EXECUTING_TESTS, "static_validation_passed")
        try:
            raw = self.executor.execute(generated.workspace.workspace, generated.context.snapshot)
        except (OSError, ValueError) as exc:
            state.errors.append({"type": "INFRASTRUCTURE_ERROR", "message": str(exc)[:500]})
            state.classification = RunClassification.INFRASTRUCTURE_ERROR
            PrepareRunService._move(state, RunStatus.FAILED, "test_infrastructure_failed")
            evaluation = {
                "accepted": False,
                "conclusion": "Test execution infrastructure failed",
                "tests": None,
                "passed": None,
                "failed": None,
            }
            report_path = self.run_store.save_report(state, None, evaluation)
            return CompleteWorkflowResult(state, generated.run_dir, report_path)

        execution = self.run_store.save_execution(state, raw)
        state.evidence_refs.extend([execution.stdout_ref, execution.stderr_ref])
        state.facts["execution"] = {
            "image": execution.image,
            "command": list(execution.command),
            "exit_code": execution.exit_code,
            "duration_ms": execution.duration_ms,
            "tests": execution.tests,
            "passed": execution.passed,
            "failed": execution.failed,
            "timed_out": execution.timed_out,
        }
        PrepareRunService._move(state, RunStatus.EVALUATING_EVIDENCE, "execution_evidence_saved")
        infrastructure_failure = execution.timed_out or execution.exit_code in {125, 126, 127}
        accepted = (
            execution.exit_code == 0
            and not infrastructure_failure
            and execution.tests is not None
            and execution.tests > 0
            and execution.failed == 0
            and execution.passed == execution.tests
        )
        evaluation = {
            "accepted": accepted,
            "conclusion": (
                "Generated tests passed in the isolated runtime"
                if accepted
                else "Generated tests did not satisfy the deterministic acceptance oracle"
            ),
            "tests": execution.tests,
            "passed": execution.passed,
            "failed": execution.failed,
            "timed_out": execution.timed_out,
        }
        state.facts["evaluation"] = evaluation
        PrepareRunService._move(state, RunStatus.GENERATING_REPORT, "evaluation_complete")
        if accepted:
            state.classification = RunClassification.ACCEPTED
            PrepareRunService._move(state, RunStatus.SUCCEEDED, "deterministic_oracle_accepted")
        elif infrastructure_failure:
            state.classification = RunClassification.INFRASTRUCTURE_ERROR
            PrepareRunService._move(state, RunStatus.FAILED, "execution_infrastructure_failure")
        else:
            state.classification = RunClassification.TEST_FAILURE
            PrepareRunService._move(state, RunStatus.FAILED, "deterministic_oracle_rejected")
        report_path = self.run_store.save_report(state, execution, evaluation)
        return CompleteWorkflowResult(state, generated.run_dir, report_path, execution)
