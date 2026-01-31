# VibeDNA Agent Message Types
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Message types for inter-agent communication in the VibeDNA system.

This module defines the message formats used for task requests,
responses, and inter-agent messaging.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class MessageType(Enum):
    """Types of messages in the agent system."""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    TASK_UPDATE = "task_update"
    HEARTBEAT = "heartbeat"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    LOG = "log"
    METRIC = "metric"
    WORKFLOW_EVENT = "workflow_event"
    RESOURCE_ALLOCATION = "resource_allocation"


class TaskStatus(Enum):
    """Status of a task in the system."""
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


class TaskPriority(Enum):
    """Priority levels for tasks."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class OperationType(Enum):
    """Types of operations that can be requested."""
    ENCODE = "encode"
    DECODE = "decode"
    COMPUTE = "compute"
    STORE = "store"
    RETRIEVE = "retrieve"
    VALIDATE = "validate"
    VISUALIZE = "visualize"
    SYNTHESIZE = "synthesize"
    BATCH_PROCESS = "batch_process"
    ERROR_CORRECT = "error_correct"
    INDEX = "index"
    SEARCH = "search"


@dataclass
class AgentMessage:
    """Base message class for inter-agent communication."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.LOG
    sender_id: str = ""
    receiver_id: Optional[str] = None  # None for broadcast
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None  # For request-response correlation
    ttl_seconds: Optional[float] = None  # Time-to-live


@dataclass
class TaskRequest:
    """Request for an agent to perform a task."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: OperationType = OperationType.ENCODE
    priority: TaskPriority = TaskPriority.NORMAL
    source_agent: str = ""
    target_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    callbacks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request_id": self.request_id,
            "operation": self.operation.value,
            "priority": self.priority.value,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "created_at": self.created_at.isoformat(),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "parameters": self.parameters,
            "context": self.context,
            "callbacks": self.callbacks,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskRequest":
        """Create from dictionary representation."""
        return cls(
            request_id=data.get("request_id", str(uuid.uuid4())),
            operation=OperationType(data.get("operation", "encode")),
            priority=TaskPriority(data.get("priority", 2)),
            source_agent=data.get("source_agent", ""),
            target_agent=data.get("target_agent"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            parameters=data.get("parameters", {}),
            context=data.get("context", {}),
            callbacks=data.get("callbacks", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TaskResponse:
    """Response from an agent after processing a task."""
    request_id: str
    status: TaskStatus = TaskStatus.COMPLETED
    completed_at: datetime = field(default_factory=datetime.utcnow)
    result: Optional[Any] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    workflow_trace: List[Dict[str, Any]] = field(default_factory=list)
    quality_report: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    footer: str = "© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "completed_at": self.completed_at.isoformat(),
            "result": self.result,
            "error": self.error,
            "warnings": self.warnings,
            "workflow_trace": self.workflow_trace,
            "quality_report": self.quality_report,
            "metrics": self.metrics,
            "metadata": self.metadata,
            "footer": self.footer,
        }

    @classmethod
    def success(cls, request_id: str, result: Any, **kwargs) -> "TaskResponse":
        """Create a successful response."""
        return cls(
            request_id=request_id,
            status=TaskStatus.COMPLETED,
            result=result,
            **kwargs,
        )

    @classmethod
    def failure(cls, request_id: str, error: str, **kwargs) -> "TaskResponse":
        """Create a failure response."""
        return cls(
            request_id=request_id,
            status=TaskStatus.FAILED,
            error=error,
            **kwargs,
        )

    @classmethod
    def partial(cls, request_id: str, result: Any, error: str, **kwargs) -> "TaskResponse":
        """Create a partial success response."""
        return cls(
            request_id=request_id,
            status=TaskStatus.PARTIAL,
            result=result,
            error=error,
            **kwargs,
        )


@dataclass
class WorkflowStep:
    """A step in a workflow execution."""
    step_id: str
    agent_id: str
    action: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: Optional[float] = None


@dataclass
class QualityReport:
    """Quality assessment report for a task result."""
    checksum_valid: bool = True
    error_correction_applied: bool = False
    errors_detected: int = 0
    errors_corrected: int = 0
    gc_content: Optional[float] = None
    homopolymer_max: Optional[int] = None
    synthesis_compatible: bool = True
    validation_passed: bool = True
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "checksum_valid": self.checksum_valid,
            "error_correction_applied": self.error_correction_applied,
            "errors_detected": self.errors_detected,
            "errors_corrected": self.errors_corrected,
            "gc_content": self.gc_content,
            "homopolymer_max": self.homopolymer_max,
            "synthesis_compatible": self.synthesis_compatible,
            "validation_passed": self.validation_passed,
            "warnings": self.warnings,
        }


@dataclass
class DelegationMatrix:
    """Defines which agents handle which operations."""
    operation_agents: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default delegation matrix."""
        if not self.operation_agents:
            self.operation_agents = {
                "encode": {
                    "primary": ["encoder-agent"],
                    "support": ["validation-agent", "error-correction-agent"],
                },
                "decode": {
                    "primary": ["decoder-agent"],
                    "support": ["error-correction-agent", "validation-agent"],
                },
                "compute": {
                    "primary": ["compute-agent"],
                    "support": ["validation-agent"],
                },
                "store": {
                    "primary": ["filesystem-agent"],
                    "support": ["encoder-agent", "index-agent"],
                },
                "retrieve": {
                    "primary": ["filesystem-agent"],
                    "support": ["decoder-agent", "index-agent"],
                },
                "validate": {
                    "primary": ["validation-agent"],
                    "support": ["error-correction-agent"],
                },
                "visualize": {
                    "primary": ["visualization-agent"],
                    "support": ["decoder-agent"],
                },
                "batch_process": {
                    "primary": ["workflow-orchestrator"],
                    "support": ["all-specialists"],
                },
            }

    def get_agents_for_operation(self, operation: str) -> Dict[str, List[str]]:
        """Get the agents assigned to handle an operation."""
        return self.operation_agents.get(operation, {"primary": [], "support": []})
