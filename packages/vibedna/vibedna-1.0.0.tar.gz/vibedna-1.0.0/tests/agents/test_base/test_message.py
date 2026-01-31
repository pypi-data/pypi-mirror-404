# VibeDNA Message Tests
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""Tests for message classes."""

import pytest
from vibedna.agents.base.message import (
    AgentMessage,
    MessageType,
    TaskRequest,
    TaskResponse,
    TaskStatus,
    TaskPriority,
    OperationType,
    DelegationMatrix,
)


class TestMessageType:
    """Tests for MessageType enum."""

    def test_message_types(self):
        """Test all message types exist."""
        assert MessageType.TASK_REQUEST
        assert MessageType.TASK_RESPONSE
        assert MessageType.STATUS_UPDATE
        assert MessageType.ERROR
        assert MessageType.HEARTBEAT


class TestTaskRequest:
    """Tests for TaskRequest."""

    def test_create_request(self):
        """Test creating a task request."""
        request = TaskRequest(
            request_id="req-001",
            operation=OperationType.ENCODE,
            parameters={"data": "test"},
            priority=TaskPriority.HIGH,
        )

        assert request.request_id == "req-001"
        assert request.operation == OperationType.ENCODE
        assert request.parameters == {"data": "test"}
        assert request.priority == TaskPriority.HIGH

    def test_default_priority(self):
        """Test default priority."""
        request = TaskRequest(
            request_id="req-002",
            operation=OperationType.DECODE,
            parameters={},
        )

        assert request.priority == TaskPriority.NORMAL

    def test_to_dict(self):
        """Test converting request to dict."""
        request = TaskRequest(
            request_id="req-003",
            operation=OperationType.ENCODE,
            parameters={"data": "test"},
        )
        data = request.to_dict()

        assert data["request_id"] == "req-003"
        assert data["operation"] == "encode"


class TestTaskResponse:
    """Tests for TaskResponse."""

    def test_success_response(self):
        """Test creating success response."""
        response = TaskResponse.success("req-001", {"encoded": "ATCG"})

        assert response.request_id == "req-001"
        assert response.status == TaskStatus.COMPLETED
        assert response.result == {"encoded": "ATCG"}
        assert response.error is None

    def test_failure_response(self):
        """Test creating failure response."""
        response = TaskResponse.failure("req-002", "Invalid input")

        assert response.request_id == "req-002"
        assert response.status == TaskStatus.FAILED
        assert response.error == "Invalid input"

    def test_partial_response(self):
        """Test creating partial response."""
        response = TaskResponse.partial("req-003", {"partial": "data"}, "Some error")

        assert response.request_id == "req-003"
        assert response.status == TaskStatus.PARTIAL
        assert response.result == {"partial": "data"}
        assert response.error == "Some error"

    def test_to_dict(self):
        """Test converting response to dict."""
        response = TaskResponse.success("req-004", {"data": "test"})
        data = response.to_dict()

        assert data["request_id"] == "req-004"
        assert data["status"] == "completed"
        assert data["result"] == {"data": "test"}


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_status_values(self):
        """Test status values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestOperationType:
    """Tests for OperationType enum."""

    def test_operation_types(self):
        """Test operation types exist."""
        assert OperationType.ENCODE
        assert OperationType.DECODE
        assert OperationType.COMPUTE
        assert OperationType.STORE
        assert OperationType.SEARCH
        assert OperationType.VALIDATE
        assert OperationType.SYNTHESIZE


class TestDelegationMatrix:
    """Tests for DelegationMatrix."""

    def test_get_agents_for_operation(self):
        """Test getting agents for operations."""
        matrix = DelegationMatrix()

        encode_agents = matrix.get_agents_for_operation("encode")
        assert "primary" in encode_agents
        assert "encoder-agent" in encode_agents["primary"]

        decode_agents = matrix.get_agents_for_operation("decode")
        assert "primary" in decode_agents
        assert "decoder-agent" in decode_agents["primary"]

    def test_unknown_operation(self):
        """Test unknown operation returns empty dict."""
        matrix = DelegationMatrix()

        agents = matrix.get_agents_for_operation("unknown")
        assert agents == {"primary": [], "support": []}


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
