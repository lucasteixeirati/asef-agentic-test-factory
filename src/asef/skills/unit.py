from __future__ import annotations

import ast
from typing import Any

from ..contracts import ContractValidationError, UnitTestArtifact


class UnitSkillPolicyError(ValueError):
    pass


class UnitSkill:
    allowed_import_roots = frozenset({"calculator", "unittest"})
    forbidden_calls = frozenset({"open", "exec", "eval", "compile", "__import__", "input"})
    sensitive_markers = ("sk-", "api_key=", "password=", "access_token=", "secret=")

    def validate(self, artifact: UnitTestArtifact) -> dict[str, Any]:
        try:
            artifact.validate()
        except ContractValidationError as exc:
            raise UnitSkillPolicyError(f"artifact contract violation: {exc}") from exc
        lowered_content = artifact.content.lower()
        if any(marker in lowered_content for marker in self.sensitive_markers):
            raise UnitSkillPolicyError("generated test contains a sensitive value marker")
        try:
            tree = ast.parse(artifact.content, filename=artifact.relative_path)
        except SyntaxError as exc:
            raise UnitSkillPolicyError(f"generated test has invalid Python syntax: {exc.msg}") from exc
        imports: set[str] = set()
        test_methods = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    raise UnitSkillPolicyError("relative imports are forbidden")
                imports.add((node.module or "").split(".", 1)[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in self.forbidden_calls:
                    raise UnitSkillPolicyError(f"forbidden call in generated test: {node.func.id}")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in self.forbidden_calls:
                    raise UnitSkillPolicyError(f"forbidden call in generated test: {node.func.attr}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    test_methods += 1
        forbidden_imports = imports - self.allowed_import_roots
        if forbidden_imports:
            raise UnitSkillPolicyError(
                f"forbidden imports in generated test: {sorted(forbidden_imports)}"
            )
        if test_methods < 1:
            raise UnitSkillPolicyError("generated artifact must contain at least one test_ method")
        return {
            "schema_version": "1.0.0",
            "status": "PASSED",
            "skill_id": "unit",
            "imports": sorted(imports),
            "test_methods": test_methods,
            "artifact_sha256": artifact.content_sha256,
        }
