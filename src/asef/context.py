from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ContextValidationError(ValueError):
    pass


REQUIRED_SECTIONS = {
    "schema_version",
    "qa_profile",
    "team",
    "systems",
    "repositories",
    "skill_catalog",
    "mcp_servers",
    "llm_policy",
}
SENSITIVE_KEY_PARTS = ("api_key", "password", "access_token", "private_key", "secret")


@dataclass(slots=True, frozen=True)
class QualityContext:
    data: dict[str, Any]
    source_sha256: str = ""

    @classmethod
    def load(cls, path: Path) -> QualityContext:
        raw = path.read_bytes()
        return cls(
            validate_quality_context(json.loads(raw.decode("utf-8"))),
            hashlib.sha256(raw).hexdigest(),
        )

    def skills_for(self, system_id: str, requested: set[str] | None = None) -> list[dict[str, Any]]:
        systems = {item["id"]: item for item in self.data["systems"]}
        if system_id not in systems:
            raise ContextValidationError(f"unknown system_id: {system_id}")
        capabilities = set(systems[system_id]["quality_capabilities"])
        if requested is not None:
            capabilities &= requested
        return [
            skill
            for skill in self.data["skill_catalog"]
            if skill["capability"] in capabilities and skill.get("enabled", True)
        ]

    def snapshot_for(self, request: Any) -> Any:
        from .contracts import ContextSnapshot, ContractValidationError

        systems = {item["id"]: item for item in self.data["systems"]}
        system = systems.get(request.system_id)
        if system is None:
            raise ContextValidationError(f"unknown system_id: {request.system_id}")
        skills = {item["id"]: item for item in self.skills_for(request.system_id)}
        skill = skills.get(request.requested_skill)
        if skill is None:
            raise ContextValidationError(
                f"skill {request.requested_skill} is not enabled for system {request.system_id}"
            )
        repositories = {item["id"]: item for item in self.data["repositories"]}
        repository_ids = system.get("repository_ids", [])
        if len(repository_ids) != 1:
            raise ContextValidationError("walking skeleton requires exactly one repository")
        repository = repositories[repository_ids[0]]
        policy = self.data["llm_policy"]
        if request.execution_mode == "live":
            if policy.get("provider") != "openai":
                raise ContextValidationError("live mode currently requires provider openai")
            required_tasks = {"analysis", "test-generation", "test-correction"}
            if not required_tasks.issubset(set(policy.get("allowed_tasks", []))):
                raise ContextValidationError(
                    "live policy must authorize analysis, test-generation and test-correction"
                )
            if policy.get("live_requires_budget") is not True:
                raise ContextValidationError("live policy must require an explicit budget")
        try:
            snapshot = ContextSnapshot(
                source_sha256=self.source_sha256,
                qa_profile_id=self.data["qa_profile"]["id"],
                team_id=self.data["team"]["id"],
                system_id=system["id"],
                repository_id=repository["id"],
                skill_id=skill["id"],
                language_profile=repository["language_profile"],
                image=repository["execution_image"],
                provider=policy["provider"],
                model=policy["model"],
                mode="demo" if request.execution_mode == "demo" else "live",
                read_scopes=tuple(repository["read_scope"]),
                write_scopes=tuple(repository["write_scope"]),
                mcp_server_ids=tuple(skill.get("allowed_mcp_servers", [])),
            )
            snapshot.validate()
            return snapshot
        except (KeyError, ContractValidationError) as exc:
            raise ContextValidationError(f"context cannot produce a valid snapshot: {exc}") from exc


def validate_quality_context(value: dict[str, Any]) -> dict[str, Any]:
    missing = REQUIRED_SECTIONS - set(value)
    if missing:
        raise ContextValidationError(f"missing context sections: {sorted(missing)}")
    _reject_inline_secrets(value)

    repositories = _index_unique(value["repositories"], "repository")
    systems = _index_unique(value["systems"], "system")
    skills = _index_unique(value["skill_catalog"], "skill")
    mcp_servers = _index_unique(value["mcp_servers"], "MCP server")

    for system in systems.values():
        unknown_repositories = set(system.get("repository_ids", [])) - set(repositories)
        if unknown_repositories:
            raise ContextValidationError(
                f"system {system['id']} references unknown repositories: {sorted(unknown_repositories)}"
            )

    for skill in skills.values():
        unknown_mcps = set(skill.get("allowed_mcp_servers", [])) - set(mcp_servers)
        if unknown_mcps:
            raise ContextValidationError(
                f"skill {skill['id']} references unknown MCP servers: {sorted(unknown_mcps)}"
            )

    return value


def _index_unique(items: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            raise ContextValidationError(f"{label} id is required")
        if item_id in result:
            raise ContextValidationError(f"duplicate {label} id: {item_id}")
        result[item_id] = item
    return result


def _reject_inline_secrets(value: Any, path: str = "context") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = key.lower()
            if any(part in normalized for part in SENSITIVE_KEY_PARTS) and not normalized.endswith(
                "_ref"
            ):
                raise ContextValidationError(f"inline secret field is forbidden: {path}.{key}")
            _reject_inline_secrets(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_inline_secrets(nested, f"{path}[{index}]")
