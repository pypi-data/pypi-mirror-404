"""
VibeDNA Constants

System-wide constants and mappings for DNA encoding operations.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Dict, List, Final

# Nucleotide bases
NUCLEOTIDES: Final[List[str]] = ["A", "T", "C", "G"]

# Primary encoding: 2 bits → 1 nucleotide (Quaternary mapping)
BIT_TO_NUCLEOTIDE: Final[Dict[str, str]] = {
    "00": "A",  # Adenine
    "01": "T",  # Thymine
    "10": "C",  # Cytosine
    "11": "G",  # Guanine
}

# Reverse mapping: 1 nucleotide → 2 bits
NUCLEOTIDE_TO_BIT: Final[Dict[str, str]] = {
    "A": "00",
    "T": "01",
    "C": "10",
    "G": "11",
}

# Nucleotide numeric values for computation
NUCLEOTIDE_VALUE: Final[Dict[str, int]] = {
    "A": 0,
    "T": 1,
    "C": 2,
    "G": 3,
}

VALUE_NUCLEOTIDE: Final[Dict[int, str]] = {
    0: "A",
    1: "T",
    2: "C",
    3: "G",
}

# Complement mapping for NOT operation
NUCLEOTIDE_COMPLEMENT: Final[Dict[str, str]] = {
    "A": "G",  # 00 → 11
    "T": "C",  # 01 → 10
    "C": "T",  # 10 → 01
    "G": "A",  # 11 → 00
}

# Balanced GC rotation mappings (4 different mappings to balance GC content)
BALANCED_GC_MAPPINGS: Final[List[Dict[str, str]]] = [
    {"00": "A", "01": "T", "10": "G", "11": "C"},  # Standard
    {"00": "T", "01": "A", "10": "C", "11": "G"},  # Rotated 1
    {"00": "G", "01": "C", "10": "A", "11": "T"},  # Rotated 2
    {"00": "C", "01": "G", "10": "T", "11": "A"},  # Rotated 3
]

# Triplet encoding for high error tolerance
TRIPLET_ENCODING: Final[Dict[str, str]] = {
    "0": "ATC",
    "1": "GAC",
}

TRIPLET_DECODING: Final[Dict[str, str]] = {
    "ATC": "0",
    "GAC": "1",
}

# File format markers
MAGIC_SEQUENCE: Final[str] = "ATCGATCG"  # 8 nucleotides - file identifier
END_MARKER: Final[str] = "GCTAGCTA"  # 8 nucleotides - file end marker
VERSION: Final[str] = "AAAT"  # 4 nucleotides - version 1.0

# Encoding scheme identifiers (4 nucleotides each)
SCHEME_QUATERNARY: Final[str] = "AAAA"
SCHEME_BALANCED_GC: Final[str] = "AAAT"
SCHEME_RLL: Final[str] = "AATC"
SCHEME_TRIPLET: Final[str] = "AATG"

SCHEME_TO_ID: Final[Dict[str, str]] = {
    "quaternary": SCHEME_QUATERNARY,
    "balanced_gc": SCHEME_BALANCED_GC,
    "rll": SCHEME_RLL,
    "triplet": SCHEME_TRIPLET,
}

ID_TO_SCHEME: Final[Dict[str, str]] = {v: k for k, v in SCHEME_TO_ID.items()}

# Header structure sizes (in nucleotides)
HEADER_SIZE: Final[int] = 256  # Total header size
HEADER_MAGIC_SIZE: Final[int] = 8  # Magic sequence
HEADER_VERSION_SIZE: Final[int] = 4  # Encoding version
HEADER_SCHEME_SIZE: Final[int] = 4  # Encoding scheme
HEADER_FILESIZE_SIZE: Final[int] = 32  # Original binary size
HEADER_FILENAME_SIZE: Final[int] = 128  # Encoded filename
HEADER_MIMETYPE_SIZE: Final[int] = 32  # Content type
HEADER_CHECKSUM_SIZE: Final[int] = 32  # Header integrity
HEADER_RESERVED_SIZE: Final[int] = 16  # Future use

# Block structure sizes
BLOCK_SIZE: Final[int] = 512  # Bytes per block
BLOCK_DNA_SIZE: Final[int] = 1024  # Nucleotides per block (512 bytes × 2)
BLOCK_HEADER_SIZE: Final[int] = 16  # Block header in nucleotides
BLOCK_INDEX_SIZE: Final[int] = 8  # Block index in nucleotides
BLOCK_CHECKSUM_SIZE: Final[int] = 8  # Block checksum in nucleotides

# Error correction sizes
RS_PARITY_SIZE: Final[int] = 64  # Reed-Solomon parity per block
GLOBAL_CHECKSUM_SIZE: Final[int] = 64  # Global checksum

# Footer structure sizes
FOOTER_SIZE: Final[int] = 32  # Total footer size
FOOTER_END_MARKER_SIZE: Final[int] = 8  # End marker
FOOTER_BLOCK_COUNT_SIZE: Final[int] = 8  # Total blocks
FOOTER_CHECKSUM_SIZE: Final[int] = 16  # Final checksum

# Run-length limited constraints
RLL_MAX_HOMOPOLYMER: Final[int] = 3  # Maximum consecutive same nucleotides
RLL_SPACER_NUCLEOTIDES: Final[List[str]] = ["T", "C"]  # Spacers to break runs

# GC content constraints
GC_MIN_RATIO: Final[float] = 0.3
GC_MAX_RATIO: Final[float] = 0.7
GC_TARGET_RATIO: Final[float] = 0.5

# Performance limits
MAX_FILE_SIZE: Final[int] = 100 * 1024 * 1024  # 100 MB max file size
STREAM_CHUNK_SIZE: Final[int] = 8192  # Bytes per stream chunk

# Copyright notice
COPYRIGHT: Final[str] = (
    "© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. "
    "All rights reserved."
)

# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
