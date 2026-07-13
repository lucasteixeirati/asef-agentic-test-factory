from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..contracts import ContextSnapshot, SkeletonRunState


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
        self._write_json(manifest_path, manifest)

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
