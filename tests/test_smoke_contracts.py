from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from asef.adapters.smoke_dataset import SmokeDatasetLoader
from asef.adapters.context_file import FileQualityContextAdapter
from asef.contracts import ContractValidationError
from asef.contracts import SkeletonRunRequest
from asef.evaluation_contracts import dataset_case_from_dict
from asef.smoke_contracts import (
    SMOKE_CASE_IDS,
    SmokeComparison,
    SmokeActualUsage,
    SmokeCaseResult,
    SmokeExecutorKind,
    SmokeObservation,
    SmokeSuiteReport,
    SmokeTerminalAction,
    semantic_fingerprint,
    smoke_demo_spec_from_dict,
)


ROOT = Path(__file__).resolve().parents[1]


def valid_demo(case_id: str = "SMK-001") -> dict[str, object]:
    base = f"datasets/smoke/{case_id}"
    return {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "case_version": "1.0.0",
        "context_ref": "examples/context/smoke.json",
        "system_id": "reference-sut",
        "analysis_cassette_ref": f"{base}/demo/analysis.json",
        "artifact_cassette_refs": [f"{base}/demo/artifact-001.json"],
        "executor": "PYTEST_DOCKER",
        "expected": {
            "status": "SUCCEEDED",
            "classification": "ACCEPTED",
            "action": "ACCEPT",
            "usage": {
                "model_calls": 2,
                "provider_retries": 0,
                "corrections": 0,
                "execution_attempts": 1,
            },
            "docker_called": True,
            "oracle_executed": True,
            "human_checkpoint_requested": False,
        },
    }


class SmokeDemoContractTests(unittest.TestCase):
    def test_accepts_exact_and_range_counters(self) -> None:
        value = valid_demo()
        value["expected"]["usage"]["model_calls"] = {"min": 2, "max": 3}  # type: ignore[index]
        spec = smoke_demo_spec_from_dict(value)
        self.assertIs(spec.executor, SmokeExecutorKind.PYTEST_DOCKER)
        self.assertTrue(spec.expected.usage.model_calls.matches(3))
        self.assertFalse(spec.expected.usage.model_calls.matches(4))

    def test_rejects_unknown_nested_fields_and_unknown_classification(self) -> None:
        value = valid_demo()
        value["expected"]["unexpected"] = True  # type: ignore[index]
        with self.assertRaisesRegex(ContractValidationError, "unknown fields"):
            smoke_demo_spec_from_dict(value)

        value = valid_demo()
        value["expected"]["classification"] = "IMAGINARY"  # type: ignore[index]
        with self.assertRaisesRegex(ContractValidationError, "smoke demo is invalid"):
            smoke_demo_spec_from_dict(value)

    def test_rejects_traversal_and_incoherent_executor(self) -> None:
        value = valid_demo()
        value["context_ref"] = "../outside.json"
        with self.assertRaisesRegex(ContractValidationError, "inside the workspace"):
            smoke_demo_spec_from_dict(value)

        value = valid_demo()
        value["executor"] = "NOT_REACHED"
        with self.assertRaisesRegex(ContractValidationError, "cannot call Docker"):
            smoke_demo_spec_from_dict(value)

    def test_rejects_more_than_two_corrections(self) -> None:
        value = valid_demo()
        value["artifact_cassette_refs"] = [
            f"datasets/smoke/SMK-001/demo/artifact-{number:03d}.json"
            for number in range(1, 5)
        ]
        with self.assertRaisesRegex(ContractValidationError, "at most two corrections"):
            smoke_demo_spec_from_dict(value)

    def test_dataset_case_rejects_unknown_expected_classification(self) -> None:
        case = self._case_value("SMK-001")
        case["expected_classifications"] = ["IMAGINARY"]
        with self.assertRaisesRegex(ContractValidationError, "unknown values"):
            dataset_case_from_dict(case)

    def test_result_and_suite_reconcile_semantic_facts(self) -> None:
        spec = smoke_demo_spec_from_dict(valid_demo())
        actual = SmokeObservation(
            status=spec.expected.status,
            classification=spec.expected.classification,
            action=SmokeTerminalAction.ACCEPT,
            usage=SmokeActualUsage(2, 0, 0, 1),
            docker_called=True,
            oracle_executed=True,
            human_checkpoint_requested=False,
            artifact_hash="a" * 64,
            oracle_hash="b" * 64,
        )
        fingerprint = semantic_fingerprint(
            {
                "case_id": spec.case_id,
                "status": actual.status.value,
                "classification": actual.classification.value,
                "action": actual.action.value,
                "artifact_hash": actual.artifact_hash,
                "oracle_hash": actual.oracle_hash,
            }
        )
        result = SmokeCaseResult(
            case_id=spec.case_id,
            case_version=spec.case_version,
            repetition=1,
            run_id="run-001",
            run_dir_ref=".asef/smoke/suite/run-001",
            expected=spec.expected,
            actual=actual,
            comparison=SmokeComparison.MATCHED,
            semantic_fingerprint=fingerprint,
        )
        results = tuple(
            replace(
                result,
                case_id=case_id,
                run_id=f"run-{case_id}",
                run_dir_ref=f".asef/smoke/suite/{case_id}",
            )
            for case_id in SMOKE_CASE_IDS
        )
        report = SmokeSuiteReport(
            suite_id="suite-001",
            asef_version="0.1.0a3",
            dataset_hash="c" * 64,
            repeat=1,
            environment="test",
            results=results,
            matched=10,
            mismatched=0,
            runner_errors=0,
            limitations=("Curated non-statistical dataset",),
        )
        self.assertEqual(report.to_dict()["total"], 10)
        with self.assertRaisesRegex(ContractValidationError, "do not reconcile"):
            SmokeSuiteReport(
                suite_id=report.suite_id,
                asef_version=report.asef_version,
                dataset_hash=report.dataset_hash,
                repeat=report.repeat,
                environment=report.environment,
                results=report.results,
                matched=0,
                mismatched=1,
                runner_errors=0,
                limitations=report.limitations,
            ).validate()

    @staticmethod
    def _case_value(case_id: str) -> dict[str, object]:
        base = f"datasets/smoke/{case_id}"
        return {
            "schema_version": "1.0.0",
            "case_id": case_id,
            "version": "1.0.0",
            "kind": "SMOKE",
            "title": "Case",
            "objective": "Exercise the workflow",
            "origin": "test",
            "license": "MIT",
            "curator": "ASEF",
            "language_profile": "python-pytest",
            "sut_ref": "sut",
            "requirement_ref": f"{base}/requirement.md",
            "oracle_ref": f"{base}/oracle/test_oracle.py",
            "generation_input_refs": [
                f"{base}/requirement.md",
                "sut/module.py",
            ],
            "evaluation_input_refs": [f"{base}/oracle/test_oracle.py"],
            "expected_classifications": ["ACCEPTED"],
            "allowed_modes": ["demo"],
            "exposure": "PUBLIC",
            "oracle_policy": "PROMPT_ISOLATED",
            "tags": ["fixture"],
        }


class SmokeDatasetLoaderTests(unittest.TestCase):
    def test_repository_dataset_and_context_are_complete(self) -> None:
        dataset = SmokeDatasetLoader(ROOT).load("datasets/smoke")
        self.assertEqual(tuple(item.case.case_id for item in dataset.cases), SMOKE_CASE_IDS)
        expected = {
            "SMK-001": ("SUCCEEDED", "ACCEPTED", "ACCEPT"),
            "SMK-002": ("SUCCEEDED", "ACCEPTED", "ACCEPT"),
            "SMK-003": ("SUCCEEDED", "ACCEPTED", "ACCEPT"),
            "SMK-004": ("WAITING_FOR_CLARIFICATION", "WAITING_HUMAN", "NOT_REACHED"),
            "SMK-005": ("WAITING_FOR_CLARIFICATION", "WAITING_HUMAN", "NOT_REACHED"),
            "SMK-006": ("SUCCEEDED", "ACCEPTED", "ACCEPT"),
            "SMK-007": (
                "WAITING_FOR_HUMAN_REVIEW",
                "SUT_DEFECT_SUSPECTED",
                "HUMAN_REVIEW",
            ),
            "SMK-008": ("BUDGET_EXHAUSTED", "BUDGET_ERROR", "NOT_REACHED"),
            "SMK-009": ("FAILED", "INFRASTRUCTURE_ERROR", "NOT_REACHED"),
            "SMK-010": ("POLICY_BLOCKED", "POLICY_VIOLATION", "NOT_REACHED"),
        }
        for loaded in dataset.cases:
            actual = (
                loaded.demo.expected.status.value,
                loaded.demo.expected.classification.value,
                loaded.demo.expected.action.value,
            )
            self.assertEqual(actual, expected[loaded.case.case_id])

        adapter = FileQualityContextAdapter(ROOT)
        for system_id, repository_name in (
            ("alpha-reference-sut", "reference_sut"),
            ("alpha-defective-sut", "defective_sut"),
        ):
            request = SkeletonRunRequest(
                context_ref="examples/context/python-alpha-smoke-context.json",
                system_id=system_id,
                requested_skill="unit",
                requirement_title="Smoke context validation",
                requirement_description="Validate deterministic public fixture.",
            )
            resolved = adapter.resolve(request)
            self.assertEqual(resolved.authorized_root.parent.name, repository_name)
            self.assertEqual(len(resolved.authorized_files), 3)

    def test_loads_exactly_ten_cases_and_hash_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._build_dataset(root)
            loader = SmokeDatasetLoader(root)
            first = loader.load("datasets/smoke")
            second = loader.load("datasets/smoke")
            self.assertEqual(tuple(item.case.case_id for item in first.cases), SMOKE_CASE_IDS)
            self.assertEqual(first.dataset_hash, second.dataset_hash)
            self.assertEqual(len(first.dataset_hash), 64)
            self.assertGreater(first.loaded_bytes, 0)
            (root / "sut/support.py").write_text("VALUE = 2\n", encoding="utf-8")
            third = loader.load("datasets/smoke")
            self.assertNotEqual(first.dataset_hash, third.dataset_hash)

    def test_rejects_missing_extra_and_version_mismatch_before_loading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._build_dataset(root)
            (root / "datasets/smoke/SMK-010").rename(root / "datasets/smoke/SMK-011")
            with self.assertRaisesRegex(ContractValidationError, "missing=.*SMK-010"):
                SmokeDatasetLoader(root).load("datasets/smoke")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._build_dataset(root)
            path = root / "datasets/smoke/SMK-004/demo.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["case_version"] = "2.0.0"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ContractValidationError, "versions differ"):
                SmokeDatasetLoader(root).load("datasets/smoke")

    def test_rejects_missing_ref_duplicate_json_key_and_oracle_leak(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._build_dataset(root)
            (root / "sut/module.py").unlink()
            with self.assertRaisesRegex(ContractValidationError, "does not exist"):
                SmokeDatasetLoader(root).load("datasets/smoke")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._build_dataset(root)
            path = root / "datasets/smoke/SMK-001/demo.json"
            path.write_text('{"case_id":"SMK-001","case_id":"SMK-001"}', encoding="utf-8")
            with self.assertRaisesRegex(ContractValidationError, "duplicate JSON field"):
                SmokeDatasetLoader(root).load("datasets/smoke")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._build_dataset(root)
            path = root / "datasets/smoke/SMK-002/demo/analysis.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["oracle_ref"] = "datasets/smoke/SMK-002/oracle/test_oracle.py"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ContractValidationError, "exposes its oracle"):
                SmokeDatasetLoader(root).load("datasets/smoke")

    def test_rejects_dataset_root_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory() as outside:
            with self.assertRaisesRegex(ContractValidationError, "escapes"):
                SmokeDatasetLoader(Path(workspace)).load(Path(outside))

    @staticmethod
    def _build_dataset(root: Path) -> None:
        (root / "sut").mkdir(parents=True)
        (root / "sut/module.py").write_text("def value(): return 1\n", encoding="utf-8")
        (root / "sut/support.py").write_text("VALUE = 1\n", encoding="utf-8")
        context = root / "examples/context/smoke.json"
        context.parent.mkdir(parents=True)
        context.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0-draft",
                    "qa_profile": {"id": "qa-smoke"},
                    "team": {"id": "team-smoke"},
                    "repositories": [
                        {
                            "id": "smoke-repository",
                            "repository_ref": "workspace:sut",
                            "language_profile": "python-pytest",
                            "execution_image": "python@sha256:" + "a" * 64,
                            "read_scope": ["module.py", "support.py"],
                            "write_scope": [".asef/runs/**"],
                        }
                    ],
                    "systems": [
                        {
                            "id": "reference-sut",
                            "repository_ids": ["smoke-repository"],
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
                    "llm_policy": {"provider": "recorded", "model": "fixture"},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        for case_id in SMOKE_CASE_IDS:
            case_dir = root / f"datasets/smoke/{case_id}"
            (case_dir / "oracle").mkdir(parents=True)
            (case_dir / "demo").mkdir()
            case = SmokeDemoContractTests._case_value(case_id)
            (case_dir / "case.json").write_text(
                json.dumps(case, indent=2) + "\n", encoding="utf-8"
            )
            (case_dir / "requirement.md").write_text("Requirement\n", encoding="utf-8")
            (case_dir / "oracle/test_oracle.py").write_text(
                "def test_oracle(): assert True\n", encoding="utf-8"
            )
            demo = valid_demo(case_id)
            (case_dir / "demo.json").write_text(
                json.dumps(demo, indent=2) + "\n", encoding="utf-8"
            )
            analysis = {
                "schema_name": "wf001_analysis",
                "output": {
                    "behaviors": ["value"],
                    "risks": ["incorrect value"],
                    "scenarios": ["SCN-001"],
                    "clarification_required": False,
                },
            }
            artifact = {
                "schema_name": "wf001_unit_artifact",
                "output": {
                    "relative_path": "tests/test_value.py",
                    "content": "def test_value(): assert True\n",
                    "scenario_ids": ["SCN-001"],
                },
            }
            (case_dir / "demo/analysis.json").write_text(
                json.dumps(analysis), encoding="utf-8"
            )
            (case_dir / "demo/artifact-001.json").write_text(
                json.dumps(artifact), encoding="utf-8"
            )


if __name__ == "__main__":
    unittest.main()
