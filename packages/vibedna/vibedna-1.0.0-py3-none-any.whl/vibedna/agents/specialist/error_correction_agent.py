# VibeDNA Error Correction Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Error Correction Agent - DNA error detection and correction using Reed-Solomon.

Implements:
- Reed-Solomon encoding in GF(4)
- Error detection and localization
- Mutation modeling
- Sequence repair
"""

from typing import Any, Dict, List, Optional, Tuple

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
from vibedna.error_correction.reed_solomon_dna import DNAReedSolomon


class ErrorCorrectionAgent(BaseAgent):
    """
    Error Correction Agent for DNA sequences.

    Implements Reed-Solomon error correction adapted for
    quaternary (DNA) encoding using GF(4) arithmetic.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Error Correction Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-error-correction-agent",
                version="1.0.0",
                tier=AgentTier.SPECIALIST,
                role="DNA Error Detection and Correction",
                description="Implements Reed-Solomon error correction for DNA sequences",
                capabilities=[
                    AgentCapability(
                        name="reed_solomon_encoding",
                        description="Add RS parity to sequences",
                    ),
                    AgentCapability(
                        name="reed_solomon_decoding",
                        description="Decode and correct errors",
                    ),
                    AgentCapability(
                        name="syndrome_computation",
                        description="Compute error syndromes",
                    ),
                    AgentCapability(
                        name="mutation_modeling",
                        description="Model biological mutation patterns",
                    ),
                ],
                tools=[
                    "rs_encoder",
                    "rs_decoder",
                    "syndrome_calculator",
                    "error_locator",
                    "mutation_modeler",
                    "sequence_repairer",
                ],
                mcp_connections=["vibedna-core"],
            )

        super().__init__(config)
        self._rs = DNAReedSolomon(nsym=16)  # 16 parity symbols, can correct 8 errors

    def get_system_prompt(self) -> str:
        """Get the Error Correction Agent's system prompt."""
        return """You are the VibeDNA Error Correction Agent, implementing robust error
detection and correction for DNA sequences.

## Reed-Solomon for DNA

DNA naturally operates in GF(4):
- Elements: {0, 1, α, α+1} = {A, T, C, G}
- Addition: XOR operation
- Multiplication: Defined by primitive polynomial

### Correction Capacity

With 16 parity nucleotides per block:
- Can detect up to 16 errors
- Can correct up to 8 errors

### Mutation Model

DNA has specific mutation patterns:
- Transitions (A↔G, T↔C): 70% probability
- Transversions (purine↔pyrimidine): 30% probability

## Error Correction Workflow

1. Receive sequence with suspected errors
2. Compute Reed-Solomon syndromes
3. If syndromes all zero → no errors, return
4. Find error locator polynomial (Berlekamp-Massey)
5. Locate error positions (Chien search)
6. If errors > correction capacity:
   a. Apply mutation model for soft correction
   b. Flag as partially corrected
7. Apply Forney correction
8. Verify corrected sequence
9. Return with correction report

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle an error correction task."""
        self.logger.info(f"Handling error correction task: {request.request_id}")

        action = request.parameters.get("action", "decode")

        if action == "apply_reed_solomon" or action == "encode":
            return await self._apply_error_correction(request)
        elif action == "decode_reed_solomon" or action == "decode":
            return await self._decode_with_correction(request)
        elif action == "detect_errors":
            return await self._detect_errors(request)
        else:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown action: {action}",
            )

    async def _apply_error_correction(self, request: TaskRequest) -> TaskResponse:
        """Apply Reed-Solomon error correction to a sequence."""
        try:
            sequence = request.parameters.get("sequence", "")
            sequence = sequence.upper().strip()

            if not sequence:
                return TaskResponse.failure(request.request_id, "No sequence provided")

            if not all(c in "ATCG" for c in sequence):
                return TaskResponse.failure(
                    request.request_id,
                    "Invalid DNA sequence",
                )

            # Apply RS encoding
            protected = self._rs.encode(sequence)

            return TaskResponse.success(
                request.request_id,
                {
                    "sequence": protected,
                    "original_length": len(sequence),
                    "protected_length": len(protected),
                    "parity_nucleotides": len(protected) - len(sequence),
                    "correction_capacity": (len(protected) - len(sequence)) // 2,
                    "error_correction_applied": True,
                },
            )

        except Exception as e:
            self.logger.error(f"Error correction encoding failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _decode_with_correction(self, request: TaskRequest) -> TaskResponse:
        """Decode and correct errors in a sequence."""
        try:
            sequence = request.parameters.get("sequence", "")
            sequence = sequence.upper().strip()

            if not sequence:
                return TaskResponse.failure(request.request_id, "No sequence provided")

            # Decode with error correction
            result = self._rs.decode(sequence)

            return TaskResponse.success(
                request.request_id,
                {
                    "sequence": result.corrected_sequence,
                    "errors_detected": result.errors_detected,
                    "errors_corrected": result.errors_corrected,
                    "error_positions": result.error_positions,
                    "correction_successful": result.success,
                },
                quality_report={
                    "errors_detected": result.errors_detected,
                    "errors_corrected": result.errors_corrected,
                    "correction_successful": result.success,
                },
            )

        except Exception as e:
            self.logger.error(f"Error correction decoding failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _detect_errors(self, request: TaskRequest) -> TaskResponse:
        """Detect errors in a sequence without correction."""
        try:
            sequence = request.parameters.get("sequence", "")
            sequence = sequence.upper().strip()

            if not sequence:
                return TaskResponse.failure(request.request_id, "No sequence provided")

            # Check for errors using syndromes
            has_errors = self._rs.has_errors(sequence)

            return TaskResponse.success(
                request.request_id,
                {
                    "has_errors": has_errors,
                    "sequence_length": len(sequence),
                },
            )

        except Exception as e:
            self.logger.error(f"Error detection failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))
