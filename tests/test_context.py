from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from asef.context import ContextValidationError, QualityContext, validate_quality_context
from asef.contracts import SkeletonRunRequest


EXAMPLE = Path("examples/context/quality-context.example.json")


class QualityContextTests(unittest.TestCase):
    def test_walking_skeleton_fixture_resolves_deterministic_snapshot(self) -> None:
        context = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
        snapshot = context.snapshot_for(
            SkeletonRunRequest(
                context_ref="examples/context/walking-skeleton-context.json",
                system_id="calculator-service",
                requested_skill="unit",
                requirement_title="Add integers",
                requirement_description="Return the sum",
            )
        )
        value = snapshot.to_dict()
        self.assertEqual(value["system_id"], "calculator-service")
        self.assertEqual(value["skill_id"], "unit")
        self.assertEqual(value["repository_id"], "calculator-example")
        self.assertEqual(value["provider"], "recorded")
        self.assertEqual(len(value["source_sha256"]), 64)

    def data(self) -> dict:
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_is_valid_and_selects_system_skills(self) -> None:
        context = QualityContext.load(EXAMPLE)
        selected = context.skills_for("orders-api", {"backend-api", "performance", "mobile"})
        self.assertEqual([skill["id"] for skill in selected], ["backend-api", "performance"])

    def test_inline_secret_is_rejected(self) -> None:
        value = self.data()
        value["mcp_servers"][0]["access_token"] = "forbidden"
        with self.assertRaisesRegex(ContextValidationError, "inline secret"):
            validate_quality_context(value)

    def test_secret_reference_is_allowed(self) -> None:
        value = self.data()
        value["mcp_servers"][0]["secret_ref"] = "env:GITHUB_TOKEN"
        validate_quality_context(value)

    def test_unknown_repository_reference_is_rejected(self) -> None:
        value = self.data()
        value["systems"][0]["repository_ids"].append("missing")
        with self.assertRaisesRegex(ContextValidationError, "unknown repositories"):
            validate_quality_context(value)

    def test_duplicate_skill_is_rejected(self) -> None:
        value = self.data()
        value["skill_catalog"].append(copy.deepcopy(value["skill_catalog"][0]))
        with self.assertRaisesRegex(ContextValidationError, "duplicate skill"):
            validate_quality_context(value)
