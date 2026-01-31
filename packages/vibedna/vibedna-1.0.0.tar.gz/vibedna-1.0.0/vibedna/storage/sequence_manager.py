"""
VibeDNA Sequence Manager

CRUD operations for DNA sequences.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import hashlib


@dataclass
class DNASequenceRecord:
    """Record for a stored DNA sequence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    sequence: str = ""
    length: int = 0
    checksum: str = ""
    gc_content: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    modified_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SequenceManager:
    """
    Manage DNA sequence storage and retrieval.

    Provides CRUD operations for raw DNA sequences
    without the full file system overhead.

    Example:
        >>> manager = SequenceManager()
        >>> record = manager.create("ATCGATCG", name="test")
        >>> retrieved = manager.get(record.id)
        >>> print(retrieved.sequence)
        ATCGATCG
    """

    def __init__(self):
        """Initialize sequence manager."""
        self._sequences: Dict[str, DNASequenceRecord] = {}
        self._name_index: Dict[str, str] = {}  # name → id

    def create(
        self,
        sequence: str,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DNASequenceRecord:
        """
        Create and store a new sequence.

        Args:
            sequence: DNA sequence to store
            name: Optional name for the sequence
            tags: Optional tags
            metadata: Optional metadata

        Returns:
            Created sequence record
        """
        sequence = sequence.upper()

        # Calculate properties
        length = len(sequence)
        checksum = self._compute_checksum(sequence)
        gc_content = self._calculate_gc_content(sequence)

        record = DNASequenceRecord(
            name=name or f"seq_{uuid.uuid4().hex[:8]}",
            sequence=sequence,
            length=length,
            checksum=checksum,
            gc_content=gc_content,
            tags=tags or [],
            metadata=metadata or {},
        )

        self._sequences[record.id] = record
        self._name_index[record.name] = record.id

        return record

    def get(self, id: str) -> Optional[DNASequenceRecord]:
        """
        Get a sequence by ID.

        Args:
            id: Sequence ID

        Returns:
            Sequence record or None
        """
        return self._sequences.get(id)

    def get_by_name(self, name: str) -> Optional[DNASequenceRecord]:
        """
        Get a sequence by name.

        Args:
            name: Sequence name

        Returns:
            Sequence record or None
        """
        id = self._name_index.get(name)
        if id:
            return self._sequences.get(id)
        return None

    def update(
        self,
        id: str,
        sequence: Optional[str] = None,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[DNASequenceRecord]:
        """
        Update a sequence record.

        Args:
            id: Sequence ID
            sequence: New sequence (optional)
            name: New name (optional)
            tags: New tags (optional)
            metadata: New metadata (optional)

        Returns:
            Updated record or None
        """
        record = self._sequences.get(id)
        if not record:
            return None

        if sequence is not None:
            sequence = sequence.upper()
            record.sequence = sequence
            record.length = len(sequence)
            record.checksum = self._compute_checksum(sequence)
            record.gc_content = self._calculate_gc_content(sequence)

        if name is not None:
            # Update name index
            del self._name_index[record.name]
            record.name = name
            self._name_index[name] = id

        if tags is not None:
            record.tags = tags

        if metadata is not None:
            record.metadata = metadata

        record.modified_at = datetime.utcnow()
        return record

    def delete(self, id: str) -> bool:
        """
        Delete a sequence.

        Args:
            id: Sequence ID

        Returns:
            True if deleted
        """
        record = self._sequences.get(id)
        if not record:
            return False

        del self._name_index[record.name]
        del self._sequences[id]
        return True

    def list_all(self) -> List[DNASequenceRecord]:
        """
        List all sequences.

        Returns:
            List of all sequence records
        """
        return list(self._sequences.values())

    def search(
        self,
        name_pattern: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> List[DNASequenceRecord]:
        """
        Search for sequences.

        Args:
            name_pattern: Pattern to match in name
            min_length: Minimum sequence length
            max_length: Maximum sequence length
            tags: Tags to match (any)

        Returns:
            List of matching records
        """
        results = []

        for record in self._sequences.values():
            # Name filter
            if name_pattern and name_pattern.lower() not in record.name.lower():
                continue

            # Length filters
            if min_length and record.length < min_length:
                continue
            if max_length and record.length > max_length:
                continue

            # Tags filter
            if tags and not any(t in record.tags for t in tags):
                continue

            results.append(record)

        return results

    def find_by_fragment(self, fragment: str) -> List[DNASequenceRecord]:
        """
        Find sequences containing a fragment.

        Args:
            fragment: DNA fragment to search for

        Returns:
            List of matching records
        """
        fragment = fragment.upper()
        results = []

        for record in self._sequences.values():
            if fragment in record.sequence:
                results.append(record)

        return results

    def _compute_checksum(self, sequence: str) -> str:
        """Compute checksum for sequence."""
        return hashlib.sha256(sequence.encode()).hexdigest()[:16]

    def _calculate_gc_content(self, sequence: str) -> float:
        """Calculate GC content."""
        if not sequence:
            return 0.0
        gc_count = sum(1 for n in sequence if n in "GC")
        return gc_count / len(sequence)


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
