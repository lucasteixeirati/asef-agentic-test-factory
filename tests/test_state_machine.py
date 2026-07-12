from __future__ import annotations

import unittest

from asef_spike.domain import RunState, RunStatus, WorkflowRequest
from asef_spike.state_machine import InvalidTransition, WorkflowMachine


def request() -> WorkflowRequest:
    return WorkflowRequest("Add", "Return the sum", "calculator.add")


class WorkflowMachineTests(unittest.TestCase):
    def test_happy_path_records_history(self) -> None:
        state = RunState(request())
        machine = WorkflowMachine(state)

        machine.transition(RunStatus.VALIDATING_INPUT, "start")
        machine.transition(RunStatus.INSPECTING_SUT, "input_valid")

        self.assertEqual(state.status, RunStatus.INSPECTING_SUT)
        self.assertEqual(len(state.history), 2)
        self.assertEqual(state.history[0]["source"], "RECEIVED")

    def test_invalid_transition_is_rejected(self) -> None:
        machine = WorkflowMachine(RunState(request()))
        with self.assertRaises(InvalidTransition):
            machine.transition(RunStatus.SUCCEEDED, "skip_everything")

    def test_terminal_state_cannot_transition(self) -> None:
        state = RunState(request(), status=RunStatus.FAILED)
        machine = WorkflowMachine(state)
        with self.assertRaises(InvalidTransition):
            machine.transition(RunStatus.CANCELLED, "cancel")

    def test_global_policy_block_is_allowed_from_active_state(self) -> None:
        state = RunState(request(), status=RunStatus.ANALYZING_RISK)
        machine = WorkflowMachine(state)
        machine.transition(RunStatus.POLICY_BLOCKED, "runtime_policy")
        self.assertEqual(state.status, RunStatus.POLICY_BLOCKED)


if __name__ == "__main__":
    unittest.main()

