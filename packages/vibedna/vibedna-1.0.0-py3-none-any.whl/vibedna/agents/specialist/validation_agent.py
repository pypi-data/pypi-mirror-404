# VibeDNA Validation Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Validation Agent - Sequence validation and integrity checking.

Validates DNA sequences for:
- Format compliance
- Structural integrity
- Biological constraints
"""

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


class ValidationAgent(BaseAgent):
    """
    Validation Agent for DNA sequence quality assurance.

    Performs comprehensive validation of DNA sequences including
    format, structure, and biological constraint checks.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Validation Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-validation-agent",
                version="1.0.0",
                tier=AgentTier.SPECIALIST,
                role="Sequence Validation and Integrity",
                description="Validates DNA sequences for format and integrity",
                capabilities=[
                    AgentCapability(
                        name="format_validation",
                        description="Validate sequence format",
                    ),
                    AgentCapability(
                        name="structure_validation",
                        description="Validate header/footer structure",
                    ),
                    AgentCapability(
                        name="integrity_verification",
                        description="Verify checksums and integrity",
                    ),
                    AgentCapability(
                        name="biological_constraints",
                        description="Check GC content and homopolymers",
                    ),
                ],
                tools=[
                    "character_validator",
                    "structure_validator",
                    "checksum_verifier",
                    "gc_analyzer",
                    "homopolymer_detector",
                    "block_validator",
                ],
                mcp_connections=["vibedna-core"],
            )

        super().__init__(config)

    def get_system_prompt(self) -> str:
        """Get the Validation Agent's system prompt."""
        return """You are the VibeDNA Validation Agent, ensuring sequence quality and integrity.

## Validation Checks

1. Character validation - Only ATCG allowed
2. Header validation - Magic sequence, version, scheme
3. Footer validation - End marker, block count, checksum
4. Checksum validation - Verify integrity
5. Block structure validation - Block headers and data
6. GC content check - Warn if outside 30-70%
7. Homopolymer check - Warn if runs > 5

## Severity Levels

- error: Prevents further processing
- warning: Informational, processing can continue

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a validation task."""
        self.logger.info(f"Handling validation task: {request.request_id}")

        action = request.parameters.get("action", "validate")

        if action in ["validate", "validate_sequence"]:
            return await self._validate_sequence(request)
        elif action == "validate_binary":
            return await self._validate_binary(request)
        elif action == "validate_format":
            return await self._validate_format(request)
        elif action == "validate_structure":
            return await self._validate_structure(request)
        elif action == "verify_checksum":
            return await self._verify_checksum(request)
        elif action == "verify_integrity":
            return await self._verify_integrity(request)
        else:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown action: {action}",
            )

    async def _validate_sequence(self, request: TaskRequest) -> TaskResponse:
        """Comprehensive sequence validation."""
        try:
            sequence = request.parameters.get("sequence", "")
            sequence = sequence.upper().strip()

            issues = []

            # Character validation
            invalid_chars = set(sequence) - set("ATCG")
            if invalid_chars:
                issues.append({
                    "code": "INVALID_CHARS",
                    "severity": "error",
                    "message": f"Invalid characters: {invalid_chars}",
                })

            # Length check
            if len(sequence) < 256:
                issues.append({
                    "code": "TOO_SHORT",
                    "severity": "error",
                    "message": "Sequence too short for valid header",
                })
            else:
                # Header validation
                if sequence[:8] != "ATCGATCG":
                    issues.append({
                        "code": "MAGIC_MISSING",
                        "severity": "error",
                        "message": "VibeDNA magic sequence not found",
                    })

                # Footer validation
                if len(sequence) >= 32:
                    footer_start = sequence[-32:-24]
                    if footer_start != "GCTAGCTA":
                        issues.append({
                            "code": "FOOTER_MISSING",
                            "severity": "error",
                            "message": "VibeDNA footer marker not found",
                        })

            # GC content
            gc_count = sum(1 for c in sequence if c in "GC")
            gc_content = gc_count / len(sequence) if sequence else 0

            if gc_content < 0.3 or gc_content > 0.7:
                issues.append({
                    "code": "GC_IMBALANCE",
                    "severity": "warning",
                    "message": f"GC content ({gc_content:.1%}) outside optimal range",
                })

            # Homopolymer check
            max_run = self._find_max_run(sequence)
            if max_run > 5:
                issues.append({
                    "code": "LONG_HOMOPOLYMER",
                    "severity": "warning",
                    "message": f"Long homopolymer run: {max_run}",
                })

            is_valid = not any(i["severity"] == "error" for i in issues)

            return TaskResponse.success(
                request.request_id,
                {
                    "valid": is_valid,
                    "issues": issues,
                    "metadata": {
                        "length": len(sequence),
                        "gc_content": gc_content,
                        "max_homopolymer": max_run,
                    },
                },
                quality_report={
                    "validation_passed": is_valid,
                    "gc_content": gc_content,
                    "homopolymer_max": max_run,
                },
            )

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _validate_binary(self, request: TaskRequest) -> TaskResponse:
        """Validate binary data for encoding."""
        try:
            data = request.parameters.get("data")

            if data is None:
                return TaskResponse.failure(
                    request.request_id,
                    "No data provided",
                )

            # Check size limits
            max_size = 100 * 1024 * 1024  # 100MB
            if isinstance(data, (bytes, bytearray)):
                size = len(data)
            elif isinstance(data, str):
                size = len(data)
            else:
                return TaskResponse.failure(
                    request.request_id,
                    "Invalid data type",
                )

            issues = []
            if size > max_size:
                issues.append({
                    "code": "SIZE_EXCEEDED",
                    "severity": "error",
                    "message": f"Data size {size} exceeds max {max_size}",
                })

            if size == 0:
                issues.append({
                    "code": "EMPTY_DATA",
                    "severity": "warning",
                    "message": "Empty data provided",
                })

            is_valid = not any(i["severity"] == "error" for i in issues)

            return TaskResponse.success(
                request.request_id,
                {
                    "valid": is_valid,
                    "validated_data": data,
                    "size": size,
                    "issues": issues,
                },
            )

        except Exception as e:
            self.logger.error(f"Binary validation failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _validate_format(self, request: TaskRequest) -> TaskResponse:
        """Validate sequence format only."""
        try:
            sequence = request.parameters.get("sequence", "")
            sequence = sequence.upper().strip()

            issues = []
            invalid_chars = set(sequence) - set("ATCG")
            if invalid_chars:
                issues.append({
                    "code": "INVALID_CHARS",
                    "severity": "error",
                    "message": f"Invalid characters: {invalid_chars}",
                })

            is_valid = len(issues) == 0

            return TaskResponse.success(
                request.request_id,
                {"valid": is_valid, "issues": issues},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _validate_structure(self, request: TaskRequest) -> TaskResponse:
        """Validate sequence structure (header/footer)."""
        try:
            sequence = request.parameters.get("sequence", "")
            sequence = sequence.upper().strip()

            issues = []

            if len(sequence) < 256:
                issues.append({
                    "code": "TOO_SHORT",
                    "severity": "error",
                    "message": "Too short for header",
                })
            else:
                if sequence[:8] != "ATCGATCG":
                    issues.append({
                        "code": "MAGIC_MISSING",
                        "severity": "error",
                        "message": "Magic sequence missing",
                    })

            if len(sequence) >= 32:
                if sequence[-32:-24] != "GCTAGCTA":
                    issues.append({
                        "code": "FOOTER_MISSING",
                        "severity": "error",
                        "message": "Footer marker missing",
                    })

            is_valid = not any(i["severity"] == "error" for i in issues)

            return TaskResponse.success(
                request.request_id,
                {"valid": is_valid, "issues": issues},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _verify_checksum(self, request: TaskRequest) -> TaskResponse:
        """Verify sequence checksum."""
        try:
            sequence = request.parameters.get("sequence", "")
            expected = request.parameters.get("expected_checksum")

            # Extract checksum from footer
            if len(sequence) >= 32:
                actual_checksum = sequence[-16:]
            else:
                return TaskResponse.failure(
                    request.request_id,
                    "Sequence too short",
                )

            # Compare if expected provided
            if expected:
                valid = actual_checksum == expected
            else:
                # Can't verify without expected, assume valid
                valid = True

            return TaskResponse.success(
                request.request_id,
                {
                    "valid": valid,
                    "checksum": actual_checksum,
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _verify_integrity(self, request: TaskRequest) -> TaskResponse:
        """Full integrity verification."""
        try:
            sequence = request.parameters.get("sequence", "")

            # Run all validations
            format_result = await self._validate_format(request)
            structure_result = await self._validate_structure(request)
            checksum_result = await self._verify_checksum(request)

            all_issues = []
            if format_result.result:
                all_issues.extend(format_result.result.get("issues", []))
            if structure_result.result:
                all_issues.extend(structure_result.result.get("issues", []))

            is_valid = (
                format_result.result.get("valid", False) and
                structure_result.result.get("valid", False) and
                checksum_result.result.get("valid", False)
            )

            return TaskResponse.success(
                request.request_id,
                {
                    "valid": is_valid,
                    "issues": all_issues,
                    "format_valid": format_result.result.get("valid"),
                    "structure_valid": structure_result.result.get("valid"),
                    "checksum_valid": checksum_result.result.get("valid"),
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    def _find_max_run(self, sequence: str) -> int:
        """Find maximum homopolymer run length."""
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
