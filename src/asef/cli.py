from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters.context_file import FileQualityContextAdapter
from .adapters.run_store import JsonRunStore
from .application.prepare_run import PrepareRunService
from .context import ContextValidationError
from .contracts import ContractValidationError, SkeletonRunRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="asef")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="prepare WF-001 up to the agentic boundary")
    prepare.add_argument(
        "--context",
        type=Path,
        default=Path("examples/context/walking-skeleton-context.json"),
    )
    prepare.add_argument("--system", default="calculator-service")
    prepare.add_argument("--skill", default="unit")
    prepare.add_argument("--title", default="Sum two integers")
    prepare.add_argument(
        "--requirement",
        default="The add(a, b) function returns the arithmetic sum of two integers.",
    )
    prepare.add_argument("--mode", choices=("demo", "live"), default="demo")
    prepare.add_argument("--api-budget-brl", type=float, default=0.0)
    prepare.add_argument("--output", type=Path, default=Path(".asef/runs"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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
    try:
        result = PrepareRunService(
            FileQualityContextAdapter(),
            JsonRunStore(args.output),
        ).execute(request)
    except (ContractValidationError, ContextValidationError, OSError) as exc:
        print(json.dumps({"status": "REJECTED", "classification": "INPUT_OR_CONTEXT_ERROR"}), file=sys.stdout)
        print(f"asef: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "run_id": result.state.run_id,
                "status": result.state.status.value,
                "classification": result.state.classification.value,
                "run_dir": result.run_dir.as_posix(),
                "ready_for": "requirement_analysis",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
