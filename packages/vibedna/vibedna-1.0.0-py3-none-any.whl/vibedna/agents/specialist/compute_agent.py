# VibeDNA Compute Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Compute Agent - DNA-native computation engine.

Performs operations directly on DNA sequences:
- Logic gates (AND, OR, XOR, NOT, etc.)
- Arithmetic (add, subtract, multiply, divide)
- Comparison and shifting
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
from vibedna.compute.dna_logic_gates import DNAComputeEngine, DNALogicGate


class ComputeAgent(BaseAgent):
    """
    Compute Agent for DNA-native computation.

    Performs logical and arithmetic operations directly on
    DNA sequences without encode/decode cycles.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Compute Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-compute-agent",
                version="1.0.0",
                tier=AgentTier.SPECIALIST,
                role="DNA-Native Computation Engine",
                description="Performs computations directly on DNA sequences",
                capabilities=[
                    AgentCapability(
                        name="logic_gates",
                        description="AND, OR, XOR, NOT, NAND, NOR, XNOR",
                    ),
                    AgentCapability(
                        name="arithmetic",
                        description="Addition, subtraction, multiplication, division",
                    ),
                    AgentCapability(
                        name="comparison",
                        description="Compare DNA numbers",
                    ),
                    AgentCapability(
                        name="shifting",
                        description="Bit shift operations",
                    ),
                ],
                tools=[
                    "logic_gate_executor",
                    "arithmetic_processor",
                    "expression_parser",
                    "sequence_comparator",
                    "shift_operator",
                ],
                mcp_connections=["vibedna-compute"],
            )

        super().__init__(config)
        self._compute = DNAComputeEngine()

    def get_system_prompt(self) -> str:
        """Get the Compute Agent's system prompt."""
        return """You are the VibeDNA Compute Agent, executing computations on DNA-encoded data.

## DNA Logic Gates

Map binary logic to nucleotide operations:
- Nucleotide values: A=0, T=1, C=2, G=3
- AND: min of nucleotide values
- OR: max of nucleotide values
- XOR: (a + b) mod 4
- NOT: complement (A↔G, T↔C)

## DNA Arithmetic

Base-4 arithmetic on DNA numbers:
- Addition: with carry
- Subtraction: with borrow
- Multiplication: standard algorithm
- Division: quotient and remainder

## Expression Evaluation

Supports compound expressions:
- Variables: A, B, C, etc.
- Operators: AND, OR, XOR, NOT, NAND, NOR, XNOR
- Parentheses for grouping

Example: "(A AND B) XOR C"

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a compute task."""
        self.logger.info(f"Handling compute task: {request.request_id}")

        operation = request.parameters.get("operation", "and")

        if operation in ["and", "or", "xor", "not", "nand", "nor", "xnor"]:
            return await self._execute_logic_gate(request, operation)
        elif operation in ["add", "subtract", "multiply", "divide"]:
            return await self._execute_arithmetic(request, operation)
        elif operation == "compare":
            return await self._execute_compare(request)
        elif operation in ["shift_left", "shift_right"]:
            return await self._execute_shift(request, operation)
        else:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown operation: {operation}",
            )

    async def _execute_logic_gate(
        self,
        request: TaskRequest,
        operation: str,
    ) -> TaskResponse:
        """Execute a logic gate operation."""
        try:
            seq_a = request.parameters.get("sequence_a", "").upper().strip()
            seq_b = request.parameters.get("sequence_b", "").upper().strip()

            if not seq_a:
                return TaskResponse.failure(request.request_id, "sequence_a required")

            # Validate sequences
            if not all(c in "ATCG" for c in seq_a):
                return TaskResponse.failure(request.request_id, "Invalid sequence_a")

            if seq_b and not all(c in "ATCG" for c in seq_b):
                return TaskResponse.failure(request.request_id, "Invalid sequence_b")

            # Map operation to gate
            gate_map = {
                "and": DNALogicGate.AND,
                "or": DNALogicGate.OR,
                "xor": DNALogicGate.XOR,
                "not": DNALogicGate.NOT,
                "nand": DNALogicGate.NAND,
                "nor": DNALogicGate.NOR,
                "xnor": DNALogicGate.XNOR,
            }
            gate = gate_map[operation]

            # Execute gate
            if operation == "not":
                result = self._compute.apply_gate(gate, seq_a)
            else:
                if not seq_b:
                    return TaskResponse.failure(
                        request.request_id,
                        f"sequence_b required for {operation}",
                    )
                result = self._compute.apply_gate(gate, seq_a, seq_b)

            return TaskResponse.success(
                request.request_id,
                {
                    "operation": operation,
                    "sequence_a": seq_a,
                    "sequence_b": seq_b,
                    "result": result,
                },
            )

        except Exception as e:
            self.logger.error(f"Logic gate failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _execute_arithmetic(
        self,
        request: TaskRequest,
        operation: str,
    ) -> TaskResponse:
        """Execute an arithmetic operation."""
        try:
            seq_a = request.parameters.get("sequence_a", "").upper().strip()
            seq_b = request.parameters.get("sequence_b", "").upper().strip()

            if not seq_a or not seq_b:
                return TaskResponse.failure(
                    request.request_id,
                    "Both sequence_a and sequence_b required",
                )

            # Validate sequences
            if not all(c in "ATCG" for c in seq_a + seq_b):
                return TaskResponse.failure(request.request_id, "Invalid sequence")

            result = None
            extra = {}

            if operation == "add":
                result, overflow = self._compute.add(seq_a, seq_b)
                extra["overflow"] = overflow
            elif operation == "subtract":
                result, underflow = self._compute.subtract(seq_a, seq_b)
                extra["underflow"] = underflow
            elif operation == "multiply":
                result = self._compute.multiply(seq_a, seq_b)
            elif operation == "divide":
                quotient, remainder = self._compute.divide(seq_a, seq_b)
                result = quotient
                extra["remainder"] = remainder

            return TaskResponse.success(
                request.request_id,
                {
                    "operation": operation,
                    "sequence_a": seq_a,
                    "sequence_b": seq_b,
                    "result": result,
                    **extra,
                },
            )

        except Exception as e:
            self.logger.error(f"Arithmetic failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _execute_compare(self, request: TaskRequest) -> TaskResponse:
        """Compare two DNA sequences."""
        try:
            seq_a = request.parameters.get("sequence_a", "").upper().strip()
            seq_b = request.parameters.get("sequence_b", "").upper().strip()

            if not seq_a or not seq_b:
                return TaskResponse.failure(
                    request.request_id,
                    "Both sequences required",
                )

            comparison = self._compute.compare(seq_a, seq_b)

            return TaskResponse.success(
                request.request_id,
                {
                    "sequence_a": seq_a,
                    "sequence_b": seq_b,
                    "comparison": comparison,
                    "equal": comparison == 0,
                    "a_greater": comparison > 0,
                    "b_greater": comparison < 0,
                },
            )

        except Exception as e:
            self.logger.error(f"Compare failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _execute_shift(
        self,
        request: TaskRequest,
        operation: str,
    ) -> TaskResponse:
        """Execute a shift operation."""
        try:
            sequence = request.parameters.get("sequence", "").upper().strip()
            positions = request.parameters.get("positions", 1)

            if not sequence:
                return TaskResponse.failure(request.request_id, "sequence required")

            if operation == "shift_left":
                result = self._compute.shift_left(sequence, positions)
            else:
                result = self._compute.shift_right(sequence, positions)

            return TaskResponse.success(
                request.request_id,
                {
                    "original": sequence,
                    "direction": "left" if operation == "shift_left" else "right",
                    "positions": positions,
                    "result": result,
                },
            )

        except Exception as e:
            self.logger.error(f"Shift failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))
