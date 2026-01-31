# VibeDNA Compute MCP Server
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Compute MCP Server for DNA-native computation operations.

Provides tools for:
- Logic gate operations (AND, OR, XOR, NOT, etc.)
- Arithmetic operations (add, subtract, multiply, divide)
- Sequence comparison
- Bit shift operations
- Expression evaluation
"""

from typing import Any, Dict, Optional

from vibedna.agents.mcp_servers.base_server import (
    BaseMCPServer,
    MCPServerConfig,
    MCPTool,
    MCPToolParameter,
    MCPResource,
    TransportType,
)
from vibedna.compute.dna_logic_gates import DNAComputeEngine, DNALogicGate


class VibeDNAComputeMCPServer(BaseMCPServer):
    """
    Compute MCP Server for DNA-native computation.

    Tools:
    - logic_gate: Apply logic gate to DNA sequences
    - arithmetic: Perform arithmetic on DNA sequences
    - compare: Compare two DNA sequences
    - shift: Bit shift DNA sequence
    - evaluate_expression: Evaluate compound expression
    """

    def __init__(self, config: Optional[MCPServerConfig] = None):
        """Initialize the Compute MCP server."""
        if config is None:
            config = MCPServerConfig(
                name="vibedna-compute",
                version="1.0.0",
                description="DNA computation MCP server",
                transport=TransportType.SSE,
                url="https://mcp.vibedna.vibecaas.com/compute",
                port=8091,
            )
        super().__init__(config)

        # Initialize compute engine
        self._compute = DNAComputeEngine()

    def _register_tools(self) -> None:
        """Register compute tools."""

        # logic_gate tool
        self.register_tool(MCPTool(
            name="logic_gate",
            description="Apply a logic gate operation to DNA sequences",
            parameters=[
                MCPToolParameter(
                    name="gate",
                    param_type="string",
                    description="Logic gate to apply",
                    required=True,
                    enum=["AND", "OR", "XOR", "NOT", "NAND", "NOR", "XNOR"],
                ),
                MCPToolParameter(
                    name="sequence_a",
                    param_type="string",
                    description="First DNA sequence",
                    required=True,
                ),
                MCPToolParameter(
                    name="sequence_b",
                    param_type="string",
                    description="Second DNA sequence (not required for NOT)",
                    required=False,
                ),
            ],
            handler=self._logic_gate,
        ))

        # arithmetic tool
        self.register_tool(MCPTool(
            name="arithmetic",
            description="Perform arithmetic operation on DNA sequences",
            parameters=[
                MCPToolParameter(
                    name="operation",
                    param_type="string",
                    description="Arithmetic operation",
                    required=True,
                    enum=["add", "subtract", "multiply", "divide"],
                ),
                MCPToolParameter(
                    name="sequence_a",
                    param_type="string",
                    description="First DNA sequence (operand A)",
                    required=True,
                ),
                MCPToolParameter(
                    name="sequence_b",
                    param_type="string",
                    description="Second DNA sequence (operand B)",
                    required=True,
                ),
            ],
            handler=self._arithmetic,
        ))

        # compare tool
        self.register_tool(MCPTool(
            name="compare",
            description="Compare two DNA sequences numerically",
            parameters=[
                MCPToolParameter(
                    name="sequence_a",
                    param_type="string",
                    description="First DNA sequence",
                    required=True,
                ),
                MCPToolParameter(
                    name="sequence_b",
                    param_type="string",
                    description="Second DNA sequence",
                    required=True,
                ),
            ],
            handler=self._compare,
        ))

        # shift tool
        self.register_tool(MCPTool(
            name="shift",
            description="Bit shift a DNA sequence",
            parameters=[
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence to shift",
                    required=True,
                ),
                MCPToolParameter(
                    name="direction",
                    param_type="string",
                    description="Shift direction",
                    required=True,
                    enum=["left", "right"],
                ),
                MCPToolParameter(
                    name="positions",
                    param_type="integer",
                    description="Number of positions to shift",
                    required=True,
                ),
            ],
            handler=self._shift,
        ))

        # evaluate_expression tool
        self.register_tool(MCPTool(
            name="evaluate_expression",
            description="Evaluate a compound expression with DNA sequences",
            parameters=[
                MCPToolParameter(
                    name="expression",
                    param_type="string",
                    description="Expression to evaluate (e.g., '(A AND B) XOR C')",
                    required=True,
                ),
                MCPToolParameter(
                    name="variables",
                    param_type="object",
                    description="Variable mappings (e.g., {'A': 'ATCG', 'B': 'GCTA'})",
                    required=True,
                ),
            ],
            handler=self._evaluate_expression,
        ))

    def _register_resources(self) -> None:
        """Register compute resources."""

        self.register_resource(MCPResource(
            name="operations",
            description="Available computation operations",
            uri="vibedna://compute/operations",
            mime_type="application/json",
            handler=self._get_operations,
        ))

    async def _logic_gate(
        self,
        gate: str,
        sequence_a: str,
        sequence_b: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply a logic gate operation."""
        try:
            sequence_a = sequence_a.upper().strip()
            if sequence_b:
                sequence_b = sequence_b.upper().strip()

            # Validate sequences
            for seq in [sequence_a, sequence_b]:
                if seq and not all(c in "ATCG" for c in seq):
                    raise ValueError(f"Invalid DNA sequence: contains non-ATCG characters")

            # Map gate name to enum
            gate_map = {
                "AND": DNALogicGate.AND,
                "OR": DNALogicGate.OR,
                "XOR": DNALogicGate.XOR,
                "NOT": DNALogicGate.NOT,
                "NAND": DNALogicGate.NAND,
                "NOR": DNALogicGate.NOR,
                "XNOR": DNALogicGate.XNOR,
            }

            gate_enum = gate_map.get(gate.upper())
            if not gate_enum:
                raise ValueError(f"Unknown gate: {gate}")

            # Apply gate
            if gate.upper() == "NOT":
                result = self._compute.apply_gate(gate_enum, sequence_a)
            else:
                if not sequence_b:
                    raise ValueError(f"Gate {gate} requires two sequences")
                result = self._compute.apply_gate(gate_enum, sequence_a, sequence_b)

            return {
                "gate": gate,
                "sequence_a": sequence_a,
                "sequence_b": sequence_b,
                "result": result,
            }
        except Exception as e:
            raise ValueError(f"Logic gate operation failed: {str(e)}")

    async def _arithmetic(
        self,
        operation: str,
        sequence_a: str,
        sequence_b: str,
    ) -> Dict[str, Any]:
        """Perform arithmetic operation."""
        try:
            sequence_a = sequence_a.upper().strip()
            sequence_b = sequence_b.upper().strip()

            # Validate sequences
            for seq in [sequence_a, sequence_b]:
                if not all(c in "ATCG" for c in seq):
                    raise ValueError(f"Invalid DNA sequence: contains non-ATCG characters")

            result = None
            overflow = None
            remainder = None

            if operation == "add":
                result, overflow = self._compute.add(sequence_a, sequence_b)
            elif operation == "subtract":
                result, overflow = self._compute.subtract(sequence_a, sequence_b)
            elif operation == "multiply":
                result = self._compute.multiply(sequence_a, sequence_b)
            elif operation == "divide":
                result, remainder = self._compute.divide(sequence_a, sequence_b)
            else:
                raise ValueError(f"Unknown operation: {operation}")

            response = {
                "operation": operation,
                "sequence_a": sequence_a,
                "sequence_b": sequence_b,
                "result": result,
            }

            if overflow is not None:
                response["overflow"] = overflow
            if remainder is not None:
                response["remainder"] = remainder

            return response
        except Exception as e:
            raise ValueError(f"Arithmetic operation failed: {str(e)}")

    async def _compare(
        self,
        sequence_a: str,
        sequence_b: str,
    ) -> Dict[str, Any]:
        """Compare two DNA sequences."""
        try:
            sequence_a = sequence_a.upper().strip()
            sequence_b = sequence_b.upper().strip()

            comparison = self._compute.compare(sequence_a, sequence_b)

            return {
                "sequence_a": sequence_a,
                "sequence_b": sequence_b,
                "comparison": comparison,  # -1, 0, or 1
                "equal": comparison == 0,
                "a_greater": comparison > 0,
                "b_greater": comparison < 0,
            }
        except Exception as e:
            raise ValueError(f"Comparison failed: {str(e)}")

    async def _shift(
        self,
        sequence: str,
        direction: str,
        positions: int,
    ) -> Dict[str, Any]:
        """Bit shift a DNA sequence."""
        try:
            sequence = sequence.upper().strip()

            if not all(c in "ATCG" for c in sequence):
                raise ValueError("Invalid DNA sequence: contains non-ATCG characters")

            if direction == "left":
                result = self._compute.shift_left(sequence, positions)
            elif direction == "right":
                result = self._compute.shift_right(sequence, positions)
            else:
                raise ValueError(f"Unknown direction: {direction}")

            return {
                "original": sequence,
                "direction": direction,
                "positions": positions,
                "result": result,
            }
        except Exception as e:
            raise ValueError(f"Shift operation failed: {str(e)}")

    async def _evaluate_expression(
        self,
        expression: str,
        variables: Dict[str, str],
    ) -> Dict[str, Any]:
        """Evaluate a compound expression."""
        try:
            # Normalize variables
            normalized_vars = {
                k: v.upper().strip()
                for k, v in variables.items()
            }

            # Parse and evaluate expression
            result = self._evaluate_expr_recursive(expression, normalized_vars)

            return {
                "expression": expression,
                "variables": variables,
                "result": result,
            }
        except Exception as e:
            raise ValueError(f"Expression evaluation failed: {str(e)}")

    def _evaluate_expr_recursive(
        self,
        expr: str,
        variables: Dict[str, str],
    ) -> str:
        """Recursively evaluate expression."""
        expr = expr.strip()

        # Handle parentheses
        while "(" in expr:
            # Find innermost parentheses
            start = expr.rfind("(")
            end = expr.find(")", start)
            if end == -1:
                raise ValueError("Mismatched parentheses")

            inner = expr[start + 1:end]
            inner_result = self._evaluate_expr_recursive(inner, variables)

            # Replace with temporary variable
            temp_var = f"_TEMP_{len(variables)}"
            variables[temp_var] = inner_result
            expr = expr[:start] + temp_var + expr[end + 1:]

        # Split by operators (in order of precedence)
        for op in ["XOR", "XNOR", "OR", "NOR", "AND", "NAND"]:
            if f" {op} " in expr:
                parts = expr.split(f" {op} ", 1)
                left = self._evaluate_expr_recursive(parts[0], variables)
                right = self._evaluate_expr_recursive(parts[1], variables)

                gate_map = {
                    "AND": DNALogicGate.AND,
                    "OR": DNALogicGate.OR,
                    "XOR": DNALogicGate.XOR,
                    "NAND": DNALogicGate.NAND,
                    "NOR": DNALogicGate.NOR,
                    "XNOR": DNALogicGate.XNOR,
                }
                return self._compute.apply_gate(gate_map[op], left, right)

        # Handle NOT
        if expr.startswith("NOT "):
            operand = self._evaluate_expr_recursive(expr[4:], variables)
            return self._compute.apply_gate(DNALogicGate.NOT, operand)

        # Must be a variable
        if expr in variables:
            return variables[expr]

        # Or a direct sequence
        if all(c in "ATCG" for c in expr):
            return expr

        raise ValueError(f"Unknown operand: {expr}")

    def _get_operations(self) -> Dict[str, Any]:
        """Get available operations."""
        return {
            "logic_gates": [
                {
                    "name": "AND",
                    "description": "Bitwise AND: min of nucleotide values",
                    "arity": 2,
                },
                {
                    "name": "OR",
                    "description": "Bitwise OR: max of nucleotide values",
                    "arity": 2,
                },
                {
                    "name": "XOR",
                    "description": "Bitwise XOR: (a + b) mod 4",
                    "arity": 2,
                },
                {
                    "name": "NOT",
                    "description": "Bitwise NOT: complement (A↔G, T↔C)",
                    "arity": 1,
                },
                {
                    "name": "NAND",
                    "description": "NOT AND",
                    "arity": 2,
                },
                {
                    "name": "NOR",
                    "description": "NOT OR",
                    "arity": 2,
                },
                {
                    "name": "XNOR",
                    "description": "NOT XOR",
                    "arity": 2,
                },
            ],
            "arithmetic": [
                {
                    "name": "add",
                    "description": "Base-4 addition",
                    "returns": ["result", "overflow"],
                },
                {
                    "name": "subtract",
                    "description": "Base-4 subtraction",
                    "returns": ["result", "underflow"],
                },
                {
                    "name": "multiply",
                    "description": "Base-4 multiplication",
                    "returns": ["result"],
                },
                {
                    "name": "divide",
                    "description": "Base-4 division",
                    "returns": ["quotient", "remainder"],
                },
            ],
            "nucleotide_values": {
                "A": 0,
                "T": 1,
                "C": 2,
                "G": 3,
            },
        }
