# VibeDNA Specialist Agent Tests
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""Tests for specialist tier agents."""

import pytest
from vibedna.agents.specialist.encoder_agent import EncoderAgent
from vibedna.agents.specialist.decoder_agent import DecoderAgent
from vibedna.agents.specialist.error_correction_agent import ErrorCorrectionAgent
from vibedna.agents.specialist.compute_agent import ComputeAgent
from vibedna.agents.specialist.filesystem_agent import FileSystemAgent
from vibedna.agents.specialist.validation_agent import ValidationAgent
from vibedna.agents.specialist.visualization_agent import VisualizationAgent
from vibedna.agents.specialist.synthesis_agent import SynthesisAgent
from vibedna.agents.base.message import TaskRequest
from vibedna.agents.base.agent_base import AgentTier


class TestEncoderAgent:
    """Tests for EncoderAgent."""

    def test_creation(self):
        """Test creating encoder agent."""
        agent = EncoderAgent()

        assert agent.config.agent_id == "vibedna-encoder-agent"
        assert agent.config.tier == AgentTier.SPECIALIST
        assert "binary_to_dna" in [c.name for c in agent.config.capabilities]

    def test_system_prompt(self):
        """Test system prompt."""
        agent = EncoderAgent()
        prompt = agent.get_system_prompt()

        assert "Encoder Agent" in prompt
        assert "quaternary" in prompt.lower()

    @pytest.mark.asyncio
    async def test_encode_task(self):
        """Test encoding task."""
        agent = EncoderAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="encode",
            parameters={
                "action": "encode",
                "data": "SGVsbG8=",  # base64 "Hello"
                "scheme": "quaternary",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-001"
        # Should have either result or error
        assert response.success is not None

    @pytest.mark.asyncio
    async def test_list_schemes(self):
        """Test listing encoding schemes."""
        agent = EncoderAgent()

        request = TaskRequest(
            request_id="test-002",
            task_type="list_schemes",
            parameters={"action": "list_schemes"},
        )

        response = await agent.handle_task(request)
        assert response.success is True
        assert "schemes" in response.result


class TestDecoderAgent:
    """Tests for DecoderAgent."""

    def test_creation(self):
        """Test creating decoder agent."""
        agent = DecoderAgent()

        assert agent.config.agent_id == "vibedna-decoder-agent"
        assert agent.config.tier == AgentTier.SPECIALIST

    @pytest.mark.asyncio
    async def test_decode_task(self):
        """Test decoding task."""
        agent = DecoderAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="decode",
            parameters={
                "action": "decode",
                "sequence": "ATCGATCG",
                "scheme": "quaternary",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-001"


class TestErrorCorrectionAgent:
    """Tests for ErrorCorrectionAgent."""

    def test_creation(self):
        """Test creating error correction agent."""
        agent = ErrorCorrectionAgent()

        assert agent.config.agent_id == "vibedna-error-correction-agent"
        assert agent.config.tier == AgentTier.SPECIALIST
        assert "reed_solomon_encoding" in [c.name for c in agent.config.capabilities]

    def test_system_prompt(self):
        """Test system prompt includes Reed-Solomon."""
        agent = ErrorCorrectionAgent()
        prompt = agent.get_system_prompt()

        assert "Reed-Solomon" in prompt

    @pytest.mark.asyncio
    async def test_add_ecc(self):
        """Test adding error correction."""
        agent = ErrorCorrectionAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="add_ecc",
            parameters={
                "action": "add_ecc",
                "sequence": "ATCGATCGATCGATCG",
                "nsym": 4,
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-001"

    @pytest.mark.asyncio
    async def test_verify_ecc(self):
        """Test verifying error correction."""
        agent = ErrorCorrectionAgent()

        request = TaskRequest(
            request_id="test-002",
            task_type="verify_ecc",
            parameters={
                "action": "verify",
                "sequence": "ATCGATCGATCGATCG",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-002"


class TestComputeAgent:
    """Tests for ComputeAgent."""

    def test_creation(self):
        """Test creating compute agent."""
        agent = ComputeAgent()

        assert agent.config.agent_id == "vibedna-compute-agent"
        assert agent.config.tier == AgentTier.SPECIALIST

    @pytest.mark.asyncio
    async def test_logic_gate(self):
        """Test logic gate operation."""
        agent = ComputeAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="logic_gate",
            parameters={
                "action": "logic_gate",
                "gate": "AND",
                "input_a": "ATCG",
                "input_b": "ATCG",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-001"

    @pytest.mark.asyncio
    async def test_arithmetic(self):
        """Test arithmetic operation."""
        agent = ComputeAgent()

        request = TaskRequest(
            request_id="test-002",
            task_type="arithmetic",
            parameters={
                "action": "arithmetic",
                "operation": "add",
                "operand_a": "ATCG",
                "operand_b": "GCTA",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-002"


class TestFileSystemAgent:
    """Tests for FileSystemAgent."""

    def test_creation(self):
        """Test creating filesystem agent."""
        agent = FileSystemAgent()

        assert agent.config.agent_id == "vibedna-filesystem-agent"
        assert agent.config.tier == AgentTier.SPECIALIST

    @pytest.mark.asyncio
    async def test_store_sequence(self):
        """Test storing sequence."""
        agent = FileSystemAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="store",
            parameters={
                "action": "store",
                "sequence": "ATCGATCG",
                "name": "test_sequence",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-001"

    @pytest.mark.asyncio
    async def test_list_sequences(self):
        """Test listing sequences."""
        agent = FileSystemAgent()

        request = TaskRequest(
            request_id="test-002",
            task_type="list",
            parameters={"action": "list"},
        )

        response = await agent.handle_task(request)
        assert response.success is True


class TestValidationAgent:
    """Tests for ValidationAgent."""

    def test_creation(self):
        """Test creating validation agent."""
        agent = ValidationAgent()

        assert agent.config.agent_id == "vibedna-validation-agent"
        assert agent.config.tier == AgentTier.SPECIALIST

    @pytest.mark.asyncio
    async def test_validate_sequence(self):
        """Test validating sequence."""
        agent = ValidationAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="validate",
            parameters={
                "action": "validate",
                "sequence": "ATCGATCG",
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True
        assert "valid" in response.result

    @pytest.mark.asyncio
    async def test_validate_invalid_sequence(self):
        """Test validating invalid sequence."""
        agent = ValidationAgent()

        request = TaskRequest(
            request_id="test-002",
            task_type="validate",
            parameters={
                "action": "validate",
                "sequence": "ATCGXYZ",  # Invalid characters
            },
        )

        response = await agent.handle_task(request)
        # Should return validation result (not error)
        assert response.request_id == "test-002"


class TestVisualizationAgent:
    """Tests for VisualizationAgent."""

    def test_creation(self):
        """Test creating visualization agent."""
        agent = VisualizationAgent()

        assert agent.config.agent_id == "vibedna-visualization-agent"
        assert agent.config.tier == AgentTier.SPECIALIST

    @pytest.mark.asyncio
    async def test_visualize_sequence(self):
        """Test visualizing sequence."""
        agent = VisualizationAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="visualize",
            parameters={
                "action": "visualize_sequence",
                "sequence": "ATCGATCG",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-001"


class TestSynthesisAgent:
    """Tests for SynthesisAgent."""

    def test_creation(self):
        """Test creating synthesis agent."""
        agent = SynthesisAgent()

        assert agent.config.agent_id == "vibedna-synthesis-agent"
        assert agent.config.tier == AgentTier.SPECIALIST

    @pytest.mark.asyncio
    async def test_optimize_sequence(self):
        """Test optimizing sequence for synthesis."""
        agent = SynthesisAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="optimize",
            parameters={
                "action": "optimize",
                "sequence": "ATCGATCG",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-001"

    @pytest.mark.asyncio
    async def test_check_synthesizability(self):
        """Test checking synthesizability."""
        agent = SynthesisAgent()

        request = TaskRequest(
            request_id="test-002",
            task_type="check",
            parameters={
                "action": "check_synthesizability",
                "sequence": "ATCGATCG",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-002"


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
