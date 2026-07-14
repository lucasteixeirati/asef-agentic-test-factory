from __future__ import annotations

import json
import unittest
from pathlib import Path

from asef.contracts import (
    MAX_ARTIFACT_BYTES,
    ContextResolution,
    ContextSnapshot,
    ContractValidationError,
    EvidenceRef,
    IncompatibleSchemaError,
    NormalizedExecutionResult,
    RunOrigin,
    SkeletonRunRequest,
    SkeletonRunState,
    SkeletonBudgetLimits,
    SkeletonBudgetUsage,
    TestExecutionOutcome,
    UnitTestArtifact,
    ensure_compatible_state_schema,
    import_state_v1,
    resolve_new_run_context,
    start_replay,
    state_from_dict,
)
from asef.outcomes import ExitCode, RunClassification, RunStatus, exit_code_for


DIGEST = "a" * 64
IMAGE = f"python@sha256:{DIGEST}"


def request(**overrides: object) -> SkeletonRunRequest:
    values = {
        "context_ref": "examples/context/walking-skeleton-context.json",
        "system_id": "calculator-service",
        "requested_skill": "unit",
        "requirement_title": "Add integers",
        "requirement_description": "Return the arithmetic sum of two integers",
    }
    values.update(overrides)
    return SkeletonRunRequest(**values)


def evidence(kind: str) -> EvidenceRef:
    return EvidenceRef(kind=kind, relative_path=f"results/{kind}.txt", sha256=DIGEST)


class SkeletonRequestContractTests(unittest.TestCase):
    def test_demo_request_is_serializable(self) -> None:
        value = request().to_dict()
        self.assertEqual(value["execution_mode"], "demo")
        json.dumps(value)

    def test_live_requires_positive_budget(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "positive api_budget"):
            request(execution_mode="live").validate()

    def test_requirement_size_is_bounded(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "exceeds"):
            request(requirement_description="x" * 20_001).validate()


class UnitTestArtifactContractTests(unittest.TestCase):
    def test_valid_artifact_has_runtime_hash(self) -> None:
        artifact = UnitTestArtifact(
            relative_path="tests_generated/test_calculator.py",
            content="import unittest\n",
            scenario_ids=("SCN-001",),
        )
        value = artifact.to_dict()
        self.assertEqual(len(value["content_sha256"]), 64)
        self.assertEqual(value["scenario_ids"], ["SCN-001"])

    def test_parent_traversal_is_rejected(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "escapes"):
            UnitTestArtifact(
                relative_path="../test_escape.py",
                content="pass",
                scenario_ids=("SCN-001",),
            ).validate()

    def test_nested_or_non_python_artifact_is_rejected(self) -> None:
        for path in ("tests_generated/nested/test_x.py", "tests_generated/test_x.txt"):
            with self.subTest(path=path), self.assertRaisesRegex(
                ContractValidationError, "one .py file"
            ):
                UnitTestArtifact(path, "pass", ("SCN-001",)).validate()

    def test_artifact_size_is_bounded_by_utf8_bytes(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "exceeds"):
            UnitTestArtifact(
                "tests_generated/test_large.py",
                "á" * (MAX_ARTIFACT_BYTES // 2 + 1),
                ("SCN-001",),
            ).validate()


class ContextSnapshotContractTests(unittest.TestCase):
    def snapshot(self, **overrides: object) -> ContextSnapshot:
        values = {
            "source_sha256": DIGEST,
            "qa_profile_id": "qa-example",
            "team_id": "quality-team",
            "system_id": "calculator-service",
            "repository_id": "calculator-example",
            "skill_id": "unit",
            "language_profile": "python-pytest",
            "image": IMAGE,
            "provider": "recorded",
            "model": "cassette-v1",
            "mode": "demo",
            "read_scopes": ("calculator.py",),
            "write_scopes": (".asef/runs/**",),
        }
        values.update(overrides)
        return ContextSnapshot(**values)

    def test_snapshot_is_primitive_and_has_no_mcp_by_default(self) -> None:
        value = self.snapshot().to_dict()
        self.assertEqual(value["mcp_server_ids"], [])
        json.dumps(value)

    def test_image_must_be_fixed_by_digest(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "fixed by digest"):
            self.snapshot(image="python:latest").validate()

    def test_scope_with_inline_secret_marker_is_rejected(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "sensitive"):
            self.snapshot(read_scopes=("token=forbidden",)).validate()


class ExecutionResultContractTests(unittest.TestCase):
    def test_execution_result_is_serializable(self) -> None:
        result = NormalizedExecutionResult(
            image=IMAGE,
            command=("python", "-m", "unittest"),
            exit_code=0,
            duration_ms=100,
            stdout_ref=evidence("stdout"),
            stderr_ref=evidence("stderr"),
            tests=1,
            passed=1,
            failed=0,
        )
        json.dumps(result.to_dict())

    def test_inconsistent_test_counts_are_rejected(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "cannot exceed"):
            NormalizedExecutionResult(
                image=IMAGE,
                command=("python", "-m", "unittest"),
                exit_code=1,
                duration_ms=100,
                stdout_ref=evidence("stdout"),
                stderr_ref=evidence("stderr"),
                tests=1,
                passed=1,
                failed=1,
            ).validate()

    def test_sensitive_command_argument_is_rejected(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "sensitive"):
            NormalizedExecutionResult(
                image=IMAGE,
                command=("python", "token=forbidden"),
                exit_code=1,
                duration_ms=1,
                stdout_ref=evidence("stdout"),
                stderr_ref=evidence("stderr"),
            ).validate()

    def test_structured_pytest_result_reconciles_counts_and_raw_evidence(self) -> None:
        result = NormalizedExecutionResult(
            image="sha256:" + DIGEST,
            command=("python", "-m", "pytest"),
            exit_code=1,
            duration_ms=10,
            stdout_ref=evidence("stdout"),
            stderr_ref=evidence("stderr"),
            tests=3,
            passed=1,
            failed=1,
            errors=0,
            skipped=1,
            tool_id="pytest",
            tool_version="8.3.3",
            outcome=TestExecutionOutcome.ASSERTION_FAILURE,
            raw_result_ref=evidence("junit"),
        )
        self.assertEqual(result.to_dict()["schema_version"], "1.1.0")
        with self.assertRaisesRegex(ContractValidationError, "must equal"):
            NormalizedExecutionResult(
                image="sha256:" + DIGEST,
                command=("python", "-m", "pytest"),
                exit_code=1,
                duration_ms=10,
                stdout_ref=evidence("stdout"),
                stderr_ref=evidence("stderr"),
                tests=3,
                passed=2,
                failed=0,
                errors=0,
                skipped=0,
            ).validate()


class SkeletonStateAndOutcomeTests(unittest.TestCase):
    def test_state_is_json_serializable_with_primitive_enums(self) -> None:
        state = SkeletonRunState(request())
        value = state.to_dict()
        self.assertEqual(value["schema_version"], "1.2.0")
        self.assertEqual(value["origin"], "NEW")
        self.assertEqual(value["context_resolution"], "CONTEXT_UNRESOLVED")
        self.assertEqual(value["status"], "RECEIVED")
        self.assertEqual(value["classification"], "UNCLASSIFIED")
        json.dumps(value)

    def test_state_1_1_without_correction_fields_remains_readable(self) -> None:
        value = SkeletonRunState(request()).to_dict()
        value["schema_version"] = "1.1.0"
        value["budgets"].pop("max_test_corrections")
        value["usage"].pop("test_corrections")
        restored = state_from_dict(value)
        self.assertEqual(restored.schema_version, "1.1.0")
        self.assertEqual(restored.budgets.max_test_corrections, 2)
        self.assertEqual(restored.usage.test_corrections, 0)

    def test_state_rejects_budget_usage_above_limit(self) -> None:
        state = SkeletonRunState(
            request(),
            budgets=SkeletonBudgetLimits(max_model_calls=1),
            usage=SkeletonBudgetUsage(model_calls=2),
        )
        with self.assertRaisesRegex(ContractValidationError, "exceeds"):
            state.validate()

    def test_spike_state_is_importable_but_not_resumed(self) -> None:
        legacy = {
            "schema_version": "1.0.0",
            "run_id": "legacy-run",
            "attempts": {"analysis": 1},
            "facts": {"analysis": {"summary": "preserved"}},
            "usage": {"model_calls": 2, "input_tokens": 100, "output_tokens": 50},
            "history": [{"event": "old-event"}],
        }
        state = import_state_v1(legacy, request())
        self.assertEqual(state.run_id, "legacy-run")
        self.assertEqual(state.origin, RunOrigin.IMPORTED)
        self.assertEqual(state.context_resolution, ContextResolution.UNRESOLVED)
        self.assertEqual(state.imported_facts, legacy["facts"])
        self.assertEqual(state.usage.model_calls, 2)
        self.assertEqual(state.imported_usage, legacy["usage"])
        self.assertFalse(state.history[-1]["resume_supported"])

    def test_new_run_resolves_context_before_side_effects(self) -> None:
        state = resolve_new_run_context(
            SkeletonRunState(request()),
            context_snapshot_ref="context/snapshot.json",
        )
        self.assertEqual(state.context_resolution, ContextResolution.RESOLVED)
        self.assertEqual(state.history[-1]["event"], "CONTEXT_RESOLVED")

    def test_imported_run_cannot_be_resolved_in_place(self) -> None:
        imported = import_state_v1(
            {"schema_version": "1.0.0", "run_id": "legacy-run"}, request()
        )
        with self.assertRaisesRegex(ContractValidationError, "only a new run"):
            resolve_new_run_context(imported, context_snapshot_ref="context/snapshot.json")

    def test_versioned_import_fixture_preserves_non_normalized_usage(self) -> None:
        document = json.loads(
            Path("examples/state/spike-state-v1.example.json").read_text(encoding="utf-8")
        )
        state = import_state_v1(document, request())
        self.assertEqual(state.imported_usage["estimated_cost_brl"], 0.01)
        self.assertEqual(state.imported_budgets["max_test_corrections"], 2)

    def test_replay_is_a_new_run_linked_to_import(self) -> None:
        imported = import_state_v1(
            {"schema_version": "1.0.0", "run_id": "legacy-run", "facts": {"x": 1}},
            request(),
        )
        replay = start_replay(imported, context_snapshot_ref="context/snapshot.json")
        self.assertNotEqual(replay.run_id, imported.run_id)
        self.assertEqual(replay.origin, RunOrigin.REPLAY)
        self.assertEqual(replay.source_run_id, imported.run_id)
        self.assertEqual(replay.context_resolution, ContextResolution.RESOLVED)
        self.assertEqual(replay.usage.model_calls, 0)
        self.assertEqual(replay.imported_facts, {"x": 1})
        self.assertFalse(replay.history[-1]["resume_supported"])

    def test_import_rejects_non_1_0_document(self) -> None:
        with self.assertRaisesRegex(IncompatibleSchemaError, "only state schema 1.0.0"):
            import_state_v1({"schema_version": "2.0.0", "run_id": "old"}, request())

    def test_import_rejects_sensitive_legacy_evidence(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "sensitive field"):
            import_state_v1(
                {"schema_version": "1.0.0", "run_id": "old", "facts": {"api_key": "x"}},
                request(),
            )

    def test_current_major_accepts_future_minor(self) -> None:
        ensure_compatible_state_schema("1.3.0")

    def test_exit_code_contract(self) -> None:
        cases = {
            (RunStatus.SUCCEEDED, RunClassification.ACCEPTED): ExitCode.SUCCESS,
            (
                RunStatus.WAITING_FOR_CLARIFICATION,
                RunClassification.WAITING_HUMAN,
            ): ExitCode.WAITING_HUMAN,
            (RunStatus.FAILED, RunClassification.INPUT_ERROR): ExitCode.INVALID_INPUT_OR_CONTEXT,
            (RunStatus.FAILED, RunClassification.TEST_FAILURE): ExitCode.FUNCTIONAL_FAILURE,
            (
                RunStatus.POLICY_BLOCKED,
                RunClassification.POLICY_VIOLATION,
            ): ExitCode.POLICY_BLOCKED,
            (
                RunStatus.BUDGET_EXHAUSTED,
                RunClassification.BUDGET_ERROR,
            ): ExitCode.BUDGET_EXHAUSTED,
            (
                RunStatus.FAILED,
                RunClassification.INFRASTRUCTURE_ERROR,
            ): ExitCode.PROVIDER_OR_INFRASTRUCTURE,
            (RunStatus.CANCELLED, RunClassification.CANCELLED_BY_USER): ExitCode.CANCELLED,
            (RunStatus.SUCCEEDED, RunClassification.UNCLASSIFIED): ExitCode.FUNCTIONAL_FAILURE,
            (RunStatus.FAILED, RunClassification.ACCEPTED): ExitCode.FUNCTIONAL_FAILURE,
        }
        for (status, classification), expected in cases.items():
            with self.subTest(status=status, classification=classification):
                self.assertEqual(exit_code_for(status, classification), expected)

    def test_public_contract_package_has_no_framework_imports(self) -> None:
        for path in ("src/asef/contracts.py", "src/asef/outcomes.py"):
            source = Path(path).read_text(encoding="utf-8")
            for forbidden in ("langgraph", "openai", "docker", "pydantic_ai"):
                self.assertNotIn(forbidden, source.lower())

    def test_distribution_contains_only_one_source_package(self) -> None:
        removed_package = "asef" + "_spike"
        pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('packages = ["src/asef"]', pyproject)
        self.assertFalse(any((Path("src") / removed_package).glob("*.py")))
        for root in (Path("src"), Path("tests"), Path("spikes")):
            for source_path in root.rglob("*.py"):
                self.assertNotIn(
                    removed_package,
                    source_path.read_text(encoding="utf-8"),
                    str(source_path),
                )


if __name__ == "__main__":
    unittest.main()
