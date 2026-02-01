"""Middleware system for request/response processing.

Middleware provides hooks for intercepting and modifying:
- LLM requests/responses
- Agent lifecycle events
- Tool execution
- Sub-agent delegation
- Message persistence
"""
from .types import TriggerMode, HookAction, HookResult, MiddlewareConfig
from .base import Middleware, BaseMiddleware
from .chain import MiddlewareChain
from .message_container import MessageContainerMiddleware
from .message import MessageBackendMiddleware
from .truncation import MessageTruncationMiddleware

__all__ = [
    "TriggerMode",
    "HookAction",
    "HookResult",
    "MiddlewareConfig",
    "Middleware",
    "BaseMiddleware",
    "MiddlewareChain",
    # Default middlewares
    "MessageContainerMiddleware",
    "MessageBackendMiddleware",
    "MessageTruncationMiddleware",
]
