"""Workflow system for DAG-based orchestration."""
from .types import (
    NodeType,
    Position,
    NodeSpec,
    EdgeSpec,
    WorkflowSpec,
    Workflow,
)
from .parser import (
    WorkflowParser,
    WorkflowValidationError,
)
from .expression import (
    ExpressionEvaluator,
    ExpressionError,
)
from .state import (
    WorkflowState,
    MergeStrategy,
    CollectListStrategy,
    CollectDictStrategy,
    FirstSuccessStrategy,
    get_merge_strategy,
)
from .dag import DAGExecutor
from .executor import WorkflowExecutor
from ..core.factory import AgentFactory
from .adapter import WorkflowAgent
from .dsl import (
    DSLNode,
    DSLSequence,
    DSLStep,
    DSLParallel,
    DSLCondition,
    DSLWorkflow,
    workflow,
    step,
    parallel,
    condition,
    skip,
)

__all__ = [
    # Types
    "NodeType",
    "Position",
    "NodeSpec",
    "EdgeSpec",
    "WorkflowSpec",
    "Workflow",
    # Parser
    "WorkflowParser",
    "WorkflowValidationError",
    # Expression
    "ExpressionEvaluator",
    "ExpressionError",
    # State
    "WorkflowState",
    "MergeStrategy",
    "CollectListStrategy",
    "CollectDictStrategy",
    "FirstSuccessStrategy",
    "get_merge_strategy",
    # DAG
    "DAGExecutor",
    # Executor
    "WorkflowExecutor",
    # Factory
    "AgentFactory",
    # Agent
    "WorkflowAgent",
    # DSL
    "DSLNode",
    "DSLSequence",
    "DSLStep",
    "DSLParallel",
    "DSLCondition",
    "DSLWorkflow",
    "workflow",
    "step",
    "parallel",
    "condition",
    "skip",
]
