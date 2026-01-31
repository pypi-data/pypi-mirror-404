"""
VibeDNA Hamming Code for DNA

Implements Hamming code error correction adapted for DNA sequences.
Provides single-error correction and double-error detection (SECDED).

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Tuple, List, Optional
from dataclasses import dataclass

from vibedna.utils.constants import NUCLEOTIDE_VALUE, VALUE_NUCLEOTIDE


@dataclass
class HammingResult:
    """Result of Hamming code operation."""
    data: str
    errors_detected: int
    errors_corrected: int
    error_position: Optional[int]
    is_valid: bool


class DNAHamming:
    """
    Hamming code implementation for DNA sequences.

    Standard Hamming codes work on binary data. This implementation
    treats each nucleotide as 2 bits and applies Hamming(7,4) encoding
    to groups of 4 data bits (2 nucleotides).

    Features:
    - Single error correction
    - Double error detection (SECDED with extra parity)
    - Low overhead (~75% efficiency for data)

    Example:
        >>> hamming = DNAHamming()
        >>> encoded = hamming.encode("ATCG")
        >>> # Introduce an error
        >>> corrupted = encoded[0] + "A" + encoded[2:]
        >>> result = hamming.decode(corrupted)
        >>> print(result.data)
        ATCG
    """

    # Hamming(7,4) generator matrix (each row is a data bit position)
    # G = [I4 | P] where P is the parity check matrix
    GENERATOR_MATRIX = [
        [1, 0, 0, 0, 1, 1, 0],  # d1
        [0, 1, 0, 0, 1, 0, 1],  # d2
        [0, 0, 1, 0, 0, 1, 1],  # d3
        [0, 0, 0, 1, 1, 1, 1],  # d4
    ]

    # Parity check matrix for syndrome calculation
    # H = [P^T | I3]
    PARITY_CHECK_MATRIX = [
        [1, 1, 0, 1, 1, 0, 0],  # p1
        [1, 0, 1, 1, 0, 1, 0],  # p2
        [0, 1, 1, 1, 0, 0, 1],  # p3
    ]

    def __init__(self, use_secded: bool = True):
        """
        Initialize Hamming codec.

        Args:
            use_secded: If True, adds extra parity for double error detection
        """
        self.use_secded = use_secded

    def encode(self, sequence: str) -> str:
        """
        Encode DNA sequence with Hamming parity.

        Each 2 nucleotides (4 bits) are encoded with 3 parity bits,
        producing approximately 7/4 nucleotides output per input.

        Args:
            sequence: DNA sequence to encode

        Returns:
            Encoded sequence with Hamming parity
        """
        # Convert to binary
        binary = self._dna_to_binary(sequence.upper())

        # Pad to multiple of 4 bits
        while len(binary) % 4 != 0:
            binary += "0"

        # Encode each 4-bit block
        encoded_bits = []
        for i in range(0, len(binary), 4):
            data_bits = [int(b) for b in binary[i:i + 4]]
            code_word = self._encode_block(data_bits)
            encoded_bits.extend(code_word)

        # Convert back to DNA
        return self._binary_to_dna("".join(str(b) for b in encoded_bits))

    def decode(self, sequence: str) -> HammingResult:
        """
        Decode and correct errors in Hamming-encoded sequence.

        Args:
            sequence: Hamming-encoded DNA sequence

        Returns:
            HammingResult with decoded data and error info
        """
        # Convert to binary
        binary = self._dna_to_binary(sequence.upper())

        # Determine block size (7 bits, or 8 with SECDED)
        block_size = 8 if self.use_secded else 7

        # Pad if needed
        while len(binary) % block_size != 0:
            binary += "0"

        # Decode each block
        decoded_bits = []
        total_errors_detected = 0
        total_errors_corrected = 0
        error_positions = []
        is_valid = True

        for i in range(0, len(binary), block_size):
            block = [int(b) for b in binary[i:i + block_size]]
            data, detected, corrected, pos, valid = self._decode_block(block)

            decoded_bits.extend(data)
            total_errors_detected += detected
            total_errors_corrected += corrected
            if pos is not None:
                error_positions.append(i // block_size * 4 + pos)
            is_valid = is_valid and valid

        # Convert back to DNA
        decoded_dna = self._binary_to_dna("".join(str(b) for b in decoded_bits))

        return HammingResult(
            data=decoded_dna,
            errors_detected=total_errors_detected,
            errors_corrected=total_errors_corrected,
            error_position=error_positions[0] if error_positions else None,
            is_valid=is_valid,
        )

    def _encode_block(self, data_bits: List[int]) -> List[int]:
        """
        Encode a 4-bit block using Hamming(7,4).

        Args:
            data_bits: 4 data bits

        Returns:
            7 or 8 encoded bits (with SECDED)
        """
        # Compute code word using generator matrix
        code_word = [0] * 7

        for i, d in enumerate(data_bits):
            for j in range(7):
                code_word[j] ^= d * self.GENERATOR_MATRIX[i][j]

        if self.use_secded:
            # Add overall parity bit
            parity = sum(code_word) % 2
            code_word.append(parity)

        return code_word

    def _decode_block(
        self, block: List[int]
    ) -> Tuple[List[int], int, int, Optional[int], bool]:
        """
        Decode a Hamming code block.

        Returns:
            Tuple of (data_bits, errors_detected, errors_corrected,
                     error_position, is_valid)
        """
        # Extract the 7-bit Hamming code (ignore extra parity for now)
        hamming_bits = block[:7]

        # Compute syndrome
        syndrome = [0, 0, 0]
        for i in range(3):
            for j in range(7):
                syndrome[i] ^= hamming_bits[j] * self.PARITY_CHECK_MATRIX[i][j]

        # Convert syndrome to error position
        error_pos = syndrome[0] + 2 * syndrome[1] + 4 * syndrome[2]

        errors_detected = 0
        errors_corrected = 0
        error_position = None
        is_valid = True

        if error_pos != 0:
            errors_detected = 1

            if self.use_secded and len(block) == 8:
                # Check overall parity
                overall_parity = sum(block) % 2

                if overall_parity == 1:
                    # Single error - correct it
                    if error_pos <= 7:
                        hamming_bits[error_pos - 1] ^= 1
                        errors_corrected = 1
                        error_position = error_pos - 1
                else:
                    # Double error - detected but not correctable
                    errors_detected = 2
                    is_valid = False
            else:
                # Without SECDED, just correct
                if error_pos <= 7:
                    hamming_bits[error_pos - 1] ^= 1
                    errors_corrected = 1
                    error_position = error_pos - 1

        # Extract original 4 data bits
        data_bits = [hamming_bits[0], hamming_bits[1], hamming_bits[2], hamming_bits[3]]

        return data_bits, errors_detected, errors_corrected, error_position, is_valid

    def _dna_to_binary(self, dna: str) -> str:
        """Convert DNA sequence to binary string."""
        binary_map = {"A": "00", "T": "01", "C": "10", "G": "11"}
        return "".join(binary_map.get(n, "00") for n in dna)

    def _binary_to_dna(self, binary: str) -> str:
        """Convert binary string to DNA sequence."""
        dna_map = {"00": "A", "01": "T", "10": "C", "11": "G"}

        # Pad to even length
        while len(binary) % 2 != 0:
            binary += "0"

        result = []
        for i in range(0, len(binary), 2):
            bits = binary[i:i + 2]
            result.append(dna_map.get(bits, "A"))

        return "".join(result)


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
