"""Regression baseline retained during the 4.R1 promotion.

This namespace is not the target public API. It will be retired after the
walking skeleton demonstrates equivalent behavior through the new runtime.
"""

from .domain import RunState, RunStatus
from .state_machine import WorkflowMachine

__all__ = ["RunState", "RunStatus", "WorkflowMachine"]
