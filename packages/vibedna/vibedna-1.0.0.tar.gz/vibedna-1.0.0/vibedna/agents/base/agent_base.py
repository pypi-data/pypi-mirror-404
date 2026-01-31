# VibeDNA Agent Base Classes
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Base classes and interfaces for the VibeDNA Agent System.

This module provides the foundational abstractions for all agents in the system,
including configuration, capabilities, and lifecycle management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
import asyncio
import logging
import uuid

from vibedna.agents.base.message import (
    TaskRequest,
    TaskResponse,
    TaskStatus,
    AgentMessage,
    MessageType,
)
from vibedna.agents.base.tool import Tool, ToolResult
from vibedna.agents.base.context import AgentContext


class AgentTier(Enum):
    """Agent tier classification."""
    ORCHESTRATION = "orchestration"
    SPECIALIST = "specialist"
    SUPPORT = "support"


class AgentStatus(Enum):
    """Agent operational status."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentCapability:
    """Describes a capability that an agent provides."""
    name: str
    description: str
    version: str = "1.0.0"
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""
    agent_id: str
    version: str = "1.0.0"
    tier: AgentTier = AgentTier.SPECIALIST
    role: str = ""
    description: str = ""
    capabilities: List[AgentCapability] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    mcp_connections: List[str] = field(default_factory=list)
    skills_required: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 10
    timeout_seconds: float = 300.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    personality: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentHealth:
    """Agent health status."""
    status: AgentStatus
    uptime_seconds: float
    tasks_completed: int
    tasks_failed: int
    current_load: float
    memory_usage_bytes: int
    last_heartbeat: datetime
    error_message: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all VibeDNA agents.

    All agents in the system inherit from this class and must implement
    the abstract methods for task handling and lifecycle management.
    """

    FOOTER = "© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."

    def __init__(self, config: AgentConfig):
        """
        Initialize the agent with configuration.

        Args:
            config: Agent configuration containing ID, capabilities, etc.
        """
        self.config = config
        self.logger = logging.getLogger(f"vibedna.agent.{config.agent_id}")
        self._status = AgentStatus.INITIALIZING
        self._start_time: Optional[datetime] = None
        self._tools: Dict[str, Tool] = {}
        self._tasks_completed = 0
        self._tasks_failed = 0
        self._current_tasks: Dict[str, TaskRequest] = {}
        self._message_handlers: Dict[MessageType, List[Callable]] = {}
        self._context: Optional[AgentContext] = None

    @property
    def agent_id(self) -> str:
        """Get the agent's unique identifier."""
        return self.config.agent_id

    @property
    def tier(self) -> AgentTier:
        """Get the agent's tier classification."""
        return self.config.tier

    @property
    def status(self) -> AgentStatus:
        """Get the agent's current status."""
        return self._status

    @status.setter
    def status(self, value: AgentStatus) -> None:
        """Set the agent's status with logging."""
        old_status = self._status
        self._status = value
        self.logger.info(f"Agent status changed: {old_status.value} -> {value.value}")

    @property
    def is_ready(self) -> bool:
        """Check if agent is ready to accept tasks."""
        return self._status == AgentStatus.READY

    @property
    def current_load(self) -> float:
        """Get current task load (0.0 to 1.0)."""
        if self.config.max_concurrent_tasks == 0:
            return 0.0
        return len(self._current_tasks) / self.config.max_concurrent_tasks

    async def initialize(self) -> None:
        """
        Initialize the agent.

        Called once when the agent starts up. Override to perform
        custom initialization logic.
        """
        self._start_time = datetime.utcnow()
        self._register_default_tools()
        await self._initialize_mcp_connections()
        self.status = AgentStatus.READY
        self.logger.info(f"Agent {self.agent_id} initialized successfully")

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the agent.

        Called when the agent is being terminated. Override to perform
        cleanup operations.
        """
        self.status = AgentStatus.SHUTDOWN
        # Wait for current tasks to complete
        if self._current_tasks:
            self.logger.info(f"Waiting for {len(self._current_tasks)} tasks to complete")
            await asyncio.sleep(1)  # Brief wait for task completion
        self.logger.info(f"Agent {self.agent_id} shutdown complete")

    @abstractmethod
    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """
        Handle an incoming task request.

        This is the main entry point for task processing. Each agent
        must implement this method to define its behavior.

        Args:
            request: The task request to process

        Returns:
            TaskResponse containing the result or error information
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the agent's system prompt.

        Returns the detailed instructions that define the agent's
        behavior and capabilities.

        Returns:
            System prompt string
        """
        pass

    async def process_task(self, request: TaskRequest) -> TaskResponse:
        """
        Process a task with full lifecycle management.

        This method wraps handle_task with error handling, retries,
        and metrics collection.

        Args:
            request: The task request to process

        Returns:
            TaskResponse containing the result or error information
        """
        if not self.is_ready:
            return TaskResponse(
                request_id=request.request_id,
                status=TaskStatus.FAILED,
                error=f"Agent not ready: {self._status.value}",
                footer=self.FOOTER,
            )

        if self.current_load >= 1.0:
            return TaskResponse(
                request_id=request.request_id,
                status=TaskStatus.FAILED,
                error="Agent at maximum capacity",
                footer=self.FOOTER,
            )

        self._current_tasks[request.request_id] = request
        self.status = AgentStatus.BUSY

        try:
            response = await self._execute_with_retry(request)
            self._tasks_completed += 1
            return response
        except Exception as e:
            self._tasks_failed += 1
            self.logger.error(f"Task {request.request_id} failed: {e}")
            return TaskResponse(
                request_id=request.request_id,
                status=TaskStatus.FAILED,
                error=str(e),
                footer=self.FOOTER,
            )
        finally:
            del self._current_tasks[request.request_id]
            if not self._current_tasks:
                self.status = AgentStatus.READY

    async def _execute_with_retry(self, request: TaskRequest) -> TaskResponse:
        """Execute task with retry logic."""
        last_error = None

        for attempt in range(self.config.retry_attempts):
            try:
                response = await asyncio.wait_for(
                    self.handle_task(request),
                    timeout=self.config.timeout_seconds
                )
                return response
            except asyncio.TimeoutError:
                last_error = f"Task timed out after {self.config.timeout_seconds}s"
                self.logger.warning(f"Attempt {attempt + 1} timed out for task {request.request_id}")
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Attempt {attempt + 1} failed for task {request.request_id}: {e}")

            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay_seconds * (attempt + 1))

        raise RuntimeError(last_error)

    def register_tool(self, tool: Tool) -> None:
        """Register a tool with the agent."""
        self._tools[tool.name] = tool
        self.logger.debug(f"Registered tool: {tool.name}")

    async def invoke_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Invoke a registered tool."""
        if tool_name not in self._tools:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}",
            )

        tool = self._tools[tool_name]
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
            )

    def _register_default_tools(self) -> None:
        """Register default tools for the agent."""
        # Override in subclasses to register agent-specific tools
        pass

    async def _initialize_mcp_connections(self) -> None:
        """Initialize MCP server connections."""
        for mcp_server in self.config.mcp_connections:
            self.logger.debug(f"Connecting to MCP server: {mcp_server}")
            # MCP connection logic will be implemented in mcp_servers module

    def get_health(self) -> AgentHealth:
        """Get current health status of the agent."""
        uptime = 0.0
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()

        return AgentHealth(
            status=self._status,
            uptime_seconds=uptime,
            tasks_completed=self._tasks_completed,
            tasks_failed=self._tasks_failed,
            current_load=self.current_load,
            memory_usage_bytes=0,  # To be implemented
            last_heartbeat=datetime.utcnow(),
        )

    def subscribe_message(self, message_type: MessageType, handler: Callable) -> None:
        """Subscribe to messages of a specific type."""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)

    async def send_message(self, message: AgentMessage) -> None:
        """Send a message to subscribed handlers."""
        handlers = self._message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                self.logger.error(f"Message handler error: {e}")

    def add_footer(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Add the VibeDNA footer to a response."""
        response["footer"] = self.FOOTER
        return response

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} status={self._status.value}>"
