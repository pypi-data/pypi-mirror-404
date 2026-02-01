"""BashTool - Execute shell commands."""
from __future__ import annotations

import asyncio
import subprocess
from typing import Any

from ...core.types.tool import BaseTool, ToolContext, ToolResult, ToolInfo
from ...core.logging import tool_logger as logger


class BashTool(BaseTool):
    """Execute shell commands.
    
    Provides the ability to run shell commands with timeout and working directory support.
    
    Security Note:
        In production, you should restrict the commands that can be executed,
        or run in a sandboxed environment.
    """
    
    _name = "bash"
    _description = "Execute shell commands and return the output"
    _parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 30)",
                "default": 30,
            },
            "working_dir": {
                "type": "string",
                "description": "Working directory for the command (optional)",
            },
        },
        "required": ["command"],
    }
    
    def __init__(self, allowed_commands: list[str] | None = None):
        """Initialize BashTool.
        
        Args:
            allowed_commands: List of allowed command prefixes (None = allow all)
        """
        self._allowed_commands = allowed_commands
    
    async def execute(
        self,
        params: dict[str, Any],
        ctx: ToolContext,
    ) -> ToolResult:
        """Execute the shell command."""
        command = params.get("command", "")
        timeout = params.get("timeout", 30)
        working_dir = params.get("working_dir")
        invocation_id = ctx.invocation_id if ctx else None
        
        logger.info(f"BashTool executing command, invocation_id={invocation_id}, timeout={timeout}")
        
        if not command:
            logger.warning(f"BashTool: command is empty, invocation_id={invocation_id}")
            return ToolResult.error("Command is required")
        
        # Security check
        if self._allowed_commands:
            cmd_prefix = command.split()[0] if command.split() else ""
            if cmd_prefix not in self._allowed_commands:
                logger.warning(f"BashTool: command not allowed, cmd={cmd_prefix}, invocation_id={invocation_id}")
                return ToolResult.error(f"Command '{cmd_prefix}' is not allowed")
        
        try:
            logger.debug(f"BashTool: starting subprocess, working_dir={working_dir}, invocation_id={invocation_id}")
            # Run command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                logger.warning(f"BashTool: command timeout, timeout={timeout}, invocation_id={invocation_id}")
                return ToolResult.error(f"Command timed out after {timeout} seconds")
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            if process.returncode != 0:
                logger.info(f"BashTool: command failed, exit_code={process.returncode}, invocation_id={invocation_id}")
                return ToolResult(
                    output=f"Exit code: {process.returncode}\n\nSTDOUT:\n{output}\n\nSTDERR:\n{error_output}",
                    is_error=True,
                )
            
            result_output = output
            if error_output:
                result_output += f"\n\nSTDERR:\n{error_output}"
            
            logger.info(f"BashTool: command completed successfully, output_len={len(result_output)}, invocation_id={invocation_id}")
            return ToolResult(output=result_output.strip() or "(no output)")
            
        except Exception as e:
            logger.error(f"BashTool: execution error, error={type(e).__name__}, invocation_id={invocation_id}", exc_info=True)
            return ToolResult.error(str(e))


__all__ = ["BashTool"]
