"""Plan tool - manage execution plan with checklist.

Emits PLAN block and manages plan state.
Combines planning (design) and tracking (checklist) in one tool.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from ...core.types.tool import BaseTool, ToolContext, ToolResult
from ...core.types.block import BlockEvent, BlockKind, BlockOp
from ...core.types.session import generate_id


class PlanTool(BaseTool):
    """Manage execution plan with checklist.
    
    Actions:
    - create: Create new plan with items
    - add: Add item to existing plan
    - check: Mark item as done
    - uncheck: Mark item as pending
    - update: Update plan title/summary
    - view: View current plan
    """
    
    _name = "plan"
    _description = """Manage your execution plan.

Actions:
- create: Create a new plan with checklist items
- add: Add an item to the plan
- check: Mark an item as completed
- uncheck: Mark an item as pending
- update: Update plan title or summary
- view: View current plan status

Use this to track your progress on complex tasks."""

    _parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "add", "check", "uncheck", "update", "view"],
                "description": "Action to perform",
            },
            "title": {
                "type": "string",
                "description": "Plan title (for create/update)",
            },
            "summary": {
                "type": "string",
                "description": "Plan summary/notes (for create/update)",
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "note": {"type": "string"},
                    },
                    "required": ["title"],
                },
                "description": "Checklist items (for create)",
            },
            "item": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "note": {"type": "string"},
                },
                "description": "Single item to add (for add)",
            },
            "item_id": {
                "type": "string",
                "description": "Item ID (for check/uncheck)",
            },
        },
        "required": ["action"],
    }
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters
    
    async def execute(
        self,
        params: dict[str, Any],
        ctx: ToolContext,
    ) -> ToolResult:
        """Execute plan action."""
        from ...core.logging import tool_logger as logger
        
        action = params.get("action", "view")
        logger.info(
            f"Plan tool action: {action}",
            extra={
                "invocation_id": ctx.invocation_id,
                "session_id": ctx.session_id,
            },
        )
        
        # Storage key
        key = f"plan:{ctx.session_id}"
        
        # Get storage
        storage = getattr(ctx, 'storage', None)
        if storage is None:
            return ToolResult.error("Storage not configured")
        
        # Load current plan
        plan = await storage.get("plan", key) or self._empty_plan()
        
        # Execute action
        if action == "create":
            plan = await self._create(params, plan)
        elif action == "add":
            plan = await self._add(params, plan)
        elif action == "check":
            plan = await self._check(params, plan, done=True)
        elif action == "uncheck":
            plan = await self._check(params, plan, done=False)
        elif action == "update":
            plan = await self._update(params, plan)
        elif action == "view":
            pass  # Just return current plan
        else:
            return ToolResult.error(f"Unknown action: {action}")
        
        # Save plan
        await storage.set("plan", key, plan)
        
        from ...core.logging import tool_logger as logger
        logger.debug(
            f"Plan updated",
            extra={
                "action": action,
                "status": plan.get("status"),
                "item_count": len(plan.get("items", [])),
            },
        )
        
        # Emit PLAN block
        await self._emit_plan_block(ctx, plan, action)
        
        # Format output
        output = self._format_plan(plan)
        
        return ToolResult(output=output)
    
    def _empty_plan(self) -> dict[str, Any]:
        """Create empty plan structure."""
        return {
            "block_id": None,  # Block ID for emit
            "title": "",
            "summary": "",
            "status": "draft",
            "items": [],
        }
    
    async def _create(self, params: dict[str, Any], plan: dict) -> dict:
        """Create new plan."""
        plan = {
            "block_id": generate_id("blk"),  # New block_id for new plan
            "title": params.get("title", "Execution Plan"),
            "summary": params.get("summary", ""),
            "status": "in_progress",
            "items": [],
        }
        
        items = params.get("items", [])
        for item in items:
            plan["items"].append({
                "id": str(uuid4())[:8],
                "title": item.get("title", ""),
                "note": item.get("note", ""),
                "status": "pending",
            })
        
        return plan
    
    async def _add(self, params: dict[str, Any], plan: dict) -> dict:
        """Add item to plan."""
        item = params.get("item", {})
        if not item.get("title"):
            item = {"title": params.get("title", ""), "note": params.get("note", "")}
        
        if not item.get("title"):
            raise ValueError("Item title is required")
        
        plan["items"].append({
            "id": str(uuid4())[:8],
            "title": item.get("title", ""),
            "note": item.get("note", ""),
            "status": "pending",
        })
        
        if plan["status"] == "draft":
            plan["status"] = "in_progress"
        
        return plan
    
    async def _check(self, params: dict[str, Any], plan: dict, done: bool) -> dict:
        """Mark item as done/pending."""
        item_id = params.get("item_id", "")
        
        for item in plan["items"]:
            if item["id"] == item_id:
                item["status"] = "done" if done else "pending"
                break
        
        # Update plan status if all done
        if all(i["status"] == "done" for i in plan["items"]) and plan["items"]:
            plan["status"] = "done"
        elif any(i["status"] == "done" for i in plan["items"]):
            plan["status"] = "in_progress"
        
        return plan
    
    async def _update(self, params: dict[str, Any], plan: dict) -> dict:
        """Update plan metadata."""
        if "title" in params:
            plan["title"] = params["title"]
        if "summary" in params:
            plan["summary"] = params["summary"]
        return plan
    
    async def _emit_plan_block(self, ctx: ToolContext, plan: dict, action: str) -> None:
        """Emit PLAN block event."""
        # Get or generate block_id
        block_id = plan.get("block_id")
        if not block_id:
            block_id = generate_id("blk")
            plan["block_id"] = block_id
        
        op = BlockOp.APPLY if action == "create" else BlockOp.PATCH
        
        # Don't include block_id in data (it's metadata)
        data = {k: v for k, v in plan.items() if k != "block_id"}
        
        block = BlockEvent(
            block_id=block_id,
            kind=BlockKind.PLAN,
            op=op,
            data=data,
            session_id=ctx.session_id,
            invocation_id=ctx.invocation_id,
        )
        
        await self.emit(block)
    
    def _format_plan(self, plan: dict) -> str:
        """Format plan as text."""
        lines = []
        
        if plan["title"]:
            lines.append(f"# {plan['title']}")
        
        if plan["summary"]:
            lines.append(f"\n{plan['summary']}")
        
        lines.append(f"\nStatus: {plan['status']}")
        
        if plan["items"]:
            lines.append("\nChecklist:")
            for item in plan["items"]:
                icon = "✓" if item["status"] == "done" else "○"
                line = f"  [{icon}] {item['title']}"
                if item.get("note"):
                    line += f" - {item['note']}"
                line += f" (id: {item['id']})"
                lines.append(line)
        
        pending = sum(1 for i in plan["items"] if i["status"] == "pending")
        done = sum(1 for i in plan["items"] if i["status"] == "done")
        lines.append(f"\nProgress: {done}/{len(plan['items'])} completed")
        
        return "\n".join(lines)


__all__ = ["PlanTool"]
