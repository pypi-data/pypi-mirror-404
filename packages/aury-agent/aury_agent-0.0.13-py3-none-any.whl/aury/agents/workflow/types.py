"""Workflow DSL types."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..middleware import Middleware, MiddlewareChain


class NodeType(Enum):
    """Workflow node types."""
    TRIGGER = "trigger"
    AGENT = "agent"
    PARALLEL = "parallel"
    SEQUENCE = "sequence"
    CONDITION = "condition"
    TERMINAL = "terminal"


@dataclass
class Position:
    """Node position for visual editors."""
    x: float = 0.0
    y: float = 0.0


@dataclass
class NodeSpec:
    """Node specification."""
    id: str
    type: NodeType
    position: Position = field(default_factory=Position)
    agent: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)
    output: str | None = None
    when: str | None = None  # Conditional expression
    
    # For parallel/sequence nodes
    branches: list[dict[str, Any]] | None = None
    steps: list[str] | None = None
    
    # For condition nodes
    expression: str | None = None
    then_node: str | None = None
    else_node: str | None = None
    
    # Node-level middleware (overrides/extends workflow middleware)
    middleware: list["Middleware"] | None = None


@dataclass
class EdgeSpec:
    """Edge specification."""
    from_node: str
    to_node: str
    when: str | None = None  # Conditional edge


@dataclass
class WorkflowSpec:
    """Workflow specification from DSL."""
    name: str
    version: str = "1.0"
    description: str | None = None
    state: dict[str, str] = field(default_factory=dict)
    inputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    nodes: list[NodeSpec] = field(default_factory=list)
    edges: list[EdgeSpec] = field(default_factory=list)
    
    # Workflow-level middleware (applied to all nodes)
    middleware: "MiddlewareChain | None" = None


@dataclass
class Workflow:
    """Parsed executable workflow."""
    spec: WorkflowSpec
    
    # Computed properties
    node_map: dict[str, NodeSpec] = field(default_factory=dict)
    incoming_edges: dict[str, list[str]] = field(default_factory=dict)
    outgoing_edges: dict[str, list[str]] = field(default_factory=dict)
    edge_conditions: dict[tuple[str, str], str | None] = field(default_factory=dict)
