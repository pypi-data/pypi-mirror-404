# VibeDNA Encoder Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Encoder Agent - Specialized agent for binary-to-DNA conversion.

Supports multiple encoding schemes:
- Quaternary: 2 bits per nucleotide (highest density)
- Balanced GC: Synthesis-optimized encoding
- Run-Length Limited: Prevents homopolymer runs
- Redundant Triplet: High error tolerance
"""

import base64
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
    TaskStatus,
    OperationType,
)
from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme


class EncoderAgent(BaseAgent):
    """
    Encoder Agent for binary-to-DNA conversion.

    This specialist agent handles all encoding operations using
    the VibeDNA core encoding engine.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Encoder Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-encoder-agent",
                version="1.0.0",
                tier=AgentTier.SPECIALIST,
                role="Binary to DNA Encoder",
                description="Specialized agent for converting binary data to DNA sequences",
                capabilities=[
                    AgentCapability(
                        name="quaternary_encoding",
                        description="2 bits per nucleotide encoding",
                    ),
                    AgentCapability(
                        name="balanced_gc_encoding",
                        description="GC-balanced encoding for synthesis",
                    ),
                    AgentCapability(
                        name="rll_encoding",
                        description="Run-length limited encoding",
                    ),
                    AgentCapability(
                        name="triplet_encoding",
                        description="Redundant triplet encoding",
                    ),
                    AgentCapability(
                        name="streaming_encoding",
                        description="Streaming encoding for large files",
                    ),
                ],
                tools=[
                    "binary_converter",
                    "scheme_encoder",
                    "header_generator",
                    "block_chunker",
                    "checksum_calculator",
                    "gc_analyzer",
                ],
                mcp_connections=["vibedna-core"],
            )

        super().__init__(config)
        self._encoder = DNAEncoder()

    def get_system_prompt(self) -> str:
        """Get the Encoder Agent's system prompt."""
        return """You are the VibeDNA Encoder Agent, specializing in binary-to-DNA conversion.

## Encoding Schemes

### 1. Quaternary (Default)
Mapping: 00→A, 01→T, 10→C, 11→G
Density: 2 bits per nucleotide
Use case: Maximum storage density

### 2. Balanced GC
Rotating mapping to maintain 40-60% GC content
Density: ~1.9 bits per nucleotide
Use case: DNA synthesis compatibility

### 3. Run-Length Limited (RLL)
Inserts spacer nucleotides to prevent runs > 3
Density: ~1.7 bits per nucleotide
Use case: Sequencing accuracy

### 4. Redundant Triplet
Each bit encoded as 3 nucleotides (0→ATC, 1→GAC)
Density: 0.67 bits per nucleotide
Use case: Maximum error tolerance

## Encoding Protocol

1. Validate input data
2. Generate file header (256 nucleotides)
3. Convert to binary string
4. Apply encoding scheme
5. Chunk into blocks (1024 nucleotides)
6. Add block headers
7. Generate footer (32 nucleotides)
8. Return complete sequence

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle an encoding task."""
        self.logger.info(f"Handling encode task: {request.request_id}")

        try:
            # Get parameters
            data = request.parameters.get("data")
            scheme = request.parameters.get("scheme", "quaternary")
            filename = request.parameters.get("filename", "untitled")
            add_ec = request.parameters.get("add_error_correction", True)

            # Handle different input formats
            if isinstance(data, str):
                # Try to decode as base64
                try:
                    binary_data = base64.b64decode(data)
                except Exception:
                    # Treat as raw string
                    binary_data = data.encode("utf-8")
            elif isinstance(data, bytes):
                binary_data = data
            else:
                return TaskResponse.failure(
                    request.request_id,
                    "Invalid data format: expected string or bytes",
                )

            # Map scheme string to enum
            scheme_map = {
                "quaternary": EncodingScheme.QUATERNARY,
                "balanced_gc": EncodingScheme.BALANCED_GC,
                "rll": EncodingScheme.RUN_LENGTH_LIMITED,
                "triplet": EncodingScheme.REDUNDANT_TRIPLET,
            }
            encoding_scheme = scheme_map.get(scheme, EncodingScheme.QUATERNARY)

            # Configure and encode
            config = EncodingConfig(
                scheme=encoding_scheme,
                filename=filename,
                add_error_correction=add_ec,
            )
            encoder = DNAEncoder(config)

            result = encoder.encode(binary_data)

            # Calculate GC content
            gc_count = sum(1 for c in result.sequence if c in "GC")
            gc_content = gc_count / len(result.sequence) if result.sequence else 0

            return TaskResponse.success(
                request.request_id,
                {
                    "sequence": result.sequence,
                    "nucleotide_count": len(result.sequence),
                    "block_count": result.block_count,
                    "scheme": scheme,
                    "checksum": result.checksum,
                    "metadata": {
                        "original_size": len(binary_data),
                        "filename": filename,
                        "gc_content": gc_content,
                        "compression_ratio": len(binary_data) * 8 / len(result.sequence) if result.sequence else 0,
                    },
                },
                quality_report={
                    "encoding_valid": True,
                    "gc_content": gc_content,
                },
            )

        except Exception as e:
            self.logger.error(f"Encoding failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))
