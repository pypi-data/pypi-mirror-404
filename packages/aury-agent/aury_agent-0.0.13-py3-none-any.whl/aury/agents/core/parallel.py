"""Parallel execution utilities for SubAgent.

Provides utilities for parallel SubAgent execution, inspired by Google ADK.
Supports merging async generators from multiple agents.
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, TYPE_CHECKING

from .logging import context_logger as logger

if TYPE_CHECKING:
    from .types.block import BlockEvent


async def merge_agent_runs(
    agent_runs: list[AsyncGenerator["BlockEvent", None]],
) -> AsyncGenerator["BlockEvent", None]:
    """Merge multiple agent runs into a single stream.
    
    Executes agents in parallel, yielding events as they arrive.
    Each agent's events are processed sequentially to maintain order.
    
    Args:
        agent_runs: List of async generators yielding BlockEvents
        
    Yields:
        BlockEvent from any of the running agents
        
    Example:
        async def run_agent(agent, input):
            async for event in agent.run(input):
                yield event
        
        runs = [run_agent(a, "task") for a in agents]
        async for event in merge_agent_runs(runs):
            print(event)
    """
    if not agent_runs:
        logger.debug("merge_agent_runs: no agent runs provided")
        return
    
    logger.debug(f"merge_agent_runs: starting merge with {len(agent_runs)} agent runs")
    sentinel = object()
    queue: asyncio.Queue[tuple[Any, asyncio.Event | None]] = asyncio.Queue()
    
    async def process_agent(events: AsyncGenerator["BlockEvent", None], agent_idx: int) -> None:
        """Process single agent's events."""
        event_count = 0
        try:
            async for event in events:
                event_count += 1
                # Create resume signal to wait for consumer
                resume_signal = asyncio.Event()
                await queue.put((event, resume_signal))
                # Wait for upstream to consume before generating more
                await resume_signal.wait()
        finally:
            logger.debug(f"merge_agent_runs: agent #{agent_idx} completed with {event_count} events")
            # Mark this agent as finished
            await queue.put((sentinel, None))
    
    # Use TaskGroup for parallel execution (Python 3.11+)
    async with asyncio.TaskGroup() as tg:
        for idx, events in enumerate(agent_runs):
            tg.create_task(process_agent(events, idx))
        
        sentinel_count = 0
        total_events = 0
        # Run until all agents finished
        while sentinel_count < len(agent_runs):
            item, resume_signal = await queue.get()
            
            if item is sentinel:
                sentinel_count += 1
                logger.debug(f"merge_agent_runs: agent finished, {sentinel_count}/{len(agent_runs)} agents done")
            else:
                total_events += 1
                yield item
                # Signal agent to continue
                if resume_signal:
                    resume_signal.set()
    
    logger.debug(f"merge_agent_runs: merge completed, total_events={total_events}")


async def run_agents_parallel(
    agent_tasks: list[tuple[str, Any]],  # [(agent_name, input), ...]
    agent_runner: Any,  # Callable to run agent: (name, input) -> AsyncGenerator
    timeout: float | None = None,
) -> dict[str, Any]:
    """Run multiple agents in parallel and collect results.
    
    Unlike merge_agent_runs which streams events, this collects final results.
    
    Args:
        agent_tasks: List of (agent_name, input) tuples
        agent_runner: Async function to run agent
        timeout: Optional timeout in seconds
        
    Returns:
        Dict mapping agent_name to result or error
        
    Example:
        async def run_agent(name, input):
            agent = get_agent(name)
            result = []
            async for event in agent.run(input):
                if event.kind == BlockKind.TEXT:
                    result.append(event.data.get("content", ""))
            return "".join(result)
        
        results = await run_agents_parallel(
            [("researcher", "find data"), ("analyzer", "analyze")],
            run_agent,
            timeout=60.0,
        )
    """
    logger.debug(f"run_agents_parallel: starting {len(agent_tasks)} agents, timeout={timeout}")
    results: dict[str, Any] = {}
    
    async def run_one(name: str, input: Any) -> tuple[str, Any]:
        try:
            logger.debug(f"run_agents_parallel: running agent, name={name}")
            result = await agent_runner(name, input)
            logger.info(f"run_agents_parallel: agent completed, name={name}")
            return (name, result)
        except Exception as e:
            logger.error(f"run_agents_parallel: agent failed, name={name}, error={type(e).__name__}", exc_info=True)
            return (name, {"error": str(e)})
    
    tasks = [run_one(name, input) for name, input in agent_tasks]
    
    if timeout:
        try:
            logger.debug(f"run_agents_parallel: waiting for agents with timeout={timeout}s")
            completed = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"run_agents_parallel: timeout after {timeout}s, marking incomplete agents as timed out")
            # Return partial results with timeout error for incomplete
            for name, _ in agent_tasks:
                if name not in results:
                    results[name] = {"error": "timeout"}
            return results
    else:
        completed = await asyncio.gather(*tasks, return_exceptions=True)
    
    for item in completed:
        if isinstance(item, tuple):
            name, result = item
            results[name] = result
        elif isinstance(item, Exception):
            # Exception from gather
            logger.warning(f"run_agents_parallel: gathered exception: {type(item).__name__}")
    
    logger.info(f"run_agents_parallel: completed, total_agents={len(agent_tasks)}, success={len(results)}, errors={len([r for r in results.values() if isinstance(r, dict) and 'error' in r])}")
    return results


class ParallelSubAgentContext:
    """Context for tracking parallel SubAgent execution.
    
    Manages branch isolation and result collection for parallel execution.
    """
    
    def __init__(
        self,
        parent_invocation_id: str,
        session_id: str,
    ):
        self.parent_invocation_id = parent_invocation_id
        self.session_id = session_id
        self.branches: dict[str, str] = {}  # agent_name -> branch_id
        self.results: dict[str, Any] = {}
        self.errors: dict[str, str] = {}
        self._completed: set[str] = set()
    
    def create_branch(self, agent_name: str) -> str:
        """Create isolated branch for sub-agent."""
        branch_id = f"{self.parent_invocation_id}.{agent_name}"
        self.branches[agent_name] = branch_id
        logger.debug(f"ParallelSubAgentContext: created branch, agent={agent_name}, branch_id={branch_id}")
        return branch_id
    
    def mark_completed(self, agent_name: str, result: Any) -> None:
        """Mark agent as completed with result."""
        self._completed.add(agent_name)
        self.results[agent_name] = result
        logger.info(f"ParallelSubAgentContext: agent completed, agent={agent_name}, pending={len(self.pending_agents)}")
    
    def mark_failed(self, agent_name: str, error: str) -> None:
        """Mark agent as failed with error."""
        self._completed.add(agent_name)
        self.errors[agent_name] = error
        logger.warning(f"ParallelSubAgentContext: agent failed, agent={agent_name}, error={error}")
    
    @property
    def all_completed(self) -> bool:
        """Check if all agents completed."""
        return len(self._completed) == len(self.branches)
    
    @property
    def pending_agents(self) -> list[str]:
        """Get list of pending agent names."""
        return [n for n in self.branches if n not in self._completed]


__all__ = [
    "merge_agent_runs",
    "run_agents_parallel",
    "ParallelSubAgentContext",
]
