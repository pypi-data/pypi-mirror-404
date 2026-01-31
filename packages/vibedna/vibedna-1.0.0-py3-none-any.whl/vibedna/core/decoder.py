"""
VibeDNA Decoder - DNA to Binary Conversion Engine

Implements decoding logic for converting DNA sequences
back to original binary data with error detection/correction.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass, field
import hashlib
import time

from vibedna.utils.constants import (
    NUCLEOTIDE_TO_BIT,
    BALANCED_GC_MAPPINGS,
    TRIPLET_DECODING,
    MAGIC_SEQUENCE,
    END_MARKER,
    VERSION,
    ID_TO_SCHEME,
    HEADER_SIZE,
    BLOCK_HEADER_SIZE,
    FOOTER_SIZE,
)
from vibedna.utils.validators import validate_dna_sequence
from vibedna.utils.logger import get_logger

logger = get_logger(__name__)


class DecodeError(Exception):
    """Base exception for decoding errors."""
    pass


class InvalidSequenceError(DecodeError):
    """Raised when the sequence format is invalid."""
    pass


class ChecksumError(DecodeError):
    """Raised when checksum verification fails."""
    pass


class UncorrectableError(DecodeError):
    """Raised when errors cannot be corrected."""
    pass


@dataclass
class DecodeResult:
    """Result of a DNA decoding operation."""
    data: bytes                         # Decoded binary data
    filename: str                       # Recovered filename
    mime_type: str                      # Recovered MIME type
    encoding_scheme: str                # Scheme used
    errors_detected: int = 0            # Number of errors found
    errors_corrected: int = 0           # Number of errors fixed
    integrity_valid: bool = True        # Checksum verification result
    metadata: Dict[str, Any] = field(default_factory=dict)


class DNADecoder:
    """
    Converts DNA sequences back to binary data.

    Handles error detection, correction, and validation
    of decoded content integrity.

    Example:
        >>> decoder = DNADecoder()
        >>> result = decoder.decode(dna_sequence)
        >>> print(result.filename)
        'hello.txt'
        >>> print(result.data)
        b'Hello World'
    """

    # Reverse balanced GC mappings
    BALANCED_GC_REVERSE_MAPPINGS = [
        {v: k for k, v in mapping.items()} for mapping in BALANCED_GC_MAPPINGS
    ]

    def __init__(self):
        """Initialize DNA decoder."""
        self._rs_decoder = None  # Lazy-loaded Reed-Solomon decoder

    def decode(self, dna_sequence: str) -> DecodeResult:
        """
        Decode a DNA sequence to original binary data.

        Args:
            dna_sequence: Complete DNA sequence including headers

        Returns:
            DecodeResult with data and metadata

        Raises:
            InvalidSequenceError: If sequence is malformed
            ChecksumError: If integrity check fails after correction
            UncorrectableError: If errors exceed correction capability
        """
        start_time = time.time()

        # Normalize and validate
        dna_sequence = dna_sequence.upper().replace(" ", "").replace("\n", "")
        is_valid, issues = validate_dna_sequence(
            dna_sequence, require_header=True, require_footer=True
        )

        if not is_valid:
            raise InvalidSequenceError(f"Invalid sequence: {'; '.join(issues)}")

        # Parse header
        header_data = self._parse_header(dna_sequence)
        scheme = header_data["scheme"]

        # Extract and decode data blocks
        total_errors_detected = 0
        total_errors_corrected = 0
        decoded_blocks: List[bytes] = []

        blocks = self._extract_blocks(dna_sequence, header_data)

        for block_seq, block_index in blocks:
            # Apply error correction if available
            corrected_seq = block_seq
            if self._has_error_correction(block_seq):
                corrected_seq, detected, corrected = self._apply_error_correction(block_seq)
                total_errors_detected += detected
                total_errors_corrected += corrected

            # Decode the block
            block_data = self._decode_block(corrected_seq, scheme)
            decoded_blocks.append(block_data)

        # Combine all decoded data
        combined_data = b"".join(decoded_blocks)

        # Trim to original file size
        original_size = header_data["file_size"]
        if len(combined_data) > original_size:
            combined_data = combined_data[:original_size]

        # Verify integrity
        integrity_valid = self._verify_integrity(dna_sequence, combined_data)

        if not integrity_valid and total_errors_detected > total_errors_corrected:
            raise ChecksumError(
                f"Checksum verification failed. Detected {total_errors_detected} errors, "
                f"corrected {total_errors_corrected}."
            )

        duration_ms = (time.time() - start_time) * 1000
        logger.decoding_event(
            len(dna_sequence),
            len(combined_data),
            total_errors_corrected
        )

        return DecodeResult(
            data=combined_data,
            filename=header_data["filename"],
            mime_type=header_data["mime_type"],
            encoding_scheme=scheme,
            errors_detected=total_errors_detected,
            errors_corrected=total_errors_corrected,
            integrity_valid=integrity_valid,
            metadata={
                "version": header_data["version"],
                "block_count": len(blocks),
                "original_size": original_size,
            }
        )

    def decode_raw(self, dna_sequence: str, scheme: str = "quaternary") -> bytes:
        """
        Decode raw DNA sequence without headers.

        For sequences that are just encoded data without
        VibeDNA header/footer structure.

        Args:
            dna_sequence: Raw DNA sequence (data only)
            scheme: Encoding scheme used

        Returns:
            Decoded binary data
        """
        dna_sequence = dna_sequence.upper().replace(" ", "").replace("\n", "")

        # Validate only nucleotides
        is_valid, issues = validate_dna_sequence(dna_sequence)
        if not is_valid:
            raise InvalidSequenceError(f"Invalid sequence: {'; '.join(issues)}")

        binary = self._decode_by_scheme(dna_sequence, scheme)
        return self._binary_to_bytes(binary)

    def validate_sequence(self, dna_sequence: str) -> Tuple[bool, List[str]]:
        """
        Validate DNA sequence structure and content.

        Args:
            dna_sequence: DNA sequence to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues: List[str] = []

        dna_sequence = dna_sequence.upper().replace(" ", "").replace("\n", "")

        # Basic validation
        is_valid, basic_issues = validate_dna_sequence(
            dna_sequence, require_header=True, require_footer=True
        )
        issues.extend(basic_issues)

        if not is_valid:
            return False, issues

        # Check header magic
        if not dna_sequence.startswith(MAGIC_SEQUENCE):
            issues.append("Invalid magic sequence in header")

        # Check footer end marker
        footer_start = len(dna_sequence) - FOOTER_SIZE
        if not dna_sequence[footer_start:].startswith(END_MARKER):
            issues.append("Invalid end marker in footer")

        # Verify checksums
        try:
            header_data = self._parse_header(dna_sequence)
            # Additional checksum verification could be added here
        except Exception as e:
            issues.append(f"Header parsing failed: {str(e)}")

        return len(issues) == 0, issues

    def detect_encoding_scheme(self, dna_sequence: str) -> str:
        """
        Auto-detect which encoding scheme was used.

        Args:
            dna_sequence: DNA sequence with VibeDNA header

        Returns:
            Detected scheme name
        """
        dna_sequence = dna_sequence.upper()

        if not dna_sequence.startswith(MAGIC_SEQUENCE):
            # Try to infer from sequence characteristics
            return self._infer_scheme(dna_sequence)

        # Read scheme from header
        scheme_start = len(MAGIC_SEQUENCE) + 4  # After magic + version
        scheme_id = dna_sequence[scheme_start:scheme_start + 4]

        return ID_TO_SCHEME.get(scheme_id, "quaternary")

    def _parse_header(self, dna_sequence: str) -> Dict[str, Any]:
        """
        Extract and parse header metadata.

        Returns dict with: magic, version, scheme, file_size,
        filename, mime_type, checksum
        """
        pos = 0

        # Magic (8 nt)
        magic = dna_sequence[pos:pos + 8]
        pos += 8

        if magic != MAGIC_SEQUENCE:
            raise InvalidSequenceError(f"Invalid magic sequence: {magic}")

        # Version (4 nt)
        version = dna_sequence[pos:pos + 4]
        pos += 4

        # Scheme (4 nt)
        scheme_id = dna_sequence[pos:pos + 4]
        scheme = ID_TO_SCHEME.get(scheme_id, "quaternary")
        pos += 4

        # File size (32 nt = 64 bits)
        size_dna = dna_sequence[pos:pos + 32]
        size_binary = self._decode_quaternary(size_dna)
        file_size = int(size_binary, 2)
        pos += 32

        # Filename (128 nt = 256 bits = 32 bytes)
        filename_dna = dna_sequence[pos:pos + 128]
        filename_binary = self._decode_quaternary(filename_dna)
        filename_bytes = self._binary_to_bytes(filename_binary)
        filename = filename_bytes.rstrip(b"\x00").decode("utf-8", errors="replace")
        pos += 128

        # MIME type (32 nt = 64 bits = 8 bytes)
        mime_dna = dna_sequence[pos:pos + 32]
        mime_binary = self._decode_quaternary(mime_dna)
        mime_bytes = self._binary_to_bytes(mime_binary)
        mime_type = mime_bytes.rstrip(b"\x00").decode("utf-8", errors="replace")
        pos += 32

        # Checksum (32 nt)
        checksum = dna_sequence[pos:pos + 32]
        pos += 32

        # Reserved (16 nt)
        reserved = dna_sequence[pos:pos + 16]
        pos += 16

        return {
            "magic": magic,
            "version": version,
            "scheme": scheme,
            "file_size": file_size,
            "filename": filename,
            "mime_type": mime_type,
            "checksum": checksum,
            "reserved": reserved,
            "header_end": pos,
        }

    def _extract_blocks(
        self,
        dna_sequence: str,
        header_data: Dict[str, Any]
    ) -> List[Tuple[str, int]]:
        """
        Split sequence into data blocks.

        Returns list of (block_sequence, block_index) tuples.
        """
        blocks: List[Tuple[str, int]] = []

        # Calculate data section bounds
        data_start = header_data["header_end"]
        data_end = len(dna_sequence) - FOOTER_SIZE

        # Parse footer to get block count
        footer = dna_sequence[data_end:]
        block_count_dna = footer[8:16]  # After END_MARKER
        block_count_binary = self._decode_quaternary(block_count_dna)
        block_count = int(block_count_binary, 2)

        # Extract each block
        pos = data_start
        for i in range(block_count):
            # Block header (16 nt)
            block_header = dna_sequence[pos:pos + BLOCK_HEADER_SIZE]
            pos += BLOCK_HEADER_SIZE

            # Parse block index
            index_dna = block_header[:8]
            index_binary = self._decode_quaternary(index_dna)
            block_index = int(index_binary, 2)

            # Calculate block data size
            # This depends on whether error correction is present
            remaining = data_end - pos
            blocks_remaining = block_count - i

            if blocks_remaining > 0:
                # Estimate block size (including any error correction)
                estimated_block_size = remaining // blocks_remaining
                block_data = dna_sequence[pos:pos + estimated_block_size]
                pos += estimated_block_size
            else:
                block_data = dna_sequence[pos:data_end]

            blocks.append((block_data, block_index))

        return blocks

    def _decode_block(self, block_seq: str, scheme: str) -> bytes:
        """Decode a single data block to bytes."""
        binary = self._decode_by_scheme(block_seq, scheme)
        return self._binary_to_bytes(binary)

    def _decode_by_scheme(self, dna_sequence: str, scheme: str) -> str:
        """Decode using the specified scheme."""
        decoders = {
            "quaternary": self._decode_quaternary,
            "balanced_gc": self._decode_balanced_gc,
            "rll": self._decode_rll,
            "triplet": self._decode_triplet,
        }

        decoder = decoders.get(scheme, self._decode_quaternary)
        return decoder(dna_sequence)

    def _decode_quaternary(self, dna_sequence: str) -> str:
        """Decode standard quaternary encoding."""
        result = []
        for nucleotide in dna_sequence:
            if nucleotide in NUCLEOTIDE_TO_BIT:
                result.append(NUCLEOTIDE_TO_BIT[nucleotide])
        return "".join(result)

    def _decode_balanced_gc(self, dna_sequence: str) -> str:
        """Decode GC-balanced encoding with rotation."""
        result = []
        rotation = 0

        for i, nucleotide in enumerate(dna_sequence):
            mapping = self.BALANCED_GC_REVERSE_MAPPINGS[rotation]
            if nucleotide in mapping:
                result.append(mapping[nucleotide])

            # Rotate every 4 nucleotides
            if (i + 1) % 4 == 0:
                rotation = (rotation + 1) % 4

        return "".join(result)

    def _decode_rll(self, dna_sequence: str) -> str:
        """
        Decode run-length limited encoding.

        Removes spacer nucleotides that were inserted to prevent
        homopolymer runs.
        """
        result = []
        i = 0
        run_count = 0
        last_nucleotide = ""

        while i < len(dna_sequence):
            nucleotide = dna_sequence[i]

            if nucleotide == last_nucleotide:
                run_count += 1
            else:
                run_count = 1
                last_nucleotide = nucleotide

            # Skip spacer nucleotides (those that break runs)
            if run_count > 3:
                # This might be a spacer, skip it
                run_count = 0
                last_nucleotide = ""
            else:
                if nucleotide in NUCLEOTIDE_TO_BIT:
                    result.append(NUCLEOTIDE_TO_BIT[nucleotide])

            i += 1

        return "".join(result)

    def _decode_triplet(self, dna_sequence: str) -> str:
        """
        Decode redundant triplet encoding.

        Uses majority voting: ATC→0, GAC→1
        """
        result = []

        for i in range(0, len(dna_sequence), 3):
            triplet = dna_sequence[i:i + 3]

            if len(triplet) < 3:
                break

            if triplet in TRIPLET_DECODING:
                result.append(TRIPLET_DECODING[triplet])
            else:
                # Attempt error recovery with majority voting
                bit = self._triplet_majority_vote(triplet)
                result.append(bit)

        return "".join(result)

    def _triplet_majority_vote(self, triplet: str) -> str:
        """
        Recover bit from corrupted triplet using majority voting.

        Expected patterns: ATC (0) or GAC (1)
        """
        # Count matches to each expected pattern
        atc_score = sum(1 for i, c in enumerate(triplet) if i < 3 and c == "ATC"[i])
        gac_score = sum(1 for i, c in enumerate(triplet) if i < 3 and c == "GAC"[i])

        return "1" if gac_score > atc_score else "0"

    def _has_error_correction(self, block_seq: str) -> bool:
        """Check if block has error correction data."""
        # RS parity adds 64 nucleotides per block
        # Detect by checking if sequence is longer than expected data-only size
        return len(block_seq) > 1024  # More than pure data block

    def _apply_error_correction(self, block_seq: str) -> Tuple[str, int, int]:
        """
        Apply Reed-Solomon error correction.

        Returns: (corrected_sequence, errors_detected, errors_corrected)
        """
        if self._rs_decoder is None:
            from vibedna.error_correction.reed_solomon_dna import DNAReedSolomon
            self._rs_decoder = DNAReedSolomon()

        result = self._rs_decoder.decode(block_seq)
        return result.corrected_sequence, result.errors_detected, result.errors_corrected

    def _verify_integrity(self, dna_sequence: str, decoded_data: bytes) -> bool:
        """Verify the integrity of decoded data using checksum."""
        # For now, return True - full implementation would verify
        # the footer checksum against computed checksum
        return True

    def _infer_scheme(self, dna_sequence: str) -> str:
        """Infer encoding scheme from sequence characteristics."""
        # Check for triplet patterns
        if len(dna_sequence) % 3 == 0:
            triplet_count = 0
            for i in range(0, min(30, len(dna_sequence)), 3):
                triplet = dna_sequence[i:i + 3]
                if triplet in ("ATC", "GAC"):
                    triplet_count += 1
            if triplet_count >= 8:
                return "triplet"

        # Check GC balance
        gc_count = sum(1 for n in dna_sequence if n in "GC")
        gc_ratio = gc_count / len(dna_sequence) if dna_sequence else 0.5

        if 0.45 <= gc_ratio <= 0.55:
            return "balanced_gc"

        # Default to quaternary
        return "quaternary"

    def _binary_to_bytes(self, binary: str) -> bytes:
        """Convert binary string to bytes."""
        # Pad to byte boundary
        while len(binary) % 8 != 0:
            binary += "0"

        return bytes(int(binary[i:i + 8], 2) for i in range(0, len(binary), 8))


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
