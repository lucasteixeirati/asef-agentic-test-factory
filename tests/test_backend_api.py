from __future__ import annotations

import json
import io
import threading
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from asef.adapters.http_api_execution import LoopbackHttpApiExecutor
from asef.adapters.api_plan_agent import ApiPlanAgentAdapter
from asef.adapters.api_plan_file import ApiPlanFileAdapter
from asef.adapters.gateway import ModelResult
from asef.api_contracts import ApiAssertion, ApiScenario, ApiTestPlan
from asef.skills.backend_api import BackendApiPolicy, BackendApiPolicyError, BackendApiSkill
from asef.cli import main


class _FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        if self.path == "/health":
            self._json(200, {"status": "ok", "service": {"name": "fixture"}})
        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/health")
            self.end_headers()
        elif self.path == "/large":
            content = b"x" * 64
            self.send_response(200)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self._json(404, {"error": "not-found"})

    def log_message(self, format: str, *args: object) -> None:
        return

    def _json(self, status: int, payload: dict[str, object]) -> None:
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


class BackendApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def plan(self, path: str = "/health", expected_status: int = 200) -> ApiTestPlan:
        return ApiTestPlan(
            plan_id="API-PLAN-001",
            base_url=f"http://127.0.0.1:{self.port}",
            scenarios=(
                ApiScenario(
                    scenario_id="SCN-001",
                    description="health is available",
                    method="GET",
                    path=path,
                    assertion=ApiAssertion(expected_status, {"status": "ok"} if path == "/health" else None),
                ),
            ),
        )

    def test_validates_and_executes_local_rest_plan(self) -> None:
        policy = BackendApiPolicy(allowed_ports=(self.port,))
        validation = BackendApiSkill(policy).validate(self.plan())
        result = LoopbackHttpApiExecutor(policy).execute(self.plan())
        self.assertEqual("PASSED", validation["status"])
        self.assertEqual("loopback-only", validation["network_scope"])
        self.assertEqual((1, 1, 0, 0), (result.tests, result.passed, result.failed, result.errors))

    def test_rejects_external_host(self) -> None:
        plan = ApiTestPlan("API-PLAN-002", "http://example.com:80", self.plan().scenarios)
        with self.assertRaisesRegex(BackendApiPolicyError, "loopback allowlist"):
            BackendApiSkill().validate(plan)

    def test_rejects_mutating_method_by_default(self) -> None:
        scenario = ApiScenario("SCN-001", "mutation", "POST", "/items", ApiAssertion(201), json_body={"name": "x"})
        plan = ApiTestPlan("API-PLAN-003", f"http://127.0.0.1:{self.port}", (scenario,))
        with self.assertRaisesRegex(BackendApiPolicyError, "method is not allowed"):
            BackendApiSkill().validate(plan)

    def test_rejects_persisted_sensitive_header(self) -> None:
        scenario = ApiScenario("SCN-001", "secret", "GET", "/health", ApiAssertion(200), headers=(("Authorization", "redacted"),))
        plan = ApiTestPlan("API-PLAN-004", f"http://127.0.0.1:{self.port}", (scenario,))
        with self.assertRaisesRegex(BackendApiPolicyError, "sensitive headers"):
            BackendApiSkill().validate(plan)

    def test_rejects_caller_controlled_transport_header(self) -> None:
        scenario = ApiScenario("SCN-001", "smuggling guard", "GET", "/health", ApiAssertion(200), headers=(("Transfer-Encoding", "chunked"),))
        plan = ApiTestPlan("API-PLAN-006", f"http://127.0.0.1:{self.port}", (scenario,))
        with self.assertRaisesRegex(BackendApiPolicyError, "transport headers"):
            BackendApiSkill().validate(plan)

    def test_rejects_sensitive_query_parameter(self) -> None:
        plan = self.plan("/health?token=redacted", 200)
        with self.assertRaisesRegex(BackendApiPolicyError, "query parameters"):
            BackendApiSkill().validate(plan)

    def test_rejects_sensitive_json_field(self) -> None:
        scenario = ApiScenario("SCN-001", "secret body", "POST", "/items", ApiAssertion(201), json_body={"profile": {"password": "redacted"}})
        plan = ApiTestPlan("API-PLAN-007", f"http://127.0.0.1:{self.port}", (scenario,))
        policy = BackendApiPolicy(allowed_methods=("POST",))
        with self.assertRaisesRegex(BackendApiPolicyError, "sensitive JSON fields"):
            BackendApiSkill(policy).validate(plan)

    def test_plan_file_rejects_duplicate_json_keys(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=".asef") as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text(
                '{"schema_version":"1.0.0","plan_id":"A","plan_id":"B","base_url":"http://127.0.0.1:8765","scenarios":[]}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                ApiPlanFileAdapter().load(path)

    def test_does_not_follow_redirect(self) -> None:
        result = LoopbackHttpApiExecutor().execute(self.plan("/redirect", 200))
        self.assertEqual("FAILED", result.status)
        self.assertEqual("STATUS_MISMATCH", result.scenarios[0].diagnostic_code)
        self.assertEqual(302, result.scenarios[0].observed_status)

    def test_limits_response_size(self) -> None:
        policy = BackendApiPolicy(max_response_bytes=16)
        result = LoopbackHttpApiExecutor(policy).execute(self.plan("/large", 200))
        self.assertEqual("ERROR", result.status)
        self.assertEqual("RESPONSE_LIMIT_EXCEEDED", result.scenarios[0].diagnostic_code)

    def test_reports_json_assertion_mismatch(self) -> None:
        plan = ApiTestPlan(
            "API-PLAN-005",
            f"http://127.0.0.1:{self.port}",
            (ApiScenario("SCN-001", "wrong oracle", "GET", "/health", ApiAssertion(200, {"status": "down"})),),
        )
        result = LoopbackHttpApiExecutor().execute(plan)
        self.assertEqual("FAILED", result.status)
        self.assertEqual("JSON_SUBSET_MISMATCH", result.scenarios[0].diagnostic_code)

    def test_cli_executes_json_plan_and_writes_reports(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=".asef") as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            output = root / "reports"
            plan_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "plan_id": "API-CLI-001",
                        "base_url": f"http://127.0.0.1:{self.port}",
                        "scenarios": [
                            {
                                "scenario_id": "SCN-001",
                                "description": "health via CLI",
                                "method": "GET",
                                "path": "/health",
                                "assertion": {"expected_status": 200, "expected_json_subset": {"status": "ok"}},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(
                    [
                        "api",
                        "--plan",
                        str(plan_path),
                        "--allow-port",
                        str(self.port),
                        "--output",
                        str(output),
                    ]
                )
            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, code, stderr.getvalue())
            self.assertEqual("ACCEPTED", payload["classification"])
            self.assertTrue((Path.cwd() / payload["report_json"]).is_file())
            self.assertTrue((Path.cwd() / payload["report_markdown"]).is_file())

    def test_agent_generates_typed_plan_but_runtime_injects_origin(self) -> None:
        class Gateway:
            def __init__(self) -> None:
                self.calls: list[dict[str, object]] = []

            def generate(self, *, prompt, schema, schema_name):
                self.calls.append({"prompt": prompt, "schema": schema, "schema_name": schema_name})
                return ModelResult(
                    output={
                        "scenarios": [
                            {
                                "description": "health",
                                "method": "GET",
                                "path": "/health",
                                "expected_status": 200,
                                "expected_json_properties": [{"name": "status", "value": "ok"}],
                            }
                        ]
                    },
                    model="fake",
                    response_id="response-1",
                    provider="recorded",
                )

        gateway = Gateway()
        result = ApiPlanAgentAdapter(
            gateway,
            BackendApiPolicy(allowed_ports=(self.port,)),
        ).generate("Verify the health endpoint", f"http://127.0.0.1:{self.port}")
        self.assertEqual(f"http://127.0.0.1:{self.port}", result.plan.base_url)
        self.assertEqual({"status": "ok"}, result.plan.scenarios[0].assertion.expected_json_subset)
        self.assertEqual("backend_api_plan_v1", gateway.calls[0]["schema_name"])
        self.assertNotIn("base_url", gateway.calls[0]["schema"]["properties"])

    def test_agent_rejects_sensitive_requirement_before_gateway(self) -> None:
        class Gateway:
            calls = 0

            def generate(self, **kwargs):
                self.calls += 1
                raise AssertionError(kwargs)

        gateway = Gateway()
        with self.assertRaisesRegex(BackendApiPolicyError, "sensitive marker"):
            ApiPlanAgentAdapter(gateway, BackendApiPolicy()).generate(
                "Use api_key=do-not-send",
                f"http://127.0.0.1:{self.port}",
            )
        self.assertEqual(0, gateway.calls)

    def test_cli_generates_reviewable_plan_from_natural_language(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=".asef") as temporary:
            output = Path(temporary) / "generated.json"
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(
                    [
                        "api-generate",
                        "--requirement",
                        "Verify that the local API is healthy",
                        "--base-url",
                        f"http://127.0.0.1:{self.port}",
                        "--allow-port",
                        str(self.port),
                        "--output",
                        str(output),
                        "--run-output",
                        str(Path(temporary) / "runs"),
                    ]
                )
            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, code, stderr.getvalue())
            self.assertEqual("PLAN_READY_FOR_REVIEW", payload["classification"])
            self.assertEqual(f"http://127.0.0.1:{self.port}", ApiPlanFileAdapter().load(output).base_url)

    def test_generated_run_resumes_by_id_after_explicit_review_command(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=".asef") as temporary:
            root = Path(temporary)
            plan_path = root / "review-plan.json"
            run_root = root / "runs"
            generated_stdout, executed_stdout, stderr = io.StringIO(), io.StringIO(), io.StringIO()
            with redirect_stdout(generated_stdout), redirect_stderr(stderr):
                generated_code = main(
                    [
                        "api-generate",
                        "--requirement",
                        "Verify that the local API is healthy",
                        "--base-url",
                        f"http://127.0.0.1:{self.port}",
                        "--allow-port",
                        str(self.port),
                        "--output",
                        str(plan_path),
                        "--run-output",
                        str(run_root),
                    ]
                )
            generated = json.loads(generated_stdout.getvalue())
            with redirect_stdout(executed_stdout), redirect_stderr(stderr):
                executed_code = main(
                    [
                        "api",
                        "--run-id",
                        generated["run_id"],
                        "--allow-port",
                        str(self.port),
                        "--output",
                        str(run_root),
                    ]
                )
            executed = json.loads(executed_stdout.getvalue())
            self.assertEqual((0, 0), (generated_code, executed_code), stderr.getvalue())
            self.assertEqual(generated["run_id"], executed["run_id"])
            self.assertEqual("ACCEPTED", executed["classification"])

    def test_cli_accepts_relative_output_paths_shown_in_tutorial(self) -> None:
        Path(".asef").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=".asef") as temporary:
            relative_root = Path(temporary).resolve().relative_to(Path.cwd().resolve())
            plan_path = relative_root / "plan.json"
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                generated_code = main(
                    [
                        "api-generate",
                        "--requirement",
                        "Verify the local health endpoint",
                        "--base-url",
                        f"http://127.0.0.1:{self.port}",
                        "--allow-port",
                        str(self.port),
                        "--output",
                        str(plan_path),
                    ]
                )
                executed_code = main(
                    [
                        "api",
                        "--plan",
                        str(plan_path),
                        "--allow-port",
                        str(self.port),
                        "--output",
                        str(relative_root / "reports"),
                    ]
                )
            lines = stdout.getvalue().splitlines()
            self.assertEqual((0, 0), (generated_code, executed_code), stderr.getvalue())
            self.assertEqual("PLAN_READY_FOR_REVIEW", json.loads(lines[0])["classification"])
            self.assertEqual("ACCEPTED", json.loads(lines[1])["classification"])


if __name__ == "__main__":
    unittest.main()
