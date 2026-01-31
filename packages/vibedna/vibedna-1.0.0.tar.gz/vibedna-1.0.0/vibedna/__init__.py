"""
VibeDNA - Binary ↔ DNA Encoding and Computation System

Where Digital Meets Biological

This package provides comprehensive tools for encoding binary data as DNA sequences,
decoding DNA back to binary, performing computations on DNA-encoded data, and
managing files in a DNA-based virtual file system.

Example:
    >>> from vibedna import DNAEncoder, DNADecoder
    >>> encoder = DNAEncoder()
    >>> dna = encoder.encode(b"Hello World", filename="hello.txt")
    >>> decoder = DNADecoder()
    >>> result = decoder.decode(dna)
    >>> print(result.data)
    b'Hello World'

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

__version__ = "1.0.0"
__author__ = "NeuralQuantum.ai"
__email__ = "contact@neuralquantum.ai"

from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme
from vibedna.core.decoder import DNADecoder, DecodeResult
from vibedna.storage.dna_file_system import DNAFileSystem, DNAFile, DNADirectory
from vibedna.compute.dna_logic_gates import DNAComputeEngine, DNALogicGate
from vibedna.error_correction.reed_solomon_dna import DNAReedSolomon

__all__ = [
    "DNAEncoder",
    "DNADecoder",
    "EncodingConfig",
    "EncodingScheme",
    "DecodeResult",
    "DNAFileSystem",
    "DNAFile",
    "DNADirectory",
    "DNAComputeEngine",
    "DNALogicGate",
    "DNAReedSolomon",
]

# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
