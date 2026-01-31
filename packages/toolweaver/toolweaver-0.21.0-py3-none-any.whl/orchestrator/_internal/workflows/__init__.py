"""
Workflows subpackage

Workflow-related modules and control-flow patterns under a stable namespace.
"""

from .control_flow_patterns import (
    ControlFlowPatterns,
    PatternType,
    create_conditional_code,
    create_parallel_code,
    create_polling_code,
    create_retry_code,
)
from .engine import WorkflowExecutor
from .workflow import (
    StepStatus,
    WorkflowContext,
    WorkflowStep,
    WorkflowTemplate,
)
from .workflow_library import (
    PatternDetector,
    ToolSequence,
    WorkflowLibrary,
)

__all__ = [
    # control flow
    "ControlFlowPatterns",
    "PatternType",
    "create_polling_code",
    "create_parallel_code",
    "create_conditional_code",
    "create_retry_code",
    # workflow core
    "WorkflowTemplate",
    "WorkflowStep",
    "WorkflowExecutor",
    "WorkflowContext",
    "StepStatus",
    # workflow library
    "WorkflowLibrary",
    "PatternDetector",
    "ToolSequence",
]
