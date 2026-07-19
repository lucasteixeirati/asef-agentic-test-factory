from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from ..api_contracts import ApiExecutionResult, ApiTestPlan, api_plan_from_dict
from ..capability_runs import CapabilityRunContractError, CapabilityRunState, capability_run_from_dict
from ..contracts import EvidenceRef
from ..openapi_contracts import OpenApiSummary
from ..web_ui_contracts import WebUiExecutionResult, WebUiTestPlan, web_ui_plan_from_dict


class CapabilityRunStore:
    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root

    def create(self, state: CapabilityRunState) -> Path:
        state.validate()
        run_dir = self._run_dir(state.run_id)
        run_dir.mkdir(parents=True, exist_ok=False)
        self._write_state_bundle(run_dir, state)
        return run_dir

    def save_state(self, state: CapabilityRunState) -> None:
        state.validate()
        run_dir = self._run_dir(state.run_id, require_existing=True)
        self._write_state_bundle(run_dir, state)

    def load_state(self, run_id: str) -> CapabilityRunState:
        return capability_run_from_dict(self._read_json(self._run_dir(run_id, require_existing=True) / "state.json"))

    def save_plan(self, state: CapabilityRunState, plan: ApiTestPlan) -> EvidenceRef:
        plan.validate()
        run_dir = self._run_dir(state.run_id, require_existing=True)
        path = run_dir / "artifacts" / "api-plan.json"
        self._write_json(path, plan.to_dict())
        ref = EvidenceRef("api_test_plan", "artifacts/api-plan.json", self._sha256(path))
        state.plan_id = plan.plan_id
        state.plan_sha256 = ref.sha256
        state.evidence_refs.append(ref)
        self.save_state(state)
        return ref

    def save_openapi_summary(self, state: CapabilityRunState, summary: OpenApiSummary) -> EvidenceRef:
        summary.validate()
        run_dir = self._run_dir(state.run_id, require_existing=True)
        path = run_dir / "artifacts" / "openapi-summary.json"
        value = {
            "schema_version": summary.schema_version,
            "source_sha256": summary.source_sha256,
            "openapi_version": summary.openapi_version,
            "title": summary.title,
            "operations": summary.prompt_value(),
        }
        self._write_json(path, value)
        ref = EvidenceRef("openapi_summary", "artifacts/openapi-summary.json", self._sha256(path))
        state.evidence_refs.append(ref)
        self.save_state(state)
        return ref

    def load_plan(self, state: CapabilityRunState) -> ApiTestPlan:
        if state.plan_sha256 is None:
            raise CapabilityRunContractError("capability run has no plan")
        path = self._run_dir(state.run_id, require_existing=True) / "artifacts" / "api-plan.json"
        if not path.is_file() or self._sha256(path) != state.plan_sha256:
            raise CapabilityRunContractError("persisted API plan integrity mismatch")
        plan = api_plan_from_dict(self._read_json(path))
        if plan.plan_id != state.plan_id:
            raise CapabilityRunContractError("persisted API plan identity mismatch")
        return plan

    def save_result(self, state: CapabilityRunState, result: ApiExecutionResult) -> EvidenceRef:
        result.validate()
        path = self._run_dir(state.run_id, require_existing=True) / "results" / "api-result.json"
        self._write_json(path, result.to_dict())
        ref = EvidenceRef("api_execution_result", "results/api-result.json", self._sha256(path))
        state.evidence_refs.append(ref)
        self.save_state(state)
        return ref

    def save_web_plan(self, state: CapabilityRunState, plan: WebUiTestPlan) -> EvidenceRef:
        plan.validate()
        path = self._run_dir(state.run_id, require_existing=True) / "artifacts" / "web-ui-plan.json"
        self._write_json(path, plan.to_dict())
        ref = EvidenceRef("web_ui_test_plan", "artifacts/web-ui-plan.json", self._sha256(path))
        state.plan_id, state.plan_sha256 = plan.plan_id, ref.sha256
        state.evidence_refs.append(ref)
        self.save_state(state)
        return ref

    def load_web_plan(self, state: CapabilityRunState) -> WebUiTestPlan:
        if state.plan_sha256 is None:
            raise CapabilityRunContractError("capability run has no Web UI plan")
        path = self._run_dir(state.run_id, require_existing=True) / "artifacts" / "web-ui-plan.json"
        if not path.is_file() or self._sha256(path) != state.plan_sha256:
            raise CapabilityRunContractError("persisted Web UI plan integrity mismatch")
        plan = web_ui_plan_from_dict(self._read_json(path))
        if plan.plan_id != state.plan_id:
            raise CapabilityRunContractError("persisted Web UI plan identity mismatch")
        return plan

    def save_web_result(self, state: CapabilityRunState, result: WebUiExecutionResult) -> EvidenceRef:
        result.validate()
        path = self._run_dir(state.run_id, require_existing=True) / "results" / "web-ui-result.json"
        self._write_json(path, result.to_dict())
        ref = EvidenceRef("web_ui_execution_result", "results/web-ui-result.json", self._sha256(path))
        state.evidence_refs.append(ref)
        self.save_state(state)
        return ref

    def register_evidence(self, state: CapabilityRunState, kind: str, path: Path) -> EvidenceRef:
        run_dir = self._run_dir(state.run_id, require_existing=True)
        resolved = path.resolve(strict=True)
        if not resolved.is_file() or not resolved.is_relative_to(run_dir):
            raise CapabilityRunContractError("evidence must be a regular file inside the run")
        relative = resolved.relative_to(run_dir).as_posix()
        if any(item.relative_path == relative for item in state.evidence_refs):
            raise CapabilityRunContractError("evidence path is already registered")
        ref = EvidenceRef(kind, relative, self._sha256(resolved))
        state.evidence_refs.append(ref)
        self.save_state(state)
        return ref

    def run_dir(self, run_id: str) -> Path:
        return self._run_dir(run_id, require_existing=True)

    def _manifest(self, state: CapabilityRunState) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "run_id": state.run_id,
            "workflow_id": state.workflow_id,
            "skill_id": state.skill_id,
            "language_profile": state.language_profile,
            "status": state.status.value,
            "classification": state.classification.value,
            "terminal": state.terminal,
            "plan_id": state.plan_id,
            "plan_sha256": state.plan_sha256,
            "budgets": state.to_dict()["budgets"],
            "usage": state.to_dict()["usage"],
            "evidence_refs": [
                {"kind": item.kind, "relative_path": item.relative_path, "sha256": item.sha256}
                for item in state.evidence_refs
            ],
        }

    def _run_dir(self, run_id: str, *, require_existing: bool = False) -> Path:
        try:
            from uuid import UUID
            UUID(run_id)
        except ValueError as exc:
            raise CapabilityRunContractError("run_id must be a UUID") from exc
        root = self.output_root.resolve()
        candidate = (root / run_id).resolve()
        if not candidate.is_relative_to(root):
            raise CapabilityRunContractError("run path escapes output root")
        if require_existing and not candidate.is_dir():
            raise CapabilityRunContractError("capability run directory is unavailable")
        return candidate

    @staticmethod
    def _read_json(path: Path) -> object:
        try:
            return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=CapabilityRunStore._object)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CapabilityRunContractError("persisted capability run JSON is invalid") from exc

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def _write_state_bundle(self, run_dir: Path, state: CapabilityRunState) -> None:
        state_value = state.to_dict()
        values = {
            run_dir / "state.json": state_value,
            run_dir / "manifest.json": self._manifest(state),
        }
        temporaries: dict[Path, Path] = {}
        previous = {path: path.read_bytes() if path.is_file() else None for path in values}
        try:
            for path, value in values.items():
                temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
                temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                temporaries[path] = temporary
            for path, temporary in temporaries.items():
                os.replace(temporary, path)
        except BaseException:
            for path, content in previous.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    restoration = path.with_name(f".{path.name}.{uuid4().hex}.restore")
                    restoration.write_bytes(content)
                    os.replace(restoration, path)
            raise
        finally:
            for temporary in temporaries.values():
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise CapabilityRunContractError(f"duplicate JSON key in capability run: {key}")
            value[key] = item
        return value

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
