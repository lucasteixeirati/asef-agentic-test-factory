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
        self._write_json(run_dir / "state.json", state.to_dict())
        (run_dir / "events.jsonl").write_text(
            "".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in state.history),
            encoding="utf-8",
        )
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
        return run_dir

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
