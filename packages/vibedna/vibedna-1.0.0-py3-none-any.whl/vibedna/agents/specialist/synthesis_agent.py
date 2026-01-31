# VibeDNA Synthesis Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Synthesis Agent - DNA synthesis optimization.

Optimizes sequences for physical DNA synthesis:
- Platform-specific constraints
- GC balancing
- Homopolymer breaking
- Fragment generation
"""

from dataclasses import dataclass
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


@dataclass
class PlatformConstraints:
    """Synthesis platform constraints."""
    name: str
    max_length: int
    min_gc: float
    max_gc: float
    max_homopolymer: int
    forbidden: List[str]


PLATFORMS = {
    "twist_bioscience": PlatformConstraints(
        "Twist Bioscience", 300, 0.25, 0.65, 6, ["GAATTC", "GGATCC"]
    ),
    "idt": PlatformConstraints(
        "IDT", 200, 0.30, 0.70, 4, []
    ),
    "genscript": PlatformConstraints(
        "GenScript", 500, 0.20, 0.80, 8, []
    ),
}


class SynthesisAgent(BaseAgent):
    """
    Synthesis Agent for DNA synthesis optimization.

    Optimizes sequences for physical synthesis on
    various DNA synthesis platforms.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Synthesis Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-synthesis-agent",
                version="1.0.0",
                tier=AgentTier.SPECIALIST,
                role="DNA Synthesis Optimization",
                description="Optimizes sequences for DNA synthesis",
                capabilities=[
                    AgentCapability(
                        name="gc_balancing",
                        description="Balance GC content",
                    ),
                    AgentCapability(
                        name="homopolymer_breaking",
                        description="Break long homopolymer runs",
                    ),
                    AgentCapability(
                        name="fragmentation",
                        description="Fragment for synthesis",
                    ),
                    AgentCapability(
                        name="order_generation",
                        description="Generate synthesis orders",
                    ),
                ],
                tools=[
                    "gc_balancer",
                    "homopolymer_breaker",
                    "forbidden_remover",
                    "sequence_fragmenter",
                    "assembly_planner",
                ],
                mcp_connections=["vibedna-synth"],
            )

        super().__init__(config)

    def get_system_prompt(self) -> str:
        """Get the Synthesis Agent's system prompt."""
        return """You are the VibeDNA Synthesis Agent, optimizing sequences for DNA synthesis.

## Synthesis Platforms

- Twist Bioscience: max 300bp, 25-65% GC, max 6 homopolymer
- IDT: max 200bp, 30-70% GC, max 4 homopolymer
- GenScript: max 500bp, 20-80% GC, max 8 homopolymer

## Optimization Steps

1. Check GC content and balance if needed
2. Break long homopolymer runs
3. Remove forbidden sequences
4. Fragment if length exceeds platform max
5. Generate synthesis order

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a synthesis task."""
        self.logger.info(f"Handling synthesis task: {request.request_id}")

        action = request.parameters.get("action", "optimize")

        if action == "optimize":
            return await self._optimize_sequence(request)
        elif action == "check_constraints":
            return await self._check_constraints(request)
        elif action == "fragment":
            return await self._fragment_sequence(request)
        elif action == "generate_order":
            return await self._generate_order(request)
        else:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown action: {action}",
            )

    async def _optimize_sequence(self, request: TaskRequest) -> TaskResponse:
        """Optimize sequence for synthesis."""
        try:
            sequence = request.parameters.get("sequence", "")
            platform = request.parameters.get("platform", "twist_bioscience")

            sequence = sequence.upper().strip()
            if not sequence:
                return TaskResponse.failure(request.request_id, "No sequence provided")

            constraints = PLATFORMS.get(platform)
            if not constraints:
                return TaskResponse.failure(
                    request.request_id,
                    f"Unknown platform: {platform}",
                )

            issues = []
            optimized = sequence

            # Check GC
            gc = self._calculate_gc(optimized)
            if gc < constraints.min_gc or gc > constraints.max_gc:
                issues.append(f"GC content ({gc:.1%}) outside range")
                optimized = self._balance_gc(optimized, constraints.min_gc, constraints.max_gc)

            # Check homopolymers
            max_run = self._find_max_run(optimized)
            if max_run > constraints.max_homopolymer:
                issues.append(f"Homopolymer run ({max_run}) exceeds limit")
                optimized = self._break_homopolymers(optimized, constraints.max_homopolymer)

            # Check forbidden
            for forbidden in constraints.forbidden:
                if forbidden in optimized:
                    issues.append(f"Forbidden sequence: {forbidden}")
                    optimized = self._remove_forbidden(optimized, forbidden)

            return TaskResponse.success(
                request.request_id,
                {
                    "original": sequence,
                    "optimized": optimized,
                    "platform": platform,
                    "issues_found": len(issues),
                    "issues": issues,
                    "modified": sequence != optimized,
                    "final_gc": self._calculate_gc(optimized),
                    "final_max_homopolymer": self._find_max_run(optimized),
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _check_constraints(self, request: TaskRequest) -> TaskResponse:
        """Check sequence against platform constraints."""
        try:
            sequence = request.parameters.get("sequence", "")
            platform = request.parameters.get("platform", "twist_bioscience")

            sequence = sequence.upper().strip()
            constraints = PLATFORMS.get(platform)

            if not constraints:
                return TaskResponse.failure(
                    request.request_id,
                    f"Unknown platform: {platform}",
                )

            issues = []

            # Length
            if len(sequence) > constraints.max_length:
                issues.append({
                    "type": "length",
                    "severity": "error",
                    "message": f"Length {len(sequence)} > max {constraints.max_length}",
                })

            # GC
            gc = self._calculate_gc(sequence)
            if gc < constraints.min_gc or gc > constraints.max_gc:
                issues.append({
                    "type": "gc_content",
                    "severity": "warning",
                    "message": f"GC {gc:.1%} outside {constraints.min_gc:.0%}-{constraints.max_gc:.0%}",
                })

            # Homopolymer
            max_run = self._find_max_run(sequence)
            if max_run > constraints.max_homopolymer:
                issues.append({
                    "type": "homopolymer",
                    "severity": "warning",
                    "message": f"Run {max_run} > max {constraints.max_homopolymer}",
                })

            # Forbidden
            for forbidden in constraints.forbidden:
                if forbidden in sequence:
                    issues.append({
                        "type": "forbidden",
                        "severity": "error",
                        "message": f"Contains {forbidden}",
                    })

            passes = not any(i["severity"] == "error" for i in issues)

            return TaskResponse.success(
                request.request_id,
                {
                    "passes": passes,
                    "issues": issues,
                    "gc_content": gc,
                    "max_homopolymer": max_run,
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _fragment_sequence(self, request: TaskRequest) -> TaskResponse:
        """Fragment sequence for synthesis."""
        try:
            sequence = request.parameters.get("sequence", "")
            platform = request.parameters.get("platform", "twist_bioscience")
            overlap = request.parameters.get("overlap", 20)

            sequence = sequence.upper().strip()
            constraints = PLATFORMS.get(platform)

            if not constraints:
                return TaskResponse.failure(
                    request.request_id,
                    f"Unknown platform: {platform}",
                )

            max_len = constraints.max_length
            fragments = []
            pos = 0
            idx = 0

            while pos < len(sequence):
                end = min(pos + max_len, len(sequence))
                frag = sequence[pos:end]

                overlap_5 = sequence[max(0, pos - overlap):pos] if pos > 0 else ""
                overlap_3 = sequence[end:min(len(sequence), end + overlap)]

                fragments.append({
                    "index": idx,
                    "sequence": frag,
                    "length": len(frag),
                    "start": pos,
                    "end": end,
                    "overlap_5prime": overlap_5,
                    "overlap_3prime": overlap_3,
                })

                pos = end - overlap if end < len(sequence) else end
                idx += 1

            return TaskResponse.success(
                request.request_id,
                {
                    "original_length": len(sequence),
                    "fragment_count": len(fragments),
                    "fragments": fragments,
                    "assembly_method": "Gibson Assembly" if overlap >= 20 else "Ligation",
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _generate_order(self, request: TaskRequest) -> TaskResponse:
        """Generate synthesis order."""
        try:
            sequence = request.parameters.get("sequence", "")
            platform = request.parameters.get("platform", "twist_bioscience")
            project = request.parameters.get("project_name", "VibeDNA_Order")

            # Fragment first
            frag_result = await self._fragment_sequence(request)
            if frag_result.status != "completed":
                return frag_result

            frags = frag_result.result["fragments"]
            constraints = PLATFORMS.get(platform)

            # Generate FASTA
            lines = [
                f"# VibeDNA Synthesis Order",
                f"# Platform: {constraints.name if constraints else platform}",
                f"# Project: {project}",
                f"# Fragments: {len(frags)}",
                "",
            ]

            for frag in frags:
                lines.append(f">Fragment_{frag['index']:03d} [{frag['start']}-{frag['end']}]")
                seq = frag["sequence"]
                for i in range(0, len(seq), 60):
                    lines.append(seq[i:i + 60])
                lines.append("")

            lines.append(self.FOOTER)
            order = "\n".join(lines)

            return TaskResponse.success(
                request.request_id,
                {
                    "project_name": project,
                    "platform": platform,
                    "fragment_count": len(frags),
                    "order_content": order,
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    def _calculate_gc(self, seq: str) -> float:
        """Calculate GC content."""
        if not seq:
            return 0.0
        return sum(1 for c in seq if c in "GC") / len(seq)

    def _find_max_run(self, seq: str) -> int:
        """Find maximum homopolymer run."""
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

    def _balance_gc(self, seq: str, min_gc: float, max_gc: float) -> str:
        """Balance GC content."""
        result = list(seq)
        gc = self._calculate_gc(seq)
        target = (min_gc + max_gc) / 2

        if gc < target:
            for i in range(len(result)):
                if result[i] == 'A':
                    result[i] = 'G'
                    if self._calculate_gc(''.join(result)) >= target:
                        break
                elif result[i] == 'T':
                    result[i] = 'C'
                    if self._calculate_gc(''.join(result)) >= target:
                        break
        elif gc > target:
            for i in range(len(result)):
                if result[i] == 'G':
                    result[i] = 'A'
                    if self._calculate_gc(''.join(result)) <= target:
                        break
                elif result[i] == 'C':
                    result[i] = 'T'
                    if self._calculate_gc(''.join(result)) <= target:
                        break

        return ''.join(result)

    def _break_homopolymers(self, seq: str, max_run: int) -> str:
        """Break long homopolymer runs."""
        result = list(seq)
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}

        i = 0
        while i < len(result):
            start = i
            while i < len(result) and result[i] == result[start]:
                i += 1
            run_len = i - start

            if run_len > max_run:
                for j in range(start + max_run, i, max_run):
                    if j < len(result):
                        result[j] = complement[result[j]]

        return ''.join(result)

    def _remove_forbidden(self, seq: str, forbidden: str) -> str:
        """Remove forbidden sequence."""
        result = seq
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}

        while forbidden in result:
            pos = result.find(forbidden)
            mid = pos + len(forbidden) // 2
            chars = list(result)
            chars[mid] = complement[chars[mid]]
            result = ''.join(chars)

        return result
