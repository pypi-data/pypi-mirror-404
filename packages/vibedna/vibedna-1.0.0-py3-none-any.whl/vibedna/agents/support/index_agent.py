# VibeDNA Index Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Index Agent - Catalog and search index management.

Maintains searchable index of all DNA sequences for:
- Full-text search
- Sequence similarity search
- Tag-based filtering
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import hashlib

from vibedna.agents.base.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentTier,
)
from vibedna.agents.base.message import (
    TaskRequest,
    TaskResponse,
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
    indexed_at: datetime = field(default_factory=datetime.utcnow)


class IndexAgent(BaseAgent):
    """
    Index Agent for catalog and search management.

    Maintains a searchable index of sequences and files
    for fast lookup and retrieval.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Index Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-index-agent",
                version="1.0.0",
                tier=AgentTier.SUPPORT,
                role="Catalog and Search Index",
                description="Maintains searchable index of DNA sequences",
                capabilities=[
                    AgentCapability(
                        name="catalog_management",
                        description="Manage file catalog",
                    ),
                    AgentCapability(
                        name="full_text_search",
                        description="Full-text search across files",
                    ),
                    AgentCapability(
                        name="similarity_search",
                        description="Sequence similarity search",
                    ),
                ],
                tools=[
                    "catalog_manager",
                    "full_text_indexer",
                    "similarity_indexer",
                    "search_executor",
                ],
                mcp_connections=["vibedna-search"],
            )

        super().__init__(config)
        self._index: Dict[str, IndexEntry] = {}
        self._text_index: Dict[str, Set[str]] = {}
        self._tag_index: Dict[str, Set[str]] = {}

    def get_system_prompt(self) -> str:
        """Get the Index Agent's system prompt."""
        return """You are the VibeDNA Index Agent, managing the sequence catalog and search.

## Capabilities

1. Catalog Management - Add, update, remove entries
2. Full-Text Search - Search by name, tags, metadata
3. Similarity Search - Find similar sequences using MinHash

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle an index task."""
        action = request.parameters.get("action", "search")

        if action == "add_to_catalog" or action == "index":
            return await self._add_to_index(request)
        elif action == "remove":
            return await self._remove_from_index(request)
        elif action == "search":
            return await self._search(request)
        elif action == "lookup":
            return await self._lookup(request)
        elif action == "get_stats":
            return await self._get_stats(request)
        else:
            return TaskResponse.failure(request.request_id, f"Unknown action: {action}")

    async def _add_to_index(self, request: TaskRequest) -> TaskResponse:
        """Add entry to index."""
        try:
            id = request.parameters.get("id") or request.parameters.get("sequence_id")
            path = request.parameters.get("path", "")
            name = request.parameters.get("name", "")
            mime_type = request.parameters.get("mime_type", "application/octet-stream")
            tags = request.parameters.get("tags", [])
            metadata = request.parameters.get("metadata", {})

            if not id:
                return TaskResponse.failure(request.request_id, "id required")

            entry = IndexEntry(
                id=id,
                path=path,
                name=name,
                mime_type=mime_type,
                tags=tags,
                metadata=metadata,
            )

            self._index[id] = entry

            # Update text index
            text = f"{name} {' '.join(tags)} {str(metadata)}".lower()
            for word in text.split():
                if len(word) >= 2:
                    if word not in self._text_index:
                        self._text_index[word] = set()
                    self._text_index[word].add(id)

            # Update tag index
            for tag in tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(id)

            return TaskResponse.success(
                request.request_id,
                {"indexed": True, "id": id},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _remove_from_index(self, request: TaskRequest) -> TaskResponse:
        """Remove entry from index."""
        try:
            id = request.parameters.get("id")

            if id not in self._index:
                return TaskResponse.success(
                    request.request_id,
                    {"removed": False, "reason": "not found"},
                )

            entry = self._index[id]

            # Remove from text index
            for word_ids in self._text_index.values():
                word_ids.discard(id)

            # Remove from tag index
            for tag in entry.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(id)

            del self._index[id]

            return TaskResponse.success(
                request.request_id,
                {"removed": True, "id": id},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _search(self, request: TaskRequest) -> TaskResponse:
        """Search the index."""
        try:
            query = request.parameters.get("query", "")
            tags = request.parameters.get("tags", [])
            limit = request.parameters.get("limit", 100)

            matching_ids: Optional[Set[str]] = None

            # Text search
            if query:
                words = query.lower().split()
                for word in words:
                    word_ids = self._text_index.get(word, set())
                    if matching_ids is None:
                        matching_ids = word_ids.copy()
                    else:
                        matching_ids &= word_ids

            # Tag filter
            if tags:
                tag_ids = set()
                for tag in tags:
                    tag_ids |= self._tag_index.get(tag, set())
                if matching_ids is None:
                    matching_ids = tag_ids
                else:
                    matching_ids &= tag_ids

            if matching_ids is None:
                matching_ids = set(self._index.keys())

            results = []
            for id in list(matching_ids)[:limit]:
                entry = self._index.get(id)
                if entry:
                    results.append({
                        "id": entry.id,
                        "path": entry.path,
                        "name": entry.name,
                        "tags": entry.tags,
                    })

            return TaskResponse.success(
                request.request_id,
                {"results": results, "count": len(results)},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _lookup(self, request: TaskRequest) -> TaskResponse:
        """Lookup a specific entry."""
        try:
            id = request.parameters.get("id")
            path = request.parameters.get("path")

            if id and id in self._index:
                entry = self._index[id]
                return TaskResponse.success(
                    request.request_id,
                    {
                        "found": True,
                        "id": entry.id,
                        "path": entry.path,
                        "name": entry.name,
                        "tags": entry.tags,
                        "metadata": entry.metadata,
                    },
                )

            if path:
                for entry in self._index.values():
                    if entry.path == path:
                        return TaskResponse.success(
                            request.request_id,
                            {
                                "found": True,
                                "id": entry.id,
                                "path": entry.path,
                                "name": entry.name,
                            },
                        )

            return TaskResponse.success(
                request.request_id,
                {"found": False},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _get_stats(self, request: TaskRequest) -> TaskResponse:
        """Get index statistics."""
        return TaskResponse.success(
            request.request_id,
            {
                "total_entries": len(self._index),
                "total_terms": len(self._text_index),
                "total_tags": len(self._tag_index),
            },
        )
