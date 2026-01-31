"""
VibeDNA Checksum Generator

Integrity verification using various checksum algorithms
optimized for DNA sequences.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Union, Tuple
import hashlib
from enum import Enum

from vibedna.utils.constants import NUCLEOTIDE_VALUE, VALUE_NUCLEOTIDE, BIT_TO_NUCLEOTIDE


class ChecksumAlgorithm(Enum):
    """Available checksum algorithms."""
    CRC4 = "crc4"           # 4-nucleotide CRC
    CRC8 = "crc8"           # 8-nucleotide CRC
    SHA256_DNA = "sha256"   # SHA256 encoded as DNA
    SIMPLE_SUM = "sum"      # Simple nucleotide sum


class ChecksumGenerator:
    """
    Generate and verify checksums for DNA sequences.

    Provides multiple algorithms for different use cases:
    - CRC4/CRC8: Fast, good for small blocks
    - SHA256_DNA: Cryptographic, good for important data
    - SIMPLE_SUM: Very fast, basic integrity check

    Example:
        >>> gen = ChecksumGenerator()
        >>> checksum = gen.compute("ATCGATCG")
        >>> gen.verify("ATCGATCG", checksum)
        True
    """

    # CRC-4 polynomial: x^4 + x + 1 = 0x13
    CRC4_POLY = 0x13

    # CRC-8 polynomial: x^8 + x^2 + x + 1 = 0x107
    CRC8_POLY = 0x107

    def __init__(self, algorithm: ChecksumAlgorithm = ChecksumAlgorithm.CRC8):
        """
        Initialize checksum generator.

        Args:
            algorithm: Checksum algorithm to use
        """
        self.algorithm = algorithm
        self._lookup_table = self._build_lookup_table()

    def _build_lookup_table(self) -> list:
        """Build CRC lookup table for faster computation."""
        if self.algorithm == ChecksumAlgorithm.CRC4:
            return self._build_crc_table(4, self.CRC4_POLY)
        elif self.algorithm == ChecksumAlgorithm.CRC8:
            return self._build_crc_table(8, self.CRC8_POLY)
        return []

    def _build_crc_table(self, bits: int, poly: int) -> list:
        """Build CRC lookup table."""
        table = []
        top_bit = 1 << (bits - 1)
        mask = (1 << bits) - 1

        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & top_bit:
                    crc = ((crc << 1) ^ poly) & mask
                else:
                    crc = (crc << 1) & mask
            table.append(crc)

        return table

    def compute(self, sequence: str, length: int = None) -> str:
        """
        Compute checksum for DNA sequence.

        Args:
            sequence: DNA sequence
            length: Optional output length in nucleotides

        Returns:
            Checksum as DNA sequence
        """
        sequence = sequence.upper()

        if self.algorithm == ChecksumAlgorithm.CRC4:
            return self._compute_crc4(sequence)
        elif self.algorithm == ChecksumAlgorithm.CRC8:
            return self._compute_crc8(sequence)
        elif self.algorithm == ChecksumAlgorithm.SHA256_DNA:
            return self._compute_sha256(sequence, length or 16)
        elif self.algorithm == ChecksumAlgorithm.SIMPLE_SUM:
            return self._compute_simple_sum(sequence)
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")

    def verify(self, sequence: str, checksum: str) -> bool:
        """
        Verify checksum against sequence.

        Args:
            sequence: DNA sequence
            checksum: Expected checksum

        Returns:
            True if checksum matches
        """
        computed = self.compute(sequence, len(checksum))
        return computed == checksum.upper()

    def compute_and_append(self, sequence: str) -> str:
        """
        Compute checksum and append to sequence.

        Args:
            sequence: DNA sequence

        Returns:
            Sequence with checksum appended
        """
        checksum = self.compute(sequence)
        return sequence + checksum

    def verify_and_strip(self, sequence: str) -> Tuple[bool, str]:
        """
        Verify checksum and return data without checksum.

        Args:
            sequence: DNA sequence with appended checksum

        Returns:
            Tuple of (is_valid, data_without_checksum)
        """
        # Determine checksum length based on algorithm
        checksum_lengths = {
            ChecksumAlgorithm.CRC4: 2,
            ChecksumAlgorithm.CRC8: 4,
            ChecksumAlgorithm.SHA256_DNA: 16,
            ChecksumAlgorithm.SIMPLE_SUM: 2,
        }

        length = checksum_lengths.get(self.algorithm, 4)

        if len(sequence) < length:
            return False, sequence

        data = sequence[:-length]
        checksum = sequence[-length:]

        is_valid = self.verify(data, checksum)
        return is_valid, data

    def _compute_crc4(self, sequence: str) -> str:
        """Compute CRC-4 checksum."""
        crc = 0

        for nucleotide in sequence:
            value = NUCLEOTIDE_VALUE.get(nucleotide, 0)
            # Process 2 bits at a time (each nucleotide)
            for i in range(1, -1, -1):
                bit = (value >> i) & 1
                if crc & 0x8:
                    crc = ((crc << 1) ^ self.CRC4_POLY) & 0xF
                else:
                    crc = (crc << 1) & 0xF
                crc ^= bit

        # Convert 4-bit CRC to 2 nucleotides
        return VALUE_NUCLEOTIDE[(crc >> 2) & 3] + VALUE_NUCLEOTIDE[crc & 3]

    def _compute_crc8(self, sequence: str) -> str:
        """Compute CRC-8 checksum."""
        crc = 0

        for nucleotide in sequence:
            value = NUCLEOTIDE_VALUE.get(nucleotide, 0)
            # Use lookup table
            crc = self._lookup_table[(crc ^ (value << 6)) & 0xFF]

        # Convert 8-bit CRC to 4 nucleotides
        return (
            VALUE_NUCLEOTIDE[(crc >> 6) & 3] +
            VALUE_NUCLEOTIDE[(crc >> 4) & 3] +
            VALUE_NUCLEOTIDE[(crc >> 2) & 3] +
            VALUE_NUCLEOTIDE[crc & 3]
        )

    def _compute_sha256(self, sequence: str, length: int) -> str:
        """Compute SHA-256 and encode as DNA."""
        # Hash the sequence
        hash_bytes = hashlib.sha256(sequence.encode()).digest()

        # Convert to DNA
        result = []
        for byte in hash_bytes[:length // 2]:
            result.append(VALUE_NUCLEOTIDE[(byte >> 6) & 3])
            result.append(VALUE_NUCLEOTIDE[(byte >> 4) & 3])
            result.append(VALUE_NUCLEOTIDE[(byte >> 2) & 3])
            result.append(VALUE_NUCLEOTIDE[byte & 3])

        return "".join(result)[:length]

    def _compute_simple_sum(self, sequence: str) -> str:
        """Compute simple sum checksum."""
        total = 0
        for nucleotide in sequence:
            total += NUCLEOTIDE_VALUE.get(nucleotide, 0)

        # Reduce to 4 bits
        total = total & 0xF

        # Convert to 2 nucleotides
        return VALUE_NUCLEOTIDE[(total >> 2) & 3] + VALUE_NUCLEOTIDE[total & 3]


def quick_checksum(sequence: str) -> str:
    """
    Quick utility function to compute default checksum.

    Args:
        sequence: DNA sequence

    Returns:
        CRC-8 checksum as DNA
    """
    gen = ChecksumGenerator(ChecksumAlgorithm.CRC8)
    return gen.compute(sequence)


def verify_checksum(sequence: str, checksum: str) -> bool:
    """
    Quick utility function to verify checksum.

    Args:
        sequence: DNA sequence
        checksum: Expected checksum

    Returns:
        True if valid
    """
    gen = ChecksumGenerator(ChecksumAlgorithm.CRC8)
    return gen.verify(sequence, checksum)


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
