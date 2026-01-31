"""
VibeDNA File System - DNA-Based Virtual File System

Implements a complete file system where all data is stored
as DNA sequences, with directories, permissions, and versioning.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import PurePosixPath
import uuid
import json
import os

from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme
from vibedna.core.decoder import DNADecoder, DecodeResult
from vibedna.utils.validators import validate_file_path
from vibedna.utils.logger import get_logger

logger = get_logger(__name__)


class FileSystemError(Exception):
    """Base exception for file system errors."""
    pass


class FileNotFoundError(FileSystemError):
    """File not found."""
    pass


class DirectoryNotFoundError(FileSystemError):
    """Directory not found."""
    pass


class FileExistsError(FileSystemError):
    """File already exists."""
    pass


@dataclass
class DNAFile:
    """Represents a file stored as DNA sequence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    path: str = "/"
    dna_sequence: str = ""
    original_size: int = 0
    dna_length: int = 0
    mime_type: str = "application/octet-stream"
    created_at: datetime = field(default_factory=datetime.utcnow)
    modified_at: datetime = field(default_factory=datetime.utcnow)
    checksum: str = ""
    encoding_scheme: str = "quaternary"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "original_size": self.original_size,
            "dna_length": self.dna_length,
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "checksum": self.checksum,
            "encoding_scheme": self.encoding_scheme,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class DNADirectory:
    """Represents a directory in the DNA file system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    path: str = "/"
    parent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class DNAFileSystem:
    """
    Virtual file system using DNA sequences for storage.

    Provides familiar file system operations (create, read, update, delete)
    with all data encoded and stored as DNA sequences.

    Features:
    - Hierarchical directory structure
    - File versioning
    - Metadata and tagging
    - Search and indexing
    - Import/export from traditional filesystem

    Example:
        >>> fs = DNAFileSystem()
        >>> fs.create_file("/hello.txt", b"Hello DNA!")
        >>> data = fs.read_file("/hello.txt")
        >>> print(data)
        b'Hello DNA!'
    """

    def __init__(self, storage_backend: str = "memory"):
        """
        Initialize DNA file system.

        Args:
            storage_backend: Where to persist DNA sequences
                - "memory": In-memory (non-persistent)
                - "sqlite": SQLite database (future)
                - "json": JSON file storage
        """
        self.storage_backend = storage_backend
        self._encoder: Optional[DNAEncoder] = None
        self._decoder: Optional[DNADecoder] = None

        # In-memory storage
        self._files: Dict[str, DNAFile] = {}
        self._directories: Dict[str, DNADirectory] = {}

        # Initialize root directory
        self._init_root()

    def _init_root(self) -> None:
        """Initialize root directory."""
        root = DNADirectory(
            id="root",
            name="",
            path="/",
            parent_id=None,
        )
        self._directories["/"] = root

    @property
    def encoder(self) -> DNAEncoder:
        """Lazy-load encoder."""
        if self._encoder is None:
            self._encoder = DNAEncoder()
        return self._encoder

    @property
    def decoder(self) -> DNADecoder:
        """Lazy-load decoder."""
        if self._decoder is None:
            self._decoder = DNADecoder()
        return self._decoder

    # ═══════════════════════════════════════════════════════════════
    # File Operations
    # ═══════════════════════════════════════════════════════════════

    def create_file(
        self,
        path: str,
        data: bytes,
        mime_type: str = "application/octet-stream",
        encoding_scheme: str = "quaternary",
        tags: Optional[List[str]] = None
    ) -> DNAFile:
        """
        Create a new file encoded as DNA.

        Args:
            path: Full path for the file
            data: Binary data to store
            mime_type: MIME type of the content
            encoding_scheme: Encoding scheme to use
            tags: Optional tags for the file

        Returns:
            Created DNAFile object

        Raises:
            FileExistsError: If file already exists
            DirectoryNotFoundError: If parent directory doesn't exist
        """
        # Validate path
        is_valid, error = validate_file_path(path)
        if not is_valid:
            raise FileSystemError(error)

        # Check if file exists
        if path in self._files:
            raise FileExistsError(f"File already exists: {path}")

        # Ensure parent directory exists
        parent_path = str(PurePosixPath(path).parent)
        if parent_path not in self._directories:
            raise DirectoryNotFoundError(f"Parent directory not found: {parent_path}")

        # Configure encoder
        scheme = EncodingScheme(encoding_scheme)
        config = EncodingConfig(scheme=scheme)
        encoder = DNAEncoder(config)

        # Encode data
        filename = PurePosixPath(path).name
        dna_sequence = encoder.encode(data, filename=filename, mime_type=mime_type)

        # Create file record
        file = DNAFile(
            name=filename,
            path=path,
            dna_sequence=dna_sequence,
            original_size=len(data),
            dna_length=len(dna_sequence),
            mime_type=mime_type,
            encoding_scheme=encoding_scheme,
            tags=tags or [],
            checksum=self._compute_checksum(dna_sequence),
        )

        self._files[path] = file
        logger.info(f"Created file: {path} ({len(data)} bytes → {len(dna_sequence)} nt)")

        return file

    def read_file(self, path: str) -> bytes:
        """
        Read and decode a file from DNA storage.

        Args:
            path: Full path to the file

        Returns:
            Original binary data

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")

        file = self._files[path]

        # Decode DNA sequence
        result = self.decoder.decode(file.dna_sequence)
        return result.data

    def update_file(self, path: str, data: bytes) -> DNAFile:
        """
        Update existing file content.

        Args:
            path: Full path to the file
            data: New binary data

        Returns:
            Updated DNAFile object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")

        file = self._files[path]

        # Re-encode with same scheme
        scheme = EncodingScheme(file.encoding_scheme)
        config = EncodingConfig(scheme=scheme)
        encoder = DNAEncoder(config)

        dna_sequence = encoder.encode(
            data,
            filename=file.name,
            mime_type=file.mime_type
        )

        # Update file
        file.dna_sequence = dna_sequence
        file.original_size = len(data)
        file.dna_length = len(dna_sequence)
        file.modified_at = datetime.utcnow()
        file.checksum = self._compute_checksum(dna_sequence)

        logger.info(f"Updated file: {path}")
        return file

    def delete_file(self, path: str) -> bool:
        """
        Delete a file from DNA storage.

        Args:
            path: Full path to the file

        Returns:
            True if deleted successfully

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")

        del self._files[path]
        logger.info(f"Deleted file: {path}")
        return True

    def get_file_info(self, path: str) -> DNAFile:
        """
        Get file metadata without decoding content.

        Args:
            path: Full path to the file

        Returns:
            DNAFile object with metadata

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")

        return self._files[path]

    def get_raw_sequence(self, path: str) -> str:
        """
        Get the raw DNA sequence for a file.

        Args:
            path: Full path to the file

        Returns:
            DNA sequence string
        """
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")

        return self._files[path].dna_sequence

    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        return path in self._files

    # ═══════════════════════════════════════════════════════════════
    # Directory Operations
    # ═══════════════════════════════════════════════════════════════

    def create_directory(self, path: str) -> DNADirectory:
        """
        Create a new directory.

        Args:
            path: Full path for the directory

        Returns:
            Created DNADirectory object

        Raises:
            FileExistsError: If directory already exists
        """
        # Validate path
        is_valid, error = validate_file_path(path)
        if not is_valid:
            raise FileSystemError(error)

        if path in self._directories:
            raise FileExistsError(f"Directory already exists: {path}")

        # Ensure parent directory exists
        parent_path = str(PurePosixPath(path).parent)
        if parent_path != "/" and parent_path not in self._directories:
            raise DirectoryNotFoundError(f"Parent directory not found: {parent_path}")

        # Get parent directory
        parent = self._directories.get(parent_path)
        parent_id = parent.id if parent else None

        # Create directory
        directory = DNADirectory(
            name=PurePosixPath(path).name,
            path=path,
            parent_id=parent_id,
        )

        self._directories[path] = directory
        logger.info(f"Created directory: {path}")

        return directory

    def list_directory(
        self,
        path: str = "/"
    ) -> List[Union[DNAFile, DNADirectory]]:
        """
        List contents of a directory.

        Args:
            path: Directory path

        Returns:
            List of files and directories
        """
        if path not in self._directories:
            raise DirectoryNotFoundError(f"Directory not found: {path}")

        # Normalize path
        if not path.endswith("/"):
            path = path + "/"
        if path == "//":
            path = "/"

        contents: List[Union[DNAFile, DNADirectory]] = []

        # Find files in this directory
        for file_path, file in self._files.items():
            parent = str(PurePosixPath(file_path).parent)
            if parent == path.rstrip("/") or (path == "/" and parent == "/"):
                contents.append(file)

        # Find subdirectories
        for dir_path, directory in self._directories.items():
            if dir_path == path.rstrip("/"):
                continue  # Skip the directory itself

            parent = str(PurePosixPath(dir_path).parent)
            if parent == path.rstrip("/") or (path == "/" and parent == "/"):
                contents.append(directory)

        return contents

    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """
        Delete a directory.

        Args:
            path: Directory path
            recursive: If True, delete contents recursively

        Returns:
            True if deleted successfully
        """
        if path == "/":
            raise FileSystemError("Cannot delete root directory")

        if path not in self._directories:
            raise DirectoryNotFoundError(f"Directory not found: {path}")

        contents = self.list_directory(path)

        if contents and not recursive:
            raise FileSystemError(f"Directory not empty: {path}")

        if recursive:
            for item in contents:
                if isinstance(item, DNAFile):
                    self.delete_file(item.path)
                else:
                    self.delete_directory(item.path, recursive=True)

        del self._directories[path]
        logger.info(f"Deleted directory: {path}")
        return True

    def directory_exists(self, path: str) -> bool:
        """Check if a directory exists."""
        return path in self._directories

    # ═══════════════════════════════════════════════════════════════
    # Search Operations
    # ═══════════════════════════════════════════════════════════════

    def search(
        self,
        query: Optional[str] = None,
        path_prefix: str = "/",
        mime_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> List[DNAFile]:
        """
        Search for files matching criteria.

        Args:
            query: Filename pattern to match
            path_prefix: Only search under this path
            mime_types: Filter by MIME types
            tags: Filter by tags (any match)
            created_after: Files created after this time
            created_before: Files created before this time

        Returns:
            List of matching files
        """
        results = []

        for path, file in self._files.items():
            # Path prefix filter
            if not path.startswith(path_prefix):
                continue

            # Query filter (simple substring match)
            if query and query.lower() not in file.name.lower():
                continue

            # MIME type filter
            if mime_types and file.mime_type not in mime_types:
                continue

            # Tags filter
            if tags and not any(t in file.tags for t in tags):
                continue

            # Date filters
            if created_after and file.created_at < created_after:
                continue
            if created_before and file.created_at > created_before:
                continue

            results.append(file)

        return results

    def find_by_sequence(self, sequence_fragment: str) -> List[DNAFile]:
        """
        Find files containing a DNA sequence fragment.

        Args:
            sequence_fragment: DNA sequence to search for

        Returns:
            List of files containing the fragment
        """
        sequence_fragment = sequence_fragment.upper()
        results = []

        for file in self._files.values():
            if sequence_fragment in file.dna_sequence:
                results.append(file)

        return results

    # ═══════════════════════════════════════════════════════════════
    # Utility Operations
    # ═══════════════════════════════════════════════════════════════

    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        total_files = len(self._files)
        total_directories = len(self._directories)
        total_binary_size = sum(f.original_size for f in self._files.values())
        total_dna_length = sum(f.dna_length for f in self._files.values())

        # Calculate expansion ratio
        expansion_ratio = total_dna_length / total_binary_size if total_binary_size > 0 else 0

        return {
            "total_files": total_files,
            "total_directories": total_directories,
            "total_binary_size": total_binary_size,
            "total_dna_length": total_dna_length,
            "expansion_ratio": expansion_ratio,
            "backend": self.storage_backend,
        }

    def verify_integrity(self, path: Optional[str] = None) -> dict:
        """
        Verify integrity of stored files.

        Args:
            path: Optional specific path to verify (all if None)

        Returns:
            Dictionary with verification results
        """
        results = {"verified": 0, "failed": 0, "errors": []}

        files_to_check = (
            [self._files[path]] if path and path in self._files
            else self._files.values()
        )

        for file in files_to_check:
            try:
                computed_checksum = self._compute_checksum(file.dna_sequence)
                if computed_checksum == file.checksum:
                    results["verified"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        f"{file.path}: checksum mismatch"
                    )
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{file.path}: {str(e)}")

        return results

    def export_catalog(self, format: str = "json") -> str:
        """
        Export file system catalog.

        Args:
            format: Output format ("json")

        Returns:
            Catalog as string
        """
        catalog = {
            "files": [f.to_dict() for f in self._files.values()],
            "directories": [d.to_dict() for d in self._directories.values()],
            "stats": self.get_storage_stats(),
        }

        if format == "json":
            return json.dumps(catalog, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_from_filesystem(
        self,
        source_path: str,
        target_path: str = "/"
    ) -> List[DNAFile]:
        """
        Import files from traditional filesystem to DNA storage.

        Args:
            source_path: Path on traditional filesystem
            target_path: Target path in DNA filesystem

        Returns:
            List of imported files
        """
        imported = []

        if os.path.isfile(source_path):
            # Import single file
            filename = os.path.basename(source_path)
            dna_path = f"{target_path.rstrip('/')}/{filename}"

            with open(source_path, "rb") as f:
                data = f.read()

            file = self.create_file(dna_path, data)
            imported.append(file)

        elif os.path.isdir(source_path):
            # Ensure target directory exists
            if not self.directory_exists(target_path):
                self.create_directory(target_path)

            # Import directory recursively
            for item in os.listdir(source_path):
                item_path = os.path.join(source_path, item)
                dna_target = f"{target_path.rstrip('/')}/{item}"

                imported.extend(
                    self.import_from_filesystem(item_path, dna_target)
                )

        return imported

    def export_to_filesystem(self, source_path: str, target_path: str) -> None:
        """
        Export files from DNA storage to traditional filesystem.

        Args:
            source_path: Path in DNA filesystem
            target_path: Target path on traditional filesystem
        """
        if source_path in self._files:
            # Export single file
            data = self.read_file(source_path)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(data)

        elif source_path in self._directories:
            # Export directory
            os.makedirs(target_path, exist_ok=True)

            for item in self.list_directory(source_path):
                item_target = os.path.join(target_path, item.name)

                if isinstance(item, DNAFile):
                    data = self.read_file(item.path)
                    with open(item_target, "wb") as f:
                        f.write(data)
                else:
                    self.export_to_filesystem(item.path, item_target)

    def _compute_checksum(self, sequence: str) -> str:
        """Compute checksum for a DNA sequence."""
        import hashlib
        return hashlib.sha256(sequence.encode()).hexdigest()[:16]


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
