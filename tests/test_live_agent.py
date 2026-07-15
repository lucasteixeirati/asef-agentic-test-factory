from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from asef.adapters.gateway import ModelResult, OpenAIResponsesGateway
from asef.adapters.live_agent import LiveAgentAdapter, LiveAgentConfig
from asef.adapters.run_store import JsonRunStore
from asef.adapters.workspace import EphemeralWorkspaceAdapter
from asef.application.generate_unit import GenerateUnitTestService
from asef.application.ports import (
    AnalysisResult,
    ProviderPermanentError,
    ProviderTransientError,
    ResolvedQualityContext,
)
from asef.application.prepare_run import PrepareRunService
from asef.contracts import ContextSnapshot, SkeletonRunRequest, TestExecutionOutcome
from asef.evaluation_contracts import build_correction_feedback
from asef.outcomes import RunClassification, RunStatus
from asef.skills.unit import UnitSkill
from asef.cli import main


def request(*, budget: float = 1.0) -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title="Add integers",
        requirement_description="The add function returns the integer sum.",
        execution_mode="live",
        api_budget_brl=budget,
    )


def analysis_output() -> dict[str, object]:
    return {
        "behaviors": ["return the sum"],
        "risks": ["negative values"],
        "scenarios": ["positive integers"],
        "clarification_required": False,
    }


def artifact_output(content: str = "def test_add():\n    assert 1 + 1 == 2\n") -> dict[str, object]:
    return {
        "relative_path": "tests_generated/test_calculator.py",
        "content": content,
        "scenario_ids": ["SCN-001"],
    }


class FakeGateway:
    def __init__(self, outputs: list[dict[str, object] | Exception]) -> None:
        self.outputs = outputs
        self.calls: list[dict[str, object]] = []

    def generate(self, *, prompt, schema, schema_name):
        self.calls.append({"prompt": prompt, "schema": schema, "schema_name": schema_name})
        value = self.outputs.pop(0)
        if isinstance(value, Exception):
            raise value
        return ModelResult(
            output=value,
            model="fake-live-model",
            response_id=f"response-{len(self.calls)}",
            input_tokens=100,
            output_tokens=50,
            provider="openai",
            latency_ms=12,
        )


class ContextPort:
    def resolve(self, request):
        return ResolvedQualityContext(
            ContextSnapshot(
                source_sha256="a" * 64,
                qa_profile_id="qa",
                team_id="team",
                system_id=request.system_id,
                repository_id="repo",
                skill_id="unit",
                language_profile="python-pytest",
                image="python@sha256:" + "b" * 64,
                provider="openai",
                model="fake-live-model",
                mode="live",
                read_scopes=("calculator.py",),
                write_scopes=(".asef/runs/**",),
            ),
            Path("examples/calculator").resolve(),
            ("calculator.py",),
        )


class LiveAgentContractTests(unittest.TestCase):
    def adapter(self, outputs, cassette_dir=None, rate=10.0):
        gateway = FakeGateway(outputs)
        adapter = LiveAgentAdapter(
            gateway,
            LiveAgentConfig(rate, rate, cassette_dir),
        )
        adapter.bind_context(ContextPort().resolve(request()))
        return adapter, gateway

    def test_analysis_generation_and_correction_use_strict_typed_schemas(self) -> None:
        adapter, gateway = self.adapter(
            [analysis_output(), artifact_output(), artifact_output("def test_add():\n    assert 2 + 2 == 4\n")]
        )
        analysis = adapter.analyze(request())
        generated = adapter.generate(request(), analysis)
        corrected = adapter.correct(
            request(),
            generated.artifact,
            build_correction_feedback(TestExecutionOutcome.TEST_ERROR, "", "failure"),
        )
        self.assertEqual(corrected.artifact.attempt, 2)
        self.assertEqual([call["schema_name"] for call in gateway.calls], [
            "wf001_analysis", "wf001_unit_artifact", "wf001_unit_artifact"
        ])
        self.assertTrue(all(call["schema"]["additionalProperties"] is False for call in gateway.calls))
        self.assertEqual(analysis.provider, "openai")
        self.assertEqual(analysis.latency_ms, 12)
        self.assertGreater(analysis.estimated_cost_brl, 0)

    def test_non_finite_rates_are_rejected(self) -> None:
        for value in (float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "positive"):
                LiveAgentConfig(value, 1.0).validate()

    def test_generate_revalidates_sensitive_request_before_provider_call(self) -> None:
        adapter, gateway = self.adapter([artifact_output()])
        sensitive = SkeletonRunRequest(
            **{
                **request().to_dict(),
                "requirement_description": "api_key=do-not-send",
            }
        )
        analysis = AnalysisResult(
            behaviors=("sum",),
            risks=("negative",),
            scenarios=("integers",),
            clarification_required=False,
            model="fake-live-model",
            response_id="response-analysis",
            provider="openai",
        )
        with self.assertRaisesRegex(ValueError, "sensitive marker"):
            adapter.generate(sensitive, analysis)
        self.assertEqual(gateway.calls, [])

    def test_cassette_omits_prompt_and_sanitizes_provider_output(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            sensitive_output = analysis_output()
            sensitive_output["behaviors"] = ["api_key=do-not-persist"]
            adapter, _ = self.adapter(
                [sensitive_output], Path(directory), rate=1.0
            )
            adapter.analyze(request())
            cassette = json.loads(next(Path(directory).glob("*.json")).read_text(encoding="utf-8"))
            serialized = json.dumps(cassette)
            self.assertNotIn("do-not-persist", serialized)
            self.assertNotIn("prompt", cassette)
            self.assertIn("prompt_sha256", cassette)

    def test_application_persists_call_and_stops_when_observed_cost_exceeds_budget(self) -> None:
        adapter, gateway = self.adapter([analysis_output()], rate=100.0)
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            store = JsonRunStore(Path(directory))
            service = GenerateUnitTestService(
                PrepareRunService(ContextPort(), store),
                adapter,
                UnitSkill(),
                EphemeralWorkspaceAdapter(),
                store,
            )
            result = service.execute(request(budget=0.0001))
            self.assertEqual(result.state.status, RunStatus.BUDGET_EXHAUSTED)
            self.assertEqual(result.state.classification, RunClassification.BUDGET_ERROR)
            self.assertEqual(result.state.usage.model_calls, 1)
            self.assertGreater(result.state.usage.estimated_cost_brl, result.state.budgets.api_budget_brl)
            self.assertEqual(len(gateway.calls), 1)

    def test_permanent_provider_failure_is_not_retried_and_reservation_is_persisted(self) -> None:
        adapter, gateway = self.adapter([ProviderPermanentError("denied")])
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            store = JsonRunStore(Path(directory))
            result = GenerateUnitTestService(
                PrepareRunService(ContextPort(), store), adapter, UnitSkill(), EphemeralWorkspaceAdapter(), store
            ).execute(request())
            self.assertEqual(result.state.status, RunStatus.FAILED)
            self.assertEqual(result.state.classification, RunClassification.PROVIDER_ERROR)
            self.assertEqual(result.state.usage.model_calls, 1)
            self.assertEqual(len(gateway.calls), 1)
            persisted = store.load_state(result.state.run_id)
            self.assertEqual(persisted.usage.model_calls, 1)

    def test_transient_analysis_failure_consumes_one_central_retry(self) -> None:
        adapter, gateway = self.adapter(
            [ProviderTransientError("temporary"), analysis_output(), artifact_output()]
        )
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            store = JsonRunStore(Path(directory))
            result = GenerateUnitTestService(
                PrepareRunService(ContextPort(), store), adapter, UnitSkill(), EphemeralWorkspaceAdapter(), store
            ).execute(request())
            self.assertEqual(result.state.status, RunStatus.STATIC_VALIDATION)
            self.assertEqual(result.state.usage.model_calls, 3)
            self.assertEqual(result.state.usage.provider_retries, 1)
            self.assertEqual(len(gateway.calls), 3)

    def test_invalid_observed_output_preserves_usage_before_retry(self) -> None:
        adapter, gateway = self.adapter(
            [{"unexpected": True}, analysis_output(), artifact_output()], rate=10.0
        )
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            store = JsonRunStore(Path(directory))
            result = GenerateUnitTestService(
                PrepareRunService(ContextPort(), store), adapter, UnitSkill(), EphemeralWorkspaceAdapter(), store
            ).execute(request())
            self.assertEqual(result.state.status, RunStatus.STATIC_VALIDATION)
            self.assertEqual(result.state.usage.model_calls, 3)
            self.assertEqual(result.state.usage.provider_retries, 1)
            self.assertEqual(result.state.usage.input_tokens, 300)
            self.assertEqual(result.state.usage.output_tokens, 150)
            self.assertEqual(len(result.state.facts["provider_calls"]), 3)
            self.assertEqual(len(gateway.calls), 3)

    def test_public_generate_live_uses_explicit_context_and_fake_transport(self) -> None:
        gateway = FakeGateway([analysis_output(), artifact_output()])
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            stdout, stderr = StringIO(), StringIO()
            with (
                patch("asef.cli.OpenAIResponsesGateway", return_value=gateway),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                code = main(
                    [
                        "generate",
                        "--mode", "live",
                        "--context", "examples/context/walking-skeleton-live-context.example.json",
                        "--model", "gpt-5.4",
                        "--api-budget-brl", "1",
                        "--input-cost-brl-per-million", "1",
                        "--output-cost-brl-per-million", "1",
                        "--output", directory,
                    ]
                )
            payload = json.loads(stdout.getvalue())
            self.assertEqual(code, 0, stderr.getvalue())
            self.assertEqual(payload["status"], "STATIC_VALIDATION")
            self.assertEqual(len(gateway.calls), 2)

    def test_public_live_requires_explicit_context_before_provider_creation(self) -> None:
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["generate", "--mode", "live", "--api-budget-brl", "1"])
        self.assertEqual(code, 2)
        self.assertIn("explicit --context", stderr.getvalue())

    def test_sensitive_authorized_source_is_blocked_before_provider_call(self) -> None:
        adapter, gateway = self.adapter([analysis_output()])
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as source_directory, tempfile.TemporaryDirectory(
            dir=Path(".asef")
        ) as run_directory:
            source_root = Path(source_directory)
            (source_root / "source.py").write_text(
                "api_key=super-secret-value\n", encoding="utf-8"
            )
            base = ContextPort().resolve(request())
            resolved = ResolvedQualityContext(base.snapshot, source_root, ("source.py",))

            class SensitiveContextPort:
                def resolve(self, ignored):
                    del ignored
                    return resolved

            store = JsonRunStore(Path(run_directory))
            result = GenerateUnitTestService(
                PrepareRunService(SensitiveContextPort(), store),
                adapter,
                UnitSkill(),
                EphemeralWorkspaceAdapter(),
                store,
            ).execute(request())
            self.assertEqual(result.state.status, RunStatus.POLICY_BLOCKED)
            self.assertEqual(result.state.classification, RunClassification.POLICY_VIOLATION)
            self.assertEqual(result.state.usage.model_calls, 0)
            self.assertEqual(gateway.calls, [])

    def test_sensitive_requirement_is_blocked_before_provider_call(self) -> None:
        adapter, gateway = self.adapter([analysis_output()])
        sensitive_request = SkeletonRunRequest(
            **{
                **request().to_dict(),
                "requirement_description": "api_key=do-not-send",
            }
        )
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory:
            store = JsonRunStore(Path(directory))
            result = GenerateUnitTestService(
                PrepareRunService(ContextPort(), store), adapter, UnitSkill(), EphemeralWorkspaceAdapter(), store
            ).execute(sensitive_request)
            self.assertEqual(result.state.status, RunStatus.POLICY_BLOCKED)
            self.assertEqual(result.state.usage.model_calls, 0)
            self.assertEqual(gateway.calls, [])

    def test_requested_cassette_failure_preserves_usage_as_infrastructure_error(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(".asef")) as directory, tempfile.TemporaryDirectory(
            dir=Path(".asef")
        ) as run_directory:
            cassette_target = Path(directory) / "not-a-directory"
            cassette_target.write_text("occupied", encoding="utf-8")
            adapter, gateway = self.adapter(
                [analysis_output()], cassette_dir=cassette_target, rate=10.0
            )
            store = JsonRunStore(Path(run_directory))
            result = GenerateUnitTestService(
                PrepareRunService(ContextPort(), store), adapter, UnitSkill(), EphemeralWorkspaceAdapter(), store
            ).execute(request())
            self.assertEqual(result.state.status, RunStatus.FAILED)
            self.assertEqual(result.state.classification, RunClassification.INFRASTRUCTURE_ERROR)
            self.assertEqual(result.state.usage.model_calls, 1)
            self.assertEqual(result.state.usage.input_tokens, 100)
            self.assertEqual(len(gateway.calls), 1)


@unittest.skipUnless(os.environ.get("ASEF_RUN_LIVE_TESTS") == "1", "manual live test disabled")
class ManualOpenAILiveSmokeTests(unittest.TestCase):
    def test_bounded_analysis_call(self) -> None:
        model = os.environ["ASEF_OPENAI_MODEL"]
        budget = float(os.environ["ASEF_LIVE_BUDGET_BRL"])
        input_rate = float(os.environ["ASEF_OPENAI_INPUT_BRL_PER_MTOK"])
        output_rate = float(os.environ["ASEF_OPENAI_OUTPUT_BRL_PER_MTOK"])
        adapter = LiveAgentAdapter(
            OpenAIResponsesGateway(model=model, api_budget_brl=budget, max_output_tokens=300),
            LiveAgentConfig(input_rate, output_rate),
        )
        adapter.bind_context(ContextPort().resolve(request(budget=budget)))
        result = adapter.analyze(request(budget=budget))
        self.assertEqual(result.provider, "openai")
        self.assertGreater(result.input_tokens, 0)
        self.assertLessEqual(result.estimated_cost_brl, budget)
        print(
            "LIVE_SMOKE_METRICS="
            + json.dumps(
                {
                    "estimated_cost_brl": result.estimated_cost_brl,
                    "input_tokens": result.input_tokens,
                    "latency_ms": result.latency_ms,
                    "model": result.model,
                    "output_tokens": result.output_tokens,
                    "provider": result.provider,
                    "response_id": result.response_id,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
