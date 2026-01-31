"""
VibeDNA Codec Registry

Centralized registry for managing encoding schemes and their implementations.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Dict, Callable, Optional, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum

from vibedna.utils.constants import (
    BIT_TO_NUCLEOTIDE,
    NUCLEOTIDE_TO_BIT,
    BALANCED_GC_MAPPINGS,
    TRIPLET_ENCODING,
    TRIPLET_DECODING,
)


@dataclass
class CodecInfo:
    """Information about a registered codec."""
    name: str
    description: str
    bits_per_nucleotide: float  # Average bits encoded per nucleotide
    error_tolerance: str  # "none", "low", "medium", "high"
    gc_balanced: bool
    homopolymer_safe: bool
    encoder: Callable[[str], str]  # binary → DNA
    decoder: Callable[[str], str]  # DNA → binary


class CodecRegistry:
    """
    Registry for DNA encoding/decoding schemes.

    Provides a central place to register, retrieve, and manage
    encoding schemes.

    Example:
        >>> registry = CodecRegistry()
        >>> codec = registry.get("quaternary")
        >>> dna = codec.encoder("01001000")  # Encode binary
        >>> binary = codec.decoder("ATCG")    # Decode DNA

        >>> # Register custom codec
        >>> registry.register(
        ...     name="custom",
        ...     description="Custom encoding scheme",
        ...     bits_per_nucleotide=2.0,
        ...     error_tolerance="none",
        ...     gc_balanced=False,
        ...     homopolymer_safe=False,
        ...     encoder=my_encoder,
        ...     decoder=my_decoder
        ... )
    """

    _instance: Optional["CodecRegistry"] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern - only one registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the registry with built-in codecs."""
        if CodecRegistry._initialized:
            return

        self._codecs: Dict[str, CodecInfo] = {}
        self._register_builtin_codecs()
        CodecRegistry._initialized = True

    def _register_builtin_codecs(self) -> None:
        """Register all built-in encoding schemes."""
        # Quaternary codec
        self.register(
            name="quaternary",
            description="Standard 2-bit per nucleotide encoding",
            bits_per_nucleotide=2.0,
            error_tolerance="none",
            gc_balanced=False,
            homopolymer_safe=False,
            encoder=self._quaternary_encode,
            decoder=self._quaternary_decode,
        )

        # Balanced GC codec
        self.register(
            name="balanced_gc",
            description="GC-content balanced encoding with rotation",
            bits_per_nucleotide=2.0,
            error_tolerance="none",
            gc_balanced=True,
            homopolymer_safe=False,
            encoder=self._balanced_gc_encode,
            decoder=self._balanced_gc_decode,
        )

        # Run-length limited codec
        self.register(
            name="rll",
            description="Run-length limited encoding (no homopolymer runs)",
            bits_per_nucleotide=1.8,  # ~10% overhead from spacers
            error_tolerance="none",
            gc_balanced=False,
            homopolymer_safe=True,
            encoder=self._rll_encode,
            decoder=self._rll_decode,
        )

        # Triplet codec
        self.register(
            name="triplet",
            description="Redundant triplet encoding for high error tolerance",
            bits_per_nucleotide=0.33,  # 1 bit per 3 nucleotides
            error_tolerance="high",
            gc_balanced=False,
            homopolymer_safe=False,
            encoder=self._triplet_encode,
            decoder=self._triplet_decode,
        )

    def register(
        self,
        name: str,
        description: str,
        bits_per_nucleotide: float,
        error_tolerance: str,
        gc_balanced: bool,
        homopolymer_safe: bool,
        encoder: Callable[[str], str],
        decoder: Callable[[str], str],
    ) -> None:
        """
        Register a new codec.

        Args:
            name: Unique codec name
            description: Human-readable description
            bits_per_nucleotide: Average bits encoded per nucleotide
            error_tolerance: "none", "low", "medium", or "high"
            gc_balanced: Whether codec maintains balanced GC content
            homopolymer_safe: Whether codec prevents homopolymer runs
            encoder: Function to encode binary string to DNA
            decoder: Function to decode DNA to binary string
        """
        if name in self._codecs:
            raise ValueError(f"Codec '{name}' is already registered")

        self._codecs[name] = CodecInfo(
            name=name,
            description=description,
            bits_per_nucleotide=bits_per_nucleotide,
            error_tolerance=error_tolerance,
            gc_balanced=gc_balanced,
            homopolymer_safe=homopolymer_safe,
            encoder=encoder,
            decoder=decoder,
        )

    def unregister(self, name: str) -> None:
        """
        Unregister a codec.

        Args:
            name: Codec name to remove
        """
        if name not in self._codecs:
            raise KeyError(f"Codec '{name}' not found")
        del self._codecs[name]

    def get(self, name: str) -> CodecInfo:
        """
        Get a codec by name.

        Args:
            name: Codec name

        Returns:
            CodecInfo object

        Raises:
            KeyError: If codec not found
        """
        if name not in self._codecs:
            raise KeyError(f"Codec '{name}' not found. Available: {self.list_codecs()}")
        return self._codecs[name]

    def list_codecs(self) -> List[str]:
        """
        List all registered codec names.

        Returns:
            List of codec names
        """
        return list(self._codecs.keys())

    def get_codec_info(self, name: str) -> Dict[str, Any]:
        """
        Get codec information as dictionary.

        Args:
            name: Codec name

        Returns:
            Dictionary with codec details
        """
        codec = self.get(name)
        return {
            "name": codec.name,
            "description": codec.description,
            "bits_per_nucleotide": codec.bits_per_nucleotide,
            "error_tolerance": codec.error_tolerance,
            "gc_balanced": codec.gc_balanced,
            "homopolymer_safe": codec.homopolymer_safe,
        }

    def encode(self, binary: str, codec_name: str = "quaternary") -> str:
        """
        Encode binary string using specified codec.

        Args:
            binary: Binary string to encode
            codec_name: Name of codec to use

        Returns:
            DNA sequence
        """
        codec = self.get(codec_name)
        return codec.encoder(binary)

    def decode(self, dna: str, codec_name: str = "quaternary") -> str:
        """
        Decode DNA sequence using specified codec.

        Args:
            dna: DNA sequence to decode
            codec_name: Name of codec to use

        Returns:
            Binary string
        """
        codec = self.get(codec_name)
        return codec.decoder(dna)

    def recommend_codec(
        self,
        require_gc_balance: bool = False,
        require_homopolymer_safe: bool = False,
        min_error_tolerance: str = "none",
    ) -> str:
        """
        Recommend best codec based on requirements.

        Args:
            require_gc_balance: Must maintain balanced GC content
            require_homopolymer_safe: Must prevent homopolymer runs
            min_error_tolerance: Minimum error tolerance level

        Returns:
            Recommended codec name
        """
        tolerance_order = {"none": 0, "low": 1, "medium": 2, "high": 3}
        min_tolerance = tolerance_order.get(min_error_tolerance, 0)

        best_codec = None
        best_score = -1

        for name, codec in self._codecs.items():
            # Check requirements
            if require_gc_balance and not codec.gc_balanced:
                continue
            if require_homopolymer_safe and not codec.homopolymer_safe:
                continue

            codec_tolerance = tolerance_order.get(codec.error_tolerance, 0)
            if codec_tolerance < min_tolerance:
                continue

            # Score based on bits per nucleotide (higher is better for density)
            score = codec.bits_per_nucleotide

            if score > best_score:
                best_score = score
                best_codec = name

        return best_codec or "quaternary"

    # Built-in encoder/decoder implementations

    @staticmethod
    def _quaternary_encode(binary: str) -> str:
        """Quaternary encoding: 2 bits per nucleotide."""
        if len(binary) % 2 != 0:
            binary += "0"

        result = []
        for i in range(0, len(binary), 2):
            bits = binary[i:i + 2]
            result.append(BIT_TO_NUCLEOTIDE[bits])

        return "".join(result)

    @staticmethod
    def _quaternary_decode(dna: str) -> str:
        """Quaternary decoding."""
        result = []
        for nucleotide in dna.upper():
            if nucleotide in NUCLEOTIDE_TO_BIT:
                result.append(NUCLEOTIDE_TO_BIT[nucleotide])
        return "".join(result)

    @staticmethod
    def _balanced_gc_encode(binary: str) -> str:
        """Balanced GC encoding with rotation."""
        if len(binary) % 2 != 0:
            binary += "0"

        result = []
        rotation = 0

        for i in range(0, len(binary), 2):
            bits = binary[i:i + 2]
            mapping = BALANCED_GC_MAPPINGS[rotation]
            result.append(mapping[bits])

            if (i // 2 + 1) % 4 == 0:
                rotation = (rotation + 1) % 4

        return "".join(result)

    @staticmethod
    def _balanced_gc_decode(dna: str) -> str:
        """Balanced GC decoding with rotation."""
        reverse_mappings = [
            {v: k for k, v in mapping.items()} for mapping in BALANCED_GC_MAPPINGS
        ]

        result = []
        rotation = 0

        for i, nucleotide in enumerate(dna.upper()):
            mapping = reverse_mappings[rotation]
            if nucleotide in mapping:
                result.append(mapping[nucleotide])

            if (i + 1) % 4 == 0:
                rotation = (rotation + 1) % 4

        return "".join(result)

    @staticmethod
    def _rll_encode(binary: str) -> str:
        """Run-length limited encoding."""
        if len(binary) % 2 != 0:
            binary += "0"

        result = []
        current_run = 0
        last_nucleotide = ""
        spacers = {"A": "C", "T": "G", "C": "A", "G": "T"}

        for i in range(0, len(binary), 2):
            bits = binary[i:i + 2]
            nucleotide = BIT_TO_NUCLEOTIDE[bits]

            if nucleotide == last_nucleotide:
                current_run += 1
                if current_run >= 3:
                    result.append(spacers[nucleotide])
                    current_run = 0
            else:
                current_run = 1
                last_nucleotide = nucleotide

            result.append(nucleotide)

        return "".join(result)

    @staticmethod
    def _rll_decode(dna: str) -> str:
        """Run-length limited decoding."""
        result = []
        run_count = 0
        last_nucleotide = ""

        for nucleotide in dna.upper():
            if nucleotide == last_nucleotide:
                run_count += 1
            else:
                run_count = 1
                last_nucleotide = nucleotide

            # Skip spacers (detected by run break patterns)
            if run_count > 3:
                run_count = 0
                last_nucleotide = ""
            elif nucleotide in NUCLEOTIDE_TO_BIT:
                result.append(NUCLEOTIDE_TO_BIT[nucleotide])

        return "".join(result)

    @staticmethod
    def _triplet_encode(binary: str) -> str:
        """Triplet encoding: 1 bit per 3 nucleotides."""
        result = []
        for bit in binary:
            result.append(TRIPLET_ENCODING[bit])
        return "".join(result)

    @staticmethod
    def _triplet_decode(dna: str) -> str:
        """Triplet decoding with majority voting."""
        result = []

        for i in range(0, len(dna), 3):
            triplet = dna[i:i + 3].upper()
            if len(triplet) < 3:
                break

            if triplet in TRIPLET_DECODING:
                result.append(TRIPLET_DECODING[triplet])
            else:
                # Majority voting for error recovery
                atc_score = sum(1 for j, c in enumerate(triplet) if c == "ATC"[j])
                gac_score = sum(1 for j, c in enumerate(triplet) if c == "GAC"[j])
                result.append("1" if gac_score > atc_score else "0")

        return "".join(result)


# Global registry instance
_registry: Optional[CodecRegistry] = None


def get_registry() -> CodecRegistry:
    """Get the global codec registry."""
    global _registry
    if _registry is None:
        _registry = CodecRegistry()
    return _registry


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
