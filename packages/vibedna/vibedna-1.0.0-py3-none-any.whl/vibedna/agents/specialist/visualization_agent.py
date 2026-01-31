# VibeDNA Visualization Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Visualization Agent - DNA sequence visualization.

Creates visual representations:
- Sequence views
- Statistics dashboards
- Encoding animations
- 3D helix renderers
"""

from typing import Any, Dict, Optional

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


class VisualizationAgent(BaseAgent):
    """
    Visualization Agent for DNA sequences.

    Creates visual representations of DNA sequences
    and encoding statistics.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Visualization Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-visualization-agent",
                version="1.0.0",
                tier=AgentTier.SPECIALIST,
                role="DNA Sequence Visualization",
                description="Creates visual DNA representations",
                capabilities=[
                    AgentCapability(
                        name="sequence_view",
                        description="Formatted sequence display",
                    ),
                    AgentCapability(
                        name="statistics_dashboard",
                        description="Statistics visualization",
                    ),
                    AgentCapability(
                        name="chart_generation",
                        description="Generate charts and graphs",
                    ),
                ],
                tools=[
                    "sequence_formatter",
                    "statistics_generator",
                    "chart_renderer",
                    "animation_generator",
                ],
                mcp_connections=["vibedna-core"],
            )

        super().__init__(config)

    def get_system_prompt(self) -> str:
        """Get the Visualization Agent's system prompt."""
        return """You are the VibeDNA Visualization Agent, creating visual DNA representations.

## Visualization Types

1. Sequence View - Formatted sequence with annotations
2. Statistics Dashboard - Nucleotide distribution, GC content
3. Encoding Animation - Step-by-step encoding visualization
4. 3D Helix - DNA structure visualization

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a visualization task."""
        self.logger.info(f"Handling visualization task: {request.request_id}")

        action = request.parameters.get("action", "sequence_view")

        if action == "sequence_view":
            return await self._generate_sequence_view(request)
        elif action == "statistics":
            return await self._generate_statistics(request)
        elif action == "dashboard":
            return await self._generate_dashboard(request)
        else:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown action: {action}",
            )

    async def _generate_sequence_view(self, request: TaskRequest) -> TaskResponse:
        """Generate formatted sequence view."""
        try:
            sequence = request.parameters.get("sequence", "")
            sequence = sequence.upper().strip()
            line_length = request.parameters.get("line_length", 60)

            if not sequence:
                return TaskResponse.failure(request.request_id, "No sequence provided")

            # Format sequence
            lines = []
            lines.append("=" * 70)
            lines.append("VIBEDNA SEQUENCE VIEW")
            lines.append("=" * 70)

            # Header info
            if len(sequence) >= 256:
                lines.append("")
                lines.append("HEADER [0-255]")
                lines.append(f"  Magic:   {sequence[:8]}")
                lines.append(f"  Version: {sequence[8:12]}")
                lines.append(f"  Scheme:  {sequence[12:16]}")

            # Data section
            lines.append("")
            lines.append("DATA")
            data_start = 256 if len(sequence) >= 256 else 0
            data_end = len(sequence) - 32 if len(sequence) >= 32 else len(sequence)

            for i in range(data_start, data_end, line_length):
                chunk = sequence[i:i + line_length]
                pos_str = f"{i:>8}"
                lines.append(f"  {pos_str}  {chunk}")

            # Footer info
            if len(sequence) >= 32:
                lines.append("")
                lines.append(f"FOOTER [{len(sequence) - 32}-{len(sequence)}]")
                lines.append(f"  Marker:   {sequence[-32:-24]}")
                lines.append(f"  Checksum: {sequence[-16:]}")

            lines.append("")
            lines.append("=" * 70)
            lines.append(self.FOOTER)

            view = "\n".join(lines)

            return TaskResponse.success(
                request.request_id,
                {"view": view, "length": len(sequence)},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _generate_statistics(self, request: TaskRequest) -> TaskResponse:
        """Generate sequence statistics."""
        try:
            sequence = request.parameters.get("sequence", "")
            sequence = sequence.upper().strip()

            if not sequence:
                return TaskResponse.failure(request.request_id, "No sequence provided")

            # Calculate statistics
            counts = {"A": 0, "T": 0, "C": 0, "G": 0}
            for c in sequence:
                if c in counts:
                    counts[c] += 1

            total = len(sequence)
            distribution = {k: v / total if total > 0 else 0 for k, v in counts.items()}

            gc_content = (counts["G"] + counts["C"]) / total if total > 0 else 0

            # Find max homopolymer
            max_run = 1
            current_run = 1
            for i in range(1, len(sequence)):
                if sequence[i] == sequence[i - 1]:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 1

            return TaskResponse.success(
                request.request_id,
                {
                    "length": total,
                    "counts": counts,
                    "distribution": distribution,
                    "gc_content": gc_content,
                    "max_homopolymer": max_run,
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _generate_dashboard(self, request: TaskRequest) -> TaskResponse:
        """Generate statistics dashboard."""
        try:
            sequence = request.parameters.get("sequence", "")
            sequence = sequence.upper().strip()

            if not sequence:
                return TaskResponse.failure(request.request_id, "No sequence provided")

            # Get statistics first
            stats_result = await self._generate_statistics(request)
            if stats_result.status != "completed":
                return stats_result

            stats = stats_result.result

            # Create ASCII dashboard
            lines = []
            lines.append("╔" + "═" * 60 + "╗")
            lines.append("║" + "VIBEDNA SEQUENCE ANALYSIS".center(60) + "║")
            lines.append("╠" + "═" * 60 + "╣")
            lines.append(f"║  Total Length:     {stats['length']:>15,} nt" + " " * 21 + "║")
            lines.append(f"║  GC Content:       {stats['gc_content']:>15.1%}" + " " * 21 + "║")
            lines.append(f"║  Max Homopolymer:  {stats['max_homopolymer']:>15}" + " " * 21 + "║")
            lines.append("╠" + "═" * 60 + "╣")
            lines.append("║  NUCLEOTIDE DISTRIBUTION" + " " * 35 + "║")

            for nuc in "ATCG":
                pct = stats["distribution"][nuc]
                bar_len = int(pct * 30)
                bar = "█" * bar_len
                lines.append(f"║  {nuc}: {pct:>5.1%}  {bar:<30}" + " " * (24 - bar_len) + "║")

            lines.append("╚" + "═" * 60 + "╝")
            lines.append(self.FOOTER)

            dashboard = "\n".join(lines)

            return TaskResponse.success(
                request.request_id,
                {"dashboard": dashboard, "statistics": stats},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))
