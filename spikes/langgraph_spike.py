from __future__ import annotations

from dataclasses import asdict
from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from asef_spike.budgets import BudgetController
from asef_spike.domain import WorkflowRequest
from asef_spike.gateway import ModelGateway
from asef_spike.runner import RISK_SCHEMA


class GraphState(TypedDict):
    request: dict[str, Any]
    status: str
    facts: dict[str, Any]
    history: list[str]


def build_graph(gateway: ModelGateway, *, checkpointer=None):
    def get_request(state: GraphState) -> WorkflowRequest:
        return WorkflowRequest(**state["request"])

    def validate(state: GraphState) -> dict[str, Any]:
        errors = get_request(state).validate()
        return {
            "status": "FAILED" if errors else "VALIDATED",
            "facts": {**state["facts"], "validation_errors": errors},
            "history": [*state["history"], "validate"],
        }

    def route_validation(state: GraphState) -> str:
        return "failed" if state["status"] == "FAILED" else "inspect"

    def inspect(state: GraphState) -> dict[str, Any]:
        request = get_request(state)
        return {
            "status": "SUT_INSPECTED",
            "facts": {
                **state["facts"],
                "sut": {"entrypoint": request.sut_entrypoint, "profile": request.language_profile},
            },
            "history": [*state["history"], "inspect"],
        }

    def analyze(state: GraphState) -> dict[str, Any]:
        request = get_request(state)
        prompt = (
            "Analyze this software requirement for test design. Return behaviors, risks, scenarios, "
            "and whether clarification is required.\n\n"
            f"Title: {request.requirement_title}\n"
            f"Description: {request.requirement_description}\n"
            f"SUT entrypoint: {request.sut_entrypoint}"
        )
        result = gateway.generate(prompt=prompt, schema=RISK_SCHEMA, schema_name="wf001_analysis")
        return {
            "status": "ANALYZED",
            "facts": {
                **state["facts"],
                "analysis": result.output,
                "model": {"id": result.model, "recorded": result.recorded},
            },
            "history": [*state["history"], "analyze"],
        }

    def route_analysis(state: GraphState) -> str:
        return "clarification" if state["facts"]["analysis"]["clarification_required"] else "design"

    def clarification_wait(state: GraphState) -> dict[str, Any]:
        return {
            "status": "WAITING_FOR_CLARIFICATION",
            "history": [*state["history"], "clarification_wait"],
        }

    def collect_clarification(state: GraphState) -> dict[str, Any]:
        answer = interrupt(
            {
                "kind": "requirement_clarification",
                "question": "Provide the missing requirement clarification.",
            }
        )
        return {
            "status": "CLARIFIED",
            "facts": {**state["facts"], "clarification": str(answer)},
            "history": [*state["history"], "collect_clarification"],
        }

    def design(state: GraphState) -> dict[str, Any]:
        return {
            "status": "DESIGNED",
            "facts": {**state["facts"], "scenarios": state["facts"]["analysis"]["scenarios"]},
            "history": [*state["history"], "design"],
        }

    def simulate_execution(state: GraphState) -> dict[str, Any]:
        return {
            "status": "EXECUTED",
            "facts": {**state["facts"], "execution": {"status": "simulated", "passed": 1}},
            "history": [*state["history"], "simulate_execution"],
        }

    def report(state: GraphState) -> dict[str, Any]:
        return {"status": "SUCCEEDED", "history": [*state["history"], "report"]}

    builder = StateGraph(GraphState)
    builder.add_node("validate", validate)
    builder.add_node("inspect", inspect)
    builder.add_node("analyze", analyze)
    builder.add_node("clarification_wait", clarification_wait)
    builder.add_node("collect_clarification", collect_clarification)
    builder.add_node("design", design)
    builder.add_node("simulate_execution", simulate_execution)
    builder.add_node("report", report)
    builder.add_edge(START, "validate")
    builder.add_conditional_edges("validate", route_validation, {"failed": END, "inspect": "inspect"})
    builder.add_edge("inspect", "analyze")
    builder.add_conditional_edges(
        "analyze",
        route_analysis,
        {"clarification": "clarification_wait", "design": "design"},
    )
    builder.add_edge("clarification_wait", "collect_clarification")
    builder.add_edge("collect_clarification", "design")
    builder.add_edge("design", "simulate_execution")
    builder.add_edge("simulate_execution", "report")
    builder.add_edge("report", END)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


def run_graph(graph, request: WorkflowRequest, *, thread_id: str = "spike-thread") -> GraphState:
    initial: GraphState = {
        "request": asdict(request),
        "status": "RECEIVED",
        "facts": {},
        "history": [],
    }
    return graph.invoke(initial, {"configurable": {"thread_id": thread_id}})


def resume_graph(graph, answer: str, *, thread_id: str = "spike-thread") -> GraphState:
    return graph.invoke(
        Command(resume=answer),
        {"configurable": {"thread_id": thread_id}},
    )
