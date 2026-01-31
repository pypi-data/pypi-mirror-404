# VibeDNA Metrics Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Metrics Agent - Performance monitoring and metrics collection.

Collects and reports:
- Throughput metrics
- Latency metrics
- Error rates
- Resource utilization
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

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


@dataclass
class MetricsStore:
    """In-memory metrics storage."""
    encode_requests: int = 0
    decode_requests: int = 0
    compute_operations: int = 0
    encoding_errors: int = 0
    decoding_errors: int = 0
    encode_durations: List[float] = field(default_factory=list)
    decode_durations: List[float] = field(default_factory=list)
    storage_bytes: int = 0
    start_time: datetime = field(default_factory=datetime.utcnow)


class MetricsAgent(BaseAgent):
    """
    Metrics Agent for performance monitoring.

    Collects, aggregates, and reports system metrics
    for monitoring and alerting.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Metrics Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-metrics-agent",
                version="1.0.0",
                tier=AgentTier.SUPPORT,
                role="Performance Monitoring",
                description="Collects and reports performance metrics",
                capabilities=[
                    AgentCapability(
                        name="metrics_collection",
                        description="Collect system metrics",
                    ),
                    AgentCapability(
                        name="dashboard_generation",
                        description="Generate metrics dashboards",
                    ),
                    AgentCapability(
                        name="alerting",
                        description="Alert on thresholds",
                    ),
                ],
                tools=[
                    "metrics_collector",
                    "dashboard_generator",
                    "alert_manager",
                ],
                mcp_connections=["vibedna-monitor"],
            )

        super().__init__(config)
        self._metrics = MetricsStore()

    def get_system_prompt(self) -> str:
        """Get the Metrics Agent's system prompt."""
        return """You are the VibeDNA Metrics Agent, monitoring system performance.

## Metrics Categories

1. Throughput - Requests per minute, bytes processed
2. Latency - P50, P99 response times
3. Errors - Error rates, failure counts
4. Resources - Memory, CPU, storage usage

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a metrics task."""
        action = request.parameters.get("action", "get_metrics")

        if action == "record":
            return await self._record_metric(request)
        elif action == "get_metrics":
            return await self._get_metrics(request)
        elif action == "get_dashboard":
            return await self._get_dashboard(request)
        elif action == "reset":
            return await self._reset_metrics(request)
        else:
            return TaskResponse.failure(request.request_id, f"Unknown action: {action}")

    async def _record_metric(self, request: TaskRequest) -> TaskResponse:
        """Record a metric value."""
        try:
            metric_name = request.parameters.get("metric")
            value = request.parameters.get("value")

            if metric_name == "encode_request":
                self._metrics.encode_requests += 1
            elif metric_name == "decode_request":
                self._metrics.decode_requests += 1
            elif metric_name == "compute_operation":
                self._metrics.compute_operations += 1
            elif metric_name == "encode_duration":
                self._metrics.encode_durations.append(float(value))
                if len(self._metrics.encode_durations) > 1000:
                    self._metrics.encode_durations = self._metrics.encode_durations[-1000:]
            elif metric_name == "decode_duration":
                self._metrics.decode_durations.append(float(value))
                if len(self._metrics.decode_durations) > 1000:
                    self._metrics.decode_durations = self._metrics.decode_durations[-1000:]
            elif metric_name == "encoding_error":
                self._metrics.encoding_errors += 1
            elif metric_name == "decoding_error":
                self._metrics.decoding_errors += 1
            elif metric_name == "storage_bytes":
                self._metrics.storage_bytes = int(value)

            return TaskResponse.success(
                request.request_id,
                {"recorded": True, "metric": metric_name},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _get_metrics(self, request: TaskRequest) -> TaskResponse:
        """Get current metrics."""
        try:
            category = request.parameters.get("category", "all")
            uptime = (datetime.utcnow() - self._metrics.start_time).total_seconds()

            metrics = {}

            if category in ["all", "throughput"]:
                metrics["throughput"] = {
                    "encode_requests": self._metrics.encode_requests,
                    "decode_requests": self._metrics.decode_requests,
                    "compute_operations": self._metrics.compute_operations,
                    "encodes_per_minute": self._metrics.encode_requests / (uptime / 60) if uptime > 0 else 0,
                }

            if category in ["all", "latency"]:
                metrics["latency"] = {
                    "encode_p50": self._percentile(self._metrics.encode_durations, 50),
                    "encode_p99": self._percentile(self._metrics.encode_durations, 99),
                    "decode_p50": self._percentile(self._metrics.decode_durations, 50),
                    "decode_p99": self._percentile(self._metrics.decode_durations, 99),
                }

            if category in ["all", "errors"]:
                total = self._metrics.encode_requests + self._metrics.decode_requests
                errors = self._metrics.encoding_errors + self._metrics.decoding_errors
                metrics["errors"] = {
                    "encoding_errors": self._metrics.encoding_errors,
                    "decoding_errors": self._metrics.decoding_errors,
                    "error_rate": errors / total if total > 0 else 0,
                }

            if category in ["all", "storage"]:
                metrics["storage"] = {
                    "bytes_used": self._metrics.storage_bytes,
                }

            return TaskResponse.success(request.request_id, metrics)

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _get_dashboard(self, request: TaskRequest) -> TaskResponse:
        """Get metrics dashboard."""
        try:
            metrics_result = await self._get_metrics(
                TaskRequest(parameters={"category": "all"})
            )

            uptime = (datetime.utcnow() - self._metrics.start_time).total_seconds()

            dashboard = {
                "title": "VibeDNA Metrics Dashboard",
                "uptime_seconds": uptime,
                "metrics": metrics_result.result,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return TaskResponse.success(request.request_id, dashboard)

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _reset_metrics(self, request: TaskRequest) -> TaskResponse:
        """Reset all metrics."""
        self._metrics = MetricsStore()
        return TaskResponse.success(request.request_id, {"reset": True})

    def _percentile(self, values: List[float], p: int) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        idx = int(len(sorted_values) * p / 100)
        return sorted_values[min(idx, len(sorted_values) - 1)]
