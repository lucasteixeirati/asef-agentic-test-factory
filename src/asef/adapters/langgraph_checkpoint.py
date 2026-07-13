from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, TypedDict


class OptionalWorkflowDependencyError(RuntimeError):
    pass


class HumanCheckpointError(RuntimeError):
    pass


class _CheckpointState(TypedDict):
    run_id: str
    payload: dict[str, object]
    decision: dict[str, str] | None


class LangGraphHumanCheckpointAdapter:
    """Optional technical checkpoint; ASEF remains the domain authority."""

    def pause(self, run_id: str, database: Path, payload: dict[str, object]) -> None:
        graph, connection, config, interrupt_type, _ = self._open(run_id, database)
        try:
            result = graph.invoke(
                {"run_id": run_id, "payload": payload, "decision": None},
                config,
            )
            if "__interrupt__" not in result:
                raise HumanCheckpointError("checkpoint graph did not reach a human interrupt")
            if not isinstance(result["__interrupt__"][0], interrupt_type):
                raise HumanCheckpointError("checkpoint returned an unexpected interrupt type")
        finally:
            connection.close()

    def resume(self, run_id: str, database: Path, answer: str) -> dict[str, object]:
        return self._decide(run_id, database, {"action": "resume", "answer": answer})

    def cancel(self, run_id: str, database: Path, reason: str) -> dict[str, object]:
        return self._decide(run_id, database, {"action": "cancel", "reason": reason})

    def _decide(
        self,
        run_id: str,
        database: Path,
        decision: dict[str, str],
    ) -> dict[str, object]:
        if not database.is_file():
            raise HumanCheckpointError("checkpoint database does not exist")
        graph, connection, config, _, command_type = self._open(run_id, database)
        try:
            snapshot = graph.get_state(config)
            existing = snapshot.values.get("decision") if snapshot.values else None
            if existing is not None:
                result = snapshot.values
            else:
                result = graph.invoke(command_type(resume=decision), config)
        except (sqlite3.DatabaseError, KeyError, TypeError, ValueError) as exc:
            raise HumanCheckpointError(f"checkpoint cannot be resumed safely: {exc}") from exc
        finally:
            connection.close()
        if result.get("decision") != decision or not isinstance(result.get("payload"), dict):
            raise HumanCheckpointError("checkpoint result is inconsistent with the human decision")
        return {"payload": result["payload"], "decision": result["decision"]}

    @staticmethod
    def _open(run_id: str, database: Path):
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
            from langgraph.graph import END, START, StateGraph
            from langgraph.types import Command, Interrupt, interrupt
        except ImportError as exc:
            raise OptionalWorkflowDependencyError(
                "human checkpoint commands require the workflow-langgraph optional extra"
            ) from exc

        database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database, check_same_thread=False)

        def wait_for_human(state: _CheckpointState) -> dict[str, object]:
            decision = interrupt(
                {
                    "kind": "requirement_clarification",
                    "run_id": state["run_id"],
                }
            )
            return {"decision": decision}

        builder = StateGraph(_CheckpointState)
        builder.add_node("wait_for_human", wait_for_human)
        builder.add_edge(START, "wait_for_human")
        builder.add_edge("wait_for_human", END)
        graph = builder.compile(checkpointer=SqliteSaver(connection))
        return graph, connection, {"configurable": {"thread_id": run_id}}, Interrupt, Command
