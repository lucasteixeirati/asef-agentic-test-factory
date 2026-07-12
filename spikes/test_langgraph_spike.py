from __future__ import annotations

import unittest
import sqlite3
import tempfile
from pathlib import Path

from asef.adapters.gateway import RecordedModelGateway
from asef.legacy.domain import BudgetLimits, BudgetUsage, WorkflowRequest
from asef.runtime.budgets import BudgetController
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph_spike import build_graph, resume_graph, run_graph


class LangGraphSpikeTests(unittest.TestCase):
    def gateway(self, usage: BudgetUsage) -> RecordedModelGateway:
        return RecordedModelGateway(
            Path("tests/fixtures/cassettes/wf001_analysis_success.json"),
            BudgetController(BudgetLimits(), usage),
        )

    def clarification_gateway(self, usage: BudgetUsage) -> RecordedModelGateway:
        return RecordedModelGateway(
            Path("tests/fixtures/cassettes/wf001_analysis_clarification.json"),
            BudgetController(BudgetLimits(), usage),
        )

    def test_happy_path_matches_baseline_outcome(self) -> None:
        usage = BudgetUsage()
        graph = build_graph(self.gateway(usage))
        result = run_graph(
            graph,
            WorkflowRequest("Add", "Return the sum of two integers", "calculator.add"),
        )
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(usage.model_calls, 1)
        self.assertEqual(
            result["history"],
            ["validate", "inspect", "analyze", "design", "simulate_execution", "report"],
        )

    def test_invalid_input_ends_without_model_call(self) -> None:
        usage = BudgetUsage()
        graph = build_graph(self.gateway(usage))
        result = run_graph(graph, WorkflowRequest("", "", ""), thread_id="invalid")
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(usage.model_calls, 0)

    def test_checkpointer_preserves_final_state(self) -> None:
        usage = BudgetUsage()
        graph = build_graph(self.gateway(usage))
        config = {"configurable": {"thread_id": "checkpoint"}}
        run_graph(
            graph,
            WorkflowRequest("Add", "Return the sum of two integers", "calculator.add"),
            thread_id="checkpoint",
        )
        snapshot = graph.get_state(config)
        self.assertEqual(snapshot.values["status"], "SUCCEEDED")

    def test_interrupt_waits_for_human_and_resumes(self) -> None:
        usage = BudgetUsage()
        graph = build_graph(self.clarification_gateway(usage))
        result = run_graph(
            graph,
            WorkflowRequest("Transfer", "Transfer funds safely", "payments.transfer"),
            thread_id="clarification",
        )
        self.assertEqual(result["status"], "WAITING_FOR_CLARIFICATION")
        self.assertIn("__interrupt__", result)

        resumed = resume_graph(graph, "Only authenticated owners may transfer", thread_id="clarification")
        self.assertEqual(resumed["status"], "SUCCEEDED")
        self.assertEqual(resumed["facts"]["clarification"], "Only authenticated owners may transfer")
        self.assertEqual(usage.model_calls, 1)

    def test_sqlite_checkpoint_survives_graph_recreation(self) -> None:
        usage = BudgetUsage()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "checkpoints.sqlite"
            first_connection = sqlite3.connect(database, check_same_thread=False)
            first_graph = build_graph(
                self.clarification_gateway(usage),
                checkpointer=SqliteSaver(first_connection),
            )
            waiting = run_graph(
                first_graph,
                WorkflowRequest("Transfer", "Transfer funds safely", "payments.transfer"),
                thread_id="durable",
            )
            self.assertEqual(waiting["status"], "WAITING_FOR_CLARIFICATION")
            first_connection.close()

            second_connection = sqlite3.connect(database, check_same_thread=False)
            try:
                second_graph = build_graph(
                    self.clarification_gateway(usage),
                    checkpointer=SqliteSaver(second_connection),
                )
                resumed = resume_graph(
                    second_graph,
                    "Transfers are limited to R$ 1.000",
                    thread_id="durable",
                )
                self.assertEqual(resumed["status"], "SUCCEEDED")
                self.assertEqual(usage.model_calls, 1)
            finally:
                second_connection.close()


if __name__ == "__main__":
    unittest.main()
