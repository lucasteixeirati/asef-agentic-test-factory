"""Framework-independent baseline for ASEF architectural spikes."""

from .domain import RunState, RunStatus
from .state_machine import WorkflowMachine

__all__ = ["RunState", "RunStatus", "WorkflowMachine"]

