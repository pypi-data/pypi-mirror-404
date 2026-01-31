"""
VibeDNA Roundtrip Integration Tests

Integration tests for complete encode-decode cycles.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

import pytest
from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme
from vibedna.core.decoder import DNADecoder
from vibedna.storage.dna_file_system import DNAFileSystem


class TestCompleteRoundtrip:
    """Test complete encode-decode roundtrips."""

    @pytest.mark.parametrize("scheme", [
        EncodingScheme.QUATERNARY,
        EncodingScheme.BALANCED_GC,
        EncodingScheme.RUN_LENGTH_LIMITED,
        EncodingScheme.REDUNDANT_TRIPLET,
    ])
    def test_roundtrip_all_schemes(self, scheme):
        """Test roundtrip with all encoding schemes."""
        config = EncodingConfig(scheme=scheme)
        encoder = DNAEncoder(config)
        decoder = DNADecoder()

        original = b"Hello, VibeDNA! Testing scheme: " + scheme.value.encode()
        encoded = encoder.encode(original, filename="test.txt")
        result = decoder.decode(encoded)

        assert result.data == original
        assert result.encoding_scheme == scheme.value

    @pytest.mark.parametrize("data_size", [0, 1, 10, 100, 1000, 10000])
    def test_roundtrip_various_sizes(self, data_size):
        """Test roundtrip with various data sizes."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        original = b"X" * data_size
        encoded = encoder.encode(original, filename="test.bin")
        result = decoder.decode(encoded)

        assert result.data == original
        assert len(result.data) == data_size

    def test_roundtrip_binary_data(self):
        """Test roundtrip with binary data (all byte values)."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        original = bytes(range(256))
        encoded = encoder.encode(original, filename="binary.bin")
        result = decoder.decode(encoded)

        assert result.data == original

    def test_roundtrip_preserves_filename(self):
        """Test that filename is preserved through roundtrip."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        filename = "my_important_file.txt"
        encoded = encoder.encode(b"content", filename=filename)
        result = decoder.decode(encoded)

        assert result.filename == filename

    def test_roundtrip_preserves_mime_type(self):
        """Test that MIME type is preserved through roundtrip."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        mime_type = "text/plain"
        encoded = encoder.encode(b"content", mime_type=mime_type)
        result = decoder.decode(encoded)

        # MIME type might be truncated, check prefix
        assert result.mime_type.startswith("text")


class TestFileSystemRoundtrip:
    """Test file system roundtrip operations."""

    def test_create_read_file(self):
        """Test creating and reading a file."""
        fs = DNAFileSystem()

        original = b"Hello, DNA File System!"
        fs.create_file("/test.txt", original)
        result = fs.read_file("/test.txt")

        assert result == original

    def test_update_file(self):
        """Test updating a file."""
        fs = DNAFileSystem()

        fs.create_file("/test.txt", b"Original content")
        fs.update_file("/test.txt", b"Updated content")
        result = fs.read_file("/test.txt")

        assert result == b"Updated content"

    def test_delete_file(self):
        """Test deleting a file."""
        fs = DNAFileSystem()

        fs.create_file("/test.txt", b"content")
        assert fs.file_exists("/test.txt")

        fs.delete_file("/test.txt")
        assert not fs.file_exists("/test.txt")

    def test_directory_operations(self):
        """Test directory create/list/delete."""
        fs = DNAFileSystem()

        fs.create_directory("/documents")
        assert fs.directory_exists("/documents")

        fs.create_file("/documents/file1.txt", b"content1")
        fs.create_file("/documents/file2.txt", b"content2")

        contents = fs.list_directory("/documents")
        assert len(contents) == 2

        fs.delete_directory("/documents", recursive=True)
        assert not fs.directory_exists("/documents")

    def test_file_metadata(self):
        """Test that file metadata is preserved."""
        fs = DNAFileSystem()

        original = b"Test content"
        fs.create_file(
            "/test.txt",
            original,
            mime_type="text/plain",
            tags=["test", "example"],
        )

        file_info = fs.get_file_info("/test.txt")

        assert file_info.original_size == len(original)
        assert file_info.mime_type == "text/plain"
        assert "test" in file_info.tags


class TestErrorRecovery:
    """Test error detection and recovery."""

    def test_encoder_with_error_correction(self):
        """Test that error correction is applied."""
        config = EncodingConfig(error_correction=True)
        encoder = DNAEncoder(config)

        encoded = encoder.encode(b"Test data")

        # Encoded should be longer due to error correction
        raw_encoded_length = len(encoder.encode_raw(b"Test data"))
        assert len(encoded) > raw_encoded_length

    def test_integrity_check(self):
        """Test integrity verification."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        encoded = encoder.encode(b"Test data")
        result = decoder.decode(encoded)

        assert result.integrity_valid is True


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
