# VibeDNA Agent Tools
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Tool definitions for VibeDNA agents.

Tools are discrete capabilities that agents can invoke to perform
specific operations. This module provides the base classes and
utilities for tool management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union
import asyncio
import inspect
import logging


class ParameterType(Enum):
    """Parameter types for tool definitions."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    BYTES = "bytes"
    DNA_SEQUENCE = "dna_sequence"


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    param_type: ParameterType
    description: str = ""
    required: bool = True
    default: Any = None
    enum_values: Optional[List[str]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # Regex pattern for validation

    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this parameter's constraints.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            if self.required:
                return False, f"Required parameter '{self.name}' is missing"
            return True, None

        # Type validation
        type_validators = {
            ParameterType.STRING: lambda v: isinstance(v, str),
            ParameterType.INTEGER: lambda v: isinstance(v, int) and not isinstance(v, bool),
            ParameterType.FLOAT: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            ParameterType.BOOLEAN: lambda v: isinstance(v, bool),
            ParameterType.ARRAY: lambda v: isinstance(v, list),
            ParameterType.OBJECT: lambda v: isinstance(v, dict),
            ParameterType.BYTES: lambda v: isinstance(v, (bytes, bytearray)),
            ParameterType.DNA_SEQUENCE: lambda v: isinstance(v, str) and all(c in "ATCG" for c in v.upper()),
        }

        validator = type_validators.get(self.param_type)
        if validator and not validator(value):
            return False, f"Parameter '{self.name}' must be of type {self.param_type.value}"

        # Enum validation
        if self.enum_values and value not in self.enum_values:
            return False, f"Parameter '{self.name}' must be one of: {self.enum_values}"

        # Numeric range validation
        if self.min_value is not None and value < self.min_value:
            return False, f"Parameter '{self.name}' must be >= {self.min_value}"
        if self.max_value is not None and value > self.max_value:
            return False, f"Parameter '{self.name}' must be <= {self.max_value}"

        # String/array length validation
        if hasattr(value, "__len__"):
            if self.min_length is not None and len(value) < self.min_length:
                return False, f"Parameter '{self.name}' must have length >= {self.min_length}"
            if self.max_length is not None and len(value) > self.max_length:
                return False, f"Parameter '{self.name}' must have length <= {self.max_length}"

        return True, None


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def ok(cls, data: Any = None, **kwargs) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, data=data, **kwargs)

    @classmethod
    def err(cls, error: str, **kwargs) -> "ToolResult":
        """Create a failure result."""
        return cls(success=False, error=error, **kwargs)


@dataclass
class ToolDefinition:
    """Schema definition for a tool."""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    returns: Optional[ToolParameter] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    version: str = "1.0.0"

    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.param_type.value,
                "description": param.description,
            }
            if param.enum_values:
                prop["enum"] = param.enum_values
            if param.default is not None:
                prop["default"] = param.default
            if param.min_value is not None:
                prop["minimum"] = param.min_value
            if param.max_value is not None:
                prop["maximum"] = param.max_value

            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


class Tool(ABC):
    """
    Abstract base class for agent tools.

    Tools encapsulate discrete operations that agents can perform.
    Each tool has a defined interface and execution logic.
    """

    def __init__(self, definition: ToolDefinition):
        """Initialize the tool with its definition."""
        self.definition = definition
        self.logger = logging.getLogger(f"vibedna.tool.{definition.name}")
        self._call_count = 0
        self._total_execution_time_ms = 0.0

    @property
    def name(self) -> str:
        """Get the tool name."""
        return self.definition.name

    @property
    def description(self) -> str:
        """Get the tool description."""
        return self.definition.description

    @abstractmethod
    async def _execute(self, **kwargs) -> Any:
        """
        Execute the tool's core logic.

        This method must be implemented by subclasses to define
        the tool's behavior.

        Args:
            **kwargs: Tool parameters

        Returns:
            The result of the tool execution
        """
        pass

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with validation and error handling.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult containing the execution result or error
        """
        start_time = datetime.utcnow()

        # Validate parameters
        for param in self.definition.parameters:
            value = kwargs.get(param.name, param.default)
            is_valid, error = param.validate(value)
            if not is_valid:
                return ToolResult.err(error)

        try:
            result = await self._execute(**kwargs)
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            self._call_count += 1
            self._total_execution_time_ms += execution_time

            return ToolResult.ok(
                data=result,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ToolResult.err(
                error=str(e),
                execution_time_ms=execution_time,
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        avg_time = 0.0
        if self._call_count > 0:
            avg_time = self._total_execution_time_ms / self._call_count

        return {
            "name": self.name,
            "call_count": self._call_count,
            "total_execution_time_ms": self._total_execution_time_ms,
            "average_execution_time_ms": avg_time,
        }


class FunctionTool(Tool):
    """
    Tool that wraps a Python function.

    This allows creating tools from simple functions without
    subclassing Tool.
    """

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[List[ToolParameter]] = None,
    ):
        """
        Create a tool from a function.

        Args:
            func: The function to wrap
            name: Tool name (defaults to function name)
            description: Tool description (defaults to function docstring)
            parameters: Parameter definitions (auto-inferred if not provided)
        """
        self._func = func
        self._is_async = asyncio.iscoroutinefunction(func)

        # Auto-infer definition from function
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or ""
        tool_params = parameters or self._infer_parameters(func)

        definition = ToolDefinition(
            name=tool_name,
            description=tool_desc,
            parameters=tool_params,
        )

        super().__init__(definition)

    def _infer_parameters(self, func: Callable) -> List[ToolParameter]:
        """Infer parameters from function signature."""
        params = []
        sig = inspect.signature(func)

        type_mapping = {
            str: ParameterType.STRING,
            int: ParameterType.INTEGER,
            float: ParameterType.FLOAT,
            bool: ParameterType.BOOLEAN,
            list: ParameterType.ARRAY,
            dict: ParameterType.OBJECT,
            bytes: ParameterType.BYTES,
        }

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            param_type = ParameterType.STRING
            if param.annotation != inspect.Parameter.empty:
                param_type = type_mapping.get(param.annotation, ParameterType.STRING)

            required = param.default == inspect.Parameter.empty
            default = None if required else param.default

            params.append(ToolParameter(
                name=name,
                param_type=param_type,
                required=required,
                default=default,
            ))

        return params

    async def _execute(self, **kwargs) -> Any:
        """Execute the wrapped function."""
        if self._is_async:
            return await self._func(**kwargs)
        else:
            return self._func(**kwargs)


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[List[ToolParameter]] = None,
) -> Callable:
    """
    Decorator to create a tool from a function.

    Usage:
        @tool(name="encode_sequence", description="Encode data to DNA")
        def encode_sequence(data: bytes, scheme: str = "quaternary") -> str:
            ...
    """
    def decorator(func: Callable) -> FunctionTool:
        return FunctionTool(func, name, description, parameters)
    return decorator


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self.logger = logging.getLogger("vibedna.tool_registry")

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        if tool.name in self._tools:
            self.logger.warning(f"Overwriting existing tool: {tool.name}")
        self._tools[tool.name] = tool
        self.logger.debug(f"Registered tool: {tool.name}")

    def unregister(self, name: str) -> bool:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get JSON schemas for all tools."""
        return [tool.definition.to_schema() for tool in self._tools.values()]

    async def invoke(self, name: str, **kwargs) -> ToolResult:
        """Invoke a tool by name."""
        tool = self.get(name)
        if not tool:
            return ToolResult.err(f"Tool not found: {name}")
        return await tool.execute(**kwargs)
