"""EditTool - Edit file contents."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from ...core.types.tool import BaseTool, ToolContext, ToolResult
from ...core.logging import tool_logger as logger


class EditTool(BaseTool):
    """Edit file contents with multiple modes."""
    
    _name = "edit"
    _description = "Edit file contents (overwrite, append, or insert at line)"
    _parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to edit",
            },
            "content": {
                "type": "string",
                "description": "Content to write",
            },
            "mode": {
                "type": "string",
                "enum": ["overwrite", "append", "insert"],
                "description": "Edit mode: overwrite (replace), append (add to end), insert (at line)",
                "default": "overwrite",
            },
            "line": {
                "type": "integer",
                "description": "Line number for insert mode (1-indexed)",
            },
            "encoding": {
                "type": "string",
                "description": "File encoding (default: utf-8)",
                "default": "utf-8",
            },
            "create_dirs": {
                "type": "boolean",
                "description": "Create parent directories if needed",
                "default": True,
            },
        },
        "required": ["path", "content"],
    }
    
    def __init__(self, allowed_paths: list[str] | None = None):
        """Initialize EditTool.
        
        Args:
            allowed_paths: List of allowed path prefixes (None = allow all)
        """
        self._allowed_paths = allowed_paths
    
    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        file_path = params.get("path", "")
        content = params.get("content", "")
        mode = params.get("mode", "overwrite")
        line = params.get("line")
        encoding = params.get("encoding", "utf-8")
        create_dirs = params.get("create_dirs", True)
        invocation_id = ctx.invocation_id if ctx else None
        
        logger.info(f"EditTool editing file, path={file_path}, mode={mode}, content_len={len(content)}, invocation_id={invocation_id}")
        
        if not file_path:
            logger.warning(f"EditTool: path is empty, invocation_id={invocation_id}")
            return ToolResult.error("Path is required")
        
        path = Path(file_path).expanduser().resolve()
        logger.debug(f"EditTool: resolved path, path={path}, invocation_id={invocation_id}")
        
        # Security check
        if self._allowed_paths:
            if not any(str(path).startswith(p) for p in self._allowed_paths):
                logger.warning(f"EditTool: path not allowed, path={path}, invocation_id={invocation_id}")
                return ToolResult.error(f"Path not allowed: {path}")
        
        try:
            # Create parent directories
            if create_dirs and not path.parent.exists():
                logger.debug(f"EditTool: creating parent directories, path={path.parent}, invocation_id={invocation_id}")
                path.parent.mkdir(parents=True, exist_ok=True)
            
            if mode == "overwrite":
                path.write_text(content, encoding=encoding)
                logger.info(f"EditTool: file overwritten, path={path}, content_len={len(content)}, invocation_id={invocation_id}")
                return ToolResult(output=f"File written ({len(content)} chars)")
            
            elif mode == "append":
                existing = path.read_text(encoding=encoding) if path.exists() else ""
                path.write_text(existing + content, encoding=encoding)
                logger.info(f"EditTool: content appended, path={path}, appended_len={len(content)}, invocation_id={invocation_id}")
                return ToolResult(output=f"Content appended ({len(content)} chars)")
            
            elif mode == "insert":
                if line is None:
                    logger.warning(f"EditTool: insert mode requires line number, invocation_id={invocation_id}")
                    return ToolResult.error("Line number required for insert mode")
                
                if path.exists():
                    lines = path.read_text(encoding=encoding).splitlines(keepends=True)
                else:
                    lines = []
                
                logger.debug(f"EditTool: read existing content, total_lines={len(lines)}, invocation_id={invocation_id}")
                
                # Pad with empty lines if needed
                while len(lines) < line - 1:
                    lines.append("\n")
                
                # Insert at position
                insert_idx = max(0, line - 1)
                content_lines = content.splitlines(keepends=True)
                if content_lines and not content_lines[-1].endswith("\n"):
                    content_lines[-1] += "\n"
                
                new_lines = lines[:insert_idx] + content_lines + lines[insert_idx:]
                path.write_text("".join(new_lines), encoding=encoding)
                
                logger.info(f"EditTool: content inserted, path={path}, line={line}, inserted_lines={len(content_lines)}, invocation_id={invocation_id}")
                return ToolResult(output=f"Content inserted at line {line} ({len(content_lines)} lines)")
            
            else:
                logger.warning(f"EditTool: unknown mode, mode={mode}, invocation_id={invocation_id}")
                return ToolResult.error(f"Unknown mode: {mode}")
            
        except Exception as e:
            logger.error(f"EditTool: edit error, error={type(e).__name__}, path={path}, mode={mode}, invocation_id={invocation_id}", exc_info=True)
            return ToolResult.error(str(e))


__all__ = ["EditTool"]
