from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import ast
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from asef.adapters.security_case_executor import SecurityCaseExecutor
from asef.adapters.security_dataset import SecurityDatasetLoader
from asef.adapters.security_report_store import SecurityReportStore
from asef.application.security_runner import SecuritySuiteRunner
from asef.contracts import ContractValidationError
from asef.security_contracts import (
    SECURITY_CASE_IDS,
    SecurityCaseStatus,
    SecurityClassification,
    SecurityExecutionObservation,
)


ROOT = Path(__file__).resolve().parents[1]


class SecurityDatasetLoaderTests(unittest.TestCase):
    def test_repository_dataset_loads_exactly_twelve_cases_with_stable_hash(self) -> None:
        loader = SecurityDatasetLoader(ROOT)
        first = loader.load("datasets/security")
        second = loader.load("datasets/security")
        self.assertEqual(
            tuple(item.spec.case_id for item in first.cases), SECURITY_CASE_IDS
        )
        self.assertEqual(first.dataset_hash, second.dataset_hash)
        self.assertGreater(first.loaded_bytes, 0)

    def test_loader_rejects_extra_case_file_and_duplicate_json_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "datasets/security", root / "datasets/security")
            dataset = root / "datasets/security"
            (dataset / "extra.txt").write_text("extra", encoding="utf-8")
            with self.assertRaisesRegex(ContractValidationError, "unexpected fileset"):
                SecurityDatasetLoader(root).load("datasets/security")
            (dataset / "extra.txt").unlink()
            case = dataset / "SEC-001/case.json"
            case.write_text(
                '{"schema_version":"1.0.0","schema_version":"1.0.0"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractValidationError, "duplicate JSON field"):
                SecurityDatasetLoader(root).load("datasets/security")

    def test_loader_rejects_escape_and_noncanonical_fixture_ref(self) -> None:
        loader = SecurityDatasetLoader(ROOT)
        with self.assertRaisesRegex(ContractValidationError, "escapes"):
            loader.load("../outside")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "datasets/security", root / "datasets/security")
            path = root / "datasets/security/SEC-001/case.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["fixture_refs"] = ["datasets/security/SEC-002/fixtures/fixture.txt"]
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ContractValidationError, "not canonical"):
                SecurityDatasetLoader(root).load("datasets/security")


class FakeExecutor:
    def execute(self, loaded, suite_dir, fixture_text):
        del suite_dir
        return SecurityExecutionObservation(
            SecurityCaseStatus.PASSED,
            SecurityClassification.CONTROL_ENFORCED,
            1,
            {"case_number": int(loaded.spec.case_id[-3:]), "fixture_loaded": bool(fixture_text)},
        )


class OneFailureExecutor(FakeExecutor):
    def execute(self, loaded, suite_dir, fixture_text):
        if loaded.spec.case_id == "SEC-004":
            return SecurityExecutionObservation(
                SecurityCaseStatus.FAILED,
                SecurityClassification.CONTROL_FAILED,
                1,
                {"link_rejected": False},
                "LINK_NOT_REJECTED",
                "Link was not rejected",
            )
        return super().execute(loaded, suite_dir, fixture_text)


class SecuritySuiteRunnerTests(unittest.TestCase):
    def test_application_runner_does_not_import_adapters_or_docker(self) -> None:
        path = ROOT / "src/asef/application/security_runner.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertFalse(any("adapters" in item or "docker" in item for item in imports))

    def test_runner_persists_twelve_results_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            shutil.copytree(ROOT / "datasets/security", workspace / "datasets/security")
            runner = SecuritySuiteRunner(
                SecurityDatasetLoader(workspace),
                FakeExecutor(),
                SecurityReportStore(workspace),
                asef_version="0.1.0a4",
                environment="test",
            )
            output = runner.run("datasets/security", ".asef/security")
            self.assertTrue(output.report.accepted)
            self.assertEqual(output.report.passed, 12)
            self.assertTrue(output.suite_json.is_file())
            self.assertTrue(output.suite_markdown.is_file())
            self.assertEqual(
                len(list((output.suite_dir / "results").glob("SEC-*.json"))), 12
            )

    def test_control_failure_does_not_stop_later_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            shutil.copytree(ROOT / "datasets/security", workspace / "datasets/security")
            output = SecuritySuiteRunner(
                SecurityDatasetLoader(workspace),
                OneFailureExecutor(),
                SecurityReportStore(workspace),
                asef_version="0.1.0a4",
                environment="test",
            ).run("datasets/security", ".asef/security")
            self.assertFalse(output.report.accepted)
            self.assertEqual((output.report.passed, output.report.failed), (11, 1))
            self.assertEqual(output.report.results[-1].case_id, "SEC-012")

    def test_pure_internal_executors_pass_without_docker(self) -> None:
        dataset = SecurityDatasetLoader(ROOT).load("datasets/security")
        selected = {
            item.spec.case_id: item
            for item in dataset.cases
            if item.spec.case_id in {"SEC-003", "SEC-009", "SEC-010", "SEC-012"}
        }
        with tempfile.TemporaryDirectory() as directory:
            suite = Path(directory)
            executor = SecurityCaseExecutor()
            loader = SecurityDatasetLoader(ROOT)
            for case_id in sorted(selected):
                loaded = selected[case_id]
                observation = executor.execute(
                    loaded,
                    suite,
                    loader.read_fixture(loaded.spec.fixture_refs[0]),
                )
                with self.subTest(case_id=case_id):
                    self.assertIs(observation.status, SecurityCaseStatus.PASSED)

    def test_report_store_rejects_output_outside_asef(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = SecurityReportStore(Path(directory))
            with self.assertRaisesRegex(ContractValidationError, "below .asef"):
                store.validate_output_root("outside")

    def test_docker_handlers_normalize_expected_control_facts_with_fake_runner(self) -> None:
        executor = SecurityCaseExecutor()
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            with patch.object(
                executor,
                "_json_docker",
                return_value=({"sentinel_present": False}, object()),
            ):
                self.assertFalse(executor._secret_absent(workspace, "")["sentinel_present"])
            with patch.object(
                executor,
                "_json_docker",
                return_value=({"blocked": True}, object()),
            ):
                self.assertTrue(executor._network_blocked(workspace, "")["network_blocked"])
            with patch.object(
                executor,
                "_json_docker",
                return_value=({"blocked": True, "spawned": 15}, object()),
            ):
                self.assertEqual(executor._pids_limited(workspace, "")["spawned"], 15)
            with patch.object(
                executor,
                "_json_docker",
                return_value=({"socket_present": False}, object()),
            ):
                self.assertFalse(executor._socket_absent(workspace, "")["socket_present"])

            class Runner:
                def __init__(self, result):
                    self.result = result

                def run(self, *args, **kwargs):
                    del args, kwargs
                    return self.result

            memory = SimpleNamespace(exit_code=137)
            with patch.object(executor, "_runner", return_value=Runner(memory)):
                self.assertEqual(executor._memory_limited(workspace, "")["exit_code"], 137)
            timeout = SimpleNamespace(timed_out=True, exit_code=124)
            with patch.object(executor, "_runner", return_value=Runner(timeout)):
                self.assertTrue(executor._timeout_enforced(workspace, "")["timed_out"])
            output = SimpleNamespace(stdout_truncated=True, stderr_truncated=True)
            with patch.object(executor, "_runner", return_value=Runner(output)):
                facts = executor._output_truncated(workspace, "")
                self.assertTrue(facts["stdout_truncated"])
                self.assertTrue(facts["stderr_truncated"])


if __name__ == "__main__":
    unittest.main()
