import inspect
from typing import Callable, Any, Dict, List

class Tool:
    """
    Wraps a python function into an LLM-compatible tool.
    """
    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__
        self.description = func.__doc__ or "No description provided."
        self.schema = self._generate_schema()

    def _generate_schema(self) -> Dict[str, Any]:
        """
        Auto-generates OpenAI function schema from the python function signature.
        """
        sig = inspect.signature(self.func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }

        for name, param in sig.parameters.items():
            # Map python types to JSON types
            param_type = "string"
            if param.annotation == int: param_type = "integer"
            elif param.annotation == float: param_type = "number"
            elif param.annotation == bool: param_type = "boolean"
            elif param.annotation == dict: param_type = "object"

            parameters["properties"][name] = {
                "type": param_type,
                "description": name  # ideally we parse docstrings for this
            }
            
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters
            }
        }

    def execute(self, **kwargs):
        """Runs the actual python code."""
        return self.func(**kwargs)