# VibeDNA Compute Workflow Protocol
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Compute Workflow Protocol - DNA computation workflow orchestration.

Workflow Steps:
1. Validate input sequences
2. Execute operation
3. Validate result
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum


class ComputeOperation(Enum):
    """Supported compute operations."""
    AND = "and"
    OR = "or"
    XOR = "xor"
    NOT = "not"
    NAND = "nand"
    NOR = "nor"
    XNOR = "xnor"
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    COMPARE = "compare"
    SHIFT_LEFT = "shift_left"
    SHIFT_RIGHT = "shift_right"


class ComputeQualityGate(Enum):
    """Quality gates for compute workflow."""
    INPUT_VALID = "input_valid"
    COMPUTATION_COMPLETE = "computation_complete"
    RESULT_VALID = "result_valid"


@dataclass
class ComputeWorkflowConfig:
    """Configuration for compute workflow."""
    operation: ComputeOperation = ComputeOperation.AND
    validate_result: bool = True


class ComputeWorkflowProtocol:
    """
    Compute Workflow Protocol.

    Defines the standard workflow for DNA computations.
    """

    PROTOCOL_NAME = "compute_workflow"
    PROTOCOL_VERSION = "1.0.0"

    PARTICIPANTS = [
        "master_orchestrator",
        "workflow_orchestrator",
        "validation_agent",
        "compute_agent",
    ]

    SUPPORTED_OPERATIONS = {
        "logic_gates": ["and", "or", "xor", "not", "nand", "nor", "xnor"],
        "arithmetic": ["add", "subtract", "multiply", "divide"],
        "comparison": ["compare"],
        "shift": ["shift_left", "shift_right"],
    }

    ERROR_HANDLERS = {
        "validation_failure": {
            "action": "abort",
            "response": "invalid_sequence",
        },
        "computation_failure": {
            "action": "abort",
            "response": "computation_error",
        },
        "overflow": {
            "action": "return_with_warning",
            "warning": "overflow_occurred",
        },
    }

    @classmethod
    def get_steps(cls, config: Optional[ComputeWorkflowConfig] = None) -> List[Dict[str, Any]]:
        """Get workflow steps based on configuration."""
        if config is None:
            config = ComputeWorkflowConfig()

        steps = [
            {
                "id": "validate_sequences",
                "agent": "validation-agent",
                "action": "validate_sequence",
                "input": {
                    "sequence": "${trigger.sequence_a}",
                },
                "on_success": "execute_operation",
                "on_failure": "abort_invalid",
                "required": True,
            },
            {
                "id": "execute_operation",
                "agent": "compute-agent",
                "action": config.operation.value,
                "input": {
                    "sequence_a": "${trigger.sequence_a}",
                    "sequence_b": "${trigger.sequence_b}",
                    "operation": config.operation.value,
                },
                "on_success": "validate_result" if config.validate_result else "complete",
                "on_failure": "abort_computation_failed",
                "required": True,
            },
        ]

        if config.validate_result:
            steps.append({
                "id": "validate_result",
                "agent": "validation-agent",
                "action": "validate_sequence",
                "input": {"sequence": "${steps.execute_operation.output.result}"},
                "on_success": "complete",
                "on_failure": "warn_invalid_result",
                "required": True,
            })

        return steps

    @classmethod
    def get_quality_gates(cls, config: Optional[ComputeWorkflowConfig] = None) -> List[Dict[str, Any]]:
        """Get quality gates for the workflow."""
        if config is None:
            config = ComputeWorkflowConfig()

        gates = [
            {
                "name": ComputeQualityGate.INPUT_VALID.value,
                "agent": "validation-agent",
                "required": True,
            },
            {
                "name": ComputeQualityGate.COMPUTATION_COMPLETE.value,
                "agent": "compute-agent",
                "required": True,
            },
        ]

        if config.validate_result:
            gates.append({
                "name": ComputeQualityGate.RESULT_VALID.value,
                "agent": "validation-agent",
                "required": True,
            })

        return gates

    @classmethod
    def get_outputs(cls) -> Dict[str, str]:
        """Get workflow output mappings."""
        return {
            "result": "${steps.execute_operation.output.result}",
            "operation": "${trigger.operation}",
            "overflow": "${steps.execute_operation.output.overflow}",
            "remainder": "${steps.execute_operation.output.remainder}",
        }

    @classmethod
    def to_workflow_definition(cls, config: Optional[ComputeWorkflowConfig] = None) -> Dict[str, Any]:
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
