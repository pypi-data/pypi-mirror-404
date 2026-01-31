"""
VibeDNA Error Correction Tests

Unit tests for the error correction modules.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

import pytest
from vibedna.error_correction.reed_solomon_dna import DNAReedSolomon, GF4
from vibedna.error_correction.hamming_dna import DNAHamming
from vibedna.error_correction.checksum_generator import ChecksumGenerator, ChecksumAlgorithm


class TestGF4:
    """Test suite for GF(4) arithmetic."""

    def test_add_identity(self):
        """Adding 0 should not change value."""
        for a in range(4):
            assert GF4.add(a, 0) == a

    def test_add_self_is_zero(self):
        """Adding element to itself gives 0 in GF(4)."""
        for a in range(4):
            assert GF4.add(a, a) == 0

    def test_mul_identity(self):
        """Multiplying by 1 should not change value."""
        for a in range(4):
            assert GF4.mul(a, 1) == a

    def test_mul_zero(self):
        """Multiplying by 0 should give 0."""
        for a in range(4):
            assert GF4.mul(a, 0) == 0

    def test_inverse(self):
        """Multiplying by inverse should give 1."""
        for a in range(1, 4):  # Skip 0
            inv = GF4.INV_TABLE[a]
            assert GF4.mul(a, inv) == 1


class TestDNAReedSolomon:
    """Test suite for Reed-Solomon error correction."""

    def test_encode_decode_no_errors(self):
        """Test encoding and decoding with no errors."""
        rs = DNAReedSolomon(nsym=8)

        original = "ATCGATCGATCGATCG"
        encoded = rs.encode(original)
        result = rs.decode(encoded)

        assert result.corrected_sequence == original
        assert result.errors_detected == 0
        assert result.errors_corrected == 0
        assert result.uncorrectable is False

    def test_encode_increases_length(self):
        """Encoding should add parity symbols."""
        rs = DNAReedSolomon(nsym=8)

        original = "ATCGATCG"
        encoded = rs.encode(original)

        assert len(encoded) == len(original) + 8

    def test_single_error_correction(self):
        """Single error should be corrected."""
        rs = DNAReedSolomon(nsym=8)

        original = "ATCGATCGATCGATCG"
        encoded = rs.encode(original)

        # Introduce single error
        corrupted = encoded[0] + "A" + encoded[2:]  # Change position 1

        result = rs.decode(corrupted)

        assert result.errors_detected >= 1
        assert result.uncorrectable is False

    def test_multiple_errors_within_limit(self):
        """Multiple errors within limit should be corrected."""
        rs = DNAReedSolomon(nsym=16)  # Can correct up to 8 errors

        original = "ATCGATCGATCGATCGATCGATCGATCGATCG"
        encoded = rs.encode(original)

        # Introduce 4 errors (within limit)
        corrupted = list(encoded)
        corrupted[0] = "G" if corrupted[0] != "G" else "A"
        corrupted[5] = "G" if corrupted[5] != "G" else "A"
        corrupted[10] = "G" if corrupted[10] != "G" else "A"
        corrupted[15] = "G" if corrupted[15] != "G" else "A"
        corrupted = "".join(corrupted)

        result = rs.decode(corrupted)

        # Should detect errors
        assert result.errors_detected >= 1


class TestDNAHamming:
    """Test suite for Hamming code error correction."""

    def test_encode_decode_no_errors(self):
        """Test encoding and decoding with no errors."""
        hamming = DNAHamming()

        original = "ATCG"
        encoded = hamming.encode(original)
        result = hamming.decode(encoded)

        assert result.errors_detected == 0
        assert result.is_valid is True

    def test_encode_increases_length(self):
        """Encoding should add parity bits."""
        hamming = DNAHamming()

        original = "ATCG"
        encoded = hamming.encode(original)

        # Hamming(7,4) adds 3 parity bits per 4 data bits
        # Plus SECDED adds 1 more
        assert len(encoded) > len(original)


class TestChecksumGenerator:
    """Test suite for checksum generation."""

    def test_crc8_deterministic(self):
        """CRC8 should be deterministic."""
        gen = ChecksumGenerator(ChecksumAlgorithm.CRC8)

        checksum1 = gen.compute("ATCGATCG")
        checksum2 = gen.compute("ATCGATCG")

        assert checksum1 == checksum2

    def test_crc8_different_inputs(self):
        """Different inputs should produce different checksums."""
        gen = ChecksumGenerator(ChecksumAlgorithm.CRC8)

        checksum1 = gen.compute("ATCGATCG")
        checksum2 = gen.compute("GCTAGCTA")

        assert checksum1 != checksum2

    def test_verify_correct(self):
        """Verify should return True for correct checksum."""
        gen = ChecksumGenerator(ChecksumAlgorithm.CRC8)

        sequence = "ATCGATCG"
        checksum = gen.compute(sequence)

        assert gen.verify(sequence, checksum) is True

    def test_verify_incorrect(self):
        """Verify should return False for incorrect checksum."""
        gen = ChecksumGenerator(ChecksumAlgorithm.CRC8)

        sequence = "ATCGATCG"
        wrong_checksum = "AAAA"

        assert gen.verify(sequence, wrong_checksum) is False

    def test_compute_and_append(self):
        """Test compute and append functionality."""
        gen = ChecksumGenerator(ChecksumAlgorithm.CRC8)

        sequence = "ATCGATCG"
        result = gen.compute_and_append(sequence)

        assert result.startswith(sequence)
        assert len(result) > len(sequence)

    def test_sha256_produces_valid_dna(self):
        """SHA256 checksum should produce valid DNA."""
        gen = ChecksumGenerator(ChecksumAlgorithm.SHA256_DNA)

        checksum = gen.compute("ATCGATCG", length=16)

        assert all(n in "ATCG" for n in checksum)
        assert len(checksum) == 16


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
