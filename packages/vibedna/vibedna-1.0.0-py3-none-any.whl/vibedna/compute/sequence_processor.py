"""
VibeDNA Sequence Processor

DNA-native operations for processing and transforming sequences.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import List, Tuple, Callable, Optional
from enum import Enum


class TransformationType(Enum):
    """Available sequence transformations."""
    COMPLEMENT = "complement"
    REVERSE = "reverse"
    REVERSE_COMPLEMENT = "reverse_complement"
    TRANSCRIBE = "transcribe"
    TRANSLATE = "translate"


class SequenceProcessor:
    """
    Process DNA sequences with biologically-inspired operations.

    Provides transformations and analysis operations that
    mirror real DNA processing.

    Example:
        >>> proc = SequenceProcessor()
        >>> proc.complement("ATCG")
        'TAGC'
        >>> proc.reverse_complement("ATCG")
        'CGAT'
    """

    # Watson-Crick complement mapping
    COMPLEMENT_MAP = {"A": "T", "T": "A", "C": "G", "G": "C"}

    # DNA to RNA transcription
    TRANSCRIBE_MAP = {"A": "U", "T": "A", "C": "G", "G": "C"}

    # Codon table (simplified)
    CODON_TABLE = {
        "ATA": "I", "ATC": "I", "ATT": "I", "ATG": "M",
        "ACA": "T", "ACC": "T", "ACG": "T", "ACT": "T",
        "AAC": "N", "AAT": "N", "AAA": "K", "AAG": "K",
        "AGC": "S", "AGT": "S", "AGA": "R", "AGG": "R",
        "CTA": "L", "CTC": "L", "CTG": "L", "CTT": "L",
        "CCA": "P", "CCC": "P", "CCG": "P", "CCT": "P",
        "CAC": "H", "CAT": "H", "CAA": "Q", "CAG": "Q",
        "CGA": "R", "CGC": "R", "CGG": "R", "CGT": "R",
        "GTA": "V", "GTC": "V", "GTG": "V", "GTT": "V",
        "GCA": "A", "GCC": "A", "GCG": "A", "GCT": "A",
        "GAC": "D", "GAT": "D", "GAA": "E", "GAG": "E",
        "GGA": "G", "GGC": "G", "GGG": "G", "GGT": "G",
        "TCA": "S", "TCC": "S", "TCG": "S", "TCT": "S",
        "TTC": "F", "TTT": "F", "TTA": "L", "TTG": "L",
        "TAC": "Y", "TAT": "Y", "TAA": "*", "TAG": "*",
        "TGC": "C", "TGT": "C", "TGA": "*", "TGG": "W",
    }

    def complement(self, sequence: str) -> str:
        """
        Get Watson-Crick complement of sequence.

        A↔T, C↔G

        Args:
            sequence: DNA sequence

        Returns:
            Complement sequence
        """
        sequence = sequence.upper()
        return "".join(self.COMPLEMENT_MAP.get(n, n) for n in sequence)

    def reverse(self, sequence: str) -> str:
        """
        Reverse a sequence.

        Args:
            sequence: DNA sequence

        Returns:
            Reversed sequence
        """
        return sequence[::-1].upper()

    def reverse_complement(self, sequence: str) -> str:
        """
        Get reverse complement of sequence.

        Args:
            sequence: DNA sequence

        Returns:
            Reverse complement sequence
        """
        return self.reverse(self.complement(sequence))

    def transcribe(self, sequence: str) -> str:
        """
        Transcribe DNA to RNA.

        Args:
            sequence: DNA sequence

        Returns:
            RNA sequence (with U instead of T)
        """
        sequence = sequence.upper()
        return sequence.replace("T", "U")

    def translate(self, sequence: str, start: int = 0) -> str:
        """
        Translate DNA to amino acid sequence.

        Args:
            sequence: DNA sequence
            start: Starting position (frame)

        Returns:
            Amino acid sequence
        """
        sequence = sequence.upper()
        result = []

        for i in range(start, len(sequence) - 2, 3):
            codon = sequence[i:i + 3]
            amino_acid = self.CODON_TABLE.get(codon, "X")
            if amino_acid == "*":  # Stop codon
                break
            result.append(amino_acid)

        return "".join(result)

    def find_orfs(self, sequence: str) -> List[Tuple[int, int, str]]:
        """
        Find open reading frames (ORFs) in sequence.

        Args:
            sequence: DNA sequence

        Returns:
            List of (start, end, protein) tuples
        """
        sequence = sequence.upper()
        orfs = []

        for frame in range(3):
            i = frame
            while i < len(sequence) - 2:
                codon = sequence[i:i + 3]

                if codon == "ATG":  # Start codon
                    start = i
                    j = i + 3

                    while j < len(sequence) - 2:
                        next_codon = sequence[j:j + 3]
                        if next_codon in ("TAA", "TAG", "TGA"):
                            protein = self.translate(sequence[start:j + 3])
                            orfs.append((start, j + 3, protein))
                            break
                        j += 3

                i += 3

        return orfs

    def gc_content(self, sequence: str) -> float:
        """
        Calculate GC content of sequence.

        Args:
            sequence: DNA sequence

        Returns:
            GC content as fraction (0.0 to 1.0)
        """
        sequence = sequence.upper()
        if not sequence:
            return 0.0

        gc_count = sum(1 for n in sequence if n in "GC")
        return gc_count / len(sequence)

    def count_nucleotides(self, sequence: str) -> dict:
        """
        Count occurrences of each nucleotide.

        Args:
            sequence: DNA sequence

        Returns:
            Dictionary with counts for A, T, C, G
        """
        sequence = sequence.upper()
        return {
            "A": sequence.count("A"),
            "T": sequence.count("T"),
            "C": sequence.count("C"),
            "G": sequence.count("G"),
        }

    def find_motif(self, sequence: str, motif: str) -> List[int]:
        """
        Find all occurrences of a motif in sequence.

        Args:
            sequence: DNA sequence to search
            motif: Pattern to find

        Returns:
            List of starting positions
        """
        sequence = sequence.upper()
        motif = motif.upper()
        positions = []

        start = 0
        while True:
            pos = sequence.find(motif, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1

        return positions

    def hamming_distance(self, seq_a: str, seq_b: str) -> int:
        """
        Calculate Hamming distance between sequences.

        Args:
            seq_a: First sequence
            seq_b: Second sequence

        Returns:
            Number of differing positions

        Raises:
            ValueError: If sequences have different lengths
        """
        seq_a = seq_a.upper()
        seq_b = seq_b.upper()

        if len(seq_a) != len(seq_b):
            raise ValueError("Sequences must have equal length")

        return sum(a != b for a, b in zip(seq_a, seq_b))

    def consensus(self, sequences: List[str]) -> Tuple[str, dict]:
        """
        Find consensus sequence from multiple sequences.

        Args:
            sequences: List of aligned sequences

        Returns:
            Tuple of (consensus_sequence, profile_matrix)
        """
        if not sequences:
            return "", {}

        sequences = [s.upper() for s in sequences]
        length = len(sequences[0])

        profile = {"A": [], "T": [], "C": [], "G": []}
        consensus = []

        for i in range(length):
            counts = {"A": 0, "T": 0, "C": 0, "G": 0}

            for seq in sequences:
                if i < len(seq) and seq[i] in counts:
                    counts[seq[i]] += 1

            for n in profile:
                profile[n].append(counts[n])

            consensus.append(max(counts.keys(), key=lambda k: counts[k]))

        return "".join(consensus), profile

    def chunk(self, sequence: str, size: int) -> List[str]:
        """
        Split sequence into chunks.

        Args:
            sequence: DNA sequence
            size: Chunk size

        Returns:
            List of sequence chunks
        """
        return [sequence[i:i + size] for i in range(0, len(sequence), size)]

    def join(self, sequences: List[str], separator: str = "") -> str:
        """
        Join multiple sequences.

        Args:
            sequences: List of DNA sequences
            separator: Optional separator between sequences

        Returns:
            Joined sequence
        """
        return separator.join(s.upper() for s in sequences)

    def pad(self, sequence: str, length: int, nucleotide: str = "A") -> str:
        """
        Pad sequence to specified length.

        Args:
            sequence: DNA sequence
            length: Target length
            nucleotide: Nucleotide to pad with

        Returns:
            Padded sequence
        """
        sequence = sequence.upper()
        if len(sequence) >= length:
            return sequence

        padding = nucleotide.upper() * (length - len(sequence))
        return sequence + padding

    def trim(self, sequence: str, nucleotide: str = "A") -> str:
        """
        Trim trailing nucleotides from sequence.

        Args:
            sequence: DNA sequence
            nucleotide: Nucleotide to trim

        Returns:
            Trimmed sequence
        """
        sequence = sequence.upper()
        return sequence.rstrip(nucleotide.upper())

    def map_sequence(
        self,
        sequence: str,
        transform: Callable[[str], str]
    ) -> str:
        """
        Apply transformation to each nucleotide.

        Args:
            sequence: DNA sequence
            transform: Function to apply to each nucleotide

        Returns:
            Transformed sequence
        """
        return "".join(transform(n) for n in sequence.upper())

    def filter_sequence(
        self,
        sequence: str,
        predicate: Callable[[str], bool]
    ) -> str:
        """
        Filter nucleotides based on predicate.

        Args:
            sequence: DNA sequence
            predicate: Function that returns True to keep nucleotide

        Returns:
            Filtered sequence
        """
        return "".join(n for n in sequence.upper() if predicate(n))


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
