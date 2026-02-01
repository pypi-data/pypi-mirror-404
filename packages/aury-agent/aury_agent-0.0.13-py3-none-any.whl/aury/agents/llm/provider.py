"""LLM Provider protocol and events."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal, Protocol, runtime_checkable


@dataclass
class Capabilities:
    """Model capabilities.
    
    Example:
        caps = Capabilities(supports_tools=True, supports_thinking=True)
    """
    # Core
    supports_tools: bool = True
    supports_streaming: bool = True
    supports_thinking: bool = False
    
    # Multimodal
    supports_vision: bool = False
    supports_audio: bool = False
    supports_video: bool = False
    supports_files: bool = False
    
    # Context
    max_context_tokens: int = 128000
    max_output_tokens: int = 4096
    
    # Advanced
    supports_json_mode: bool = False
    supports_prefill: bool = False
    supports_caching: bool = False


@dataclass
class ToolCall:
    """Tool call from LLM."""
    id: str
    name: str
    arguments: str  # JSON string


@dataclass
class Usage:
    """Token usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0  # Thinking/reasoning tokens (for models that support extended thinking)
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.reasoning_tokens
    
    def __add__(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
        )


@dataclass
class LLMEvent:
    """LLM streaming event.
    
    Unified format for all LLM providers.
    """
    type: Literal[
        "content",           # Text content delta
        "thinking",          # Thinking content delta (some models)
        "tool_call_start",   # Tool call started (name known, arguments pending)
        "tool_call_delta",   # Tool arguments delta (streaming)
        "tool_call_progress",# Tool arguments progress (bytes received)
        "tool_call",         # Tool call complete (arguments complete)
        "usage",             # Token usage
        "completed",         # Generation complete
        "error",             # Error
    ]
    
    # content/thinking delta
    delta: str | None = None
    
    # tool_call
    tool_call: ToolCall | None = None
    tool_call_delta: dict | None = None      # {"call_id": str, "arguments_delta": str}
    tool_call_progress: dict | None = None   # {"call_id": str, "bytes_received": int, "last_delta_size": int}
    
    # usage/completed
    usage: Usage | None = None
    finish_reason: str | None = None
    
    # error
    error: str | None = None


@dataclass
class ToolDefinition:
    """Tool definition for LLM."""
    name: str
    description: str
    input_schema: dict[str, Any]
    
    def to_anthropic(self) -> dict[str, Any]:
        """Convert to Anthropic format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }
    
    def to_openai(self) -> dict[str, Any]:
        """Convert to OpenAI format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


@dataclass
class LLMMessage:
    """Message for LLM API.
    
    Roles:
        - system: System prompt
        - user: User message (can include images)
        - assistant: Assistant response (can include tool_calls)
        - tool: Tool result (requires tool_call_id and name)
    
    Supports dual content for context management:
        - content: Complete content (raw), for storage and recall
        - truncated_content: Shortened content for context window (defaults to content)
    """
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]]
    tool_call_id: str | None = None  # Required for tool role
    name: str | None = None  # Tool name, required for Gemini compatibility
    truncated_content: str | list[dict[str, Any]] | None = None  # Shortened content (defaults to content)
    
    def to_dict(self) -> dict[str, Any]:
        d = {"role": self.role, "content": self.content}
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        if self.truncated_content is not None:
            d["truncated_content"] = self.truncated_content
        return d
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access for middleware compatibility."""
        return getattr(self, key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Dict-like access via []."""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)
    
    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        """Create system message."""
        return cls(role="system", content=content)
    
    @classmethod
    def user(cls, content: str | list[dict[str, Any]]) -> "LLMMessage":
        """Create user message."""
        return cls(role="user", content=content)
    
    @classmethod
    def assistant(cls, content: str | list[dict[str, Any]]) -> "LLMMessage":
        """Create assistant message."""
        return cls(role="assistant", content=content)
    
    @classmethod
    def tool(
        cls,
        content: str,
        tool_call_id: str,
        name: str | None = None,
        truncated_content: str | None = None,
    ) -> "LLMMessage":
        """Create tool result message.
        
        Args:
            content: Tool result content (complete/raw)
            tool_call_id: ID of the tool call this result is for
            name: Tool name (required for Gemini compatibility)
            truncated_content: Shortened content for context window (defaults to content)
        """
        return cls(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            truncated_content=truncated_content,
        )


@runtime_checkable
class LLMProvider(Protocol):
    """LLM Provider protocol.
    
    Implement this protocol to support different LLM backends.
    """
    
    @property
    def provider(self) -> str:
        """Provider name (openai, anthropic, etc.)."""
        ...
    
    @property
    def model(self) -> str:
        """Model name."""
        ...
    
    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMEvent]:
        """Generate completion with streaming.
        
        Args:
            messages: Conversation messages
            tools: Available tools (optional)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Yields:
            LLMEvent: Streaming events
        """
        ...


@dataclass
class MockResponse:
    """Mock response configuration.
    
    Attributes:
        text: Text response content
        thinking: Thinking content (for models that support it)
        tool_calls: List of tool calls to make
        finish_reason: Completion reason
        delay: Simulated delay in seconds
        stream: Whether to stream character by character
    """
    text: str = ""
    thinking: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str = "end_turn"
    delay: float = 0.0
    stream: bool = True


class MockLLMProvider:
    """Mock LLM provider for testing and examples.
    
    Supports both simple string responses and structured MockResponse objects.
    
    Examples:
        # Simple usage
        llm = MockLLMProvider(responses=["Hello!", "How can I help?"])
        
        # With MockResponse for tool calls
        llm = MockLLMProvider(responses=[
            MockResponse(
                thinking="I need to use the calculator",
                tool_calls=[{"name": "calc", "arguments": {"expr": "1+1"}}]
            ),
            MockResponse(text="The result is 2.")
        ])
        
        # Smart mode - auto-generate responses
        llm = MockLLMProvider(smart_mode=True)
    """
    
    def __init__(
        self,
        provider: str = "mock",
        model: str = "mock-model",
        responses: list[str | MockResponse] | None = None,
        smart_mode: bool = False,
        default_delay: float = 0.0,
    ):
        self._provider = provider
        self._model = model
        self._responses = responses or []
        self._smart_mode = smart_mode
        self._default_delay = default_delay
        self._call_count = 0
        self._response_index = 0
    
    @property
    def provider(self) -> str:
        return self._provider
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def call_count(self) -> int:
        return self._call_count
    
    def reset(self) -> None:
        """Reset call count and response index."""
        self._call_count = 0
        self._response_index = 0
    
    def add_response(self, response: str | MockResponse) -> None:
        """Add a response to the queue."""
        self._responses.append(response)
    
    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        enable_thinking: bool = False,
        **kwargs: Any,
    ) -> AsyncIterator[LLMEvent]:
        """Return mock response.
        
        Args:
            messages: Conversation messages
            tools: Available tools
            enable_thinking: Whether to output thinking content
            **kwargs: Additional parameters (ignored)
        """
        import asyncio
        import json
        
        self._call_count += 1
        
        # Get response
        response = self._get_response(messages, tools)
        
        # Delay if configured
        if isinstance(response, MockResponse) and response.delay > 0:
            await asyncio.sleep(response.delay)
        elif self._default_delay > 0:
            await asyncio.sleep(self._default_delay)
        
        # Normalize to MockResponse
        if isinstance(response, str):
            response = MockResponse(text=response)
        
        # Stream thinking (only if enabled and response has thinking)
        if enable_thinking and response.thinking:
            if response.stream:
                for char in response.thinking:
                    yield LLMEvent(type="thinking", delta=char)
            else:
                yield LLMEvent(type="thinking", delta=response.thinking)
        
        # Stream text
        if response.text:
            if response.stream:
                for char in response.text:
                    yield LLMEvent(type="content", delta=char)
            else:
                yield LLMEvent(type="content", delta=response.text)
        
        # Tool calls
        for i, tc in enumerate(response.tool_calls):
            tool_call = ToolCall(
                id=tc.get("id", f"call_{self._call_count}_{i}"),
                name=tc["name"],
                arguments=json.dumps(tc.get("arguments", {})),
            )
            yield LLMEvent(type="tool_call", tool_call=tool_call)
        
        # Usage
        yield LLMEvent(
            type="usage",
            usage=Usage(
                input_tokens=self._estimate_tokens(messages),
                output_tokens=len(response.text) // 4 + len(response.thinking) // 4 + 10,
            ),
        )
        
        # Complete
        finish_reason = response.finish_reason
        if response.tool_calls:
            finish_reason = "tool_use"
        yield LLMEvent(type="completed", finish_reason=finish_reason)
    
    def _get_response(self, messages: list[LLMMessage], tools: list[ToolDefinition] | None) -> str | MockResponse:
        """Get next response."""
        # Use queued responses first
        if self._response_index < len(self._responses):
            response = self._responses[self._response_index]
            self._response_index += 1
            return response
        
        # Smart mode: generate response based on input
        if self._smart_mode:
            return self._generate_smart_response(messages, tools)
        
        # Default response
        return "Hello! How can I help you?"
    
    def _generate_smart_response(self, messages: list[LLMMessage], tools: list[ToolDefinition] | None) -> MockResponse:
        """Generate response based on input."""
        # Check for tool results
        for msg in messages:
            if isinstance(msg.content, list):
                for part in msg.content:
                    if isinstance(part, dict) and part.get("type") == "tool_result":
                        return MockResponse(text="I've processed the tool result. Is there anything else?")
        
        # Get last user message
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.role == "user":
                if isinstance(msg.content, str):
                    last_user_msg = msg.content
                break
        
        # Simple keyword responses
        lower_msg = last_user_msg.lower()
        if "hello" in lower_msg or "你好" in lower_msg:
            return MockResponse(text="你好！我是 AI 助手，有什么可以帮助你的？")
        if "谢谢" in lower_msg or "thank" in lower_msg:
            return MockResponse(text="不客气！还有其他问题吗？")
        if "再见" in lower_msg or "bye" in lower_msg:
            return MockResponse(text="再见！祝你有愉快的一天！")
        
        return MockResponse(text=f"[Mock] 收到: {last_user_msg[:50]}...")
    
    def _estimate_tokens(self, messages: list[LLMMessage]) -> int:
        """Estimate token count."""
        total = 0
        for msg in messages:
            if isinstance(msg.content, str):
                total += len(msg.content) // 4
            elif isinstance(msg.content, list):
                total += sum(len(str(p)) // 4 for p in msg.content)
        return max(total, 10)


class ToolCallMockProvider(MockLLMProvider):
    """Mock provider that returns tool calls in sequence.
    
    Example:
        llm = ToolCallMockProvider(
            tool_calls=[
                {"name": "search", "arguments": {"query": "test"}},
                {"name": "read", "arguments": {"file": "test.txt"}},
            ],
            final_response="Based on the results, here's my answer..."
        )
    """
    
    def __init__(
        self,
        tool_calls: list[dict[str, Any]],
        final_response: str = "Done!",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._tool_call_queue = tool_calls
        self._final_response = final_response
        self._tool_results_received = 0
    
    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMEvent]:
        """Return tool calls or final response."""
        import json
        
        self._call_count += 1
        
        # Check if we've received tool results
        has_tool_result = any(
            isinstance(m.content, list) and 
            any(p.get("type") == "tool_result" for p in m.content if isinstance(p, dict))
            for m in messages
        )
        
        if has_tool_result:
            self._tool_results_received += 1
        
        # Return tool calls if we haven't exhausted them
        if self._tool_results_received < len(self._tool_call_queue):
            tc = self._tool_call_queue[self._tool_results_received]
            yield LLMEvent(
                type="tool_call",
                tool_call=ToolCall(
                    id=f"call_{self._tool_results_received}",
                    name=tc["name"],
                    arguments=json.dumps(tc.get("arguments", {})),
                ),
            )
        else:
            # Return final response
            for char in self._final_response:
                yield LLMEvent(type="content", delta=char)
        
        yield LLMEvent(
            type="usage",
            usage=Usage(input_tokens=100, output_tokens=50),
        )
        yield LLMEvent(type="completed", finish_reason="end_turn")
