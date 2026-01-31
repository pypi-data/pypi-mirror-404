# VibeDNA Agent Orchestration System
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
VibeDNA Agent Orchestration System

A hierarchical multi-agent architecture for distributed DNA encoding,
decoding, computation, and file management operations.

Architecture:
- Orchestration Tier: Strategic coordination and workflow management
- Specialist Tier: Domain-specific task execution
- Support Tier: Infrastructure, monitoring, and utilities
"""

from vibedna.agents.base.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentTier,
    AgentStatus,
)
from vibedna.agents.base.message import (
    AgentMessage,
    MessageType,
    TaskRequest,
    TaskResponse,
    TaskStatus,
)
from vibedna.agents.base.tool import Tool, ToolResult, ToolParameter
from vibedna.agents.base.context import AgentContext, WorkflowContext

# Orchestration Tier
from vibedna.agents.orchestration.master_orchestrator import MasterOrchestrator
from vibedna.agents.orchestration.workflow_orchestrator import WorkflowOrchestrator
from vibedna.agents.orchestration.resource_orchestrator import ResourceOrchestrator

# Specialist Tier
from vibedna.agents.specialist.encoder_agent import EncoderAgent
from vibedna.agents.specialist.decoder_agent import DecoderAgent
from vibedna.agents.specialist.error_correction_agent import ErrorCorrectionAgent
from vibedna.agents.specialist.compute_agent import ComputeAgent
from vibedna.agents.specialist.filesystem_agent import FileSystemAgent
from vibedna.agents.specialist.validation_agent import ValidationAgent
from vibedna.agents.specialist.visualization_agent import VisualizationAgent
from vibedna.agents.specialist.synthesis_agent import SynthesisAgent

# Support Tier
from vibedna.agents.support.index_agent import IndexAgent
from vibedna.agents.support.metrics_agent import MetricsAgent
from vibedna.agents.support.logging_agent import LoggingAgent
from vibedna.agents.support.docs_agent import DocsAgent
from vibedna.agents.support.security_agent import SecurityAgent

__version__ = "1.0.0"
__author__ = "VibeDNA Team"
__footer__ = "© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved."

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentConfig",
    "AgentCapability",
    "AgentTier",
    "AgentStatus",
    "AgentMessage",
    "MessageType",
    "TaskRequest",
    "TaskResponse",
    "TaskStatus",
    "Tool",
    "ToolResult",
    "ToolParameter",
    "AgentContext",
    "WorkflowContext",
    # Orchestration Tier
    "MasterOrchestrator",
    "WorkflowOrchestrator",
    "ResourceOrchestrator",
    # Specialist Tier
    "EncoderAgent",
    "DecoderAgent",
    "ErrorCorrectionAgent",
    "ComputeAgent",
    "FileSystemAgent",
    "ValidationAgent",
    "VisualizationAgent",
    "SynthesisAgent",
    # Support Tier
    "IndexAgent",
    "MetricsAgent",
    "LoggingAgent",
    "DocsAgent",
    "SecurityAgent",
]
