"""Thinking tool - emit reasoning process.

Allows agent to externalize its thinking/reasoning process.
Useful for transparency, debugging, and chain-of-thought.
"""
from __future__ import annotations

from typing import Any

from ...core.logging import tool_logger as logger
from ...core.types.tool import BaseTool, ToolContext, ToolResult
from ...core.types.block import BlockEvent, BlockKind, BlockOp


class ThinkingTool(BaseTool):
    """Emit thinking/reasoning process.
    
    Use this tool to externalize your reasoning:
    - Breaking down complex problems
    - Weighing options and trade-offs
    - Planning approach before acting
    - Explaining decision rationale
    
    This creates a THINKING block in the output stream,
    making reasoning visible to users and useful for debugging.
    """
    
    _name = "thinking"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return """Emit your thinking/reasoning process.

Use this to externalize your thought process:
- Analyzing a problem
- Weighing options
- Planning an approach
- Explaining decisions

This makes your reasoning visible and traceable."""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "Your thinking/reasoning content",
                },
                "category": {
                    "type": "string",
                    "enum": ["analysis", "planning", "decision", "reflection", "observation"],
                    "description": "Category of thinking",
                    "default": "analysis",
                },
            },
            "required": ["thought"],
        }
    
    async def execute(
        self,
        params: dict[str, Any],
        ctx: ToolContext,
    ) -> ToolResult:
        """Execute thinking - emit reasoning block."""
        thought = params.get("thought", "")
        category = params.get("category", "analysis")
        invocation_id = ctx.invocation_id if ctx else None
        
        logger.info(
            f"ThinkingTool processing, category={category}, thought_len={len(thought)}, invocation_id={invocation_id}"
        )
        
        # Emit THINKING block
        await self._emit_thinking_block(ctx, thought, category, invocation_id)
        
        # Thinking doesn't produce actionable output
        # It's purely for transparency/logging
        logger.debug(f"ThinkingTool completed, invocation_id={invocation_id}")
        return ToolResult(output=thought)
    
    async def _emit_thinking_block(
        self,
        ctx: ToolContext,
        thought: str,
        category: str,
        invocation_id: int | None = None,
    ) -> None:
        """Emit THINKING block."""
        logger.debug(f"ThinkingTool: emitting block, category={category}, invocation_id={invocation_id}")
        
        block = BlockEvent(
            kind=BlockKind.THINKING,
            op=BlockOp.APPLY,
            data={
                "thought": thought,
                "category": category,
            },
            session_id=ctx.session_id,
            invocation_id=ctx.invocation_id,
        )
        
        await self.emit(block)
        logger.debug(f"ThinkingTool: block emitted successfully, invocation_id={invocation_id}")


__all__ = ["ThinkingTool"]
