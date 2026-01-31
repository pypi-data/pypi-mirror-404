# VibeDNA FileSystem MCP Server
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
FileSystem MCP Server for VibeDNA DNA-based file storage operations.

Provides tools for:
- File creation and storage
- File reading and retrieval
- File updates and deletion
- Directory management
- File search
"""

import base64
from datetime import datetime
from typing import Any, Dict, List, Optional

from vibedna.agents.mcp_servers.base_server import (
    BaseMCPServer,
    MCPServerConfig,
    MCPTool,
    MCPToolParameter,
    MCPResource,
    TransportType,
)
from vibedna.storage.dna_file_system import DNAFileSystem


class VibeDNAFSMCPServer(BaseMCPServer):
    """
    FileSystem MCP Server for DNA-based file storage.

    Tools:
    - create_file: Create file in DNA storage
    - read_file: Read file from DNA storage
    - update_file: Update existing file
    - delete_file: Delete file from storage
    - list_directory: List directory contents
    - search_files: Search for files
    - get_raw_sequence: Get raw DNA sequence for a file

    Resources:
    - storage_stats: Storage statistics
    """

    def __init__(self, config: Optional[MCPServerConfig] = None):
        """Initialize the FileSystem MCP server."""
        if config is None:
            config = MCPServerConfig(
                name="vibedna-fs",
                version="1.0.0",
                description="DNA-based file system MCP server",
                transport=TransportType.SSE,
                url="https://mcp.vibedna.vibecaas.com/filesystem",
                port=8092,
            )
        super().__init__(config)

        # Initialize file system
        self._fs = DNAFileSystem()

    def _register_tools(self) -> None:
        """Register file system tools."""

        # create_file tool
        self.register_tool(MCPTool(
            name="create_file",
            description="Create a new file in DNA storage",
            parameters=[
                MCPToolParameter(
                    name="path",
                    param_type="string",
                    description="File path in the virtual file system",
                    required=True,
                ),
                MCPToolParameter(
                    name="data",
                    param_type="string",
                    description="Base64-encoded file content",
                    required=True,
                ),
                MCPToolParameter(
                    name="mime_type",
                    param_type="string",
                    description="MIME type of the file",
                    required=False,
                    default="application/octet-stream",
                ),
                MCPToolParameter(
                    name="encoding",
                    param_type="string",
                    description="Encoding scheme to use",
                    required=False,
                    default="quaternary",
                    enum=["quaternary", "balanced_gc", "rll", "triplet"],
                ),
                MCPToolParameter(
                    name="tags",
                    param_type="array",
                    description="Tags for the file",
                    required=False,
                ),
            ],
            handler=self._create_file,
        ))

        # read_file tool
        self.register_tool(MCPTool(
            name="read_file",
            description="Read a file from DNA storage",
            parameters=[
                MCPToolParameter(
                    name="path",
                    param_type="string",
                    description="File path to read",
                    required=True,
                ),
            ],
            handler=self._read_file,
        ))

        # update_file tool
        self.register_tool(MCPTool(
            name="update_file",
            description="Update an existing file's content",
            parameters=[
                MCPToolParameter(
                    name="path",
                    param_type="string",
                    description="File path to update",
                    required=True,
                ),
                MCPToolParameter(
                    name="data",
                    param_type="string",
                    description="New base64-encoded content",
                    required=True,
                ),
            ],
            handler=self._update_file,
        ))

        # delete_file tool
        self.register_tool(MCPTool(
            name="delete_file",
            description="Delete a file from storage",
            parameters=[
                MCPToolParameter(
                    name="path",
                    param_type="string",
                    description="File path to delete",
                    required=True,
                ),
                MCPToolParameter(
                    name="permanent",
                    param_type="boolean",
                    description="Permanently delete (skip trash)",
                    required=False,
                    default=False,
                ),
            ],
            handler=self._delete_file,
        ))

        # list_directory tool
        self.register_tool(MCPTool(
            name="list_directory",
            description="List contents of a directory",
            parameters=[
                MCPToolParameter(
                    name="path",
                    param_type="string",
                    description="Directory path to list",
                    required=False,
                    default="/",
                ),
            ],
            handler=self._list_directory,
        ))

        # search_files tool
        self.register_tool(MCPTool(
            name="search_files",
            description="Search for files by query and filters",
            parameters=[
                MCPToolParameter(
                    name="query",
                    param_type="string",
                    description="Search query",
                    required=False,
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
            ],
            handler=self._search_files,
        ))

        # get_raw_sequence tool
        self.register_tool(MCPTool(
            name="get_raw_sequence",
            description="Get the raw DNA sequence for a file",
            parameters=[
                MCPToolParameter(
                    name="path",
                    param_type="string",
                    description="File path",
                    required=True,
                ),
            ],
            handler=self._get_raw_sequence,
        ))

    def _register_resources(self) -> None:
        """Register file system resources."""

        self.register_resource(MCPResource(
            name="storage_stats",
            description="Storage statistics",
            uri="vibedna://fs/stats",
            mime_type="application/json",
            handler=self._get_storage_stats,
        ))

    async def _create_file(
        self,
        path: str,
        data: str,
        mime_type: str = "application/octet-stream",
        encoding: str = "quaternary",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new file in DNA storage."""
        try:
            # Decode base64 data
            binary_data = base64.b64decode(data)

            # Create file
            file = self._fs.create_file(
                path=path,
                data=binary_data,
                mime_type=mime_type,
                encoding_scheme=encoding,
                tags=tags or [],
            )

            return {
                "file_id": file.id,
                "path": file.path,
                "dna_length": file.dna_length,
                "original_size": file.original_size,
                "encoding": file.encoding_scheme,
                "created_at": file.created_at.isoformat() if file.created_at else None,
            }
        except Exception as e:
            raise ValueError(f"Failed to create file: {str(e)}")

    async def _read_file(self, path: str) -> Dict[str, Any]:
        """Read a file from DNA storage."""
        try:
            data = self._fs.read_file(path)
            file = self._fs.get_file(path)

            return {
                "data": base64.b64encode(data).decode("utf-8"),
                "metadata": {
                    "path": file.path,
                    "name": file.name,
                    "mime_type": file.mime_type,
                    "original_size": file.original_size,
                    "dna_length": file.dna_length,
                    "encoding": file.encoding_scheme,
                    "tags": file.tags,
                },
            }
        except Exception as e:
            raise ValueError(f"Failed to read file: {str(e)}")

    async def _update_file(self, path: str, data: str) -> Dict[str, Any]:
        """Update an existing file."""
        try:
            binary_data = base64.b64decode(data)
            file = self._fs.update_file(path, binary_data)

            return {
                "file_id": file.id,
                "path": file.path,
                "dna_length": file.dna_length,
                "original_size": file.original_size,
                "modified_at": file.modified_at.isoformat() if file.modified_at else None,
            }
        except Exception as e:
            raise ValueError(f"Failed to update file: {str(e)}")

    async def _delete_file(self, path: str, permanent: bool = False) -> Dict[str, Any]:
        """Delete a file from storage."""
        try:
            success = self._fs.delete_file(path, permanent=permanent)
            return {
                "success": success,
                "path": path,
                "permanent": permanent,
            }
        except Exception as e:
            raise ValueError(f"Failed to delete file: {str(e)}")

    async def _list_directory(self, path: str = "/") -> Dict[str, Any]:
        """List contents of a directory."""
        try:
            items = self._fs.list_directory(path)

            return {
                "path": path,
                "items": [
                    {
                        "name": item.name,
                        "path": item.path,
                        "type": "directory" if hasattr(item, "children") else "file",
                        "size": getattr(item, "original_size", None),
                        "dna_length": getattr(item, "dna_length", None),
                    }
                    for item in items
                ],
                "count": len(items),
            }
        except Exception as e:
            raise ValueError(f"Failed to list directory: {str(e)}")

    async def _search_files(
        self,
        query: Optional[str] = None,
        path_prefix: str = "/",
        mime_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search for files."""
        try:
            results = self._fs.search(
                query=query,
                path_prefix=path_prefix,
                mime_types=mime_types,
                tags=tags,
            )

            return {
                "query": query,
                "results": [
                    {
                        "path": f.path,
                        "name": f.name,
                        "mime_type": f.mime_type,
                        "size": f.original_size,
                        "tags": f.tags,
                    }
                    for f in results
                ],
                "count": len(results),
            }
        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")

    async def _get_raw_sequence(self, path: str) -> Dict[str, Any]:
        """Get the raw DNA sequence for a file."""
        try:
            file = self._fs.get_file(path)
            return {
                "path": path,
                "sequence": file.dna_sequence,
                "length": len(file.dna_sequence) if file.dna_sequence else 0,
            }
        except Exception as e:
            raise ValueError(f"Failed to get sequence: {str(e)}")

    def _get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            stats = self._fs.get_stats()
            return {
                "total_files": stats.get("total_files", 0),
                "total_original_bytes": stats.get("total_original_bytes", 0),
                "total_nucleotides": stats.get("total_nucleotides", 0),
                "average_compression": stats.get("average_compression", 1.0),
                "encoding_distribution": stats.get("encoding_distribution", {}),
            }
        except Exception as e:
            return {
                "error": str(e),
                "total_files": 0,
                "total_nucleotides": 0,
            }
