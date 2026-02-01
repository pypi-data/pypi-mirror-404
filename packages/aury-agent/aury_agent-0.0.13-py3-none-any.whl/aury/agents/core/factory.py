"""Agent factory for creating agent instances.

Provides unified creation of both ReactAgent and WorkflowAgent:
    factory = AgentFactory()
    factory.register("researcher", ResearcherAgent)  # ReactAgent subclass
    factory.register("pipeline", PipelineWorkflow)   # WorkflowAgent subclass
    
    agent = factory.create("researcher", ctx)  # Works for both types
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .base import AgentConfig
from .logging import context_logger as logger

if TYPE_CHECKING:
    from .base import BaseAgent
    from .context import InvocationContext


class AgentFactory:
    """Factory for creating agent instances.
    
    Unified factory for both ReactAgent and WorkflowAgent.
    All agents use the same constructor:
        __init__(self, ctx: InvocationContext, config: AgentConfig | None = None)
    
    Usage:
        factory = AgentFactory()
        
        # Register agent classes
        factory.register("researcher", ResearcherAgent)
        factory.register("coder", CoderAgent)
        factory.register("pipeline", PipelineWorkflow)
        
        # Create agents
        agent = factory.create("researcher", ctx)
        agent = factory.create("researcher", ctx, config=custom_config)
        
        # Auto-register from class
        factory.register_class(ResearcherAgent)  # Uses class.name
    """
    
    def __init__(self):
        self._registry: dict[str, type["BaseAgent"]] = {}
    
    def register(self, name: str, agent_class: type["BaseAgent"]) -> None:
        """Register an agent class with a name.
        
        Args:
            name: Name to register under
            agent_class: Agent class (must have unified constructor)
        """
        logger.debug(f"AgentFactory.register: registering agent, name={name}, class={agent_class.__name__}")
        self._registry[name] = agent_class
    
    def register_class(self, agent_class: type["BaseAgent"]) -> None:
        """Register an agent class using its class-level name.
        
        Args:
            agent_class: Agent class with 'name' class attribute
        """
        name = getattr(agent_class, 'name', agent_class.__name__)
        logger.debug(f"AgentFactory.register_class: registering agent, name={name}, class={agent_class.__name__}")
        self._registry[name] = agent_class
    
    def register_all(self, *agent_classes: type["BaseAgent"]) -> None:
        """Register multiple agent classes.
        
        Args:
            agent_classes: Agent classes with 'name' class attribute
        """
        logger.debug(f"AgentFactory.register_all: registering {len(agent_classes)} agents")
        for agent_class in agent_classes:
            self.register_class(agent_class)
    
    def create(
        self,
        agent_type: str,
        ctx: "InvocationContext",
        config: AgentConfig | None = None,
    ) -> "BaseAgent":
        """Create an agent instance.
        
        All agents are created with the same signature:
            agent = AgentClass(ctx, config)
        
        Args:
            agent_type: Registered agent type name
            ctx: InvocationContext with all services
            config: Agent configuration (optional)
            
        Returns:
            Agent instance (ReactAgent or WorkflowAgent)
            
        Raises:
            KeyError: If agent type not registered
        """
        if agent_type not in self._registry:
            available = ", ".join(self._registry.keys()) or "none"
            logger.error(f"AgentFactory.create: unknown agent type, type={agent_type}, available={available}, invocation_id={ctx.invocation_id}")
            raise KeyError(
                f"Unknown agent type: {agent_type}. Available: {available}"
            )
        
        agent_class = self._registry[agent_type]
        logger.debug(f"AgentFactory.create: creating agent, type={agent_type}, class={agent_class.__name__}, invocation_id={ctx.invocation_id}")
        return agent_class(ctx, config)
    
    def create_subagent(
        self,
        agent_type: str,
        parent_ctx: "InvocationContext",
        mode: str = "delegated",
        config: AgentConfig | None = None,
    ) -> "BaseAgent":
        """Create a sub-agent with child context.
        
        Convenience method that creates child context and agent.
        
        Args:
            agent_type: Registered agent type name
            parent_ctx: Parent's InvocationContext
            mode: Execution mode ('delegated' or 'embedded')
            config: Agent configuration (optional)
            
        Returns:
            Agent instance with child context
        """
        logger.debug(f"AgentFactory.create_subagent: creating subagent, type={agent_type}, mode={mode}, parent_invocation_id={parent_ctx.invocation_id}")
        
        # Get agent name from class if available
        agent_class = self._registry.get(agent_type)
        agent_name = getattr(agent_class, 'name', agent_type) if agent_class else agent_type
        
        child_ctx = parent_ctx.create_child(agent_id=agent_type, agent_name=agent_name, mode=mode)
        logger.debug(f"AgentFactory.create_subagent: child context created, child_invocation_id={child_ctx.invocation_id}")
        return self.create(agent_type, child_ctx, config)
    
    def list_types(self) -> list[str]:
        """List registered agent types."""
        return list(self._registry.keys())
    
    def get_class(self, agent_type: str) -> type["BaseAgent"] | None:
        """Get agent class by type name."""
        return self._registry.get(agent_type)
    
    def is_registered(self, agent_type: str) -> bool:
        """Check if agent type is registered."""
        return agent_type in self._registry
    
    def get_info(self, agent_type: str) -> dict[str, Any] | None:
        """Get agent info (name, description, type).
        
        Returns:
            Dict with name, description, agent_type, or None if not found
        """
        agent_class = self._registry.get(agent_type)
        if agent_class is None:
            return None
        
        return {
            "name": getattr(agent_class, 'name', agent_type),
            "description": getattr(agent_class, 'description', ''),
            "agent_type": getattr(agent_class, 'agent_type', 'react'),
            "sub_agents": [
                getattr(sa, 'name', sa.__name__)
                for sa in getattr(agent_class, 'sub_agents', [])
            ],
        }
    
    def list_info(self) -> list[dict[str, Any]]:
        """List info for all registered agents."""
        return [
            self.get_info(name)
            for name in self._registry.keys()
            if self.get_info(name) is not None
        ]


__all__ = ["AgentFactory"]
