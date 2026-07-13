from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEMO_VERSION = "v1"
CALCULATOR_SOURCE = '''def add(a: int, b: int) -> int:
    """Return the arithmetic sum of two integers."""
    return a + b
'''


@dataclass(slots=True, frozen=True)
class DemoAssets:
    context: Path
    analysis_success: Path
    analysis_clarification: Path
    artifact_success: Path


def materialize_demo_assets(workspace_root: Path | None = None) -> DemoAssets:
    """Create the public, keyless demo without relying on repository test files."""
    root = (workspace_root or Path.cwd()).resolve()
    demo_root = root / ".asef" / "demo" / DEMO_VERSION
    calculator_root = demo_root / "calculator"
    cassettes_root = demo_root / "cassettes"
    calculator_root.mkdir(parents=True, exist_ok=True)
    cassettes_root.mkdir(parents=True, exist_ok=True)

    _write_text(calculator_root / "calculator.py", CALCULATOR_SOURCE)
    context = demo_root / "context.json"
    _write_json(context, _context_payload())

    analysis_success = cassettes_root / "analysis-success.json"
    _write_json(analysis_success, _analysis_payload(clarification_required=False))
    analysis_clarification = cassettes_root / "analysis-clarification.json"
    _write_json(analysis_clarification, _analysis_payload(clarification_required=True))
    artifact_success = cassettes_root / "artifact-success.json"
    _write_json(artifact_success, _artifact_payload())
    return DemoAssets(context, analysis_success, analysis_clarification, artifact_success)


def _context_payload() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0-draft",
        "qa_profile": {
            "id": "qa-walking-skeleton",
            "role": "quality-engineer",
            "experience_level": "senior",
            "approval_boundaries": ["export-tests", "increase-budget"],
        },
        "team": {
            "id": "calculator-quality",
            "quality_goals": ["fast-feedback"],
            "risk_taxonomy": ["functional"],
            "data_classification": "public",
        },
        "repositories": [
            {
                "id": "calculator-example",
                "provider": "local",
                "repository_ref": "workspace:.asef/demo/v1/calculator",
                "default_branch": "main",
                "language_profile": "python-pytest",
                "execution_image": "python@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0",
                "read_scope": ["calculator.py"],
                "write_scope": [".asef/runs/**"],
            }
        ],
        "systems": [
            {
                "id": "calculator-service",
                "kind": "python-library",
                "repository_ids": ["calculator-example"],
                "critical_flows": ["add-integers"],
                "quality_capabilities": ["unit"],
            }
        ],
        "skill_catalog": [
            {
                "id": "unit",
                "capability": "unit",
                "enabled": True,
                "allowed_mcp_servers": [],
            }
        ],
        "mcp_servers": [],
        "llm_policy": {
            "provider": "recorded",
            "model": "cassette-v1",
            "allowed_tasks": ["analysis", "test-generation"],
            "data_rules": ["no-secrets", "respect-read-scope"],
            "default_mode": "recorded",
            "live_requires_budget": True,
        },
    }


def _analysis_payload(*, clarification_required: bool) -> dict[str, Any]:
    return {
        "schema_name": "wf001_analysis",
        "model": "recorded-demo",
        "response_id": (
            "cassette-calculator-clarification-001"
            if clarification_required
            else "cassette-smk-001"
        ),
        "usage": {"input_tokens": 72, "output_tokens": 88},
        "output": {
            "behaviors": ["Return the arithmetic sum of two integers"],
            "risks": [
                "The accepted numeric type is not explicit"
                if clarification_required
                else "Incorrect handling of negative values"
            ],
            "scenarios": [
                "Two positive integers",
                "Positive and negative integer",
                "Two negative integers",
                "Zero as either operand",
            ],
            "clarification_required": clarification_required,
        },
    }


def _artifact_payload() -> dict[str, Any]:
    content = '''import unittest

from calculator import add


class CalculatorTests(unittest.TestCase):
    def test_two_positive_integers(self):
        self.assertEqual(add(2, 3), 5)

    def test_positive_and_negative_integer(self):
        self.assertEqual(add(7, -2), 5)

    def test_two_negative_integers(self):
        self.assertEqual(add(-4, -6), -10)

    def test_zero_operand(self):
        self.assertEqual(add(0, 9), 9)
'''
    return {
        "schema_name": "wf001_unit_artifact",
        "model": "recorded-demo",
        "response_id": "cassette-artifact-001",
        "usage": {"input_tokens": 120, "output_tokens": 160},
        "output": {
            "relative_path": "tests_generated/test_calculator.py",
            "content": content,
            "scenario_ids": ["SCN-001", "SCN-002", "SCN-003", "SCN-004"],
        },
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    _write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8", newline="\n")
