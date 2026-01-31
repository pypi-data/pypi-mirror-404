# VibeDNA FileSystem Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
FileSystem Agent - DNA-based file management.

Manages a virtual file system where all data is stored as DNA sequences,
providing familiar CRUD operations.
"""

import base64
from typing import Any, Dict, List, Optional

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
from vibedna.storage.dna_file_system import DNAFileSystem


class FileSystemAgent(BaseAgent):
    """
    FileSystem Agent for DNA-based storage.

    Manages files stored as DNA sequences with full
    CRUD operations and directory management.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the FileSystem Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-filesystem-agent",
                version="1.0.0",
                tier=AgentTier.SPECIALIST,
                role="DNA-Based File Management",
                description="Manages DNA-encoded file storage",
                capabilities=[
                    AgentCapability(
                        name="file_crud",
                        description="Create, read, update, delete files",
                    ),
                    AgentCapability(
                        name="directory_management",
                        description="Manage directory structure",
                    ),
                    AgentCapability(
                        name="file_search",
                        description="Search files by various criteria",
                    ),
                ],
                tools=[
                    "file_creator",
                    "file_reader",
                    "file_updater",
                    "file_deleter",
                    "directory_manager",
                    "file_searcher",
                    "catalog_manager",
                ],
                mcp_connections=["vibedna-fs"],
            )

        super().__init__(config)
        self._fs = DNAFileSystem()

    def get_system_prompt(self) -> str:
        """Get the FileSystem Agent's system prompt."""
        return """You are the VibeDNA FileSystem Agent, managing DNA-encoded file storage.

## File System Structure

/
├── .vibedna/
│   ├── config.dna          # System configuration
│   ├── catalog.dna         # File catalog/index
│   └── trash/              # Deleted files (recoverable)
├── documents/
├── images/
├── data/
└── projects/

## File Operations

- create_file: Create new file with DNA encoding
- read_file: Read and decode file
- update_file: Update existing file
- delete_file: Delete (move to trash or permanent)
- list_directory: List directory contents
- search: Search by query, tags, mime types

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a file system task."""
        self.logger.info(f"Handling filesystem task: {request.request_id}")

        action = request.parameters.get("action", "list")

        if action == "create_file":
            return await self._create_file(request)
        elif action == "read_file":
            return await self._read_file(request)
        elif action == "update_file":
            return await self._update_file(request)
        elif action == "delete_file":
            return await self._delete_file(request)
        elif action == "list" or action == "list_directory":
            return await self._list_directory(request)
        elif action == "search":
            return await self._search_files(request)
        elif action == "get_stats":
            return await self._get_stats(request)
        else:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown action: {action}",
            )

    async def _create_file(self, request: TaskRequest) -> TaskResponse:
        """Create a new file."""
        try:
            path = request.parameters.get("path")
            data = request.parameters.get("data")
            mime_type = request.parameters.get("mime_type", "application/octet-stream")
            encoding = request.parameters.get("encoding_scheme", "quaternary")
            tags = request.parameters.get("tags", [])

            if not path:
                return TaskResponse.failure(request.request_id, "path required")

            if not data:
                return TaskResponse.failure(request.request_id, "data required")

            # Decode base64 if string
            if isinstance(data, str):
                try:
                    binary_data = base64.b64decode(data)
                except Exception:
                    binary_data = data.encode("utf-8")
            else:
                binary_data = data

            file = self._fs.create_file(
                path=path,
                data=binary_data,
                mime_type=mime_type,
                encoding_scheme=encoding,
                tags=tags,
            )

            return TaskResponse.success(
                request.request_id,
                {
                    "file_id": file.id,
                    "path": file.path,
                    "dna_length": file.dna_length,
                    "original_size": file.original_size,
                },
            )

        except Exception as e:
            self.logger.error(f"Create file failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _read_file(self, request: TaskRequest) -> TaskResponse:
        """Read a file."""
        try:
            path = request.parameters.get("path")

            if not path:
                return TaskResponse.failure(request.request_id, "path required")

            data = self._fs.read_file(path)
            file = self._fs.get_file(path)

            return TaskResponse.success(
                request.request_id,
                {
                    "data": base64.b64encode(data).decode("utf-8"),
                    "path": file.path,
                    "name": file.name,
                    "mime_type": file.mime_type,
                    "original_size": len(data),
                },
            )

        except Exception as e:
            self.logger.error(f"Read file failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _update_file(self, request: TaskRequest) -> TaskResponse:
        """Update a file."""
        try:
            path = request.parameters.get("path")
            data = request.parameters.get("data")

            if not path:
                return TaskResponse.failure(request.request_id, "path required")

            if not data:
                return TaskResponse.failure(request.request_id, "data required")

            if isinstance(data, str):
                try:
                    binary_data = base64.b64decode(data)
                except Exception:
                    binary_data = data.encode("utf-8")
            else:
                binary_data = data

            file = self._fs.update_file(path, binary_data)

            return TaskResponse.success(
                request.request_id,
                {
                    "file_id": file.id,
                    "path": file.path,
                    "dna_length": file.dna_length,
                },
            )

        except Exception as e:
            self.logger.error(f"Update file failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _delete_file(self, request: TaskRequest) -> TaskResponse:
        """Delete a file."""
        try:
            path = request.parameters.get("path")
            permanent = request.parameters.get("permanent", False)

            if not path:
                return TaskResponse.failure(request.request_id, "path required")

            success = self._fs.delete_file(path, permanent=permanent)

            return TaskResponse.success(
                request.request_id,
                {"deleted": success, "path": path, "permanent": permanent},
            )

        except Exception as e:
            self.logger.error(f"Delete file failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _list_directory(self, request: TaskRequest) -> TaskResponse:
        """List directory contents."""
        try:
            path = request.parameters.get("path", "/")

            items = self._fs.list_directory(path)

            return TaskResponse.success(
                request.request_id,
                {
                    "path": path,
                    "items": [
                        {
                            "name": item.name,
                            "path": item.path,
                            "type": "directory" if hasattr(item, "children") else "file",
                        }
                        for item in items
                    ],
                },
            )

        except Exception as e:
            self.logger.error(f"List directory failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _search_files(self, request: TaskRequest) -> TaskResponse:
        """Search for files."""
        try:
            query = request.parameters.get("query")
            path_prefix = request.parameters.get("path_prefix", "/")
            mime_types = request.parameters.get("mime_types")
            tags = request.parameters.get("tags")

            results = self._fs.search(
                query=query,
                path_prefix=path_prefix,
                mime_types=mime_types,
                tags=tags,
            )

            return TaskResponse.success(
                request.request_id,
                {
                    "query": query,
                    "results": [
                        {"path": f.path, "name": f.name, "tags": f.tags}
                        for f in results
                    ],
                    "count": len(results),
                },
            )

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _get_stats(self, request: TaskRequest) -> TaskResponse:
        """Get storage statistics."""
        try:
            stats = self._fs.get_stats()

            return TaskResponse.success(request.request_id, stats)

        except Exception as e:
            self.logger.error(f"Get stats failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))
