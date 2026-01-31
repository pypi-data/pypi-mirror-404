# VibeDNA Resource Orchestrator
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Resource Orchestrator - Operational resource manager for the VibeDNA system.

The Resource Orchestrator is responsible for:
- Resource allocation and scheduling
- Load balancing across agent pools
- Memory management for large sequences
- Rate limiting and quota enforcement
- Auto-scaling triggers
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import random
import uuid

from vibedna.agents.base.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentTier,
    AgentHealth,
)
from vibedna.agents.base.message import (
    TaskRequest,
    TaskResponse,
    TaskStatus,
    TaskPriority,
    OperationType,
)
from vibedna.agents.base.context import ResourceAllocation


@dataclass
class AgentPoolConfig:
    """Configuration for an agent pool."""
    pool_name: str
    min_instances: int = 2
    max_instances: int = 10
    scale_up_threshold: float = 0.8  # CPU utilization
    scale_down_threshold: float = 0.3
    cooldown_period: int = 300  # seconds


@dataclass
class AgentInstance:
    """Represents an agent instance in a pool."""
    instance_id: str
    pool_name: str
    agent: Optional[BaseAgent] = None
    current_load: float = 0.0
    tasks_active: int = 0
    tasks_completed: int = 0
    last_task_at: Optional[datetime] = None
    cache_keys: List[str] = field(default_factory=list)
    health: str = "healthy"


@dataclass
class QuotaConfig:
    """Quota configuration."""
    encode_requests_per_hour: int = 1000
    decode_requests_per_hour: int = 1000
    compute_operations_per_hour: int = 500
    storage_bytes: int = 10 * 1024 * 1024 * 1024  # 10 GB
    max_input_size: int = 100 * 1024 * 1024  # 100 MB
    max_sequence_length: int = 1_000_000_000  # 1B nucleotides
    timeout_seconds: int = 3600


@dataclass
class QuotaUsage:
    """Tracks quota usage."""
    user_id: str
    encode_requests: int = 0
    decode_requests: int = 0
    compute_operations: int = 0
    storage_bytes_used: int = 0
    period_start: datetime = field(default_factory=datetime.utcnow)


class ResourceOrchestrator(BaseAgent):
    """
    Resource Orchestrator for the VibeDNA Agent System.

    Manages compute resources, handles load balancing, monitors utilization,
    and optimizes for throughput or latency based on requirements.
    """

    # Default pool configurations
    DEFAULT_POOLS = {
        "encoder_pool": AgentPoolConfig("encoder_pool", 2, 10, 0.8, 0.3),
        "decoder_pool": AgentPoolConfig("decoder_pool", 2, 10, 0.8, 0.3),
        "compute_pool": AgentPoolConfig("compute_pool", 1, 5, 0.7, 0.3),
        "filesystem_pool": AgentPoolConfig("filesystem_pool", 2, 8, 0.75, 0.3),
        "validation_pool": AgentPoolConfig("validation_pool", 2, 6, 0.8, 0.3),
    }

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Resource Orchestrator."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-resource-orchestrator",
                version="1.0.0",
                tier=AgentTier.ORCHESTRATION,
                role="Operational Resource Manager",
                description="Manages computational resources for DNA processing",
                capabilities=[
                    AgentCapability(
                        name="resource_allocation",
                        description="Allocate resources for tasks",
                    ),
                    AgentCapability(
                        name="load_balancing",
                        description="Balance load across agent pools",
                    ),
                    AgentCapability(
                        name="quota_management",
                        description="Enforce usage quotas",
                    ),
                    AgentCapability(
                        name="auto_scaling",
                        description="Trigger auto-scaling based on load",
                    ),
                ],
                tools=[
                    "resource_monitor",
                    "pool_scaler",
                    "quota_enforcer",
                    "load_balancer",
                    "cache_manager",
                ],
                mcp_connections=["vibedna-monitor"],
            )

        super().__init__(config)

        # Agent pools
        self._pools: Dict[str, AgentPoolConfig] = dict(self.DEFAULT_POOLS)
        self._pool_instances: Dict[str, List[AgentInstance]] = {}

        # Active allocations
        self._allocations: Dict[str, ResourceAllocation] = {}

        # Quota tracking
        self._quotas: Dict[str, QuotaConfig] = {"default": QuotaConfig()}
        self._usage: Dict[str, QuotaUsage] = {}

        # Scaling state
        self._last_scale_action: Dict[str, datetime] = {}

        # Request queue for rate limiting
        self._request_queue: List[TaskRequest] = []

    def get_system_prompt(self) -> str:
        """Get the Resource Orchestrator's system prompt."""
        return """You are the VibeDNA Resource Orchestrator, managing computational resources
for DNA processing operations.

## Resource Model

Resource Types:
├── Compute
│   ├── CPU cores (for encoding/decoding)
│   ├── Memory (for sequence buffers)
│   └── GPU (optional, for parallel operations)
├── Storage
│   ├── Hot storage (active sequences)
│   ├── Warm storage (recent sequences)
│   └── Cold storage (archived sequences)
└── Network
    ├── Internal bandwidth (agent communication)
    └── External bandwidth (API responses)

## Allocation Strategy

1. Estimate resource requirements based on task type
2. Check availability in appropriate pool
3. If not available, queue or preempt lower priority
4. Allocate with 20% buffer
5. Set timeout based on estimated duration

## Load Balancing

Use weighted round-robin with:
- Inverse of current load as weight
- Cache affinity bonus (2x for warm cache)
- Health check filtering

## Quota Enforcement

Per user per hour:
- encode_requests: 1000
- decode_requests: 1000
- compute_operations: 500
- storage: 10 GB

Per request:
- max_input_size: 100 MB
- max_sequence_length: 1B nucleotides
- timeout: 3600 seconds

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a resource management request."""
        action = request.parameters.get("action", "allocate")

        if action == "allocate":
            return await self._handle_allocate(request)
        elif action == "release":
            return await self._handle_release(request)
        elif action == "check_quota":
            return await self._handle_check_quota(request)
        elif action == "get_stats":
            return await self._handle_get_stats(request)
        elif action == "select_agent":
            return await self._handle_select_agent(request)
        elif action == "scale":
            return await self._handle_scale(request)
        else:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown action: {action}",
            )

    async def _handle_allocate(self, request: TaskRequest) -> TaskResponse:
        """Allocate resources for a task."""
        task_id = request.parameters.get("task_id", request.request_id)
        task_type = request.parameters.get("task_type", "encode")
        priority = request.parameters.get("priority", TaskPriority.NORMAL.value)
        input_size = request.parameters.get("input_size", 0)
        user_id = request.parameters.get("user_id", "default")

        # Check quota
        quota_check = self._check_quota(user_id, task_type, input_size)
        if not quota_check["allowed"]:
            return TaskResponse.failure(
                request.request_id,
                f"Quota exceeded: {quota_check['reason']}",
            )

        # Estimate requirements
        memory_bytes = self._estimate_memory(task_type, input_size)
        cpu_cores = self._estimate_cpu(task_type, input_size)
        timeout = self._estimate_timeout(task_type, input_size)

        # Select pool
        pool_name = self._get_pool_for_task(task_type)

        # Check availability
        pool_instances = self._pool_instances.get(pool_name, [])
        available_capacity = sum(
            1 - inst.current_load
            for inst in pool_instances
            if inst.health == "healthy"
        )

        if available_capacity < 0.1:  # Less than 10% capacity
            if priority == TaskPriority.CRITICAL.value:
                # Try to preempt lower priority tasks
                self.logger.info("Attempting to preempt lower priority tasks")
            else:
                # Queue the request
                self._request_queue.append(request)
                return TaskResponse(
                    request_id=request.request_id,
                    status=TaskStatus.QUEUED,
                    result={
                        "queued": True,
                        "queue_position": len(self._request_queue),
                    },
                )

        # Create allocation
        allocation = ResourceAllocation(
            task_id=task_id,
            agent_id="",  # Will be set when agent is selected
            memory_bytes=int(memory_bytes * 1.2),  # 20% buffer
            cpu_cores=cpu_cores,
            timeout_seconds=timeout * 2,
            priority=priority,
            expires_at=datetime.utcnow() + timedelta(seconds=timeout * 2),
        )

        self._allocations[allocation.allocation_id] = allocation

        # Update quota usage
        self._record_usage(user_id, task_type)

        return TaskResponse.success(
            request.request_id,
            {
                "allocation_id": allocation.allocation_id,
                "memory_bytes": allocation.memory_bytes,
                "cpu_cores": allocation.cpu_cores,
                "timeout_seconds": allocation.timeout_seconds,
                "pool": pool_name,
            },
        )

    async def _handle_release(self, request: TaskRequest) -> TaskResponse:
        """Release allocated resources."""
        allocation_id = request.parameters.get("allocation_id")

        if allocation_id not in self._allocations:
            return TaskResponse.failure(
                request.request_id,
                f"Allocation not found: {allocation_id}",
            )

        del self._allocations[allocation_id]

        # Process queued requests
        if self._request_queue:
            queued = self._request_queue.pop(0)
            asyncio.create_task(self._handle_allocate(queued))

        return TaskResponse.success(
            request.request_id,
            {"released": True, "allocation_id": allocation_id},
        )

    async def _handle_check_quota(self, request: TaskRequest) -> TaskResponse:
        """Check quota for a user."""
        user_id = request.parameters.get("user_id", "default")
        task_type = request.parameters.get("task_type")
        input_size = request.parameters.get("input_size", 0)

        result = self._check_quota(user_id, task_type, input_size)

        return TaskResponse.success(request.request_id, result)

    async def _handle_get_stats(self, request: TaskRequest) -> TaskResponse:
        """Get resource statistics."""
        stats = {
            "pools": {},
            "allocations": {
                "active": len(self._allocations),
                "total_memory": sum(a.memory_bytes for a in self._allocations.values()),
            },
            "queue_depth": len(self._request_queue),
        }

        for pool_name, pool_config in self._pools.items():
            instances = self._pool_instances.get(pool_name, [])
            healthy = [i for i in instances if i.health == "healthy"]
            stats["pools"][pool_name] = {
                "instances": len(instances),
                "healthy": len(healthy),
                "avg_load": (
                    sum(i.current_load for i in instances) / len(instances)
                    if instances else 0
                ),
                "config": {
                    "min": pool_config.min_instances,
                    "max": pool_config.max_instances,
                },
            }

        return TaskResponse.success(request.request_id, stats)

    async def _handle_select_agent(self, request: TaskRequest) -> TaskResponse:
        """Select an agent from a pool for a task."""
        pool_name = request.parameters.get("pool")
        cache_key = request.parameters.get("cache_key")

        if pool_name not in self._pools:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown pool: {pool_name}",
            )

        instances = self._pool_instances.get(pool_name, [])
        healthy = [i for i in instances if i.health == "healthy"]

        if not healthy:
            return TaskResponse.failure(
                request.request_id,
                f"No healthy agents in pool: {pool_name}",
            )

        # Weighted selection
        selected = self._select_agent_weighted(healthy, cache_key)

        return TaskResponse.success(
            request.request_id,
            {
                "instance_id": selected.instance_id,
                "agent_id": selected.agent.agent_id if selected.agent else None,
                "current_load": selected.current_load,
            },
        )

    async def _handle_scale(self, request: TaskRequest) -> TaskResponse:
        """Handle scaling request."""
        pool_name = request.parameters.get("pool")
        direction = request.parameters.get("direction", "auto")  # up, down, auto

        if pool_name not in self._pools:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown pool: {pool_name}",
            )

        pool_config = self._pools[pool_name]
        instances = self._pool_instances.get(pool_name, [])

        # Check cooldown
        last_scale = self._last_scale_action.get(pool_name)
        if last_scale:
            elapsed = (datetime.utcnow() - last_scale).total_seconds()
            if elapsed < pool_config.cooldown_period:
                return TaskResponse.success(
                    request.request_id,
                    {"scaled": False, "reason": "cooldown_period"},
                )

        # Calculate average load
        avg_load = (
            sum(i.current_load for i in instances) / len(instances)
            if instances else 0
        )

        scaled = False
        new_count = len(instances)

        if direction == "up" or (direction == "auto" and avg_load > pool_config.scale_up_threshold):
            if len(instances) < pool_config.max_instances:
                # Scale up
                new_count = min(len(instances) + 1, pool_config.max_instances)
                scaled = True

        elif direction == "down" or (direction == "auto" and avg_load < pool_config.scale_down_threshold):
            if len(instances) > pool_config.min_instances:
                # Scale down
                new_count = max(len(instances) - 1, pool_config.min_instances)
                scaled = True

        if scaled:
            self._last_scale_action[pool_name] = datetime.utcnow()

        return TaskResponse.success(
            request.request_id,
            {
                "scaled": scaled,
                "pool": pool_name,
                "previous_count": len(instances),
                "new_count": new_count,
                "avg_load": avg_load,
            },
        )

    def _estimate_memory(self, task_type: str, input_size: int) -> int:
        """Estimate memory requirements for a task."""
        if task_type == "encode":
            # Input size * 2 (binary string) + output * 2.5 (DNA + headers)
            return int(input_size * 4.5)
        elif task_type == "decode":
            # DNA length / 4 * 1.5 (with error correction buffers)
            return int(input_size * 0.375)
        elif task_type == "compute":
            # Both sequences + result + intermediate
            return int(input_size * 4)
        else:
            return input_size * 2

    def _estimate_cpu(self, task_type: str, input_size: int) -> int:
        """Estimate CPU cores needed."""
        # For now, always 1 core
        # Could scale based on input size for parallel processing
        if input_size > 10 * 1024 * 1024:  # > 10MB
            return 2
        return 1

    def _estimate_timeout(self, task_type: str, input_size: int) -> float:
        """Estimate timeout in seconds."""
        # Base time + time per MB
        base_time = 10.0
        time_per_mb = 0.5
        mb = input_size / (1024 * 1024)

        return base_time + (time_per_mb * mb)

    def _get_pool_for_task(self, task_type: str) -> str:
        """Get the appropriate pool for a task type."""
        pool_map = {
            "encode": "encoder_pool",
            "decode": "decoder_pool",
            "compute": "compute_pool",
            "store": "filesystem_pool",
            "retrieve": "filesystem_pool",
            "validate": "validation_pool",
        }
        return pool_map.get(task_type, "encoder_pool")

    def _check_quota(
        self,
        user_id: str,
        task_type: Optional[str],
        input_size: int,
    ) -> Dict[str, Any]:
        """Check if request is within quota."""
        quota = self._quotas.get(user_id, self._quotas["default"])
        usage = self._usage.get(user_id)

        # Reset usage if period expired
        if usage:
            period_elapsed = datetime.utcnow() - usage.period_start
            if period_elapsed > timedelta(hours=1):
                usage = None

        if not usage:
            usage = QuotaUsage(user_id=user_id)
            self._usage[user_id] = usage

        # Check per-request limits
        if input_size > quota.max_input_size:
            return {
                "allowed": False,
                "reason": f"Input size {input_size} exceeds max {quota.max_input_size}",
            }

        # Check rate limits
        if task_type == "encode" and usage.encode_requests >= quota.encode_requests_per_hour:
            return {
                "allowed": False,
                "reason": "Encode request rate limit exceeded",
            }
        elif task_type == "decode" and usage.decode_requests >= quota.decode_requests_per_hour:
            return {
                "allowed": False,
                "reason": "Decode request rate limit exceeded",
            }
        elif task_type == "compute" and usage.compute_operations >= quota.compute_operations_per_hour:
            return {
                "allowed": False,
                "reason": "Compute operation rate limit exceeded",
            }

        return {"allowed": True}

    def _record_usage(self, user_id: str, task_type: str) -> None:
        """Record resource usage."""
        if user_id not in self._usage:
            self._usage[user_id] = QuotaUsage(user_id=user_id)

        usage = self._usage[user_id]

        if task_type == "encode":
            usage.encode_requests += 1
        elif task_type == "decode":
            usage.decode_requests += 1
        elif task_type == "compute":
            usage.compute_operations += 1

    def _select_agent_weighted(
        self,
        instances: List[AgentInstance],
        cache_key: Optional[str],
    ) -> AgentInstance:
        """Select an agent using weighted round-robin."""
        # Calculate weights based on inverse of load
        weights = []
        for inst in instances:
            weight = 1 / (inst.current_load + 0.1)

            # Bonus for cache affinity
            if cache_key and cache_key in inst.cache_keys:
                weight *= 2

            weights.append(weight)

        # Weighted random selection
        return random.choices(instances, weights=weights, k=1)[0]

    def register_pool_instance(
        self,
        pool_name: str,
        agent: Optional[BaseAgent] = None,
    ) -> AgentInstance:
        """Register a new instance in a pool."""
        instance = AgentInstance(
            instance_id=str(uuid.uuid4()),
            pool_name=pool_name,
            agent=agent,
        )

        if pool_name not in self._pool_instances:
            self._pool_instances[pool_name] = []

        self._pool_instances[pool_name].append(instance)
        return instance

    def update_instance_load(self, instance_id: str, load: float) -> None:
        """Update the load of an instance."""
        for instances in self._pool_instances.values():
            for inst in instances:
                if inst.instance_id == instance_id:
                    inst.current_load = load
                    return

    def set_quota(self, user_id: str, quota: QuotaConfig) -> None:
        """Set quota for a user."""
        self._quotas[user_id] = quota
