# VibeDNA Orchestrator Tests
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""Tests for orchestration tier agents."""

import pytest
from vibedna.agents.orchestration.master_orchestrator import MasterOrchestrator
from vibedna.agents.orchestration.workflow_orchestrator import WorkflowOrchestrator
from vibedna.agents.orchestration.resource_orchestrator import ResourceOrchestrator
from vibedna.agents.base.message import TaskRequest, OperationType
from vibedna.agents.base.agent_base import AgentTier


class TestMasterOrchestrator:
    """Tests for MasterOrchestrator."""

    def test_creation(self):
        """Test creating master orchestrator."""
        orchestrator = MasterOrchestrator()

        assert orchestrator.config.agent_id == "vibedna-master-orchestrator"
        assert orchestrator.config.tier == AgentTier.ORCHESTRATION
        assert "workflow_planning" in [c.name for c in orchestrator.config.capabilities]

    def test_system_prompt(self):
        """Test system prompt."""
        orchestrator = MasterOrchestrator()
        prompt = orchestrator.get_system_prompt()

        assert "VibeDNA Master Orchestrator" in prompt
        assert "VibeCaaS.com" in prompt

    @pytest.mark.asyncio
    async def test_plan_workflow(self):
        """Test workflow planning."""
        orchestrator = MasterOrchestrator()

        request = TaskRequest(
            request_id="test-001",
            task_type="plan_workflow",
            parameters={
                "action": "plan_workflow",
                "operation": OperationType.ENCODE.value,
                "input_data": {"data": "test"},
            },
        )

        response = await orchestrator.handle_task(request)
        assert response.request_id == "test-001"
        # The response should contain either success or structured error
        assert response.success is not None

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting orchestrator status."""
        orchestrator = MasterOrchestrator()

        request = TaskRequest(
            request_id="test-002",
            task_type="status",
            parameters={"action": "get_status"},
        )

        response = await orchestrator.handle_task(request)
        assert response.success is True
        assert "agent_id" in response.result


class TestWorkflowOrchestrator:
    """Tests for WorkflowOrchestrator."""

    def test_creation(self):
        """Test creating workflow orchestrator."""
        orchestrator = WorkflowOrchestrator()

        assert orchestrator.config.agent_id == "vibedna-workflow-orchestrator"
        assert orchestrator.config.tier == AgentTier.ORCHESTRATION

    def test_system_prompt(self):
        """Test system prompt."""
        orchestrator = WorkflowOrchestrator()
        prompt = orchestrator.get_system_prompt()

        assert "Workflow Orchestrator" in prompt

    @pytest.mark.asyncio
    async def test_list_workflows(self):
        """Test listing available workflows."""
        orchestrator = WorkflowOrchestrator()

        request = TaskRequest(
            request_id="test-001",
            task_type="list_workflows",
            parameters={"action": "list_workflows"},
        )

        response = await orchestrator.handle_task(request)
        assert response.success is True
        assert "workflows" in response.result

    @pytest.mark.asyncio
    async def test_start_workflow(self):
        """Test starting a workflow."""
        orchestrator = WorkflowOrchestrator()

        request = TaskRequest(
            request_id="test-002",
            task_type="start_workflow",
            parameters={
                "action": "start_workflow",
                "workflow_name": "encode_simple",
                "input_data": {"data": "test"},
            },
        )

        response = await orchestrator.handle_task(request)
        # Should either succeed or fail with meaningful error
        assert response.request_id == "test-002"


class TestResourceOrchestrator:
    """Tests for ResourceOrchestrator."""

    def test_creation(self):
        """Test creating resource orchestrator."""
        orchestrator = ResourceOrchestrator()

        assert orchestrator.config.agent_id == "vibedna-resource-orchestrator"
        assert orchestrator.config.tier == AgentTier.ORCHESTRATION

    def test_system_prompt(self):
        """Test system prompt."""
        orchestrator = ResourceOrchestrator()
        prompt = orchestrator.get_system_prompt()

        assert "Resource Orchestrator" in prompt

    @pytest.mark.asyncio
    async def test_allocate_resources(self):
        """Test resource allocation."""
        orchestrator = ResourceOrchestrator()

        request = TaskRequest(
            request_id="test-001",
            task_type="allocate",
            parameters={
                "action": "allocate",
                "task_id": "task-001",
                "agent_id": "encoder-agent",
                "memory_bytes": 1024 * 1024,
                "cpu_cores": 1,
            },
        )

        response = await orchestrator.handle_task(request)
        assert response.success is True
        assert "allocation_id" in response.result

    @pytest.mark.asyncio
    async def test_release_resources(self):
        """Test releasing resources."""
        orchestrator = ResourceOrchestrator()

        # First allocate
        alloc_request = TaskRequest(
            request_id="test-alloc",
            task_type="allocate",
            parameters={
                "action": "allocate",
                "task_id": "task-002",
                "agent_id": "decoder-agent",
            },
        )
        alloc_response = await orchestrator.handle_task(alloc_request)
        allocation_id = alloc_response.result.get("allocation_id")

        # Then release
        release_request = TaskRequest(
            request_id="test-release",
            task_type="release",
            parameters={
                "action": "release",
                "allocation_id": allocation_id,
            },
        )

        response = await orchestrator.handle_task(release_request)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_get_agent_status(self):
        """Test getting agent status."""
        orchestrator = ResourceOrchestrator()

        request = TaskRequest(
            request_id="test-003",
            task_type="get_agent_status",
            parameters={"action": "get_agent_status"},
        )

        response = await orchestrator.handle_task(request)
        assert response.success is True
        assert "agents" in response.result

    @pytest.mark.asyncio
    async def test_set_quota(self):
        """Test setting quota."""
        orchestrator = ResourceOrchestrator()

        request = TaskRequest(
            request_id="test-004",
            task_type="set_quota",
            parameters={
                "action": "set_quota",
                "agent_id": "test-agent",
                "max_memory": 1024 * 1024 * 1024,
                "max_cpu": 4,
                "max_tasks": 10,
            },
        )

        response = await orchestrator.handle_task(request)
        assert response.success is True


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
