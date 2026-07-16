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
from .adapters.docker_execution import DockerUnitTestAdapter
from .adapters.recorded_agent import RecordedAgentAdapter, RecordedAgentError
from .adapters.gateway import GatewayError, OpenAIResponsesGateway
from .adapters.live_agent import LiveAgentAdapter, LiveAgentConfig
from .adapters.run_store import JsonRunStore
from .adapters.smoke_case_executor import SmokeCaseExecutorAdapter
from .adapters.smoke_dataset import SmokeDatasetLoader
from .adapters.smoke_report_store import SmokeReportStore
from .adapters.workspace import EphemeralWorkspaceAdapter
from .adapters.langgraph_checkpoint import (
    HumanCheckpointError,
    LangGraphHumanCheckpointAdapter,
    OptionalWorkflowDependencyError,
)
from .application.generate_unit import GenerateUnitTestService
from .application.complete_workflow import CompleteWorkflowService
from .application.human_decision import HumanDecisionService
from .application.prepare_run import PrepareRunService
from .application.smoke_runner import SmokeSuiteInfrastructureError, SmokeSuiteRunner
from .context import ContextValidationError
from .contracts import ContractValidationError, SkeletonRunRequest
from .application.ports import ProviderError
from .demo import materialize_demo_assets
from .outcomes import exit_code_for
from .observability import close_operational_logging, configure_operational_logging
from .skills.unit import UnitSkill


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
        return "0.1.0a4"


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
        if getattr(args, "mode", "demo") == "live" and not context_was_explicit:
            raise ContractValidationError("live mode requires an explicit --context")
        allowed_output_root = (Path.cwd() / ".asef").resolve()
        resolved_output = args.output.resolve()
        if not resolved_output.is_relative_to(allowed_output_root):
            raise ContractValidationError("output must remain inside the .asef directory")
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
                payload = {
                    "run_id": generated.state.run_id,
                    "status": generated.state.status.value,
                    "classification": generated.state.classification.value,
                    "run_dir": generated.run_dir.as_posix(),
                    "artifact_path": generated.artifact.relative_path if generated.artifact else None,
                    "ready_for": (
                        "test_execution"
                        if generated.workspace
                        else "human_decision"
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
                }
                code = int(exit_code_for(completed.state.status, completed.state.classification))
    except (OptionalWorkflowDependencyError, HumanCheckpointError, SmokeSuiteInfrastructureError) as exc:
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
