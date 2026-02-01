"""Delegate tool - delegate tasks to sub-agents.

Uses SubAgentBackend to retrieve available agents.
LLM specifies agent key and task data.
Mode is determined by agent config, not LLM.

Supports parallel execution of multiple sub-agents.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, TYPE_CHECKING

from ...core.logging import tool_logger as logger
from ...core.types.tool import BaseTool, ToolContext, ToolResult
from ...core.types.session import generate_id, ControlFrame
from ...core.types.subagent import SubAgentMode, SubAgentResult, SubAgentMetadata
from ...core.types.block import BlockEvent, BlockKind, BlockOp
from ...core.parallel import ParallelSubAgentContext

if TYPE_CHECKING:
    from ...backends.subagent import SubAgentBackend, AgentConfig
    from ...middleware import MiddlewareChain


class DelegateTool(BaseTool):
    """Delegate tasks to sub-agents.
    
    Uses SubAgentBackend to retrieve available agents.
    The execution mode (embedded/delegated) is determined by agent config.
    """
    
    _name = "delegate"
    
    def __init__(
        self,
        subagent_backend: "SubAgentBackend",
        middleware: "MiddlewareChain | None" = None,
    ):
        """Initialize with SubAgentBackend.
        
        Args:
            subagent_backend: Backend for retrieving sub-agents
            middleware: Optional middleware chain for progressive disclosure
        """
        self.backend = subagent_backend
        self.middleware = middleware
        self._description_cache: str | None = None
        self._parameters_cache: dict | None = None
        self._active_block_ids: dict[str, str] = {}  # session_id:agent -> block_id
        self._dynamic_agents: dict[str, "AgentConfig"] = {}  # Dynamic agents from middleware
    
    @property
    def name(self) -> str:
        return self._name
    
    def _get_agents_sync(self) -> list["AgentConfig"]:
        """Synchronously get agent list for property getters."""
        if hasattr(self.backend, 'list_sync'):
            return self.backend.list_sync()
        return []
    
    @property
    def description(self) -> str:
        """Build description with available agents."""
        agents = self._get_agents_sync()
        if not agents:
            return "Delegate a task to a specialized sub-agent. No agents currently available."
        
        agent_list = "\n".join([
            f"  - {a.key}: {a.description or 'No description'}"
            for a in agents
        ])
        return f"""Delegate a task to a specialized sub-agent.

Available agents:
{agent_list}

Provide task_context (user intent, background, requirements) and artifact_refs (related materials) for the sub-agent."""
    
    @property
    def parameters(self) -> dict[str, Any]:
        """Build parameters with agent enum."""
        agents = self._get_agents_sync()
        agent_keys = [a.key for a in agents] if agents else []
        
        agent_schema: dict[str, Any] = {
            "type": "string",
            "description": "Key of the agent to delegate to",
        }
        if agent_keys:
            agent_schema["enum"] = agent_keys
        
        return {
            "type": "object",
            "properties": {
                "agent": agent_schema,
                "task_context": {
                    "type": "string",
                    "description": "任务上下文：尽可能描述用户意图、背景信息、具体要求。包括用户最初的问题、对话中提到的偏好、强调的重点等。",
                },
                "artifact_refs": {
                    "type": "array",
                    "description": "相关资料引用列表，每项包含 id 和 summary",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Artifact ID"},
                            "summary": {"type": "string", "description": "摘要"},
                        },
                        "required": ["id"],
                    },
                },
            },
            "required": ["agent"],
        }
    
    async def get_dynamic_description(self, ctx: ToolContext | None = None) -> str:
        """Build description with available agents.
        
        Includes both static agents from backend and dynamic agents from middleware.
        """
        agents = await self._get_all_agents(ctx)
        if not agents:
            return "Delegate a task to a sub-agent. No agents currently available."
        
        agent_list = "\n".join([
            f"- {a.key}: {a.description or 'No description'} (mode: {a.mode})"
            for a in agents
        ])
        return f"""Delegate a task to a specialized sub-agent.

Available agents:
{agent_list}

Specify the agent key and task data."""
    
    async def _get_all_agents(
        self,
        ctx: ToolContext | None = None,
    ) -> list["AgentConfig"]:
        """Get all available agents (static + dynamic from middleware).
        
        Args:
            ctx: Optional tool context for middleware disclosure
            
        Returns:
            Combined list of AgentConfig
        """
        # Get static agents from backend
        agents = list(await self.backend.list())
        
        # Get dynamic agents from middleware (progressive disclosure)
        if self.middleware and ctx:
            dynamic_agents = await self.middleware.get_dynamic_subagents()
            if dynamic_agents:
                # Store dynamic agents for later lookup
                for config in dynamic_agents:
                    self._dynamic_agents[config.key] = config
                agents.extend(dynamic_agents)
        
        return agents
    
    async def _get_agent_config(
        self,
        key: str,
        ctx: ToolContext | None = None,
    ) -> "AgentConfig | None":
        """Get agent config by key (static or dynamic).
        
        Args:
            key: Agent key
            ctx: Optional tool context
            
        Returns:
            AgentConfig or None if not found
        """
        # First check static backend
        config = await self.backend.get(key)
        if config:
            return config
        
        # Then check dynamic agents from middleware
        if key in self._dynamic_agents:
            return self._dynamic_agents[key]
        
        # If not found and we have middleware, try to refresh dynamic agents
        if self.middleware and ctx:
            await self._get_all_agents(ctx)
            return self._dynamic_agents.get(key)
        
        return None
    
    async def execute(
        self,
        params: dict[str, Any],
        ctx: ToolContext,
    ) -> ToolResult:
        """Execute delegation.
        
        Supports two modes:
        1. Single agent: {"agent": "name", "data": {...}}
        2. Parallel agents: {"agents": [{"agent": "name1", "data": {...}}, ...]}
        """
        # Check if parallel execution
        agents_param = params.get("agents")
        if agents_param and isinstance(agents_param, list) and len(agents_param) > 1:
            return await self._execute_parallel(agents_param, ctx)
        
        # Single agent execution
        agent_key = params.get("agent", "")
        task_context = params.get("task_context")
        artifact_refs = params.get("artifact_refs")
        
        # Handle single item in agents array
        if agents_param and len(agents_param) == 1:
            agent_key = agents_param[0].get("agent", "")
            task_context = task_context or agents_param[0].get("task_context")
            artifact_refs = artifact_refs or agents_param[0].get("artifact_refs")
        
        if not agent_key:
            return ToolResult.error("Missing 'agent' parameter")
        
        logger.info(
            "Delegating to sub-agent",
            extra={
                "agent": agent_key,
                "invocation_id": ctx.invocation_id,
                "session_id": ctx.session_id,
            },
        )
        
        # Get agent config (static or dynamic)
        config = await self._get_agent_config(agent_key, ctx)
        if config is None:
            logger.error(
                f"Unknown sub-agent: {agent_key}",
                extra={"invocation_id": ctx.invocation_id},
            )
            agents = await self._get_all_agents(ctx)
            available = ", ".join(a.key for a in agents) or "none"
            return ToolResult.error(f"Unknown agent: {agent_key}. Available: {available}")
        
        # Create block_id for this delegation
        block_key = f"{ctx.session_id}:{config.key}"
        block_id = generate_id("blk")
        self._active_block_ids[block_key] = block_id
        
        # Emit SUB_AGENT block (start)
        await self._emit_subagent_block(ctx, config, "start", block_id)
        
        try:
            # 根据 create_invocation 决定执行模式
            mode = "delegated" if config.create_invocation else "embedded"
            logger.debug(
                f"Executing sub-agent in {mode} mode",
                extra={"agent": agent_key, "invocation_id": ctx.invocation_id},
            )
            
            if config.create_invocation:
                result = await self._execute_delegated(
                    config, ctx, task_context, artifact_refs
                )
            else:
                result = await self._execute_embedded(
                    config, ctx, task_context, artifact_refs
                )
            
            logger.info(
                f"Sub-agent execution completed",
                extra={
                    "agent": agent_key,
                    "invocation_id": ctx.invocation_id,
                    "is_error": result.is_error,
                },
            )
            
            # Emit SUB_AGENT block (end)
            await self._emit_subagent_block(ctx, config, "end", block_id)
            
            # Cleanup
            self._active_block_ids.pop(block_key, None)
            
            return result
        except Exception as e:
            logger.error(
                "Sub-agent delegation failed",
                extra={"agent": agent_key, "invocation_id": ctx.invocation_id, "error": str(e)},
                exc_info=True,
            )
            # Emit error state
            await self._emit_subagent_block(ctx, config, "error", block_id)
            self._active_block_ids.pop(block_key, None)
            return ToolResult.error(f"Delegation failed: {str(e)}")
    
    async def _execute_parallel(
        self,
        agents_param: list[dict[str, Any]],
        ctx: ToolContext,
    ) -> ToolResult:
        """Execute multiple sub-agents in parallel.
        
        Args:
            agents_param: List of {"agent": "name", ...}
            ctx: Tool context
            
        Returns:
            Combined results from all agents
        """
        logger.info(
            "Parallel delegation",
            extra={
                "agents": [a.get("agent") for a in agents_param],
                "invocation_id": ctx.invocation_id,
                "session_id": ctx.session_id,
                "count": len(agents_param),
            },
        )
        
        # Validate all agents exist
        configs: list["AgentConfig"] = []
        for item in agents_param:
            agent_key = item.get("agent", "")
            
            config = await self.backend.get(agent_key)
            if config is None:
                agents = await self.backend.list()
                available = ", ".join(a.key for a in agents) or "none"
                return ToolResult.error(f"Unknown agent: {agent_key}. Available: {available}")
            configs.append(config)
        
        # Create parallel context for tracking
        parallel_ctx = ParallelSubAgentContext(
            parent_invocation_id=ctx.invocation_id,
            session_id=ctx.session_id,
        )
        
        # Emit parallel start block
        parallel_block_id = generate_id("blk")
        await self._emit_parallel_block(
            ctx, [c.key for c in configs], "start", parallel_block_id
        )
        
        # Execute all agents in parallel
        async def run_one(
            config: "AgentConfig",
        ) -> tuple[str, ToolResult]:
            """Run single agent and return (name, result)."""
            branch_id = parallel_ctx.create_branch(config.key)
            block_id = generate_id("blk")
            
            try:
                # Emit individual agent start
                await self._emit_subagent_block(
                    ctx, config, "start", block_id, branch=branch_id
                )
                
                # 根据 create_invocation 决定执行模式
                if config.create_invocation:
                    result = await self._execute_delegated(config, ctx)
                else:
                    result = await self._execute_embedded(config, ctx)
                
                # Emit individual agent end
                await self._emit_subagent_block(
                    ctx, config, "end", block_id, branch=branch_id
                )
                
                parallel_ctx.mark_completed(config.key, result)
                return (config.key, result)
                
            except Exception as e:
                error_msg = str(e)
                parallel_ctx.mark_failed(config.key, error_msg)
                await self._emit_subagent_block(
                    ctx, config, "error", block_id, branch=branch_id
                )
                return (
                    config.key,
                    ToolResult.error(f"Delegation failed: {error_msg}"),
                )
        
        # Run all agents in parallel using asyncio.gather
        tasks = [run_one(config) for config in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Emit parallel end block
        await self._emit_parallel_block(
            ctx, [c.key for c in configs], "end", parallel_block_id
        )
        
        # Combine results
        combined_output = []
        combined_data = {}
        all_success = True
        
        for item in results:
            if isinstance(item, Exception):
                all_success = False
                combined_output.append(f"Error: {str(item)}")
            elif isinstance(item, tuple):
                name, result = item
                combined_data[name] = {"output": result.output}
                if result.is_error:
                    all_success = False
                combined_output.append(f"[{name}] {result.output}")
        
        return ToolResult(output="\n\n".join(combined_output))
    
    def _get_merged_middleware(
        self,
        config: "AgentConfig",
        ctx: ToolContext,
    ) -> "MiddlewareChain | None":
        """Get merged middleware for sub-agent execution.
        
        Merges caller's inheritable middlewares with sub-agent's own middlewares.
        
        Args:
            config: Sub-agent config
            ctx: Tool context containing caller's middleware
            
        Returns:
            Merged MiddlewareChain or None
        """
        caller_middleware = ctx.middleware
        
        # Get sub-agent's middleware (if agent is an instance with middleware)
        sub_agent = config.agent
        sub_middleware = getattr(sub_agent, 'middleware', None)
        
        # Merge: caller's inheritable + sub-agent's own
        if caller_middleware:
            return caller_middleware.merge(sub_middleware)
        elif sub_middleware:
            return sub_middleware
        
        return None
    
    async def _execute_embedded(
        self,
        config: "AgentConfig",
        ctx: ToolContext,
        task_context: str | None = None,
        artifact_refs: list[dict[str, str]] | None = None,
    ) -> ToolResult:
        """Execute in embedded mode (inline, same invocation).
        
        Embedded 模式特点：
        - 不创建新 invocation
        - BlockEvent 透传到父 agent 的 queue
        - ActionEvent 被收集，用于获取 sub-agent 结果
        - 客户端可以实时看到 sub-agent 的执行过程
        
        消息记录配置：
        - config.record_messages=False → SubAgent 不记录消息
        - config.message_namespace → 消息写入独立命名空间（隔离）
        """
        from ...core.types.action import ActionEvent, ActionType
        from ...core.context import _emit_queue_var
        
        start_time = datetime.now()
        
        # Get agent instance
        agent = config.agent
        if agent is None:
            return ToolResult.error(f"Agent '{config.key}' not found")
        
        # Configure message recording for sub-agent
        self._configure_subagent_messages(agent, config, ctx)
        
        # Build input message
        input_message = self._build_input_message(task_context, artifact_refs)
        
        logger.info(f"Starting sub-agent '{config.key}' in embedded mode")
        logger.info(f"Input: {input_message[:300]}...")
        
        # Capture parent queue BEFORE sub-agent sets its own
        # This is critical - sub-agent's run() will set ContextVar to its own queue
        try:
            parent_queue = _emit_queue_var.get()
        except LookupError:
            parent_queue = None
        
        async def forward_to_parent(event):
            """Forward event directly to parent queue, bypassing ContextVar."""
            if parent_queue is not None:
                await parent_queue.put(event)
                # Yield control so event can be processed
                import asyncio
                await asyncio.sleep(0)
        
        # Get timeout from config (default 5 min)
        timeout = getattr(config, 'timeout', 300.0)
        
        try:
            # 消费事件流：BlockEvent 转发，ActionEvent 收集
            # 使用 _force_own_queue=True 让 sub-agent 创建自己的 queue
            # 实现活跃刷新超时：收到事件时重置超时
            import asyncio
            
            async def iter_with_activity_timeout():
                """Iterate with activity-based timeout refresh."""
                # Use list as mutable container for last_activity
                state = {"last_activity": asyncio.get_event_loop().time()}
                
                async def check_timeout():
                    while True:
                        await asyncio.sleep(1.0)  # Check every second
                        if asyncio.get_event_loop().time() - state["last_activity"] > timeout:
                            raise asyncio.TimeoutError(f"Sub-agent timed out after {timeout}s of inactivity")
                
                timeout_task = asyncio.create_task(check_timeout())
                
                try:
                    async for event in agent.run(input_message, _force_own_queue=True):
                        state["last_activity"] = asyncio.get_event_loop().time()
                        yield event
                finally:
                    timeout_task.cancel()
                    try:
                        await timeout_task
                    except asyncio.CancelledError:
                        pass
            
            async for event in iter_with_activity_timeout():
                if isinstance(event, ActionEvent):
                    # 非 internal 的 ActionEvent 转发
                    if not event.internal:
                        await forward_to_parent(event)
                else:
                    # 转发 BlockEvent 给 parent（直接往 parent queue 发，不用 ctx.emit）
                    await forward_to_parent(event)
            
            logger.info(f"Sub-agent '{config.key}' completed")
        
        except Exception as e:
            logger.error(f"Sub-agent execution failed: {e}")
            return ToolResult.error(f"Sub-agent '{config.key}' failed: {str(e)}")
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # 从 agent.action_collector 获取结果（比从事件流收集更可靠）
        result_data: dict[str, Any] | None = None
        if agent.action_collector:
            result_data = agent.action_collector.get_result()
        
        # 构建结果 - 直接返回 result_data，让调用方自己处理格式
        if result_data:
            import json
            output_text = json.dumps(result_data, ensure_ascii=False, indent=2)
        else:
            output_text = f"Sub-agent '{config.key}' completed (no result data)"
        
        return ToolResult(output=output_text)
    
    def _configure_subagent_messages(
        self,
        agent: Any,
        config: "AgentConfig",
        ctx: ToolContext,
    ) -> None:
        """Configure sub-agent's message recording based on config.
        
        消息记录策略（由 return_to_parent 派生）：
        - record_messages=False → 禁用消息保存
        - record_messages=True → 保存到独立 namespace（agent_key:call_id）
        
        每次委派调用使用 call_id 保证对话独立。
        """
        if not config.record_messages:
            # 禁用消息保存
            agent._disable_message_save = True
            if hasattr(agent, '_message_namespace'):
                delattr(agent, '_message_namespace')
        else:
            # 保存到独立 namespace
            agent._message_namespace = f"{config.key}:{ctx.call_id}"
            agent._disable_message_save = False
    
    def _build_input_message(
        self,
        task_context: str | None = None,
        artifact_refs: list[dict[str, str]] | None = None,
    ) -> str:
        """构建输入消息.
        
        Args:
            task_context: 任务上下文
            artifact_refs: 相关资料引用
        """
        parts = []
        
        # 任务上下文
        if task_context:
            parts.append(f"任务背景：\n{task_context}")
        
        # 相关资料
        if artifact_refs:
            refs_text = "\n".join([
                f"- [{r.get('id', '')}] {r.get('summary', '')[:100]}"
                for r in artifact_refs
            ])
            parts.append(f"可用资料（使用 read_artifact 工具获取完整内容）：\n{refs_text}")
        
        return "\n\n".join(parts) if parts else "请执行任务"
    
    def _extract_text_from_event(self, event: Any) -> str | None:
        """从 agent event 中提取文本."""
        # BlockEvent with text content
        if hasattr(event, 'kind'):
            kind = event.kind.value if hasattr(event.kind, 'value') else event.kind
            if kind == "text" and hasattr(event, 'data') and event.data:
                return event.data.get('content', '')
        
        # Direct text delta
        if hasattr(event, 'text_delta'):
            return event.text_delta
        
        return None
    
    def _extract_data_from_event(self, event: Any) -> dict[str, Any] | None:
        """从 agent event 中提取结构化数据."""
        # ARTIFACT block
        if hasattr(event, 'kind'):
            kind = event.kind.value if hasattr(event.kind, 'value') else event.kind
            if kind == "artifact" and hasattr(event, 'data') and event.data:
                return {
                    "artifact_id": event.data.get('artifact_id'),
                    "url": event.data.get('url'),
                }
        
        # Tool result with metadata
        if hasattr(event, 'metadata') and event.metadata:
            if 'artifact_id' in event.metadata:
                return {
                    "artifact_id": event.metadata.get('artifact_id'),
                    "url": event.metadata.get('url'),
                }
        
        return None
    
    async def _emit_subagent_progress(
        self,
        ctx: ToolContext,
        config: "AgentConfig",
        event: Any,
    ) -> None:
        """发送 sub-agent 进度事件（transient，不持久化）."""
        # 直接转发 event，但标记为 sub-agent 的
        if hasattr(event, 'to_dict'):
            # 已经是 BlockEvent，直接转发
            await self.emit(event)
    
    async def _execute_delegated(
        self,
        config: "AgentConfig",
        ctx: ToolContext,
        task_context: str | None = None,
        artifact_refs: list[dict[str, str]] | None = None,
    ) -> ToolResult:
        """Execute in delegated mode (new invocation, user can interact)."""
        child_inv_id = generate_id("inv")
        
        # Get merged middleware for sub-agent
        merged_middleware = self._get_merged_middleware(config, ctx)
        
        # Create control frame
        frame = ControlFrame(
            agent_id=config.key,
            invocation_id=child_inv_id,
            parent_invocation_id=ctx.invocation_id,
        )
        
        # Note: Real implementation would:
        # 1. Push frame to session.control_stack
        # 2. Create child InvocationContext with merged_middleware
        # 3. Inject yield_result tool
        # 4. Start agent execution
        # 5. Return - user continues with sub-agent
        
        result = SubAgentResult(
            output=f"[DELEGATED] Control transferred to {config.key}. User can interact directly.",
            status="completed",
            metadata=SubAgentMetadata(
                child_invocation_id=child_inv_id,
                agent_name=config.key,
                agent_type="react",
            ),
        )
        
        return ToolResult(output=result.output)
    
    async def _emit_subagent_block(
        self,
        ctx: ToolContext,
        config: "AgentConfig",
        stage: str,
        block_id: str,
        branch: str | None = None,
    ) -> None:
        """Emit SUB_AGENT block."""
        block = BlockEvent(
            block_id=block_id,
            kind=BlockKind.SUB_AGENT,
            op=BlockOp.APPLY if stage == "start" else BlockOp.PATCH,
            data={
                "agent": config.key,
                "mode": config.mode,
                "stage": stage,
                "branch": branch,
            },
            session_id=ctx.session_id,
            invocation_id=ctx.invocation_id,
        )
        
        await self.emit(block)
    
    async def _emit_parallel_block(
        self,
        ctx: ToolContext,
        agents: list[str],
        stage: str,
        block_id: str,
    ) -> None:
        """Emit PARALLEL block for parallel execution."""
        block = BlockEvent(
            block_id=block_id,
            kind=BlockKind.SUB_AGENT,  # Use SUB_AGENT with parallel flag
            op=BlockOp.APPLY if stage == "start" else BlockOp.PATCH,
            data={
                "parallel": True,
                "agents": agents,
                "stage": stage,
            },
            session_id=ctx.session_id,
            invocation_id=ctx.invocation_id,
        )
        
        await self.emit(block)


__all__ = ["DelegateTool"]
