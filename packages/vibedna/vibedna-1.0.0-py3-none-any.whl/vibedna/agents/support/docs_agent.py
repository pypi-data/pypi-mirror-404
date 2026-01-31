# VibeDNA Docs Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Docs Agent - Documentation generation and management.

Generates:
- API documentation
- Sequence metadata docs
- Workflow documentation
"""

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


class DocsAgent(BaseAgent):
    """
    Docs Agent for documentation generation.

    Generates and manages documentation for the
    VibeDNA system.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Docs Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-docs-agent",
                version="1.0.0",
                tier=AgentTier.SUPPORT,
                role="Documentation Generation",
                description="Generates and manages system documentation",
                capabilities=[
                    AgentCapability(
                        name="api_docs",
                        description="Generate API documentation",
                    ),
                    AgentCapability(
                        name="sequence_docs",
                        description="Generate sequence documentation",
                    ),
                    AgentCapability(
                        name="workflow_docs",
                        description="Generate workflow documentation",
                    ),
                ],
                tools=[
                    "doc_generator",
                    "markdown_formatter",
                ],
                mcp_connections=[],
            )

        super().__init__(config)

    def get_system_prompt(self) -> str:
        """Get the Docs Agent's system prompt."""
        return """You are the VibeDNA Docs Agent, generating system documentation.

## Documentation Types

1. API Docs - Endpoint documentation
2. Sequence Docs - Sequence metadata and structure
3. Workflow Docs - Workflow definitions and usage

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a documentation task."""
        action = request.parameters.get("action", "generate")

        if action == "generate_sequence_doc":
            return await self._generate_sequence_doc(request)
        elif action == "generate_workflow_doc":
            return await self._generate_workflow_doc(request)
        elif action == "generate_api_doc":
            return await self._generate_api_doc(request)
        else:
            return TaskResponse.failure(request.request_id, f"Unknown action: {action}")

    async def _generate_sequence_doc(self, request: TaskRequest) -> TaskResponse:
        """Generate documentation for a sequence."""
        try:
            sequence = request.parameters.get("sequence", "")
            metadata = request.parameters.get("metadata", {})

            # Generate markdown documentation
            doc_lines = [
                "# VibeDNA Sequence Documentation",
                "",
                f"**Generated:** {datetime.utcnow().isoformat()}",
                "",
                "## Sequence Properties",
                "",
                f"- **Length:** {len(sequence)} nucleotides",
                f"- **GC Content:** {self._calculate_gc(sequence):.1%}",
                f"- **Max Homopolymer:** {self._find_max_run(sequence)}",
                "",
            ]

            if metadata:
                doc_lines.extend([
                    "## Metadata",
                    "",
                ])
                for key, value in metadata.items():
                    doc_lines.append(f"- **{key}:** {value}")
                doc_lines.append("")

            doc_lines.extend([
                "## Structure",
                "",
                "```",
                f"Header:  {sequence[:8] if len(sequence) >= 8 else 'N/A'}...",
                f"Data:    {len(sequence) - 288 if len(sequence) > 288 else 0} nucleotides",
                f"Footer:  ...{sequence[-8:] if len(sequence) >= 8 else 'N/A'}",
                "```",
                "",
                "---",
                self.FOOTER,
            ])

            doc = "\n".join(doc_lines)

            return TaskResponse.success(
                request.request_id,
                {"documentation": doc, "format": "markdown"},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _generate_workflow_doc(self, request: TaskRequest) -> TaskResponse:
        """Generate documentation for a workflow."""
        try:
            workflow_name = request.parameters.get("name", "Unknown")
            steps = request.parameters.get("steps", [])

            doc_lines = [
                f"# Workflow: {workflow_name}",
                "",
                f"**Generated:** {datetime.utcnow().isoformat()}",
                "",
                "## Steps",
                "",
            ]

            for i, step in enumerate(steps, 1):
                doc_lines.extend([
                    f"### Step {i}: {step.get('id', 'Unknown')}",
                    "",
                    f"- **Agent:** {step.get('agent', 'N/A')}",
                    f"- **Action:** {step.get('action', 'N/A')}",
                    "",
                ])

            doc_lines.extend([
                "---",
                self.FOOTER,
            ])

            doc = "\n".join(doc_lines)

            return TaskResponse.success(
                request.request_id,
                {"documentation": doc, "format": "markdown"},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _generate_api_doc(self, request: TaskRequest) -> TaskResponse:
        """Generate API documentation."""
        try:
            endpoints = request.parameters.get("endpoints", [])

            doc_lines = [
                "# VibeDNA API Documentation",
                "",
                f"**Generated:** {datetime.utcnow().isoformat()}",
                "",
                "## Endpoints",
                "",
            ]

            for endpoint in endpoints:
                doc_lines.extend([
                    f"### {endpoint.get('method', 'GET')} {endpoint.get('path', '/')}",
                    "",
                    endpoint.get("description", "No description"),
                    "",
                ])

            doc_lines.extend([
                "---",
                self.FOOTER,
            ])

            doc = "\n".join(doc_lines)

            return TaskResponse.success(
                request.request_id,
                {"documentation": doc, "format": "markdown"},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    def _calculate_gc(self, seq: str) -> float:
        """Calculate GC content."""
        if not seq:
            return 0.0
        return sum(1 for c in seq.upper() if c in "GC") / len(seq)

    def _find_max_run(self, seq: str) -> int:
        """Find max homopolymer run."""
        if not seq:
            return 0
        max_run = current = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i - 1]:
                current += 1
                max_run = max(max_run, current)
            else:
                current = 1
        return max_run
