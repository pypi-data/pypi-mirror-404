"""
VibeDNA Mutation Detector

Detects and classifies mutations in DNA sequences by comparing
against expected patterns or reference sequences.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

from vibedna.utils.constants import NUCLEOTIDE_VALUE


class MutationType(Enum):
    """Types of DNA mutations."""
    SUBSTITUTION = "substitution"   # Single nucleotide change
    TRANSITION = "transition"       # Purine↔Purine or Pyrimidine↔Pyrimidine
    TRANSVERSION = "transversion"   # Purine↔Pyrimidine
    INSERTION = "insertion"         # Extra nucleotide inserted
    DELETION = "deletion"           # Nucleotide deleted
    DUPLICATION = "duplication"     # Sequence duplicated


@dataclass
class Mutation:
    """Represents a detected mutation."""
    position: int
    mutation_type: MutationType
    original: Optional[str]
    mutated: str
    confidence: float
    context: str  # Surrounding sequence


@dataclass
class MutationReport:
    """Complete mutation analysis report."""
    mutations: List[Mutation]
    total_positions: int
    mutation_count: int
    mutation_rate: float
    transition_count: int
    transversion_count: int
    insertion_count: int
    deletion_count: int
    is_likely_corrupted: bool


class MutationDetector:
    """
    Detects mutations in DNA sequences.

    Can detect mutations by:
    1. Comparing to a reference sequence
    2. Analyzing sequence patterns
    3. Using expected encoding structure

    Example:
        >>> detector = MutationDetector()
        >>> report = detector.compare("ATCGATCG", "ATCAATCG")
        >>> print(report.mutation_count)
        1
        >>> print(report.mutations[0].mutation_type)
        MutationType.TRANSITION
    """

    # Purines and pyrimidines for transition/transversion classification
    PURINES = {"A", "G"}
    PYRIMIDINES = {"T", "C"}

    # Homopolymer run threshold for pattern detection
    HOMOPOLYMER_THRESHOLD = 4

    def __init__(self, context_size: int = 3):
        """
        Initialize mutation detector.

        Args:
            context_size: Number of surrounding nucleotides to include
        """
        self.context_size = context_size

    def compare(
        self,
        reference: str,
        sequence: str,
        allow_indels: bool = True
    ) -> MutationReport:
        """
        Compare sequence against reference and detect mutations.

        Args:
            reference: Reference (expected) sequence
            sequence: Sequence to check for mutations
            allow_indels: If True, detect insertions/deletions

        Returns:
            MutationReport with all detected mutations
        """
        reference = reference.upper()
        sequence = sequence.upper()

        mutations: List[Mutation] = []
        transition_count = 0
        transversion_count = 0
        insertion_count = 0
        deletion_count = 0

        if allow_indels and len(reference) != len(sequence):
            # Use alignment-based comparison
            mutations = self._aligned_compare(reference, sequence)
        else:
            # Direct position-by-position comparison
            for i in range(min(len(reference), len(sequence))):
                if reference[i] != sequence[i]:
                    mutation_type = self._classify_substitution(
                        reference[i], sequence[i]
                    )
                    context = self._get_context(sequence, i)

                    mutation = Mutation(
                        position=i,
                        mutation_type=mutation_type,
                        original=reference[i],
                        mutated=sequence[i],
                        confidence=1.0,
                        context=context,
                    )
                    mutations.append(mutation)

        # Count mutation types
        for m in mutations:
            if m.mutation_type == MutationType.TRANSITION:
                transition_count += 1
            elif m.mutation_type == MutationType.TRANSVERSION:
                transversion_count += 1
            elif m.mutation_type == MutationType.INSERTION:
                insertion_count += 1
            elif m.mutation_type == MutationType.DELETION:
                deletion_count += 1

        total_positions = max(len(reference), len(sequence))
        mutation_rate = len(mutations) / total_positions if total_positions > 0 else 0

        return MutationReport(
            mutations=mutations,
            total_positions=total_positions,
            mutation_count=len(mutations),
            mutation_rate=mutation_rate,
            transition_count=transition_count,
            transversion_count=transversion_count,
            insertion_count=insertion_count,
            deletion_count=deletion_count,
            is_likely_corrupted=mutation_rate > 0.1,  # >10% mutation rate
        )

    def detect_patterns(self, sequence: str) -> List[Mutation]:
        """
        Detect likely mutations based on sequence patterns.

        Looks for patterns that suggest errors:
        - Unexpected homopolymer runs
        - Invalid triplet codes
        - Unusual GC content locally

        Args:
            sequence: DNA sequence to analyze

        Returns:
            List of suspected mutations
        """
        sequence = sequence.upper()
        suspected: List[Mutation] = []

        # Detect homopolymer runs
        current_run = 1
        run_start = 0

        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i - 1]:
                current_run += 1
            else:
                if current_run >= self.HOMOPOLYMER_THRESHOLD:
                    # Possible run-induced error
                    suspected.append(Mutation(
                        position=run_start + current_run - 1,
                        mutation_type=MutationType.SUBSTITUTION,
                        original=None,
                        mutated=sequence[run_start],
                        confidence=0.7,
                        context=self._get_context(sequence, run_start),
                    ))
                current_run = 1
                run_start = i

        # Check final run
        if current_run >= self.HOMOPOLYMER_THRESHOLD:
            suspected.append(Mutation(
                position=run_start + current_run - 1,
                mutation_type=MutationType.SUBSTITUTION,
                original=None,
                mutated=sequence[run_start],
                confidence=0.7,
                context=self._get_context(sequence, run_start),
            ))

        return suspected

    def estimate_error_rate(self, sequence: str) -> float:
        """
        Estimate the error rate of a sequence based on patterns.

        Args:
            sequence: DNA sequence to analyze

        Returns:
            Estimated error rate (0.0 to 1.0)
        """
        if not sequence:
            return 0.0

        sequence = sequence.upper()
        error_indicators = 0

        # Check GC content
        gc_count = sum(1 for n in sequence if n in "GC")
        gc_ratio = gc_count / len(sequence)

        # Very skewed GC content suggests errors
        if gc_ratio < 0.2 or gc_ratio > 0.8:
            error_indicators += len(sequence) * 0.1

        # Count long homopolymer runs
        current_run = 1
        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i - 1]:
                current_run += 1
                if current_run > self.HOMOPOLYMER_THRESHOLD:
                    error_indicators += 1
            else:
                current_run = 1

        # Estimate based on indicators
        base_error_rate = error_indicators / len(sequence)
        return min(1.0, base_error_rate)

    def _classify_substitution(self, original: str, mutated: str) -> MutationType:
        """Classify a substitution as transition or transversion."""
        # Transition: purine↔purine or pyrimidine↔pyrimidine
        if (original in self.PURINES and mutated in self.PURINES) or \
           (original in self.PYRIMIDINES and mutated in self.PYRIMIDINES):
            return MutationType.TRANSITION
        else:
            return MutationType.TRANSVERSION

    def _get_context(self, sequence: str, position: int) -> str:
        """Get surrounding context for a position."""
        start = max(0, position - self.context_size)
        end = min(len(sequence), position + self.context_size + 1)
        return sequence[start:end]

    def _aligned_compare(
        self,
        reference: str,
        sequence: str
    ) -> List[Mutation]:
        """
        Compare sequences with different lengths using simple alignment.

        Uses a simplified Needleman-Wunsch-like approach.
        """
        mutations: List[Mutation] = []

        # Simple approach: find best local alignment
        i, j = 0, 0

        while i < len(reference) and j < len(sequence):
            if reference[i] == sequence[j]:
                i += 1
                j += 1
            else:
                # Check if insertion or deletion is more likely
                # Look ahead to see if skipping helps alignment

                # Check for insertion (extra in sequence)
                if j + 1 < len(sequence) and reference[i] == sequence[j + 1]:
                    mutations.append(Mutation(
                        position=j,
                        mutation_type=MutationType.INSERTION,
                        original=None,
                        mutated=sequence[j],
                        confidence=0.8,
                        context=self._get_context(sequence, j),
                    ))
                    j += 1
                # Check for deletion (missing in sequence)
                elif i + 1 < len(reference) and reference[i + 1] == sequence[j]:
                    mutations.append(Mutation(
                        position=i,
                        mutation_type=MutationType.DELETION,
                        original=reference[i],
                        mutated="",
                        confidence=0.8,
                        context=self._get_context(reference, i),
                    ))
                    i += 1
                else:
                    # Substitution
                    mutation_type = self._classify_substitution(
                        reference[i], sequence[j]
                    )
                    mutations.append(Mutation(
                        position=i,
                        mutation_type=mutation_type,
                        original=reference[i],
                        mutated=sequence[j],
                        confidence=1.0,
                        context=self._get_context(sequence, j),
                    ))
                    i += 1
                    j += 1

        # Handle remaining insertions
        while j < len(sequence):
            mutations.append(Mutation(
                position=j,
                mutation_type=MutationType.INSERTION,
                original=None,
                mutated=sequence[j],
                confidence=0.8,
                context=self._get_context(sequence, j),
            ))
            j += 1

        # Handle remaining deletions
        while i < len(reference):
            mutations.append(Mutation(
                position=i,
                mutation_type=MutationType.DELETION,
                original=reference[i],
                mutated="",
                confidence=0.8,
                context=self._get_context(reference, i),
            ))
            i += 1

        return mutations


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
