from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import sys
from importlib import metadata
from pathlib import Path

from .adapters.context_file import FileQualityContextAdapter
from .adapters.api_plan_file import ApiPlanFileAdapter
from .adapters.api_plan_agent import ApiPlanAgentAdapter, ApiPlanAgentPricing
from .adapters.api_report_store import ApiReportStore
from .adapters.capability_run_store import CapabilityRunStore
from .adapters.http_api_execution import LoopbackHttpApiExecutor
from .adapters.web_ui_plan_agent import WebUiPlanAgentAdapter, WebUiPlanAgentPricing
from .adapters.web_ui_plan_file import WebUiPlanFileAdapter
from .adapters.java_unit_plan_agent import JavaUnitPlanAgentAdapter, JavaUnitPlanAgentPricing
from .adapters.java_unit_plan_file import JavaUnitPlanFileAdapter
from .adapters.cleanup_executor import CleanupExecutor
from .adapters.cleanup_report_store import CleanupReportStore
from .adapters.doctor_check_executor import DoctorCheckExecutor
from .adapters.doctor_report_store import DoctorReportStore
from .adapters.docker_execution import DockerUnitTestAdapter
from .adapters.recorded_agent import RecordedAgentAdapter, RecordedAgentError
from .adapters.gateway import GatewayError, OpenAIResponsesGateway, RecordedModelGateway
from .adapters.live_agent import LiveAgentAdapter, LiveAgentConfig
from .adapters.run_store import JsonRunStore
from .adapters.smoke_case_executor import SmokeCaseExecutorAdapter
from .adapters.smoke_dataset import SmokeDatasetLoader
from .adapters.smoke_report_store import SmokeReportStore
from .adapters.security_case_executor import SecurityCaseExecutor
from .adapters.security_dataset import SecurityDatasetLoader
from .adapters.security_report_store import SecurityReportStore
from .adapters.workspace import EphemeralWorkspaceAdapter
from .adapters.langgraph_checkpoint import (
    HumanCheckpointError,
    LangGraphHumanCheckpointAdapter,
    OptionalWorkflowDependencyError,
)
from .application.generate_unit import GenerateUnitTestService
from .application.complete_workflow import CompleteWorkflowService
from .application.cleanup_runner import CleanupInfrastructureError, CleanupRunner
from .application.backend_api_run import (
    ExecuteBackendApiPlanService,
    GenerateBackendApiPlanService,
    RegisterBackendApiPlanService,
)
from .application.web_ui_run import ExecuteWebUiPlanService, GenerateWebUiPlanService
from .application.java_unit_run import ExecuteJavaUnitPlanService, GenerateJavaUnitPlanService
from .application.doctor_runner import (
    DoctorInfrastructureError,
    DoctorRequest,
    DoctorRunner,
)
from .application.human_decision import HumanDecisionService
from .application.prepare_run import PrepareRunService
from .application.smoke_runner import SmokeSuiteInfrastructureError, SmokeSuiteRunner
from .application.security_runner import (
    SecuritySuiteInfrastructureError,
    SecuritySuiteRunner,
)
from .report_contracts import REPORT_SCHEMA_VERSION
from .context import ContextValidationError
from .contracts import ContractValidationError, SkeletonRunRequest
from .api_contracts import ApiContractError
from .java_unit_contracts import JavaUnitContractError
from .capability_runs import CapabilityRunBudgets, CapabilityRunContractError, CapabilityRunStatus
from .security_contracts import CleanupKind, CleanupMode, CleanupRequest
from .application.ports import ProviderError
from .demo import materialize_demo_assets
from .outcomes import RunStatus, exit_code_for
from .observability import close_operational_logging, configure_operational_logging
from .openapi_contracts import OpenApiContractError, OpenApiJsonLoader
from .skills.unit import UnitSkill
from .skills.backend_api import BackendApiPolicy, BackendApiPolicyError
from .skills.web_ui import WebUiPolicy, WebUiPolicyError
from .skills.java_unit import JavaUnitPolicy, JavaUnitPolicyError
from .runtime.budgets import BudgetController
from .legacy.domain import BudgetLimits, BudgetUsage


def _environment_float(name: str) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _package_version() -> str:
    try:
        return metadata.version("asef-agentic-test-factory")
    except metadata.PackageNotFoundError:
        # Source-tree execution used by contributors before an editable install.
        return "0.1.0a7"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="asef")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="prepare WF-001 up to the agentic boundary")
    _common_arguments(prepare)
    generate = subparsers.add_parser("generate", help="generate and statically validate a unit test")
    _common_arguments(generate)
    _recorded_arguments(generate)
    run = subparsers.add_parser("run", help="execute the complete recorded WS-001 in Docker")
    _common_arguments(run)
    _recorded_arguments(run)
    wait = subparsers.add_parser("wait", help="start WS-002 and persist a human checkpoint")
    _common_arguments(wait)
    _recorded_arguments(
        wait,
        clarification_default=True,
    )
    resume = subparsers.add_parser("resume", help="resume a waiting run")
    _decision_arguments(resume)
    resume.add_argument("--answer", required=True)
    cancel = subparsers.add_parser("cancel", help="cancel a waiting run")
    _decision_arguments(cancel)
    cancel.add_argument("--reason", required=True)
    smoke = subparsers.add_parser("smoke", help="execute the deterministic Alpha Smoke Dataset")
    smoke.add_argument("--dataset-root", type=Path, default=Path("datasets/smoke"))
    smoke.add_argument(
        "--context",
        type=Path,
        default=Path("examples/context/python-alpha-smoke-context.json"),
    )
    smoke.add_argument("--mode", choices=("demo",), default="demo")
    smoke.add_argument("--output", type=Path, default=Path(".asef/smoke"))
    smoke.add_argument("--repeat", type=int, default=1)
    smoke.add_argument("--timeout-seconds", type=int, default=60)
    _logging_argument(smoke)
    security = subparsers.add_parser(
        "security", help="execute the deterministic ASEF Security Dataset"
    )
    security.add_argument(
        "--dataset-root", type=Path, default=Path("datasets/security")
    )
    security.add_argument("--output", type=Path, default=Path(".asef/security"))
    security.add_argument("--timeout-seconds", type=int, default=20)
    _logging_argument(security)
    doctor = subparsers.add_parser(
        "doctor", help="diagnose ASEF runtime requirements without changing the host"
    )
    doctor.add_argument("--context", type=Path, default=None)
    doctor.add_argument("--mode", choices=("demo", "live"), default="demo")
    doctor.add_argument("--output", type=Path, default=Path(".asef/doctor"))
    doctor.add_argument("--timeout-seconds", type=int, default=5)
    _logging_argument(doctor)
    cleanup = subparsers.add_parser(
        "cleanup", help="plan or apply conservative cleanup below .asef"
    )
    cleanup.add_argument(
        "--kind",
        choices=tuple(item.value for item in CleanupKind),
        required=True,
    )
    cleanup.add_argument("--older-than-days", type=int, required=True)
    cleanup.add_argument("--apply", action="store_true")
    cleanup.set_defaults(output=Path(".asef/maintenance/cleanup"))
    _logging_argument(cleanup)
    api = subparsers.add_parser(
        "api", help="execute a bounded backend-api plan against an authorized loopback target"
    )
    api_source = api.add_mutually_exclusive_group(required=True)
    api_source.add_argument("--plan", type=Path)
    api_source.add_argument("--run-id")
    api.add_argument("--allow-port", type=int, action="append", required=True)
    api.add_argument("--allow-method", action="append", default=["GET", "HEAD", "OPTIONS"])
    api.add_argument("--timeout-seconds", type=float, default=5.0)
    api.add_argument("--max-response-bytes", type=int, default=1_048_576)
    api.add_argument("--max-requests", type=int, default=20)
    api.add_argument("--max-workflow-seconds", type=int, default=60)
    api.add_argument("--output", type=Path, default=Path(".asef/runs"))
    _logging_argument(api)
    api_generate = subparsers.add_parser(
        "api-generate", help="turn a natural-language API requirement into a reviewable bounded plan"
    )
    api_generate.add_argument("--requirement", required=True)
    api_generate.add_argument("--base-url", required=True)
    api_generate.add_argument("--openapi", type=Path)
    api_generate.add_argument("--allow-port", type=int, action="append", required=True)
    api_generate.add_argument("--max-scenarios", type=int, default=20)
    api_generate.add_argument("--max-workflow-seconds", type=int, default=60)
    api_generate.add_argument("--mode", choices=("demo", "live"), default="demo")
    api_generate.add_argument("--model", default=os.environ.get("ASEF_OPENAI_MODEL"))
    api_generate.add_argument("--api-budget-brl", type=float, default=0.0)
    api_generate.add_argument("--input-cost-brl-per-million", type=float, default=0.0)
    api_generate.add_argument("--output-cost-brl-per-million", type=float, default=0.0)
    api_generate.add_argument("--provider-timeout-seconds", type=int, default=60)
    api_generate.add_argument("--max-output-tokens", type=int, default=600)
    api_generate.add_argument("--max-provider-retries", type=int, default=1)
    api_generate.add_argument("--cassette", type=Path, default=None)
    api_generate.add_argument("--output", type=Path, default=Path(".asef/api/plans/generated-plan.json"))
    api_generate.add_argument("--run-output", type=Path, default=Path(".asef/runs"))
    _logging_argument(api_generate)
    web_generate = subparsers.add_parser(
        "web-generate", help="turn a natural-language fixture requirement into a reviewable Web UI plan"
    )
    web_generate.add_argument("--requirement", required=True)
    web_generate.add_argument("--base-url", default="http://127.0.0.1:4173")
    web_generate.add_argument("--allow-port", type=int, action="append", default=[4173])
    web_generate.add_argument("--max-scenarios", type=int, default=20)
    web_generate.add_argument("--max-workflow-seconds", type=int, default=90)
    web_generate.add_argument("--mode", choices=("demo", "live"), default="demo")
    web_generate.add_argument("--model", default=os.environ.get("ASEF_OPENAI_MODEL"))
    web_generate.add_argument("--api-budget-brl", type=float, default=0.0)
    web_generate.add_argument("--input-cost-brl-per-million", type=float, default=0.0)
    web_generate.add_argument("--output-cost-brl-per-million", type=float, default=0.0)
    web_generate.add_argument("--provider-timeout-seconds", type=int, default=60)
    web_generate.add_argument("--max-output-tokens", type=int, default=1200)
    web_generate.add_argument("--max-provider-retries", type=int, default=1)
    web_generate.add_argument("--cassette", type=Path, default=None)
    web_generate.add_argument("--output", type=Path, default=Path(".asef/web/plans/generated-plan.json"))
    web_generate.add_argument("--run-output", type=Path, default=Path(".asef/runs"))
    _logging_argument(web_generate)
    web = subparsers.add_parser(
        "web", help="execute a reviewed Web UI capability run against the local fixture"
    )
    web.add_argument("--run-id", required=True)
    web.add_argument("--output", type=Path, default=Path(".asef/runs"))
    _logging_argument(web)
    java_generate = subparsers.add_parser(
        "java-generate", help="turn a natural-language Calculator requirement into a reviewable JUnit plan"
    )
    java_generate.add_argument("--requirement", required=True)
    java_generate.add_argument("--max-scenarios", type=int, default=20)
    java_generate.add_argument("--max-workflow-seconds", type=int, default=90)
    java_generate.add_argument("--mode", choices=("demo", "live"), default="demo")
    java_generate.add_argument("--model", default=os.environ.get("ASEF_OPENAI_MODEL"))
    java_generate.add_argument("--api-budget-brl", type=float, default=0.0)
    java_generate.add_argument("--input-cost-brl-per-million", type=float, default=0.0)
    java_generate.add_argument("--output-cost-brl-per-million", type=float, default=0.0)
    java_generate.add_argument("--provider-timeout-seconds", type=int, default=60)
    java_generate.add_argument("--max-output-tokens", type=int, default=800)
    java_generate.add_argument("--max-provider-retries", type=int, default=1)
    java_generate.add_argument("--cassette", type=Path, default=None)
    java_generate.add_argument("--output", type=Path, default=Path(".asef/java/plans/generated-plan.json"))
    java_generate.add_argument("--run-output", type=Path, default=Path(".asef/runs"))
    _logging_argument(java_generate)
    java = subparsers.add_parser("java", help="execute a reviewed Java/JUnit capability run")
    java.add_argument("--run-id", required=True)
    java.add_argument("--output", type=Path, default=Path(".asef/runs"))
    _logging_argument(java)
    return parser


def _recorded_arguments(
    parser: argparse.ArgumentParser,
    *,
    clarification_default: bool = False,
) -> None:
    parser.add_argument(
        "--analysis-cassette",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--artifact-cassette",
        type=Path,
        default=None,
    )
    parser.set_defaults(demo_clarification=clarification_default)
    parser.add_argument("--model", default=os.environ.get("ASEF_OPENAI_MODEL"))
    parser.add_argument("--provider-timeout-seconds", type=int, default=60)
    parser.add_argument("--max-output-tokens", type=int, default=600)
    parser.add_argument(
        "--input-cost-brl-per-million",
        type=float,
        default=_environment_float("ASEF_OPENAI_INPUT_BRL_PER_MTOK"),
    )
    parser.add_argument(
        "--output-cost-brl-per-million",
        type=float,
        default=_environment_float("ASEF_OPENAI_OUTPUT_BRL_PER_MTOK"),
    )
    parser.add_argument("--record-live-cassettes", action="store_true")


def _decision_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, default=Path(".asef/runs"))
    _logging_argument(parser)
    parser.add_argument(
        "--artifact-cassette",
        type=Path,
        default=None,
    )


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--context", type=Path, default=None
    )
    parser.add_argument("--system", default="calculator-service")
    parser.add_argument("--skill", default="unit")
    parser.add_argument("--title", default="Sum two integers")
    parser.add_argument(
        "--requirement",
        default="The add(a, b) function returns the arithmetic sum of two integers.",
    )
    parser.add_argument("--mode", choices=("demo", "live"), default="demo")
    parser.add_argument("--api-budget-brl", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=Path(".asef/runs"))
    _logging_argument(parser)


def _logging_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logger = configure_operational_logging(Path.cwd() / ".asef" / "logs", args.log_level)
    logger.info(
        "command_started",
        extra={"operation": args.command, "component": "cli"},
    )
    try:
        context_was_explicit = not hasattr(args, "context") or args.context is not None
        if (
            args.command != "doctor"
            and getattr(args, "mode", "demo") == "live"
            and not context_was_explicit
        ):
            raise ContractValidationError("live mode requires an explicit --context")
        allowed_output_root = (Path.cwd() / ".asef").resolve()
        resolved_output = args.output.resolve()
        if not resolved_output.is_relative_to(allowed_output_root):
            raise ContractValidationError("output must remain inside the .asef directory")
        if hasattr(args, "run_output") and not args.run_output.resolve().is_relative_to(allowed_output_root):
            raise ContractValidationError("run output must remain inside the .asef directory")
        if args.command == "smoke":
            if args.timeout_seconds < 1 or args.timeout_seconds > 300:
                raise ContractValidationError("smoke timeout must be between 1 and 300 seconds")
            runner = SmokeSuiteRunner(
                SmokeDatasetLoader(),
                SmokeCaseExecutorAdapter(timeout_seconds=args.timeout_seconds),
                SmokeReportStore(),
                asef_version=_package_version(),
                environment=(
                    f"{platform.system().lower()}-{platform.machine().lower()}-"
                    f"python-{platform.python_version()}"
                ),
            )
            smoke_result = runner.run(
                args.dataset_root,
                args.output,
                repeat=args.repeat,
                context_ref=args.context,
            )
            report = smoke_result.report
            if report.runner_errors:
                code = 7
                status = "FAILED"
                classification = "INFRASTRUCTURE_ERROR"
            elif report.mismatched:
                code = 4
                status = "FAILED"
                classification = "SMOKE_MISMATCH"
            else:
                code = 0
                status = "SUCCEEDED"
                classification = "ACCEPTED"
            payload = {
                "suite_id": report.suite_id,
                "status": status,
                "classification": classification,
                "total": report.total,
                "matched": report.matched,
                "mismatched": report.mismatched,
                "runner_errors": report.runner_errors,
                "dataset_hash": report.dataset_hash,
                "suite_json": smoke_result.suite_json.relative_to(Path.cwd()).as_posix(),
                "suite_markdown": smoke_result.suite_markdown.relative_to(Path.cwd()).as_posix(),
            }
            _log_completion(logger, args.command, report.suite_id, payload, code)
            print(json.dumps(payload))
            close_operational_logging(logger)
            return code
        if args.command == "security":
            if args.timeout_seconds < 1 or args.timeout_seconds > 120:
                raise ContractValidationError(
                    "security timeout must be between 1 and 120 seconds"
                )
            security_output = SecuritySuiteRunner(
                SecurityDatasetLoader(),
                SecurityCaseExecutor(timeout_seconds=args.timeout_seconds),
                SecurityReportStore(),
                asef_version=_package_version(),
                environment=(
                    f"{platform.system().lower()}-{platform.machine().lower()}-"
                    f"python-{platform.python_version()}"
                ),
            ).run(args.dataset_root, args.output)
            report = security_output.report
            if report.errors or report.unsupported:
                code, status, classification = 7, "FAILED", "INFRASTRUCTURE_ERROR"
            elif report.failed:
                code, status, classification = 4, "FAILED", "SECURITY_CONTROL_FAILURE"
            else:
                code, status, classification = 0, "SUCCEEDED", "ACCEPTED"
            payload = {
                "suite_id": report.suite_id,
                "status": status,
                "classification": classification,
                "total": len(report.results),
                "passed": report.passed,
                "failed": report.failed,
                "errors": report.errors,
                "unsupported": report.unsupported,
                "dataset_hash": report.dataset_hash,
                "suite_json": security_output.suite_json.relative_to(Path.cwd()).as_posix(),
                "suite_markdown": security_output.suite_markdown.relative_to(Path.cwd()).as_posix(),
            }
            _log_completion(logger, args.command, report.suite_id, payload, code)
            print(json.dumps(payload))
            close_operational_logging(logger)
            return code
        if args.command == "doctor":
            doctor_output = DoctorRunner(
                DoctorCheckExecutor(timeout_seconds=args.timeout_seconds),
                DoctorReportStore(),
                asef_version=_package_version(),
                python_version=platform.python_version(),
                environment=(
                    f"{platform.system().lower()}-{platform.machine().lower()}"
                ),
            ).run(
                DoctorRequest(
                    mode=args.mode,
                    output_root=args.output,
                    context_ref=args.context,
                )
            )
            report = doctor_output.report
            code = 0 if report.healthy else 7
            payload = {
                "report_id": report.report_id,
                "status": report.status.value,
                "classification": (
                    "READY" if report.healthy else "REQUIREMENTS_BLOCKED"
                ),
                "healthy": report.healthy,
                "checks": len(report.checks),
                "report_json": doctor_output.report_json.relative_to(
                    Path.cwd()
                ).as_posix(),
                "report_markdown": doctor_output.report_markdown.relative_to(
                    Path.cwd()
                ).as_posix(),
            }
            _log_completion(logger, args.command, report.report_id, payload, code)
            print(json.dumps(payload))
            close_operational_logging(logger)
            return code
        if args.command == "cleanup":
            cleanup_output = CleanupRunner(
                CleanupExecutor(),
                CleanupReportStore(),
            ).run(
                CleanupRequest(
                    kind=CleanupKind(args.kind),
                    older_than_days=args.older_than_days,
                    mode=CleanupMode.APPLY if args.apply else CleanupMode.DRY_RUN,
                )
            )
            report = cleanup_output.report
            code = 7 if report.failed else 0
            payload = {
                "cleanup_id": report.cleanup_id,
                "status": "FAILED" if report.failed else "SUCCEEDED",
                "classification": (
                    "CLEANUP_PARTIAL"
                    if report.failed
                    else (
                        "DRY_RUN_COMPLETE"
                        if report.request.mode is CleanupMode.DRY_RUN
                        else "CLEANUP_COMPLETE"
                    )
                ),
                "mode": report.request.mode.value,
                "planned": report.planned,
                "deleted": report.deleted,
                "failed": report.failed,
                "skipped": report.skipped,
                "report_json": cleanup_output.report_json.relative_to(
                    Path.cwd()
                ).as_posix(),
                "report_markdown": cleanup_output.report_markdown.relative_to(
                    Path.cwd()
                ).as_posix(),
            }
            _log_completion(logger, args.command, report.cleanup_id, payload, code)
            print(json.dumps(payload))
            close_operational_logging(logger)
            return code
        if args.command == "api":
            policy = BackendApiPolicy(
                allowed_ports=tuple(args.allow_port),
                allowed_methods=tuple(dict.fromkeys(args.allow_method)),
                timeout_seconds=args.timeout_seconds,
                max_response_bytes=args.max_response_bytes,
            )
            store = CapabilityRunStore(args.output)
            executor = LoopbackHttpApiExecutor(policy)
            if args.run_id:
                run_id = args.run_id
            else:
                plan = ApiPlanFileAdapter().load(args.plan)
                registered = RegisterBackendApiPlanService(
                    executor.skill,
                    store,
                ).execute(
                    plan,
                    CapabilityRunBudgets(
                        max_model_calls=0,
                        max_requests=args.max_requests,
                        max_workflow_seconds=args.max_workflow_seconds,
                    ),
                )
                run_id = registered.state.run_id
            completed = ExecuteBackendApiPlanService(
                executor,
                store,
                ApiReportStore(),
                asef_version=_package_version(),
            ).execute(run_id)
            result = completed.result
            if result is None:
                code = 6
            else:
                code = 0 if result.status == "PASSED" else (4 if result.status == "FAILED" else 7)
            payload = {
                "run_id": completed.state.run_id,
                "status": completed.state.status.value,
                "classification": completed.state.classification.value,
                "skill_id": "backend-api",
                "support_level": "experimental-under-development",
                "tests": result.tests if result else 0,
                "passed": result.passed if result else 0,
                "failed": result.failed if result else 0,
                "errors": result.errors if result else 0,
                "run_dir": store.run_dir(completed.state.run_id).relative_to(Path.cwd().resolve()).as_posix(),
                "report_json": completed.reports.report_json.resolve().relative_to(Path.cwd().resolve()).as_posix() if completed.reports else None,
                "report_markdown": completed.reports.report_markdown.resolve().relative_to(Path.cwd().resolve()).as_posix() if completed.reports else None,
            }
            _log_completion(logger, args.command, completed.state.run_id, payload, code)
            print(json.dumps(payload))
            close_operational_logging(logger)
            return code
        if args.command == "api-generate":
            openapi = OpenApiJsonLoader().load(args.openapi) if args.openapi else None
            cassette = args.cassette or (
                Path(__file__).parent / "fixtures" / "backend-api-plan-demo.json"
            )
            policy = BackendApiPolicy(
                allowed_ports=tuple(args.allow_port),
                max_scenarios=args.max_scenarios,
            )
            pricing = ApiPlanAgentPricing(
                args.input_cost_brl_per_million,
                args.output_cost_brl_per_million,
            )
            if args.mode == "live":
                pricing.validate_live()
                if args.api_budget_brl <= 0 or not args.model:
                    raise ContractValidationError("live API generation requires model and positive api budget")
                gateway = OpenAIResponsesGateway(
                    model=args.model,
                    timeout_seconds=args.provider_timeout_seconds,
                    api_budget_brl=args.api_budget_brl,
                    max_output_tokens=args.max_output_tokens,
                )
            else:
                budgets = BudgetController(
                    BudgetLimits(max_model_calls=1, max_input_tokens=10_000, max_output_tokens=5_000),
                    BudgetUsage(),
                )
                gateway = RecordedModelGateway(cassette, budgets)
            run_store = CapabilityRunStore(args.run_output)
            generated = GenerateBackendApiPlanService(
                ApiPlanAgentAdapter(gateway, policy, pricing),
                run_store,
            ).execute(
                args.requirement,
                args.base_url,
                CapabilityRunBudgets(
                    max_model_calls=(args.max_provider_retries + 1 if args.mode == "live" else 1),
                    max_provider_retries=(args.max_provider_retries if args.mode == "live" else 0),
                    max_input_tokens=10_000,
                    max_output_tokens=5_000,
                    max_requests=args.max_scenarios,
                    max_workflow_seconds=args.max_workflow_seconds,
                    api_budget_brl=args.api_budget_brl,
                ),
                openapi,
            )
            if generated.plan is not None:
                ApiPlanFileAdapter().save(args.output, generated.plan)
            code = 0 if generated.state.status is CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW else 6
            generation = generated.state.facts.get("generation", {})
            payload = {
                "run_id": generated.state.run_id,
                "plan_id": generated.plan.plan_id if generated.plan else None,
                "status": generated.state.status.value,
                "classification": generated.state.classification.value,
                "skill_id": "backend-api",
                "provider": generation.get("provider"),
                "model": generation.get("model"),
                "scenarios": len(generated.plan.scenarios) if generated.plan else 0,
                "openapi_sha256": generation.get("openapi_sha256"),
                "estimated_cost_brl": generated.state.usage.estimated_cost_brl,
                "plan_path": (
                    args.output.resolve().relative_to(Path.cwd().resolve()).as_posix()
                    if generated.plan else None
                ),
                "run_dir": run_store.run_dir(generated.state.run_id).relative_to(Path.cwd().resolve()).as_posix(),
                "next_action": (
                    f"review_then_execute_with_asef_api_run_id:{generated.state.run_id}"
                    if code == 0
                    else None
                ),
            }
            _log_completion(logger, args.command, generated.state.run_id, payload, code)
            print(json.dumps(payload))
            close_operational_logging(logger)
            return code
        if args.command == "web-generate":
            cassette = args.cassette or (Path(__file__).parent / "fixtures" / "web-ui-plan-demo.json")
            pricing = WebUiPlanAgentPricing(
                args.input_cost_brl_per_million, args.output_cost_brl_per_million
            )
            if args.mode == "live":
                pricing.validate_live()
                if args.api_budget_brl <= 0 or not args.model:
                    raise ContractValidationError("live Web UI generation requires model and positive api budget")
                gateway = OpenAIResponsesGateway(
                    model=args.model, timeout_seconds=args.provider_timeout_seconds,
                    api_budget_brl=args.api_budget_brl, max_output_tokens=args.max_output_tokens,
                )
            else:
                gateway = RecordedModelGateway(
                    cassette,
                    BudgetController(
                        BudgetLimits(max_model_calls=1, max_input_tokens=10_000, max_output_tokens=5_000),
                        BudgetUsage(),
                    ),
                )
            store = CapabilityRunStore(args.run_output)
            generated = GenerateWebUiPlanService(
                WebUiPlanAgentAdapter(
                    gateway, WebUiPolicy(allowed_hosts=("127.0.0.1",), allowed_ports=tuple(args.allow_port), max_scenarios=args.max_scenarios), pricing,
                ),
                store,
            ).execute(
                args.requirement,
                args.base_url,
                CapabilityRunBudgets(
                    max_model_calls=(args.max_provider_retries + 1 if args.mode == "live" else 1),
                    max_provider_retries=(args.max_provider_retries if args.mode == "live" else 0),
                    max_input_tokens=10_000, max_output_tokens=5_000,
                    max_requests=args.max_scenarios,
                    max_workflow_seconds=args.max_workflow_seconds,
                    api_budget_brl=args.api_budget_brl,
                ),
            )
            if generated.plan:
                WebUiPlanFileAdapter().save(args.output, generated.plan)
            code = 0 if generated.state.status is CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW else 6
            payload = {
                "run_id": generated.state.run_id,
                "plan_id": generated.plan.plan_id if generated.plan else None,
                "status": generated.state.status.value,
                "classification": generated.state.classification.value,
                "skill_id": "web-ui", "provider": generated.state.facts.get("generation", {}).get("provider"),
                "model": generated.state.facts.get("generation", {}).get("model"),
                "estimated_cost_brl": generated.state.usage.estimated_cost_brl,
                "scenarios": len(generated.plan.scenarios) if generated.plan else 0,
                "plan_path": args.output.resolve().relative_to(Path.cwd().resolve()).as_posix() if generated.plan else None,
                "run_dir": store.run_dir(generated.state.run_id).relative_to(Path.cwd().resolve()).as_posix(),
                "next_action": f"review_then_execute_with_asef_web_run_id:{generated.state.run_id}" if code == 0 else None,
            }
            _log_completion(logger, args.command, generated.state.run_id, payload, code)
            print(json.dumps(payload))
            close_operational_logging(logger)
            return code
        if args.command == "web":
            store = CapabilityRunStore(args.output)
            completed = ExecuteWebUiPlanService(store).execute(args.run_id)
            result = completed.result
            code = 6 if result is None else (0 if result.status == "PASSED" else (4 if result.status == "FAILED" else 7))
            payload = {
                "run_id": completed.state.run_id,
                "status": completed.state.status.value,
                "classification": completed.state.classification.value,
                "skill_id": "web-ui", "support_level": "planned-under-development",
                "tests": result.tests if result else 0,
                "passed": result.passed if result else 0,
                "failed": result.failed if result else 0,
                "errors": result.errors if result else 0,
                "run_dir": store.run_dir(completed.state.run_id).relative_to(Path.cwd().resolve()).as_posix(),
            }
            _log_completion(logger, args.command, completed.state.run_id, payload, code)
            print(json.dumps(payload))
            close_operational_logging(logger)
            return code
        if args.command == "java-generate":
            cassette = args.cassette or (Path(__file__).parent / "fixtures" / "java-unit-plan-demo.json")
            pricing = JavaUnitPlanAgentPricing(args.input_cost_brl_per_million, args.output_cost_brl_per_million)
            if args.mode == "live":
                pricing.validate_live()
                if args.api_budget_brl <= 0 or not args.model:
                    raise ContractValidationError("live Java unit generation requires model and positive api budget")
                gateway = OpenAIResponsesGateway(
                    model=args.model, timeout_seconds=args.provider_timeout_seconds,
                    api_budget_brl=args.api_budget_brl, max_output_tokens=args.max_output_tokens,
                )
            else:
                gateway = RecordedModelGateway(
                    cassette, BudgetController(BudgetLimits(max_model_calls=1, max_input_tokens=10_000, max_output_tokens=5_000), BudgetUsage()),
                )
            store = CapabilityRunStore(args.run_output)
            generated = GenerateJavaUnitPlanService(
                JavaUnitPlanAgentAdapter(gateway, JavaUnitPolicy(args.max_scenarios), pricing), store,
            ).execute(args.requirement, CapabilityRunBudgets(
                max_model_calls=(args.max_provider_retries + 1 if args.mode == "live" else 1),
                max_provider_retries=(args.max_provider_retries if args.mode == "live" else 0),
                max_input_tokens=10_000, max_output_tokens=5_000, max_requests=args.max_scenarios,
                max_workflow_seconds=args.max_workflow_seconds, api_budget_brl=args.api_budget_brl,
            ))
            if generated.plan: JavaUnitPlanFileAdapter().save(args.output, generated.plan)
            code = 0 if generated.state.status is CapabilityRunStatus.WAITING_FOR_HUMAN_REVIEW else 6
            payload = {
                "run_id": generated.state.run_id, "plan_id": generated.plan.plan_id if generated.plan else None,
                "status": generated.state.status.value, "classification": generated.state.classification.value,
                "skill_id": "java-unit", "provider": generated.state.facts.get("generation", {}).get("provider"),
                "model": generated.state.facts.get("generation", {}).get("model"),
                "estimated_cost_brl": generated.state.usage.estimated_cost_brl,
                "scenarios": len(generated.plan.scenarios) if generated.plan else 0,
                "plan_path": args.output.resolve().relative_to(Path.cwd().resolve()).as_posix() if generated.plan else None,
                "run_dir": store.run_dir(generated.state.run_id).relative_to(Path.cwd().resolve()).as_posix(),
                "next_action": f"review_then_execute_with_asef_java_run_id:{generated.state.run_id}" if code == 0 else None,
            }
            _log_completion(logger, args.command, generated.state.run_id, payload, code)
            print(json.dumps(payload)); close_operational_logging(logger); return code
        if args.command == "java":
            store = CapabilityRunStore(args.output)
            completed = ExecuteJavaUnitPlanService(store).execute(args.run_id); result = completed.result
            code = 6 if result is None else (0 if result.outcome.value == "PASSED" else (4 if result.outcome.value == "ASSERTION_FAILURE" else 7))
            payload = {
                "run_id": completed.state.run_id, "status": completed.state.status.value,
                "classification": completed.state.classification.value, "skill_id": "java-unit",
                "support_level": "planned-under-development", "tests": result.tests if result else 0,
                "passed": result.passed if result else 0, "failed": result.failed if result else 0,
                "errors": result.errors if result else 0,
                "run_dir": store.run_dir(completed.state.run_id).relative_to(Path.cwd().resolve()).as_posix(),
            }
            _log_completion(logger, args.command, completed.state.run_id, payload, code)
            print(json.dumps(payload)); close_operational_logging(logger); return code
        demo_assets = materialize_demo_assets()
        if hasattr(args, "context") and args.context is None:
            args.context = demo_assets.context.relative_to(Path.cwd())
        if hasattr(args, "analysis_cassette") and args.analysis_cassette is None:
            args.analysis_cassette = (
                demo_assets.analysis_clarification
                if getattr(args, "demo_clarification", False)
                else demo_assets.analysis_success
            )
        if hasattr(args, "artifact_cassette") and args.artifact_cassette is None:
            args.artifact_cassette = demo_assets.artifact_success
        store = JsonRunStore(args.output)
        context_port = FileQualityContextAdapter()
        prepare_service = PrepareRunService(context_port, store)
        checkpoint = LangGraphHumanCheckpointAdapter()
        if args.command in {"resume", "cancel"}:
            generation_service = GenerateUnitTestService(
                prepare_service,
                RecordedAgentAdapter(
                    demo_assets.analysis_success,
                    args.artifact_cassette,
                ),
                UnitSkill(),
                EphemeralWorkspaceAdapter(),
                store,
                checkpoint,
            )
            completion = CompleteWorkflowService(
                generation_service,
                DockerUnitTestAdapter(args.output, timeout_seconds=60),
                store,
            )
            decisions = HumanDecisionService(
                context_port,
                checkpoint,
                generation_service,
                completion,
                store,
                args.output,
            )
            if args.command == "resume":
                decided = decisions.resume(args.run_id, args.answer)
            else:
                decided = decisions.cancel(args.run_id, args.reason)
            payload = {
                "run_id": decided.state.run_id,
                "status": decided.state.status.value,
                "classification": decided.state.classification.value,
                "run_dir": decided.run_dir.as_posix(),
                "report_path": (
                    f"{decided.run_dir.as_posix()}/{decided.report_path}"
                    if decided.report_path
                    else None
                ),
                "report_json": (
                    f"{decided.run_dir.as_posix()}/report.json"
                    if decided.report_path
                    else None
                ),
                "report_markdown": (
                    f"{decided.run_dir.as_posix()}/report.md"
                    if decided.report_path
                    else None
                ),
                "report_schema_version": (
                    REPORT_SCHEMA_VERSION if decided.report_path else None
                ),
            }
            code = int(exit_code_for(decided.state.status, decided.state.classification))
            _log_completion(logger, args.command, decided.state.run_id, payload, code)
            print(json.dumps(payload))
            close_operational_logging(logger)
            return code

        request = SkeletonRunRequest(
            context_ref=args.context.as_posix(),
            system_id=args.system,
            requested_skill=args.skill,
            requirement_title=args.title,
            requirement_description=args.requirement,
            output_root_ref=args.output.as_posix(),
            execution_mode=args.mode,
            api_budget_brl=args.api_budget_brl,
        )
        if args.command == "prepare":
            result = prepare_service.execute(request)
            payload = {
                "run_id": result.state.run_id,
                "status": result.state.status.value,
                "classification": result.state.classification.value,
                "run_dir": result.run_dir.as_posix(),
                "ready_for": "requirement_analysis",
            }
            code = 0
        else:
            if args.mode == "demo":
                agent = RecordedAgentAdapter(args.analysis_cassette, args.artifact_cassette)
            else:
                if not args.model:
                    raise ContractValidationError(
                        "live mode requires --model or ASEF_OPENAI_MODEL"
                    )
                if args.input_cost_brl_per_million <= 0 or args.output_cost_brl_per_million <= 0:
                    raise ContractValidationError(
                        "live mode requires positive input/output BRL token rates"
                    )
                cassette_dir = (
                    args.output / "live-cassettes" if args.record_live_cassettes else None
                )
                agent = LiveAgentAdapter(
                    OpenAIResponsesGateway(
                        model=args.model,
                        timeout_seconds=args.provider_timeout_seconds,
                        api_budget_brl=args.api_budget_brl,
                        max_output_tokens=args.max_output_tokens,
                    ),
                    LiveAgentConfig(
                        input_cost_brl_per_million=args.input_cost_brl_per_million,
                        output_cost_brl_per_million=args.output_cost_brl_per_million,
                        cassette_dir=cassette_dir,
                    ),
                )
            generation_service = GenerateUnitTestService(
                prepare_service,
                agent,
                UnitSkill(),
                EphemeralWorkspaceAdapter(),
                store,
                checkpoint if args.command == "wait" else None,
            )
            if args.command in {"generate", "wait"}:
                generated = generation_service.execute(request)
                terminal_report_path = None
                if generated.workspace is None and generated.state.status in {
                    RunStatus.FAILED,
                    RunStatus.CANCELLED,
                    RunStatus.POLICY_BLOCKED,
                    RunStatus.BUDGET_EXHAUSTED,
                }:
                    terminal_report_path = CompleteWorkflowService(
                        generation_service,
                        DockerUnitTestAdapter(args.output, timeout_seconds=60),
                        store,
                    ).complete_generated(generated).report_path
                payload = {
                    "run_id": generated.state.run_id,
                    "status": generated.state.status.value,
                    "classification": generated.state.classification.value,
                    "run_dir": generated.run_dir.as_posix(),
                    "artifact_path": generated.artifact.relative_path if generated.artifact else None,
                    "ready_for": (
                        "test_execution"
                        if generated.workspace
                        else (
                            "human_decision"
                            if generated.state.status
                            in {
                                RunStatus.WAITING_FOR_CLARIFICATION,
                                RunStatus.WAITING_FOR_HUMAN_REVIEW,
                            }
                            else None
                        )
                    ),
                    "report_path": (
                        f"{generated.run_dir.as_posix()}/{terminal_report_path}"
                        if terminal_report_path
                        else None
                    ),
                    "report_json": (
                        f"{generated.run_dir.as_posix()}/report.json"
                        if terminal_report_path
                        else None
                    ),
                    "report_markdown": (
                        f"{generated.run_dir.as_posix()}/report.md"
                        if terminal_report_path
                        else None
                    ),
                    "report_schema_version": (
                        REPORT_SCHEMA_VERSION if terminal_report_path else None
                    ),
                }
                code = 0 if generated.workspace else int(
                    exit_code_for(generated.state.status, generated.state.classification)
                )
            else:
                completed = CompleteWorkflowService(
                    generation_service,
                    DockerUnitTestAdapter(args.output, timeout_seconds=60),
                    store,
                ).execute(request)
                payload = {
                    "run_id": completed.state.run_id,
                    "status": completed.state.status.value,
                    "classification": completed.state.classification.value,
                    "run_dir": completed.run_dir.as_posix(),
                    "report_path": (
                        f"{completed.run_dir.as_posix()}/{completed.report_path}"
                        if completed.report_path
                        else None
                    ),
                    "report_json": (
                        f"{completed.run_dir.as_posix()}/report.json"
                        if completed.report_path
                        else None
                    ),
                    "report_markdown": (
                        f"{completed.run_dir.as_posix()}/report.md"
                        if completed.report_path
                        else None
                    ),
                    "report_schema_version": (
                        REPORT_SCHEMA_VERSION if completed.report_path else None
                    ),
                }
                code = int(exit_code_for(completed.state.status, completed.state.classification))
    except (
        OptionalWorkflowDependencyError,
        HumanCheckpointError,
        SmokeSuiteInfrastructureError,
        SecuritySuiteInfrastructureError,
        DoctorInfrastructureError,
        CleanupInfrastructureError,
    ) as exc:
        logger.error(
            "command_failed",
            extra={"operation": args.command, "component": "cli", "classification": "INFRASTRUCTURE_ERROR"},
            exc_info=True,
        )
        print(json.dumps({"status": "FAILED", "classification": "INFRASTRUCTURE_ERROR"}))
        print(f"asef: {exc}", file=sys.stderr)
        close_operational_logging(logger)
        return 7
    except (
        ContractValidationError,
        ApiContractError,
        BackendApiPolicyError,
        WebUiPolicyError,
        JavaUnitContractError,
        JavaUnitPolicyError,
        CapabilityRunContractError,
        ContextValidationError,
        RecordedAgentError,
        GatewayError,
        ProviderError,
        OSError,
        ValueError,
    ) as exc:
        logger.warning(
            "command_rejected: %s",
            exc,
            extra={"operation": args.command, "component": "cli", "classification": "INPUT_OR_CONTEXT_ERROR"},
        )
        print(json.dumps({"status": "REJECTED", "classification": "INPUT_OR_CONTEXT_ERROR"}), file=sys.stdout)
        print(f"asef: {exc}", file=sys.stderr)
        close_operational_logging(logger)
        return 2
    _log_completion(logger, args.command, payload["run_id"], payload, code)
    print(json.dumps(payload))
    close_operational_logging(logger)
    return code


def _log_completion(
    logger: logging.Logger,
    operation: str,
    run_id: str,
    payload: dict[str, object],
    code: int,
) -> None:
    logger.info(
        "command_completed",
        extra={
            "run_id": run_id,
            "operation": operation,
            "component": "cli",
            "status": payload["status"],
            "classification": payload["classification"],
            "exit_code": code,
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
