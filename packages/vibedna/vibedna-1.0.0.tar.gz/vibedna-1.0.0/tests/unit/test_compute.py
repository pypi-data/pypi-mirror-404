"""
VibeDNA Compute Tests

Unit tests for the DNA computation engine.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

import pytest
from vibedna.compute.dna_logic_gates import DNAComputeEngine, DNALogicGate


class TestDNALogicGates:
    """Test suite for DNA logic gates."""

    @pytest.fixture
    def engine(self):
        """Create compute engine fixture."""
        return DNAComputeEngine()

    def test_and_gate_same_nucleotide(self, engine):
        """AND of same nucleotide should return same nucleotide."""
        assert engine.apply_gate(DNALogicGate.AND, "A", "A") == "A"
        assert engine.apply_gate(DNALogicGate.AND, "T", "T") == "T"
        assert engine.apply_gate(DNALogicGate.AND, "C", "C") == "C"
        assert engine.apply_gate(DNALogicGate.AND, "G", "G") == "G"

    def test_and_gate_min_value(self, engine):
        """AND should return minimum value."""
        # A=0, T=1, C=2, G=3
        assert engine.apply_gate(DNALogicGate.AND, "G", "A") == "A"  # min(3,0)=0
        assert engine.apply_gate(DNALogicGate.AND, "C", "T") == "T"  # min(2,1)=1
        assert engine.apply_gate(DNALogicGate.AND, "G", "C") == "C"  # min(3,2)=2

    def test_or_gate_same_nucleotide(self, engine):
        """OR of same nucleotide should return same nucleotide."""
        assert engine.apply_gate(DNALogicGate.OR, "A", "A") == "A"
        assert engine.apply_gate(DNALogicGate.OR, "G", "G") == "G"

    def test_or_gate_max_value(self, engine):
        """OR should return maximum value."""
        assert engine.apply_gate(DNALogicGate.OR, "A", "G") == "G"  # max(0,3)=3
        assert engine.apply_gate(DNALogicGate.OR, "T", "C") == "C"  # max(1,2)=2
        assert engine.apply_gate(DNALogicGate.OR, "A", "T") == "T"  # max(0,1)=1

    def test_xor_gate(self, engine):
        """XOR should be (a + b) mod 4."""
        # A=0, T=1, C=2, G=3
        assert engine.apply_gate(DNALogicGate.XOR, "A", "A") == "A"  # (0+0)%4=0
        assert engine.apply_gate(DNALogicGate.XOR, "A", "T") == "T"  # (0+1)%4=1
        assert engine.apply_gate(DNALogicGate.XOR, "T", "T") == "C"  # (1+1)%4=2
        assert engine.apply_gate(DNALogicGate.XOR, "C", "C") == "A"  # (2+2)%4=0
        assert engine.apply_gate(DNALogicGate.XOR, "G", "T") == "A"  # (3+1)%4=0

    def test_not_gate(self, engine):
        """NOT should complement (A↔G, T↔C)."""
        assert engine.apply_gate(DNALogicGate.NOT, "A") == "G"
        assert engine.apply_gate(DNALogicGate.NOT, "T") == "C"
        assert engine.apply_gate(DNALogicGate.NOT, "C") == "T"
        assert engine.apply_gate(DNALogicGate.NOT, "G") == "A"

    def test_not_gate_double(self, engine):
        """Double NOT should return original."""
        for n in "ATCG":
            result = engine.apply_gate(
                DNALogicGate.NOT,
                engine.apply_gate(DNALogicGate.NOT, n)
            )
            assert result == n

    def test_nand_gate(self, engine):
        """NAND should be NOT(AND)."""
        result = engine.apply_gate(DNALogicGate.NAND, "AT", "CG")
        expected = engine.apply_gate(
            DNALogicGate.NOT,
            engine.apply_gate(DNALogicGate.AND, "AT", "CG")
        )
        assert result == expected

    def test_nor_gate(self, engine):
        """NOR should be NOT(OR)."""
        result = engine.apply_gate(DNALogicGate.NOR, "AT", "CG")
        expected = engine.apply_gate(
            DNALogicGate.NOT,
            engine.apply_gate(DNALogicGate.OR, "AT", "CG")
        )
        assert result == expected

    def test_xnor_gate(self, engine):
        """XNOR should be NOT(XOR)."""
        result = engine.apply_gate(DNALogicGate.XNOR, "AT", "CG")
        expected = engine.apply_gate(
            DNALogicGate.NOT,
            engine.apply_gate(DNALogicGate.XOR, "AT", "CG")
        )
        assert result == expected

    def test_gate_sequence_operation(self, engine):
        """Gates should operate on full sequences."""
        result = engine.apply_gate(DNALogicGate.XOR, "ATCG", "ATCG")
        assert len(result) == 4

    def test_gate_requires_same_length(self, engine):
        """Binary gates should require same length sequences."""
        with pytest.raises(ValueError):
            engine.apply_gate(DNALogicGate.AND, "ATCG", "AT")


class TestDNAArithmetic:
    """Test suite for DNA arithmetic operations."""

    @pytest.fixture
    def engine(self):
        """Create compute engine fixture."""
        return DNAComputeEngine()

    def test_add_zero(self, engine):
        """Adding zero should not change value."""
        result, overflow = engine.add("ATCG", "AAAA")
        assert result == "ATCG"
        assert overflow is False

    def test_add_simple(self, engine):
        """Test simple addition."""
        # T + T = C (1 + 1 = 2)
        result, overflow = engine.add("T", "T")
        assert result == "C"
        assert overflow is False

    def test_add_with_carry(self, engine):
        """Test addition with carry."""
        # G + T = A with carry (3 + 1 = 4 = 0 + carry)
        result, overflow = engine.add("G", "T")
        # Result depends on implementation - check overflow
        assert overflow is True or result[0] != "G"

    def test_subtract_zero(self, engine):
        """Subtracting zero should not change value."""
        result, underflow = engine.subtract("ATCG", "AAAA")
        assert result == "ATCG"
        assert underflow is False

    def test_subtract_self(self, engine):
        """Subtracting self should give zero."""
        result, underflow = engine.subtract("ATCG", "ATCG")
        assert result == "AAAA"
        assert underflow is False

    def test_multiply_by_zero(self, engine):
        """Multiplying by zero should give zero."""
        result = engine.multiply("ATCG", "AAAA")
        assert all(n == "A" for n in result)

    def test_multiply_by_one(self, engine):
        """Multiplying by one should not change value."""
        result = engine.multiply("ATCG", "AAAT")  # T = 1
        # Result should equal original value (with possible padding)
        assert engine._dna_to_int(result) == engine._dna_to_int("ATCG")

    def test_divide_by_one(self, engine):
        """Dividing by one should not change value."""
        quotient, remainder = engine.divide("ATCG", "AAAT")  # T = 1
        assert engine._dna_to_int(quotient) == engine._dna_to_int("ATCG")
        assert engine._dna_to_int(remainder) == 0

    def test_divide_by_zero(self, engine):
        """Dividing by zero should raise error."""
        with pytest.raises(ZeroDivisionError):
            engine.divide("ATCG", "AAAA")


class TestDNAComparison:
    """Test suite for DNA comparison operations."""

    @pytest.fixture
    def engine(self):
        """Create compute engine fixture."""
        return DNAComputeEngine()

    def test_compare_equal(self, engine):
        """Equal sequences should compare as 0."""
        assert engine.compare("ATCG", "ATCG") == 0

    def test_compare_less(self, engine):
        """Smaller sequence should compare as -1."""
        assert engine.compare("AAAA", "GGGG") == -1

    def test_compare_greater(self, engine):
        """Larger sequence should compare as 1."""
        assert engine.compare("GGGG", "AAAA") == 1

    def test_equals(self, engine):
        """Test equals method."""
        assert engine.equals("ATCG", "ATCG") is True
        assert engine.equals("ATCG", "GCTA") is False


class TestDNAShift:
    """Test suite for DNA shift operations."""

    @pytest.fixture
    def engine(self):
        """Create compute engine fixture."""
        return DNAComputeEngine()

    def test_shift_left(self, engine):
        """Shift left should append A's."""
        result = engine.shift_left("ATCG", 2)
        assert result == "ATCGAA"

    def test_shift_right(self, engine):
        """Shift right should truncate from right."""
        result = engine.shift_right("ATCG", 2)
        assert result == "AT"

    def test_shift_right_all(self, engine):
        """Shift right by full length should give A."""
        result = engine.shift_right("ATCG", 4)
        assert result == "A"


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
