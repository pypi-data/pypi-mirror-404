"""
VibeDNA Encoder - Binary to DNA Conversion Engine

Implements the primary encoding logic for converting binary data
to DNA sequences with configurable encoding schemes.

Encoding Schemes:
    - quaternary: Standard 2-bit per nucleotide mapping
    - balanced_gc: GC-content balanced encoding
    - rll: Run-length limited (no homopolymer runs)
    - triplet: Redundant triplet encoding for error tolerance

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Union, Generator, Optional, List
from enum import Enum
from dataclasses import dataclass
import hashlib
import time

from vibedna.utils.constants import (
    BIT_TO_NUCLEOTIDE,
    NUCLEOTIDE_VALUE,
    VALUE_NUCLEOTIDE,
    BALANCED_GC_MAPPINGS,
    TRIPLET_ENCODING,
    MAGIC_SEQUENCE,
    END_MARKER,
    VERSION,
    SCHEME_TO_ID,
    HEADER_SIZE,
    BLOCK_SIZE,
    BLOCK_DNA_SIZE,
    BLOCK_HEADER_SIZE,
    FOOTER_SIZE,
    RLL_MAX_HOMOPOLYMER,
    COPYRIGHT,
)
from vibedna.utils.validators import ValidationError
from vibedna.utils.logger import get_logger

logger = get_logger(__name__)


class EncodingScheme(Enum):
    """Available DNA encoding schemes."""
    QUATERNARY = "quaternary"           # Standard 2-bit per nucleotide
    BALANCED_GC = "balanced_gc"         # GC-content balanced
    RUN_LENGTH_LIMITED = "rll"          # No homopolymer runs
    REDUNDANT_TRIPLET = "triplet"       # Error-tolerant triplet


@dataclass
class EncodingConfig:
    """Configuration for DNA encoding operations."""
    scheme: EncodingScheme = EncodingScheme.QUATERNARY
    block_size: int = BLOCK_SIZE        # Bytes per block
    error_correction: bool = True       # Enable Reed-Solomon
    gc_balance_target: float = 0.5      # Target GC content (0.4-0.6)
    max_homopolymer_run: int = RLL_MAX_HOMOPOLYMER  # Max consecutive same nucleotides


class DNAEncoder:
    """
    Converts binary data to DNA sequences.

    Supports multiple encoding schemes optimized for different
    use cases: storage density, error tolerance, or synthesis compatibility.

    Example:
        >>> encoder = DNAEncoder()
        >>> dna = encoder.encode(b"Hello", filename="hello.txt")
        >>> print(dna[:20])  # First 20 nucleotides
        ATCGATCGAAATAAAAAAAA

        >>> # Use balanced GC encoding
        >>> config = EncodingConfig(scheme=EncodingScheme.BALANCED_GC)
        >>> encoder = DNAEncoder(config)
        >>> dna = encoder.encode(b"Hello")
    """

    NUCLEOTIDES = ["A", "T", "C", "G"]

    def __init__(self, config: Optional[EncodingConfig] = None):
        """
        Initialize DNA encoder.

        Args:
            config: Optional encoding configuration. Uses defaults if not provided.
        """
        self.config = config or EncodingConfig()
        self._validate_config()
        self._rs_encoder = None  # Lazy-loaded Reed-Solomon encoder

    def _validate_config(self) -> None:
        """Validate encoding configuration parameters."""
        if not 0.3 <= self.config.gc_balance_target <= 0.7:
            raise ValueError("GC balance target must be between 0.3 and 0.7")
        if self.config.max_homopolymer_run < 1:
            raise ValueError("Max homopolymer run must be at least 1")
        if self.config.block_size < 64:
            raise ValueError("Block size must be at least 64 bytes")

    def encode(
        self,
        data: Union[bytes, str],
        filename: str = "untitled",
        mime_type: str = "application/octet-stream"
    ) -> str:
        """
        Encode binary data to a complete DNA sequence.

        Args:
            data: Binary data or string to encode
            filename: Original filename for metadata
            mime_type: MIME type of the content

        Returns:
            Complete DNA sequence with headers, data, and error correction

        Example:
            >>> encoder = DNAEncoder()
            >>> dna = encoder.encode(b"Test data", filename="test.bin")
        """
        start_time = time.time()

        # Convert input to bytes if string
        if isinstance(data, str):
            data = data.encode("utf-8")

        # Convert bytes to binary string
        binary = self._bytes_to_binary(data)

        # Generate header
        header = self._generate_header(len(data), filename, mime_type)

        # Encode data in blocks
        blocks: List[str] = []
        scheme_encoder = self._get_scheme_encoder()

        for i in range(0, len(binary), self.config.block_size * 8):
            block_binary = binary[i:i + self.config.block_size * 8]
            block_index = len(blocks)

            # Encode the block data
            block_data = scheme_encoder(block_binary)

            # Generate block header
            block_header = self._generate_block_header(block_index, block_data)

            # Add error correction if enabled
            if self.config.error_correction:
                block_data = self._add_error_correction(block_data)

            blocks.append(block_header + block_data)

        # Generate footer
        footer = self._generate_footer(len(blocks), header + "".join(blocks))

        # Combine all parts
        sequence = header + "".join(blocks) + footer

        duration_ms = (time.time() - start_time) * 1000
        logger.encoding_event(len(data), len(sequence), self.config.scheme.value)

        return sequence

    def encode_stream(
        self,
        data_stream: Generator[bytes, None, None]
    ) -> Generator[str, None, None]:
        """
        Stream-encode binary data for large files.

        Yields DNA sequence chunks as they're encoded,
        suitable for files too large for memory.

        Args:
            data_stream: Generator yielding binary chunks

        Yields:
            DNA sequence chunks
        """
        scheme_encoder = self._get_scheme_encoder()
        block_index = 0
        buffer = b""

        for chunk in data_stream:
            buffer += chunk

            while len(buffer) >= self.config.block_size:
                block_data = buffer[:self.config.block_size]
                buffer = buffer[self.config.block_size:]

                binary = self._bytes_to_binary(block_data)
                encoded = scheme_encoder(binary)

                block_header = self._generate_block_header(block_index, encoded)

                if self.config.error_correction:
                    encoded = self._add_error_correction(encoded)

                yield block_header + encoded
                block_index += 1

        # Handle remaining data
        if buffer:
            binary = self._bytes_to_binary(buffer)
            encoded = scheme_encoder(binary)
            block_header = self._generate_block_header(block_index, encoded)

            if self.config.error_correction:
                encoded = self._add_error_correction(encoded)

            yield block_header + encoded

    def encode_raw(self, data: Union[bytes, str]) -> str:
        """
        Encode data without headers/footers (raw encoding).

        Args:
            data: Binary data or string to encode

        Returns:
            Raw DNA sequence without VibeDNA structure
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        binary = self._bytes_to_binary(data)
        scheme_encoder = self._get_scheme_encoder()

        return scheme_encoder(binary)

    def _get_scheme_encoder(self):
        """Get the encoder function for the configured scheme."""
        encoders = {
            EncodingScheme.QUATERNARY: self._encode_quaternary,
            EncodingScheme.BALANCED_GC: self._encode_balanced_gc,
            EncodingScheme.RUN_LENGTH_LIMITED: self._encode_rll,
            EncodingScheme.REDUNDANT_TRIPLET: self._encode_triplet,
        }
        return encoders[self.config.scheme]

    def _encode_quaternary(self, binary: str) -> str:
        """
        Standard quaternary encoding (2 bits per nucleotide).

        Mapping: 00→A, 01→T, 10→C, 11→G
        """
        # Pad to even length
        if len(binary) % 2 != 0:
            binary += "0"

        result = []
        for i in range(0, len(binary), 2):
            bits = binary[i:i + 2]
            result.append(BIT_TO_NUCLEOTIDE[bits])

        return "".join(result)

    def _encode_balanced_gc(self, binary: str) -> str:
        """
        GC-balanced encoding with rotation.

        Rotates through 4 different mappings to balance GC content
        across the sequence.
        """
        if len(binary) % 2 != 0:
            binary += "0"

        result = []
        rotation = 0

        for i in range(0, len(binary), 2):
            bits = binary[i:i + 2]
            mapping = BALANCED_GC_MAPPINGS[rotation]
            result.append(mapping[bits])

            # Rotate every 4 nucleotides
            if (i // 2 + 1) % 4 == 0:
                rotation = (rotation + 1) % 4

        return "".join(result)

    def _encode_rll(self, binary: str) -> str:
        """
        Run-length limited encoding.

        Prevents homopolymer runs by inserting spacer nucleotides
        when consecutive runs would exceed the maximum.
        """
        if len(binary) % 2 != 0:
            binary += "0"

        result = []
        current_run = 0
        last_nucleotide = ""

        for i in range(0, len(binary), 2):
            bits = binary[i:i + 2]
            nucleotide = BIT_TO_NUCLEOTIDE[bits]

            if nucleotide == last_nucleotide:
                current_run += 1
                if current_run >= self.config.max_homopolymer_run:
                    # Insert a spacer that differs from current nucleotide
                    spacer = self._get_spacer(nucleotide)
                    result.append(spacer)
                    current_run = 0
            else:
                current_run = 1
                last_nucleotide = nucleotide

            result.append(nucleotide)

        return "".join(result)

    def _get_spacer(self, avoid: str) -> str:
        """Get a spacer nucleotide that differs from the given one."""
        # Return complement: A↔C, T↔G
        spacers = {"A": "C", "T": "G", "C": "A", "G": "T"}
        return spacers[avoid]

    def _encode_triplet(self, binary: str) -> str:
        """
        Redundant triplet encoding for high error tolerance.

        Each bit is encoded as 3 nucleotides:
        0 → ATC
        1 → GAC
        """
        result = []
        for bit in binary:
            result.append(TRIPLET_ENCODING[bit])

        return "".join(result)

    def _generate_header(
        self,
        data_size: int,
        filename: str,
        mime_type: str
    ) -> str:
        """
        Generate DNA sequence header with metadata.

        Header structure (256 nucleotides):
        - Magic: 8 nt
        - Version: 4 nt
        - Scheme: 4 nt
        - File size: 32 nt
        - Filename: 128 nt
        - MIME type: 32 nt
        - Checksum: 32 nt
        - Reserved: 16 nt
        """
        parts = []

        # Magic sequence (8 nt)
        parts.append(MAGIC_SEQUENCE)

        # Version (4 nt)
        parts.append(VERSION)

        # Encoding scheme (4 nt)
        parts.append(SCHEME_TO_ID[self.config.scheme.value])

        # File size (32 nt = 64 bits = 8 bytes for size)
        size_binary = format(data_size, "064b")
        parts.append(self._encode_quaternary(size_binary))

        # Filename (128 nt = 256 bits = 32 bytes)
        filename_bytes = filename.encode("utf-8")[:32].ljust(32, b"\x00")
        filename_binary = self._bytes_to_binary(filename_bytes)
        parts.append(self._encode_quaternary(filename_binary))

        # MIME type (32 nt = 64 bits = 8 bytes)
        mime_bytes = mime_type.encode("utf-8")[:8].ljust(8, b"\x00")
        mime_binary = self._bytes_to_binary(mime_bytes)
        parts.append(self._encode_quaternary(mime_binary))

        # Calculate checksum of header content so far
        header_content = "".join(parts)
        checksum = self._calculate_checksum(header_content)
        parts.append(checksum)  # 32 nt

        # Reserved (16 nt)
        parts.append("A" * 16)

        return "".join(parts)

    def _generate_block_header(self, block_index: int, block_data: str) -> str:
        """
        Generate block header (16 nucleotides).

        - Block index: 8 nt (16 bits, up to 65535 blocks)
        - Block checksum: 8 nt
        """
        # Block index (8 nt)
        index_binary = format(block_index, "016b")
        index_dna = self._encode_quaternary(index_binary)

        # Block checksum (8 nt)
        checksum = self._calculate_checksum(block_data)[:8]

        return index_dna + checksum

    def _generate_footer(self, block_count: int, sequence: str) -> str:
        """
        Generate footer (32 nucleotides).

        - End marker: 8 nt
        - Block count: 8 nt
        - Final checksum: 16 nt
        """
        parts = []

        # End marker (8 nt)
        parts.append(END_MARKER)

        # Block count (8 nt)
        count_binary = format(block_count, "016b")
        parts.append(self._encode_quaternary(count_binary))

        # Final checksum (16 nt)
        checksum = self._calculate_checksum(sequence)[:16]
        parts.append(checksum)

        return "".join(parts)

    def _add_error_correction(self, sequence: str) -> str:
        """Add Reed-Solomon error correction parity."""
        if self._rs_encoder is None:
            from vibedna.error_correction.reed_solomon_dna import DNAReedSolomon
            self._rs_encoder = DNAReedSolomon()

        return self._rs_encoder.encode(sequence)

    def _bytes_to_binary(self, data: bytes) -> str:
        """Convert bytes to binary string representation."""
        return "".join(format(byte, "08b") for byte in data)

    def _calculate_checksum(self, sequence: str) -> str:
        """
        Calculate DNA checksum for integrity verification.

        Uses SHA-256 hash of the sequence, then encodes the hash
        as DNA.
        """
        hash_bytes = hashlib.sha256(sequence.encode()).digest()[:16]
        hash_binary = self._bytes_to_binary(hash_bytes)
        return self._encode_quaternary(hash_binary)


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
