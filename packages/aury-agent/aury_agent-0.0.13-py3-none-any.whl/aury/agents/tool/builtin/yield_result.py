"""Yield result tool - return control to parent agent.

Only available in DELEGATED mode sub-agents.
Dynamically injected when control is transferred.
"""
from __future__ import annotations

from typing import Any

from ...core.logging import tool_logger as logger
from ...core.types.tool import BaseTool, ToolContext, ToolResult
from ...core.types.block import BlockEvent, BlockKind, BlockOp


class YieldResultTool(BaseTool):
    """Return control to parent agent with results.
    
    This tool is only available to sub-agents running in DELEGATED mode.
    It is dynamically injected when control is transferred via delegate().
    
    When called:
    1. Pops current frame from control_stack
    2. Passes result to parent agent
    3. Resumes parent invocation
    """
    
    _name = "yield_result"
    
    def __init__(self, parent_invocation_id: str):
        """Initialize with parent context.
        
        Args:
            parent_invocation_id: ID of the parent invocation to return to
        """
        self.parent_invocation_id = parent_invocation_id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return """Return control to the parent agent with task results.

Use this when the delegated task is complete and you want to
return the results to the agent that delegated to you.

This will end your current session and resume the parent."""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Summary of what was accomplished",
                },
                "data": {
                    "type": "object",
                    "description": "Structured data to pass back to parent",
                },
                "status": {
                    "type": "string",
                    "enum": ["completed", "failed", "cancelled"],
                    "description": "Status of the delegated task",
                    "default": "completed",
                },
            },
            "required": ["result"],
        }
    
    async def execute(
        self,
        params: dict[str, Any],
        ctx: ToolContext,
    ) -> ToolResult:
        """Execute yield - return to parent."""
        result_text = params.get("result", "")
        data = params.get("data", {})
        status = params.get("status", "completed")
        invocation_id = ctx.invocation_id if ctx else None
        
        logger.info(
            f"YieldResultTool: yielding to parent, parent_invocation_id={self.parent_invocation_id}, status={status}, data_keys={list(data.keys())}, result_len={len(result_text)}, invocation_id={invocation_id}"
        )
        
        # Emit YIELD block
        await self._emit_yield_block(ctx, result_text, data, status, invocation_id)
        
        # Note: Real implementation would:
        # 1. Pop current frame from session.control_stack
        # 2. Serialize result for parent
        # 3. Update state to trigger parent resumption
        # 4. End current invocation
        
        logger.debug(f"YieldResultTool: returning to parent, invocation_id={invocation_id}")
        return ToolResult(output=f"Returning to parent agent with status: {status}\nResult: {result_text}")
    
    async def _emit_yield_block(
        self,
        ctx: ToolContext,
        result: str,
        data: dict[str, Any],
        status: str,
        invocation_id: int | None = None,
    ) -> None:
        """Emit YIELD block."""
        logger.debug(f"YieldResultTool: emitting yield block, status={status}, invocation_id={invocation_id}")
        
        block = BlockEvent(
            kind=BlockKind.YIELD,
            op=BlockOp.APPLY,
            data={
                "result": result,
                "data": data,
                "status": status,
                "parent_invocation_id": self.parent_invocation_id,
            },
            session_id=ctx.session_id,
            invocation_id=ctx.invocation_id,
        )
        
        await self.emit(block)
        logger.debug(f"YieldResultTool: yield block emitted successfully, invocation_id={invocation_id}")


__all__ = ["YieldResultTool"]
