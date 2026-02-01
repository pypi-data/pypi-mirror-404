"""State persistence helpers for ReactAgent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .agent import ReactAgent
    from ..core.types import PromptInput


def save_messages_to_state(agent: "ReactAgent") -> None:
    """Save execution state for recovery.
    
    This saves to state.execution namespace:
    - step: current step number
    - message_ids: references to raw messages (if using RawMessageMiddleware)
    - For legacy/fallback: message_history as serialized data
    
    Note: With RawMessageMiddleware, message_ids are automatically populated
    by the middleware. This method saves additional execution state.
    
    Args:
        agent: ReactAgent instance
    """
    if not agent._state:
        return
    
    # Save step to execution namespace
    agent._state.execution["step"] = agent._current_step
    
    # Save invocation_id for recovery context
    if agent._current_invocation:
        agent._state.execution["invocation_id"] = agent._current_invocation.id
    
    # Fallback: if message_ids not populated by middleware, save full history
    # This ensures backward compatibility when RawMessageMiddleware is not used
    if "message_ids" not in agent._state.execution:
        messages_data = []
        for msg in agent._message_history:
            msg_dict = {"role": msg.role, "content": msg.content}
            if hasattr(msg, "tool_call_id") and msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            messages_data.append(msg_dict)
        agent._state.execution["message_history"] = messages_data


def clear_messages_from_state(agent: "ReactAgent") -> None:
    """Clear execution state after invocation completes.
    
    Called when invocation completes normally. Historical messages
    are already persisted (truncated) via MessageStore.
    
    Args:
        agent: ReactAgent instance
    """
    if not agent._state:
        return
    
    # Clear execution namespace
    agent._state.execution.clear()


async def trigger_message_save(agent: "ReactAgent", message: dict) -> dict | None:
    """Trigger on_message_save hook via middleware.
    
    Message persistence is handled by MessageBackendMiddleware.
    Agent only triggers the hook, doesn't save directly.
    
    Args:
        agent: ReactAgent instance
        message: Message dict with role, content, etc.
        
    Returns:
        Modified message or None if blocked
    """
    # Check if message saving is disabled (e.g., for sub-agents with record_messages=False)
    if getattr(agent, '_disable_message_save', False):
        return message
    
    if not agent.middleware:
        return message
    
    return await agent.middleware.process_message_save(message)


async def save_user_message(agent: "ReactAgent", input: "PromptInput") -> None:
    """Trigger save for user message.
    
    Args:
        agent: ReactAgent instance
        input: User prompt input
    """
    # Build user content
    content: str | list[dict] = input.text
    if agent._agent_context and agent._agent_context.user_content:
        content = agent._agent_context.user_content + "\n\n" + input.text
    
    if input.attachments:
        content_parts: list[dict] = [{"type": "text", "text": content}]
        for attachment in input.attachments:
            content_parts.append(attachment)
        content = content_parts
    
    # Build message and trigger hook
    message = {
        "role": "user",
        "content": content,
        "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
    }
    
    await trigger_message_save(agent, message)


async def save_assistant_message(agent: "ReactAgent") -> None:
    """Trigger save for assistant message.
    
    Args:
        agent: ReactAgent instance
    """
    if not agent._text_buffer and not agent._tool_invocations and not agent._thinking_buffer:
        return
    
    # Build assistant content
    content: str | list[dict] = agent._text_buffer
    if agent._tool_invocations or agent._thinking_buffer:
        content_parts: list[dict] = []
        # Claude requires thinking block first when thinking is enabled
        if agent._thinking_buffer:
            content_parts.append({"type": "thinking", "thinking": agent._thinking_buffer})
        if agent._text_buffer:
            content_parts.append({"type": "text", "text": agent._text_buffer})
        for inv in agent._tool_invocations:
            content_parts.append({
                "type": "tool_use",
                "id": inv.tool_call_id,
                "name": inv.tool_name,
                "input": inv.args,
            })
        content = content_parts
    
    # Build message and trigger hook
    message = {
        "role": "assistant",
        "content": content,
        "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
    }
    
    await trigger_message_save(agent, message)


async def save_tool_messages(agent: "ReactAgent") -> None:
    """Trigger save for tool result messages.
    
    Args:
        agent: ReactAgent instance
    """
    for inv in agent._tool_invocations:
        if inv.result is not None:
            # Build tool result message (raw content)
            content: list[dict] = [{
                "type": "tool_result",
                "tool_use_id": inv.tool_call_id,
                "content": inv.result,
                "is_error": inv.is_error,
            }]
            
            message: dict = {
                "role": "tool",
                "content": content,
                "tool_call_id": inv.tool_call_id,
                "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
            }
            
            # Add truncated_content if different from raw
            if inv.truncated_result is not None and inv.truncated_result != inv.result:
                truncated_content: list[dict] = [{
                    "type": "tool_result",
                    "tool_use_id": inv.tool_call_id,
                    "content": inv.truncated_result,
                    "is_error": inv.is_error,
                }]
                message["truncated_content"] = truncated_content
            
            await trigger_message_save(agent, message)
