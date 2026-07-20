from __future__ import annotations

import json
from pathlib import Path

from ..java_unit_contracts import JavaUnitContractError, JavaUnitTestPlan, java_unit_plan_from_dict


class JavaUnitPlanFileAdapter:
    def load(self, path: Path) -> JavaUnitTestPlan:
        if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= 1_048_576:
            raise JavaUnitContractError("Java unit plan must be a regular JSON file up to 1 MiB")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=self._object)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise JavaUnitContractError("Java unit plan is not valid UTF-8 JSON") from exc
        return java_unit_plan_from_dict(raw)

    def save(self, path: Path, plan: JavaUnitTestPlan) -> Path:
        plan.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _object(pairs):
        value = {}
        for key, item in pairs:
            if key in value: raise JavaUnitContractError(f"duplicate JSON key in Java unit plan: {key}")
            value[key] = item
        return value
