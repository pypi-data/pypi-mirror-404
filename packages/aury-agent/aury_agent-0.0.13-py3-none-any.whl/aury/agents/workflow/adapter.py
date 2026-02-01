"""Workflow agent - executes DAG-based workflows.

WorkflowAgent uses the unified BaseAgent constructor:
    __init__(self, ctx: InvocationContext, config: AgentConfig | None = None)

Workflow definition and AgentFactory are passed via config or set after init.

Middleware hooks are called at:
- on_agent_start/end: workflow start/end
- on_subagent_start/end: each node execution (in executor)
"""
from __future__ import annotations

from typing import Any, AsyncIterator, ClassVar, Literal, TYPE_CHECKING

from ..core.base import BaseAgent, AgentConfig
from ..core.context import InvocationContext
from ..core.logging import workflow_logger as logger
from ..core.types.block import BlockEvent, BlockKind, BlockOp
from ..middleware import HookAction
from .types import Workflow
from .executor import WorkflowExecutor

if TYPE_CHECKING:
    from ..core.factory import AgentFactory
    from ..core.types.session import Session
    from ..backends import Backends
    from ..core.event_bus import Bus
    from ..middleware import MiddlewareChain


class WorkflowAgent(BaseAgent):
    """Workflow agent - executes DAG-based workflows.
    
    Two ways to create:
    
    1. Simple (recommended):
        agent = WorkflowAgent.create(workflow=wf, agent_factory=factory)
    
    2. Advanced (for custom Session/Backends/Bus):
        ctx = InvocationContext(session=session, backends=backends, bus=bus)
        agent = WorkflowAgent(ctx, config)
        agent.set_workflow(workflow, agent_factory)
    """
    
    agent_type: ClassVar[Literal["react", "workflow"]] = "workflow"
    
    @classmethod
    def create(
        cls,
        workflow: Workflow,
        agent_factory: "WorkflowAgentFactory",
        config: AgentConfig | None = None,
        *,
        backends: "Backends | None" = None,
        session: "Session | None" = None,
        bus: "Bus | None" = None,
        middleware: "MiddlewareChain | None" = None,
    ) -> "WorkflowAgent":
        """Create WorkflowAgent with minimal boilerplate.
        
        Args:
            workflow: Workflow definition
            agent_factory: Factory for creating sub-agents
            config: Agent configuration (optional)
            backends: Backends container (auto-created if None)
            session: Session object (auto-created if None)
            bus: Event bus (auto-created if None)
            middleware: Middleware chain (optional)
            
        Returns:
            Configured WorkflowAgent ready to run
            
        Example:
            agent = WorkflowAgent.create(
                workflow=my_workflow,
                agent_factory=factory,
            )
            async for response in agent.run(inputs):
                print(response)
        """
        from ..core.event_bus import Bus
        from ..core.types.session import Session, generate_id
        from ..backends import Backends
        
        # Auto-create backends if not provided
        if backends is None:
            backends = Backends.create_default()
        
        # Auto-create missing components
        if session is None:
            session = Session(id=generate_id("sess"))
        if bus is None:
            bus = Bus()
        
        # Build context
        ctx = InvocationContext(
            session=session,
            invocation_id=generate_id("inv"),
            agent_id=config.name if config else workflow.spec.name,
            backends=backends,
            bus=bus,
            middleware=middleware,
        )
        
        agent = cls(ctx, config)
        agent.set_workflow(workflow, agent_factory)
        return agent

    def __init__(
        self,
        ctx: InvocationContext,
        config: AgentConfig | None = None,
    ):
        """Initialize WorkflowAgent.
        
        Args:
            ctx: InvocationContext with storage, bus, etc.
            config: Agent configuration (may contain workflow in metadata)
        """
        super().__init__(ctx, config)
        
        # Workflow can be set via config.metadata or set_workflow()
        self.workflow: Workflow | None = self.config.metadata.get('workflow')
        self.agent_factory: "WorkflowAgentFactory | None" = self.config.metadata.get('agent_factory')
        self._executor: WorkflowExecutor | None = None
    
    def set_workflow(
        self,
        workflow: Workflow,
        agent_factory: "WorkflowAgentFactory",
    ) -> "WorkflowAgent":
        """Set workflow definition and factory.
        
        Args:
            workflow: Workflow definition
            agent_factory: Factory for creating sub-agents
            
        Returns:
            Self for chaining
        """
        logger.debug(f"WorkflowAgent set_workflow, workflow_name={workflow.spec.name}, invocation_id={self.ctx.invocation_id}")
        self.workflow = workflow
        self.agent_factory = agent_factory
        return self
    
    async def _execute(self, input: Any) -> None:
        """Execute workflow with middleware hooks.
        
        Args:
            input: Workflow inputs (dict or single value)
            
        Raises:
            ValueError: If workflow or agent_factory not set
        """
        # Validate workflow is set
        if self.workflow is None:
            raise ValueError("Workflow not set. Call set_workflow() first.")
        if self.agent_factory is None:
            raise ValueError("AgentFactory not set. Call set_workflow() first.")
        
        inputs = input if isinstance(input, dict) else {"input": input}
        logger.info(f"WorkflowAgent executing, workflow={self.workflow.spec.name}, invocation_id={self.ctx.invocation_id}")
        
        # === Middleware: on_agent_start ===
        if self.middleware:
            logger.debug(f"WorkflowAgent: processing on_agent_start hooks, invocation_id={self.ctx.invocation_id}")
            hook_result = await self.middleware.process_agent_start(inputs)
            if hook_result.action == HookAction.STOP:
                logger.warning(f"Workflow stopped by middleware on_agent_start, invocation_id={self.ctx.invocation_id}")
                await self.ctx.emit(BlockEvent(
                    kind=BlockKind.ERROR,
                    op=BlockOp.APPLY,
                    data={"message": hook_result.message or "Stopped by middleware"},
                ))
                return
            elif hook_result.action == HookAction.SKIP:
                logger.warning(f"Workflow skipped by middleware on_agent_start, invocation_id={self.ctx.invocation_id}")
                return
        
        try:
            logger.debug(f"WorkflowAgent: creating executor, workflow={self.workflow.spec.name}, invocation_id={self.ctx.invocation_id}")
            # Create executor with context (pass middleware)
            self._executor = WorkflowExecutor(
                workflow=self.workflow,
                agent_factory=self.agent_factory,
                ctx=self.ctx,
                middleware=self.middleware,
            )
            
            result = await self._executor.execute(inputs)
            logger.info(f"WorkflowAgent: execution completed, workflow={self.workflow.spec.name}, invocation_id={self.ctx.invocation_id}")
            
            # === Middleware: on_agent_end ===
            if self.middleware:
                logger.debug(f"WorkflowAgent: processing on_agent_end hooks, invocation_id={self.ctx.invocation_id}")
                await self.middleware.process_agent_end(result)
        
        except Exception as e:
            logger.error(f"WorkflowAgent: execution error, error={type(e).__name__}, workflow={self.workflow.spec.name}, invocation_id={self.ctx.invocation_id}", exc_info=True)
            # === Middleware: on_error ===
            if self.middleware:
                logger.debug(f"WorkflowAgent: processing on_error hooks, invocation_id={self.ctx.invocation_id}")
                processed_error = await self.middleware.process_error(e)
                if processed_error is None:
                    logger.warning(f"WorkflowAgent: error suppressed by middleware, invocation_id={self.ctx.invocation_id}")
                    return
            raise
    
    async def pause(self) -> str:
        """Pause workflow and return invocation ID."""
        logger.info(f"WorkflowAgent pause requested, invocation_id={self.ctx.invocation_id}")
        if self._executor:
            self._executor.pause()
        return self.ctx.invocation_id
    
    async def _resume_internal(self, invocation_id: str) -> None:
        """Internal resume logic."""
        logger.info(f"WorkflowAgent resuming, invocation_id={invocation_id}")
        if self.workflow is None or self.agent_factory is None:
            raise ValueError("Workflow not set. Call set_workflow() first.")
        
        # Load saved state
        state_key = f"workflow_state:{invocation_id}"
        if not self.ctx.backends or not self.ctx.backends.state:
            raise ValueError("No state backend available")
        logger.debug(f"WorkflowAgent: loading saved state, state_key={state_key}, invocation_id={invocation_id}")
        saved_state = await self.ctx.backends.state.get("workflow", state_key)
        
        if not saved_state:
            logger.error(f"WorkflowAgent: no saved state found, state_key={state_key}, invocation_id={invocation_id}")
            raise ValueError(f"No saved state for invocation: {invocation_id}")
        
        inputs = saved_state.get("inputs", {})
        logger.debug(f"WorkflowAgent: resume state loaded, inputs_keys={list(inputs.keys())}, invocation_id={invocation_id}")
        
        # Create executor and resume
        self._executor = WorkflowExecutor(
            workflow=self.workflow,
            agent_factory=self.agent_factory,
            ctx=self.ctx,
        )
        
        logger.info(f"WorkflowAgent: resuming execution, workflow={self.workflow.spec.name}, invocation_id={invocation_id}")
        await self._executor.execute(inputs, resume_state=saved_state)
    
    async def resume(self, invocation_id: str) -> AsyncIterator[BlockEvent]:
        """Resume paused workflow."""
        logger.debug(f"WorkflowAgent resume iterator started, invocation_id={invocation_id}")
        import asyncio
        from ..core.context import _emit_queue_var
        
        queue: asyncio.Queue[BlockEvent] = asyncio.Queue()
        token = _emit_queue_var.set(queue)
        
        try:
            exec_task = asyncio.create_task(self._resume_internal(invocation_id))
            block_count = 0
            
            while not exec_task.done() or not queue.empty():
                try:
                    block = await asyncio.wait_for(queue.get(), timeout=0.05)
                    block_count += 1
                    logger.debug(f"WorkflowAgent resume: yielding block, kind={block.kind}, block_num={block_count}, invocation_id={invocation_id}")
                    yield block
                except asyncio.TimeoutError:
                    continue
            
            await exec_task
            logger.debug(f"WorkflowAgent resume: completed, total_blocks={block_count}, invocation_id={invocation_id}")
            
        finally:
            _emit_queue_var.reset(token)

