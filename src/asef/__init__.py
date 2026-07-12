"""Public ASEF skeleton contracts.

The package deliberately contains no framework adapters in Stage 4.1.
"""

from .contracts import (
    ContextSnapshot,
    ContractValidationError,
    EvidenceRef,
    NormalizedExecutionResult,
    SkeletonBudgetLimits,
    SkeletonBudgetUsage,
    SkeletonRunRequest,
    SkeletonRunState,
    UnitTestArtifact,
)
from .outcomes import ExitCode, RunClassification, RunStatus, exit_code_for

__all__ = [
    "ContextSnapshot",
    "ContractValidationError",
    "EvidenceRef",
    "ExitCode",
    "NormalizedExecutionResult",
    "RunClassification",
    "RunStatus",
    "SkeletonBudgetLimits",
    "SkeletonBudgetUsage",
    "SkeletonRunRequest",
    "SkeletonRunState",
    "UnitTestArtifact",
    "exit_code_for",
]
