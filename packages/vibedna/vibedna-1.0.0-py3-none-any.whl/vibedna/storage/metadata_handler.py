"""
VibeDNA Metadata Handler

Encode and decode file metadata in DNA headers.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

from vibedna.utils.constants import (
    BIT_TO_NUCLEOTIDE,
    NUCLEOTIDE_TO_BIT,
    HEADER_SIZE,
)


@dataclass
class FileMetadata:
    """File metadata structure."""
    filename: str = ""
    mime_type: str = "application/octet-stream"
    file_size: int = 0
    encoding_scheme: str = "quaternary"
    version: str = "1.0"
    checksum: str = ""
    custom: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom is None:
            self.custom = {}


class MetadataHandler:
    """
    Handle encoding and decoding of metadata in DNA headers.

    Metadata is encoded as DNA and placed in the sequence header,
    allowing files to be self-describing.

    Example:
        >>> handler = MetadataHandler()
        >>> meta = FileMetadata(filename="test.txt", file_size=100)
        >>> dna = handler.encode(meta)
        >>> recovered = handler.decode(dna)
        >>> print(recovered.filename)
        test.txt
    """

    # Field sizes in nucleotides
    FIELD_SIZES = {
        "version": 4,
        "scheme": 4,
        "file_size": 32,
        "filename": 128,
        "mime_type": 32,
        "checksum": 32,
        "custom_length": 8,
    }

    def encode(self, metadata: FileMetadata) -> str:
        """
        Encode metadata as DNA sequence.

        Args:
            metadata: Metadata to encode

        Returns:
            DNA sequence containing metadata
        """
        parts = []

        # Version (4 nt)
        parts.append(self._encode_string(metadata.version, 2))

        # Encoding scheme (4 nt)
        parts.append(self._encode_string(metadata.encoding_scheme[:2], 2))

        # File size (32 nt = 64 bits)
        parts.append(self._encode_int(metadata.file_size, 32))

        # Filename (128 nt = 256 bits = 32 bytes)
        parts.append(self._encode_string(metadata.filename, 32))

        # MIME type (32 nt = 64 bits = 8 bytes)
        parts.append(self._encode_string(metadata.mime_type, 8))

        # Checksum (32 nt)
        parts.append(self._encode_string(metadata.checksum, 16))

        # Custom metadata as JSON
        if metadata.custom:
            custom_json = json.dumps(metadata.custom)[:100]
            custom_dna = self._encode_string(custom_json, 50)
            custom_length = len(custom_dna)
            parts.append(self._encode_int(custom_length, 8))
            parts.append(custom_dna)
        else:
            parts.append(self._encode_int(0, 8))

        return "".join(parts)

    def decode(self, dna_sequence: str) -> FileMetadata:
        """
        Decode metadata from DNA sequence.

        Args:
            dna_sequence: DNA sequence containing metadata

        Returns:
            Decoded FileMetadata object
        """
        pos = 0

        # Version (4 nt)
        version = self._decode_string(dna_sequence[pos:pos + 4], 2)
        pos += 4

        # Scheme (4 nt)
        scheme = self._decode_string(dna_sequence[pos:pos + 4], 2)
        pos += 4

        # File size (32 nt)
        file_size = self._decode_int(dna_sequence[pos:pos + 32])
        pos += 32

        # Filename (128 nt)
        filename = self._decode_string(dna_sequence[pos:pos + 128], 32)
        pos += 128

        # MIME type (32 nt)
        mime_type = self._decode_string(dna_sequence[pos:pos + 32], 8)
        pos += 32

        # Checksum (32 nt)
        checksum = self._decode_string(dna_sequence[pos:pos + 32], 16)
        pos += 32

        # Custom length (8 nt)
        custom_length = self._decode_int(dna_sequence[pos:pos + 8])
        pos += 8

        # Custom metadata
        custom = {}
        if custom_length > 0 and pos + custom_length <= len(dna_sequence):
            custom_json = self._decode_string(
                dna_sequence[pos:pos + custom_length],
                custom_length // 4
            )
            try:
                custom = json.loads(custom_json)
            except json.JSONDecodeError:
                pass

        return FileMetadata(
            filename=filename.strip("\x00"),
            mime_type=mime_type.strip("\x00"),
            file_size=file_size,
            encoding_scheme=scheme.strip("\x00"),
            version=version.strip("\x00"),
            checksum=checksum,
            custom=custom,
        )

    def _encode_string(self, text: str, max_bytes: int) -> str:
        """Encode string as DNA."""
        # Pad or truncate
        text_bytes = text.encode("utf-8")[:max_bytes].ljust(max_bytes, b"\x00")

        # Convert to binary then DNA
        binary = "".join(format(b, "08b") for b in text_bytes)
        return self._binary_to_dna(binary)

    def _decode_string(self, dna: str, max_bytes: int) -> str:
        """Decode DNA to string."""
        binary = self._dna_to_binary(dna)

        # Convert binary to bytes
        byte_list = []
        for i in range(0, min(len(binary), max_bytes * 8), 8):
            byte_val = int(binary[i:i + 8], 2)
            byte_list.append(byte_val)

        return bytes(byte_list).decode("utf-8", errors="replace")

    def _encode_int(self, value: int, nucleotides: int) -> str:
        """Encode integer as DNA."""
        bits = nucleotides * 2
        binary = format(value, f"0{bits}b")
        return self._binary_to_dna(binary)

    def _decode_int(self, dna: str) -> int:
        """Decode DNA to integer."""
        binary = self._dna_to_binary(dna)
        return int(binary, 2) if binary else 0

    def _binary_to_dna(self, binary: str) -> str:
        """Convert binary string to DNA."""
        # Pad to even length
        if len(binary) % 2 != 0:
            binary += "0"

        result = []
        for i in range(0, len(binary), 2):
            bits = binary[i:i + 2]
            result.append(BIT_TO_NUCLEOTIDE[bits])

        return "".join(result)

    def _dna_to_binary(self, dna: str) -> str:
        """Convert DNA to binary string."""
        result = []
        for nucleotide in dna.upper():
            if nucleotide in NUCLEOTIDE_TO_BIT:
                result.append(NUCLEOTIDE_TO_BIT[nucleotide])
        return "".join(result)


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
