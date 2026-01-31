# VibeDNA Decoder Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Decoder Agent - Specialized agent for DNA-to-binary conversion.

Supports:
- Auto-detection of encoding scheme
- Error detection during decoding
- Checksum verification
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
from vibedna.core.decoder import DNADecoder


class DecoderAgent(BaseAgent):
    """
    Decoder Agent for DNA-to-binary conversion.

    This specialist agent handles all decoding operations using
    the VibeDNA core decoding engine.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Decoder Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-decoder-agent",
                version="1.0.0",
                tier=AgentTier.SPECIALIST,
                role="DNA to Binary Decoder",
                description="Specialized agent for converting DNA sequences to binary data",
                capabilities=[
                    AgentCapability(
                        name="scheme_decoding",
                        description="Decode all supported schemes",
                    ),
                    AgentCapability(
                        name="auto_detection",
                        description="Auto-detect encoding scheme",
                    ),
                    AgentCapability(
                        name="error_detection",
                        description="Detect errors during decoding",
                    ),
                ],
                tools=[
                    "sequence_validator",
                    "header_parser",
                    "scheme_detector",
                    "block_extractor",
                    "scheme_decoder",
                    "checksum_verifier",
                ],
                mcp_connections=["vibedna-core"],
            )

        super().__init__(config)
        self._decoder = DNADecoder()

    def get_system_prompt(self) -> str:
        """Get the Decoder Agent's system prompt."""
        return """You are the VibeDNA Decoder Agent, specializing in DNA-to-binary conversion.

## Decoding Protocol

1. Validate sequence format
2. Parse header (first 256 nucleotides)
3. Auto-detect encoding scheme (or use header value)
4. Extract data blocks
5. Decode each block using scheme decoder
6. Verify checksum
7. Return binary data with metadata

## Scheme Auto-Detection

1. First check header for scheme code
2. If unavailable, use statistical detection:
   - Triplet: Look for ATC/GAC patterns
   - RLL: No runs > 3 nucleotides
   - Balanced GC: 45-55% GC content
   - Default: Quaternary

## Error Handling

- Invalid characters: Fail with error
- Checksum mismatch: Request error correction
- Missing header: Attempt best-effort decode

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a decoding task."""
        self.logger.info(f"Handling decode task: {request.request_id}")

        try:
            # Get parameters
            sequence = request.parameters.get("sequence", "")
            verify_checksum = request.parameters.get("verify_checksum", True)
            attempt_repair = request.parameters.get("attempt_repair", True)

            # Validate sequence
            sequence = sequence.upper().strip()
            if not sequence:
                return TaskResponse.failure(
                    request.request_id,
                    "No sequence provided",
                )

            if not all(c in "ATCG" for c in sequence):
                return TaskResponse.failure(
                    request.request_id,
                    "Invalid DNA sequence: contains non-ATCG characters",
                )

            # Decode
            result = self._decoder.decode(sequence, verify_checksum=verify_checksum)

            return TaskResponse.success(
                request.request_id,
                {
                    "data": base64.b64encode(result.data).decode("utf-8"),
                    "filename": result.filename,
                    "mime_type": result.mime_type,
                    "scheme": result.scheme,
                    "original_size": len(result.data),
                    "errors_corrected": result.errors_corrected,
                    "metadata": {
                        "integrity_valid": result.integrity_valid,
                    },
                },
                quality_report={
                    "decoding_valid": True,
                    "errors_corrected": result.errors_corrected,
                    "checksum_valid": result.integrity_valid,
                },
            )

        except Exception as e:
            self.logger.error(f"Decoding failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))
