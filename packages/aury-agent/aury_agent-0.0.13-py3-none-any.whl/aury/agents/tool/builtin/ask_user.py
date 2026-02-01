"""Ask user tool - human-in-the-loop interaction.

Enables agent to request clarification or confirmation from user.
"""
from __future__ import annotations

from typing import Any, Literal

from ...core.logging import tool_logger as logger
from ...core.types.tool import BaseTool, ToolContext, ToolResult
from ...core.types.block import BlockEvent, BlockKind, BlockOp


QuestionType = Literal["text", "confirm", "choice"]


class AskUserTool(BaseTool):
    """Request input from the user.
    
    Use this tool when you need:
    - Clarification on ambiguous requirements
    - Confirmation before destructive operations
    - User to make a choice between options
    - Additional information not available in context
    
    The tool will pause execution and wait for user response.
    """
    
    _name = "ask_user"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return """Ask the user a question and wait for their response.

Use this when you need clarification, confirmation, or additional
information from the user. Supports:
- text: Open-ended questions
- confirm: Yes/No questions  
- choice: Multiple choice selection

The conversation will pause until the user responds."""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user",
                },
                "type": {
                    "type": "string",
                    "enum": ["text", "confirm", "choice"],
                    "description": "Type of response expected",
                    "default": "text",
                },
                "choices": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Options for 'choice' type questions",
                },
                "default": {
                    "type": "string",
                    "description": "Default value if user skips",
                },
                "context": {
                    "type": "string",
                    "description": "Additional context to help user answer",
                },
            },
            "required": ["question"],
        }
    
    async def execute(
        self,
        params: dict[str, Any],
        ctx: ToolContext,
    ) -> ToolResult:
        """Execute ask - request user input."""
        question = params.get("question", "")
        q_type: QuestionType = params.get("type", "text")
        choices = params.get("choices", [])
        default = params.get("default")
        context = params.get("context")
        
        logger.info(
            "Asking user",
            extra={"question": question[:50], "type": q_type},
        )
        
        # Validate choice type has choices
        if q_type == "choice" and not choices:
            return ToolResult.error("Choice type questions require 'choices' parameter")
        
        # Emit ASK block
        await self._emit_ask_block(ctx, question, q_type, choices, default, context)
        
        # Build display output
        output_parts = [f"Question: {question}"]
        if context:
            output_parts.append(f"Context: {context}")
        if q_type == "confirm":
            output_parts.append("Type: Yes/No")
        elif q_type == "choice" and choices:
            output_parts.append("Options:")
            for i, choice in enumerate(choices, 1):
                output_parts.append(f"  {i}. {choice}")
        if default:
            output_parts.append(f"Default: {default}")
        
        # Note: Real implementation would:
        # 1. Emit HITL block/event
        # 2. Set invocation state to "waiting_for_input"
        # 3. Pause agent execution
        # 4. When user responds, resume with answer in context
        
        return ToolResult(output="\n".join(output_parts))
    
    async def _emit_ask_block(
        self,
        ctx: ToolContext,
        question: str,
        q_type: QuestionType,
        choices: list[str],
        default: str | None,
        context: str | None,
    ) -> None:
        """Emit ASK block."""
        block = BlockEvent(
            kind=BlockKind.ASK,
            op=BlockOp.APPLY,
            data={
                "question": question,
                "type": q_type,
                "choices": choices,
                "default": default,
                "context": context,
            },
            session_id=ctx.session_id,
            invocation_id=ctx.invocation_id,
        )
        
        await self.emit(block)


__all__ = ["AskUserTool"]
