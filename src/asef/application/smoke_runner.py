from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from ..contracts import ContractValidationError, SkeletonRunRequest
from ..smoke_contracts import (
    LoadedSmokeCase,
    LoadedSmokeDataset,
    SmokeActualUsage,
    SmokeCaseResult,
    SmokeComparison,
    SmokeObservation,
    SmokeSuiteReport,
    SmokeTerminalAction,
    action_from_evaluation,
    semantic_fingerprint,
)
from .run_alpha_case import AlphaCaseRunResult


SMOKE_LIMITATIONS = (
    "Dataset público, curado e pequeno; não constitui amostra estatística.",
    "O score mede conformidade com expectativas versionadas, não qualidade universal do modelo.",
    "O modo demo usa respostas gravadas e não compara providers ou modelos.",
)


class SmokeCaseExecutionPort(Protocol):
    def execute(
        self,
        loaded: LoadedSmokeCase,
        request: SkeletonRunRequest,
    ) -> AlphaCaseRunResult: ...


class SmokeDatasetPort(Protocol):
    def load(self, dataset_root: str | Path) -> LoadedSmokeDataset: ...

    def read_text_ref(self, ref: str) -> str: ...

    def normalize_ref(self, ref: str | Path) -> str: ...


class SmokeReportStorePort(Protocol):
    def validate_output_root(self, output_root: str | Path) -> Path: ...

    def create_suite(self, output_root: str | Path) -> tuple[str, Path]: ...

    def save_case_result(self, suite_dir: Path, result: SmokeCaseResult) -> Path: ...

    def save_suite(self, suite_dir: Path, report: SmokeSuiteReport) -> tuple[Path, Path]: ...

    def relative_to_workspace(self, path: Path) -> str: ...


@dataclass(slots=True, frozen=True)
class SmokeRunOutput:
    report: SmokeSuiteReport
    suite_dir: Path
    suite_json: Path
    suite_markdown: Path


class SmokeSuiteInfrastructureError(RuntimeError):
    pass


class SmokeSuiteRunner:
    def __init__(
        self,
        loader: SmokeDatasetPort,
        executor: SmokeCaseExecutionPort,
        report_store: SmokeReportStorePort,
        *,
        asef_version: str,
        environment: str,
    ) -> None:
        self.loader = loader
        self.executor = executor
        self.report_store = report_store
        self.asef_version = asef_version
        self.environment = environment

    def run(
        self,
        dataset_root: str | Path,
        output_root: str | Path,
        *,
        repeat: int = 1,
        context_ref: str | Path | None = None,
    ) -> SmokeRunOutput:
        if isinstance(repeat, bool) or not isinstance(repeat, int) or not 1 <= repeat <= 3:
            raise ContractValidationError("smoke repeat must be an integer from 1 to 3")
        self.report_store.validate_output_root(output_root)
        dataset = self.loader.load(dataset_root)
        selected_context = (
            self.loader.normalize_ref(context_ref)
            if context_ref is not None
            else dataset.cases[0].demo.context_ref
        )
        if any(item.demo.context_ref != selected_context for item in dataset.cases):
            raise ContractValidationError(
                "--context must match the versioned context declared by every smoke case"
            )
        try:
            suite_id, suite_dir = self.report_store.create_suite(output_root)
        except (OSError, ContractValidationError) as exc:
            raise SmokeSuiteInfrastructureError("cannot create smoke suite directory") from exc
        results: list[SmokeCaseResult] = []
        for repetition in range(1, repeat + 1):
            for loaded in dataset.cases:
                results.append(
                    self._run_case(loaded, repetition, suite_dir, selected_context)
                )

        results = self._apply_reproducibility(results, repeat)
        try:
            for result in results:
                self.report_store.save_case_result(suite_dir, result)
        except (OSError, ContractValidationError) as exc:
            raise SmokeSuiteInfrastructureError("cannot persist smoke case results") from exc
        report = SmokeSuiteReport(
            suite_id=suite_id,
            asef_version=self.asef_version,
            dataset_hash=dataset.dataset_hash,
            repeat=repeat,
            environment=self.environment,
            results=tuple(results),
            matched=sum(item.comparison is SmokeComparison.MATCHED for item in results),
            mismatched=sum(item.comparison is SmokeComparison.MISMATCH for item in results),
            runner_errors=sum(item.comparison is SmokeComparison.RUNNER_ERROR for item in results),
            limitations=SMOKE_LIMITATIONS,
        )
        try:
            report.validate()
            suite_json, suite_markdown = self.report_store.save_suite(suite_dir, report)
        except (OSError, ContractValidationError) as exc:
            raise SmokeSuiteInfrastructureError("cannot persist smoke suite reports") from exc
        return SmokeRunOutput(report, suite_dir, suite_json, suite_markdown)

    def _run_case(
        self,
        loaded: LoadedSmokeCase,
        repetition: int,
        suite_dir: Path,
        context_ref: str,
    ) -> SmokeCaseResult:
        request = SkeletonRunRequest(
            context_ref=context_ref,
            system_id=loaded.demo.system_id,
            requested_skill="unit",
            requirement_title=loaded.case.title,
            requirement_description=self._requirement(loaded.case.requirement_ref),
            output_root_ref=self.report_store.relative_to_workspace(suite_dir / "runs"),
            execution_mode="demo",
        )
        try:
            outcome = self.executor.execute(loaded, request)
            actual = self._observation(outcome)
            mismatches = self._mismatches(loaded, actual)
            comparison = SmokeComparison.MISMATCH if mismatches else SmokeComparison.MATCHED
            message = "; ".join(mismatches)
            facts = self._semantic_facts(loaded, actual, comparison)
            return SmokeCaseResult(
                case_id=loaded.case.case_id,
                case_version=loaded.case.version,
                repetition=repetition,
                run_id=outcome.state.run_id,
                run_dir_ref=self.report_store.relative_to_workspace(outcome.run_dir),
                expected=loaded.demo.expected,
                actual=actual,
                comparison=comparison,
                semantic_fingerprint=semantic_fingerprint(facts),
                evidence_refs=tuple(outcome.state.evidence_refs),
                message=message,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            message = self._safe_error(exc)
            facts = {
                "case_id": loaded.case.case_id,
                "case_version": loaded.case.version,
                "comparison": SmokeComparison.RUNNER_ERROR.value,
                "error_type": type(exc).__name__,
                "message": message,
            }
            return SmokeCaseResult(
                case_id=loaded.case.case_id,
                case_version=loaded.case.version,
                repetition=repetition,
                run_id=f"runner-error-{repetition:03d}-{loaded.case.case_id.lower()}",
                run_dir_ref=(
                    self.report_store.relative_to_workspace(suite_dir)
                    + f"/runner-errors/repetition-{repetition:03d}/{loaded.case.case_id}"
                ),
                expected=loaded.demo.expected,
                actual=None,
                comparison=SmokeComparison.RUNNER_ERROR,
                semantic_fingerprint=semantic_fingerprint(facts),
                message=message,
            )

    def _requirement(self, ref: str) -> str:
        return self.loader.read_text_ref(ref)

    @staticmethod
    def _observation(outcome: AlphaCaseRunResult) -> SmokeObservation:
        state = outcome.state
        oracle = state.facts.get("oracle")
        oracle_hash = oracle.get("sha256") if isinstance(oracle, dict) else None
        action = (
            action_from_evaluation(outcome.terminal_action)
            if outcome.terminal_action is not None
            else SmokeTerminalAction.NOT_REACHED
        )
        return SmokeObservation(
            status=state.status,
            classification=state.classification,
            action=action,
            usage=SmokeActualUsage(
                model_calls=state.usage.model_calls,
                provider_retries=state.usage.provider_retries,
                corrections=state.usage.test_corrections,
                execution_attempts=outcome.attempts_executed,
            ),
            docker_called=outcome.attempts_executed > 0,
            oracle_executed=isinstance(oracle, dict),
            human_checkpoint_requested=isinstance(state.facts.get("human_checkpoint"), dict),
            artifact_hash=outcome.artifact.content_sha256 if outcome.artifact else None,
            oracle_hash=oracle_hash if isinstance(oracle_hash, str) else None,
        )

    @staticmethod
    def _mismatches(loaded: LoadedSmokeCase, actual: SmokeObservation) -> list[str]:
        expected = loaded.demo.expected
        mismatches: list[str] = []
        for name in ("status", "classification", "action"):
            if getattr(actual, name) is not getattr(expected, name):
                mismatches.append(
                    f"{name}: expected {getattr(expected, name).value}, "
                    f"got {getattr(actual, name).value}"
                )
        for name in ("docker_called", "oracle_executed", "human_checkpoint_requested"):
            if getattr(actual, name) is not getattr(expected, name):
                mismatches.append(
                    f"{name}: expected {getattr(expected, name)}, got {getattr(actual, name)}"
                )
        expected_usage = expected.usage
        for name in ("model_calls", "provider_retries", "corrections", "execution_attempts"):
            expectation = getattr(expected_usage, name)
            value = getattr(actual.usage, name)
            if not expectation.matches(value):
                mismatches.append(
                    f"{name}: expected {expectation.minimum}..{expectation.maximum}, got {value}"
                )
        return mismatches

    @staticmethod
    def _semantic_facts(
        loaded: LoadedSmokeCase,
        actual: SmokeObservation,
        comparison: SmokeComparison,
    ) -> dict[str, object]:
        return {
            "case_id": loaded.case.case_id,
            "case_version": loaded.case.version,
            "demo_schema_version": loaded.demo.schema_version,
            "status": actual.status.value,
            "classification": actual.classification.value,
            "action": actual.action.value,
            "usage": {
                "model_calls": actual.usage.model_calls,
                "provider_retries": actual.usage.provider_retries,
                "corrections": actual.usage.corrections,
                "execution_attempts": actual.usage.execution_attempts,
            },
            "artifact_hash": actual.artifact_hash,
            "oracle_hash": actual.oracle_hash,
            "docker_called": actual.docker_called,
            "oracle_executed": actual.oracle_executed,
            "human_checkpoint_requested": actual.human_checkpoint_requested,
            "comparison": comparison.value,
        }

    @staticmethod
    def _apply_reproducibility(
        results: list[SmokeCaseResult], repeat: int
    ) -> list[SmokeCaseResult]:
        if repeat == 1:
            return results
        fingerprints: dict[str, set[str]] = {}
        for result in results:
            fingerprints.setdefault(result.case_id, set()).add(result.semantic_fingerprint)
        unstable = {case_id for case_id, values in fingerprints.items() if len(values) != 1}
        if not unstable:
            return results
        return [
            replace(
                result,
                comparison=SmokeComparison.MISMATCH,
                message=(result.message + "; " if result.message else "")
                + "semantic fingerprint changed across repetitions",
            )
            if result.case_id in unstable and result.comparison is not SmokeComparison.RUNNER_ERROR
            else result
            for result in results
        ]

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        message = " ".join(str(exc).replace("`", "'").split())
        if not message:
            message = type(exc).__name__
        if ":\\" in message or "file://" in message.lower() or "traceback" in message.lower():
            message = type(exc).__name__
        return message.encode("utf-8")[:500].decode("utf-8", errors="ignore")
