from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .budgets import BudgetController
from .domain import BudgetLimits, BudgetUsage, WorkflowRequest
from .gateway import OpenAIResponsesGateway, RecordedModelGateway
from .runner import DemoWorkflowRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="asef-spike")
    parser.add_argument("--mode", choices=("demo", "live"), default="demo")
    parser.add_argument("--title", default="Sum two integers")
    parser.add_argument(
        "--requirement",
        default="The add(a, b) function returns the arithmetic sum of two integers.",
    )
    parser.add_argument("--sut", default="calculator.add")
    parser.add_argument("--output", type=Path, default=Path("runs"))
    parser.add_argument(
        "--cassette",
        type=Path,
        default=Path("tests/fixtures/cassettes/wf001_analysis_success.json"),
    )
    parser.add_argument("--api-budget-brl", type=float, default=0.0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    limits = BudgetLimits(api_budget_brl=args.api_budget_brl)
    usage = BudgetUsage()
    controller = BudgetController(limits, usage)
    if args.mode == "demo":
        gateway = RecordedModelGateway(args.cassette, controller)
    else:
        gateway = OpenAIResponsesGateway(
            controller,
            model=os.environ.get("ASEF_OPENAI_MODEL"),
        )

    request = WorkflowRequest(
        requirement_title=args.title,
        requirement_description=args.requirement,
        sut_entrypoint=args.sut,
        execution_mode=args.mode,
    )
    state = DemoWorkflowRunner(gateway, args.output, controller).run(request)
    print(json.dumps({"run_id": state.run_id, "status": state.status.value}, ensure_ascii=False))
    if state.status.value == "SUCCEEDED":
        return 0
    if state.status.value in {"WAITING_FOR_CLARIFICATION", "WAITING_FOR_HUMAN_REVIEW"}:
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
