"""ReadTool - Read file contents."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ...core.types.tool import BaseTool, ToolContext, ToolResult
from ...core.logging import tool_logger as logger


class ReadTool(BaseTool):
    """Read file contents with optional line range."""
    
    _name = "read"
    _description = "Read file contents, optionally specifying line range"
    _parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read",
            },
            "start_line": {
                "type": "integer",
                "description": "Start line number (1-indexed, optional)",
            },
            "end_line": {
                "type": "integer",
                "description": "End line number (inclusive, optional)",
            },
            "encoding": {
                "type": "string",
                "description": "File encoding (default: utf-8)",
                "default": "utf-8",
            },
        },
        "required": ["path"],
    }
    
    def __init__(self, allowed_paths: list[str] | None = None):
        """Initialize ReadTool.
        
        Args:
            allowed_paths: List of allowed path prefixes (None = allow all)
        """
        self._allowed_paths = allowed_paths
    
    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        file_path = params.get("path", "")
        start_line = params.get("start_line")
        end_line = params.get("end_line")
        encoding = params.get("encoding", "utf-8")
        invocation_id = ctx.invocation_id if ctx else None
        
        logger.info(f"ReadTool reading file, path={file_path}, start_line={start_line}, end_line={end_line}, invocation_id={invocation_id}")
        
        if not file_path:
            logger.warning(f"ReadTool: path is empty, invocation_id={invocation_id}")
            return ToolResult.error("Path is required")
        
        path = Path(file_path).expanduser().resolve()
        logger.debug(f"ReadTool: resolved path, path={path}, invocation_id={invocation_id}")
        
        # Security check
        if self._allowed_paths:
            if not any(str(path).startswith(p) for p in self._allowed_paths):
                logger.warning(f"ReadTool: path not allowed, path={path}, invocation_id={invocation_id}")
                return ToolResult.error(f"Path not allowed: {path}")
        
        if not path.exists():
            logger.warning(f"ReadTool: file not found, path={path}, invocation_id={invocation_id}")
            return ToolResult.error(f"File not found: {path}")
        
        if not path.is_file():
            logger.warning(f"ReadTool: not a file, path={path}, invocation_id={invocation_id}")
            return ToolResult.error(f"Not a file: {path}")
        
        try:
            content = path.read_text(encoding=encoding)
            lines = content.splitlines(keepends=True)
            logger.debug(f"ReadTool: read file, total_lines={len(lines)}, invocation_id={invocation_id}")
            
            # Apply line range
            if start_line is not None or end_line is not None:
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else len(lines)
                lines = lines[start_idx:end_idx]
                logger.debug(f"ReadTool: applied line range, start_idx={start_idx}, end_idx={end_idx}, selected_lines={len(lines)}, invocation_id={invocation_id}")
                
                # Add line numbers
                output_lines = []
                for i, line in enumerate(lines, start=start_idx + 1):
                    output_lines.append(f"{i:4d}| {line.rstrip()}")
                content = "\n".join(output_lines)
            
            logger.info(f"ReadTool: read completed, content_len={len(content)}, invocation_id={invocation_id}")
            return ToolResult(output=content or "(empty file)")
            
        except Exception as e:
            logger.error(f"ReadTool: read error, error={type(e).__name__}, path={path}, invocation_id={invocation_id}", exc_info=True)
            return ToolResult.error(str(e))


__all__ = ["ReadTool"]
