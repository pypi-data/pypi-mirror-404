# VibeDNA Decode Workflow Protocol
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Decode Workflow Protocol - Standard decoding workflow orchestration.

Workflow Steps:
1. Validate sequence format
2. Apply error correction
3. Decode to binary
4. Verify checksum
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum


class DecodeQualityGate(Enum):
    """Quality gates for decode workflow."""
    SEQUENCE_VALID = "sequence_valid"
    ERROR_CORRECTION_COMPLETE = "error_correction_complete"
    DECODING_COMPLETE = "decoding_complete"
    CHECKSUM_VALID = "checksum_valid"


@dataclass
class DecodeWorkflowConfig:
    """Configuration for decode workflow."""
    apply_error_correction: bool = True
    verify_checksum: bool = True
    attempt_repair: bool = True
    max_retries: int = 2


class DecodeWorkflowProtocol:
    """
    Decode Workflow Protocol.

    Defines the standard workflow for decoding DNA to binary data.
    """

    PROTOCOL_NAME = "decode_workflow"
    PROTOCOL_VERSION = "1.0.0"

    PARTICIPANTS = [
        "master_orchestrator",
        "workflow_orchestrator",
        "validation_agent",
        "error_correction_agent",
        "decoder_agent",
    ]

    ERROR_HANDLERS = {
        "validation_failure": {
            "action": "abort",
            "response": "invalid_sequence",
        },
        "decoding_failure": {
            "action": "retry_with_repair",
            "max_retries": 2,
        },
        "checksum_failure": {
            "action": "return_with_warning",
            "warning": "integrity_not_verified",
        },
    }

    @classmethod
    def get_steps(cls, config: Optional[DecodeWorkflowConfig] = None) -> List[Dict[str, Any]]:
        """Get workflow steps based on configuration."""
        if config is None:
            config = DecodeWorkflowConfig()

        steps = [
            {
                "id": "validate_sequence",
                "agent": "validation-agent",
                "action": "validate_sequence",
                "input": {"sequence": "${trigger.sequence}"},
                "on_success": "apply_error_correction" if config.apply_error_correction else "decode_data",
                "on_failure": "abort_invalid",
                "required": True,
            },
        ]

        if config.apply_error_correction:
            steps.append({
                "id": "apply_error_correction",
                "agent": "error-correction-agent",
                "action": "decode_reed_solomon",
                "input": {"sequence": "${steps.validate_sequence.input.sequence}"},
                "on_success": "decode_data",
                "on_failure": "decode_without_correction" if config.attempt_repair else "abort_corrupted",
                "required": False,
            })

        steps.append({
            "id": "decode_data",
            "agent": "decoder-agent",
            "action": "decode",
            "input": {
                "sequence": "${steps.apply_error_correction.output.sequence}" if config.apply_error_correction
                else "${steps.validate_sequence.input.sequence}",
                "verify_checksum": config.verify_checksum,
            },
            "on_success": "verify_checksum" if config.verify_checksum else "complete",
            "on_failure": "abort_decode_failed",
            "required": True,
        })

        if config.verify_checksum:
            steps.append({
                "id": "verify_checksum",
                "agent": "validation-agent",
                "action": "verify_checksum",
                "input": {
                    "data": "${steps.decode_data.output.data}",
                    "expected_checksum": "${steps.decode_data.output.checksum}",
                },
                "on_success": "complete",
                "on_failure": "warn_checksum_failed",
                "required": True,
            })

        return steps

    @classmethod
    def get_quality_gates(cls, config: Optional[DecodeWorkflowConfig] = None) -> List[Dict[str, Any]]:
        """Get quality gates for the workflow."""
        if config is None:
            config = DecodeWorkflowConfig()

        gates = [
            {
                "name": DecodeQualityGate.SEQUENCE_VALID.value,
                "agent": "validation-agent",
                "required": True,
            },
        ]

        if config.apply_error_correction:
            gates.append({
                "name": DecodeQualityGate.ERROR_CORRECTION_COMPLETE.value,
                "agent": "error-correction-agent",
                "required": False,
            })

        gates.append({
            "name": DecodeQualityGate.DECODING_COMPLETE.value,
            "agent": "decoder-agent",
            "required": True,
        })

        if config.verify_checksum:
            gates.append({
                "name": DecodeQualityGate.CHECKSUM_VALID.value,
                "agent": "validation-agent",
                "required": True,
            })

        return gates

    @classmethod
    def get_outputs(cls) -> Dict[str, str]:
        """Get workflow output mappings."""
        return {
            "data": "${steps.decode_data.output.data}",
            "filename": "${steps.decode_data.output.filename}",
            "mime_type": "${steps.decode_data.output.mime_type}",
            "errors_corrected": "${steps.apply_error_correction.output.errors_corrected}",
            "checksum_valid": "${steps.verify_checksum.output.valid}",
        }

    @classmethod
    def to_workflow_definition(cls, config: Optional[DecodeWorkflowConfig] = None) -> Dict[str, Any]:
        """Convert protocol to workflow definition."""
        return {
            "name": cls.PROTOCOL_NAME,
            "version": cls.PROTOCOL_VERSION,
            "participants": cls.PARTICIPANTS,
            "steps": cls.get_steps(config),
            "quality_gates": cls.get_quality_gates(config),
            "error_handlers": cls.ERROR_HANDLERS,
            "outputs": cls.get_outputs(),
        }
