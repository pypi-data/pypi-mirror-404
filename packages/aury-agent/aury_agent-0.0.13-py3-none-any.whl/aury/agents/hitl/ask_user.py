"""AskUser tool for LLM to request human input.

This tool allows the LLM to pause execution and ask the user
for clarification or additional information.
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ..tool import BaseTool, ToolResult
from ..core.types.session import generate_id
from ..core.types.block import BlockEvent
from ..core.signals import HITLSuspend
from .exceptions import HITLRequest

if TYPE_CHECKING:
    from ..core.context import InvocationContext


class AskUserTool(BaseTool):
    """Tool for LLM to ask user questions.
    
    When executed, this tool:
    1. Checkpoints current state
    2. Updates invocation status to SUSPENDED
    3. Emits a hitl_request block to frontend
    4. Raises HITLSuspend signal to pause execution
    
    The user's response comes via:
    - agent.respond(request_id, response)
    - agent.run(response) (auto-detects suspended state)
    
    Note: Uses HITLSuspend (inherits BaseException) so it won't be caught
    by generic `except Exception` handlers.
    """
    
    _name = "ask_user"
    _description = "Ask the user for clarification or additional information. Use this when you need more details to complete a task."
    _parameters = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to ask the user",
            },
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of suggested answers",
            },
            "context": {
                "type": "string",
                "description": "Additional context about why you're asking",
            },
        },
        "required": ["question"],
    }
    
    async def execute(
        self,
        question: str,
        options: list[str] | None = None,
        context: str | None = None,
        *,
        ctx: "InvocationContext | None" = None,
    ) -> ToolResult:
        """Execute ask_user tool.
        
        This method does NOT return normally - it raises HITLSuspend
        to pause the agent execution.
        
        Args:
            question: Question to ask the user
            options: Optional predefined answer options
            context: Additional context
            ctx: Invocation context (injected by agent)
            
        Returns:
            Never returns normally
            
        Raises:
            HITLSuspend: Always raised to suspend execution
        """
        if ctx is None:
            # If no context, return error (should not happen in normal use)
            return ToolResult.error("Cannot ask user without execution context")
        
        from ..core.logging import tool_logger as logger
        
        # Generate HITL ID
        hitl_id = generate_id("hitl")
        logger.info(
            "ask_user HITL request",
            extra={
                "invocation_id": ctx.invocation_id,
                "hitl_id": hitl_id,
                "question": question[:100],
                "has_options": options is not None,
            },
        )
        
        # Create HITL request data
        request = HITLRequest(
            hitl_id=hitl_id,
            hitl_type="ask_user",
            data={"message": question, "options": options},
            tool_name=self._name,
            metadata={"context": context} if context else {},
        )
        
        # Checkpoint current state
        if hasattr(ctx, "state") and ctx.state is not None:
            logger.debug(
                "Checkpointing state before HITL suspend",
                extra={"invocation_id": ctx.invocation_id},
            )
            await ctx.state.checkpoint()
        
        # Update invocation status to SUSPENDED
        if ctx.backends and ctx.backends.invocation:
            await ctx.backends.invocation.update(ctx.invocation_id, {
                "status": "suspended",
            })
        
        # Store HITL record
        if ctx.backends and ctx.backends.hitl:
            await ctx.backends.hitl.create(
                hitl_id=hitl_id,
                hitl_type="ask_user",
                session_id=ctx.session_id,
                invocation_id=ctx.invocation_id,
                data={"message": question, "options": options},
                metadata={"context": context} if context else None,
                tool_name=self._name,
            )
        
        # Emit HITL block to frontend
        await ctx.emit(BlockEvent(
            kind="hitl",
            data={
                "hitl_id": hitl_id,
                "hitl_type": "ask_user",
                "message": question,
                "options": options,
                "context": context,
            },
        ))
        
        # Raise signal to suspend execution
        logger.info(
            "Suspending execution for HITL ask_user",
            extra={
                "invocation_id": ctx.invocation_id,
                "hitl_id": hitl_id,
            },
        )
        raise HITLSuspend(
            hitl_id=hitl_id,
            hitl_type="ask_user",
            data={"message": question, "options": options},
            tool_name=self._name,
            metadata={"context": context} if context else {},
        )


class ConfirmTool(BaseTool):
    """Tool for LLM to request confirmation before proceeding.
    
    Similar to ask_user but specifically for yes/no confirmations.
    """
    
    _name = "confirm"
    _description = "Ask the user to confirm an action before proceeding."
    _parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The action you want to perform",
            },
            "details": {
                "type": "string",
                "description": "Details about the action",
            },
            "risk_level": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Risk level of the action",
            },
        },
        "required": ["action"],
    }
    
    async def execute(
        self,
        action: str,
        details: str | None = None,
        risk_level: str = "medium",
        *,
        ctx: "InvocationContext | None" = None,
    ) -> ToolResult:
        """Execute confirm tool.
        
        Args:
            action: Action to confirm
            details: Additional details
            risk_level: Risk level (low, medium, high)
            ctx: Invocation context
            
        Raises:
            HITLSuspend: Always raised to suspend execution
        """
        if ctx is None:
            return ToolResult.error("Cannot confirm without execution context")
        
        from ..core.logging import tool_logger as logger
        
        hitl_id = generate_id("hitl")
        logger.info(
            "confirm HITL request",
            extra={
                "invocation_id": ctx.invocation_id,
                "hitl_id": hitl_id,
                "action": action[:100],
                "risk_level": risk_level,
            },
        )
        
        message = f"Confirm: {action}"
        if details:
            message += f"\n\nDetails: {details}"
        
        hitl_data = {
            "message": message,
            "options": ["Yes, proceed", "No, cancel"],
            "action": action,
            "details": details,
            "risk_level": risk_level,
        }
        
        request = HITLRequest(
            hitl_id=hitl_id,
            hitl_type="confirm",
            data=hitl_data,
            tool_name=self._name,
        )
        
        # Checkpoint
        if hasattr(ctx, "state") and ctx.state is not None:
            logger.debug(
                "Checkpointing state before confirm suspend",
                extra={"invocation_id": ctx.invocation_id},
            )
            await ctx.state.checkpoint()
        
        # Update invocation
        if ctx.backends and ctx.backends.invocation:
            await ctx.backends.invocation.update(ctx.invocation_id, {
                "status": "suspended",
            })
        
        # Store HITL record
        if ctx.backends and ctx.backends.hitl:
            await ctx.backends.hitl.create(
                hitl_id=hitl_id,
                hitl_type="confirm",
                session_id=ctx.session_id,
                invocation_id=ctx.invocation_id,
                data=hitl_data,
                tool_name=self._name,
            )
        
        # Emit block
        await ctx.emit(BlockEvent(
            kind="hitl",
            data={
                "hitl_id": hitl_id,
                "hitl_type": "confirm",
                **hitl_data,
            },
        ))
        
        logger.info(
            "Suspending execution for confirm",
            extra={
                "invocation_id": ctx.invocation_id,
                "hitl_id": hitl_id,
            },
        )
        raise HITLSuspend(
            hitl_id=hitl_id,
            hitl_type="confirm",
            data=hitl_data,
            tool_name=self._name,
        )


__all__ = ["AskUserTool", "ConfirmTool"]
