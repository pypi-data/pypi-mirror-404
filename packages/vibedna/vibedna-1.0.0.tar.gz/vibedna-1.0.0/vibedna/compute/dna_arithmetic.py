"""
VibeDNA Arithmetic - Advanced DNA-Based Arithmetic Operations

Extended arithmetic operations for DNA-encoded numerical data.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Tuple, List
from decimal import Decimal, getcontext

from vibedna.utils.constants import NUCLEOTIDE_VALUE, VALUE_NUCLEOTIDE


class DNAArithmetic:
    """
    Advanced arithmetic operations on DNA sequences.

    Extends basic operations with:
    - Arbitrary precision arithmetic
    - Floating-point representation
    - Power and root operations
    - Modular arithmetic

    Example:
        >>> arith = DNAArithmetic()
        >>> result = arith.power("TC", 3)  # 2^3 = 8
        >>> print(result)
        AACT  # 8 in quaternary
    """

    # Base for DNA arithmetic (4 nucleotides)
    BASE = 4

    def __init__(self, precision: int = 50):
        """
        Initialize DNA arithmetic.

        Args:
            precision: Decimal precision for calculations
        """
        self.precision = precision
        getcontext().prec = precision

    def add(self, seq_a: str, seq_b: str) -> str:
        """
        Add two DNA numbers.

        Args:
            seq_a: First operand
            seq_b: Second operand

        Returns:
            Sum as DNA sequence
        """
        val_a = self._to_int(seq_a)
        val_b = self._to_int(seq_b)
        return self._from_int(val_a + val_b)

    def subtract(self, seq_a: str, seq_b: str) -> str:
        """
        Subtract seq_b from seq_a.

        Args:
            seq_a: Minuend
            seq_b: Subtrahend

        Returns:
            Difference as DNA sequence
        """
        val_a = self._to_int(seq_a)
        val_b = self._to_int(seq_b)

        if val_b > val_a:
            # Return negative representation (two's complement)
            result = val_b - val_a
            # Negate in quaternary
            return self._negate(self._from_int(result))

        return self._from_int(val_a - val_b)

    def multiply(self, seq_a: str, seq_b: str) -> str:
        """
        Multiply two DNA numbers.

        Args:
            seq_a: First factor
            seq_b: Second factor

        Returns:
            Product as DNA sequence
        """
        val_a = self._to_int(seq_a)
        val_b = self._to_int(seq_b)
        return self._from_int(val_a * val_b)

    def divide(self, seq_a: str, seq_b: str) -> Tuple[str, str]:
        """
        Integer division with remainder.

        Args:
            seq_a: Dividend
            seq_b: Divisor

        Returns:
            Tuple of (quotient, remainder)

        Raises:
            ZeroDivisionError: If divisor is zero
        """
        val_a = self._to_int(seq_a)
        val_b = self._to_int(seq_b)

        if val_b == 0:
            raise ZeroDivisionError("Division by zero")

        quotient = val_a // val_b
        remainder = val_a % val_b

        return self._from_int(quotient), self._from_int(remainder)

    def power(self, base: str, exponent: int) -> str:
        """
        Raise DNA number to integer power.

        Args:
            base: Base as DNA sequence
            exponent: Integer exponent

        Returns:
            Result as DNA sequence
        """
        val_base = self._to_int(base)
        result = val_base ** exponent
        return self._from_int(result)

    def sqrt(self, sequence: str) -> str:
        """
        Integer square root.

        Args:
            sequence: DNA number

        Returns:
            Floor of square root as DNA sequence
        """
        val = self._to_int(sequence)
        result = int(val ** 0.5)
        return self._from_int(result)

    def modulo(self, seq_a: str, seq_b: str) -> str:
        """
        Modulo operation.

        Args:
            seq_a: Dividend
            seq_b: Modulus

        Returns:
            Remainder as DNA sequence
        """
        val_a = self._to_int(seq_a)
        val_b = self._to_int(seq_b)

        if val_b == 0:
            raise ZeroDivisionError("Modulo by zero")

        return self._from_int(val_a % val_b)

    def gcd(self, seq_a: str, seq_b: str) -> str:
        """
        Greatest common divisor.

        Args:
            seq_a: First number
            seq_b: Second number

        Returns:
            GCD as DNA sequence
        """
        val_a = self._to_int(seq_a)
        val_b = self._to_int(seq_b)

        while val_b:
            val_a, val_b = val_b, val_a % val_b

        return self._from_int(val_a)

    def lcm(self, seq_a: str, seq_b: str) -> str:
        """
        Least common multiple.

        Args:
            seq_a: First number
            seq_b: Second number

        Returns:
            LCM as DNA sequence
        """
        val_a = self._to_int(seq_a)
        val_b = self._to_int(seq_b)

        gcd_val = self._to_int(self.gcd(seq_a, seq_b))

        if gcd_val == 0:
            return "A"

        return self._from_int((val_a * val_b) // gcd_val)

    def factorial(self, sequence: str) -> str:
        """
        Factorial of DNA number.

        Args:
            sequence: Non-negative integer as DNA

        Returns:
            Factorial as DNA sequence
        """
        n = self._to_int(sequence)

        if n < 0:
            raise ValueError("Factorial not defined for negative numbers")

        result = 1
        for i in range(2, n + 1):
            result *= i

        return self._from_int(result)

    def abs(self, sequence: str) -> str:
        """
        Absolute value.

        Args:
            sequence: DNA number

        Returns:
            Absolute value as DNA sequence
        """
        # For unsigned representation, just return as-is
        return sequence.upper()

    def min(self, *sequences: str) -> str:
        """
        Minimum of multiple DNA numbers.

        Args:
            sequences: DNA numbers to compare

        Returns:
            Minimum value as DNA sequence
        """
        if not sequences:
            raise ValueError("No sequences provided")

        min_val = float("inf")
        min_seq = sequences[0]

        for seq in sequences:
            val = self._to_int(seq)
            if val < min_val:
                min_val = val
                min_seq = seq

        return min_seq.upper()

    def max(self, *sequences: str) -> str:
        """
        Maximum of multiple DNA numbers.

        Args:
            sequences: DNA numbers to compare

        Returns:
            Maximum value as DNA sequence
        """
        if not sequences:
            raise ValueError("No sequences provided")

        max_val = -1
        max_seq = sequences[0]

        for seq in sequences:
            val = self._to_int(seq)
            if val > max_val:
                max_val = val
                max_seq = seq

        return max_seq.upper()

    # ═══════════════════════════════════════════════════════════════
    # Fixed-Point Arithmetic
    # ═══════════════════════════════════════════════════════════════

    def fixed_add(
        self,
        seq_a: str,
        seq_b: str,
        decimal_places: int
    ) -> str:
        """
        Add fixed-point DNA numbers.

        Args:
            seq_a: First number
            seq_b: Second number
            decimal_places: Position of decimal point from right

        Returns:
            Sum as DNA sequence
        """
        # Fixed-point is just integer arithmetic with implicit scaling
        return self.add(seq_a, seq_b)

    def fixed_multiply(
        self,
        seq_a: str,
        seq_b: str,
        decimal_places: int
    ) -> str:
        """
        Multiply fixed-point DNA numbers.

        Args:
            seq_a: First number
            seq_b: Second number
            decimal_places: Position of decimal point

        Returns:
            Product as DNA sequence
        """
        val_a = self._to_int(seq_a)
        val_b = self._to_int(seq_b)

        # Multiply and shift back
        result = (val_a * val_b) // (self.BASE ** decimal_places)
        return self._from_int(result)

    def fixed_divide(
        self,
        seq_a: str,
        seq_b: str,
        decimal_places: int
    ) -> str:
        """
        Divide fixed-point DNA numbers.

        Args:
            seq_a: Dividend
            seq_b: Divisor
            decimal_places: Position of decimal point

        Returns:
            Quotient as DNA sequence
        """
        val_a = self._to_int(seq_a)
        val_b = self._to_int(seq_b)

        if val_b == 0:
            raise ZeroDivisionError("Division by zero")

        # Scale up before division to maintain precision
        result = (val_a * (self.BASE ** decimal_places)) // val_b
        return self._from_int(result)

    # ═══════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════

    def _to_int(self, sequence: str) -> int:
        """Convert DNA sequence to integer."""
        sequence = sequence.upper()
        result = 0
        for nucleotide in sequence:
            if nucleotide in NUCLEOTIDE_VALUE:
                result = result * self.BASE + NUCLEOTIDE_VALUE[nucleotide]
        return result

    def _from_int(self, value: int, min_length: int = 1) -> str:
        """Convert integer to DNA sequence."""
        if value == 0:
            return "A" * min_length

        result = []
        while value > 0:
            result.append(VALUE_NUCLEOTIDE[value % self.BASE])
            value //= self.BASE

        result.reverse()

        if len(result) < min_length:
            result = ["A"] * (min_length - len(result)) + result

        return "".join(result)

    def _negate(self, sequence: str) -> str:
        """Negate a DNA number (quaternary complement + 1)."""
        # Complement each nucleotide
        complement = {"A": "G", "T": "C", "C": "T", "G": "A"}
        complemented = "".join(complement[n] for n in sequence.upper())

        # Add 1
        return self.add(complemented, "T")


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
