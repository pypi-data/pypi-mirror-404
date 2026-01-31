# VibeDNA Synthesis MCP Server
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Synthesis MCP Server for DNA synthesis optimization.

Provides tools for:
- Sequence optimization for synthesis platforms
- Constraint checking
- Fragment generation for assembly
- Synthesis order generation
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from vibedna.agents.mcp_servers.base_server import (
    BaseMCPServer,
    MCPServerConfig,
    MCPTool,
    MCPToolParameter,
    MCPResource,
    TransportType,
)


@dataclass
class PlatformConstraints:
    """Constraints for a DNA synthesis platform."""
    name: str
    max_length: int
    min_gc: float
    max_gc: float
    max_homopolymer: int
    forbidden_sequences: List[str] = field(default_factory=list)


# Define platform constraints
PLATFORM_CONSTRAINTS = {
    "twist_bioscience": PlatformConstraints(
        name="Twist Bioscience",
        max_length=300,
        min_gc=0.25,
        max_gc=0.65,
        max_homopolymer=6,
        forbidden_sequences=["GAATTC", "GGATCC"],  # EcoRI, BamHI sites
    ),
    "idt": PlatformConstraints(
        name="IDT",
        max_length=200,
        min_gc=0.30,
        max_gc=0.70,
        max_homopolymer=4,
        forbidden_sequences=[],
    ),
    "genscript": PlatformConstraints(
        name="GenScript",
        max_length=500,
        min_gc=0.20,
        max_gc=0.80,
        max_homopolymer=8,
        forbidden_sequences=[],
    ),
}


@dataclass
class SynthesisFragment:
    """A fragment for DNA synthesis."""
    index: int
    sequence: str
    start: int
    end: int
    overlap_5prime: str = ""
    overlap_3prime: str = ""


class VibeDNASynthMCPServer(BaseMCPServer):
    """
    Synthesis MCP Server for DNA synthesis optimization.

    Tools:
    - optimize_sequence: Optimize sequence for synthesis
    - check_constraints: Check sequence against platform constraints
    - fragment_sequence: Split sequence into synthesizable fragments
    - generate_order: Generate synthesis order file
    """

    def __init__(self, config: Optional[MCPServerConfig] = None):
        """Initialize the Synthesis MCP server."""
        if config is None:
            config = MCPServerConfig(
                name="vibedna-synth",
                version="1.0.0",
                description="DNA synthesis optimization MCP server",
                transport=TransportType.SSE,
                url="https://mcp.vibedna.vibecaas.com/synth",
                port=8095,
            )
        super().__init__(config)

    def _register_tools(self) -> None:
        """Register synthesis tools."""

        # optimize_sequence tool
        self.register_tool(MCPTool(
            name="optimize_sequence",
            description="Optimize a DNA sequence for synthesis on a specific platform",
            parameters=[
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence to optimize",
                    required=True,
                ),
                MCPToolParameter(
                    name="platform",
                    param_type="string",
                    description="Target synthesis platform",
                    required=False,
                    default="twist_bioscience",
                    enum=["twist_bioscience", "idt", "genscript"],
                ),
            ],
            handler=self._optimize_sequence,
        ))

        # check_constraints tool
        self.register_tool(MCPTool(
            name="check_constraints",
            description="Check if sequence meets platform constraints",
            parameters=[
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence to check",
                    required=True,
                ),
                MCPToolParameter(
                    name="platform",
                    param_type="string",
                    description="Target synthesis platform",
                    required=False,
                    default="twist_bioscience",
                    enum=["twist_bioscience", "idt", "genscript"],
                ),
            ],
            handler=self._check_constraints,
        ))

        # fragment_sequence tool
        self.register_tool(MCPTool(
            name="fragment_sequence",
            description="Split sequence into synthesizable fragments with overlaps",
            parameters=[
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence to fragment",
                    required=True,
                ),
                MCPToolParameter(
                    name="platform",
                    param_type="string",
                    description="Target synthesis platform",
                    required=False,
                    default="twist_bioscience",
                    enum=["twist_bioscience", "idt", "genscript"],
                ),
                MCPToolParameter(
                    name="overlap",
                    param_type="integer",
                    description="Overlap length between fragments",
                    required=False,
                    default=20,
                ),
            ],
            handler=self._fragment_sequence,
        ))

        # generate_order tool
        self.register_tool(MCPTool(
            name="generate_order",
            description="Generate a synthesis order file in FASTA format",
            parameters=[
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence",
                    required=True,
                ),
                MCPToolParameter(
                    name="platform",
                    param_type="string",
                    description="Target synthesis platform",
                    required=False,
                    default="twist_bioscience",
                    enum=["twist_bioscience", "idt", "genscript"],
                ),
                MCPToolParameter(
                    name="project_name",
                    param_type="string",
                    description="Name for the synthesis project",
                    required=False,
                    default="VibeDNA_Order",
                ),
            ],
            handler=self._generate_order,
        ))

    def _register_resources(self) -> None:
        """Register synthesis resources."""

        self.register_resource(MCPResource(
            name="platforms",
            description="Available synthesis platforms and their constraints",
            uri="vibedna://synth/platforms",
            mime_type="application/json",
            handler=self._get_platforms,
        ))

    async def _optimize_sequence(
        self,
        sequence: str,
        platform: str = "twist_bioscience",
    ) -> Dict[str, Any]:
        """Optimize sequence for synthesis."""
        try:
            sequence = sequence.upper().strip()
            constraints = PLATFORM_CONSTRAINTS.get(platform)

            if not constraints:
                raise ValueError(f"Unknown platform: {platform}")

            issues = []
            optimized = sequence

            # Check and fix GC content
            gc = self._calculate_gc(optimized)
            if gc < constraints.min_gc or gc > constraints.max_gc:
                issues.append(f"GC content ({gc:.1%}) outside range")
                optimized = self._balance_gc(optimized, constraints.min_gc, constraints.max_gc)

            # Check and fix homopolymers
            max_run = self._find_max_run(optimized)
            if max_run > constraints.max_homopolymer:
                issues.append(f"Homopolymer run ({max_run}) exceeds limit")
                optimized = self._break_homopolymers(optimized, constraints.max_homopolymer)

            # Check and remove forbidden sequences
            for forbidden in constraints.forbidden_sequences:
                if forbidden in optimized:
                    issues.append(f"Forbidden sequence found: {forbidden}")
                    optimized = self._remove_forbidden(optimized, forbidden)

            return {
                "original": sequence,
                "optimized": optimized,
                "platform": platform,
                "issues_found": len(issues),
                "issues": issues,
                "modifications_made": sequence != optimized,
                "final_gc": self._calculate_gc(optimized),
                "final_max_homopolymer": self._find_max_run(optimized),
            }
        except Exception as e:
            raise ValueError(f"Optimization failed: {str(e)}")

    async def _check_constraints(
        self,
        sequence: str,
        platform: str = "twist_bioscience",
    ) -> Dict[str, Any]:
        """Check sequence against platform constraints."""
        try:
            sequence = sequence.upper().strip()
            constraints = PLATFORM_CONSTRAINTS.get(platform)

            if not constraints:
                raise ValueError(f"Unknown platform: {platform}")

            issues = []

            # Length check
            if len(sequence) > constraints.max_length:
                issues.append({
                    "type": "length",
                    "severity": "error",
                    "message": f"Sequence length ({len(sequence)}) exceeds max ({constraints.max_length})",
                })

            # GC content check
            gc = self._calculate_gc(sequence)
            if gc < constraints.min_gc:
                issues.append({
                    "type": "gc_content",
                    "severity": "warning",
                    "message": f"GC content ({gc:.1%}) below minimum ({constraints.min_gc:.0%})",
                })
            elif gc > constraints.max_gc:
                issues.append({
                    "type": "gc_content",
                    "severity": "warning",
                    "message": f"GC content ({gc:.1%}) above maximum ({constraints.max_gc:.0%})",
                })

            # Homopolymer check
            max_run = self._find_max_run(sequence)
            if max_run > constraints.max_homopolymer:
                issues.append({
                    "type": "homopolymer",
                    "severity": "warning",
                    "message": f"Homopolymer run ({max_run}) exceeds limit ({constraints.max_homopolymer})",
                })

            # Forbidden sequences check
            for forbidden in constraints.forbidden_sequences:
                if forbidden in sequence:
                    pos = sequence.find(forbidden)
                    issues.append({
                        "type": "forbidden_sequence",
                        "severity": "error",
                        "message": f"Forbidden sequence '{forbidden}' found at position {pos}",
                    })

            passes = not any(i["severity"] == "error" for i in issues)

            return {
                "sequence_length": len(sequence),
                "platform": platform,
                "passes_constraints": passes,
                "issues": issues,
                "gc_content": gc,
                "max_homopolymer": max_run,
            }
        except Exception as e:
            raise ValueError(f"Constraint check failed: {str(e)}")

    async def _fragment_sequence(
        self,
        sequence: str,
        platform: str = "twist_bioscience",
        overlap: int = 20,
    ) -> Dict[str, Any]:
        """Fragment sequence for synthesis."""
        try:
            sequence = sequence.upper().strip()
            constraints = PLATFORM_CONSTRAINTS.get(platform)

            if not constraints:
                raise ValueError(f"Unknown platform: {platform}")

            max_length = constraints.max_length
            fragments = []

            pos = 0
            index = 0

            while pos < len(sequence):
                end = min(pos + max_length, len(sequence))
                fragment_seq = sequence[pos:end]

                # Get overlaps
                overlap_5 = sequence[max(0, pos - overlap):pos] if pos > 0 else ""
                overlap_3 = sequence[end:min(len(sequence), end + overlap)]

                fragment = SynthesisFragment(
                    index=index,
                    sequence=fragment_seq,
                    start=pos,
                    end=end,
                    overlap_5prime=overlap_5,
                    overlap_3prime=overlap_3,
                )

                fragments.append({
                    "index": fragment.index,
                    "sequence": fragment.sequence,
                    "length": len(fragment.sequence),
                    "start": fragment.start,
                    "end": fragment.end,
                    "overlap_5prime": fragment.overlap_5prime,
                    "overlap_3prime": fragment.overlap_3prime,
                })

                # Move position, accounting for overlap
                pos = end - overlap if end < len(sequence) else end
                index += 1

            return {
                "original_length": len(sequence),
                "platform": platform,
                "fragment_count": len(fragments),
                "overlap_length": overlap,
                "max_fragment_length": max_length,
                "fragments": fragments,
                "assembly_method": "Gibson Assembly" if overlap >= 20 else "Ligation",
            }
        except Exception as e:
            raise ValueError(f"Fragmentation failed: {str(e)}")

    async def _generate_order(
        self,
        sequence: str,
        platform: str = "twist_bioscience",
        project_name: str = "VibeDNA_Order",
    ) -> Dict[str, Any]:
        """Generate synthesis order file."""
        try:
            # First fragment the sequence
            frag_result = await self._fragment_sequence(sequence, platform)

            # Generate FASTA format
            fasta_lines = [
                f"# VibeDNA Synthesis Order",
                f"# Platform: {PLATFORM_CONSTRAINTS[platform].name}",
                f"# Project: {project_name}",
                f"# Total Fragments: {frag_result['fragment_count']}",
                f"# Assembly Method: {frag_result['assembly_method']}",
                "",
            ]

            for frag in frag_result["fragments"]:
                header = f">Fragment_{frag['index']:03d} [{frag['start']}-{frag['end']}]"
                if frag["overlap_5prime"]:
                    header += f" overlap_5prime={frag['overlap_5prime']}"
                if frag["overlap_3prime"]:
                    header += f" overlap_3prime={frag['overlap_3prime']}"

                fasta_lines.append(header)

                # Wrap sequence at 60 characters
                seq = frag["sequence"]
                for i in range(0, len(seq), 60):
                    fasta_lines.append(seq[i:i + 60])

                fasta_lines.append("")

            fasta_lines.append(self.FOOTER)

            order_content = "\n".join(fasta_lines)

            return {
                "project_name": project_name,
                "platform": platform,
                "fragment_count": frag_result["fragment_count"],
                "total_nucleotides": sum(len(f["sequence"]) for f in frag_result["fragments"]),
                "order_format": "FASTA",
                "order_content": order_content,
            }
        except Exception as e:
            raise ValueError(f"Order generation failed: {str(e)}")

    def _get_platforms(self) -> Dict[str, Any]:
        """Get available platforms."""
        platforms = []
        for key, constraints in PLATFORM_CONSTRAINTS.items():
            platforms.append({
                "id": key,
                "name": constraints.name,
                "max_length": constraints.max_length,
                "gc_range": [constraints.min_gc, constraints.max_gc],
                "max_homopolymer": constraints.max_homopolymer,
                "forbidden_sequences": constraints.forbidden_sequences,
            })

        return {"platforms": platforms}

    def _calculate_gc(self, sequence: str) -> float:
        """Calculate GC content."""
        if not sequence:
            return 0.0
        gc_count = sum(1 for c in sequence if c in "GC")
        return gc_count / len(sequence)

    def _find_max_run(self, sequence: str) -> int:
        """Find maximum homopolymer run."""
        if not sequence:
            return 0

        max_run = 1
        current_run = 1

        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i - 1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1

        return max_run

    def _balance_gc(self, sequence: str, min_gc: float, max_gc: float) -> str:
        """Attempt to balance GC content by making silent substitutions."""
        # This is a simplified implementation
        # In production, would use codon optimization if sequence is coding
        result = list(sequence)
        gc = self._calculate_gc(sequence)
        target = (min_gc + max_gc) / 2

        # AT <-> GC transitions that preserve encoding
        # This is simplified - would need context-aware substitution
        if gc < target:
            # Need more GC
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
            # Need less GC
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

    def _break_homopolymers(self, sequence: str, max_run: int) -> str:
        """Break homopolymer runs by inserting synonymous changes."""
        result = list(sequence)
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}

        i = 0
        while i < len(result):
            run_start = i
            while i < len(result) and result[i] == result[run_start]:
                i += 1
            run_length = i - run_start

            if run_length > max_run:
                # Insert breaks at regular intervals
                for j in range(run_start + max_run, i, max_run):
                    if j < len(result):
                        # Use complement to break the run
                        result[j] = complement[result[j]]

        return ''.join(result)

    def _remove_forbidden(self, sequence: str, forbidden: str) -> str:
        """Remove forbidden sequence by making substitutions."""
        result = sequence
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}

        while forbidden in result:
            pos = result.find(forbidden)
            # Change middle nucleotide of forbidden sequence
            mid = pos + len(forbidden) // 2
            chars = list(result)
            chars[mid] = complement[chars[mid]]
            result = ''.join(chars)

        return result
