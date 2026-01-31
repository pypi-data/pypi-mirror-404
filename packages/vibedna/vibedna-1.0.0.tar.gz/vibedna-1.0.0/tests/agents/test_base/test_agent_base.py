# VibeDNA Agent Base Tests
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""Tests for BaseAgent class and related components."""

import pytest
from vibedna.agents.base.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentTier,
    AgentStatus,
)
from vibedna.agents.base.message import TaskRequest, TaskResponse, OperationType


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing."""

    def __init__(self):
        config = AgentConfig(
            agent_id="test-agent",
            version="1.0.0",
            tier=AgentTier.SPECIALIST,
            role="Test Agent",
            description="A test agent for unit tests",
            capabilities=[
                AgentCapability(
                    name="test_capability",
                    description="Test capability",
                ),
            ],
            tools=["test_tool"],
        )
        super().__init__(config)

    def get_system_prompt(self) -> str:
        return "Test agent prompt"

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        return TaskResponse.success(
            request.request_id,
            {"result": "test_result"},
        )


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_config_creation(self):
        """Test creating an agent config."""
        config = AgentConfig(
            agent_id="my-agent",
            version="1.0.0",
            tier=AgentTier.ORCHESTRATION,
            role="Test Role",
            description="Test description",
        )

        assert config.agent_id == "my-agent"
        assert config.version == "1.0.0"
        assert config.tier == AgentTier.ORCHESTRATION
        assert config.role == "Test Role"

    def test_config_with_capabilities(self):
        """Test config with capabilities."""
        cap = AgentCapability(
            name="encode",
            description="Encode data",
        )
        config = AgentConfig(
            agent_id="encoder",
            version="1.0.0",
            tier=AgentTier.SPECIALIST,
            role="Encoder",
            description="Encodes data",
            capabilities=[cap],
        )

        assert len(config.capabilities) == 1
        assert config.capabilities[0].name == "encode"


class TestAgentTier:
    """Tests for AgentTier enum."""

    def test_tier_values(self):
        """Test tier values."""
        assert AgentTier.ORCHESTRATION.value == "orchestration"
        assert AgentTier.SPECIALIST.value == "specialist"
        assert AgentTier.SUPPORT.value == "support"


class TestAgentStatus:
    """Tests for AgentStatus enum."""

    def test_status_values(self):
        """Test status values."""
        assert AgentStatus.INITIALIZING.value == "initializing"
        assert AgentStatus.READY.value == "ready"
        assert AgentStatus.BUSY.value == "busy"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.SHUTDOWN.value == "shutdown"


class TestBaseAgent:
    """Tests for BaseAgent."""

    def test_agent_creation(self):
        """Test creating an agent."""
        agent = ConcreteAgent()

        assert agent.config.agent_id == "test-agent"
        assert agent.config.tier == AgentTier.SPECIALIST
        # Agent starts in INITIALIZING state
        assert agent.status == AgentStatus.INITIALIZING

    def test_get_system_prompt(self):
        """Test getting system prompt."""
        agent = ConcreteAgent()
        prompt = agent.get_system_prompt()

        assert prompt == "Test agent prompt"

    @pytest.mark.asyncio
    async def test_handle_task(self):
        """Test handling a task."""
        agent = ConcreteAgent()
        request = TaskRequest(
            request_id="test-123",
            operation=OperationType.ENCODE,
            parameters={},
        )

        response = await agent.handle_task(request)

        assert response.request_id == "test-123"
        assert response.status.value == "completed"
        assert response.result == {"result": "test_result"}

    def test_footer_constant(self):
        """Test footer constant is present."""
        assert hasattr(BaseAgent, "FOOTER")
        assert "VibeDNA" in BaseAgent.FOOTER
        assert "2026" in BaseAgent.FOOTER


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
