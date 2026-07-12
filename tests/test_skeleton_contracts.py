from __future__ import annotations

import json
import unittest
from pathlib import Path

from asef.contracts import (
    MAX_ARTIFACT_BYTES,
    ContextSnapshot,
    ContractValidationError,
    EvidenceRef,
    IncompatibleSchemaError,
    NormalizedExecutionResult,
    SkeletonRunRequest,
    SkeletonRunState,
    SkeletonBudgetLimits,
    SkeletonBudgetUsage,
    UnitTestArtifact,
    ensure_compatible_state_schema,
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


class SkeletonStateAndOutcomeTests(unittest.TestCase):
    def test_state_is_json_serializable_with_primitive_enums(self) -> None:
        state = SkeletonRunState(request())
        value = state.to_dict()
        self.assertEqual(value["schema_version"], "2.0.0")
        self.assertEqual(value["status"], "RECEIVED")
        self.assertEqual(value["classification"], "UNCLASSIFIED")
        json.dumps(value)

    def test_state_rejects_budget_usage_above_limit(self) -> None:
        state = SkeletonRunState(
            request(),
            budgets=SkeletonBudgetLimits(max_model_calls=1),
            usage=SkeletonBudgetUsage(model_calls=2),
        )
        with self.assertRaisesRegex(ContractValidationError, "exceeds"):
            state.validate()

    def test_spike_state_is_explicitly_incompatible(self) -> None:
        with self.assertRaisesRegex(IncompatibleSchemaError, "cannot be resumed"):
            ensure_compatible_state_schema("1.0.0")

    def test_current_major_accepts_future_minor(self) -> None:
        ensure_compatible_state_schema("2.3.0")

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
