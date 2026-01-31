# VibeDNA Context Tests
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""Tests for context classes."""

import pytest
from vibedna.agents.base.context import (
    AgentContext,
    WorkflowContext,
    ResourceAllocation,
    WorkflowState,
)


class TestAgentContext:
    """Tests for AgentContext."""

    def test_create_context(self):
        """Test creating agent context."""
        ctx = AgentContext(
            agent_id="test-agent",
            operation="encode",
        )

        assert ctx.agent_id == "test-agent"
        assert ctx.operation == "encode"
        assert ctx.context_id is not None

    def test_set_and_get(self):
        """Test setting and getting values."""
        ctx = AgentContext()
        ctx.set("key1", "value1")
        ctx.set("key2", 42)

        assert ctx.get("key1") == "value1"
        assert ctx.get("key2") == 42
        assert ctx.get("nonexistent") is None
        assert ctx.get("nonexistent", "default") == "default"

    def test_error_tracking(self):
        """Test error tracking."""
        ctx = AgentContext()
        assert ctx.has_errors() is False

        ctx.add_error("Something went wrong", code="ERR001")
        assert ctx.has_errors() is True
        assert len(ctx.errors) == 1
        assert ctx.errors[0]["message"] == "Something went wrong"
        assert ctx.errors[0]["code"] == "ERR001"

    def test_warning_tracking(self):
        """Test warning tracking."""
        ctx = AgentContext()
        ctx.add_warning("This is a warning")

        assert len(ctx.warnings) == 1
        assert ctx.warnings[0] == "This is a warning"

    def test_step_tracking(self):
        """Test step tracking."""
        ctx = AgentContext()

        ctx.start_step("step1")
        assert ctx.current_step == "step1"

        ctx.complete_step("step1")
        assert ctx.current_step is None
        assert "step1" in ctx.steps_completed

    def test_metrics_recording(self):
        """Test metrics recording."""
        ctx = AgentContext()
        ctx.record_metric("duration_ms", 150)
        ctx.record_metric("bytes_processed", 1024)

        assert ctx.metrics["duration_ms"] == 150
        assert ctx.metrics["bytes_processed"] == 1024

    def test_clone(self):
        """Test cloning context."""
        ctx = AgentContext(agent_id="original")
        ctx.set("key", "value")

        cloned = ctx.clone()

        assert cloned.context_id != ctx.context_id
        assert cloned.agent_id == "original"
        assert cloned.get("key") == "value"


class TestWorkflowContext:
    """Tests for WorkflowContext."""

    def test_create_workflow_context(self):
        """Test creating workflow context."""
        ctx = WorkflowContext(
            workflow_name="encode_workflow",
            version="1.0.0",
        )

        assert ctx.workflow_name == "encode_workflow"
        assert ctx.version == "1.0.0"
        assert ctx.workflow_id is not None

    def test_variable_management(self):
        """Test variable management."""
        ctx = WorkflowContext()
        ctx.set_variable("input_data", b"test")
        ctx.set_variable("scheme", "quaternary")

        assert ctx.get_variable("input_data") == b"test"
        assert ctx.get_variable("scheme") == "quaternary"
        assert ctx.get_variable("unknown") is None

    def test_resolve_variable(self):
        """Test variable resolution."""
        ctx = WorkflowContext()
        ctx.variables["data"] = "test_data"
        ctx.trigger_data["event"] = "manual"

        result = ctx.resolve_variable("${variables.data}")
        assert result == "test_data"

        result = ctx.resolve_variable("${trigger.event}")
        assert result == "manual"

        # Non-expression should return as-is
        result = ctx.resolve_variable("plain_text")
        assert result == "plain_text"

    def test_step_management(self):
        """Test step management."""
        ctx = WorkflowContext()

        ctx.start_step("step1")
        assert ctx.current_step_id == "step1"
        assert ctx.steps["step1"]["status"] == "in_progress"

        ctx.complete_step("step1", {"output": "data"})
        assert ctx.current_step_id is None
        assert ctx.steps["step1"]["status"] == "completed"
        assert "step1" in ctx.completed_steps

    def test_step_failure(self):
        """Test step failure."""
        ctx = WorkflowContext()

        ctx.start_step("failing_step")
        ctx.fail_step("failing_step", "Something went wrong")

        assert ctx.steps["failing_step"]["status"] == "failed"
        assert ctx.steps["failing_step"]["error"] == "Something went wrong"
        assert "failing_step" in ctx.failed_steps

    def test_checkpoint(self):
        """Test checkpoint creation and restoration."""
        ctx = WorkflowContext()
        ctx.set_variable("counter", 1)
        ctx.complete_step("step1", {"data": "output1"})

        checkpoint = ctx.create_checkpoint()
        checkpoint_id = checkpoint["checkpoint_id"]

        # Modify state
        ctx.set_variable("counter", 2)
        ctx.complete_step("step2", {"data": "output2"})

        # Restore checkpoint
        result = ctx.restore_checkpoint(checkpoint_id)
        assert result is True
        assert ctx.get_variable("counter") == 1
        assert "step2" not in ctx.completed_steps

    def test_quality_gates(self):
        """Test quality gate tracking."""
        ctx = WorkflowContext()

        ctx.pass_quality_gate("validation")
        ctx.pass_quality_gate("security")
        assert ctx.all_quality_gates_passed() is True

        ctx.fail_quality_gate("performance")
        assert ctx.all_quality_gates_passed() is False

    def test_progress_tracking(self):
        """Test progress tracking."""
        ctx = WorkflowContext()
        ctx.definition = {"steps": [{"id": "s1"}, {"id": "s2"}, {"id": "s3"}, {"id": "s4"}]}

        assert ctx.get_progress() == 0.0

        ctx.completed_steps = ["s1", "s2"]
        assert ctx.get_progress() == 0.5

    def test_execution_trace(self):
        """Test execution trace."""
        ctx = WorkflowContext()

        ctx.start_step("step1")
        ctx.complete_step("step1", {})

        ctx.start_step("step2")
        ctx.fail_step("step2", "Error")

        trace = ctx.get_trace()
        assert len(trace) == 2
        assert trace[0]["step_id"] == "step1"
        assert trace[1]["step_id"] == "step2"
        assert trace[1]["error"] == "Error"


class TestResourceAllocation:
    """Tests for ResourceAllocation."""

    def test_create_allocation(self):
        """Test creating resource allocation."""
        alloc = ResourceAllocation(
            task_id="task-001",
            agent_id="encoder-agent",
            memory_bytes=1024 * 1024 * 100,
            cpu_cores=2,
        )

        assert alloc.task_id == "task-001"
        assert alloc.agent_id == "encoder-agent"
        assert alloc.memory_bytes == 104857600
        assert alloc.cpu_cores == 2

    def test_expiration(self):
        """Test allocation expiration."""
        from datetime import datetime, timedelta

        alloc = ResourceAllocation()
        assert alloc.is_expired() is False

        alloc.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert alloc.is_expired() is True


class TestWorkflowState:
    """Tests for WorkflowState."""

    def test_from_context(self):
        """Test creating state from context."""
        ctx = WorkflowContext(
            workflow_name="test_workflow",
            version="1.0.0",
        )
        ctx.set_variable("data", "value")

        state = WorkflowState.from_context(ctx, status="running")

        assert state.workflow_id == ctx.workflow_id
        assert state.workflow_name == "test_workflow"
        assert state.status == "running"
        assert state.variables == {"data": "value"}

    def test_to_dict(self):
        """Test converting state to dict."""
        ctx = WorkflowContext(workflow_name="test")
        state = WorkflowState.from_context(ctx)

        data = state.to_dict()

        assert "workflow_id" in data
        assert "workflow_name" in data
        assert "status" in data
        assert data["workflow_name"] == "test"


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
