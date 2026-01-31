# VibeDNA Base MCP Server
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Base MCP Server implementation for VibeDNA.

Provides the foundation for all VibeDNA MCP servers with common
functionality for tool registration, resource management, and
prompt handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
import asyncio
import json
import logging
import uuid


class TransportType(Enum):
    """MCP transport types."""
    SSE = "sse"
    STDIO = "stdio"
    WEBSOCKET = "websocket"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    version: str = "1.0.0"
    description: str = ""
    transport: TransportType = TransportType.SSE
    url: Optional[str] = None
    host: str = "0.0.0.0"
    port: int = 8090
    api_key: Optional[str] = None
    max_connections: int = 100
    timeout_seconds: float = 60.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPToolParameter:
    """Parameter definition for an MCP tool."""
    name: str
    param_type: str  # string, integer, number, boolean, array, object
    description: str = ""
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class MCPTool:
    """Definition of an MCP tool."""
    name: str
    description: str
    parameters: List[MCPToolParameter] = field(default_factory=list)
    returns: Optional[Dict[str, Any]] = None
    handler: Optional[Callable] = None

    def to_schema(self) -> Dict[str, Any]:
        """Convert to MCP tool schema."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.param_type,
                "description": param.description,
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


@dataclass
class MCPResource:
    """Definition of an MCP resource."""
    name: str
    description: str
    uri: str
    mime_type: str = "application/json"
    handler: Optional[Callable] = None

    def to_schema(self) -> Dict[str, Any]:
        """Convert to MCP resource schema."""
        return {
            "name": self.name,
            "description": self.description,
            "uri": self.uri,
            "mimeType": self.mime_type,
        }


@dataclass
class MCPPrompt:
    """Definition of an MCP prompt template."""
    name: str
    description: str
    arguments: List[Dict[str, str]] = field(default_factory=list)
    template: str = ""

    def to_schema(self) -> Dict[str, Any]:
        """Convert to MCP prompt schema."""
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }


class MCPMessage:
    """MCP JSON-RPC message."""

    def __init__(
        self,
        method: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        error: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
    ):
        self.jsonrpc = "2.0"
        self.method = method
        self.params = params or {}
        self.result = result
        self.error = error
        self.id = id or str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        msg = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.method:
            msg["method"] = self.method
            msg["params"] = self.params
        if self.result is not None:
            msg["result"] = self.result
        if self.error:
            msg["error"] = self.error
        return msg

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMessage":
        """Create from dictionary."""
        return cls(
            method=data.get("method"),
            params=data.get("params", {}),
            result=data.get("result"),
            error=data.get("error"),
            id=data.get("id"),
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class BaseMCPServer(ABC):
    """
    Abstract base class for VibeDNA MCP servers.

    Implements the Model Context Protocol for exposing VibeDNA
    capabilities to AI agents.
    """

    FOOTER = "© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."

    def __init__(self, config: MCPServerConfig):
        """Initialize the MCP server."""
        self.config = config
        self.logger = logging.getLogger(f"vibedna.mcp.{config.name}")
        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._prompts: Dict[str, MCPPrompt] = {}
        self._running = False
        self._connections: int = 0
        self._request_count: int = 0

    @property
    def name(self) -> str:
        """Get server name."""
        return self.config.name

    @property
    def version(self) -> str:
        """Get server version."""
        return self.config.version

    @abstractmethod
    def _register_tools(self) -> None:
        """Register server-specific tools. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def _register_resources(self) -> None:
        """Register server-specific resources. Must be implemented by subclasses."""
        pass

    def _register_prompts(self) -> None:
        """Register server-specific prompts. Override in subclasses."""
        pass

    async def initialize(self) -> None:
        """Initialize the server and register capabilities."""
        self._register_tools()
        self._register_resources()
        self._register_prompts()
        self.logger.info(f"MCP Server {self.name} v{self.version} initialized")
        self.logger.info(f"  Tools: {len(self._tools)}")
        self.logger.info(f"  Resources: {len(self._resources)}")
        self.logger.info(f"  Prompts: {len(self._prompts)}")

    async def start(self) -> None:
        """Start the MCP server."""
        await self.initialize()
        self._running = True
        self.logger.info(f"MCP Server {self.name} started on {self.config.host}:{self.config.port}")

    async def stop(self) -> None:
        """Stop the MCP server."""
        self._running = False
        self.logger.info(f"MCP Server {self.name} stopped")

    def register_tool(self, tool: MCPTool) -> None:
        """Register a tool with the server."""
        self._tools[tool.name] = tool
        self.logger.debug(f"Registered tool: {tool.name}")

    def register_resource(self, resource: MCPResource) -> None:
        """Register a resource with the server."""
        self._resources[resource.name] = resource
        self.logger.debug(f"Registered resource: {resource.name}")

    def register_prompt(self, prompt: MCPPrompt) -> None:
        """Register a prompt with the server."""
        self._prompts[prompt.name] = prompt
        self.logger.debug(f"Registered prompt: {prompt.name}")

    async def handle_message(self, message: MCPMessage) -> MCPMessage:
        """
        Handle an incoming MCP message.

        Routes messages to appropriate handlers based on method.
        """
        self._request_count += 1

        try:
            if message.method == "initialize":
                return await self._handle_initialize(message)
            elif message.method == "tools/list":
                return await self._handle_tools_list(message)
            elif message.method == "tools/call":
                return await self._handle_tools_call(message)
            elif message.method == "resources/list":
                return await self._handle_resources_list(message)
            elif message.method == "resources/read":
                return await self._handle_resources_read(message)
            elif message.method == "prompts/list":
                return await self._handle_prompts_list(message)
            elif message.method == "prompts/get":
                return await self._handle_prompts_get(message)
            else:
                return MCPMessage(
                    error={"code": -32601, "message": f"Method not found: {message.method}"},
                    id=message.id,
                )
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            return MCPMessage(
                error={"code": -32603, "message": str(e)},
                id=message.id,
            )

    async def _handle_initialize(self, message: MCPMessage) -> MCPMessage:
        """Handle initialize request."""
        return MCPMessage(
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"listChanged": True, "subscribe": True},
                    "prompts": {"listChanged": True},
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version,
                },
            },
            id=message.id,
        )

    async def _handle_tools_list(self, message: MCPMessage) -> MCPMessage:
        """Handle tools/list request."""
        tools = [tool.to_schema() for tool in self._tools.values()]
        return MCPMessage(
            result={"tools": tools},
            id=message.id,
        )

    async def _handle_tools_call(self, message: MCPMessage) -> MCPMessage:
        """Handle tools/call request."""
        tool_name = message.params.get("name")
        arguments = message.params.get("arguments", {})

        if tool_name not in self._tools:
            return MCPMessage(
                error={"code": -32602, "message": f"Tool not found: {tool_name}"},
                id=message.id,
            )

        tool = self._tools[tool_name]
        if not tool.handler:
            return MCPMessage(
                error={"code": -32603, "message": f"Tool has no handler: {tool_name}"},
                id=message.id,
            )

        try:
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)

            # Add footer to result
            if isinstance(result, dict):
                result["footer"] = self.FOOTER

            return MCPMessage(
                result={
                    "content": [{"type": "text", "text": json.dumps(result)}],
                    "isError": False,
                },
                id=message.id,
            )
        except Exception as e:
            return MCPMessage(
                result={
                    "content": [{"type": "text", "text": str(e)}],
                    "isError": True,
                },
                id=message.id,
            )

    async def _handle_resources_list(self, message: MCPMessage) -> MCPMessage:
        """Handle resources/list request."""
        resources = [resource.to_schema() for resource in self._resources.values()]
        return MCPMessage(
            result={"resources": resources},
            id=message.id,
        )

    async def _handle_resources_read(self, message: MCPMessage) -> MCPMessage:
        """Handle resources/read request."""
        uri = message.params.get("uri")

        # Find resource by URI
        resource = None
        for r in self._resources.values():
            if r.uri == uri:
                resource = r
                break

        if not resource:
            return MCPMessage(
                error={"code": -32602, "message": f"Resource not found: {uri}"},
                id=message.id,
            )

        if not resource.handler:
            return MCPMessage(
                error={"code": -32603, "message": f"Resource has no handler: {uri}"},
                id=message.id,
            )

        try:
            if asyncio.iscoroutinefunction(resource.handler):
                content = await resource.handler()
            else:
                content = resource.handler()

            return MCPMessage(
                result={
                    "contents": [{
                        "uri": uri,
                        "mimeType": resource.mime_type,
                        "text": json.dumps(content) if isinstance(content, dict) else str(content),
                    }],
                },
                id=message.id,
            )
        except Exception as e:
            return MCPMessage(
                error={"code": -32603, "message": str(e)},
                id=message.id,
            )

    async def _handle_prompts_list(self, message: MCPMessage) -> MCPMessage:
        """Handle prompts/list request."""
        prompts = [prompt.to_schema() for prompt in self._prompts.values()]
        return MCPMessage(
            result={"prompts": prompts},
            id=message.id,
        )

    async def _handle_prompts_get(self, message: MCPMessage) -> MCPMessage:
        """Handle prompts/get request."""
        prompt_name = message.params.get("name")
        arguments = message.params.get("arguments", {})

        if prompt_name not in self._prompts:
            return MCPMessage(
                error={"code": -32602, "message": f"Prompt not found: {prompt_name}"},
                id=message.id,
            )

        prompt = self._prompts[prompt_name]

        # Render template with arguments
        rendered = prompt.template
        for key, value in arguments.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))

        return MCPMessage(
            result={
                "description": prompt.description,
                "messages": [{"role": "user", "content": {"type": "text", "text": rendered}}],
            },
            id=message.id,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "name": self.name,
            "version": self.version,
            "running": self._running,
            "connections": self._connections,
            "request_count": self._request_count,
            "tools_count": len(self._tools),
            "resources_count": len(self._resources),
            "prompts_count": len(self._prompts),
            "footer": self.FOOTER,
        }
