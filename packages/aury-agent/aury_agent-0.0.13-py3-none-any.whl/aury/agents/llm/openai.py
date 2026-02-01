"""OpenAI LLM Provider - Direct OpenAI SDK integration without aury-ai-model dependency."""
from __future__ import annotations

import json
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from .provider import (
    LLMEvent,
    LLMMessage,
    LLMProvider,
    ToolCall,
    ToolDefinition,
    Usage,
)


class OpenAIProvider:
    """OpenAI LLM Provider using official SDK.
    
    Supports:
    - OpenAI models (gpt-4, gpt-3.5-turbo, etc.)
    - Compatible services (OpenRouter, OneAPI, etc.)
    - Streaming tool calls with new events
    
    Example:
        provider = OpenAIProvider(
            api_key="sk-...",
            model="gpt-4-turbo",
        )
        
        # For OpenRouter:
        provider = OpenAIProvider(
            api_key="sk-or-...",
            base_url="https://openrouter.ai/api/v1",
            model="anthropic/claude-sonnet-4",
        )
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo",
        base_url: str | None = None,
        organization: str | None = None,
        **kwargs: Any,
    ):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name
            base_url: Optional base URL (for OpenRouter, etc.)
            organization: Optional organization ID
            **kwargs: Additional client kwargs
        """
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            organization=organization,
            **kwargs,
        )
        self._model = model
        self._base_url = base_url
    
    @property
    def provider(self) -> str:
        """Provider name."""
        return "openai"
    
    @property
    def model(self) -> str:
        """Model name."""
        return self._model
    
    def _convert_messages(
        self,
        messages: list[LLMMessage],
    ) -> list[dict[str, Any]]:
        """Convert LLMMessage to OpenAI format."""
        result = []
        for msg in messages:
            item: dict[str, Any] = {"role": msg.role}
            
            # Tool message
            if msg.role == "tool":
                item["content"] = str(msg.content)
                if msg.tool_call_id:
                    item["tool_call_id"] = msg.tool_call_id
                result.append(item)
                continue
            
            # Other messages
            item["content"] = msg.content
            result.append(item)
        
        return result
    
    def _convert_tools(
        self,
        tools: list[ToolDefinition],
    ) -> list[dict[str, Any]]:
        """Convert ToolDefinition to OpenAI format."""
        return [tool.to_openai() for tool in tools]
    
    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMEvent]:
        """Stream completion from OpenAI.
        
        Args:
            messages: Message history
            tools: Available tools
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Yields:
            LLMEvent objects
        """
        # Build request payload
        converted_msgs = self._convert_messages(messages)
        print(f"[DEBUG OpenAIProvider] Sending {len(converted_msgs)} messages to {self._model}")
        for i, msg in enumerate(converted_msgs):
            print(f"[DEBUG]   Message {i}: role={msg.get('role')}, content={str(msg.get('content'))[:100]}")
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": converted_msgs,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = self._convert_tools(tools)
        
        # Add optional parameters
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "stop" in kwargs:
            payload["stop"] = kwargs["stop"]
        if "seed" in kwargs:
            payload["seed"] = kwargs["seed"]
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]
        
        # Extended thinking support (OpenAI o-series)
        if kwargs.get("reasoning_effort"):
            payload["reasoning_effort"] = kwargs["reasoning_effort"]
        
        try:
            # Create streaming completion
            try:
                stream = await self._client.chat.completions.create(**payload)
            except Exception:
                # Fallback: remove stream_options if not supported
                payload.pop("stream_options", None)
                stream = await self._client.chat.completions.create(**payload)
            
            # Track partial tool calls
            partial_tools: dict[str, dict] = {}
            notified_tools: set[str] = set()
            last_progress: dict[str, int] = {}
            last_tid: str | None = None
            usage_emitted = False
            
            # Process stream
            async for chunk in stream:
                # Usage (final chunk)
                u = getattr(chunk, "usage", None)
                if u is not None and not usage_emitted:
                    rt = 0
                    try:
                        details = getattr(u, "completion_tokens_details", None)
                        if details:
                            rt = getattr(details, "reasoning_tokens", 0) or 0
                    except Exception:
                        pass
                    
                    yield LLMEvent(
                        type="usage",
                        usage=Usage(
                            input_tokens=getattr(u, "prompt_tokens", 0) or 0,
                            output_tokens=getattr(u, "completion_tokens", 0) or 0,
                            reasoning_tokens=rt,
                            cache_read_tokens=0,
                            cache_write_tokens=0,
                        ),
                    )
                    usage_emitted = True
                
                # Check for choices
                if not getattr(chunk, "choices", None):
                    continue
                
                ch = getattr(chunk.choices[0], "delta", None)
                if ch is None:
                    continue
                
                # Extended thinking (DeepSeek R1, OpenAI o-series)
                reasoning_delta = getattr(ch, "reasoning_content", None)
                if reasoning_delta:
                    yield LLMEvent(type="thinking", delta=reasoning_delta)
                
                # Content
                if getattr(ch, "content", None):
                    yield LLMEvent(type="content", delta=ch.content)
                
                # Tool calls (streaming)
                if getattr(ch, "tool_calls", None):
                    for tc in ch.tool_calls:
                        tid = getattr(tc, "id", None) or last_tid or "_last"
                        if getattr(tc, "id", None):
                            last_tid = tid
                        
                        # ⭐ 1. tool_call_start (first notification)
                        if tid not in notified_tools:
                            fn = getattr(tc, "function", None)
                            tool_name = getattr(fn, "name", None) if fn else None
                            
                            if tool_name:
                                yield LLMEvent(
                                    type="tool_call_start",
                                    tool_call=ToolCall(
                                        id=tid,
                                        name=tool_name,
                                        arguments="",
                                    ),
                                )
                                notified_tools.add(tid)
                                last_progress[tid] = 0
                        
                        # Accumulate tool call data
                        entry = partial_tools.setdefault(
                            tid,
                            {"id": tid, "name": "", "arguments": ""},
                        )
                        
                        fn = getattr(tc, "function", None)
                        if fn is not None:
                            # Accumulate name
                            if getattr(fn, "name", None):
                                entry["name"] += fn.name
                            
                            # Accumulate arguments
                            args_delta = getattr(fn, "arguments", None)
                            if args_delta is not None:
                                # ⭐ 2. tool_call_delta (argument increments)
                                if args_delta:  # Only emit non-empty deltas
                                    yield LLMEvent(
                                        type="tool_call_delta",
                                        tool_call_delta={
                                            "call_id": tid,
                                            "arguments_delta": args_delta,
                                        },
                                    )
                                
                                entry["arguments"] += args_delta
                                
                                # ⭐ 3. tool_call_progress (every 1KB)
                                current_size = len(entry["arguments"])
                                prev_size = last_progress.get(tid, 0)
                                
                                if current_size - prev_size >= 1024:
                                    yield LLMEvent(
                                        type="tool_call_progress",
                                        tool_call_progress={
                                            "call_id": tid,
                                            "bytes_received": current_size,
                                            "last_delta_size": current_size - prev_size,
                                        },
                                    )
                                    last_progress[tid] = current_size
            
            # ⭐ 4. tool_call (complete tool calls)
            for _, v in partial_tools.items():
                # Normalize tool call
                tool_call = ToolCall(
                    id=v["id"],
                    name=v["name"],
                    arguments=v["arguments"],
                )
                yield LLMEvent(type="tool_call", tool_call=tool_call)
            
            # Completion
            yield LLMEvent(type="completed", finish_reason="end_turn")
        
        except Exception as e:
            yield LLMEvent(type="error", error=str(e))


__all__ = ["OpenAIProvider"]
