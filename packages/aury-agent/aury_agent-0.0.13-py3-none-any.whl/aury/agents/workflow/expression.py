"""Expression evaluator for workflow DSL."""
from __future__ import annotations

import re
from typing import Any


class ExpressionError(Exception):
    """Expression evaluation error."""
    pass


class DotDict(dict):
    """Dict that supports dot notation access.
    
    Allows expressions like `inputs.json_data` instead of `inputs["json_data"]`.
    """
    
    def __getattr__(self, key: str) -> Any:
        try:
            value = self[key]
            # Recursively wrap nested dicts
            if isinstance(value, dict) and not isinstance(value, DotDict):
                return DotDict(value)
            return value
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{key}'")
    
    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value
    
    def __delattr__(self, key: str) -> None:
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{key}'")


class ExpressionEvaluator:
    """Expression evaluator for ${{ ... }} syntax."""
    
    EXPR_PATTERN = re.compile(r'\$\{\{\s*(.+?)\s*\}\}')
    
    def evaluate(
        self,
        expression: str,
        context: dict[str, Any],
    ) -> Any:
        """Evaluate expression.
        
        Supports:
        - Full expressions: ${{ inputs.name }}
        - Template strings: "Hello ${{ inputs.name }}!"
        - Comparisons: ${{ inputs.count > 10 }}
        """
        if expression.startswith("${{") and expression.endswith("}}"):
            inner = expression[3:-2].strip()
            return self._eval_inner(inner, context)
        
        def replace(match: re.Match) -> str:
            inner = match.group(1)
            result = self._eval_inner(inner, context)
            return str(result) if result is not None else ""
        
        return self.EXPR_PATTERN.sub(replace, expression)
    
    def _eval_inner(self, expr: str, context: dict[str, Any]) -> Any:
        """Evaluate inner expression.
        
        Uses DotDict to allow dot notation access like `inputs.json_data`.
        """
        # Wrap dicts in DotDict to support dot notation
        inputs_data = context.get("inputs", {})
        state_data = context.get("state", {})
        
        safe_context = {
            "inputs": DotDict(inputs_data) if isinstance(inputs_data, dict) else inputs_data,
            "state": DotDict(state_data.to_dict() if hasattr(state_data, 'to_dict') else state_data) if state_data else DotDict({}),
            "true": True,
            "false": False,
            "null": None,
            "True": True,
            "False": False,
            "None": None,
        }
        
        # Add extra context variables (also wrap dicts)
        for key, value in context.items():
            if key not in ("inputs", "state"):
                if isinstance(value, dict):
                    safe_context[key] = DotDict(value)
                else:
                    safe_context[key] = value
        
        try:
            return eval(expr, {"__builtins__": {}}, safe_context)
        except Exception as e:
            raise ExpressionError(f"Failed to evaluate: {expr}") from e
    
    def evaluate_condition(self, expr: str | None, context: dict[str, Any]) -> bool:
        """Evaluate condition expression."""
        if not expr:
            return True
        result = self.evaluate(expr, context)
        return bool(result)
    
    def has_expression(self, value: str) -> bool:
        """Check if string contains expression."""
        if not isinstance(value, str):
            return False
        return bool(self.EXPR_PATTERN.search(value))
    
    def resolve_inputs(
        self,
        inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve all expressions in inputs dict."""
        resolved = {}
        
        for key, value in inputs.items():
            if isinstance(value, str) and self.has_expression(value):
                resolved[key] = self.evaluate(value, context)
            elif isinstance(value, dict):
                resolved[key] = self.resolve_inputs(value, context)
            elif isinstance(value, list):
                resolved[key] = [
                    self.evaluate(v, context)
                    if isinstance(v, str) and self.has_expression(v)
                    else v
                    for v in value
                ]
            else:
                resolved[key] = value
        
        return resolved
