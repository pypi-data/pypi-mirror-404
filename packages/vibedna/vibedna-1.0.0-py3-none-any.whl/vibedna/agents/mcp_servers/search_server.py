# VibeDNA Search MCP Server
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Search MCP Server for VibeDNA sequence and file indexing.

Provides tools for:
- Full-text search across files and metadata
- Sequence similarity search
- Historical workflow lookup
- Catalog management
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import hashlib

from vibedna.agents.mcp_servers.base_server import (
    BaseMCPServer,
    MCPServerConfig,
    MCPTool,
    MCPToolParameter,
    MCPResource,
    TransportType,
)


@dataclass
class IndexEntry:
    """Entry in the search index."""
    id: str
    path: str
    name: str
    mime_type: str
    tags: List[str]
    metadata: Dict[str, Any]
    content_hash: str
    sequence_signature: Optional[bytes] = None
    indexed_at: datetime = field(default_factory=datetime.utcnow)


class VibeDNASearchMCPServer(BaseMCPServer):
    """
    Search MCP Server for indexing and search operations.

    Tools:
    - search: Full-text search across files
    - similarity_search: Find similar sequences
    - index_file: Add file to search index
    - remove_from_index: Remove file from index
    - get_index_stats: Get indexing statistics
    """

    def __init__(self, config: Optional[MCPServerConfig] = None):
        """Initialize the Search MCP server."""
        if config is None:
            config = MCPServerConfig(
                name="vibedna-search",
                version="1.0.0",
                description="Search and indexing MCP server",
                transport=TransportType.SSE,
                url="https://mcp.vibedna.vibecaas.com/search",
                port=8093,
            )
        super().__init__(config)

        # Initialize in-memory index (would use Elasticsearch in production)
        self._index: Dict[str, IndexEntry] = {}
        self._full_text_index: Dict[str, Set[str]] = {}  # term -> set of ids
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> set of ids

    def _register_tools(self) -> None:
        """Register search tools."""

        # search tool
        self.register_tool(MCPTool(
            name="search",
            description="Full-text search across indexed files",
            parameters=[
                MCPToolParameter(
                    name="query",
                    param_type="string",
                    description="Search query",
                    required=True,
                ),
                MCPToolParameter(
                    name="path_prefix",
                    param_type="string",
                    description="Limit search to path prefix",
                    required=False,
                    default="/",
                ),
                MCPToolParameter(
                    name="mime_types",
                    param_type="array",
                    description="Filter by MIME types",
                    required=False,
                ),
                MCPToolParameter(
                    name="tags",
                    param_type="array",
                    description="Filter by tags",
                    required=False,
                ),
                MCPToolParameter(
                    name="limit",
                    param_type="integer",
                    description="Maximum results to return",
                    required=False,
                    default=100,
                ),
            ],
            handler=self._search,
        ))

        # similarity_search tool
        self.register_tool(MCPTool(
            name="similarity_search",
            description="Find sequences similar to a given sequence",
            parameters=[
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence to find similar sequences for",
                    required=True,
                ),
                MCPToolParameter(
                    name="threshold",
                    param_type="number",
                    description="Similarity threshold (0.0 to 1.0)",
                    required=False,
                    default=0.8,
                ),
                MCPToolParameter(
                    name="limit",
                    param_type="integer",
                    description="Maximum results to return",
                    required=False,
                    default=10,
                ),
            ],
            handler=self._similarity_search,
        ))

        # index_file tool
        self.register_tool(MCPTool(
            name="index_file",
            description="Add or update a file in the search index",
            parameters=[
                MCPToolParameter(
                    name="id",
                    param_type="string",
                    description="Unique file ID",
                    required=True,
                ),
                MCPToolParameter(
                    name="path",
                    param_type="string",
                    description="File path",
                    required=True,
                ),
                MCPToolParameter(
                    name="name",
                    param_type="string",
                    description="File name",
                    required=True,
                ),
                MCPToolParameter(
                    name="mime_type",
                    param_type="string",
                    description="MIME type",
                    required=False,
                    default="application/octet-stream",
                ),
                MCPToolParameter(
                    name="tags",
                    param_type="array",
                    description="Tags for the file",
                    required=False,
                ),
                MCPToolParameter(
                    name="metadata",
                    param_type="object",
                    description="Additional metadata",
                    required=False,
                ),
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence for similarity indexing",
                    required=False,
                ),
            ],
            handler=self._index_file,
        ))

        # remove_from_index tool
        self.register_tool(MCPTool(
            name="remove_from_index",
            description="Remove a file from the search index",
            parameters=[
                MCPToolParameter(
                    name="id",
                    param_type="string",
                    description="File ID to remove",
                    required=True,
                ),
            ],
            handler=self._remove_from_index,
        ))

        # get_index_stats tool
        self.register_tool(MCPTool(
            name="get_index_stats",
            description="Get statistics about the search index",
            parameters=[],
            handler=self._get_index_stats,
        ))

    def _register_resources(self) -> None:
        """Register search resources."""

        self.register_resource(MCPResource(
            name="index_status",
            description="Search index status",
            uri="vibedna://search/status",
            mime_type="application/json",
            handler=self._get_index_status,
        ))

    async def _search(
        self,
        query: str,
        path_prefix: str = "/",
        mime_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Perform full-text search."""
        try:
            # Tokenize query
            terms = self._tokenize(query.lower())

            # Find matching IDs
            matching_ids: Optional[Set[str]] = None

            for term in terms:
                term_ids = self._full_text_index.get(term, set())
                if matching_ids is None:
                    matching_ids = term_ids.copy()
                else:
                    matching_ids &= term_ids

            if matching_ids is None:
                matching_ids = set()

            # Apply filters
            results = []
            for id in matching_ids:
                entry = self._index.get(id)
                if not entry:
                    continue

                # Path filter
                if not entry.path.startswith(path_prefix):
                    continue

                # MIME type filter
                if mime_types and entry.mime_type not in mime_types:
                    continue

                # Tags filter
                if tags and not any(t in entry.tags for t in tags):
                    continue

                results.append({
                    "id": entry.id,
                    "path": entry.path,
                    "name": entry.name,
                    "mime_type": entry.mime_type,
                    "tags": entry.tags,
                    "indexed_at": entry.indexed_at.isoformat(),
                })

                if len(results) >= limit:
                    break

            return {
                "query": query,
                "results": results,
                "count": len(results),
                "total_matches": len(matching_ids),
            }
        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")

    async def _similarity_search(
        self,
        sequence: str,
        threshold: float = 0.8,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Find similar sequences."""
        try:
            sequence = sequence.upper().strip()

            # Compute signature for query sequence
            query_sig = self._compute_signature(sequence)

            # Find similar sequences
            results = []
            for entry in self._index.values():
                if entry.sequence_signature is None:
                    continue

                similarity = self._compute_similarity(query_sig, entry.sequence_signature)

                if similarity >= threshold:
                    results.append({
                        "id": entry.id,
                        "path": entry.path,
                        "name": entry.name,
                        "similarity": similarity,
                    })

            # Sort by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            results = results[:limit]

            return {
                "query_length": len(sequence),
                "threshold": threshold,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            raise ValueError(f"Similarity search failed: {str(e)}")

    async def _index_file(
        self,
        id: str,
        path: str,
        name: str,
        mime_type: str = "application/octet-stream",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        sequence: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add or update a file in the index."""
        try:
            tags = tags or []
            metadata = metadata or {}

            # Compute content hash
            content = f"{path}:{name}:{mime_type}"
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            # Compute sequence signature if provided
            seq_sig = None
            if sequence:
                seq_sig = self._compute_signature(sequence.upper().strip())

            # Create entry
            entry = IndexEntry(
                id=id,
                path=path,
                name=name,
                mime_type=mime_type,
                tags=tags,
                metadata=metadata,
                content_hash=content_hash,
                sequence_signature=seq_sig,
            )

            # Remove old entry if exists
            if id in self._index:
                await self._remove_from_index(id)

            # Add to main index
            self._index[id] = entry

            # Add to full-text index
            terms = self._tokenize(f"{name} {' '.join(tags)} {str(metadata)}".lower())
            for term in terms:
                if term not in self._full_text_index:
                    self._full_text_index[term] = set()
                self._full_text_index[term].add(id)

            # Add to tag index
            for tag in tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(id)

            return {
                "indexed": True,
                "id": id,
                "path": path,
                "terms_indexed": len(terms),
            }
        except Exception as e:
            raise ValueError(f"Indexing failed: {str(e)}")

    async def _remove_from_index(self, id: str) -> Dict[str, Any]:
        """Remove a file from the index."""
        try:
            if id not in self._index:
                return {
                    "removed": False,
                    "error": f"ID not found: {id}",
                }

            entry = self._index[id]

            # Remove from full-text index
            terms = self._tokenize(
                f"{entry.name} {' '.join(entry.tags)} {str(entry.metadata)}".lower()
            )
            for term in terms:
                if term in self._full_text_index:
                    self._full_text_index[term].discard(id)
                    if not self._full_text_index[term]:
                        del self._full_text_index[term]

            # Remove from tag index
            for tag in entry.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(id)
                    if not self._tag_index[tag]:
                        del self._tag_index[tag]

            # Remove from main index
            del self._index[id]

            return {
                "removed": True,
                "id": id,
            }
        except Exception as e:
            raise ValueError(f"Remove failed: {str(e)}")

    async def _get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_entries": len(self._index),
            "total_terms": len(self._full_text_index),
            "total_tags": len(self._tag_index),
            "entries_with_sequences": sum(
                1 for e in self._index.values()
                if e.sequence_signature is not None
            ),
        }

    def _get_index_status(self) -> Dict[str, Any]:
        """Get index status for resource."""
        return {
            "status": "healthy",
            "entries": len(self._index),
            "terms": len(self._full_text_index),
            "tags": len(self._tag_index),
        }

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for indexing."""
        # Simple word tokenization
        import re
        words = re.findall(r'\w+', text.lower())
        # Filter short words
        return [w for w in words if len(w) >= 2]

    def _compute_signature(self, sequence: str) -> bytes:
        """
        Compute locality-sensitive hash for similarity search.
        Uses k-mer based MinHash approximation.
        """
        k = 8  # K-mer size
        num_hashes = 128

        # Extract k-mers
        kmers = set()
        for i in range(len(sequence) - k + 1):
            kmers.add(sequence[i:i + k])

        # Compute MinHash-style signature
        signature = []
        for i in range(num_hashes):
            min_hash = float('inf')
            for kmer in kmers:
                h = hash((kmer, i)) & 0xFFFFFFFF
                if h < min_hash:
                    min_hash = h
            signature.append(min_hash & 0xFF)

        return bytes(signature)

    def _compute_similarity(self, sig1: bytes, sig2: bytes) -> float:
        """Compute Jaccard similarity estimate from MinHash signatures."""
        if len(sig1) != len(sig2):
            return 0.0

        matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
        return matches / len(sig1)
