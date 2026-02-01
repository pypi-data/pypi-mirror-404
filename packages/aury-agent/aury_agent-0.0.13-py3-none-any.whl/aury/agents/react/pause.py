"""Pause and resume helpers for ReactAgent."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, AsyncIterator

from ..core.event_bus import Events
from ..core.types.block import BlockEvent, BlockKind, BlockOp
from ..core.types import (
    Invocation,
    InvocationState,
    ToolInvocationState,
)
from ..llm import LLMMessage

if TYPE_CHECKING:
    from .agent import ReactAgent


async def pause_agent(agent: "ReactAgent") -> str:
    """Pause execution and return invocation ID for later resume.

    Saves current state to the invocation for later resumption.
    
    Args:
        agent: ReactAgent instance

    Returns:
        Invocation ID for resuming
    """
    if not agent._current_invocation:
        raise RuntimeError("No active invocation to pause")

    # Mark as paused
    agent._paused = True
    agent._current_invocation.mark_paused()

    # Save state for resumption
    agent._current_invocation.agent_state = {
        "step": agent._current_step,
        "message_history": [
            {"role": m.role, "content": m.content} for m in agent._message_history
        ],
        "text_buffer": agent._text_buffer,
    }
    agent._current_invocation.step_count = agent._current_step

    # Save pending tool calls
    agent._current_invocation.pending_tool_ids = [
        inv.tool_call_id
        for inv in agent._tool_invocations
        if inv.state == ToolInvocationState.CALL
    ]

    # Persist invocation
    if agent.ctx.backends and agent.ctx.backends.invocation:
        await agent.ctx.backends.invocation.update(
            agent._current_invocation.id,
            agent._current_invocation.to_dict(),
        )

    await agent.bus.publish(
        Events.INVOCATION_PAUSE,
        {
            "invocation_id": agent._current_invocation.id,
            "step": agent._current_step,
        },
    )

    return agent._current_invocation.id


async def resume_agent_internal(agent: "ReactAgent", invocation_id: str) -> None:
    """Internal resume logic using emit.
    
    Args:
        agent: ReactAgent instance
        invocation_id: Invocation ID to resume
    """
    from .step import execute_step
    from .tools import process_tool_results
    from .persistence import save_assistant_message, save_tool_messages
    
    # Load invocation
    if not agent.ctx.backends or not agent.ctx.backends.invocation:
        raise ValueError("No invocation backend available")
    inv_data = await agent.ctx.backends.invocation.get(invocation_id)
    if not inv_data:
        raise ValueError(f"Invocation not found: {invocation_id}")

    invocation = Invocation.from_dict(inv_data)

    # Support both PAUSED and SUSPENDED (HITL) states
    if invocation.state not in (InvocationState.PAUSED, InvocationState.SUSPENDED):
        raise ValueError(f"Invocation is not paused/suspended: {invocation.state}")

    # Restore state
    agent._current_invocation = invocation
    agent._paused = False
    agent._running = True

    agent_state = invocation.agent_state or {}
    agent._current_step = agent_state.get("step", 0)
    agent._text_buffer = agent_state.get("text_buffer", "")

    # Restore message history
    agent._message_history = [
        LLMMessage(role=m["role"], content=m["content"])
        for m in agent_state.get("message_history", [])
    ]

    # Mark as running
    invocation.state = InvocationState.RUNNING

    await agent.bus.publish(
        Events.INVOCATION_RESUME,
        {
            "invocation_id": invocation_id,
            "step": agent._current_step,
        },
    )

    # Continue execution loop
    try:
        finish_reason = None

        while not await agent._check_abort() and not agent._paused:
            agent._current_step += 1

            if agent._current_step > agent.config.max_steps:
                await agent.ctx.emit(BlockEvent(
                    kind=BlockKind.ERROR,
                    op=BlockOp.APPLY,
                    data={"message": f"Max steps ({agent.config.max_steps}) exceeded"},
                ))
                break

            finish_reason = await execute_step(agent)
            
            # Save assistant message (real-time persistence)
            await save_assistant_message(agent)

            if finish_reason == "end_turn" and not agent._tool_invocations:
                break

            if agent._tool_invocations:
                await process_tool_results(agent)
                
                # Save tool messages (real-time persistence)
                await save_tool_messages(agent)
                
                agent._tool_invocations.clear()

        if not agent._paused:
            agent._current_invocation.state = InvocationState.COMPLETED
            agent._current_invocation.finished_at = __import__("datetime").datetime.now()
            
            # Clear agent_state after successful completion (save space)
            agent._current_invocation.agent_state = None
            
            # Update invocation to database
            if agent.ctx.backends and agent.ctx.backends.invocation:
                await agent.ctx.backends.invocation.update(
                    agent._current_invocation.id,
                    agent._current_invocation.to_dict(),
                )

    except Exception as e:
        agent._current_invocation.state = InvocationState.FAILED
        await agent.ctx.emit(BlockEvent(
            kind=BlockKind.ERROR,
            op=BlockOp.APPLY,
            data={"message": str(e)},
        ))
        raise

    finally:
        agent._running = False


async def resume_agent(agent: "ReactAgent", invocation_id: str) -> AsyncIterator[BlockEvent]:
    """Resume paused execution.

    Args:
        agent: ReactAgent instance
        invocation_id: ID from pause()

    Yields:
        BlockEvent streaming events
    """
    from ..core.context import _emit_queue_var
    
    queue: asyncio.Queue[BlockEvent] = asyncio.Queue()
    token = _emit_queue_var.set(queue)
    
    try:
        exec_task = asyncio.create_task(resume_agent_internal(agent, invocation_id))
        get_task: asyncio.Task | None = None
        
        # Event-driven processing - no timeout delays
        while True:
            # First drain any pending items from queue (non-blocking)
            while True:
                try:
                    block = queue.get_nowait()
                    yield block
                except asyncio.QueueEmpty:
                    break
            
            # Exit if task is done and queue is empty
            if exec_task.done() and queue.empty():
                break
            
            # Create get_task if needed
            if get_task is None or get_task.done():
                get_task = asyncio.create_task(queue.get())
            
            # Wait for EITHER: queue item OR exec_task completion
            done, _ = await asyncio.wait(
                {get_task, exec_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            if get_task in done:
                try:
                    block = get_task.result()
                    yield block
                    get_task = None
                except asyncio.CancelledError:
                    pass
        
        # Cancel pending get_task if any
        if get_task and not get_task.done():
            get_task.cancel()
            try:
                await get_task
            except asyncio.CancelledError:
                pass
        
        # Final drain after task completion
        while not queue.empty():
            try:
                block = queue.get_nowait()
                yield block
            except asyncio.QueueEmpty:
                break
        
        await exec_task
        
    finally:
        _emit_queue_var.reset(token)
