# VibeDNA Logging Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Logging Agent - Centralized log management.

Manages:
- Log collection from all agents
- Log aggregation and filtering
- Log searching and retrieval
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from vibedna.agents.base.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentTier,
)
from vibedna.agents.base.message import (
    TaskRequest,
    TaskResponse,
)


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """A log entry."""
    timestamp: datetime
    level: LogLevel
    source: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class LoggingAgent(BaseAgent):
    """
    Logging Agent for centralized log management.

    Collects logs from all system components and provides
    search and retrieval capabilities.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Logging Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-logging-agent",
                version="1.0.0",
                tier=AgentTier.SUPPORT,
                role="Centralized Logging",
                description="Manages centralized log collection and retrieval",
                capabilities=[
                    AgentCapability(
                        name="log_collection",
                        description="Collect logs from agents",
                    ),
                    AgentCapability(
                        name="log_search",
                        description="Search and filter logs",
                    ),
                    AgentCapability(
                        name="log_aggregation",
                        description="Aggregate log statistics",
                    ),
                ],
                tools=[
                    "log_collector",
                    "log_searcher",
                    "log_aggregator",
                ],
                mcp_connections=["vibedna-monitor"],
            )

        super().__init__(config)
        self._logs: List[LogEntry] = []
        self._max_logs = 10000

    def get_system_prompt(self) -> str:
        """Get the Logging Agent's system prompt."""
        return """You are the VibeDNA Logging Agent, managing centralized logging.

## Capabilities

1. Log Collection - Receive logs from all agents
2. Log Search - Search by level, source, time range, keywords
3. Log Aggregation - Count by level, source

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a logging task."""
        action = request.parameters.get("action", "search")

        if action == "log":
            return await self._add_log(request)
        elif action == "search":
            return await self._search_logs(request)
        elif action == "get_recent":
            return await self._get_recent(request)
        elif action == "get_stats":
            return await self._get_stats(request)
        elif action == "clear":
            return await self._clear_logs(request)
        else:
            return TaskResponse.failure(request.request_id, f"Unknown action: {action}")

    async def _add_log(self, request: TaskRequest) -> TaskResponse:
        """Add a log entry."""
        try:
            level = request.parameters.get("level", "info")
            source = request.parameters.get("source", "unknown")
            message = request.parameters.get("message", "")
            metadata = request.parameters.get("metadata", {})

            entry = LogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel(level.lower()),
                source=source,
                message=message,
                metadata=metadata,
            )

            self._logs.append(entry)

            # Trim if too many
            if len(self._logs) > self._max_logs:
                self._logs = self._logs[-self._max_logs:]

            return TaskResponse.success(
                request.request_id,
                {"logged": True},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _search_logs(self, request: TaskRequest) -> TaskResponse:
        """Search logs."""
        try:
            level = request.parameters.get("level")
            source = request.parameters.get("source")
            query = request.parameters.get("query", "")
            limit = request.parameters.get("limit", 100)

            results = []
            for entry in reversed(self._logs):
                if level and entry.level.value != level:
                    continue
                if source and entry.source != source:
                    continue
                if query and query.lower() not in entry.message.lower():
                    continue

                results.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level.value,
                    "source": entry.source,
                    "message": entry.message,
                })

                if len(results) >= limit:
                    break

            return TaskResponse.success(
                request.request_id,
                {"logs": results, "count": len(results)},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _get_recent(self, request: TaskRequest) -> TaskResponse:
        """Get recent logs."""
        try:
            limit = request.parameters.get("limit", 50)

            results = []
            for entry in self._logs[-limit:]:
                results.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level.value,
                    "source": entry.source,
                    "message": entry.message,
                })

            return TaskResponse.success(
                request.request_id,
                {"logs": list(reversed(results)), "count": len(results)},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _get_stats(self, request: TaskRequest) -> TaskResponse:
        """Get logging statistics."""
        try:
            by_level = {}
            by_source = {}

            for entry in self._logs:
                level = entry.level.value
                source = entry.source

                by_level[level] = by_level.get(level, 0) + 1
                by_source[source] = by_source.get(source, 0) + 1

            return TaskResponse.success(
                request.request_id,
                {
                    "total_logs": len(self._logs),
                    "by_level": by_level,
                    "by_source": by_source,
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _clear_logs(self, request: TaskRequest) -> TaskResponse:
        """Clear all logs."""
        self._logs = []
        return TaskResponse.success(request.request_id, {"cleared": True})
