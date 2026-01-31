"""
VibeDNA Parallel Strands - Multi-Strand Parallel Operations

Implements parallel processing on multiple DNA strands,
mimicking biological parallel computation.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import List, Tuple, Callable, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from vibedna.compute.dna_logic_gates import DNAComputeEngine, DNALogicGate


@dataclass
class StrandResult:
    """Result from a strand operation."""
    strand_id: int
    sequence: str
    result: Any
    success: bool
    error: Optional[str] = None


class ParallelStrandProcessor:
    """
    Process multiple DNA strands in parallel.

    Mimics the massively parallel nature of DNA computing,
    where millions of strands can process simultaneously.

    Example:
        >>> processor = ParallelStrandProcessor(workers=4)
        >>> strands = ["ATCG", "GCTA", "AATT", "GGCC"]
        >>> results = processor.apply_all(strands, lambda s: s[::-1])
        >>> print([r.result for r in results])
        ['GCTA', 'ATCG', 'TTAA', 'CCGG']
    """

    def __init__(self, workers: int = 4):
        """
        Initialize parallel processor.

        Args:
            workers: Number of parallel workers
        """
        self.workers = workers
        self._engine = DNAComputeEngine()
        self._lock = threading.Lock()

    def apply_all(
        self,
        strands: List[str],
        operation: Callable[[str], Any]
    ) -> List[StrandResult]:
        """
        Apply operation to all strands in parallel.

        Args:
            strands: List of DNA sequences
            operation: Function to apply to each strand

        Returns:
            List of StrandResult objects
        """
        results: List[StrandResult] = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self._process_strand, i, strand, operation): i
                for i, strand in enumerate(strands)
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        # Sort by strand_id to maintain order
        results.sort(key=lambda r: r.strand_id)
        return results

    def _process_strand(
        self,
        strand_id: int,
        sequence: str,
        operation: Callable[[str], Any]
    ) -> StrandResult:
        """Process a single strand."""
        try:
            result = operation(sequence.upper())
            return StrandResult(
                strand_id=strand_id,
                sequence=sequence,
                result=result,
                success=True,
            )
        except Exception as e:
            return StrandResult(
                strand_id=strand_id,
                sequence=sequence,
                result=None,
                success=False,
                error=str(e),
            )

    def map_gate(
        self,
        strands_a: List[str],
        strands_b: List[str],
        gate: DNALogicGate
    ) -> List[str]:
        """
        Apply logic gate pairwise across strand lists.

        Args:
            strands_a: First list of strands
            strands_b: Second list of strands
            gate: Logic gate to apply

        Returns:
            List of result strands
        """
        if len(strands_a) != len(strands_b):
            raise ValueError("Strand lists must have equal length")

        def apply_gate(pair: Tuple[str, str]) -> str:
            return self._engine.apply_gate(gate, pair[0], pair[1])

        pairs = list(zip(strands_a, strands_b))
        results = self.apply_all(
            [f"{a}|{b}" for a, b in pairs],
            lambda p: apply_gate(tuple(p.split("|")))
        )

        return [r.result for r in results if r.success]

    def reduce(
        self,
        strands: List[str],
        operation: Callable[[str, str], str]
    ) -> str:
        """
        Reduce strands using binary operation.

        Args:
            strands: List of strands to reduce
            operation: Binary operation (takes 2 strands, returns 1)

        Returns:
            Single reduced strand
        """
        if not strands:
            raise ValueError("Cannot reduce empty list")

        if len(strands) == 1:
            return strands[0]

        # Parallel tree reduction
        current = strands

        while len(current) > 1:
            pairs = []
            for i in range(0, len(current) - 1, 2):
                pairs.append((current[i], current[i + 1]))

            # Handle odd strand
            if len(current) % 2 == 1:
                odd_strand = current[-1]
            else:
                odd_strand = None

            # Process pairs in parallel
            results = self.apply_all(
                [f"{a}|{b}" for a, b in pairs],
                lambda p: operation(*p.split("|"))
            )

            current = [r.result for r in results if r.success]

            if odd_strand:
                current.append(odd_strand)

        return current[0]

    def xor_reduce(self, strands: List[str]) -> str:
        """
        XOR all strands together.

        Args:
            strands: List of strands

        Returns:
            XOR of all strands
        """
        return self.reduce(
            strands,
            lambda a, b: self._engine.apply_gate(DNALogicGate.XOR, a, b)
        )

    def and_reduce(self, strands: List[str]) -> str:
        """
        AND all strands together.

        Args:
            strands: List of strands

        Returns:
            AND of all strands
        """
        return self.reduce(
            strands,
            lambda a, b: self._engine.apply_gate(DNALogicGate.AND, a, b)
        )

    def or_reduce(self, strands: List[str]) -> str:
        """
        OR all strands together.

        Args:
            strands: List of strands

        Returns:
            OR of all strands
        """
        return self.reduce(
            strands,
            lambda a, b: self._engine.apply_gate(DNALogicGate.OR, a, b)
        )

    def filter_strands(
        self,
        strands: List[str],
        predicate: Callable[[str], bool]
    ) -> List[str]:
        """
        Filter strands based on predicate.

        Args:
            strands: List of strands
            predicate: Function that returns True to keep strand

        Returns:
            Filtered list of strands
        """
        results = self.apply_all(strands, predicate)
        return [
            r.sequence for r in results
            if r.success and r.result
        ]

    def sort_strands(
        self,
        strands: List[str],
        key: Optional[Callable[[str], Any]] = None,
        reverse: bool = False
    ) -> List[str]:
        """
        Sort strands.

        Args:
            strands: List of strands to sort
            key: Optional sort key function
            reverse: If True, sort in descending order

        Returns:
            Sorted list of strands
        """
        if key is None:
            # Sort by numeric value
            key = lambda s: self._engine._dna_to_int(s)

        return sorted(strands, key=key, reverse=reverse)

    def broadcast(
        self,
        strand: str,
        targets: List[str],
        operation: Callable[[str, str], str]
    ) -> List[str]:
        """
        Apply operation between single strand and all targets.

        Args:
            strand: Source strand
            targets: Target strands
            operation: Binary operation

        Returns:
            List of result strands
        """
        results = self.apply_all(
            targets,
            lambda t: operation(strand, t)
        )
        return [r.result for r in results if r.success]

    def select(
        self,
        strands: List[str],
        indices: List[int]
    ) -> List[str]:
        """
        Select strands at specified indices.

        Args:
            strands: Source strands
            indices: Indices to select

        Returns:
            Selected strands
        """
        return [strands[i] for i in indices if 0 <= i < len(strands)]

    def duplicate(self, strand: str, count: int) -> List[str]:
        """
        Duplicate a strand multiple times.

        Mimics DNA replication.

        Args:
            strand: Strand to duplicate
            count: Number of copies

        Returns:
            List of duplicate strands
        """
        return [strand.upper()] * count

    def hybridize(
        self,
        forward: List[str],
        reverse: List[str]
    ) -> List[Tuple[str, str]]:
        """
        Find complementary strand pairs.

        Mimics DNA hybridization.

        Args:
            forward: Forward strands
            reverse: Reverse strands

        Returns:
            List of complementary pairs
        """
        from vibedna.compute.sequence_processor import SequenceProcessor
        proc = SequenceProcessor()

        pairs = []
        for fwd in forward:
            complement = proc.reverse_complement(fwd)
            for rev in reverse:
                if rev.upper() == complement:
                    pairs.append((fwd, rev))

        return pairs


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
