from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from ..application.ports import ExecutionOutput
from ..contracts import (
    ContextSnapshot,
    EvidenceRef,
    NormalizedExecutionResult,
    SkeletonRunState,
    context_snapshot_from_dict,
    state_from_dict,
)


class JsonRunStore:
    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root

    def save_prepared(self, state: SkeletonRunState, snapshot: ContextSnapshot) -> Path:
        run_dir = self.output_root / state.run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        self._write_json(run_dir / "context-snapshot.json", snapshot.to_dict())
        self._write_json(
            run_dir / "manifest.json",
            {
                "schema_version": "1.0.0",
                "run_id": state.run_id,
                "workflow_id": state.workflow_id,
                "workflow_version": state.workflow_version,
                "status": state.status.value,
                "context_snapshot_ref": state.context_snapshot_ref,
            },
        )
        self._write_state_files(run_dir, state)
        return run_dir

    def save_state(self, state: SkeletonRunState) -> None:
        self._write_state_files(self.output_root / state.run_id, state)

    def load_state(self, run_id: str) -> SkeletonRunState:
        return state_from_dict(self._read_run_json(run_id, "state.json"))

    def load_snapshot(self, run_id: str) -> ContextSnapshot:
        return context_snapshot_from_dict(self._read_run_json(run_id, "context-snapshot.json"))

    def save_static_validation(
        self,
        state: SkeletonRunState,
        artifact: Any,
        validation: dict[str, object],
    ) -> None:
        run_dir = self.output_root / state.run_id
        if validation.get("status") == "PASSED":
            artifact_path = (
                run_dir / "artifacts" / f"attempt-{artifact.attempt:03d}" / artifact.relative_path
            )
        else:
            artifact_path = run_dir / "artifacts" / "rejected" / f"attempt-{artifact.attempt:03d}.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(artifact.content, encoding="utf-8")
        results = run_dir / "results"
        results.mkdir(parents=True, exist_ok=True)
        self._write_json(results / "static-validation.json", validation)
        self._write_state_files(run_dir, state)

    def save_execution(
        self,
        state: SkeletonRunState,
        output: ExecutionOutput,
    ) -> NormalizedExecutionResult:
        run_dir = self.output_root / state.run_id
        results = run_dir / "results"
        results.mkdir(parents=True, exist_ok=True)
        stdout_path = results / "stdout.txt"
        stderr_path = results / "stderr.txt"
        stdout_path.write_text(output.stdout, encoding="utf-8")
        stderr_path.write_text(output.stderr, encoding="utf-8")
        stdout_ref = EvidenceRef("stdout", "results/stdout.txt", self._sha256(stdout_path))
        stderr_ref = EvidenceRef("stderr", "results/stderr.txt", self._sha256(stderr_path))
        normalized = NormalizedExecutionResult(
            image=output.image,
            command=output.command,
            exit_code=output.exit_code,
            duration_ms=output.duration_ms,
            stdout_ref=stdout_ref,
            stderr_ref=stderr_ref,
            tests=output.tests,
            passed=output.passed,
            failed=output.failed,
            timed_out=output.timed_out,
            stdout_truncated=output.stdout_truncated,
            stderr_truncated=output.stderr_truncated,
        )
        self._write_json(results / "execution.json", normalized.to_dict())
        return normalized

    def save_report(
        self,
        state: SkeletonRunState,
        execution: NormalizedExecutionResult | None,
        evaluation: dict[str, object],
    ) -> str:
        run_dir = self.output_root / state.run_id
        report = {
            "schema_version": "1.0.0",
            "run_id": state.run_id,
            "workflow_id": state.workflow_id,
            "status": state.status.value,
            "classification": state.classification.value,
            "requirement": {
                "title": state.request.requirement_title,
                "description": state.request.requirement_description,
            },
            "evaluation": evaluation,
            "execution": execution.to_dict() if execution else None,
            "usage": {
                "model_calls": state.usage.model_calls,
                "input_tokens": state.usage.input_tokens,
                "output_tokens": state.usage.output_tokens,
            },
            "evidence_refs": [ref.to_dict() if hasattr(ref, "to_dict") else {
                "kind": ref.kind,
                "relative_path": ref.relative_path,
                "sha256": ref.sha256,
                "schema_version": ref.schema_version,
            } for ref in state.evidence_refs],
        }
        self._write_json(run_dir / "report.json", report)
        title = self._markdown_text(state.request.requirement_title)
        markdown = (
            "# ASEF Run Report\n\n"
            f"- Run: `{state.run_id}`\n"
            f"- Requirement: {title}\n"
            f"- Status: `{state.status.value}`\n"
            f"- Classification: `{state.classification.value}`\n"
            f"- Tests: `{evaluation.get('tests', 'unknown')}`\n"
            f"- Passed: `{evaluation.get('passed', 'unknown')}`\n"
            f"- Failed: `{evaluation.get('failed', 'unknown')}`\n"
            f"- Conclusion: {self._markdown_text(str(evaluation.get('conclusion', '')))}\n"
        )
        (run_dir / "report.md").write_text(markdown, encoding="utf-8")
        self._write_state_files(run_dir, state)
        return "report.md"

    def _write_state_files(self, run_dir: Path, state: SkeletonRunState) -> None:
        self._write_json(run_dir / "state.json", state.to_dict())
        (run_dir / "events.jsonl").write_text(
            "".join(
                json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
                for event in state.history
            ),
            encoding="utf-8",
        )
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["status"] = state.status.value
        manifest["classification"] = state.classification.value
        manifest["usage"] = state.usage.__dict__ if hasattr(state.usage, "__dict__") else {
            "model_calls": state.usage.model_calls,
            "provider_retries": state.usage.provider_retries,
            "input_tokens": state.usage.input_tokens,
            "output_tokens": state.usage.output_tokens,
            "elapsed_ms": state.usage.elapsed_ms,
        }
        manifest["evidence_refs"] = [
            {
                "kind": ref.kind,
                "relative_path": ref.relative_path,
                "sha256": ref.sha256,
                "schema_version": ref.schema_version,
            }
            for ref in state.evidence_refs
        ]
        self._write_json(manifest_path, manifest)

    def _read_run_json(self, run_id: str, filename: str) -> dict[str, Any]:
        if not run_id or any(marker in run_id for marker in ("/", "\\", "..")):
            raise ValueError("invalid run_id")
        run_dir = (self.output_root / run_id).resolve()
        root = self.output_root.resolve()
        if not run_dir.is_relative_to(root):
            raise ValueError("run_id escapes output root")
        try:
            value = json.loads((run_dir / filename).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot load {filename}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{filename} must contain an object")
        return value

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _markdown_text(value: str) -> str:
        sanitized = value.replace("|", "\\|").replace("`", "\\`")
        sanitized = sanitized.replace("<", "&lt;").replace(">", "&gt;")
        return " ".join(sanitized.splitlines()).strip()
