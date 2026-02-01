"""LLM step execution helpers for ReactAgent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from ..core.base import ToolInjectionMode
from ..core.logging import react_logger as logger
from ..core.event_bus import Events
from ..core.types.block import BlockEvent, BlockKind, BlockOp
from ..core.types import (
    ToolInvocation,
    ToolInvocationState,
    generate_id,
)
from ..llm import LLMMessage, ToolDefinition
from ..middleware import HookAction

if TYPE_CHECKING:
    from .agent import ReactAgent


def get_effective_tool_mode(agent: "ReactAgent") -> ToolInjectionMode:
    """Get effective tool mode (auto-detect based on model capabilities).
    
    Returns:
        FUNCTION_CALL if model supports tools, else PROMPT
    """
    # If explicitly set to PROMPT, use PROMPT
    if agent.config.tool_mode == ToolInjectionMode.PROMPT:
        return ToolInjectionMode.PROMPT
    
    # Auto-detect: if model doesn't support tools, use PROMPT
    caps = agent.llm.capabilities
    if not caps.supports_tools:
        logger.info(
            f"Model {agent.llm.model} does not support function calling, "
            "auto-switching to PROMPT mode for tools"
        )
        return ToolInjectionMode.PROMPT
    
    return ToolInjectionMode.FUNCTION_CALL


def build_tool_prompt(tools: list) -> str:
    """Build tool description for PROMPT mode injection.
    
    Args:
        tools: List of BaseTool objects
        
    Returns:
        Tool prompt string to inject into system message
    """
    if not tools:
        return ""
    
    tool_descriptions = []
    for tool in tools:
        info = tool.get_info()
        # Build parameter description
        params_desc = ""
        if info.parameters and "properties" in info.parameters:
            params = []
            properties = info.parameters.get("properties", {})
            required = info.parameters.get("required", [])
            for name, schema in properties.items():
                param_type = schema.get("type", "any")
                param_desc = schema.get("description", "")
                is_required = "required" if name in required else "optional"
                params.append(f"    - {name} ({param_type}, {is_required}): {param_desc}")
            params_desc = "\n" + "\n".join(params) if params else ""
        
        tool_descriptions.append(
            f"### {info.name}\n"
            f"{info.description}{params_desc}"
        )
    
    return f"""## Available Tools

You have access to the following tools. To use a tool, output a JSON block in this exact format:

```tool_call
{{
  "tool": "tool_name",
  "arguments": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}
```

IMPORTANT: 
- Use the exact format above with ```tool_call code block
- You can make multiple tool calls in one response
- Wait for tool results before continuing

{chr(10).join(tool_descriptions)}
"""


def parse_tool_calls_from_text(text: str) -> list[dict]:
    """Parse tool calls from LLM text output (for PROMPT mode).
    
    Looks for ```tool_call blocks in the format:
    ```tool_call
    {"tool": "name", "arguments": {...}}
    ```
    
    Args:
        text: LLM output text
        
    Returns:
        List of parsed tool calls: [{"name": str, "arguments": dict}, ...]
    """
    import re
    
    tool_calls = []
    
    # Match ```tool_call ... ``` blocks
    pattern = r"```tool_call\s*\n?(.+?)\n?```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            data = json.loads(match.strip())
            if "tool" in data:
                tool_calls.append({
                    "name": data["tool"],
                    "arguments": data.get("arguments", {}),
                })
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse tool call JSON: {e}")
            continue
    
    return tool_calls


async def execute_step(agent: "ReactAgent") -> str | None:
    """Execute a single LLM step with middleware hooks.
    
    This function directly modifies agent's internal state:
    - agent._text_buffer
    - agent._thinking_buffer
    - agent._tool_invocations
    - agent._current_text_block_id
    - agent._current_thinking_block_id
    - agent._call_id_to_tool
    - agent._tool_call_blocks
    - agent._message_history
    
    Args:
        agent: ReactAgent instance
        
    Returns:
        finish_reason from LLM
    """
    from ..core.context import emit as global_emit
    
    # Get tools from AgentContext (from providers)
    all_tools = agent._agent_context.tools if agent._agent_context else []
    
    # Determine effective tool mode (auto-detect based on capabilities)
    effective_tool_mode = get_effective_tool_mode(agent)
    
    # Get tool definitions (only for FUNCTION_CALL mode)
    tool_defs = None
    if effective_tool_mode == ToolInjectionMode.FUNCTION_CALL and all_tools:
        tool_defs = [
            ToolDefinition(
                name=t.name,
                description=t.description,
                input_schema=t.parameters,
            )
            for t in all_tools
        ]
    
    # For PROMPT mode, inject tools into system message
    if effective_tool_mode == ToolInjectionMode.PROMPT and all_tools:
        tool_prompt = build_tool_prompt(all_tools)
        # Inject into first system message
        if agent._message_history and agent._message_history[0].role == "system":
            original_content = agent._message_history[0].content
            agent._message_history[0] = LLMMessage(
                role="system",
                content=f"{original_content}\n\n{tool_prompt}",
            )

    # Reset buffers
    agent._text_buffer = ""
    agent._thinking_buffer = ""  # Buffer for non-streaming thinking
    agent._tool_invocations = []
    agent._last_usage = None  # Store usage for middleware
    
    # Reset block IDs for this step (each step gets fresh block IDs)
    agent._current_text_block_id = None
    agent._current_thinking_block_id = None
    
    # Track if thinking_completed has been emitted (to avoid duplicate)
    thinking_completed_emitted = False
    
    # Reset tool call tracking
    agent._call_id_to_tool = {}
    agent._tool_call_blocks = {}
    
    # Track accumulated arguments for streaming tool calls
    tool_call_accumulated_args: dict[str, dict[str, Any]] = {}

    # Build LLM call kwargs
    # Note: temperature, max_tokens, timeout, retries are configured on LLMProvider
    llm_kwargs: dict[str, Any] = {
        "messages": agent._message_history,
        "tools": tool_defs,  # None for PROMPT mode
    }
    
    # Get model capabilities
    caps = agent.llm.capabilities

    # Add thinking configuration (use runtime override if set)
    # Only if model supports thinking
    enable_thinking = agent._get_enable_thinking()
    reasoning_effort = agent._get_reasoning_effort()
    if enable_thinking:
        if caps.supports_thinking:
            llm_kwargs["enable_thinking"] = True
            if reasoning_effort:
                llm_kwargs["reasoning_effort"] = reasoning_effort
        else:
            logger.debug(
                f"Model {agent.llm.model} does not support thinking, "
                "enable_thinking will be ignored"
            )

    # === Middleware: on_request ===
    if agent.middleware:
        logger.info(
            "Calling middleware: on_request",
            extra={"invocation_id": agent._current_invocation.id},
        )
        llm_kwargs = await agent.middleware.process_request(llm_kwargs)
        if llm_kwargs is None:
            logger.warning(
                "LLM request cancelled by middleware",
                extra={"invocation_id": agent._current_invocation.id},
            )
            return None

    # Log message history before LLM call
    logger.info(
        f"LLM call - Step {agent._current_step}, messages: {len(agent._message_history)}, "
        f"tools: {len(tool_defs) if tool_defs else 0}, "
        f"thinking: {enable_thinking}, mode: {effective_tool_mode.value}",
        extra={"invocation_id": agent._current_invocation.id},
    )
    # Detailed message log (for debugging model issues like repeated calls)
    for i, msg in enumerate(agent._message_history):
        content_preview = str(msg.content)[:300] if msg.content else "<empty>"
        tool_call_id = getattr(msg, 'tool_call_id', None)
        logger.debug(
            f"  msg[{i}] role={msg.role}"
            f"{f', tool_call_id={tool_call_id}' if tool_call_id else ''}"
            f", content={content_preview}"
        )
    
    # Call LLM
    await agent.bus.publish(
        Events.LLM_START,
        {
            "provider": agent.llm.provider,
            "model": agent.llm.model,
            "step": agent._current_step,
            "enable_thinking": enable_thinking,
        },
    )

    finish_reason = None
    llm_response_data: dict[str, Any] = {}  # Collect response for middleware

    # Reset middleware stream state
    if agent.middleware:
        logger.debug(
            "Resetting middleware stream state",
            extra={"invocation_id": agent._current_invocation.id},
        )
        agent.middleware.reset_stream_state()

    logger.info(
        "Starting LLM stream",
        extra={"invocation_id": agent._current_invocation.id, "model": agent.llm.model},
    )
    
    # Track whether we aborted mid-stream
    aborted = False
    
    async for event in agent.llm.complete(**llm_kwargs):
        if await agent._check_abort():
            aborted = True
            break

        if event.type == "content":
            # Text content
            if event.delta:
                # === Middleware: on_text_stream ===
                stream_chunk = {"delta": event.delta}
                if agent.middleware:
                    stream_chunk = await agent.middleware.process_text_stream(
                        stream_chunk
                    )
                    if stream_chunk is None:
                        continue  # Skip this chunk

                delta = stream_chunk.get("delta", event.delta)
                agent._text_buffer += delta
                
                # Reuse or create block_id for text streaming
                if agent._current_text_block_id is None:
                    agent._current_text_block_id = generate_id("blk")
                
                await agent.ctx.emit(BlockEvent(
                    block_id=agent._current_text_block_id,
                    kind=BlockKind.TEXT,
                    op=BlockOp.DELTA,
                    data={"content": delta},
                ))

                await agent.bus.publish(
                    Events.LLM_STREAM,
                    {
                        "delta": delta,
                        "step": agent._current_step,
                    },
                )

        elif event.type == "thinking":
            # Thinking content - only emit if thinking is enabled
            stream_thinking = agent._get_stream_thinking()
            if event.delta and enable_thinking:
                # === Middleware: on_thinking_stream ===
                stream_chunk = {"delta": event.delta}
                if agent.middleware:
                    stream_chunk = await agent.middleware.process_thinking_stream(
                        stream_chunk
                    )
                    if stream_chunk is None:
                        continue  # Skip this chunk
                
                delta = stream_chunk.get("delta", event.delta)
                
                # Always accumulate to buffer (for middleware on_response)
                agent._thinking_buffer += delta
                
                if stream_thinking:
                    # Reuse or create block_id for thinking streaming
                    if agent._current_thinking_block_id is None:
                        agent._current_thinking_block_id = generate_id("blk")
                    
                    # Stream thinking in real-time
                    await agent.ctx.emit(BlockEvent(
                        block_id=agent._current_thinking_block_id,
                        kind=BlockKind.THINKING,
                        op=BlockOp.DELTA,
                        data={"content": delta},
                    ))

        elif event.type == "thinking_completed":
            # Thinking completed - emit block completed status
            # Note: thinking_completed from LLM means it finished naturally,
            # so we always use "completed" here (not aborted)
            if agent._current_thinking_block_id and not thinking_completed_emitted:
                await agent.ctx.emit(BlockEvent(
                    block_id=agent._current_thinking_block_id,
                    kind=BlockKind.THINKING,
                    op=BlockOp.PATCH,
                    data={"status": "completed"},
                ))
                thinking_completed_emitted = True

        elif event.type == "tool_call_start":
            # Tool call started (name known, arguments pending)
            if event.tool_call:
                tc = event.tool_call
                logger.debug(
                    f"Tool call start: {tc.name}",
                    extra={
                        "invocation_id": agent._current_invocation.id,
                        "call_id": tc.id,
                    },
                )
                agent._call_id_to_tool[tc.id] = tc.name
                
                # Always emit start notification (privacy-safe, no arguments)
                block_id = generate_id("blk")
                agent._tool_call_blocks[tc.id] = block_id
                
                # Get display_name from tool if available
                tool = agent._get_tool(tc.name)
                display_name = tool.display_name if tool else tc.name
                
                await agent.ctx.emit(BlockEvent(
                    block_id=block_id,
                    kind=BlockKind.TOOL_USE,
                    op=BlockOp.APPLY,
                    data={
                        "name": tc.name,
                        "display_name": display_name,
                        "call_id": tc.id,
                        "status": "pending",  # Initial status, arguments pending
                    },
                ))

        elif event.type == "tool_call_delta":
            # Tool arguments delta (streaming)
            if event.tool_call_delta:
                call_id = event.tool_call_delta.get("call_id")
                arguments_delta = event.tool_call_delta.get("arguments_delta")
                
                logger.debug(
                    f"Tool call delta received: call_id={call_id}, delta_type={type(arguments_delta).__name__}, delta={arguments_delta}",
                    extra={"invocation_id": agent._current_invocation.id},
                )
                
                if call_id and arguments_delta:
                    tool_name = agent._call_id_to_tool.get(call_id)
                    if tool_name:
                        tool = agent._get_tool(tool_name)
                        
                        # Check if tool allows streaming arguments
                        if tool and tool.config.stream_arguments:
                            # Update accumulated args for middleware context
                            if call_id not in tool_call_accumulated_args:
                                tool_call_accumulated_args[call_id] = {}
                            
                            # Handle different delta formats
                            # Some providers send dict, others send JSON string
                            if isinstance(arguments_delta, str):
                                # It's a JSON string fragment, accumulate as single "_raw" key
                                if "_raw" not in tool_call_accumulated_args[call_id]:
                                    tool_call_accumulated_args[call_id]["_raw"] = ""
                                tool_call_accumulated_args[call_id]["_raw"] += arguments_delta
                                
                                # Convert string delta to dict format for middleware
                                arguments_delta = {"_raw": arguments_delta}
                            
                            elif isinstance(arguments_delta, dict):
                                # Merge delta into accumulated (dict format)
                                for key, value in arguments_delta.items():
                                    if key in tool_call_accumulated_args[call_id]:
                                        # Concatenate strings, or replace other types
                                        if isinstance(value, str) and isinstance(tool_call_accumulated_args[call_id][key], str):
                                            tool_call_accumulated_args[call_id][key] += value
                                        else:
                                            tool_call_accumulated_args[call_id][key] = value
                                    else:
                                        tool_call_accumulated_args[call_id][key] = value
                                for key, value in arguments_delta.items():
                                    if key in tool_call_accumulated_args[call_id]:
                                        # Concatenate strings, or replace other types
                                        if isinstance(value, str) and isinstance(tool_call_accumulated_args[call_id][key], str):
                                            tool_call_accumulated_args[call_id][key] += value
                                        else:
                                            tool_call_accumulated_args[call_id][key] = value
                                    else:
                                        tool_call_accumulated_args[call_id][key] = value
                            
                            # === Middleware: on_tool_call_delta ===
                            processed_delta = arguments_delta
                            if agent.middleware:
                                accumulated_args = tool_call_accumulated_args.get(call_id, {})
                                processed_delta = await agent.middleware.process_tool_call_delta(
                                    call_id, tool_name, arguments_delta, accumulated_args
                                )
                                if processed_delta is None:
                                    continue  # Skip this delta
                            
                            block_id = agent._tool_call_blocks.get(call_id)
                            if block_id:
                                await agent.ctx.emit(BlockEvent(
                                    block_id=block_id,
                                    kind=BlockKind.TOOL_USE,
                                    op=BlockOp.DELTA,
                                    data={
                                        "call_id": call_id,
                                        "arguments_delta": processed_delta,
                                    },
                                ))

        elif event.type == "tool_call_progress":
            # Tool arguments progress (bytes received)
            if event.tool_call_progress:
                call_id = event.tool_call_progress.get("call_id")
                bytes_received = event.tool_call_progress.get("bytes_received")
                
                if call_id and bytes_received is not None:
                    block_id = agent._tool_call_blocks.get(call_id)
                    if block_id:
                        # Always emit progress (privacy-safe, no content)
                        await agent.ctx.emit(BlockEvent(
                            block_id=block_id,
                            kind=BlockKind.TOOL_USE,
                            op=BlockOp.PATCH,
                            data={
                                "call_id": call_id,
                                "bytes_received": bytes_received,
                                "status": "receiving",
                            },
                        ))

        elif event.type == "tool_call":
            # Tool call complete (arguments fully received)
            if event.tool_call:
                tc = event.tool_call
                # Strict mode: tool_call_start must have been received
                block_id = agent._tool_call_blocks[tc.id]  # Will raise KeyError if not found
                
                invocation = ToolInvocation(
                    tool_call_id=tc.id,
                    tool_name=tc.name,
                    block_id=block_id,
                    args_raw=tc.arguments,
                    state=ToolInvocationState.CALL,
                )

                # Parse arguments
                try:
                    invocation.args = json.loads(tc.arguments)
                except json.JSONDecodeError:
                    invocation.args = {}

                agent._tool_invocations.append(invocation)
                
                # Build patch data
                patch_data: dict[str, Any] = {
                    "call_id": tc.id,
                    "arguments": invocation.args,
                    "status": "ready",
                }
                
                await agent.ctx.emit(BlockEvent(
                    block_id=block_id,
                    kind=BlockKind.TOOL_USE,
                    op=BlockOp.PATCH,
                    data=patch_data,
                ))

                await agent.bus.publish(
                    Events.TOOL_START,
                    {
                        "call_id": tc.id,
                        "tool": tc.name,
                        "arguments": invocation.args,
                    },
                )

        elif event.type == "completed":
            finish_reason = event.finish_reason

        elif event.type == "usage":
            if event.usage:
                # Store usage for middleware
                agent._last_usage = {
                    "provider": agent.llm.provider,
                    "model": agent.llm.model,
                    "input_tokens": event.usage.input_tokens,
                    "output_tokens": event.usage.output_tokens,
                    "cache_read_tokens": event.usage.cache_read_tokens,
                    "cache_write_tokens": event.usage.cache_write_tokens,
                    "reasoning_tokens": event.usage.reasoning_tokens,
                }
                await agent.bus.publish(
                    Events.USAGE_RECORDED,
                    agent._last_usage,
                )

        elif event.type == "error":
            await agent.ctx.emit(BlockEvent(
                kind=BlockKind.ERROR,
                op=BlockOp.APPLY,
                data={"message": event.error or "Unknown LLM error"},
            ))

    # === Middleware: on_text_stream_end (flush buffered content) ===
    if agent.middleware:
        final_chunks = await agent.middleware.process_text_stream_end()
        for final_chunk in final_chunks:
            final_delta = final_chunk.get("delta", "")
            if final_delta:
                agent._text_buffer += final_delta
                # Emit the final text content
                if agent._current_text_block_id is None:
                    agent._current_text_block_id = generate_id("blk")
                await agent.ctx.emit(BlockEvent(
                    block_id=agent._current_text_block_id,
                    kind=BlockKind.TEXT,
                    op=BlockOp.DELTA,
                    data={"content": final_delta},
                ))
                logger.debug(
                    f"Emitted final text chunk from middleware: {len(final_delta)} chars",
                    extra={"invocation_id": agent._current_invocation.id},
                )
    
    # === Middleware: on_thinking_stream_end (flush buffered thinking) ===
    if agent.middleware:
        thinking_chunks = await agent.middleware.process_thinking_stream_end()
        for thinking_chunk in thinking_chunks:
            thinking_delta = thinking_chunk.get("delta", "")
            if thinking_delta:
                agent._thinking_buffer += thinking_delta
                # Emit the final thinking content (if streaming thinking)
                if agent.config.stream_thinking:
                    if agent._current_thinking_block_id is None:
                        agent._current_thinking_block_id = generate_id("blk")
                    await agent.ctx.emit(BlockEvent(
                        block_id=agent._current_thinking_block_id,
                        kind=BlockKind.THINKING,
                        op=BlockOp.DELTA,
                        data={"content": thinking_delta},
                    ))
                logger.debug(
                    f"Emitted final thinking chunk from middleware: {len(thinking_delta)} chars",
                    extra={"invocation_id": agent._current_invocation.id},
                )
    
    # Emit thinking block final status if streaming and not yet completed
    if agent._current_thinking_block_id and not thinking_completed_emitted:
        status = "aborted" if aborted else "completed"
        await agent.ctx.emit(BlockEvent(
            block_id=agent._current_thinking_block_id,
            kind=BlockKind.THINKING,
            op=BlockOp.PATCH,
            data={"status": status},
        ))
    
    # Emit text block final status (completed or aborted)
    if agent._current_text_block_id:
        status = "aborted" if aborted else "completed"
        await agent.ctx.emit(BlockEvent(
            block_id=agent._current_text_block_id,
            kind=BlockKind.TEXT,
            op=BlockOp.PATCH,
            data={"status": status},
        ))
    
    # If thinking was buffered, emit it now (non-streaming mode)
    if agent._thinking_buffer and not agent.config.stream_thinking:
        await agent.ctx.emit(BlockEvent(
            kind=BlockKind.THINKING,
            op=BlockOp.APPLY,
            data={"content": agent._thinking_buffer},
        ))
    
    # PROMPT mode: parse tool calls from text output
    if effective_tool_mode == ToolInjectionMode.PROMPT and agent._text_buffer:
        parsed_calls = parse_tool_calls_from_text(agent._text_buffer)
        for i, call in enumerate(parsed_calls):
            call_id = generate_id("call")
            invocation = ToolInvocation(
                tool_call_id=call_id,
                tool_name=call["name"],
                args_raw=json.dumps(call["arguments"]),
                args=call["arguments"],
                state=ToolInvocationState.CALL,
            )
            agent._tool_invocations.append(invocation)
            
            # Create block for tool call (no streaming events in PROMPT mode)
            block_id = generate_id("blk")
            agent._tool_call_blocks[call_id] = block_id
            agent._call_id_to_tool[call_id] = call["name"]
            
            await agent.ctx.emit(BlockEvent(
                block_id=block_id,
                kind=BlockKind.TOOL_USE,
                op=BlockOp.APPLY,
                data={
                    "name": call["name"],
                    "call_id": call_id,
                    "arguments": call["arguments"],
                    "status": "ready",
                    "source": "prompt",  # Indicate parsed from text
                },
            ))
            
            await agent.bus.publish(
                Events.TOOL_START,
                {
                    "call_id": call_id,
                    "tool": call["name"],
                    "arguments": call["arguments"],
                    "source": "prompt",
                },
            )
        
        if parsed_calls:
            logger.info(
                f"PROMPT mode: parsed {len(parsed_calls)} tool calls from text",
                extra={
                    "invocation_id": agent._current_invocation.id,
                    "tool_calls": [call["name"] for call in parsed_calls],
                },
            )

    # === Middleware: on_response ===
    llm_response_data = {
        "text": agent._text_buffer,
        "thinking": agent._thinking_buffer,
        "tool_calls": len(agent._tool_invocations),
        "finish_reason": finish_reason,
        "usage": agent._last_usage,  # Include usage for middleware
    }
    if agent.middleware:
        logger.debug(
            "Calling middleware: on_response",
            extra={
                "invocation_id": agent._current_invocation.id,
                "text_length": len(agent._text_buffer),
                "tool_calls": len(agent._tool_invocations),
            },
        )
        llm_response_data = await agent.middleware.process_response(
            llm_response_data
        )

    await agent.bus.publish(
        Events.LLM_END,
        {
            "step": agent._current_step,
            "finish_reason": finish_reason,
            "text_length": len(agent._text_buffer),
            "thinking_length": len(agent._thinking_buffer),
            "tool_calls": len(agent._tool_invocations),
        },
    )

    # Add assistant message to history
    # Save thinking for verification, but adapter will filter it out when sending to model
    if agent._text_buffer or agent._tool_invocations or agent._thinking_buffer:
        content_parts = []
        
        # Save thinking for verification (won't be sent to model)
        if agent._thinking_buffer:
            content_parts.append({"type": "thinking", "thinking": agent._thinking_buffer})
        
        # Add text content
        if agent._text_buffer:
            content_parts.append({"type": "text", "text": agent._text_buffer})
        
        # Add tool_use parts
        if agent._tool_invocations:
            for inv in agent._tool_invocations:
                content_parts.append({
                    "type": "tool_use",
                    "id": inv.tool_call_id,
                    "name": inv.tool_name,
                    "input": inv.args,
                })
        
        # content_parts is guaranteed non-empty due to outer if condition
        agent._message_history.append(
            LLMMessage(role="assistant", content=content_parts)
        )

    return finish_reason
