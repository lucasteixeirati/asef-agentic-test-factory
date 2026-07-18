from __future__ import annotations

import json
from pathlib import Path

from ..api_contracts import ApiContractError, ApiTestPlan, api_plan_from_dict


class ApiPlanFileAdapter:
    def load(self, path: Path) -> ApiTestPlan:
        if not path.is_file():
            raise ApiContractError("API plan must reference an existing regular file")
        if path.stat().st_size > 1_048_576:
            raise ApiContractError("API plan exceeds the 1 MiB file limit")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiContractError("API plan is not valid UTF-8 JSON") from exc
        return api_plan_from_dict(raw)

    def save(self, path: Path, plan: ApiTestPlan) -> Path:
        plan.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

