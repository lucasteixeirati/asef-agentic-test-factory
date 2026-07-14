from __future__ import annotations

import json
import hashlib
import re
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

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
        artifact_path.write_bytes(artifact.content.encode("utf-8"))
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
        raw_result_ref = None
        if output.raw_result_content is not None:
            filename = output.raw_result_filename or "tool-result.txt"
            if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,100}", filename):
                raise ValueError("raw result filename must be a safe basename")
            raw_path = results / filename
            raw_path.write_text(output.raw_result_content, encoding="utf-8")
            raw_result_ref = EvidenceRef(
                output.raw_result_media_type or "tool-result",
                f"results/{filename}",
                self._sha256(raw_path),
            )
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
            errors=output.errors,
            skipped=output.skipped,
            tool_id=output.tool_id,
            tool_version=output.tool_version,
            outcome=output.outcome,
            raw_result_ref=raw_result_ref,
            timed_out=output.timed_out,
            stdout_truncated=output.stdout_truncated,
            stderr_truncated=output.stderr_truncated,
        )
        self._write_json(results / "execution.json", normalized.to_dict())
        return normalized

    def save_attempt_execution(
        self,
        state: SkeletonRunState,
        output: ExecutionOutput,
        attempt: int,
        role: str,
    ) -> NormalizedExecutionResult:
        if attempt < 0 or attempt > 999:
            raise ValueError("attempt must be between 0 and 999")
        if role not in {"generated", "oracle"}:
            raise ValueError("execution role must be generated or oracle")
        filename = output.raw_result_filename or "tool-result.txt"
        if output.raw_result_content is not None and not re.fullmatch(
            r"[a-z0-9][a-z0-9._-]{0,100}", filename
        ):
            raise ValueError("raw result filename must be a safe basename")

        run_dir = self.output_root / state.run_id
        attempt_dir = run_dir / "attempts" / f"{attempt:03d}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        target = attempt_dir / role
        if target.exists():
            raise FileExistsError(f"execution evidence already exists for attempt {attempt:03d}/{role}")
        temporary = attempt_dir / f".{role}.{uuid4().hex}.tmp"
        temporary.mkdir()
        prefix = f"attempts/{attempt:03d}/{role}"
        try:
            stdout_path = temporary / "stdout.txt"
            stderr_path = temporary / "stderr.txt"
            stdout_path.write_text(output.stdout, encoding="utf-8")
            stderr_path.write_text(output.stderr, encoding="utf-8")
            stdout_ref = EvidenceRef("stdout", f"{prefix}/stdout.txt", self._sha256(stdout_path))
            stderr_ref = EvidenceRef("stderr", f"{prefix}/stderr.txt", self._sha256(stderr_path))
            raw_result_ref = None
            if output.raw_result_content is not None:
                raw_path = temporary / filename
                raw_path.write_text(output.raw_result_content, encoding="utf-8")
                raw_result_ref = EvidenceRef(
                    output.raw_result_media_type or "tool-result",
                    f"{prefix}/{filename}",
                    self._sha256(raw_path),
                )
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
                errors=output.errors,
                skipped=output.skipped,
                tool_id=output.tool_id,
                tool_version=output.tool_version,
                outcome=output.outcome,
                raw_result_ref=raw_result_ref,
                timed_out=output.timed_out,
                stdout_truncated=output.stdout_truncated,
                stderr_truncated=output.stderr_truncated,
            )
            self._write_json(temporary / "execution.json", normalized.to_dict())
            temporary.rename(target)
            return normalized
        finally:
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)

    def save_attempt_evaluation(
        self,
        state: SkeletonRunState,
        evaluation: dict[str, object],
        attempt: int,
    ) -> EvidenceRef:
        if attempt < 0 or attempt > 999:
            raise ValueError("attempt must be between 0 and 999")
        path = self.output_root / state.run_id / "attempts" / f"{attempt:03d}" / "evaluation.json"
        if path.exists():
            raise FileExistsError(f"evaluation evidence already exists for attempt {attempt:03d}")
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write_json(path, evaluation)
        return EvidenceRef("combined_oracle_evaluation", f"attempts/{attempt:03d}/evaluation.json", self._sha256(path))

    def save_attempt_artifact(
        self,
        state: SkeletonRunState,
        artifact: Any,
        metadata: dict[str, object],
    ) -> tuple[EvidenceRef, EvidenceRef]:
        artifact.validate()
        root = self.output_root / state.run_id / "artifacts" / f"attempt-{artifact.attempt:03d}"
        artifact_path = root / artifact.relative_path
        metadata_path = root / "metadata.json"
        if artifact_path.exists():
            if self._sha256(artifact_path) != artifact.content_sha256:
                raise FileExistsError("artifact attempt already exists with different content")
        else:
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_bytes(artifact.content.encode("utf-8"))
        if metadata_path.exists():
            raise FileExistsError("artifact attempt metadata already exists")
        self._write_json(metadata_path, metadata)
        return (
            EvidenceRef("unit_test_artifact", artifact_path.relative_to(self.output_root / state.run_id).as_posix(), artifact.content_sha256),
            EvidenceRef("artifact_metadata", metadata_path.relative_to(self.output_root / state.run_id).as_posix(), self._sha256(metadata_path)),
        )

    def save_oracle_evidence(
        self,
        state: SkeletonRunState,
        oracle_ref: str,
        content: bytes,
        sha256: str,
    ) -> tuple[EvidenceRef, EvidenceRef]:
        root = self.output_root / state.run_id / "oracle"
        source_path = root / "test_oracle.py"
        identity_path = root / "identity.json"
        if root.exists():
            raise FileExistsError("oracle evidence already exists")
        root.mkdir(parents=True)
        source_path.write_bytes(content)
        if self._sha256(source_path) != sha256:
            shutil.rmtree(root, ignore_errors=True)
            raise ValueError("persisted oracle hash differs from staged oracle")
        self._write_json(
            identity_path,
            {"schema_version": "1.0.0", "oracle_ref": oracle_ref, "sha256": sha256, "prompt_isolated": True},
        )
        return (
            EvidenceRef("curated_oracle", "oracle/test_oracle.py", sha256),
            EvidenceRef("oracle_identity", "oracle/identity.json", self._sha256(identity_path)),
        )

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
                "test_corrections": state.usage.test_corrections,
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
        self._append_new_events(run_dir / "events.jsonl", state.history)
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["status"] = state.status.value
        manifest["classification"] = state.classification.value
        manifest["usage"] = state.usage.__dict__ if hasattr(state.usage, "__dict__") else {
            "model_calls": state.usage.model_calls,
            "provider_retries": state.usage.provider_retries,
            "test_corrections": state.usage.test_corrections,
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
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(
                json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            temporary.replace(path)
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    @classmethod
    def _append_new_events(cls, path: Path, events: list[dict[str, Any]]) -> None:
        known: set[str] = set()
        if path.exists():
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError("event must be an object")
                    known.add(cls._event_identity(value))
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"cannot append to corrupt events.jsonl: {exc}") from exc
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            for event in events:
                identity = cls._event_identity(event)
                if identity in known:
                    continue
                stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
                known.add(identity)

    @staticmethod
    def _event_identity(event: dict[str, Any]) -> str:
        if event.get("event_id"):
            return str(event["event_id"])
        canonical = json.dumps(event, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return "legacy:" + hashlib.sha256(canonical).hexdigest()

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _markdown_text(value: str) -> str:
        sanitized = value.replace("|", "\\|").replace("`", "\\`")
        sanitized = sanitized.replace("<", "&lt;").replace(">", "&gt;")
        return " ".join(sanitized.splitlines()).strip()
