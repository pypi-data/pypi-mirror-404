"""Block and BlockEvent data structures for streaming protocol."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from .session import generate_id

if TYPE_CHECKING:
    from ..context import InvocationContext


class BlockKind(str, Enum):
    """Framework built-in block types.
    
    These are the default kinds used by the framework internally.
    Developers can use any custom string as block kind - 
    this enum is not exhaustive.
    
    Example custom kinds: "code", "chart", "table", "image", etc.
    """
    
    # === Content ===
    TEXT = "text"              # Plain text / markdown
    THINKING = "thinking"      # LLM reasoning (collapsible)
    
    # === Tool Execution ===
    # TOOL_USE manages entire tool lifecycle via PATCH:
    # APPLY → {name, call_id, arguments, status: "pending"}
    # PATCH → {status: "running", progress: ...}  (tool can emit during execution)
    # PATCH → {status: "success"}  (framework emits on completion)
    TOOL_USE = "tool_use"
    
    # === Agent ===
    SUB_AGENT = "sub_agent"    # Sub-agent delegation
    PLAN = "plan"              # Execution plan with checklist
    
    # === Workflow ===
    START = "start"            # Workflow start
    END = "end"                # Workflow end
    NODE = "node"              # Workflow node execution block
    
    # === HITL ===
    HITL = "hitl"  # Human-in-the-loop (ask_user, confirm, permission, etc.)
    
    # === Control Flow ===
    YIELD = "yield"               # Return control to parent
    
    # === Output ===
    ARTIFACT = "artifact"      # Generated artifact (file, document, etc.)
    ERROR = "error"            # Error message


class BlockOp(str, Enum):
    """Block operations.
    
    Blocks have no lifecycle - they exist once created and can be
    operated on at any time via their id.
    """
    APPLY = "apply"    # Complete data (create or replace)
    DELTA = "delta"    # Incremental append
    PATCH = "patch"    # Partial modification


class Persistence(str, Enum):
    """Framework built-in persistence types.
    
    Developers can use custom strings for specialized persistence behaviors.
    """
    PERSISTENT = "persistent"  # Stored to backend
    TRANSIENT = "transient"    # Not stored (progress bars, spinners, etc.)


@dataclass
class ActorInfo:
    """Actor information."""
    id: str
    role: Literal["user", "assistant", "system"]
    name: str | None = None
    meta: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "name": self.name,
            "meta": self.meta,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActorInfo:
        return cls(
            id=data["id"],
            role=data["role"],
            name=data.get("name"),
            meta=data.get("meta"),
        )


@dataclass
class BlockEvent:
    """Streaming block event.
    
    Used for real-time streaming to frontend.
    Operations: APPLY (create/replace), DELTA (append), PATCH (partial update)
    """
    block_id: str = field(default_factory=lambda: generate_id("blk"))
    parent_id: str | None = None  # For nesting
    kind: BlockKind | str = BlockKind.TEXT
    persistence: Persistence = Persistence.PERSISTENT
    op: BlockOp = BlockOp.APPLY
    data: dict[str, Any] | None = None
    branch: str | None = None  # For sub-agent isolation (e.g. "agent1.agent2")
    schema_version: str | None = None  # Schema version for external rendering/handling
    
    # Protocol envelope
    protocol_version: str = "1.0"
    event_id: str = field(default_factory=lambda: generate_id("evt"))
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    invocation_id: str = ""
    session_id: str = ""
    actor: ActorInfo | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        kind_value = self.kind.value if isinstance(self.kind, BlockKind) else self.kind
        return {
            "block_id": self.block_id,
            "parent_id": self.parent_id,
            "kind": kind_value,
            "persistence": self.persistence.value,
            "op": self.op.value,
            "data": self.data,
            "branch": self.branch,
            "schema_version": self.schema_version,
            "protocol_version": self.protocol_version,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "invocation_id": self.invocation_id,
            "session_id": self.session_id,
            "actor": self.actor.to_dict() if self.actor else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlockEvent:
        """Create from dictionary."""
        kind_str = data["kind"]
        try:
            kind = BlockKind(kind_str)
        except ValueError:
            kind = kind_str  # Custom kind string
        return cls(
            block_id=data["block_id"],
            parent_id=data.get("parent_id"),
            kind=kind,
            persistence=Persistence(data["persistence"]),
            op=BlockOp(data["op"]),
            data=data.get("data"),
            branch=data.get("branch"),
            schema_version=data.get("schema_version"),
            protocol_version=data.get("protocol_version", "1.0"),
            event_id=data.get("event_id", ""),
            timestamp=data.get("timestamp", 0),
            invocation_id=data.get("invocation_id", ""),
            session_id=data.get("session_id", ""),
            actor=ActorInfo.from_dict(data["actor"]) if data.get("actor") else None,
        )


# ============================================================
# BlockMerger - Merge BlockEvents by kind
# ============================================================

class BlockMerger:
    """Base class for block mergers.
    
    Mergers define how to combine multiple BlockEvents into final data.
    Register custom mergers for custom block kinds.
    
    Override apply/delta/patch methods to customize specific operations.
    """
    
    def merge(self, current: dict[str, Any] | None, event: "BlockEvent") -> dict[str, Any]:
        """Merge event into current data. Dispatches to apply/delta/patch."""
        if event.op == BlockOp.APPLY:
            return self.apply(current, event)
        elif event.op == BlockOp.DELTA:
            return self.delta(current, event)
        elif event.op == BlockOp.PATCH:
            return self.patch(current, event)
        return current or {}
    
    def apply(self, current: dict[str, Any] | None, event: "BlockEvent") -> dict[str, Any]:
        """Handle APPLY: replace entirely with new data."""
        return event.data or {}
    
    def delta(self, current: dict[str, Any] | None, event: "BlockEvent") -> dict[str, Any]:
        """Handle DELTA: append/accumulate data.
        
        Default: string concatenation, list extension.
        """
        data = dict(current) if current else {}
        if event.data:
            for key, value in event.data.items():
                if isinstance(value, str) and isinstance(data.get(key, ""), str):
                    data[key] = data.get(key, "") + value
                elif isinstance(value, list) and isinstance(data.get(key), list):
                    data[key] = data.get(key, []) + value
                else:
                    data[key] = value
        return data
    
    def patch(self, current: dict[str, Any] | None, event: "BlockEvent") -> dict[str, Any]:
        """Handle PATCH: partial update with JSON Path syntax.
        
        Default: supports nested path like "a.b.c" or "items[0].name".
        """
        data = dict(current) if current else {}
        if event.data:
            for path, value in event.data.items():
                self._set_path(data, path, value)
        return data
    
    def _set_path(self, data: dict, path: str, value: Any) -> None:
        """Set value at path (supports nested paths).
        
        Path syntax:
        - "key" -> data["key"]
        - "a.b.c" -> data["a"]["b"]["c"]
        - "items[0]" -> data["items"][0]
        - "items[0].name" -> data["items"][0]["name"]
        """
        import re
        
        # Parse path into parts
        parts = []
        for segment in path.replace("]", "").split("."):
            if "[" in segment:
                key, idx = segment.split("[")
                if key:
                    parts.append(key)
                parts.append(int(idx))
            else:
                parts.append(segment)
        
        # Navigate to parent
        current = data
        for part in parts[:-1]:
            if isinstance(part, int):
                # Ensure list exists and is long enough
                if not isinstance(current, list):
                    break
                while len(current) <= part:
                    current.append({})
                current = current[part]
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        # Set final value
        final_key = parts[-1]
        if isinstance(final_key, int) and isinstance(current, list):
            while len(current) <= final_key:
                current.append(None)
            current[final_key] = value
        elif isinstance(current, dict):
            current[final_key] = value


# Merger registry
_block_mergers: dict[str, BlockMerger] = {}
_default_merger = BlockMerger()


def register_merger(kind: str, merger: BlockMerger) -> None:
    """Register a custom merger for a block kind.
    
    Args:
        kind: Block kind (e.g. "plan", "my_custom_type")
        merger: Merger instance
    """
    _block_mergers[kind] = merger


def get_merger(kind: str | BlockKind) -> BlockMerger:
    """Get merger for a block kind.
    
    Args:
        kind: Block kind
        
    Returns:
        Registered merger or default merger
    """
    kind_str = kind.value if isinstance(kind, BlockKind) else kind
    return _block_mergers.get(kind_str, _default_merger)


# ============================================================
# PersistedBlock
# ============================================================

@dataclass
class PersistedBlock:
    """Persisted block (final state, no op).
    
    This is what gets stored after BlockEvent stream is complete.
    """
    block_id: str
    parent_id: str | None = None
    kind: BlockKind | str = BlockKind.TEXT
    data: dict[str, Any] | None = None
    
    # From protocol envelope
    session_id: str = ""
    invocation_id: str = ""
    actor: ActorInfo | None = None
    
    # Branch for sub-agent isolation
    branch: str | None = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None
    
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        kind_value = self.kind.value if isinstance(self.kind, BlockKind) else self.kind
        return {
            "block_id": self.block_id,
            "parent_id": self.parent_id,
            "kind": kind_value,
            "data": self.data,
            "session_id": self.session_id,
            "invocation_id": self.invocation_id,
            "actor": self.actor.to_dict() if self.actor else None,
            "branch": self.branch,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PersistedBlock:
        """Create from dictionary."""
        kind_str = data["kind"]
        try:
            kind = BlockKind(kind_str)
        except ValueError:
            kind = kind_str
        return cls(
            block_id=data["block_id"],
            parent_id=data.get("parent_id"),
            kind=kind,
            data=data.get("data"),
            session_id=data.get("session_id", ""),
            invocation_id=data.get("invocation_id", ""),
            actor=ActorInfo.from_dict(data["actor"]) if data.get("actor") else None,
            branch=data.get("branch"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def from_events(cls, events: list[BlockEvent]) -> "PersistedBlock":
        """Aggregate BlockEvents for a SINGLE block into a PersistedBlock.
        
        All events must have the same block_id.
        Uses registered merger for the block kind to combine events.
        """
        if not events:
            raise ValueError("Cannot create PersistedBlock from empty events")
        
        first = events[0]
        kind = first.kind
        
        # Get merger for this kind
        merger = get_merger(kind)
        
        # Merge all events
        data: dict[str, Any] | None = None
        last_timestamp = first.timestamp
        
        for event in events:
            data = merger.merge(data, event)
            last_timestamp = event.timestamp
        
        return cls(
            block_id=first.block_id,
            parent_id=first.parent_id,
            kind=kind,
            data=data,
            branch=first.branch,
            session_id=first.session_id,
            invocation_id=first.invocation_id,
            actor=first.actor,
            updated_at=datetime.fromtimestamp(last_timestamp / 1000) if len(events) > 1 else None,
        )
    
    @classmethod
    def from_event_stream(cls, events: list[BlockEvent]) -> list["PersistedBlock"]:
        """Aggregate BlockEvents into multiple PersistedBlocks.
        
        Groups events by block_id, then merges each group.
        Returns blocks in order of first appearance.
        
        Args:
            events: List of BlockEvents (can have multiple block_ids)
            
        Returns:
            List of PersistedBlocks, one per unique block_id
        """
        if not events:
            return []
        
        # Group by block_id, preserving order
        from collections import OrderedDict
        grouped: OrderedDict[str, list[BlockEvent]] = OrderedDict()
        for event in events:
            if event.block_id not in grouped:
                grouped[event.block_id] = []
            grouped[event.block_id].append(event)
        
        # Create PersistedBlock for each group
        return [cls.from_events(group) for group in grouped.values()]


# ============================================================
# BlockAggregator - Aggregate events into blocks
# ============================================================

class BlockAggregator:
    """Aggregates BlockEvents into PersistedBlocks incrementally.
    
    Processes events one by one, updating blocks as they arrive.
    
    Example:
        aggregator = BlockAggregator()
        async for event in event_stream:
            aggregator.process(event)
        blocks = aggregator.blocks  # Final result
    """
    
    def __init__(self):
        self._blocks: dict[str, PersistedBlock] = {}
        self._order: list[str] = []  # Track insertion order
    
    def process(self, event: BlockEvent) -> PersistedBlock:
        """Process a single event, updating the corresponding block.
        
        Returns the updated PersistedBlock.
        """
        block_id = event.block_id
        merger = get_merger(event.kind)
        
        if block_id in self._blocks:
            # Update existing block
            block = self._blocks[block_id]
            block.data = merger.merge(block.data, event)
            block.updated_at = datetime.fromtimestamp(event.timestamp / 1000)
        else:
            # Create new block
            block = PersistedBlock(
                block_id=block_id,
                parent_id=event.parent_id,
                kind=event.kind,
                data=merger.merge(None, event),
                branch=event.branch,
                session_id=event.session_id,
                invocation_id=event.invocation_id,
                actor=event.actor,
            )
            self._blocks[block_id] = block
            self._order.append(block_id)
        
        return block
    
    def get(self, block_id: str) -> PersistedBlock | None:
        """Get a block by ID."""
        return self._blocks.get(block_id)
    
    @property
    def blocks(self) -> list[PersistedBlock]:
        """Get all blocks in order of first appearance."""
        return [self._blocks[bid] for bid in self._order]
    
    def clear(self) -> None:
        """Clear all blocks."""
        self._blocks.clear()
        self._order.clear()


# ============================================================
# BlockHandle - Manage Block lifecycle
# ============================================================

class BlockHandle:
    """Block handle - manages a single Block's lifecycle.
    
    Use this to manage a Block that needs multiple operations over time:
    - Streaming text output (APPLY -> DELTA -> DELTA -> ...)
    - Plan with progress updates (APPLY -> PATCH -> PATCH -> ...)
    - Any Block that needs cross-content modification
    
    Example:
        # Streaming text
        text = BlockHandle(ctx, kind="text")
        await text.apply({"content": ""})
        await text.delta({"delta": "Hello "})
        await text.delta({"delta": "World"})
        
        # Plan with updates
        plan = BlockHandle(ctx, kind="plan")
        await plan.apply({"steps": [...], "current": 0})
        await plan.patch({"current": 1, "steps[0].status": "done"})
        
        # Nested blocks
        tool = BlockHandle(ctx, kind="tool_use")
        await tool.apply({"name": "bash", "args": {...}})
        output = BlockHandle(ctx, kind="text", parent=tool)
        await output.apply({"content": "result..."})
    """
    
    def __init__(
        self,
        ctx: "InvocationContext",
        kind: BlockKind | str,
        block_id: str | None = None,
        parent: "BlockHandle | str | None" = None,
        persistence: Persistence = Persistence.PERSISTENT,
        branch: str | None = None,
        schema_version: str | None = None,
    ):
        self.ctx = ctx
        self.kind = kind
        self.block_id = block_id or generate_id("blk")
        self.parent_id = parent.block_id if isinstance(parent, BlockHandle) else parent
        self.persistence = persistence
        # Use provided branch or get from context
        self.branch = branch or getattr(ctx, 'branch', None)
        # Schema version (None = auto-fill from ctx.block_schema_versions)
        self.schema_version = schema_version
    
    async def apply(self, data: dict[str, Any], **kwargs: Any) -> None:
        """Create or completely replace the Block."""
        await self.ctx.emit(BlockEvent(
            block_id=self.block_id,
            parent_id=self.parent_id,
            kind=self.kind,
            persistence=self.persistence,
            op=BlockOp.APPLY,
            data=data,
            branch=self.branch,
            schema_version=self.schema_version,
            **kwargs,
        ))
    
    async def delta(self, data: dict[str, Any]) -> None:
        """Append incremental data to the Block."""
        await self.ctx.emit(BlockEvent(
            block_id=self.block_id,
            parent_id=self.parent_id,
            kind=self.kind,
            persistence=self.persistence,
            op=BlockOp.DELTA,
            data=data,
            branch=self.branch,
            schema_version=self.schema_version,
        ))
    
    async def patch(self, data: dict[str, Any]) -> None:
        """Partially update the Block."""
        await self.ctx.emit(BlockEvent(
            block_id=self.block_id,
            parent_id=self.parent_id,
            kind=self.kind,
            persistence=self.persistence,
            op=BlockOp.PATCH,
            data=data,
            branch=self.branch,
            schema_version=self.schema_version,
        ))
    
    def child(
        self,
        kind: BlockKind | str,
        block_id: str | None = None,
        persistence: Persistence = Persistence.PERSISTENT,
        schema_version: str | None = None,
    ) -> "BlockHandle":
        """Create a child BlockHandle nested under this Block."""
        return BlockHandle(
            ctx=self.ctx,
            kind=kind,
            block_id=block_id,
            parent=self,
            persistence=persistence,
            branch=self.branch,  # Inherit branch from parent
            schema_version=schema_version,  # Child can have different schema_version
        )


# ============================================================
# Helper functions for creating BlockEvents (low-level API)
# ============================================================

def text_block(
    block_id: str | None = None,
    content: str = "",
    parent_id: str | None = None,
    session_id: str = "",
    invocation_id: str = "",
    actor: ActorInfo | None = None,
) -> BlockEvent:
    """Create a text block."""
    return BlockEvent(
        block_id=block_id or generate_id("blk"),
        parent_id=parent_id,
        kind=BlockKind.TEXT,
        op=BlockOp.APPLY,
        data={"content": content} if content else None,
        session_id=session_id,
        invocation_id=invocation_id,
        actor=actor,
    )


def text_delta(block_id: str, delta: str) -> BlockEvent:
    """Create a text block delta event."""
    return BlockEvent(
        block_id=block_id,
        kind=BlockKind.TEXT,
        op=BlockOp.DELTA,
        data={"content": delta},
    )


def thinking_block(
    block_id: str | None = None,
    content: str = "",
    parent_id: str | None = None,
    session_id: str = "",
    invocation_id: str = "",
) -> BlockEvent:
    """Create a thinking block."""
    return BlockEvent(
        block_id=block_id or generate_id("blk"),
        parent_id=parent_id,
        kind=BlockKind.THINKING,
        op=BlockOp.APPLY,
        data={"content": content} if content else None,
        session_id=session_id,
        invocation_id=invocation_id,
    )


def thinking_delta(block_id: str, delta: str) -> BlockEvent:
    """Create a thinking block delta event."""
    return BlockEvent(
        block_id=block_id,
        kind=BlockKind.THINKING,
        op=BlockOp.DELTA,
        data={"content": delta},
    )


def tool_use_block(
    block_id: str,
    name: str,
    call_id: str,
    args: dict[str, Any] | None = None,
    parent_id: str | None = None,
    session_id: str = "",
    invocation_id: str = "",
) -> BlockEvent:
    """Create a tool use block."""
    data = {"name": name, "call_id": call_id}
    if args:
        data["arguments"] = args
    return BlockEvent(
        block_id=block_id,
        parent_id=parent_id,
        kind=BlockKind.TOOL_USE,
        op=BlockOp.APPLY,
        data=data,
        session_id=session_id,
        invocation_id=invocation_id,
    )


def tool_use_patch(block_id: str, args: dict[str, Any]) -> BlockEvent:
    """Patch a tool use block with arguments."""
    return BlockEvent(
        block_id=block_id,
        kind=BlockKind.TOOL_USE,
        op=BlockOp.PATCH,
        data={"arguments": args},
    )



def error_block(
    block_id: str,
    code: str,
    message: str,
    recoverable: bool = True,
    parent_id: str | None = None,
) -> BlockEvent:
    """Create an error block."""
    return BlockEvent(
        block_id=block_id,
        parent_id=parent_id,
        kind=BlockKind.ERROR,
        op=BlockOp.APPLY,
        data={
            "code": code,
            "message": message,
            "recoverable": recoverable,
        },
    )
