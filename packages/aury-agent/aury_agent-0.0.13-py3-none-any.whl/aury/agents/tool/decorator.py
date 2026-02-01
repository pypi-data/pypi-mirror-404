"""Tool decorators for creating tools from functions."""
from __future__ import annotations

import asyncio
import inspect
from functools import wraps
from typing import Any, Callable, get_type_hints, get_origin, get_args, Union

from ..core.types.tool import BaseTool, ToolContext, ToolResult, ToolInfo, ToolConfig


def _type_to_schema(t: type) -> dict[str, Any]:
    """Convert Python type to JSON Schema."""
    # Handle None/NoneType
    if t is type(None):
        return {"type": "null"}
    
    # Handle Optional (Union with None)
    origin = get_origin(t)
    if origin is Union:
        args = get_args(t)
        # Filter out None
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            # Optional[X] -> X with nullable
            schema = _type_to_schema(non_none[0])
            return schema
        # Union of multiple types
        return {"oneOf": [_type_to_schema(a) for a in non_none]}
    
    # Handle list
    if origin is list:
        args = get_args(t)
        if args:
            return {"type": "array", "items": _type_to_schema(args[0])}
        return {"type": "array"}
    
    # Handle dict
    if origin is dict:
        args = get_args(t)
        if len(args) == 2:
            return {
                "type": "object",
                "additionalProperties": _type_to_schema(args[1]),
            }
        return {"type": "object"}
    
    # Basic types
    type_map = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
        # Any type: JSON Schema 2020-12 requires valid type, use object as fallback
        Any: {"type": "object"},
    }
    
    return type_map.get(t, {"type": "string"})


def _parse_docstring(docstring: str | None) -> tuple[str, dict[str, str]]:
    """Parse docstring to extract description and param descriptions.
    
    Returns:
        Tuple of (main description, {param_name: param_description})
    """
    if not docstring:
        return "", {}
    
    lines = docstring.strip().split("\n")
    description_lines = []
    param_docs: dict[str, str] = {}
    
    in_params = False
    current_param = None
    
    for line in lines:
        stripped = line.strip()
        
        # Check for param section
        if stripped.lower().startswith(("args:", "arguments:", "parameters:", "params:")):
            in_params = True
            continue
        
        if stripped.lower().startswith(("returns:", "return:", "raises:", "yields:")):
            in_params = False
            current_param = None
            continue
        
        if in_params:
            # Check for param definition: "param_name: description" or "param_name (type): description"
            if ":" in stripped and not stripped.startswith(" "):
                parts = stripped.split(":", 1)
                param_name = parts[0].strip()
                # Remove type annotation if present
                if "(" in param_name:
                    param_name = param_name.split("(")[0].strip()
                param_docs[param_name] = parts[1].strip() if len(parts) > 1 else ""
                current_param = param_name
            elif current_param and stripped:
                # Continuation of previous param description
                param_docs[current_param] += " " + stripped
        else:
            description_lines.append(stripped)
    
    description = " ".join(description_lines).strip()
    return description, param_docs


def tool(
    func: Callable | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> Callable[[Callable], BaseTool] | BaseTool:
    """Decorator to create a Tool from a function.
    
    The function can be sync or async. Parameters are automatically converted
    to JSON Schema based on type hints, unless manually specified.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        parameters: Manual JSON Schema for parameters (optional)
        
    Returns:
        Decorated function as a Tool
        
    Example:
        @tool
        def greet(name: str) -> str:
            return f"Hello, {name}!"
        
        @tool(name="calculator", description="Perform calculations")
        def calculate(expression: str) -> str:
            return str(eval(expression))
        
        @tool(parameters={"type": "object", "properties": {...}})
        def custom_tool(arg: str) -> str:
            return arg
    """
    def decorator(fn: Callable) -> BaseTool:
        tool_name = name or fn.__name__
        
        # Parse docstring for descriptions
        doc_desc, param_docs = _parse_docstring(fn.__doc__)
        tool_desc = description or doc_desc or f"Tool: {tool_name}"
        
        # Use manual parameters or auto-generate
        if parameters is not None:
            parameters_schema = parameters
        else:
            # Get type hints and signature
            try:
                hints = get_type_hints(fn)
            except Exception:
                hints = {}
            
            sig = inspect.signature(fn)
            
            # Build parameters schema
            properties: dict[str, Any] = {}
            required: list[str] = []
            
            for param_name, param in sig.parameters.items():
                # Skip special parameters
                if param_name in ("self", "cls", "ctx", "context"):
                    continue
                
                # Get type
                param_type = hints.get(param_name, str)
                schema = _type_to_schema(param_type)
                
                # Add description from docstring
                if param_name in param_docs:
                    schema["description"] = param_docs[param_name]
                
                properties[param_name] = schema
                
                # Check if required
                if param.default is inspect.Parameter.empty:
                    required.append(param_name)
            
            parameters_schema = {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        
        sig = inspect.signature(fn)
        
        # Check if function accepts ctx
        accepts_ctx = "ctx" in sig.parameters or "context" in sig.parameters
        ctx_param_name = "ctx" if "ctx" in sig.parameters else "context"
        
        class FunctionTool(BaseTool):
            """Tool created from decorated function."""
            
            _name = tool_name
            _description = tool_desc
            _parameters = parameters_schema
            
            async def execute(
                self,
                params: dict[str, Any],
                ctx: ToolContext,
            ) -> ToolResult:
                """Execute the wrapped function."""
                try:
                    # Add context if function accepts it
                    if accepts_ctx:
                        params = {**params, ctx_param_name: ctx}
                    
                    # Call function
                    result = fn(**params)
                    
                    # Await if coroutine
                    if asyncio.iscoroutine(result):
                        result = await result
                    
                    # Convert result to ToolResult
                    if isinstance(result, ToolResult):
                        return result
                    
                    return ToolResult(output=str(result))
                
                except Exception as e:
                    return ToolResult.error(str(e))
        
        return FunctionTool()
    
    # Support both @tool and @tool(...) usage
    if func is not None:
        return decorator(func)
    return decorator
