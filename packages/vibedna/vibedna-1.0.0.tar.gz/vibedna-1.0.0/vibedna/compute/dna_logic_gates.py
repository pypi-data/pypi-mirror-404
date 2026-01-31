"""
VibeDNA Logic Gates - DNA-Based Logical Operations

Implements logical operations on DNA-encoded data,
enabling computation directly on DNA sequences.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Tuple, Callable, Dict, Optional
from enum import Enum
import re

from vibedna.utils.constants import NUCLEOTIDE_VALUE, VALUE_NUCLEOTIDE, NUCLEOTIDE_COMPLEMENT


class DNALogicGate(Enum):
    """Available DNA logic gate operations."""
    AND = "and"
    OR = "or"
    XOR = "xor"
    NOT = "not"
    NAND = "nand"
    NOR = "nor"
    XNOR = "xnor"


class DNAComputeEngine:
    """
    Perform logical and arithmetic operations on DNA sequences.

    Implements a complete set of logic gates and arithmetic
    operations that work directly on DNA-encoded data without
    requiring decode-compute-encode cycles.

    DNA Logic Gate Definitions:
    - AND: min(nucleotide values) - keeps lower value
    - OR: max(nucleotide values) - keeps higher value
    - XOR: (a + b) mod 4 - addition modulo 4
    - NOT: complement (A↔G, T↔C) - inverts bits

    Example:
        >>> engine = DNAComputeEngine()
        >>> result = engine.apply_gate(DNALogicGate.XOR, "ATCG", "GCTA")
        >>> print(result)
        CAGT
    """

    # Nucleotide ordering: A=0 < T=1 < C=2 < G=3
    NUCLEOTIDE_ORDER = NUCLEOTIDE_VALUE
    ORDER_NUCLEOTIDE = VALUE_NUCLEOTIDE

    def __init__(self):
        """Initialize the compute engine."""
        self._gate_implementations: Dict[DNALogicGate, Callable] = {
            DNALogicGate.AND: self._dna_and,
            DNALogicGate.OR: self._dna_or,
            DNALogicGate.XOR: self._dna_xor,
            DNALogicGate.NOT: self._dna_not,
            DNALogicGate.NAND: self._dna_nand,
            DNALogicGate.NOR: self._dna_nor,
            DNALogicGate.XNOR: self._dna_xnor,
        }

    # ═══════════════════════════════════════════════════════════════
    # Logic Gates
    # ═══════════════════════════════════════════════════════════════

    def apply_gate(
        self,
        gate: DNALogicGate,
        seq_a: str,
        seq_b: Optional[str] = None
    ) -> str:
        """
        Apply a logic gate to DNA sequence(s).

        Args:
            gate: The logic gate to apply
            seq_a: First DNA sequence
            seq_b: Second DNA sequence (not needed for NOT)

        Returns:
            Resulting DNA sequence

        Raises:
            ValueError: If sequences have different lengths or are invalid
        """
        seq_a = seq_a.upper()

        if gate == DNALogicGate.NOT:
            return self._gate_implementations[gate](seq_a, None)

        if seq_b is None:
            raise ValueError(f"Gate {gate.value} requires two sequences")

        seq_b = seq_b.upper()

        if len(seq_a) != len(seq_b):
            raise ValueError(
                f"Sequences must have same length: {len(seq_a)} vs {len(seq_b)}"
            )

        return self._gate_implementations[gate](seq_a, seq_b)

    def _dna_and(self, a: str, b: str) -> str:
        """
        DNA AND: min(nucleotide values).

        Returns the nucleotide with lower value at each position.
        This corresponds to bitwise AND on the 2-bit representations.
        """
        result = []
        for na, nb in zip(a, b):
            va = self.NUCLEOTIDE_ORDER[na]
            vb = self.NUCLEOTIDE_ORDER[nb]
            result.append(self.ORDER_NUCLEOTIDE[min(va, vb)])
        return "".join(result)

    def _dna_or(self, a: str, b: str) -> str:
        """
        DNA OR: max(nucleotide values).

        Returns the nucleotide with higher value at each position.
        This corresponds to bitwise OR on the 2-bit representations.
        """
        result = []
        for na, nb in zip(a, b):
            va = self.NUCLEOTIDE_ORDER[na]
            vb = self.NUCLEOTIDE_ORDER[nb]
            result.append(self.ORDER_NUCLEOTIDE[max(va, vb)])
        return "".join(result)

    def _dna_xor(self, a: str, b: str) -> str:
        """
        DNA XOR: (a + b) mod 4.

        Addition of nucleotide values modulo 4.
        This corresponds to bitwise XOR on the 2-bit representations.
        """
        result = []
        for na, nb in zip(a, b):
            va = self.NUCLEOTIDE_ORDER[na]
            vb = self.NUCLEOTIDE_ORDER[nb]
            result.append(self.ORDER_NUCLEOTIDE[(va + vb) % 4])
        return "".join(result)

    def _dna_not(self, a: str, b: Optional[str] = None) -> str:
        """
        DNA NOT: complement (A↔G, T↔C).

        Inverts each nucleotide: A→G, T→C, C→T, G→A
        This corresponds to bitwise NOT on the 2-bit representations.
        """
        result = []
        for na in a:
            result.append(NUCLEOTIDE_COMPLEMENT[na])
        return "".join(result)

    def _dna_nand(self, a: str, b: str) -> str:
        """DNA NAND: NOT(AND)."""
        return self._dna_not(self._dna_and(a, b))

    def _dna_nor(self, a: str, b: str) -> str:
        """DNA NOR: NOT(OR)."""
        return self._dna_not(self._dna_or(a, b))

    def _dna_xnor(self, a: str, b: str) -> str:
        """DNA XNOR: NOT(XOR)."""
        return self._dna_not(self._dna_xor(a, b))

    # ═══════════════════════════════════════════════════════════════
    # Arithmetic Operations
    # ═══════════════════════════════════════════════════════════════

    def add(self, seq_a: str, seq_b: str) -> Tuple[str, bool]:
        """
        Add two DNA-encoded numbers.

        Performs quaternary (base-4) addition.

        Args:
            seq_a: First DNA sequence (number)
            seq_b: Second DNA sequence (number)

        Returns:
            Tuple of (result_sequence, overflow_flag)
        """
        seq_a = seq_a.upper()
        seq_b = seq_b.upper()

        # Pad shorter sequence with 'A' (zero)
        max_len = max(len(seq_a), len(seq_b))
        seq_a = seq_a.zfill(max_len).replace("0", "A")[-max_len:]
        seq_b = seq_b.zfill(max_len).replace("0", "A")[-max_len:]

        # Pad with A's
        seq_a = "A" * (max_len - len(seq_a)) + seq_a
        seq_b = "A" * (max_len - len(seq_b)) + seq_b

        result = []
        carry = 0

        # Add from right to left (least significant first)
        for i in range(max_len - 1, -1, -1):
            va = self.NUCLEOTIDE_ORDER[seq_a[i]]
            vb = self.NUCLEOTIDE_ORDER[seq_b[i]]

            total = va + vb + carry
            carry = total // 4
            result.append(self.ORDER_NUCLEOTIDE[total % 4])

        result.reverse()
        return "".join(result), carry > 0

    def subtract(self, seq_a: str, seq_b: str) -> Tuple[str, bool]:
        """
        Subtract seq_b from seq_a.

        Performs quaternary (base-4) subtraction.

        Args:
            seq_a: Minuend DNA sequence
            seq_b: Subtrahend DNA sequence

        Returns:
            Tuple of (result_sequence, underflow_flag)
        """
        seq_a = seq_a.upper()
        seq_b = seq_b.upper()

        max_len = max(len(seq_a), len(seq_b))
        seq_a = "A" * (max_len - len(seq_a)) + seq_a
        seq_b = "A" * (max_len - len(seq_b)) + seq_b

        result = []
        borrow = 0

        for i in range(max_len - 1, -1, -1):
            va = self.NUCLEOTIDE_ORDER[seq_a[i]]
            vb = self.NUCLEOTIDE_ORDER[seq_b[i]]

            diff = va - vb - borrow
            if diff < 0:
                diff += 4
                borrow = 1
            else:
                borrow = 0

            result.append(self.ORDER_NUCLEOTIDE[diff])

        result.reverse()
        return "".join(result), borrow > 0

    def multiply(self, seq_a: str, seq_b: str) -> str:
        """
        Multiply two DNA-encoded numbers.

        Performs quaternary multiplication using shift-and-add.

        Args:
            seq_a: First DNA sequence (number)
            seq_b: Second DNA sequence (number)

        Returns:
            Product as DNA sequence
        """
        seq_a = seq_a.upper()
        seq_b = seq_b.upper()

        # Convert to integers for multiplication
        val_a = self._dna_to_int(seq_a)
        val_b = self._dna_to_int(seq_b)

        product = val_a * val_b
        return self._int_to_dna(product, len(seq_a) + len(seq_b))

    def divide(self, seq_a: str, seq_b: str) -> Tuple[str, str]:
        """
        Divide seq_a by seq_b.

        Args:
            seq_a: Dividend DNA sequence
            seq_b: Divisor DNA sequence

        Returns:
            Tuple of (quotient_sequence, remainder_sequence)

        Raises:
            ZeroDivisionError: If divisor is zero (all A's)
        """
        seq_a = seq_a.upper()
        seq_b = seq_b.upper()

        val_a = self._dna_to_int(seq_a)
        val_b = self._dna_to_int(seq_b)

        if val_b == 0:
            raise ZeroDivisionError("Division by zero (all A's)")

        quotient = val_a // val_b
        remainder = val_a % val_b

        return (
            self._int_to_dna(quotient, len(seq_a)),
            self._int_to_dna(remainder, len(seq_b))
        )

    # ═══════════════════════════════════════════════════════════════
    # Comparison Operations
    # ═══════════════════════════════════════════════════════════════

    def compare(self, seq_a: str, seq_b: str) -> int:
        """
        Compare two DNA sequences numerically.

        Args:
            seq_a: First DNA sequence
            seq_b: Second DNA sequence

        Returns:
            -1 if a < b, 0 if a == b, 1 if a > b
        """
        seq_a = seq_a.upper()
        seq_b = seq_b.upper()

        val_a = self._dna_to_int(seq_a)
        val_b = self._dna_to_int(seq_b)

        if val_a < val_b:
            return -1
        elif val_a > val_b:
            return 1
        return 0

    def equals(self, seq_a: str, seq_b: str) -> bool:
        """Check if two sequences represent the same value."""
        return self.compare(seq_a, seq_b) == 0

    def less_than(self, seq_a: str, seq_b: str) -> bool:
        """Check if seq_a < seq_b."""
        return self.compare(seq_a, seq_b) < 0

    def greater_than(self, seq_a: str, seq_b: str) -> bool:
        """Check if seq_a > seq_b."""
        return self.compare(seq_a, seq_b) > 0

    # ═══════════════════════════════════════════════════════════════
    # Bitwise Shift Operations
    # ═══════════════════════════════════════════════════════════════

    def shift_left(self, sequence: str, positions: int) -> str:
        """
        Shift DNA sequence left (multiply by 4^positions).

        Args:
            sequence: DNA sequence to shift
            positions: Number of positions to shift

        Returns:
            Shifted sequence (with A's appended)
        """
        sequence = sequence.upper()
        return sequence + "A" * positions

    def shift_right(self, sequence: str, positions: int) -> str:
        """
        Shift DNA sequence right (divide by 4^positions).

        Args:
            sequence: DNA sequence to shift
            positions: Number of positions to shift

        Returns:
            Shifted sequence (truncated from right)
        """
        sequence = sequence.upper()
        if positions >= len(sequence):
            return "A"
        return sequence[:-positions] if positions > 0 else sequence

    def rotate_left(self, sequence: str, positions: int) -> str:
        """
        Rotate DNA sequence left.

        Args:
            sequence: DNA sequence to rotate
            positions: Number of positions to rotate

        Returns:
            Rotated sequence
        """
        sequence = sequence.upper()
        positions = positions % len(sequence)
        return sequence[positions:] + sequence[:positions]

    def rotate_right(self, sequence: str, positions: int) -> str:
        """
        Rotate DNA sequence right.

        Args:
            sequence: DNA sequence to rotate
            positions: Number of positions to rotate

        Returns:
            Rotated sequence
        """
        sequence = sequence.upper()
        positions = positions % len(sequence)
        return sequence[-positions:] + sequence[:-positions]

    # ═══════════════════════════════════════════════════════════════
    # Compound Operations
    # ═══════════════════════════════════════════════════════════════

    def execute_expression(
        self,
        expression: str,
        variables: Dict[str, str]
    ) -> str:
        """
        Execute a compound expression on DNA sequences.

        Supported syntax:
        - Variables: A, B, C, etc.
        - Gates: AND, OR, XOR, NOT, NAND, NOR, XNOR
        - Parentheses for grouping

        Example:
            >>> result = engine.execute_expression(
            ...     "(A AND B) XOR C",
            ...     {"A": "ATCG", "B": "GCTA", "C": "AATT"}
            ... )

        Args:
            expression: Expression string
            variables: Dictionary mapping variable names to DNA sequences

        Returns:
            Result DNA sequence
        """
        # Tokenize
        tokens = self._tokenize(expression)

        # Parse and evaluate
        result, _ = self._parse_expression(tokens, 0, variables)
        return result

    def _tokenize(self, expression: str) -> list:
        """Tokenize an expression."""
        pattern = r'(\(|\)|AND|OR|XOR|NOT|NAND|NOR|XNOR|[A-Z_][A-Z0-9_]*)'
        tokens = re.findall(pattern, expression.upper())
        return tokens

    def _parse_expression(
        self,
        tokens: list,
        pos: int,
        variables: Dict[str, str]
    ) -> Tuple[str, int]:
        """Parse and evaluate expression recursively."""
        if pos >= len(tokens):
            raise ValueError("Unexpected end of expression")

        # Get first operand
        left, pos = self._parse_operand(tokens, pos, variables)

        # Check for binary operator
        while pos < len(tokens) and tokens[pos] in (
            "AND", "OR", "XOR", "NAND", "NOR", "XNOR"
        ):
            op = tokens[pos]
            pos += 1

            right, pos = self._parse_operand(tokens, pos, variables)

            gate = DNALogicGate(op.lower())
            left = self.apply_gate(gate, left, right)

        return left, pos

    def _parse_operand(
        self,
        tokens: list,
        pos: int,
        variables: Dict[str, str]
    ) -> Tuple[str, int]:
        """Parse a single operand."""
        if pos >= len(tokens):
            raise ValueError("Expected operand")

        token = tokens[pos]

        if token == "(":
            # Parenthesized expression
            result, pos = self._parse_expression(tokens, pos + 1, variables)
            if pos >= len(tokens) or tokens[pos] != ")":
                raise ValueError("Missing closing parenthesis")
            return result, pos + 1

        elif token == "NOT":
            # Unary NOT
            operand, pos = self._parse_operand(tokens, pos + 1, variables)
            return self.apply_gate(DNALogicGate.NOT, operand), pos

        elif token in variables:
            # Variable
            return variables[token].upper(), pos + 1

        else:
            raise ValueError(f"Unknown token: {token}")

    # ═══════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════

    def _dna_to_int(self, sequence: str) -> int:
        """Convert DNA sequence to integer."""
        result = 0
        for nucleotide in sequence:
            result = result * 4 + self.NUCLEOTIDE_ORDER[nucleotide]
        return result

    def _int_to_dna(self, value: int, length: int) -> str:
        """Convert integer to DNA sequence of given length."""
        if value == 0:
            return "A" * length

        result = []
        while value > 0:
            result.append(self.ORDER_NUCLEOTIDE[value % 4])
            value //= 4

        result.reverse()

        # Pad or truncate to length
        if len(result) < length:
            result = ["A"] * (length - len(result)) + result
        elif len(result) > length:
            result = result[-length:]

        return "".join(result)


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
