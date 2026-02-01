"""LLM Provider adapter using aury-ai-model ModelClient."""
from __future__ import annotations

import json
from typing import Any, AsyncIterator

from ..core.logging import context_logger as logger
from .provider import (
    LLMProvider,
    LLMEvent,
    LLMMessage,
    ToolCall,
    ToolDefinition,
    Usage,
    Capabilities,
)

# Import from aury-ai-model
try:
    from aury.ai.model import (
        ModelClient,
        Message,
        StreamEvent,
        msg,
        Text,
        Evt,
        ToolCall as ModelToolCall,
        ToolSpec,
        FunctionToolSpec,
        ToolKind,
        StreamCollector,
    )
    HAS_MODEL_CLIENT = True
except ImportError:
    HAS_MODEL_CLIENT = False
    ModelClient = None  # type: ignore


class ModelClientProvider:
    """LLM Provider using aury-ai-model ModelClient.
    
    This adapter bridges the framework's LLMProvider protocol with
    the aury-ai-model ModelClient.
    
    Example:
        >>> provider = ModelClientProvider(
        ...     provider="openai",
        ...     model="gpt-4o",
        ... )
        >>> async for event in provider.complete(messages):
        ...     print(event)
    """
    
    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        capabilities: Capabilities | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ):
        """Initialize ModelClient provider.
        
        Args:
            provider: Provider name (openai, anthropic, doubao, etc.)
            model: Model name
            api_key: API key (optional, uses env if not provided)
            base_url: Base URL override
            capabilities: Model capabilities
            timeout: Request timeout in seconds (None = use provider default, typically 600s)
            **kwargs: Additional ModelClient options
        """
        if not HAS_MODEL_CLIENT:
            raise ImportError(
                "aury-ai-model is not installed. "
                "Please install it: pip install aury-ai-model[all]"
            )
        
        logger.debug(f"ModelClientProvider init, provider={provider}, model={model}")
        self._provider_name = provider
        self._model_name = model
        self._capabilities = capabilities or Capabilities()
        
        # Build ModelClient
        client_kwargs = {
            "provider": provider,
            "model": model,
        }
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url
        if timeout is not None:
            client_kwargs["timeout"] = timeout
        
        # Pass through additional options
        for key in ("default_max_tokens", "default_temperature", "default_top_p"):
            if key in kwargs:
                client_kwargs[key] = kwargs[key]
        
        self._client = ModelClient(**client_kwargs)
        self._extra_kwargs = {
            k: v for k, v in kwargs.items()
            if k not in client_kwargs
        }
        self._call_count = 0
        logger.debug(f"ModelClientProvider initialized, provider={provider}, model={model}")
    
    @property
    def provider(self) -> str:
        return self._provider_name
    
    @property
    def model(self) -> str:
        return self._model_name
    
    @property
    def call_count(self) -> int:
        """Get number of LLM calls made."""
        return self._call_count
    
    @property
    def capabilities(self) -> Capabilities:
        """Get model capabilities."""
        return self._capabilities
    
    def _convert_messages(
        self,
        messages: list[LLMMessage],
        enable_thinking: bool = False,
    ) -> list[Message]:
        """Convert LLMMessage to aury-ai-model Message.
        
        Use simple OpenAI format - let API gateway handle Claude conversion.
        
        Supports all message types from aury.ai.model:
        - system: msg.system(text)
        - user: msg.user(text, images=[])
        - assistant: msg.assistant(text, tool_calls=[])
        - tool: msg.tool(result, tool_call_id)
        """
        result = []
        
        for m in messages:
            if m.role == "system":
                result.append(msg.system(
                    m.content if isinstance(m.content, str) else str(m.content)
                ))
            
            elif m.role == "user":
                if isinstance(m.content, str):
                    result.append(msg.user(m.content))
                else:
                    # Handle multipart content (text + images)
                    text_parts = []
                    images = []
                    for part in m.content:
                        if isinstance(part, dict):
                            if part.get("type") == "text":
                                text_parts.append(part.get("text", ""))
                            elif part.get("type") == "image_url":
                                url = part.get("image_url", {}).get("url", "")
                                if url:
                                    images.append(url)
                    result.append(msg.user(
                        text=" ".join(text_parts) if text_parts else None,
                        images=images if images else None,
                    ))
            
            elif m.role == "assistant":
                # Extract text, thinking, and tool_calls from content
                # IMPORTANT: For Claude thinking mode, thinking must be included in history
                # Claude API requires assistant messages to start with thinking block when thinking is enabled
                text_content = None
                thinking_content = None
                tool_calls = None
                
                if isinstance(m.content, str):
                    text_content = m.content
                elif isinstance(m.content, list):
                    # Extract text, thinking, and tool_use from content parts
                    text_parts = []
                    thinking_parts = []
                    tool_call_list = []
                    for part in m.content:
                        if isinstance(part, dict):
                            if part.get("type") == "text":
                                text_parts.append(part.get("text", ""))
                            elif part.get("type") == "thinking":
                                # Include thinking for Claude API compatibility
                                thinking_parts.append(part.get("thinking", ""))
                            elif part.get("type") == "tool_use":
                                tool_call_list.append(ModelToolCall(
                                    id=part.get("id", ""),
                                    name=part.get("name", ""),
                                    arguments_json=json.dumps(part.get("input", {})),
                                ))
                    text_content = " ".join(text_parts) if text_parts else None
                    thinking_content = "".join(thinking_parts) if thinking_parts else None
                    tool_calls = tool_call_list if tool_call_list else None
                
                result.append(msg.assistant(
                    text=text_content,
                    thinking=thinking_content,
                    tool_calls=tool_calls,
                ))
            
            elif m.role == "tool":
                # Tool result message
                # Handle both string content (OpenAI) and list content (Anthropic)
                tool_call_id = m.tool_call_id
                tool_content = None
                
                if isinstance(m.content, str):
                    tool_content = m.content
                elif isinstance(m.content, list) and len(m.content) > 0:
                    # Anthropic format: [{'type': 'tool_result', 'tool_use_id': '...', 'content': '...'}]
                    first_item = m.content[0]
                    if isinstance(first_item, dict):
                        tool_content = first_item.get("content", "")
                        # Also extract tool_call_id if not already set
                        if not tool_call_id:
                            tool_call_id = first_item.get("tool_use_id") or first_item.get("tool_call_id")
                
                if tool_call_id and tool_content is not None:
                    result.append(msg.tool(
                        result=tool_content,
                        tool_call_id=tool_call_id,
                    ))
        
        return result
    
    def _convert_tools(
        self,
        tools: list[ToolDefinition] | None,
    ) -> list[ToolSpec] | None:
        """Convert ToolDefinition to aury-ai-model ToolSpec."""
        if not tools:
            return None
        
        return [
            ToolSpec(
                kind=ToolKind.function,
                function=FunctionToolSpec(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.input_schema,
                ),
            )
            for tool in tools
        ]
    
    def _convert_stream_event(self, event: StreamEvent) -> LLMEvent | None:
        """Convert aury-ai-model StreamEvent to LLMEvent."""
        match event.type:
            case Evt.content:
                return LLMEvent(type="content", delta=event.delta)
            
            case Evt.thinking:
                return LLMEvent(type="thinking", delta=event.delta)
            
            case Evt.thinking_completed:
                return LLMEvent(type="thinking_completed")
            
            case Evt.tool_call_start:
                if event.tool_call:
                    return LLMEvent(
                        type="tool_call_start",
                        tool_call=ToolCall(
                            id=event.tool_call.id,
                            name=event.tool_call.name,
                            arguments="",  # Empty at start
                        ),
                    )
            
            case Evt.tool_call_delta:
                if event.tool_call_delta:
                    return LLMEvent(
                        type="tool_call_delta",
                        tool_call_delta=event.tool_call_delta,
                    )
            
            case Evt.tool_call_progress:
                if event.tool_call_progress:
                    return LLMEvent(
                        type="tool_call_progress",
                        tool_call_progress=event.tool_call_progress,
                    )
            
            case Evt.tool_call:
                if event.tool_call:
                    return LLMEvent(
                        type="tool_call",
                        tool_call=ToolCall(
                            id=event.tool_call.id,
                            name=event.tool_call.name,
                            arguments=event.tool_call.arguments_json,
                        ),
                    )
            
            case Evt.usage:
                if event.usage:
                    return LLMEvent(
                        type="usage",
                        usage=Usage(
                            input_tokens=event.usage.input_tokens,
                            output_tokens=event.usage.output_tokens,
                            cache_read_tokens=getattr(event.usage, 'cache_read_tokens', 0),
                            cache_write_tokens=getattr(event.usage, 'cache_write_tokens', 0),
                            reasoning_tokens=getattr(event.usage, 'reasoning_tokens', 0),
                        ),
                    )
            
            case Evt.completed:
                return LLMEvent(type="completed", finish_reason="end_turn")
            
            case Evt.error:
                return LLMEvent(type="error", error=event.error)
        
        return None
    
    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        enable_thinking: bool = False,
        reasoning_effort: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMEvent]:
        """Generate completion with streaming.
        
        Streaming is enabled by default - this method uses ModelClient.astream()
        which always streams responses incrementally.
        
        Args:
            messages: Conversation messages
            tools: Available tools
            enable_thinking: Whether to request thinking output
            reasoning_effort: Reasoning effort level ("low", "medium", "high", "max", "auto")
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Yields:
            LLMEvent: Streaming events (content, thinking, tool_call, usage, completed, error)
        """
        # Convert messages and tools
        model_messages = self._convert_messages(messages, enable_thinking=enable_thinking)
        model_tools = self._convert_tools(tools)
        
        # Merge kwargs
        call_kwargs = {**self._extra_kwargs, **kwargs}
        if model_tools:
            call_kwargs["tools"] = model_tools
        
        # Add thinking configuration (for models that support it)
        if enable_thinking:
            call_kwargs["return_thinking"] = True
            if reasoning_effort:
                call_kwargs["reasoning_effort"] = reasoning_effort
        
        # Increment call count
        self._call_count += 1
        
        # Remove stream from kwargs if present (astream always streams, doesn't accept stream param)
        call_kwargs.pop('stream', None)
        
        # Ensure usage events are yielded (for statistics tracking)
        # This ensures usage events are included in the stream
        yield_usage_event = call_kwargs.pop('yield_usage_event', True)
        
        # Stream from ModelClient with retry support
        # astream() always streams incrementally - events arrive as they're generated
        async for event in self._client.with_retry(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
        ).astream(
            model_messages,
            yield_usage_event=yield_usage_event,
            **call_kwargs
        ):
            converted = self._convert_stream_event(event)
            if converted:
                yield converted


def create_provider(
    provider: str,
    model: str,
    timeout: float | None = None,
    **kwargs: Any,
) -> LLMProvider:
    """Create an LLM provider.
    
    Args:
        provider: Provider name (openai, anthropic, doubao, etc.)
        model: Model name
        timeout: Request timeout in seconds (None = use provider default)
        **kwargs: Additional options
    
    Returns:
        LLMProvider instance
    """
    return ModelClientProvider(provider=provider, model=model, timeout=timeout, **kwargs)
