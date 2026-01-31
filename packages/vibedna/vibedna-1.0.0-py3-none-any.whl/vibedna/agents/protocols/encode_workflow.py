# VibeDNA Encode Workflow Protocol
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Encode Workflow Protocol - Standard encoding workflow orchestration.

Workflow Steps:
1. Validate input data
2. Encode to DNA
3. Add error correction
4. Validate output sequence
5. Optionally store and index
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class EncodeQualityGate(Enum):
    """Quality gates for encode workflow."""
    INPUT_VALIDATION = "input_validation"
    ENCODING_COMPLETE = "encoding_complete"
    ERROR_CORRECTION_APPLIED = "error_correction_applied"
    OUTPUT_VALIDATION = "output_validation"


@dataclass
class EncodeWorkflowConfig:
    """Configuration for encode workflow."""
    scheme: str = "quaternary"
    add_error_correction: bool = True
    validate_output: bool = True
    store_result: bool = False
    index_result: bool = False
    max_retries: int = 2
    fallback_scheme: str = "triplet"


@dataclass
class EncodeWorkflowStep:
    """A step in the encode workflow."""
    id: str
    agent: str
    action: str
    required: bool = True
    on_success: Optional[str] = None
    on_failure: Optional[str] = None


class EncodeWorkflowProtocol:
    """
    Encode Workflow Protocol.

    Defines the standard workflow for encoding binary data to DNA.
    """

    PROTOCOL_NAME = "encode_workflow"
    PROTOCOL_VERSION = "1.0.0"

    # Workflow participants
    PARTICIPANTS = [
        "master_orchestrator",
        "workflow_orchestrator",
        "encoder_agent",
        "error_correction_agent",
        "validation_agent",
        "filesystem_agent",
        "index_agent",
    ]

    # Error handlers
    ERROR_HANDLERS = {
        "validation_failure": {
            "action": "abort",
            "response": "detailed_error",
        },
        "encoding_failure": {
            "action": "retry_with_fallback",
            "fallback_scheme": "triplet",
            "max_retries": 2,
        },
        "storage_failure": {
            "action": "return_sequence_only",
            "warning": "storage_unavailable",
        },
    }

    @classmethod
    def get_steps(cls, config: Optional[EncodeWorkflowConfig] = None) -> List[Dict[str, Any]]:
        """Get workflow steps based on configuration."""
        if config is None:
            config = EncodeWorkflowConfig()

        steps = [
            {
                "id": "validate_input",
                "agent": "validation-agent",
                "action": "validate_binary",
                "input": {"data": "${trigger.data}"},
                "on_success": "encode_data",
                "on_failure": "abort_with_error",
                "required": True,
            },
            {
                "id": "encode_data",
                "agent": "encoder-agent",
                "action": "encode",
                "input": {
                    "data": "${steps.validate_input.output.validated_data}",
                    "scheme": config.scheme,
                },
                "on_success": "add_error_correction" if config.add_error_correction else "validate_output",
                "on_failure": "retry_with_fallback",
                "required": True,
            },
        ]

        if config.add_error_correction:
            steps.append({
                "id": "add_error_correction",
                "agent": "error-correction-agent",
                "action": "apply_reed_solomon",
                "input": {"sequence": "${steps.encode_data.output.sequence}"},
                "on_success": "validate_output",
                "on_failure": "encode_without_ec",
                "required": False,
            })

        if config.validate_output:
            steps.append({
                "id": "validate_output",
                "agent": "validation-agent",
                "action": "validate_sequence",
                "input": {
                    "sequence": "${steps.add_error_correction.output.sequence}" if config.add_error_correction
                    else "${steps.encode_data.output.sequence}"
                },
                "on_success": "store_sequence" if config.store_result else "complete",
                "on_failure": "warn_and_continue",
                "required": True,
            })

        if config.store_result:
            steps.append({
                "id": "store_sequence",
                "agent": "filesystem-agent",
                "action": "create_file",
                "input": {
                    "sequence": "${steps.validate_output.input.sequence}",
                    "path": "${trigger.destination_path}",
                },
                "parallel_with": "index_sequence" if config.index_result else None,
                "on_success": "complete",
                "on_failure": "return_without_storage",
                "required": False,
            })

        if config.index_result:
            steps.append({
                "id": "index_sequence",
                "agent": "index-agent",
                "action": "add_to_catalog",
                "input": {
                    "sequence_id": "${steps.encode_data.output.sequence_id}",
                    "metadata": "${steps.encode_data.output.metadata}",
                },
                "required": False,
            })

        return steps

    @classmethod
    def get_quality_gates(cls, config: Optional[EncodeWorkflowConfig] = None) -> List[Dict[str, Any]]:
        """Get quality gates for the workflow."""
        if config is None:
            config = EncodeWorkflowConfig()

        gates = [
            {
                "name": EncodeQualityGate.INPUT_VALIDATION.value,
                "agent": "validation-agent",
                "required": True,
            },
            {
                "name": EncodeQualityGate.ENCODING_COMPLETE.value,
                "agent": "encoder-agent",
                "required": True,
            },
        ]

        if config.add_error_correction:
            gates.append({
                "name": EncodeQualityGate.ERROR_CORRECTION_APPLIED.value,
                "agent": "error-correction-agent",
                "required": False,
            })

        if config.validate_output:
            gates.append({
                "name": EncodeQualityGate.OUTPUT_VALIDATION.value,
                "agent": "validation-agent",
                "required": True,
            })

        return gates

    @classmethod
    def get_outputs(cls) -> Dict[str, str]:
        """Get workflow output mappings."""
        return {
            "sequence": "${steps.validate_output.input.sequence}",
            "sequence_id": "${steps.encode_data.output.sequence_id}",
            "nucleotide_count": "${steps.encode_data.output.nucleotide_count}",
            "checksum": "${steps.encode_data.output.checksum}",
            "file_id": "${steps.store_sequence.output.file_id}",
        }

    @classmethod
    def to_workflow_definition(cls, config: Optional[EncodeWorkflowConfig] = None) -> Dict[str, Any]:
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
