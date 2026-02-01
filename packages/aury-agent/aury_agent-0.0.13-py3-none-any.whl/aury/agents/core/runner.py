"""Runner - Entry point coordinator for agent execution.

The Runner handles:
- Creating InvocationContext from Session/Invocation
- Managing the execution lifecycle
- Coordinating services (Session, Message, Storage)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, AsyncIterator, TYPE_CHECKING

from .context import InvocationContext
from .logging import logger

if TYPE_CHECKING:
    from .base import BaseAgent
    from .types.block import BlockEvent
    from .services.session import SessionService
    from .services.message import MessageService
    from ..backends import Backends
    from .event_bus import Bus
    from ..types import PromptInput


class Runner:
    """Entry point for agent execution.
    
    Coordinates the execution lifecycle:
    1. Get or create session
    2. Create invocation
    3. Build InvocationContext
    4. Execute agent
    5. Handle completion/errors
    
    Example:
        runner = Runner(
            session_service=session_service,
            message_service=message_service,
            backends=backends,
            bus=bus,
        )
        
        async for response in runner.run(
            agent_class=MyAgent,
            session_id="sess_123",
            input=PromptInput(text="Hello"),
        ):
            print(response)
    """
    
    def __init__(
        self,
        session_service: "SessionService",
        message_service: "MessageService",
        backends: "Backends",
        bus: "Bus",
    ):
        self.session_service = session_service
        self.message_service = message_service
        self.backends = backends
        self.bus = bus
    
    async def run(
        self,
        agent_class: type["BaseAgent"],
        session_id: str | None = None,
        input: "PromptInput | None" = None,
        **agent_kwargs: Any,
    ) -> AsyncIterator["BlockEvent"]:
        """Run an agent.
        
        Args:
            agent_class: Agent class to instantiate
            session_id: Existing session ID (creates new if None)
            input: Input to agent
            **agent_kwargs: Additional args for agent constructor
            
        Yields:
            BlockEvent streaming events
        """
        from ..types import generate_id, Invocation, InvocationState
        
        # Get or create session
        if session_id:
            session = await self.session_service.get(session_id)
            if session is None:
                raise ValueError(f"Session not found: {session_id}")
        else:
            agent_name = getattr(agent_class, 'name', agent_class.__name__)
            session = await self.session_service.create(root_agent_id=agent_name)
        
        logger.info(f"Starting agent execution: session={session.id}")
        
        # Create invocation
        invocation = Invocation(
            id=generate_id("inv"),
            session_id=session.id,
            agent_id=getattr(agent_class, 'name', agent_class.__name__),
            state=InvocationState.RUNNING,
            started_at=datetime.now(),
        )
        
        # Build context
        ctx = InvocationContext(
            session_id=session.id,
            invocation_id=invocation.id,
            agent_id=invocation.agent_id,
            backends=self.backends,
            bus=self.bus,
        )
        
        # Create agent instance
        agent = agent_class(
            ctx=ctx,
            **agent_kwargs,
        )
        
        try:
            # Execute
            async for response in agent.run(input):
                yield response
            
            invocation.state = InvocationState.COMPLETED
            logger.info(f"Agent completed: invocation={invocation.id}")
            
        except Exception as e:
            invocation.state = InvocationState.FAILED
            logger.error(f"Agent failed: invocation={invocation.id}, error={e}")
            raise
        
        finally:
            invocation.finished_at = datetime.now()
            # Persist invocation
            if self.backends.state:
                await self.backends.state.set("invocation", invocation.id, invocation.__dict__)


__all__ = ["Runner"]
