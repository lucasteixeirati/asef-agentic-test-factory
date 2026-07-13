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
from .application.generate_unit import GenerateUnitTestService
from .application.complete_workflow import CompleteWorkflowService
from .application.prepare_run import PrepareRunService
from .context import ContextValidationError
from .contracts import ContractValidationError, SkeletonRunRequest
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
    return parser


def _recorded_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--analysis-cassette",
        type=Path,
        default=Path("tests/fixtures/cassettes/wf001_analysis_success.json"),
    )
    parser.add_argument(
        "--artifact-cassette",
        type=Path,
        default=Path("tests/fixtures/cassettes/wf001_unit_artifact_success.json"),
    )


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--context", type=Path, default=Path("examples/context/walking-skeleton-context.json")
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
        store = JsonRunStore(args.output)
        prepare_service = PrepareRunService(FileQualityContextAdapter(), store)
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
            )
            if args.command == "generate":
                generated = generation_service.execute(request)
                payload = {
                    "run_id": generated.state.run_id,
                    "status": generated.state.status.value,
                    "classification": generated.state.classification.value,
                    "run_dir": generated.run_dir.as_posix(),
                    "artifact_path": generated.artifact.relative_path if generated.artifact else None,
                    "ready_for": "test_execution" if generated.workspace else "human_or_policy_resolution",
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
    except (ContractValidationError, ContextValidationError, RecordedAgentError, OSError) as exc:
        print(json.dumps({"status": "REJECTED", "classification": "INPUT_OR_CONTEXT_ERROR"}), file=sys.stdout)
        print(f"asef: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
