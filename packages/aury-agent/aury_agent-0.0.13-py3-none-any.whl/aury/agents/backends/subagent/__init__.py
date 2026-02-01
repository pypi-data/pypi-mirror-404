"""SubAgent backend for sub-agent registry and retrieval.

Supports different agent retrieval strategies:
- ListSubAgentBackend: Static list of agents
- Custom backends: DB, API, dynamic discovery
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from ...core.base import BaseAgent


@dataclass
class AgentConfig:
    """Configuration for a sub-agent.
    
    行为配置:
    - inherit_messages: 是否继承父 agent 的消息历史
    - return_to_parent: 完成后是否返回结果给父 agent
    - create_invocation: 是否创建新 invocation（用户可直接交互）
    
    状态配置:
    - inherit_state: 继承哪些状态 ("all", "none", 或具体 key 列表)
    - return_state_keys: 返回哪些状态给父 agent
    - summary_mode: 返回摘要模式 ("full", "truncate", "none")
    
    手动切换配置:
    - switchable: 是否出现在前端可切换列表
    - display_name: 前端显示名称
    
    超时配置:
    - timeout: 执行超时时间（秒），收到事件时会刷新
    """
    key: str
    agent: Any  # BaseAgent instance or class
    description: str = ""
    
    # 行为配置（替代原 mode）
    inherit_messages: bool = False
    return_to_parent: bool = True
    create_invocation: bool = False
    
    # 状态配置
    inherit_state: Literal["all", "none"] | list[str] = "none"
    return_state_keys: list[str] = field(default_factory=list)
    summary_mode: Literal["full", "truncate", "none"] = "full"
    
    # 手动切换配置
    switchable: bool = False
    display_name: str = ""
    
    # 超时配置（默认 5 分钟，收到事件时刷新）
    timeout: float = 300.0
    
    # 消息记录配置（可选覆盖，默认由 return_to_parent 派生）
    # - return_to_parent=True → 不记录（消息归并到父级结果）
    # - return_to_parent=False → 记录到独立 namespace
    _record_messages: bool | None = None  # None = 用默认派生逻辑
    
    # Permission config (optional override)
    permission_config: Any | None = None
    
    @property
    def record_messages(self) -> bool:
        """是否记录消息 - 默认由 return_to_parent 派生.
        
        - return_to_parent=True → 不记录（结果归并到父级）
        - return_to_parent=False → 记录（独立运行）
        """
        if self._record_messages is not None:
            return self._record_messages
        return not self.return_to_parent
    
    @property
    def mode(self) -> Literal["embedded", "delegated"]:
        """兼容属性：根据 create_invocation 返回 mode."""
        return "delegated" if self.create_invocation else "embedded"
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "agent_name": getattr(self.agent, "name", str(self.agent)),
            "mode": self.mode,
            "description": self.description or getattr(self.agent, "description", ""),
            "inherit_messages": self.inherit_messages,
            "return_to_parent": self.return_to_parent,
            "create_invocation": self.create_invocation,
            "switchable": self.switchable,
            "display_name": self.display_name,
        }


@runtime_checkable
class SubAgentBackend(Protocol):
    """Protocol for sub-agent retrieval."""
    
    async def get(self, key: str) -> AgentConfig | None:
        """Get agent config by key."""
        ...
    
    async def list(self) -> list[AgentConfig]:
        """List all available agents."""
        ...


class ListSubAgentBackend:
    """Default implementation: Static list of agents."""
    
    def __init__(self, agents: list[AgentConfig] | None = None):
        self._agents: dict[str, AgentConfig] = {}
        if agents:
            for config in agents:
                self._agents[config.key] = config
    
    def register(self, config: AgentConfig) -> None:
        """Register an agent config."""
        self._agents[config.key] = config
    
    def register_agent(
        self,
        key: str,
        agent: Any,
        description: str = "",
        *,
        inherit_messages: bool = False,
        return_to_parent: bool = True,
        create_invocation: bool = False,
        switchable: bool = False,
        display_name: str = "",
    ) -> None:
        """Convenience method to register an agent."""
        self._agents[key] = AgentConfig(
            key=key,
            agent=agent,
            description=description or getattr(agent, "description", ""),
            inherit_messages=inherit_messages,
            return_to_parent=return_to_parent,
            create_invocation=create_invocation,
            switchable=switchable,
            display_name=display_name,
        )
    
    async def get(self, key: str) -> AgentConfig | None:
        return self._agents.get(key)
    
    async def list(self) -> list[AgentConfig]:
        return list(self._agents.values())
    
    def list_sync(self) -> list[AgentConfig]:
        """Synchronous version of list() for use in property getters."""
        return list(self._agents.values())
    
    def clear(self) -> None:
        """Clear all agents."""
        self._agents.clear()


__all__ = [
    "SubAgentBackend",
    "AgentConfig", 
    "ListSubAgentBackend",
]
