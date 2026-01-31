# VibeDNA Agent Context
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Context management for VibeDNA agents and workflows.

This module provides context objects that carry state and configuration
throughout agent operations and workflow executions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import uuid
import copy


@dataclass
class AgentContext:
    """
    Context for a single agent operation.

    Carries state, configuration, and accumulated data during
    task processing.
    """
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Request information
    request_id: Optional[str] = None
    operation: Optional[str] = None

    # Data passing
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    intermediate_data: Dict[str, Any] = field(default_factory=dict)

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Execution tracking
    steps_completed: List[str] = field(default_factory=list)
    current_step: Optional[str] = None

    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context."""
        self.intermediate_data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context."""
        return self.intermediate_data.get(key, default)

    def add_error(self, error: str, code: Optional[str] = None, severity: str = "error") -> None:
        """Add an error to the context."""
        self.errors.append({
            "message": error,
            "code": code,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "step": self.current_step,
        })

    def add_warning(self, warning: str) -> None:
        """Add a warning to the context."""
        self.warnings.append(warning)

    def record_metric(self, name: str, value: Any) -> None:
        """Record a metric value."""
        self.metrics[name] = value

    def complete_step(self, step_name: str) -> None:
        """Mark a step as completed."""
        self.steps_completed.append(step_name)
        self.current_step = None

    def start_step(self, step_name: str) -> None:
        """Start a new step."""
        self.current_step = step_name

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def clone(self) -> "AgentContext":
        """Create a deep copy of the context."""
        return AgentContext(
            context_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            request_id=self.request_id,
            operation=self.operation,
            input_data=copy.deepcopy(self.input_data),
            output_data=copy.deepcopy(self.output_data),
            intermediate_data=copy.deepcopy(self.intermediate_data),
            config=copy.deepcopy(self.config),
            metadata=copy.deepcopy(self.metadata),
            tags=self.tags.copy(),
        )


@dataclass
class WorkflowContext:
    """
    Context for a workflow execution.

    Manages state across multiple agent operations and workflow steps.
    """
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str = ""
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Workflow definition
    definition: Dict[str, Any] = field(default_factory=dict)

    # Triggers
    trigger_event: Optional[str] = None
    trigger_data: Dict[str, Any] = field(default_factory=dict)

    # Variables (resolved during execution)
    variables: Dict[str, Any] = field(default_factory=dict)

    # Step tracking
    steps: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    current_step_id: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)

    # Checkpoints for recovery
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    last_checkpoint_at: Optional[datetime] = None

    # Error handling
    error_handlers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    retries: Dict[str, int] = field(default_factory=dict)

    # Quality gates
    quality_gates: Dict[str, bool] = field(default_factory=dict)

    # Outputs
    outputs: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a workflow variable."""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a workflow variable."""
        return self.variables.get(name, default)

    def resolve_variable(self, expression: str) -> Any:
        """
        Resolve a variable expression.

        Supports patterns like:
        - ${variables.input_data}
        - ${steps.validate_input.output.validated_data}
        - ${trigger.data}
        """
        if not expression.startswith("${") or not expression.endswith("}"):
            return expression

        path = expression[2:-1]  # Remove ${ and }
        parts = path.split(".")

        if not parts:
            return expression

        # Determine the root
        root = parts[0]
        remaining = parts[1:]

        if root == "variables":
            current = self.variables
        elif root == "steps":
            current = self.steps
        elif root == "trigger":
            current = self.trigger_data
        elif root == "outputs":
            current = self.outputs
        else:
            return expression

        # Navigate the path
        for part in remaining:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return expression

            if current is None:
                return None

        return current

    def get_step_output(self, step_id: str) -> Dict[str, Any]:
        """Get the output of a completed step."""
        step = self.steps.get(step_id, {})
        return step.get("output", {})

    def set_step_output(self, step_id: str, output: Dict[str, Any]) -> None:
        """Set the output of a step."""
        if step_id not in self.steps:
            self.steps[step_id] = {}
        self.steps[step_id]["output"] = output

    def start_step(self, step_id: str) -> None:
        """Mark a step as started."""
        self.current_step_id = step_id
        if step_id not in self.steps:
            self.steps[step_id] = {}
        self.steps[step_id]["status"] = "in_progress"
        self.steps[step_id]["started_at"] = datetime.utcnow().isoformat()

    def complete_step(self, step_id: str, output: Optional[Dict[str, Any]] = None) -> None:
        """Mark a step as completed."""
        if step_id not in self.steps:
            self.steps[step_id] = {}
        self.steps[step_id]["status"] = "completed"
        self.steps[step_id]["completed_at"] = datetime.utcnow().isoformat()
        if output:
            self.steps[step_id]["output"] = output
        self.completed_steps.append(step_id)
        self.current_step_id = None

    def fail_step(self, step_id: str, error: str) -> None:
        """Mark a step as failed."""
        if step_id not in self.steps:
            self.steps[step_id] = {}
        self.steps[step_id]["status"] = "failed"
        self.steps[step_id]["error"] = error
        self.steps[step_id]["failed_at"] = datetime.utcnow().isoformat()
        self.failed_steps.append(step_id)
        self.current_step_id = None

    def create_checkpoint(self) -> Dict[str, Any]:
        """Create a checkpoint of the current state."""
        checkpoint = {
            "checkpoint_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "current_step_id": self.current_step_id,
            "completed_steps": self.completed_steps.copy(),
            "variables": copy.deepcopy(self.variables),
            "steps": copy.deepcopy(self.steps),
            "outputs": copy.deepcopy(self.outputs),
        }
        self.checkpoints.append(checkpoint)
        self.last_checkpoint_at = datetime.utcnow()
        return checkpoint

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore state from a checkpoint."""
        for checkpoint in self.checkpoints:
            if checkpoint["checkpoint_id"] == checkpoint_id:
                self.current_step_id = checkpoint["current_step_id"]
                self.completed_steps = checkpoint["completed_steps"].copy()
                self.variables = copy.deepcopy(checkpoint["variables"])
                self.steps = copy.deepcopy(checkpoint["steps"])
                self.outputs = copy.deepcopy(checkpoint["outputs"])
                return True
        return False

    def pass_quality_gate(self, gate_name: str) -> None:
        """Mark a quality gate as passed."""
        self.quality_gates[gate_name] = True

    def fail_quality_gate(self, gate_name: str) -> None:
        """Mark a quality gate as failed."""
        self.quality_gates[gate_name] = False

    def all_quality_gates_passed(self) -> bool:
        """Check if all quality gates have passed."""
        return all(self.quality_gates.values())

    def get_progress(self) -> float:
        """Get workflow progress as a percentage (0.0 to 1.0)."""
        total_steps = len(self.definition.get("steps", []))
        if total_steps == 0:
            return 1.0
        return len(self.completed_steps) / total_steps

    def get_trace(self) -> List[Dict[str, Any]]:
        """Get execution trace for debugging."""
        trace = []
        for step_id in self.completed_steps + self.failed_steps:
            step_info = self.steps.get(step_id, {})
            trace.append({
                "step_id": step_id,
                "status": step_info.get("status"),
                "started_at": step_info.get("started_at"),
                "completed_at": step_info.get("completed_at"),
                "failed_at": step_info.get("failed_at"),
                "error": step_info.get("error"),
            })
        return trace


@dataclass
class ResourceAllocation:
    """Resource allocation for a task."""
    allocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    agent_id: str = ""
    memory_bytes: int = 0
    cpu_cores: int = 1
    timeout_seconds: float = 300.0
    priority: int = 2
    allocated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if allocation has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class WorkflowState:
    """
    Serializable workflow state for persistence.

    Used for checkpointing and recovery.
    """
    workflow_id: str
    workflow_name: str
    version: str
    status: str
    created_at: str
    updated_at: str
    variables: Dict[str, Any]
    steps: Dict[str, Dict[str, Any]]
    completed_steps: List[str]
    failed_steps: List[str]
    outputs: Dict[str, Any]
    checkpoints: List[Dict[str, Any]]

    @classmethod
    def from_context(cls, context: WorkflowContext, status: str = "running") -> "WorkflowState":
        """Create state from workflow context."""
        return cls(
            workflow_id=context.workflow_id,
            workflow_name=context.workflow_name,
            version=context.version,
            status=status,
            created_at=context.created_at.isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            variables=context.variables,
            steps=context.steps,
            completed_steps=context.completed_steps,
            failed_steps=context.failed_steps,
            outputs=context.outputs,
            checkpoints=context.checkpoints,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "variables": self.variables,
            "steps": self.steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "outputs": self.outputs,
            "checkpoints": self.checkpoints,
        }
