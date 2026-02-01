"""Python DSL for workflow definition.

Provides a fluent API for building workflows:

```python
from aury.agents.workflow.dsl import workflow, step, parallel, condition
from aury.agents.middleware import BaseMiddleware, MiddlewareChain

# Simple sequence
wf = workflow("my_workflow") >> step("A") >> step("B") >> step("C")

# Parallel execution
wf = workflow("my_workflow") >> parallel(
    step("A"),
    step("B"),
) >> step("C")

# Conditional branching
wf = workflow("my_workflow") >> condition(
    expr="state.mode == 'fast'",
    then_=step("FastPath"),
    else_=step("SlowPath"),
)

# With middleware at workflow level
class LoggingMiddleware(BaseMiddleware):
    async def on_agent_start(self, agent_id, input_data, context):
        print(f"Starting {agent_id}")
        return HookResult.proceed()

middleware = MiddlewareChain().use(LoggingMiddleware())
wf = workflow("my_workflow").middleware(middleware) >> step("A") >> step("B")

# With middleware at step level
wf = workflow("my_workflow") >> step("A").with_middleware(LoggingMiddleware()) >> step("B")
```
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TYPE_CHECKING
from uuid import uuid4

from .types import NodeType, NodeSpec, EdgeSpec, WorkflowSpec, Position

if TYPE_CHECKING:
    from ..middleware import Middleware, MiddlewareChain


def _gen_id(prefix: str = "node") -> str:
    """Generate unique node ID."""
    return f"{prefix}_{uuid4().hex[:8]}"


@dataclass
class DSLNode:
    """Base DSL node for workflow building."""
    
    id: str
    node_type: NodeType
    config: dict[str, Any] = field(default_factory=dict)
    children: list["DSLNode"] = field(default_factory=list)
    condition: str | None = None  # Skip condition
    node_middleware: list["Middleware"] = field(default_factory=list)  # Node-level middleware
    
    def __rshift__(self, other: "DSLNode") -> "DSLSequence":
        """Chain operator: a >> b creates sequence."""
        return DSLSequence([self, other])
    
    def skip_when(self, condition: str) -> "DSLNode":
        """Set skip condition for this node.
        
        Usage:
            step("A").skip_when("state.skip_a == True")
        """
        self.condition = condition
        return self
    
    def with_middleware(self, *middlewares: "Middleware") -> "DSLNode":
        """Add middleware to this specific node.
        
        Usage:
            step("A").with_middleware(LoggingMiddleware(), MetricsMiddleware())
        """
        self.node_middleware.extend(middlewares)
        return self
    
    def to_spec(self, position: Position | None = None) -> NodeSpec:
        """Convert to NodeSpec."""
        return NodeSpec(
            id=self.id,
            type=self.node_type,
            position=position or Position(),
            config=self.config,
            when=self.condition,
            middleware=self.node_middleware if self.node_middleware else None,
        )


class DSLSequence:
    """Sequence of DSL nodes (a >> b >> c)."""
    
    def __init__(self, nodes: list[DSLNode]):
        self.nodes = nodes
    
    def __rshift__(self, other: DSLNode | "DSLSequence") -> "DSLSequence":
        """Extend sequence with more nodes."""
        if isinstance(other, DSLSequence):
            return DSLSequence(self.nodes + other.nodes)
        return DSLSequence(self.nodes + [other])


@dataclass 
class DSLStep(DSLNode):
    """Agent step node."""
    
    agent_name: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    output_key: str | None = None
    
    def __init__(
        self,
        agent: str,
        inputs: dict[str, Any] | None = None,
        output: str | None = None,
        id: str | None = None,
        middleware: list["Middleware"] | None = None,
    ):
        super().__init__(
            id=id or _gen_id("step"),
            node_type=NodeType.AGENT,
        )
        self.agent_name = agent
        self.inputs = inputs or {}
        self.output_key = output
        if middleware:
            self.node_middleware = middleware
    
    def to_spec(self, position: Position | None = None) -> NodeSpec:
        return NodeSpec(
            id=self.id,
            type=self.node_type,
            position=position or Position(),
            agent=self.agent_name,
            config=self.config,
            inputs=self.inputs,
            output=self.output_key,
            when=self.condition,
            middleware=self.node_middleware if self.node_middleware else None,
        )


@dataclass
class DSLParallel(DSLNode):
    """Parallel execution node."""
    
    branches: list[DSLNode | DSLSequence] = field(default_factory=list)
    merge_strategy: str = "collect_list"
    
    def __init__(
        self,
        *branches: DSLNode | DSLSequence,
        merge: str = "collect_list",
        id: str | None = None,
    ):
        super().__init__(
            id=id or _gen_id("parallel"),
            node_type=NodeType.PARALLEL,
        )
        self.branches = list(branches)
        self.merge_strategy = merge
        self.config["merge_strategy"] = merge
    
    def to_spec(self, position: Position | None = None) -> NodeSpec:
        # Convert branches to spec format
        branch_specs = []
        for branch in self.branches:
            if isinstance(branch, DSLSequence):
                # Sequence: list of step IDs
                branch_specs.append({
                    "steps": [n.id for n in branch.nodes]
                })
            else:
                # Single node
                branch_specs.append({
                    "steps": [branch.id]
                })
        
        return NodeSpec(
            id=self.id,
            type=self.node_type,
            position=position or Position(),
            config=self.config,
            branches=branch_specs,
            when=self.condition,
        )


@dataclass
class DSLCondition(DSLNode):
    """Conditional branching node."""
    
    expression: str = ""
    then_branch: DSLNode | DSLSequence | None = None
    else_branch: DSLNode | DSLSequence | None = None
    
    def __init__(
        self,
        expr: str,
        then_: DSLNode | DSLSequence | None = None,
        else_: DSLNode | DSLSequence | None = None,
        id: str | None = None,
    ):
        super().__init__(
            id=id or _gen_id("condition"),
            node_type=NodeType.CONDITION,
        )
        self.expression = expr
        self.then_branch = then_
        self.else_branch = else_
    
    def to_spec(self, position: Position | None = None) -> NodeSpec:
        then_id = None
        else_id = None
        
        if self.then_branch:
            if isinstance(self.then_branch, DSLSequence):
                then_id = self.then_branch.nodes[0].id if self.then_branch.nodes else None
            else:
                then_id = self.then_branch.id
        
        if self.else_branch:
            if isinstance(self.else_branch, DSLSequence):
                else_id = self.else_branch.nodes[0].id if self.else_branch.nodes else None
            else:
                else_id = self.else_branch.id
        
        return NodeSpec(
            id=self.id,
            type=self.node_type,
            position=position or Position(),
            config=self.config,
            expression=self.expression,
            then_node=then_id,
            else_node=else_id,
            when=self.condition,
        )


class DSLWorkflow:
    """Workflow builder using DSL."""
    
    def __init__(
        self,
        name: str,
        version: str = "1.0",
        description: str | None = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.nodes: list[DSLNode] = []
        self.state_schema: dict[str, str] = {}
        self.input_schema: dict[str, dict[str, Any]] = {}
        self._root: DSLNode | DSLSequence | None = None
        self._middleware: "MiddlewareChain | None" = None
    
    def __rshift__(self, other: DSLNode | DSLSequence) -> "DSLWorkflow":
        """Set workflow root: workflow >> step("A")."""
        self._root = other
        return self
    
    def middleware(
        self,
        *middlewares: "Middleware | MiddlewareChain",
    ) -> "DSLWorkflow":
        """Set workflow-level middleware.
        
        These middleware hooks apply to all nodes in the workflow.
        Accepts individual middlewares or a MiddlewareChain.
        Can be called multiple times to add more middleware.
        
        Usage:
            # Pass individual middlewares
            workflow("wf").middleware(LoggingMiddleware(), MetricsMiddleware()) >> step("A")
            
            # Pass a MiddlewareChain
            chain = MiddlewareChain().use(LoggingMiddleware())
            workflow("wf").middleware(chain) >> step("A")
            
            # Multiple calls (additive)
            workflow("wf").middleware(LoggingMiddleware()).middleware(MetricsMiddleware())
        """
        from ..middleware import MiddlewareChain as MWChain
        
        # Initialize chain if needed
        if self._middleware is None:
            self._middleware = MWChain()
        
        for mw in middlewares:
            if isinstance(mw, MWChain):
                # Merge chains
                for m in mw.middlewares:
                    self._middleware.use(m)
            else:
                # Add individual middleware
                self._middleware.use(mw)
        
        return self
    
    def state(self, **schema: str) -> "DSLWorkflow":
        """Define state schema.
        
        Usage:
            workflow("wf").state(count="int", items="list[str]")
        """
        self.state_schema.update(schema)
        return self
    
    def inputs(self, **schema: dict[str, Any]) -> "DSLWorkflow":
        """Define input schema.
        
        Usage:
            workflow("wf").inputs(
                query={"type": "string", "required": True}
            )
        """
        self.input_schema.update(schema)
        return self
    
    def build(self) -> WorkflowSpec:
        """Build WorkflowSpec from DSL."""
        nodes: list[NodeSpec] = []
        edges: list[EdgeSpec] = []
        
        # Collect all nodes from root
        all_nodes = self._collect_nodes(self._root)
        
        # Convert to specs with positions
        y_offset = 0
        for node in all_nodes:
            pos = Position(x=100, y=y_offset)
            nodes.append(node.to_spec(pos))
            y_offset += 100
        
        # Generate edges
        edges = self._generate_edges(self._root)
        
        return WorkflowSpec(
            name=self.name,
            version=self.version,
            description=self.description,
            state=self.state_schema,
            inputs=self.input_schema,
            nodes=nodes,
            edges=edges,
            middleware=self._middleware,
        )
    
    def _collect_nodes(
        self,
        root: DSLNode | DSLSequence | None,
    ) -> list[DSLNode]:
        """Recursively collect all nodes."""
        if root is None:
            return []
        
        nodes: list[DSLNode] = []
        
        if isinstance(root, DSLSequence):
            for node in root.nodes:
                nodes.extend(self._collect_nodes(node))
        elif isinstance(root, DSLParallel):
            nodes.append(root)
            for branch in root.branches:
                nodes.extend(self._collect_nodes(branch))
        elif isinstance(root, DSLCondition):
            nodes.append(root)
            if root.then_branch:
                nodes.extend(self._collect_nodes(root.then_branch))
            if root.else_branch:
                nodes.extend(self._collect_nodes(root.else_branch))
        else:
            nodes.append(root)
        
        return nodes
    
    def _generate_edges(
        self,
        root: DSLNode | DSLSequence | None,
    ) -> list[EdgeSpec]:
        """Generate edges from DSL structure."""
        if root is None:
            return []
        
        edges: list[EdgeSpec] = []
        
        if isinstance(root, DSLSequence):
            # Sequential edges
            for i in range(len(root.nodes) - 1):
                from_node = root.nodes[i]
                to_node = root.nodes[i + 1]
                
                # Handle parallel/condition getting last node
                from_id = self._get_exit_id(from_node)
                to_id = self._get_entry_id(to_node)
                
                edges.append(EdgeSpec(from_node=from_id, to_node=to_id))
                
                # Recurse into complex nodes
                edges.extend(self._generate_edges(from_node))
            
            # Last node recursion
            if root.nodes:
                edges.extend(self._generate_edges(root.nodes[-1]))
                
        elif isinstance(root, DSLParallel):
            # Edges into each branch
            for branch in root.branches:
                entry_id = self._get_entry_id(branch)
                edges.append(EdgeSpec(from_node=root.id, to_node=entry_id))
                edges.extend(self._generate_edges(branch))
                
        elif isinstance(root, DSLCondition):
            if root.then_branch:
                then_entry = self._get_entry_id(root.then_branch)
                edges.append(EdgeSpec(
                    from_node=root.id,
                    to_node=then_entry,
                    when=root.expression,
                ))
                edges.extend(self._generate_edges(root.then_branch))
            
            if root.else_branch:
                else_entry = self._get_entry_id(root.else_branch)
                edges.append(EdgeSpec(
                    from_node=root.id,
                    to_node=else_entry,
                    when=f"not ({root.expression})",
                ))
                edges.extend(self._generate_edges(root.else_branch))
        
        return edges
    
    def _get_entry_id(self, node: DSLNode | DSLSequence) -> str:
        """Get entry node ID."""
        if isinstance(node, DSLSequence):
            return node.nodes[0].id if node.nodes else ""
        return node.id
    
    def _get_exit_id(self, node: DSLNode | DSLSequence) -> str:
        """Get exit node ID."""
        if isinstance(node, DSLSequence):
            return node.nodes[-1].id if node.nodes else ""
        return node.id


# ========== Convenience Functions ==========

def workflow(
    name: str,
    version: str = "1.0",
    description: str | None = None,
) -> DSLWorkflow:
    """Create a new workflow builder.
    
    Usage:
        wf = workflow("my_workflow", version="1.0")
        wf = wf >> step("agent_a") >> step("agent_b")
        spec = wf.build()
    """
    return DSLWorkflow(name, version, description)


def step(
    agent: str,
    inputs: dict[str, Any] | None = None,
    output: str | None = None,
    id: str | None = None,
    middleware: list["Middleware"] | None = None,
) -> DSLStep:
    """Create an agent step.
    
    Args:
        agent: Agent name to execute
        inputs: Input mapping (state keys or expressions)
        output: State key to store output
        id: Optional explicit node ID
        middleware: Optional step-level middleware list
    
    Usage:
        step("research_agent", inputs={"query": "state.user_query"}, output="results")
        
        # With step-level middleware
        step("agent", middleware=[LoggingMiddleware(), MetricsMiddleware()])
    """
    return DSLStep(agent=agent, inputs=inputs, output=output, id=id, middleware=middleware)


def parallel(
    *branches: DSLNode | DSLSequence,
    merge: str = "collect_list",
    id: str | None = None,
) -> DSLParallel:
    """Create parallel execution node.
    
    Args:
        *branches: Parallel branches (steps or sequences)
        merge: Merge strategy ("collect_list", "collect_dict", "first_success")
        id: Optional explicit node ID
    
    Usage:
        parallel(
            step("agent_a"),
            step("agent_b") >> step("agent_c"),
            merge="collect_list",
        )
    """
    return DSLParallel(*branches, merge=merge, id=id)


def condition(
    expr: str,
    then_: DSLNode | DSLSequence | None = None,
    else_: DSLNode | DSLSequence | None = None,
    id: str | None = None,
) -> DSLCondition:
    """Create conditional branching node.
    
    Args:
        expr: Condition expression (evaluated against state)
        then_: Branch to execute if condition is true
        else_: Branch to execute if condition is false
        id: Optional explicit node ID
    
    Usage:
        condition(
            expr="state.count > 10",
            then_=step("high_path"),
            else_=step("low_path"),
        )
    """
    return DSLCondition(expr=expr, then_=then_, else_=else_, id=id)


def skip(condition: str) -> Callable[[DSLNode], DSLNode]:
    """Decorator to set skip condition.
    
    Usage:
        @skip("state.skip_step")
        def my_step():
            return step("agent")
    
    Or inline:
        step("agent").skip_when("state.skip_step")
    """
    def decorator(node: DSLNode) -> DSLNode:
        node.condition = condition
        return node
    return decorator


__all__ = [
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
