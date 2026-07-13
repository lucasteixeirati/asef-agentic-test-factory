from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters.context_file import FileQualityContextAdapter
from .adapters.docker_execution import DockerUnitTestAdapter
from .adapters.recorded_agent import RecordedAgentAdapter, RecordedAgentError
from .adapters.run_store import JsonRunStore
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
from .context import ContextValidationError
from .contracts import ContractValidationError, SkeletonRunRequest
from .demo import materialize_demo_assets
from .outcomes import exit_code_for
from .skills.unit import UnitSkill


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


def _decision_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, default=Path(".asef/runs"))
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        allowed_output_root = (Path.cwd() / ".asef").resolve()
        resolved_output = args.output.resolve()
        if not resolved_output.is_relative_to(allowed_output_root):
            raise ContractValidationError("output must remain inside the .asef directory")
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
            print(json.dumps(payload))
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
            if args.mode != "demo":
                raise ContractValidationError("generate and run support recorded demo mode only")
            generation_service = GenerateUnitTestService(
                prepare_service,
                RecordedAgentAdapter(args.analysis_cassette, args.artifact_cassette),
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
    except (OptionalWorkflowDependencyError, HumanCheckpointError) as exc:
        print(json.dumps({"status": "FAILED", "classification": "INFRASTRUCTURE_ERROR"}))
        print(f"asef: {exc}", file=sys.stderr)
        return 7
    except (ContractValidationError, ContextValidationError, RecordedAgentError, OSError, ValueError) as exc:
        print(json.dumps({"status": "REJECTED", "classification": "INPUT_OR_CONTEXT_ERROR"}), file=sys.stdout)
        print(f"asef: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
