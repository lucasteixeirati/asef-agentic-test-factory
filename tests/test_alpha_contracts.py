from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

from asef.contracts import ContractValidationError, EvidenceRef
from asef.evaluation_contracts import (
    CoverageResult,
    DatasetExposure,
    DatasetKind,
    MutationResult,
    OraclePolicy,
    dataset_case_from_dict,
)
from asef.languages import get_language_profile


DIGEST = "b" * 64
RAW_REF = EvidenceRef("raw", "results/raw.json", DIGEST)
ROOT = Path(__file__).resolve().parents[1]


class AlphaDatasetContractTests(unittest.TestCase):
    def test_smoke_cases_are_versioned_and_oracles_are_prompt_isolated(self) -> None:
        paths = sorted((ROOT / "datasets" / "smoke").glob("SMK-*/case.json"))
        self.assertEqual(
            [path.parent.name for path in paths],
            [f"SMK-{number:03d}" for number in range(1, 11)],
        )
        for path in paths:
            with self.subTest(case=path.parent.name):
                case = dataset_case_from_dict(json.loads(path.read_text(encoding="utf-8")))
                self.assertIs(case.kind, DatasetKind.SMOKE)
                self.assertIs(case.exposure, DatasetExposure.PUBLIC)
                self.assertEqual(case.case_id, path.parent.name)
                if case.oracle_ref:
                    self.assertIs(case.oracle_policy, OraclePolicy.PROMPT_ISOLATED)
                    self.assertNotIn(case.oracle_ref, case.generation_input_refs)
                    self.assertIn(case.oracle_ref, case.evaluation_input_refs)
                else:
                    self.assertIs(case.oracle_policy, OraclePolicy.NONE)
                for ref in (
                    case.sut_ref,
                    case.requirement_ref,
                    *case.generation_input_refs,
                    *case.evaluation_input_refs,
                ):
                    self.assertTrue((ROOT / ref).exists(), ref)

    def test_dataset_rejects_oracle_leakage_and_traversal(self) -> None:
        value = json.loads(
            (ROOT / "datasets/smoke/SMK-001/case.json").read_text(encoding="utf-8")
        )
        value["generation_input_refs"].append(value["oracle_ref"])
        with self.assertRaisesRegex(ContractValidationError, "oracle_ref"):
            dataset_case_from_dict(value)

        value = json.loads(
            (ROOT / "datasets/smoke/SMK-001/case.json").read_text(encoding="utf-8")
        )
        value["sut_ref"] = "../outside"
        with self.assertRaisesRegex(ContractValidationError, "inside the repository"):
            dataset_case_from_dict(value)

    def test_dataset_rejects_unknown_fields_and_malformed_version(self) -> None:
        path = ROOT / "datasets/smoke/SMK-001/case.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["unexpected"] = True
        with self.assertRaisesRegex(ContractValidationError, "unknown fields"):
            dataset_case_from_dict(value)

        value = json.loads(path.read_text(encoding="utf-8"))
        value["version"] = "latest"
        with self.assertRaisesRegex(ContractValidationError, "major.minor.patch"):
            dataset_case_from_dict(value)


class QualityMetricContractTests(unittest.TestCase):
    def test_coverage_normalizes_line_and_branch_independently(self) -> None:
        result = CoverageResult(
            tool_id="coverage.py",
            tool_version="7.10.7",
            scope=("src/reference_sut",),
            lines_covered=9,
            lines_total=10,
            branches_covered=3,
            branches_total=4,
            duration_ms=150,
            raw_result_ref=RAW_REF,
            limitations=("fixture",),
        )
        value = result.to_dict()
        self.assertEqual(value["line_percent"], 90.0)
        self.assertEqual(value["branch_percent"], 75.0)
        json.dumps(value)

    def test_zero_coverage_denominator_is_not_invented(self) -> None:
        result = CoverageResult(
            "coverage.py", "7.10.7", ("empty",), 0, 0, 0, 0, 1, RAW_REF
        )
        self.assertIsNone(result.line_percent)
        self.assertIsNone(result.branch_percent)

    def test_mutation_outcomes_and_budget_are_consistent(self) -> None:
        result = MutationResult(
            tool_id="mutmut",
            tool_version="3.6.0",
            scope=("src/reference_sut",),
            mutants_total=10,
            killed=7,
            survived=2,
            invalid=1,
            timed_out=0,
            not_run=0,
            duration_ms=500,
            max_mutants=10,
            timeout_seconds=30,
            raw_result_ref=RAW_REF,
        )
        self.assertEqual(result.to_dict()["mutation_score"], 77.78)

        with self.assertRaisesRegex(ContractValidationError, "must equal"):
            MutationResult(
                "mutmut", "3.6.0", ("src",), 10, 1, 1, 0, 0, 0, 1, 10, 30, RAW_REF
            ).validate()


class PythonReferenceProfileTests(unittest.TestCase):
    def test_python_profile_declares_current_state_without_overclaiming(self) -> None:
        profile = get_language_profile("python-pytest")
        self.assertEqual(profile.current_support_level, "experimental")
        self.assertEqual(profile.target_support_level, "reference")
        statuses = {item.capability_id: item.implementation_status for item in profile.capabilities}
        self.assertEqual(statuses["unit"], "partial")
        self.assertEqual(statuses["coverage"], "available")
        self.assertEqual(statuses["mutation"], "available")
        adapters = {item.capability_id: item.adapter_id for item in profile.capabilities}
        self.assertEqual(adapters["coverage"], "python-quality-docker")
        self.assertEqual(adapters["mutation"], "python-quality-docker")

    def test_reference_and_defective_suts_are_distinct_and_immutable_fixtures(self) -> None:
        correct = _load_module(
            "correct_arithmetic",
            ROOT / "examples/python-alpha/reference_sut/src/reference_sut/arithmetic.py",
        )
        defective = _load_module(
            "defective_arithmetic",
            ROOT / "examples/python-alpha/defective_sut/src/reference_sut/arithmetic.py",
        )
        self.assertEqual(correct.add(-2, 3), 1)
        with self.assertRaises(ValueError):
            correct.divide(1, 0)
        self.assertEqual(defective.divide(1, 0), 0.0)

        manifest = json.loads(
            (ROOT / "examples/python-alpha/fixture-manifest.json").read_text(encoding="utf-8")
        )
        for relative_path, expected_hash in manifest["files"].items():
            actual = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(actual, expected_hash, relative_path)

    def test_oracle_files_are_valid_python_but_not_imported_by_contract_tests(self) -> None:
        for path in sorted((ROOT / "datasets/smoke").glob("SMK-*/oracle/*.py")):
            with self.subTest(path=path):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


class CoreImportBoundaryTests(unittest.TestCase):
    def test_core_contract_modules_do_not_import_tooling_or_frameworks(self) -> None:
        forbidden = {"pytest", "coverage", "mutmut", "docker", "openai", "langgraph", "pydantic_ai"}
        paths = (
            ROOT / "src/asef/contracts.py",
            ROOT / "src/asef/evaluation_contracts.py",
            ROOT / "src/asef/security_contracts.py",
            ROOT / "src/asef/outcomes.py",
            ROOT / "src/asef/languages.py",
        )
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".", 1)[0])
            self.assertFalse(imported & forbidden, f"{path}: {sorted(imported & forbidden)}")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load fixture: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
