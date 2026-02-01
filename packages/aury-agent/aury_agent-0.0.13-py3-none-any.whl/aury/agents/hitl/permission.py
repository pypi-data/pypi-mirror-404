"""Registry-based permission system for human-in-the-loop approval.

Design:
1. PermissionChecker - Protocol for permission type handlers
2. PermissionRegistry - Register checkers by type
3. Unified rules format: "type:pattern" -> "allow|ask|deny"
4. Tools declare their permission requirements via PermissionSpec
"""
from __future__ import annotations

import asyncio
import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Protocol, runtime_checkable

from ..core.event_bus import EventBus, Events
from ..core.types.session import generate_id


# =============================================================================
# Exceptions
# =============================================================================

class RejectedError(Exception):
    """Raised when permission is rejected."""
    
    def __init__(
        self,
        reason: str,
        session_id: str | None = None,
        permission_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(reason)
        self.reason = reason
        self.session_id = session_id
        self.permission_id = permission_id
        self.metadata = metadata or {}


class SkippedError(Exception):
    """Raised when permission is skipped."""
    pass


# =============================================================================
# Response Types
# =============================================================================

class HumanResponse(Enum):
    """Human response options for permission requests."""
    APPROVE_ONCE = "approve_once"
    APPROVE_ALWAYS = "approve_always"
    REJECT = "reject"
    EDIT = "edit"
    SKIP = "skip"


Action = Literal["allow", "ask", "deny"]


# =============================================================================
# Permission Checker Protocol
# =============================================================================

@runtime_checkable
class PermissionChecker(Protocol):
    """Protocol for permission type handlers.
    
    Each checker handles one permission type (e.g., "shell", "file", "code").
    Tools declare which checker type they use.
    """
    
    @property
    def type(self) -> str:
        """Permission type identifier (e.g., 'shell', 'file', 'code')."""
        ...
    
    def get_pattern(self, args: dict[str, Any]) -> str:
        """Extract pattern from tool arguments for rule matching.
        
        Examples:
            shell: command string
            file: file path
            code: language or "*"
        """
        ...
    
    def get_ask_message(self, args: dict[str, Any]) -> str:
        """Generate human-readable message for permission request."""
        ...


# =============================================================================
# Built-in Checkers
# =============================================================================

class ShellPermissionChecker:
    """Permission checker for shell command execution."""
    
    type = "shell"
    
    def __init__(self, command_arg: str = "command"):
        self.command_arg = command_arg
    
    def get_pattern(self, args: dict[str, Any]) -> str:
        return args.get(self.command_arg, "")
    
    def get_ask_message(self, args: dict[str, Any]) -> str:
        cmd = self.get_pattern(args)
        return f"Execute shell command: {cmd}"


class FilePermissionChecker:
    """Permission checker for file operations."""
    
    type = "file"
    
    def __init__(self, path_arg: str = "path", op_arg: str = "operation"):
        self.path_arg = path_arg
        self.op_arg = op_arg
    
    def get_pattern(self, args: dict[str, Any]) -> str:
        op = args.get(self.op_arg, "read")
        path = args.get(self.path_arg, "")
        return f"{op}:{path}"
    
    def get_ask_message(self, args: dict[str, Any]) -> str:
        op = args.get(self.op_arg, "read")
        path = args.get(self.path_arg, "")
        return f"File {op}: {path}"


class CodePermissionChecker:
    """Permission checker for code execution."""
    
    type = "code"
    
    def __init__(self, language_arg: str = "language"):
        self.language_arg = language_arg
    
    def get_pattern(self, args: dict[str, Any]) -> str:
        return args.get(self.language_arg, "*")
    
    def get_ask_message(self, args: dict[str, Any]) -> str:
        lang = args.get(self.language_arg, "unknown")
        code = args.get("code", "")[:100]
        return f"Execute {lang} code: {code}..."


class GenericPermissionChecker:
    """Generic permission checker for custom tools."""
    
    def __init__(self, type: str, pattern_args: list[str] | None = None):
        self._type = type
        self.pattern_args = pattern_args or []
    
    @property
    def type(self) -> str:
        return self._type
    
    def get_pattern(self, args: dict[str, Any]) -> str:
        if not self.pattern_args:
            return "*"
        parts = [str(args.get(k, "")) for k in self.pattern_args]
        return ":".join(parts) if parts else "*"
    
    def get_ask_message(self, args: dict[str, Any]) -> str:
        return f"Execute {self._type}: {self.get_pattern(args)}"


# =============================================================================
# Permission Registry
# =============================================================================

class PermissionRegistry:
    """Registry for permission checkers.
    
    Usage:
        # Register checker
        PermissionRegistry.register(ShellPermissionChecker())
        
        # Get checker
        checker = PermissionRegistry.get("shell")
    """
    
    _checkers: dict[str, PermissionChecker] = {}
    
    @classmethod
    def register(cls, checker: PermissionChecker) -> None:
        """Register a permission checker."""
        cls._checkers[checker.type] = checker
    
    @classmethod
    def get(cls, type: str) -> PermissionChecker | None:
        """Get checker by type."""
        return cls._checkers.get(type)
    
    @classmethod
    def get_or_create(cls, type: str, **kwargs) -> PermissionChecker:
        """Get existing checker or create generic one."""
        if type in cls._checkers:
            return cls._checkers[type]
        return GenericPermissionChecker(type, **kwargs)
    
    @classmethod
    def list_types(cls) -> list[str]:
        """List all registered types."""
        return list(cls._checkers.keys())
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered checkers (for testing)."""
        cls._checkers.clear()


# Register built-in checkers
PermissionRegistry.register(ShellPermissionChecker())
PermissionRegistry.register(FilePermissionChecker())
PermissionRegistry.register(CodePermissionChecker())


# =============================================================================
# Permission Spec (for tools to declare requirements)
# =============================================================================

@dataclass
class PermissionSpec:
    """Permission specification for tools.
    
    Tools declare this to specify their permission requirements.
    
    Example:
        class BashTool(BaseTool):
            permission = PermissionSpec(
                type="shell",
                pattern_args=["command"],
            )
    """
    type: str
    pattern_args: list[str] = field(default_factory=list)
    custom_checker: PermissionChecker | None = None
    
    def get_checker(self) -> PermissionChecker:
        """Get the checker for this spec."""
        if self.custom_checker:
            return self.custom_checker
        return PermissionRegistry.get_or_create(
            self.type, 
            pattern_args=self.pattern_args
        )


# =============================================================================
# Rules Configuration
# =============================================================================

@dataclass
class PermissionRules:
    """Permission rules configuration.
    
    Unified format: "type:pattern" -> "allow|ask|deny"
    
    Pattern matching uses fnmatch (shell-style wildcards).
    Rules are evaluated in order, first match wins.
    
    Example:
        rules = PermissionRules({
            "shell:rm -rf *": "deny",
            "shell:sudo *": "ask",
            "shell:*": "allow",
            "file:write:/etc/*": "deny",
            "file:*": "allow",
            "code:*": "deny",
            "*:*": "ask",  # Default
        })
    """
    
    rules: dict[str, Action] = field(default_factory=dict)
    default_action: Action = "ask"
    
    def get_action(self, type: str, pattern: str) -> Action:
        """Get action for type:pattern.
        
        Evaluates rules in order, returns first match.
        """
        full_pattern = f"{type}:{pattern}"
        
        for rule_pattern, action in self.rules.items():
            if fnmatch.fnmatch(full_pattern, rule_pattern):
                return action
        
        return self.default_action
    
    @classmethod
    def allow_all(cls) -> "PermissionRules":
        """Create rules that allow everything."""
        return cls(rules={"*:*": "allow"}, default_action="allow")
    
    @classmethod
    def deny_all(cls) -> "PermissionRules":
        """Create rules that deny everything."""
        return cls(rules={"*:*": "deny"}, default_action="deny")
    
    @classmethod
    def ask_all(cls) -> "PermissionRules":
        """Create rules that ask for everything."""
        return cls(rules={}, default_action="ask")


# =============================================================================
# Pending Permission
# =============================================================================

@dataclass
class PendingPermission:
    """A pending permission request awaiting human response."""
    id: str
    type: str
    pattern: str
    session_id: str
    invocation_id: str
    block_id: str
    call_id: str | None
    message: str
    metadata: dict[str, Any]
    future: asyncio.Future[dict[str, Any] | None]
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


# =============================================================================
# Permission Manager
# =============================================================================

class Permission:
    """Permission manager for human-in-the-loop approval.
    
    Usage:
        permission = Permission(bus, rules)
        
        # Check permission (blocks if needs approval)
        await permission.check(
            type="shell",
            args={"command": "rm -rf /tmp/*"},
            session_id="...",
            ...
        )
    """
    
    def __init__(
        self,
        bus: EventBus,
        rules: PermissionRules | None = None,
    ):
        self.bus = bus
        self.rules = rules or PermissionRules()
        
        # Pending requests
        self._pending: dict[str, PendingPermission] = {}
        
        # Approved patterns: session_id -> set of "type:pattern"
        self._approved: dict[str, set[str]] = {}
        
        self._lock = asyncio.Lock()
    
    async def check(
        self,
        type: str,
        args: dict[str, Any],
        session_id: str,
        invocation_id: str,
        block_id: str,
        call_id: str | None = None,
        spec: PermissionSpec | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Check permission and wait for approval if needed.
        
        Args:
            type: Permission type (shell, file, code, etc.)
            args: Tool arguments
            session_id: Current session ID
            invocation_id: Current invocation ID
            block_id: Current block ID
            call_id: Tool call ID
            spec: Optional PermissionSpec (uses registry if not provided)
            metadata: Additional context
            
        Returns:
            Edited args if user chose EDIT, otherwise None
            
        Raises:
            RejectedError: If permission was denied
            SkippedError: If user chose to skip
        """
        metadata = metadata or {}
        
        # Get checker
        if spec:
            checker = spec.get_checker()
        else:
            checker = PermissionRegistry.get_or_create(type)
        
        # Extract pattern
        pattern = checker.get_pattern(args)
        
        # 1. Check rules
        action = self.rules.get_action(type, pattern)
        
        if action == "allow":
            return None
        
        if action == "deny":
            raise RejectedError(
                f"Permission denied by rules: {type}:{pattern}",
                session_id=session_id,
                metadata=metadata,
            )
        
        # 2. Check session approvals
        if self._is_approved(session_id, type, pattern):
            return None
        
        # 3. Request approval
        message = checker.get_ask_message(args)
        
        return await self._request_permission(
            type=type,
            pattern=pattern,
            session_id=session_id,
            invocation_id=invocation_id,
            block_id=block_id,
            call_id=call_id,
            message=message,
            metadata={**metadata, "args": args},
        )
    
    async def check_with_spec(
        self,
        spec: PermissionSpec,
        args: dict[str, Any],
        session_id: str,
        invocation_id: str,
        block_id: str,
        call_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Check permission using a PermissionSpec."""
        return await self.check(
            type=spec.type,
            args=args,
            session_id=session_id,
            invocation_id=invocation_id,
            block_id=block_id,
            call_id=call_id,
            spec=spec,
            metadata=metadata,
        )
    
    async def _request_permission(
        self,
        type: str,
        pattern: str,
        session_id: str,
        invocation_id: str,
        block_id: str,
        call_id: str | None,
        message: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Create and wait for a permission request."""
        permission_id = generate_id("perm")
        future: asyncio.Future[dict[str, Any] | None] = asyncio.Future()
        
        pending = PendingPermission(
            id=permission_id,
            type=type,
            pattern=pattern,
            session_id=session_id,
            invocation_id=invocation_id,
            block_id=block_id,
            call_id=call_id,
            message=message,
            metadata=metadata,
            future=future,
        )
        
        async with self._lock:
            self._pending[permission_id] = pending
        
        # Publish event
        await self.bus.publish(Events.PERMISSION_REQUESTED, {
            "permission_id": permission_id,
            "type": type,
            "pattern": pattern,
            "message": message,
            "session_id": session_id,
            "invocation_id": invocation_id,
            "block_id": block_id,
            "call_id": call_id,
            "metadata": metadata,
        })
        
        try:
            return await future
        finally:
            async with self._lock:
                self._pending.pop(permission_id, None)
    
    def respond(
        self,
        permission_id: str,
        response: HumanResponse,
        edited_args: dict[str, Any] | None = None,
    ) -> None:
        """Respond to a permission request."""
        if permission_id not in self._pending:
            raise ValueError(f"Unknown permission request: {permission_id}")
        
        pending = self._pending[permission_id]
        
        match response:
            case HumanResponse.APPROVE_ONCE:
                pending.future.set_result(None)
            
            case HumanResponse.APPROVE_ALWAYS:
                self._add_approved(pending.session_id, pending.type, pending.pattern)
                pending.future.set_result(None)
            
            case HumanResponse.REJECT:
                pending.future.set_exception(RejectedError(
                    "User rejected permission",
                    session_id=pending.session_id,
                    permission_id=permission_id,
                    metadata=pending.metadata,
                ))
            
            case HumanResponse.EDIT:
                pending.future.set_result(edited_args)
            
            case HumanResponse.SKIP:
                pending.future.set_exception(SkippedError())
        
        # Publish resolution
        asyncio.create_task(self.bus.publish(Events.PERMISSION_RESOLVED, {
            "permission_id": permission_id,
            "response": response.value,
            "session_id": pending.session_id,
        }))
    
    def _is_approved(self, session_id: str, type: str, pattern: str) -> bool:
        """Check if type:pattern is already approved."""
        if session_id not in self._approved:
            return False
        
        full = f"{type}:{pattern}"
        for approved in self._approved[session_id]:
            if fnmatch.fnmatch(full, approved):
                return True
        
        return False
    
    def _add_approved(self, session_id: str, type: str, pattern: str) -> None:
        """Add to approved set."""
        if session_id not in self._approved:
            self._approved[session_id] = set()
        self._approved[session_id].add(f"{type}:{pattern}")
    
    def clear_session(self, session_id: str) -> None:
        """Clear all approvals for a session."""
        self._approved.pop(session_id, None)
    
    def get_pending(self, session_id: str | None = None) -> list[PendingPermission]:
        """Get pending permission requests."""
        if session_id:
            return [p for p in self._pending.values() if p.session_id == session_id]
        return list(self._pending.values())
    
    def cancel_all(self, session_id: str | None = None) -> int:
        """Cancel all pending permissions."""
        cancelled = 0
        for pending in self.get_pending(session_id):
            if not pending.future.done():
                pending.future.set_exception(SkippedError())
                cancelled += 1
        return cancelled


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Exceptions
    "RejectedError",
    "SkippedError",
    # Types
    "HumanResponse",
    "Action",
    # Checker protocol
    "PermissionChecker",
    # Built-in checkers
    "ShellPermissionChecker",
    "FilePermissionChecker",
    "CodePermissionChecker",
    "GenericPermissionChecker",
    # Registry
    "PermissionRegistry",
    # Spec
    "PermissionSpec",
    # Rules
    "PermissionRules",
    # Manager
    "PendingPermission",
    "Permission",
]
