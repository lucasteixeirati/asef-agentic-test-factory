from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from ..application.ports import QualityExecutionOutput
from ..contracts import EvidenceRef, SkeletonRunState
from ..evaluation_contracts import (
    CoverageResult,
    MutationResult,
    QualityCapability,
    QualityCapabilityObservation,
    QualityCapabilityStatus,
    QualityEvaluationReport,
)


class QualityEvidenceStore:
    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root

    def save_execution(
        self,
        state: SkeletonRunState,
        output: QualityExecutionOutput,
    ) -> tuple[QualityCapabilityObservation, tuple[EvidenceRef, ...]]:
        root = self._run_dir(state) / "quality" / output.capability.value
        root.mkdir(parents=True, exist_ok=False)
        refs: list[EvidenceRef] = []

        raw_ref = self._write_optional(
            state,
            root / ("native-coverage.json" if output.capability is QualityCapability.COVERAGE else "native-mutation.json"),
            output.native_result_content,
            "quality-native",
            refs,
        )
        self._write_optional(
            state, root / "driver-result.json", output.driver_result_content, "quality-driver", refs
        )
        stdout_ref = self._write_optional(state, root / "stdout.txt", output.stdout, "stdout", refs)
        stderr_ref = self._write_optional(state, root / "stderr.txt", output.stderr, "stderr", refs)

        metric = None
        status = output.status
        diagnostic_code = output.diagnostic_code
        diagnostic = output.diagnostic
        if output.normalized is not None and raw_ref is not None and status not in {
            QualityCapabilityStatus.UNAVAILABLE,
            QualityCapabilityStatus.FAILED,
        }:
            metric = self._metric(output, raw_ref)
            result_path = root / "result.json"
            self._write_json_once(result_path, metric.to_dict())
            refs.append(self._ref(state, result_path, "quality-result"))
        elif status is QualityCapabilityStatus.COMPLETED:
            status = QualityCapabilityStatus.FAILED
            diagnostic_code = "QUALITY_NORMALIZED_RESULT_MISSING"
            diagnostic = "Completed quality execution did not provide normalizable native evidence"

        observation = QualityCapabilityObservation(
            capability=output.capability,
            status=status,
            tool_id=output.tool_id,
            tool_version=output.tool_version,
            scope=output.request.scope,
            duration_ms=output.duration_ms,
            result=metric,
            raw_result_ref=raw_ref,
            stdout_ref=stdout_ref,
            stderr_ref=stderr_ref,
            diagnostic_code=diagnostic_code,
            diagnostic=diagnostic,
            limitations=(
                "quality metrics do not change the functional run classification",
            ),
        )
        observation.validate()
        observation_path = root / "observation.json"
        self._write_json_once(observation_path, observation.to_dict())
        refs.append(self._ref(state, observation_path, "quality-observation"))
        return observation, tuple(refs)

    def save_evaluation(
        self,
        state: SkeletonRunState,
        report: QualityEvaluationReport,
    ) -> EvidenceRef:
        report.validate()
        path = self._run_dir(state) / "quality" / "quality-evaluation.json"
        self._write_json_once(path, report.to_dict())
        return self._ref(state, path, "quality-evaluation")

    def _metric(
        self,
        output: QualityExecutionOutput,
        raw_ref: EvidenceRef,
    ) -> CoverageResult | MutationResult:
        normalized = output.normalized or {}
        if output.capability is QualityCapability.COVERAGE:
            excluded = int(normalized["excluded_lines"])
            return CoverageResult(
                tool_id=output.tool_id,
                tool_version=output.tool_version,
                scope=output.request.scope,
                lines_covered=int(normalized["lines_covered"]),
                lines_total=int(normalized["lines_total"]),
                branches_covered=int(normalized["branches_covered"]),
                branches_total=int(normalized["branches_total"]),
                duration_ms=output.duration_ms,
                raw_result_ref=raw_ref,
                exclusions=(f"coverage.py reported {excluded} excluded lines",) if excluded else (),
            )
        return MutationResult(
            tool_id=output.tool_id,
            tool_version=output.tool_version,
            scope=output.request.scope,
            mutants_total=int(normalized["mutants_total"]),
            killed=int(normalized["killed"]),
            survived=int(normalized["survived"]),
            invalid=int(normalized["invalid"]),
            timed_out=int(normalized["timed_out"]),
            not_run=int(normalized["not_run"]),
            duration_ms=output.duration_ms,
            max_mutants=output.request.max_mutants or 0,
            timeout_seconds=output.request.timeout_seconds,
            raw_result_ref=raw_ref,
            limitations=(
                f"{int(normalized['deferred'])} discovered mutants were deferred by budget",
            ) if int(normalized["deferred"]) else (),
        )

    def _write_optional(
        self,
        state: SkeletonRunState,
        path: Path,
        content: str | None,
        kind: str,
        refs: list[EvidenceRef],
    ) -> EvidenceRef | None:
        if content is None:
            return None
        self._write_text_once(path, content)
        ref = self._ref(state, path, kind)
        refs.append(ref)
        return ref

    def _run_dir(self, state: SkeletonRunState) -> Path:
        run_dir = (self.output_root / state.run_id).resolve(strict=True)
        if not run_dir.is_relative_to(self.output_root.resolve(strict=True)):
            raise ValueError("quality run directory escapes output root")
        return run_dir

    def _ref(self, state: SkeletonRunState, path: Path, kind: str) -> EvidenceRef:
        relative = path.resolve(strict=True).relative_to(
            (self.output_root / state.run_id).resolve(strict=True)
        ).as_posix()
        return EvidenceRef(kind, relative, hashlib.sha256(path.read_bytes()).hexdigest())

    @staticmethod
    def _write_json_once(path: Path, value: dict[str, object]) -> None:
        content = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        QualityEvidenceStore._write_text_once(path, content)

    @staticmethod
    def _write_text_once(path: Path, content: str) -> None:
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
