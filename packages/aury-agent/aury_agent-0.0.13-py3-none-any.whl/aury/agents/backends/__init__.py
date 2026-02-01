"""Backend protocols and implementations.

Backends provide abstracted interfaces for various capabilities:

Data Backends (storage):
- SessionBackend: Session management
- InvocationBackend: Invocation management
- MessageBackend: Message storage
- MemoryBackend: Long-term memory with search
- ArtifactBackend: File/artifact storage
- StateBackend: Generic key-value state

Capability Backends:
- SnapshotBackend: File state tracking and revert
- ShellBackend: Shell command execution
- FileBackend: File system operations
- CodeBackend: Code execution
- SubAgentBackend: Sub-agent registry and retrieval

Backends Container:
- Backends: Dataclass container for dependency injection
"""
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# Data backends - new architecture
from .session import SessionBackend, InMemorySessionBackend
from .invocation import InvocationBackend, InMemoryInvocationBackend
from .message import MessageBackend, InMemoryMessageBackend
from .memory import MemoryBackend, InMemoryMemoryBackend
from .artifact import ArtifactBackend, ArtifactSource, InMemoryArtifactBackend
from .hitl import HITLBackend, InMemoryHITLBackend

# State backend - simplified to key-value
from .state import StateBackend, StateStore, StoreBasedStateBackend, SQLiteStateBackend, MemoryStateBackend, FileStateBackend, CompositeStateBackend

# Capability backends - existing
from .snapshot import SnapshotBackend, Patch, InMemorySnapshotBackend, GitSnapshotBackend, GitS3HybridBackend
from .shell import ShellBackend, ShellResult, LocalShellBackend
from .file import FileBackend, LocalFileBackend
from .code import CodeBackend, CodeResult
from .subagent import SubAgentBackend, AgentConfig, ListSubAgentBackend
from .sandbox import SandboxShellBackend, SandboxCodeBackend


@dataclass
class Backends:
    """Container for all backends.
    
    Provides a unified way to inject backends into agents and context.
    
    Data backends (for storage):
    - session: Session management (required)
    - invocation: Invocation management (required)
    - message: Message storage (required)
    - memory: Long-term memory (optional)
    - artifact: Artifact storage (optional)
    - state: Generic key-value state (optional)
    
    Capability backends (for actions):
    - snapshot: File tracking and revert (optional)
    - shell: Shell execution (optional)
    - file: File operations (optional)
    - code: Code execution (optional)
    - subagent: Sub-agent registry (optional)
    
    Example:
        # Create with defaults
        backends = Backends.create_default()
        
        # Create with custom implementations
        backends = Backends(
            session=DatabaseSessionBackend(db),
            invocation=DatabaseInvocationBackend(db),
            message=DatabaseMessageBackend(db),
            memory=VectorMemoryBackend(embedding_model),
        )
        
        # Use in agent
        agent = ReactAgent.create(llm=llm, backends=backends)
    """
    # Data backends - required
    session: SessionBackend
    invocation: InvocationBackend
    message: MessageBackend
    
    # Data backends - optional
    memory: MemoryBackend | None = None
    artifact: ArtifactBackend | None = None
    state: StateBackend | None = None
    hitl: HITLBackend | None = None
    
    # Capability backends - optional
    snapshot: SnapshotBackend | None = None
    shell: ShellBackend | None = None
    file: FileBackend | None = None
    code: CodeBackend | None = None
    subagent: SubAgentBackend | None = None
    
    @classmethod
    def create_default(cls) -> "Backends":
        """Create Backends with default in-memory implementations.
        
        Suitable for testing and simple single-process use cases.
        """
        return cls(
            session=InMemorySessionBackend(),
            invocation=InMemoryInvocationBackend(),
            message=InMemoryMessageBackend(),
            memory=InMemoryMemoryBackend(),
            artifact=InMemoryArtifactBackend(),
            state=MemoryStateBackend(),
            hitl=InMemoryHITLBackend(),
        )
    
    @classmethod
    def create_sqlite(cls, db_path: str = "./data/agent.db") -> "Backends":
        """Create Backends with SQLite storage.
        
        Uses SQLite for state backend, in-memory for others.
        For production, implement database backends.
        
        Args:
            db_path: Path to SQLite database file
        """
        return cls(
            session=InMemorySessionBackend(),
            invocation=InMemoryInvocationBackend(),
            message=InMemoryMessageBackend(),
            memory=InMemoryMemoryBackend(),
            artifact=InMemoryArtifactBackend(),
            state=SQLiteStateBackend(db_path),
            hitl=InMemoryHITLBackend(),
        )


__all__ = [
    # Backends container
    "Backends",
    
    # Session backend
    "SessionBackend",
    "InMemorySessionBackend",
    
    # Invocation backend
    "InvocationBackend",
    "InMemoryInvocationBackend",
    
    # Message backend
    "MessageBackend",
    "InMemoryMessageBackend",
    
    # Memory backend
    "MemoryBackend",
    "InMemoryMemoryBackend",
    
    # Artifact backend
    "ArtifactBackend",
    "ArtifactSource",
    "InMemoryArtifactBackend",
    
    # HITL backend
    "HITLBackend",
    "InMemoryHITLBackend",
    
    # State backend (key-value)
    "StateBackend",
    "StateStore",
    "StoreBasedStateBackend",
    "SQLiteStateBackend",
    "MemoryStateBackend",
    "FileStateBackend",
    "CompositeStateBackend",
    
    # Snapshot backend
    "SnapshotBackend",
    "Patch",
    "InMemorySnapshotBackend",
    "GitSnapshotBackend",
    "GitS3HybridBackend",
    
    # Shell backend
    "ShellBackend",
    "ShellResult",
    "LocalShellBackend",
    
    # File backend
    "FileBackend",
    "LocalFileBackend",
    
    # Code backend
    "CodeBackend",
    "CodeResult",
    
    # SubAgent backend
    "SubAgentBackend",
    "AgentConfig",
    "ListSubAgentBackend",
    
    # Sandbox backends
    "SandboxShellBackend",
    "SandboxCodeBackend",
]
