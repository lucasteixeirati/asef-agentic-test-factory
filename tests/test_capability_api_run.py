from __future__ import annotations

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from asef.adapters.api_plan_agent import ApiPlanAgentAdapter
from asef.adapters.api_report_store import ApiReportStore
from asef.adapters.capability_run_store import CapabilityRunStore
from asef.adapters.gateway import ModelResult
from asef.application.ports import ProviderTransientError
from asef.api_contracts import ApiExecutionResult, ApiScenarioResult
from asef.application.backend_api_run import (
    ExecuteBackendApiPlanService,
    GenerateBackendApiPlanService,
)
from asef.capability_runs import (
    CapabilityRunBudgets,
    CapabilityRunClassification,
    CapabilityRunContractError,
    CapabilityRunState,
    CapabilityRunStatus,
    capability_run_from_dict,
)
from asef.skills.backend_api import BackendApiPolicy


def _model_output() -> dict[str, object]:
    return {
        "scenarios": [
            {
                "description": "health",
                "method": "GET",
                "path": "/health",
                "expected_status": 200,
                "expected_json_properties": [{"name": "status", "value": "ok"}],
            }
        ]
    }


class _Gateway:
    def __init__(self, before_call=None) -> None:
        self.before_call = before_call
        self.calls = 0

    def generate(self, *, prompt, schema, schema_name):
        del prompt, schema
        self.calls += 1
        if self.before_call:
            self.before_call()
        self.schema_name = schema_name
        return ModelResult(
            output=_model_output(),
            model="recorded-test",
            response_id="response-api-1",
            input_tokens=70,
            output_tokens=40,
            provider="recorded",
        )


class _Executor:
    def __init__(self, status: str = "PASSED") -> None:
        self.status = status
        self.calls = 0

    def execute(self, plan):
        self.calls += 1
        scenario_status = "PASSED" if self.status == "PASSED" else self.status
        return ApiExecutionResult(
            plan_id=plan.plan_id,
            status=self.status,
            tests=1,
            passed=1 if self.status == "PASSED" else 0,
            failed=1 if self.status == "FAILED" else 0,
            errors=1 if self.status == "ERROR" else 0,
            scenarios=(
                ApiScenarioResult(
                    "SCN-001",
                    scenario_status,
                    200,
                    1,
                    15,
                    None if scenario_status == "PASSED" else f"TEST_{scenario_status}",
                ),
            ),
        )


class CapabilityApiRunTests(unittest.TestCase):
    def setUp(self) -> None:
        Path(".asef").mkdir(exist_ok=True)

    def _services(self, root: Path, gateway=None, executor=None, budgets=None):
        store = CapabilityRunStore(root)
        policy = BackendApiPolicy(allowed_ports=(8765,))
        generation = GenerateBackendApiPlanService(
            ApiPlanAgentAdapter(gateway or _Gateway(), policy),
            store,
        )
        execution = ExecuteBackendApiPlanService(
            executor or _Executor(),
            store,
            ApiReportStore(),
            asef_version="0.1.0a7",
        )
        output = generation.execute(
            "Verify the local health endpoint",
            "http://127.0.0.1:8765",
            budgets,
        )
        return store, execution, output

    def test_state_round_trip_rejects_fabricated_terminal_flag(self) -> None:
        state = CapabilityRunState("WF-API-001", "backend-api", "python-pytest")
        raw = state.to_dict()
        self.assertEqual(state.run_id, capability_run_from_dict(raw).run_id)
        raw["terminal"] = True
        with self.assertRaisesRegex(CapabilityRunContractError, "terminal flag"):
            capability_run_from_dict(raw)

    def test_run_is_persisted_before_model_call_and_plan_waits_for_review(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            gateway = _Gateway(lambda: self.assertEqual(1, len(list(root.iterdir()))))
            store, _, output = self._services(root, gateway=gateway)
            self.assertEqual(CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW, output.state.status)
            self.assertEqual(CapabilityRunClassification.PLAN_READY_FOR_REVIEW, output.state.classification)
            self.assertEqual((1, 70, 40), (output.state.usage.model_calls, output.state.usage.input_tokens, output.state.usage.output_tokens))
            self.assertEqual(output.plan.plan_id, store.load_plan(output.state).plan_id)
            self.assertEqual("backend_api_plan_v1", gateway.schema_name)

    def test_plan_tampering_blocks_resume_before_executor(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            executor = _Executor()
            store, execution, output = self._services(root, executor=executor)
            plan_path = store.run_dir(output.state.run_id) / "artifacts" / "api-plan.json"
            plan_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(CapabilityRunContractError, "integrity mismatch"):
                execution.execute(output.state.run_id)
            self.assertEqual(0, executor.calls)

    def test_request_budget_exhausts_without_execution(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            executor = _Executor()
            budgets = CapabilityRunBudgets(max_requests=1)
            store, execution, output = self._services(Path(directory), executor=executor, budgets=budgets)
            state = store.load_state(output.state.run_id)
            state.usage.requests = 1
            store.save_state(state)
            result = execution.execute(state.run_id)
            self.assertEqual(CapabilityRunStatus.BUDGET_EXHAUSTED, result.state.status)
            self.assertEqual(CapabilityRunClassification.BUDGET_ERROR, result.state.classification)
            self.assertEqual(0, executor.calls)

    def test_success_reconciles_terminal_manifest_and_evidence_hashes(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store, execution, generated = self._services(Path(directory))
            completed = execution.execute(generated.state.run_id)
            self.assertEqual(CapabilityRunStatus.SUCCEEDED, completed.state.status)
            self.assertEqual(CapabilityRunClassification.ACCEPTED, completed.state.classification)
            self.assertEqual(1, completed.state.usage.requests)
            kinds = {item.kind for item in completed.state.evidence_refs}
            self.assertEqual(
                {"api_test_plan", "api_execution_result", "api_report_json", "api_report_markdown"},
                kinds,
            )
            run_dir = store.run_dir(completed.state.run_id)
            for ref in completed.state.evidence_refs:
                import hashlib
                self.assertEqual(ref.sha256, hashlib.sha256((run_dir / ref.relative_path).read_bytes()).hexdigest())
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["terminal"])
            self.assertEqual("ACCEPTED", manifest["classification"])

    def test_functional_failure_is_terminal_but_not_infrastructure(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            _, execution, generated = self._services(Path(directory), executor=_Executor("FAILED"))
            completed = execution.execute(generated.state.run_id)
            self.assertEqual(CapabilityRunStatus.FAILED, completed.state.status)
            self.assertEqual(CapabilityRunClassification.FUNCTIONAL_FAILURE, completed.state.classification)

    def test_state_and_manifest_bundle_is_restored_when_second_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            store, _, generated = self._services(Path(directory))
            run_dir = store.run_dir(generated.state.run_id)
            before = {
                name: (run_dir / name).read_bytes()
                for name in ("state.json", "manifest.json")
            }
            state = store.load_state(generated.state.run_id)
            state.facts["new"] = "value"
            import os
            original_replace = os.replace
            calls = 0

            def fail_second(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected replace failure")
                return original_replace(source, target)

            with patch("asef.adapters.capability_run_store.os.replace", side_effect=fail_second):
                with self.assertRaisesRegex(OSError, "injected"):
                    store.save_state(state)
            after = {
                name: (run_dir / name).read_bytes()
                for name in ("state.json", "manifest.json")
            }
            self.assertEqual(before, after)

    def test_transient_provider_failure_consumes_one_retry_and_second_model_call(self) -> None:
        class RetryGateway:
            def __init__(self) -> None:
                self.calls = 0

            def generate(self, **kwargs):
                del kwargs
                self.calls += 1
                if self.calls == 1:
                    raise ProviderTransientError("temporary")
                return ModelResult(
                    output=_model_output(), model="retry", response_id="response-2",
                    input_tokens=30, output_tokens=20, provider="openai",
                )

        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            gateway = RetryGateway()
            store = CapabilityRunStore(root)
            policy = BackendApiPolicy(allowed_ports=(8765,))
            output = GenerateBackendApiPlanService(
                ApiPlanAgentAdapter(gateway, policy), store
            ).execute(
                "Verify health", "http://127.0.0.1:8765",
                CapabilityRunBudgets(max_model_calls=2, max_provider_retries=1),
            )
            self.assertEqual(CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW, output.state.status)
            self.assertEqual((2, 1), (output.state.usage.model_calls, output.state.usage.provider_retries))
            self.assertEqual(2, gateway.calls)


if __name__ == "__main__":
    unittest.main()
