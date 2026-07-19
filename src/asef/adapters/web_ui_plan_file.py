from __future__ import annotations

import json
from pathlib import Path

from ..web_ui_contracts import WebUiContractError, WebUiTestPlan, web_ui_plan_from_dict


class WebUiPlanFileAdapter:
    def load(self, path: Path) -> WebUiTestPlan:
        if not path.is_file() or path.stat().st_size > 1_048_576:
            raise WebUiContractError("Web UI plan must be a regular JSON file up to 1 MiB")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=self._object)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WebUiContractError("Web UI plan is not valid UTF-8 JSON") from exc
        return web_ui_plan_from_dict(raw)

    def save(self, path: Path, plan: WebUiTestPlan) -> Path:
        plan.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise WebUiContractError(f"duplicate JSON key in Web UI plan: {key}")
            value[key] = item
        return value
