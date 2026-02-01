"""Workflow executor with middleware support and lifecycle hooks."""
from __future__ import annotations

import asyncio
import contextvars
import time
from typing import Any, AsyncIterator, TYPE_CHECKING

from ..core.logging import workflow_logger as logger
from ..core.context import InvocationContext, set_parent_id, reset_parent_id
from ..core.event_bus import Events
from ..core.types.block import BlockEvent, BlockKind, BlockOp
from ..core.types.session import generate_id
from ..core.signals import SuspendSignal, HITLSuspend
from ..middleware import HookAction
from .types import NodeType, NodeSpec, Workflow
from .expression import ExpressionEvaluator
from .state import WorkflowState, get_merge_strategy
from .dag import DAGExecutor
from ..core.factory import AgentFactory

if TYPE_CHECKING:
    from ..middleware import MiddlewareChain


class WorkflowExecutor:
    """Workflow executor with middleware hooks.
    
    Middleware priority:
    1. Node-level middleware (from NodeSpec.middleware)
    2. Workflow-level middleware (from WorkflowSpec.middleware)
    3. Context middleware (from InvocationContext.middleware)
    
    Calls middleware hooks:
    - on_subagent_start/end: when executing agent nodes
    """
    
    def __init__(
        self,
        workflow: Workflow,
        agent_factory: AgentFactory,
        ctx: InvocationContext,
        middleware: "MiddlewareChain | None" = None,
    ):
        self.workflow = workflow
        self.agent_factory = agent_factory
        self.ctx = ctx
        # Priority: explicit > workflow spec > context
        self.middleware = middleware or workflow.spec.middleware or ctx.middleware
        self.evaluator = ExpressionEvaluator()
        
        self._state = WorkflowState()
        self._paused = False
        self._waiting_for_input = False
        self._suspended = False
        self._suspended_node_id: str | None = None
        self._pending_request: dict | None = None
        self._start_time: float | None = None
        self._node_usage: dict[str, dict] = {}  # Track per-node usage
    
    async def execute(
        self,
        inputs: dict[str, Any],
        resume_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute workflow.
        
        Args:
            inputs: Workflow inputs
            resume_state: State to resume from (for pause/resume)
            
        Returns:
            Final workflow state/result
        """
        self._start_time = time.time()
        
        # Emit START block
        await self.ctx.emit(BlockEvent(
            block_id=generate_id("blk"),
            kind=BlockKind.START,
            op=BlockOp.APPLY,
            data={
                "workflow": self.workflow.spec.name,
                "inputs": inputs,
            },
        ))
        
        # Publish start event via Bus
        await self.ctx.bus.publish(Events.INVOCATION_START, {
            "invocation_id": self.ctx.invocation_id,
            "session_id": self.ctx.session_id,
            "workflow": self.workflow.spec.name,
        })
        
        # Resume from saved state if provided
        if resume_state:
            self._state = WorkflowState.from_dict(resume_state.get("workflow_state", {}))
            completed_nodes = set(resume_state.get("completed_nodes", []))
        else:
            completed_nodes = set()
        
        logger.info(
            "Starting workflow execution",
            extra={
                "workflow": self.workflow.spec.name,
                "session_id": self.ctx.session_id,
                "invocation_id": self.ctx.invocation_id,
            }
        )
        
        eval_context = {
            "inputs": inputs,
            "state": self._state,
        }
        
        dag = DAGExecutor(
            tasks=self.workflow.spec.nodes,
            get_task_id=lambda n: n.id,
            get_dependencies=lambda n: self.workflow.incoming_edges[n.id],
        )
        
        # Mark already completed nodes (for resume)
        for node_id in completed_nodes:
            dag.mark_completed(node_id)
        
        while not dag.is_finished() and not self.ctx.is_aborted and not self._paused and not self._waiting_for_input and not self._suspended:
            ready_nodes = dag.get_ready_tasks()
            logger.debug(
                f"Workflow iteration - ready nodes: {len(ready_nodes)}, completed: {len(dag.completed)}",
                extra={"workflow": self.workflow.spec.name, "invocation_id": self.ctx.invocation_id},
            )
            
            if not ready_nodes:
                # Check if we're blocked due to failed dependencies
                if dag.is_blocked():
                    logger.error(
                        "Workflow blocked due to failed dependencies",
                        extra={
                            "workflow": self.workflow.spec.name,
                            "invocation_id": self.ctx.invocation_id,
                            "failed_nodes": list(dag.failed),
                        },
                    )
                    # Mark remaining blocked nodes as skipped
                    processed = dag.completed | dag.failed | dag.running | dag.skipped
                    for node in self.workflow.spec.nodes:
                        if node.id not in processed:
                            dag.mark_skipped(node.id)
                    break
                await asyncio.sleep(0.05)
                continue
            
            tasks = []
            # Copy current context to ensure ContextVars are inherited by child tasks
            ctx = contextvars.copy_context()
            
            for node in ready_nodes:
                # Check condition
                if node.when:
                    if not self.evaluator.evaluate_condition(node.when, eval_context):
                        logger.debug(
                            f"Node skipped by condition: {node.id}",
                            extra={"workflow": self.workflow.spec.name, "invocation_id": self.ctx.invocation_id},
                        )
                        dag.mark_skipped(node.id)
                        continue
                
                logger.info(
                    f"Executing workflow node: {node.id} ({node.type.value})",
                    extra={"workflow": self.workflow.spec.name, "invocation_id": self.ctx.invocation_id},
                )
                dag.mark_running(node.id)
                # Create task with explicit context to preserve ContextVars (emit_queue, parent_id)
                task = asyncio.create_task(
                    self._execute_node_with_context(node, eval_context, dag),
                    context=ctx,
                )
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Persist state periodically
            await self._persist_state(dag, inputs)
        
        # Persist final state (including suspended state)
        await self._persist_state(dag, inputs)
        
        # Publish end event
        status = dag.get_status()
        
        # Calculate workflow duration
        duration_ms = int((time.time() - self._start_time) * 1000) if self._start_time else 0
        
        # Summarize usage
        usage_summary = None
        if self.ctx.usage:
            usage_summary = self.ctx.usage.summarize(
                session_id=self.ctx.session_id,
                invocation_id=self.ctx.invocation_id,
            )
        
        final_data = {
            "state": self._state.to_dict(),
            "status": status,
            "duration_ms": duration_ms,
            "usage": usage_summary,
            "node_usage": self._node_usage,
        }
        
        # Determine final status
        if self._suspended:
            final_status = "suspended"
        elif self._waiting_for_input:
            final_status = "paused"
        else:
            final_status = "completed"
        
        # Emit END block with output (as sibling of start, both are roots)
        await self.ctx.emit(BlockEvent(
            block_id=generate_id("blk"),
            kind=BlockKind.END,
            op=BlockOp.APPLY,
            data={
                "status": final_status,
                "output": self._state.to_dict(),
                "duration_ms": duration_ms,
                "usage": usage_summary,
            },
        ))
        
        # Publish end event via Bus (includes usage summary)
        await self.ctx.bus.publish(Events.INVOCATION_END, {
            "invocation_id": self.ctx.invocation_id,
            "session_id": self.ctx.session_id,
            "status": final_status,
            "usage": usage_summary,
        })
        
        logger.info(
            "Workflow execution completed",
            extra={
                "workflow": self.workflow.spec.name,
                "completed": status["completed"],
                "failed": status["failed"],
                "duration_ms": duration_ms,
                "total_tokens": usage_summary.get("total_tokens") if usage_summary else 0,
            }
        )
        
        return final_data
    
    async def _persist_state(self, dag: DAGExecutor, inputs: dict[str, Any] | None = None) -> None:
        """Persist workflow state for recovery.
        
        Stores execution state including:
        - workflow_state: WorkflowState output values
        - completed_nodes: Nodes that finished execution
        - current_node: Node where suspension occurred (if suspended)
        - pending_request: HITL request details (if suspended)
        - inputs: Original workflow inputs
        """
        state_key = f"workflow_state:{self.ctx.invocation_id}"
        state_data = {
            "workflow_state": self._state.to_dict(),
            "completed_nodes": list(dag.get_status().get("completed_ids", [])),
            "inputs": inputs or {},
            "waiting_for_input": self._waiting_for_input,
            "suspended": self._suspended,
        }
        
        # Add suspension-specific data
        if self._suspended:
            state_data["current_node"] = self._suspended_node_id
            if self._pending_request:
                state_data["pending_request"] = self._pending_request
        
        if self.ctx.backends and self.ctx.backends.state:
            await self.ctx.backends.state.set("workflow", state_key, state_data)
    
    def pause(self) -> None:
        """Pause execution."""
        self._paused = True
    
    async def _execute_node_with_context(
        self,
        node: NodeSpec,
        eval_context: dict[str, Any],
        dag: DAGExecutor,
    ) -> None:
        """Execute node directly without context copying.
        
        Previously used context copying + nested task creation,
        but this caused ContextVar issues. Now we execute directly
        since set_parent_id is called within _run_single_agent.
        """
        await self._execute_node(node, eval_context, dag)
    
    async def _execute_node(
        self,
        node: NodeSpec,
        eval_context: dict[str, Any],
        dag: DAGExecutor,
    ) -> None:
        """Execute single node with lifecycle hooks.
        
        Each node execution creates a NODE block. All child agent blocks
        will have this node block as their parent via set_parent_id().
        
        Block hierarchy:
            NODE block (node_id, status: running -> completed/failed)
            └── [Child agent blocks, all with parent_id = node_block_id]
                ├── text
                ├── tool_use
                └── tool_result
        """
        node_start_time = time.time()
        node_block_id = generate_id("blk")
        
        try:
            match node.type:
                case NodeType.TRIGGER:
                    # Start node - emit NODE block with inputs
                    logger.info(
                        "Workflow START node",
                        extra={"node_id": node.id, "invocation_id": self.ctx.invocation_id},
                    )
                    await self.ctx.emit(BlockEvent(
                        block_id=node_block_id,
                        kind=BlockKind.NODE,
                        op=BlockOp.APPLY,
                        data={
                            "node_id": node.id,
                            "agent": "start",
                            "status": "running",
                            "inputs": eval_context.get("inputs", {}),
                        },
                    ))
                    # Immediately complete
                    await self.ctx.emit(BlockEvent(
                        block_id=node_block_id,
                        kind=BlockKind.NODE,
                        op=BlockOp.PATCH,
                        data={
                            "status": "completed",
                            "duration_ms": int((time.time() - node_start_time) * 1000),
                        },
                    ))
                    dag.mark_completed(node.id)
                
                case NodeType.TERMINAL:
                    # End node - emit NODE block with final output
                    logger.info(
                        "Workflow END node",
                        extra={"node_id": node.id, "invocation_id": self.ctx.invocation_id},
                    )
                    # Resolve output from node config or collect from state
                    output = self._state.to_dict()
                    if node.inputs:
                        output = self.evaluator.resolve_inputs(node.inputs, eval_context)
                    
                    await self.ctx.emit(BlockEvent(
                        block_id=node_block_id,
                        kind=BlockKind.NODE,
                        op=BlockOp.APPLY,
                        data={
                            "node_id": node.id,
                            "agent": "end",
                            "status": "running",
                            "inputs": output,
                        },
                    ))
                    # Immediately complete with output
                    await self.ctx.emit(BlockEvent(
                        block_id=node_block_id,
                        kind=BlockKind.NODE,
                        op=BlockOp.PATCH,
                        data={
                            "status": "completed",
                            "duration_ms": int((time.time() - node_start_time) * 1000),
                            "output": output,
                        },
                    ))
                    dag.mark_completed(node.id)
                
                case NodeType.AGENT:
                    # Resolve inputs
                    inputs = self.evaluator.resolve_inputs(node.inputs, eval_context)
                    
                    logger.info(
                        f"Workflow AGENT node: {node.agent}",
                        extra={
                            "node_id": node.id,
                            "agent": node.agent,
                            "invocation_id": self.ctx.invocation_id,
                        },
                    )
                    
                    # Emit NODE block with status "running"
                    await self.ctx.emit(BlockEvent(
                        block_id=node_block_id,
                        kind=BlockKind.NODE,
                        op=BlockOp.APPLY,
                        data={
                            "node_id": node.id,
                            "agent": node.agent,
                            "status": "running",
                            "inputs": inputs,
                        },
                    ))
                    
                    # Execute agent with node_block_id as parent for child blocks
                    result = await self._execute_agent_node(node, eval_context, node_block_id)
                    
                    # Record node duration
                    duration_ms = int((time.time() - node_start_time) * 1000)
                    self._node_usage[node.id] = {
                        "duration_ms": duration_ms,
                        "agent": node.agent,
                    }
                    
                    # Patch NODE block with completed status
                    await self.ctx.emit(BlockEvent(
                        block_id=node_block_id,
                        kind=BlockKind.NODE,
                        op=BlockOp.PATCH,
                        data={
                            "status": "completed",
                            "duration_ms": duration_ms,
                            "output": result,
                        },
                    ))
                    
                    dag.mark_completed(node.id)
                
                case NodeType.CONDITION:
                    logger.info(
                        f"Workflow CONDITION node: {node.id}",
                        extra={"node_id": node.id, "invocation_id": self.ctx.invocation_id},
                    )
                    await self._execute_condition_node(node, eval_context, dag)
                
                case _:
                    dag.mark_completed(node.id)
        
        except SuspendSignal as e:
            # HITL/Pause signal from child agent or tool
            logger.warning(
                "Workflow node suspended (HITL)",
                extra={
                    "node_id": node.id,
                    "signal_type": type(e).__name__,
                    "request_id": getattr(e, "request_id", None),
                    "invocation_id": self.ctx.invocation_id,
                },
            )
            
            # Patch NODE block with suspended status
            if node.type == NodeType.AGENT:
                await self.ctx.emit(BlockEvent(
                    block_id=node_block_id,
                    kind=BlockKind.NODE,
                    op=BlockOp.PATCH,
                    data={
                        "status": "suspended",
                        "duration_ms": int((time.time() - node_start_time) * 1000),
                    },
                ))
            
            # Store suspension state
            self._suspended = True
            self._suspended_node_id = node.id
            if isinstance(e, HITLSuspend):
                self._pending_request = e.to_dict()
            
            # Don't mark as failed or completed - will resume later
            # The DAG executor will stop because self._suspended is True
        
        except Exception as e:
            logger.error(
                "Workflow node execution failed",
                extra={
                    "node_id": node.id,
                    "error": str(e),
                    "invocation_id": self.ctx.invocation_id,
                },
                exc_info=True,
            )
            
            # Patch NODE block with failed status (if it was created)
            if node.type == NodeType.AGENT:
                await self.ctx.emit(BlockEvent(
                    block_id=node_block_id,
                    kind=BlockKind.NODE,
                    op=BlockOp.PATCH,
                    data={
                        "status": "failed",
                        "error": str(e),
                        "duration_ms": int((time.time() - node_start_time) * 1000),
                    },
                ))
            
            dag.mark_failed(node.id)
    
    async def _execute_agent_node(
        self,
        node: NodeSpec,
        eval_context: dict[str, Any],
        parent_block_id: str,
    ) -> Any:
        """Execute agent node and return result.
        
        Args:
            node: Node specification
            eval_context: Evaluation context with inputs and state
            parent_block_id: Block ID to use as parent for all child blocks
        """
        if "foreach" in node.config:
            items = self.evaluator.evaluate(node.config["foreach"], eval_context)
            item_var = node.config.get("as", "item")
            merge_strategy = node.config.get("merge", "collect_list")
            
            results = []
            for item in items:
                branch_state = self._state.create_branch()
                branch_context = {
                    **eval_context,
                    item_var: item,
                    "state": branch_state,
                }
                
                result = await self._run_single_agent(node, branch_context, parent_block_id)
                results.append(result)
            
            strategy = get_merge_strategy(merge_strategy)
            merged = strategy.merge(results)
            if node.output:
                self._state[node.output] = merged
            return merged
        else:
            result = await self._run_single_agent(node, eval_context, parent_block_id)
            if node.output:
                self._state[node.output] = result
            return result
    
    def _get_effective_middleware(
        self,
        node: NodeSpec,
    ) -> "MiddlewareChain | None":
        """Get effective middleware for a node.
        
        Merges node-level middleware with workflow/context middleware.
        Node middleware takes precedence (runs first).
        """
        from ..middleware import MiddlewareChain
        
        # Start with workflow/context middleware
        base_middleware = self.middleware
        
        # If node has its own middleware, create merged chain
        if node.middleware:
            merged = MiddlewareChain()
            
            # Add node middleware first (higher priority)
            for mw in node.middleware:
                merged.use(mw)
            
            # Add base middleware (lower priority)
            if base_middleware:
                for mw in base_middleware.middlewares:
                    merged.use(mw)
            
            return merged
        
        return base_middleware
    
    async def _run_single_agent(
        self,
        node: NodeSpec,
        eval_context: dict[str, Any],
        parent_block_id: str,
    ) -> Any:
        """Execute single agent with middleware hooks.
        
        Sub-agent's emit calls go to the same ContextVar queue,
        so they automatically flow to the parent's run() yield.
        
        The parent_block_id is set via ContextVar so all child blocks
        automatically inherit it as their parent_id.
        
        Args:
            node: Node specification
            eval_context: Evaluation context
            parent_block_id: Block ID for parent-child nesting
        """
        inputs = self.evaluator.resolve_inputs(node.inputs, eval_context)
        
        # Get effective middleware for this node
        effective_middleware = self._get_effective_middleware(node)
        
        # === Middleware: on_subagent_start ===
        if effective_middleware:
            hook_result = await effective_middleware.process_subagent_start(
                self.workflow.spec.name,
                node.agent,
                "embedded",  # Workflow nodes are embedded execution
            )
            if hook_result.action == HookAction.SKIP:
                logger.info(f"SubAgent {node.agent} skipped by middleware")
                return {"skipped": True, "message": hook_result.message}
        
        # Set parent_block_id via ContextVar so all child blocks inherit it
        # This is the key mechanism for block nesting
        token = set_parent_id(parent_block_id)
        
        try:
            # Create child context for sub-agent with effective middleware
            # Note: parent_block_id is already set via ContextVar above
            # Get agent name from factory if available
            agent_class = self.agent_factory.get_class(node.agent)
            agent_name = getattr(agent_class, 'name', node.agent) if agent_class else node.agent
            
            child_ctx = self.ctx.create_child(
                agent_id=node.agent,
                agent_name=agent_name,
                middleware=effective_middleware,
            )
            
            agent = self.agent_factory.create(
                agent_type=node.agent,
                ctx=child_ctx,
            )
            
            # Run agent and fully consume the generator
            # Must consume completely to avoid ContextVar issues
            result = None
            try:
                async for response in agent.run(inputs):
                    # Check for result in response
                    if hasattr(response, 'type') and response.type == "session_end" and response.data:
                        result = response.data.get("result")
            except GeneratorExit:
                pass  # Generator was closed early, that's ok
            
            # Check for result stored on agent instance (WorkflowNodeAgent pattern)
            # Prefer _outputs dict (typed outputs), fallback to _result (legacy)
            if hasattr(agent, '_outputs') and agent._outputs:
                result = agent._outputs
            elif result is None and hasattr(agent, '_result'):
                result = agent._result
            
            # === Middleware: on_subagent_end ===
            if effective_middleware:
                await effective_middleware.process_subagent_end(
                    self.workflow.spec.name,
                    node.agent,
                    result,
                )
            
            return result
        
        finally:
            # Always reset parent_id to previous value
            reset_parent_id(token)
    
    async def _execute_condition_node(
        self,
        node: NodeSpec,
        eval_context: dict[str, Any],
        dag: DAGExecutor,
    ) -> None:
        """Execute condition node."""
        condition_result = self.evaluator.evaluate_condition(
            node.expression, eval_context
        )
        
        if condition_result:
            # then branch - mark else branch as skipped
            if node.else_node:
                dag.mark_skipped(node.else_node)
        else:
            # else branch - mark then branch as skipped
            if node.then_node:
                dag.mark_skipped(node.then_node)
        
        dag.mark_completed(node.id)
    
    def stop(self) -> None:
        """Stop execution."""
        self.ctx.abort_self.set()
    
    @property
    def state(self) -> WorkflowState:
        """Get current state."""
        return self._state
