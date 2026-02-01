"""Context and message building helpers for ReactAgent."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..core.logging import react_logger as logger
from ..context_providers import AgentContext
from ..llm import LLMMessage

if TYPE_CHECKING:
    from ..core.context import InvocationContext
    from ..core.types import PromptInput
    from ..context_providers import ContextProvider
    from ..middleware import MiddlewareChain
    from ..core.types.tool import BaseTool


async def fetch_agent_context(
    ctx: "InvocationContext",
    input: "PromptInput",
    context_providers: list["ContextProvider"],
    direct_tools: list["BaseTool"],
    delegate_tool_class: type | None,
    middleware_chain: "MiddlewareChain | None",
) -> AgentContext:
    """Fetch context from all providers and merge with direct tools.
    
    Process:
    1. Fetch from all providers and merge
    2. Add direct tools (from create())
    3. If providers returned subagents, create DelegateTool
    
    Args:
        ctx: InvocationContext
        input: User prompt input
        context_providers: List of context providers
        direct_tools: Direct tools from create()
        delegate_tool_class: Custom DelegateTool class
        middleware_chain: Middleware chain for DelegateTool
        
    Returns:
        Merged AgentContext with all tools
    """
    from ..tool.builtin import DelegateTool
    from ..backends.subagent import ListSubAgentBackend
    
    # Set input on context for providers to access
    ctx.input = input
    
    # Fetch from all context_providers
    outputs: list[AgentContext] = []
    for provider in context_providers:
        try:
            output = await provider.fetch(ctx)
            outputs.append(output)
        except Exception as e:
            logger.warning(f"Provider {provider.name} fetch failed: {e}")
    
    # Merge all provider outputs
    merged = AgentContext.merge(outputs)
    
    # Add direct tools (from create())
    all_tools = list(direct_tools)  # Copy direct tools
    seen_names = {t.name for t in all_tools}
    
    # Add tools from providers (deduplicate)
    for tool in merged.tools:
        if tool.name not in seen_names:
            seen_names.add(tool.name)
            all_tools.append(tool)
    
    # If providers returned subagents, create DelegateTool
    if merged.subagents:
        # Check if we already have a delegate tool
        has_delegate = any(t.name == "delegate" for t in all_tools)
        if not has_delegate:
            backend = ListSubAgentBackend(merged.subagents)
            tool_cls = delegate_tool_class or DelegateTool
            delegate_tool = tool_cls(backend, middleware=middleware_chain)
            all_tools.append(delegate_tool)
    
    # Return merged context with combined tools
    return AgentContext(
        system_content=merged.system_content,
        user_content=merged.user_content,
        tools=all_tools,
        messages=merged.messages,
        subagents=merged.subagents,
        skills=merged.skills,
    )


def _parse_content(content):
    """Parse content, handling stringified JSON."""
    if isinstance(content, str):
        # Try to parse if it looks like JSON array
        if content.startswith("["):
            try:
                import json
                return json.loads(content)
            except json.JSONDecodeError:
                pass
    return content


def fix_incomplete_tool_calls(messages: list[dict]) -> list[dict]:
    """Fix incomplete tool_use/tool_result pairs in history.
    
    If an assistant message has tool_use blocks without corresponding
    tool_result messages, add placeholder tool_result messages.
    
    This handles cases where execution was interrupted between
    saving assistant message and saving tool results.
    
    Supports both formats:
    - OpenAI format: assistant message with tool_calls field
    - Claude format: assistant message with content containing tool_use blocks
    
    Args:
        messages: List of message dicts from history
        
    Returns:
        Fixed message list with placeholder tool_results added
    """
    if not messages:
        return messages
    
    result = []
    i = 0
    
    while i < len(messages):
        msg = messages[i]
        result.append(msg)
        
        # Check if this is an assistant message with tool_use
        if msg.get("role") == "assistant":
            tool_use_ids = []
            
            # Format 1: OpenAI format - tool_calls as separate field
            tool_calls = msg.get("tool_calls")
            if tool_calls and isinstance(tool_calls, list):
                for tc in tool_calls:
                    if isinstance(tc, dict):
                        tool_id = tc.get("id")
                        if tool_id:
                            tool_use_ids.append(tool_id)
            
            # Format 2: Claude format - tool_use in content
            if not tool_use_ids:
                content = _parse_content(msg.get("content"))
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "tool_use":
                            tool_id = part.get("id")
                            if tool_id:
                                tool_use_ids.append(tool_id)
            
            if tool_use_ids:
                # Collect tool_result ids from following messages
                tool_result_ids = set()
                j = i + 1
                while j < len(messages):
                    next_msg = messages[j]
                    if next_msg.get("role") == "tool":
                        # Check tool_call_id or content for tool_use_id
                        tcid = next_msg.get("tool_call_id")
                        if tcid:
                            tool_result_ids.add(tcid)
                        # Also check content if it's a list with tool_result
                        nc = _parse_content(next_msg.get("content"))
                        if isinstance(nc, list):
                            for part in nc:
                                if isinstance(part, dict) and part.get("type") == "tool_result":
                                    tuid = part.get("tool_use_id")
                                    if tuid:
                                        tool_result_ids.add(tuid)
                        j += 1
                    elif next_msg.get("role") in ("user", "assistant"):
                        # Stop at next user/assistant message
                        break
                    else:
                        j += 1
                
                # Add placeholder for missing tool_results
                for tool_id in tool_use_ids:
                    if tool_id not in tool_result_ids:
                        logger.warning(
                            f"Found incomplete tool_use without tool_result: {tool_id}, adding placeholder"
                        )
                        result.append({
                            "role": "tool",
                            "content": "[执行被中断]",
                            "tool_call_id": tool_id,
                        })
        
        i += 1
    
    return result


async def build_messages(
    input: "PromptInput",
    agent_context: AgentContext,
    system_prompt: str | None,
) -> list[LLMMessage]:
    """Build message history for LLM.
    
    Uses AgentContext from providers for system content, messages, etc.
    
    Args:
        input: User prompt input
        agent_context: Merged context from providers
        system_prompt: System prompt from config (or default)
        
    Returns:
        List of LLMMessage for LLM call
    """
    messages = []
    
    # System message: config.system_prompt + agent_context.system_content
    final_system_prompt = build_system_message(
        agent_context,
        system_prompt,
        input,
    )
    messages.append(LLMMessage(role="system", content=final_system_prompt))
    
    # Historical messages from AgentContext (provided by MessageContextProvider)
    # Fix incomplete tool_use/tool_result pairs first
    history_messages = fix_incomplete_tool_calls(agent_context.messages)
    for i, msg in enumerate(history_messages):
        raw_content = msg.get("content", "")
        content = _parse_content(raw_content)
        logger.info(
            f"[build_messages] msg[{i}] role={msg.get('role')}, "
            f"raw_content_type={type(raw_content).__name__}, "
            f"raw_content_preview={str(raw_content)[:200]}, "
            f"parsed_content_type={type(content).__name__}"
        )
        messages.append(LLMMessage(
            role=msg.get("role", "user"),
            content=content,
            tool_call_id=msg.get("tool_call_id"),
        ))

    # User content prefix (from providers) + current user message
    content = input.text
    if agent_context.user_content:
        content = agent_context.user_content + "\n\n" + content
    
    if input.attachments:
        # Build multimodal content
        content_parts = [{"type": "text", "text": content}]
        for attachment in input.attachments:
            content_parts.append(attachment)
        content = content_parts

    messages.append(LLMMessage(role="user", content=content))

    return messages


def build_system_message(
    agent_context: AgentContext,
    base_system_prompt: str | None,
    input: "PromptInput | None" = None,
) -> str:
    """Build system message with agent context.
    
    Args:
        agent_context: Agent context with system_content, tools, etc.
        base_system_prompt: Base system prompt (or None for default)
        input: Prompt input for custom template variables
        
    Returns:
        Final system prompt string
    """
    from datetime import datetime
    
    # Get base prompt
    final_system_prompt = base_system_prompt or default_system_prompt(agent_context.tools)
    
    # Build template variables: datetime + custom vars from input
    now = datetime.now()
    template_vars = {
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M:%S"),
        "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # Add custom variables from PromptInput
    if input and hasattr(input, 'vars') and input.vars:
        template_vars.update(input.vars)
    
    # Format with template variables
    try:
        final_system_prompt = final_system_prompt.format(**template_vars)
    except KeyError as e:
        logger.debug(f"System prompt template variable not found: {e}")
        pass
    
    # Append system_content if available
    if agent_context.system_content:
        final_system_prompt = final_system_prompt + "\n\n" + agent_context.system_content
    
    return final_system_prompt


def default_system_prompt(tools: list["BaseTool"]) -> str:
    """Generate default system prompt with tool descriptions.
    
    Args:
        tools: List of available tools
        
    Returns:
        Default system prompt string
    """
    tool_list = []
    for tool in tools:
        info = tool.get_info()
        tool_list.append(f"- {info.name}: {info.description}")

    tools_desc = "\n".join(tool_list) if tool_list else "No tools available."

    return f"""You are a helpful AI assistant with access to tools.

Available tools:
{tools_desc}

When you need to use a tool, make a tool call. After receiving the tool result, continue reasoning or provide your final response.

Think step by step and use tools when necessary to complete the user's request."""
