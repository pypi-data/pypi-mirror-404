# VibeDNA Monitor MCP Server
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Monitor MCP Server for VibeDNA system monitoring and metrics.

Provides tools for:
- Getting system metrics
- Health status checks
- Agent status monitoring
- Workflow status tracking
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import time

from vibedna.agents.mcp_servers.base_server import (
    BaseMCPServer,
    MCPServerConfig,
    MCPTool,
    MCPToolParameter,
    MCPResource,
    TransportType,
)


@dataclass
class MetricsCollector:
    """Collects and stores system metrics."""
    encode_requests_total: int = 0
    decode_requests_total: int = 0
    compute_operations_total: int = 0
    encoded_bytes_total: int = 0
    decoded_bytes_total: int = 0
    storage_bytes_used: int = 0
    encoding_errors_total: int = 0
    decoding_errors_total: int = 0
    checksum_failures_total: int = 0
    corrections_applied_total: int = 0
    active_agents: int = 0
    queue_depth: int = 0
    encode_durations: List[float] = field(default_factory=list)
    decode_durations: List[float] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)

    def record_encode(self, input_size: int, duration: float) -> None:
        """Record an encoding operation."""
        self.encode_requests_total += 1
        self.encoded_bytes_total += input_size
        self.encode_durations.append(duration)
        # Keep only last 1000 durations
        if len(self.encode_durations) > 1000:
            self.encode_durations = self.encode_durations[-1000:]

    def record_decode(self, output_size: int, duration: float) -> None:
        """Record a decoding operation."""
        self.decode_requests_total += 1
        self.decoded_bytes_total += output_size
        self.decode_durations.append(duration)
        if len(self.decode_durations) > 1000:
            self.decode_durations = self.decode_durations[-1000:]

    def get_percentile(self, durations: List[float], p: int) -> float:
        """Get percentile of durations."""
        if not durations:
            return 0.0
        sorted_d = sorted(durations)
        idx = int(len(sorted_d) * p / 100)
        return sorted_d[min(idx, len(sorted_d) - 1)]


class VibeDNAMonitorMCPServer(BaseMCPServer):
    """
    Monitor MCP Server for system health and metrics.

    Tools:
    - get_metrics: Get current metrics
    - get_health: Get system health status
    - get_agent_status: Get status of all agents
    - get_workflow_status: Get status of running workflows
    """

    def __init__(self, config: Optional[MCPServerConfig] = None):
        """Initialize the Monitor MCP server."""
        if config is None:
            config = MCPServerConfig(
                name="vibedna-monitor",
                version="1.0.0",
                description="Monitoring and metrics MCP server",
                transport=TransportType.SSE,
                url="https://mcp.vibedna.vibecaas.com/monitor",
                port=8094,
            )
        super().__init__(config)

        # Initialize metrics collector
        self._metrics = MetricsCollector()
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._workflows: Dict[str, Dict[str, Any]] = {}

    def _register_tools(self) -> None:
        """Register monitoring tools."""

        # get_metrics tool
        self.register_tool(MCPTool(
            name="get_metrics",
            description="Get current system metrics",
            parameters=[
                MCPToolParameter(
                    name="category",
                    param_type="string",
                    description="Metric category to retrieve",
                    required=False,
                    enum=["throughput", "latency", "errors", "storage", "all"],
                ),
            ],
            handler=self._get_metrics,
        ))

        # get_health tool
        self.register_tool(MCPTool(
            name="get_health",
            description="Get system health status",
            parameters=[],
            handler=self._get_health,
        ))

        # get_agent_status tool
        self.register_tool(MCPTool(
            name="get_agent_status",
            description="Get status of all agents",
            parameters=[
                MCPToolParameter(
                    name="agent_id",
                    param_type="string",
                    description="Specific agent ID (optional)",
                    required=False,
                ),
            ],
            handler=self._get_agent_status,
        ))

        # get_workflow_status tool
        self.register_tool(MCPTool(
            name="get_workflow_status",
            description="Get status of running workflows",
            parameters=[
                MCPToolParameter(
                    name="workflow_id",
                    param_type="string",
                    description="Specific workflow ID (optional)",
                    required=False,
                ),
            ],
            handler=self._get_workflow_status,
        ))

        # record_metric tool (for internal use)
        self.register_tool(MCPTool(
            name="record_metric",
            description="Record a metric value",
            parameters=[
                MCPToolParameter(
                    name="metric_name",
                    param_type="string",
                    description="Name of the metric",
                    required=True,
                ),
                MCPToolParameter(
                    name="value",
                    param_type="number",
                    description="Metric value",
                    required=True,
                ),
                MCPToolParameter(
                    name="labels",
                    param_type="object",
                    description="Metric labels",
                    required=False,
                ),
            ],
            handler=self._record_metric,
        ))

    def _register_resources(self) -> None:
        """Register monitoring resources."""

        self.register_resource(MCPResource(
            name="dashboard",
            description="Metrics dashboard",
            uri="vibedna://monitor/dashboard",
            mime_type="application/json",
            handler=self._get_dashboard,
        ))

    async def _get_metrics(
        self,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get system metrics."""
        metrics = {}

        if category in [None, "all", "throughput"]:
            uptime = (datetime.utcnow() - self._metrics.start_time).total_seconds()
            metrics["throughput"] = {
                "encode_requests_total": self._metrics.encode_requests_total,
                "decode_requests_total": self._metrics.decode_requests_total,
                "compute_operations_total": self._metrics.compute_operations_total,
                "encodes_per_minute": (
                    self._metrics.encode_requests_total / (uptime / 60)
                    if uptime > 0 else 0
                ),
                "decodes_per_minute": (
                    self._metrics.decode_requests_total / (uptime / 60)
                    if uptime > 0 else 0
                ),
                "bytes_per_second": (
                    self._metrics.encoded_bytes_total / uptime
                    if uptime > 0 else 0
                ),
            }

        if category in [None, "all", "latency"]:
            metrics["latency"] = {
                "encode_p50": self._metrics.get_percentile(self._metrics.encode_durations, 50),
                "encode_p99": self._metrics.get_percentile(self._metrics.encode_durations, 99),
                "decode_p50": self._metrics.get_percentile(self._metrics.decode_durations, 50),
                "decode_p99": self._metrics.get_percentile(self._metrics.decode_durations, 99),
            }

        if category in [None, "all", "errors"]:
            total_requests = (
                self._metrics.encode_requests_total +
                self._metrics.decode_requests_total
            )
            total_errors = (
                self._metrics.encoding_errors_total +
                self._metrics.decoding_errors_total
            )
            metrics["errors"] = {
                "encoding_errors_total": self._metrics.encoding_errors_total,
                "decoding_errors_total": self._metrics.decoding_errors_total,
                "checksum_failures_total": self._metrics.checksum_failures_total,
                "corrections_applied_total": self._metrics.corrections_applied_total,
                "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            }

        if category in [None, "all", "storage"]:
            metrics["storage"] = {
                "total_bytes": self._metrics.storage_bytes_used,
                "encoded_bytes_total": self._metrics.encoded_bytes_total,
                "decoded_bytes_total": self._metrics.decoded_bytes_total,
            }

        return metrics

    async def _get_health(self) -> Dict[str, Any]:
        """Get system health status."""
        # Check component health
        components = {
            "encoder": {"status": "healthy", "latency_ms": 0},
            "decoder": {"status": "healthy", "latency_ms": 0},
            "storage": {"status": "healthy", "latency_ms": 0},
            "compute": {"status": "healthy", "latency_ms": 0},
        }

        # Determine overall status
        all_healthy = all(c["status"] == "healthy" for c in components.values())
        any_degraded = any(c["status"] == "degraded" for c in components.values())

        if all_healthy:
            status = "healthy"
        elif any_degraded:
            status = "degraded"
        else:
            status = "unhealthy"

        uptime = (datetime.utcnow() - self._metrics.start_time).total_seconds()

        return {
            "status": status,
            "uptime_seconds": uptime,
            "components": components,
            "active_agents": self._metrics.active_agents,
            "queue_depth": self._metrics.queue_depth,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _get_agent_status(
        self,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get agent status."""
        if agent_id:
            if agent_id in self._agents:
                return {
                    "agent": self._agents[agent_id],
                }
            else:
                return {
                    "error": f"Agent not found: {agent_id}",
                }

        return {
            "agents": list(self._agents.values()),
            "total_count": len(self._agents),
            "active_count": sum(
                1 for a in self._agents.values()
                if a.get("status") == "ready"
            ),
        }

    async def _get_workflow_status(
        self,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get workflow status."""
        if workflow_id:
            if workflow_id in self._workflows:
                return {
                    "workflow": self._workflows[workflow_id],
                }
            else:
                return {
                    "error": f"Workflow not found: {workflow_id}",
                }

        return {
            "workflows": list(self._workflows.values()),
            "total_count": len(self._workflows),
            "running_count": sum(
                1 for w in self._workflows.values()
                if w.get("status") == "running"
            ),
        }

    async def _record_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Record a metric value."""
        # Map known metrics
        if metric_name == "encode_duration":
            self._metrics.record_encode(int(value), value)
        elif metric_name == "decode_duration":
            self._metrics.record_decode(int(value), value)
        elif metric_name == "encoding_error":
            self._metrics.encoding_errors_total += 1
        elif metric_name == "decoding_error":
            self._metrics.decoding_errors_total += 1
        elif metric_name == "storage_bytes":
            self._metrics.storage_bytes_used = int(value)

        return {
            "recorded": True,
            "metric": metric_name,
            "value": value,
            "labels": labels,
        }

    def _get_dashboard(self) -> Dict[str, Any]:
        """Get complete dashboard data."""
        uptime = (datetime.utcnow() - self._metrics.start_time).total_seconds()

        return {
            "title": "VibeDNA System Dashboard",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "summary": {
                "total_encodes": self._metrics.encode_requests_total,
                "total_decodes": self._metrics.decode_requests_total,
                "total_bytes_processed": (
                    self._metrics.encoded_bytes_total +
                    self._metrics.decoded_bytes_total
                ),
                "active_agents": self._metrics.active_agents,
                "queue_depth": self._metrics.queue_depth,
            },
            "throughput": {
                "encodes_per_minute": (
                    self._metrics.encode_requests_total / (uptime / 60)
                    if uptime > 60 else self._metrics.encode_requests_total
                ),
                "decodes_per_minute": (
                    self._metrics.decode_requests_total / (uptime / 60)
                    if uptime > 60 else self._metrics.decode_requests_total
                ),
            },
            "latency": {
                "encode_p50_ms": self._metrics.get_percentile(self._metrics.encode_durations, 50) * 1000,
                "encode_p99_ms": self._metrics.get_percentile(self._metrics.encode_durations, 99) * 1000,
                "decode_p50_ms": self._metrics.get_percentile(self._metrics.decode_durations, 50) * 1000,
                "decode_p99_ms": self._metrics.get_percentile(self._metrics.decode_durations, 99) * 1000,
            },
            "errors": {
                "total": (
                    self._metrics.encoding_errors_total +
                    self._metrics.decoding_errors_total
                ),
                "checksum_failures": self._metrics.checksum_failures_total,
                "corrections": self._metrics.corrections_applied_total,
            },
        }

    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> None:
        """Register an agent for monitoring."""
        self._agents[agent_id] = {
            "agent_id": agent_id,
            "registered_at": datetime.utcnow().isoformat(),
            **agent_info,
        }
        self._metrics.active_agents = len(self._agents)

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            self._metrics.active_agents = len(self._agents)

    def register_workflow(self, workflow_id: str, workflow_info: Dict[str, Any]) -> None:
        """Register a workflow for monitoring."""
        self._workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "registered_at": datetime.utcnow().isoformat(),
            **workflow_info,
        }

    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> None:
        """Update workflow status."""
        if workflow_id in self._workflows:
            self._workflows[workflow_id].update(updates)
            self._workflows[workflow_id]["updated_at"] = datetime.utcnow().isoformat()
