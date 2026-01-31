"""
VibeDNA Index Catalog

Indexing and fast retrieval for DNA sequences.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class IndexEntry:
    """Entry in the sequence index."""
    sequence_id: str
    position: int
    length: int


class IndexCatalog:
    """
    Index DNA sequences for fast retrieval.

    Uses k-mer indexing for efficient sequence search
    and similarity matching.

    Example:
        >>> catalog = IndexCatalog(kmer_size=4)
        >>> catalog.add("seq1", "ATCGATCGATCG")
        >>> matches = catalog.search("ATCG")
        >>> print(matches)
        [('seq1', 0), ('seq1', 4), ('seq1', 8)]
    """

    def __init__(self, kmer_size: int = 4):
        """
        Initialize index catalog.

        Args:
            kmer_size: Size of k-mers for indexing
        """
        self.kmer_size = kmer_size

        # k-mer to sequence positions index
        self._kmer_index: Dict[str, List[IndexEntry]] = defaultdict(list)

        # Sequence storage
        self._sequences: Dict[str, str] = {}

        # Reverse index: sequence_id → k-mers
        self._sequence_kmers: Dict[str, Set[str]] = defaultdict(set)

    def add(self, sequence_id: str, sequence: str) -> int:
        """
        Add sequence to the index.

        Args:
            sequence_id: Unique identifier for the sequence
            sequence: DNA sequence to index

        Returns:
            Number of k-mers indexed
        """
        sequence = sequence.upper()
        self._sequences[sequence_id] = sequence

        kmer_count = 0

        # Extract and index k-mers
        for i in range(len(sequence) - self.kmer_size + 1):
            kmer = sequence[i:i + self.kmer_size]

            entry = IndexEntry(
                sequence_id=sequence_id,
                position=i,
                length=self.kmer_size,
            )

            self._kmer_index[kmer].append(entry)
            self._sequence_kmers[sequence_id].add(kmer)
            kmer_count += 1

        return kmer_count

    def remove(self, sequence_id: str) -> bool:
        """
        Remove sequence from the index.

        Args:
            sequence_id: ID of sequence to remove

        Returns:
            True if removed
        """
        if sequence_id not in self._sequences:
            return False

        # Remove from k-mer index
        for kmer in self._sequence_kmers[sequence_id]:
            self._kmer_index[kmer] = [
                e for e in self._kmer_index[kmer]
                if e.sequence_id != sequence_id
            ]
            if not self._kmer_index[kmer]:
                del self._kmer_index[kmer]

        # Remove from other indexes
        del self._sequences[sequence_id]
        del self._sequence_kmers[sequence_id]

        return True

    def search(self, query: str) -> List[Tuple[str, int]]:
        """
        Search for sequences containing the query.

        Args:
            query: DNA sequence to search for

        Returns:
            List of (sequence_id, position) tuples
        """
        query = query.upper()
        results = []

        # If query is shorter than k-mer size, do direct search
        if len(query) < self.kmer_size:
            for seq_id, sequence in self._sequences.items():
                pos = 0
                while True:
                    pos = sequence.find(query, pos)
                    if pos == -1:
                        break
                    results.append((seq_id, pos))
                    pos += 1
            return results

        # Use k-mer index for longer queries
        first_kmer = query[:self.kmer_size]

        if first_kmer not in self._kmer_index:
            return []

        # Check each potential match
        for entry in self._kmer_index[first_kmer]:
            sequence = self._sequences.get(entry.sequence_id, "")
            pos = entry.position

            # Verify full query matches at this position
            if pos + len(query) <= len(sequence):
                if sequence[pos:pos + len(query)] == query:
                    results.append((entry.sequence_id, pos))

        return results

    def find_similar(
        self,
        query: str,
        min_similarity: float = 0.8
    ) -> List[Tuple[str, float]]:
        """
        Find sequences similar to query.

        Uses Jaccard similarity on k-mer sets.

        Args:
            query: DNA sequence to compare
            min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of (sequence_id, similarity) tuples
        """
        query = query.upper()

        # Get query k-mers
        query_kmers = set()
        for i in range(len(query) - self.kmer_size + 1):
            query_kmers.add(query[i:i + self.kmer_size])

        results = []

        for seq_id, seq_kmers in self._sequence_kmers.items():
            # Calculate Jaccard similarity
            intersection = len(query_kmers & seq_kmers)
            union = len(query_kmers | seq_kmers)

            if union > 0:
                similarity = intersection / union
                if similarity >= min_similarity:
                    results.append((seq_id, similarity))

        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_sequence(self, sequence_id: str) -> Optional[str]:
        """
        Get sequence by ID.

        Args:
            sequence_id: Sequence ID

        Returns:
            DNA sequence or None
        """
        return self._sequences.get(sequence_id)

    def get_kmer_frequency(self, kmer: str) -> int:
        """
        Get frequency of a k-mer across all sequences.

        Args:
            kmer: K-mer to count

        Returns:
            Number of occurrences
        """
        kmer = kmer.upper()
        return len(self._kmer_index.get(kmer, []))

    def get_stats(self) -> dict:
        """
        Get index statistics.

        Returns:
            Dictionary with index statistics
        """
        total_kmers = sum(len(entries) for entries in self._kmer_index.values())
        unique_kmers = len(self._kmer_index)

        return {
            "sequence_count": len(self._sequences),
            "unique_kmers": unique_kmers,
            "total_kmer_entries": total_kmers,
            "kmer_size": self.kmer_size,
            "avg_kmers_per_sequence": total_kmers / len(self._sequences) if self._sequences else 0,
        }

    def rebuild_index(self) -> int:
        """
        Rebuild the entire index.

        Returns:
            Number of k-mers indexed
        """
        # Clear existing index
        self._kmer_index.clear()
        self._sequence_kmers.clear()

        # Store sequences temporarily
        sequences = dict(self._sequences)
        self._sequences.clear()

        # Re-add all sequences
        total_kmers = 0
        for seq_id, sequence in sequences.items():
            total_kmers += self.add(seq_id, sequence)

        return total_kmers


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
