"""Tool execution helpers for ReactAgent."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ..core.logging import react_logger as logger
from ..core.event_bus import Events
from ..core.types.block import BlockEvent, BlockKind, BlockOp
from ..core.types import (
    ToolContext,
    ToolResult,
    ToolInvocation,
    ToolInvocationState,
)
from ..core.signals import SuspendSignal
from ..llm import LLMMessage
from ..middleware import HookAction

if TYPE_CHECKING:
    from .agent import ReactAgent
    from ..core.types.tool import BaseTool


def get_tool(agent: "ReactAgent", tool_name: str) -> "BaseTool | None":
    """Get tool by name from agent context.
    
    Args:
        agent: ReactAgent instance
        tool_name: Name of the tool to find
        
    Returns:
        Tool instance or None if not found
    """
    if agent._agent_context:
        for tool in agent._agent_context.tools:
            if tool.name == tool_name:
                return tool
    return None


async def _complete_tool_invocation(
    agent: "ReactAgent",
    invocation: ToolInvocation,
    result: ToolResult,
) -> None:
    """Complete a tool invocation.
    
    This function:
    1. Updates TOOL_USE block status (success/failed/aborted)
    2. Publishes TOOL_END event
    3. Adds result to LLM message history
    
    Args:
        agent: ReactAgent instance
        invocation: Tool invocation
        result: Tool execution result
    """
    # 1. Update invocation state if not already marked
    if not invocation.result:
        invocation.mark_result(
            result.output,
            is_error=result.is_error,
            truncated_result=result.truncated_output,
        )
    
    # 2. Map invocation state to string status for frontend
    status_map = {
        ToolInvocationState.SUCCESS: "success",
        ToolInvocationState.FAILED: "failed",
        ToolInvocationState.ABORTED: "aborted",
        ToolInvocationState.RESULT: "success",  # Backward compatibility
    }
    status = status_map.get(invocation.state, "failed")
    
    # 3. Update TOOL_USE block with final status
    # Tools can PATCH their own block during execution for UI updates.
    # Here we only update the final status.
    if invocation.block_id:
        patch_data: dict[str, Any] = {"status": status}
        if invocation.is_error:
            patch_data["error"] = result.output
        
        await agent.ctx.emit(BlockEvent(
            block_id=invocation.block_id,
            kind=BlockKind.TOOL_USE,
            op=BlockOp.PATCH,
            data=patch_data,
        ))
    
    # 5. Publish TOOL_END event (for internal subscribers: monitoring, billing, etc.)
    await agent.bus.publish(
        Events.TOOL_END,
        {
            "call_id": invocation.tool_call_id,
            "tool": invocation.tool_name,
            "result": result.output[:500],
            "is_error": invocation.is_error,
            "status": status,
            "duration_ms": invocation.duration_ms,
        },
    )
    
    # 6. Add to message history (for LLM, use truncated for context window)
    agent._message_history.append(
        LLMMessage(
            role="tool",
            content=invocation.result,
            tool_call_id=invocation.tool_call_id,
            name=invocation.tool_name,
            truncated_content=invocation.truncated_result,
        )
    )
    
    logger.debug(
        f"Tool completed: {invocation.tool_name} ({status})",
        extra={
            "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
            "call_id": invocation.tool_call_id,
            "status": status,
        },
    )


async def execute_tool(
    agent: "ReactAgent",
    invocation: ToolInvocation,
    checkpoint: Any | None = None,
) -> ToolResult:
    """Execute a single tool call.
    
    Supports two execution modes:
    1. Standard mode: Tool runs to completion
    2. Continuation mode: Tool can be resumed from checkpoint
    
    Args:
        agent: ReactAgent instance
        invocation: Tool invocation to execute
        checkpoint: ToolCheckpoint for resuming (continuation mode only)
        
    Returns:
        ToolResult from tool execution
    """
    # Check abort before execution
    if await agent._check_abort():
        error_msg = f"Tool {invocation.tool_name} aborted before execution"
        invocation.mark_result(
            error_msg,
            is_error=True,
            status=ToolInvocationState.ABORTED,  # Explicit ABORTED status
        )
        logger.info(
            f"Tool aborted before execution: {invocation.tool_name}",
            extra={
                "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
                "call_id": invocation.tool_call_id,
            },
        )
        return ToolResult.error(error_msg)
    
    invocation.mark_call_complete()
    
    is_resuming = checkpoint is not None

    logger.info(
        f"Executing tool: {invocation.tool_name}" + (" (resuming from checkpoint)" if is_resuming else ""),
        extra={
            "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
            "call_id": invocation.tool_call_id,
            "arguments": invocation.args,
            "is_resuming": is_resuming,
            "checkpoint_id": checkpoint.checkpoint_id if checkpoint else None,
        },
    )

    try:
        # Get tool from agent context
        tool = get_tool(agent, invocation.tool_name)
        if tool is None:
            error_msg = f"Unknown tool: {invocation.tool_name}"
            invocation.mark_result(error_msg, is_error=True)
            logger.warning(
                f"Tool not found: {invocation.tool_name}",
                extra={"invocation_id": agent._current_invocation.id if agent._current_invocation else ""},
            )
            return ToolResult.error(error_msg)

        # Set tool context on ctx for middleware/tool access
        agent.ctx.tool_call_id = invocation.tool_call_id
        agent.ctx.tool_block_id = invocation.block_id
        
        # === Middleware: on_tool_call ===
        # Skip middleware on resume - already processed on first call
        if agent.middleware and not is_resuming:
            logger.debug(
                f"Calling middleware: on_tool_call ({invocation.tool_name})",
                extra={"invocation_id": agent._current_invocation.id, "call_id": invocation.tool_call_id},
            )
            hook_result = await agent.middleware.process_tool_call(
                tool, invocation.args
            )
            if hook_result.action == HookAction.SKIP:
                logger.warning(
                    f"Tool {invocation.tool_name} skipped by middleware",
                    extra={"invocation_id": agent._current_invocation.id},
                )
                return ToolResult(
                    output=hook_result.message or "Skipped by middleware",
                    is_error=False,
                )
            elif hook_result.action == HookAction.RETRY and hook_result.modified_data:
                logger.debug(
                    f"Tool args modified by middleware",
                    extra={"invocation_id": agent._current_invocation.id},
                )
                invocation.args = hook_result.modified_data

        # Create ToolContext
        tool_ctx = ToolContext(
            session_id=agent.session.id,
            invocation_id=agent._current_invocation.id if agent._current_invocation else "",
            block_id=invocation.block_id,
            call_id=invocation.tool_call_id,
            agent=agent.config.name,
            abort_signal=agent._abort,
            update_metadata=agent._noop_update_metadata,
            middleware=agent.middleware,
        )
        
        # Emit running status before execution
        if invocation.block_id:
            await agent.ctx.emit(BlockEvent(
                block_id=invocation.block_id,
                kind=BlockKind.TOOL_USE,
                op=BlockOp.PATCH,
                data={"status": "running"},
            ))

        # Determine execution mode
        # Use continuation mode if: tool supports it AND (resuming OR tool always uses continuation)
        use_continuation = tool.supports_continuation
        timeout = tool.config.timeout
        
        # Set ctx on tool for self.emit() support
        tool._set_ctx(tool_ctx)
        
        try:
            if use_continuation:
                # Continuation mode: use execute_resumable
                if timeout is not None:
                    result = await asyncio.wait_for(
                        tool.execute_resumable(invocation.args, tool_ctx, checkpoint),
                        timeout=timeout,
                    )
                else:
                    result = await tool.execute_resumable(invocation.args, tool_ctx, checkpoint)
            else:
                # Standard mode: use execute
                if timeout is not None:
                    result = await asyncio.wait_for(
                        tool.execute(invocation.args, tool_ctx),
                        timeout=timeout,
                    )
                else:
                    result = await tool.execute(invocation.args, tool_ctx)
        finally:
            # Clear ctx after execution
            tool._set_ctx(None)
        
        # Check abort after execution
        if await agent._check_abort():
            invocation.mark_result(
                "Tool execution interrupted by user",
                is_error=True,
                status=ToolInvocationState.ABORTED,
            )
            return ToolResult.error("Tool execution interrupted by user")

        # === Middleware: on_tool_end ===
        if agent.middleware:
            logger.debug(
                f"Calling middleware: on_tool_end ({invocation.tool_name})",
                extra={"invocation_id": agent._current_invocation.id},
            )
            hook_result = await agent.middleware.process_tool_end(tool, result)
            if hook_result.action == HookAction.RETRY:
                logger.info(
                    f"Tool {invocation.tool_name} retry requested by middleware",
                    extra={"invocation_id": agent._current_invocation.id},
                )

        # Mark result - state will be auto-inferred (SUCCESS if not error, FAILED if error)
        invocation.mark_result(
            result.output,
            is_error=result.is_error,
            truncated_result=result.truncated_output,
        )
        logger.info(
            f"Tool executed: {invocation.tool_name}",
            extra={
                "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
                "call_id": invocation.tool_call_id,
                "is_error": result.is_error,
                "output_length": len(result.output) if result.output else 0,
            },
        )
        return result

    except asyncio.TimeoutError:
        timeout = tool.config.timeout if tool else None
        error_msg = f"Tool {invocation.tool_name} timed out after {timeout}s"
        invocation.mark_result(
            error_msg,
            is_error=True,
            status=ToolInvocationState.FAILED,  # Timeout is treated as FAILED
        )
        logger.error(
            f"Tool timeout: {invocation.tool_name}",
            extra={
                "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
                "timeout": timeout,
            },
        )
        return ToolResult.error(error_msg)

    except SuspendSignal:
        # HITL/Suspend signal must propagate up
        raise
    
    except Exception as e:
        import traceback
        import sys
        error_type = type(e).__name__
        error_msg = f"Tool execution error ({error_type}): {e}"
        stack_trace = traceback.format_exc()
        invocation.mark_result(
            error_msg,
            is_error=True,
            status=ToolInvocationState.FAILED,
        )
        # Log error - wrap in try to ensure we always return
        try:
            logger.error(
                f"Tool execution failed: {invocation.tool_name} - {error_type}: {e}\n{stack_trace}",
                extra={
                    "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
                    "error_type": error_type,
                    "error": str(e),
                },
            )
        except Exception as log_err:
            # If standard logging fails, print directly to stderr
            print(f"[TOOL_ERROR] Logging failed: {log_err}", file=sys.stderr)
            print(f"[TOOL_ERROR] Original error: {invocation.tool_name} - {error_type}: {e}", file=sys.stderr)
            print(stack_trace, file=sys.stderr)
        return ToolResult.error(error_msg)


async def process_tool_results(agent: "ReactAgent") -> None:
    """Execute tool calls and emit results in real-time.

    For parallel execution, uses asyncio.as_completed to emit each tool's
    result immediately upon completion (not waiting for all tools).
    
    This function directly modifies agent's internal state:
    - agent._message_history
    
    Args:
        agent: ReactAgent instance
    """
    if not agent._tool_invocations:
        return

    logger.info(
        f"Executing {len(agent._tool_invocations)} tools",
        extra={
            "invocation_id": agent._current_invocation.id,
            "mode": "parallel" if agent.config.parallel_tool_execution else "sequential",
            "tools": [inv.tool_name for inv in agent._tool_invocations],
        },
    )

    # Check abort before starting tool execution
    if await agent._check_abort():
        logger.info(
            "Tool execution aborted before starting",
            extra={"invocation_id": agent._current_invocation.id},
        )
        return
    
    # Execute tools based on configuration
    if agent.config.parallel_tool_execution:
        # Parallel execution with real-time result emission
        # Use as_completed to process and emit results as they finish
        
        # Wrapper to return both invocation and result
        async def execute_with_invocation(inv: ToolInvocation) -> tuple[ToolInvocation, ToolResult]:
            try:
                result = await execute_tool(agent, inv)
                return inv, result
            except SuspendSignal:
                # HITL signal - record placeholder before propagating
                inv.mark_result("[等待用户输入]", is_error=False)
                agent._message_history.append(
                    LLMMessage(
                        role="tool",
                        content=inv.result,
                        tool_call_id=inv.tool_call_id,
                        name=inv.tool_name,
                    )
                )
                await agent._save_tool_messages()
                raise  # Re-raise to abort all tools
        
        tasks = [
            asyncio.create_task(execute_with_invocation(inv))
            for inv in agent._tool_invocations
        ]
        
        # Process each tool as it completes
        for coro in asyncio.as_completed(tasks):
            try:
                invocation, result = await coro
                
                # Complete invocation immediately (don't wait for other tools)
                await _complete_tool_invocation(agent, invocation, result)
                
            except SuspendSignal:
                # HITL signal - placeholder already recorded in execute_with_invocation
                logger.info(
                    "Tool execution suspended (HITL) during parallel execution",
                    extra={"invocation_id": agent._current_invocation.id},
                )
                raise  # Propagate to abort all other tools
            
            except Exception as e:
                # Unexpected error in the wrapper itself (not from execute_tool)
                # This should be very rare as execute_tool catches all exceptions
                logger.error(
                    f"Unexpected error in parallel tool wrapper: {e}",
                    extra={"invocation_id": agent._current_invocation.id},
                    exc_info=True,
                )
                # Continue with other tools
        
        # Check abort after all parallel tools complete
        if await agent._check_abort():
            logger.info(
                "Tool execution aborted after parallel execution",
                extra={"invocation_id": agent._current_invocation.id},
            )
    
    else:
        # Sequential execution with abort check between tools
        for inv in agent._tool_invocations:
            # Check abort before each tool
            if await agent._check_abort():
                logger.info(
                    f"Tool execution aborted before {inv.tool_name}",
                    extra={"invocation_id": agent._current_invocation.id},
                )
                # Mark remaining as aborted
                error_result = ToolResult.error("Aborted before execution")
                inv.mark_result(
                    error_result.output,
                    is_error=True,
                    status=ToolInvocationState.ABORTED,
                )
                await _complete_tool_invocation(agent, inv, error_result)
                continue
                
            try:
                result = await execute_tool(agent, inv)
                await _complete_tool_invocation(agent, inv, result)
                
            except SuspendSignal:
                # HITL signal - record placeholder and propagate
                inv.mark_result("[等待用户输入]", is_error=False)
                agent._message_history.append(
                    LLMMessage(
                        role="tool",
                        content=inv.result,
                        tool_call_id=inv.tool_call_id,
                        name=inv.tool_name,
                    )
                )
                await agent._save_tool_messages()
                raise
            
            except Exception as e:
                logger.error(
                    f"Unexpected error in sequential tool execution: {e}",
                    extra={"invocation_id": agent._current_invocation.id},
                )
                error_result = ToolResult.error(f"Unexpected error: {str(e)}")
                inv.mark_result(
                    error_result.output,
                    is_error=True,
                    status=ToolInvocationState.FAILED,
                )
                await _complete_tool_invocation(agent, inv, error_result)
