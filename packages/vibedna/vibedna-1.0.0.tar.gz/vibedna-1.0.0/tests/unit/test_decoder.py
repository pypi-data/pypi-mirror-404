"""
VibeDNA Decoder Tests

Unit tests for the DNA decoder module.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

import pytest
from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme
from vibedna.core.decoder import DNADecoder, DecodeResult, InvalidSequenceError


class TestDNADecoder:
    """Test suite for DNA decoder."""

    def test_init(self):
        """Test decoder initialization."""
        decoder = DNADecoder()
        assert decoder is not None

    def test_decode_raw_quaternary(self):
        """Test raw quaternary decoding."""
        decoder = DNADecoder()

        # AAAA = 00000000 = 0x00
        result = decoder.decode_raw("AAAA", "quaternary")
        assert result == b"\x00"

        # GGGG = 11111111 = 0xFF
        result = decoder.decode_raw("GGGG", "quaternary")
        assert result == b"\xFF"

        # CCCC = 10101010 = 0xAA
        result = decoder.decode_raw("CCCC", "quaternary")
        assert result == b"\xAA"

        # TTTT = 01010101 = 0x55
        result = decoder.decode_raw("TTTT", "quaternary")
        assert result == b"\x55"

    def test_decode_raw_string(self):
        """Test decoding that produces readable text."""
        decoder = DNADecoder()

        # Encode "Hi" and decode it back
        encoder = DNAEncoder()
        dna = encoder.encode_raw("Hi")
        result = decoder.decode_raw(dna, "quaternary")

        assert result == b"Hi"

    def test_encode_decode_roundtrip(self):
        """Data should survive encode-decode cycle."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        test_data = b"Hello, VibeDNA World!"
        encoded = encoder.encode(test_data, filename="test.txt")
        decoded = decoder.decode(encoded)

        assert decoded.data == test_data
        assert decoded.filename == "test.txt"

    def test_decode_result_attributes(self):
        """Test DecodeResult has all expected attributes."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        encoded = encoder.encode(b"Test", filename="test.txt", mime_type="text/plain")
        result = decoder.decode(encoded)

        assert isinstance(result, DecodeResult)
        assert hasattr(result, "data")
        assert hasattr(result, "filename")
        assert hasattr(result, "mime_type")
        assert hasattr(result, "encoding_scheme")
        assert hasattr(result, "errors_detected")
        assert hasattr(result, "errors_corrected")
        assert hasattr(result, "integrity_valid")

    def test_validate_sequence_valid(self):
        """Test validation of valid sequence."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        encoded = encoder.encode(b"Test")
        is_valid, issues = decoder.validate_sequence(encoded)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_sequence_invalid(self):
        """Test validation of invalid sequence."""
        decoder = DNADecoder()

        # Invalid characters
        is_valid, issues = decoder.validate_sequence("ATCGXYZ")
        assert is_valid is False
        assert len(issues) > 0

    def test_detect_encoding_scheme_quaternary(self):
        """Test detection of quaternary scheme."""
        encoder = DNAEncoder(EncodingConfig(scheme=EncodingScheme.QUATERNARY))
        decoder = DNADecoder()

        encoded = encoder.encode(b"Test")
        scheme = decoder.detect_encoding_scheme(encoded)

        assert scheme == "quaternary"

    def test_detect_encoding_scheme_balanced_gc(self):
        """Test detection of balanced GC scheme."""
        encoder = DNAEncoder(EncodingConfig(scheme=EncodingScheme.BALANCED_GC))
        decoder = DNADecoder()

        encoded = encoder.encode(b"Test")
        scheme = decoder.detect_encoding_scheme(encoded)

        assert scheme == "balanced_gc"

    def test_decode_with_lowercase(self):
        """Test decoding works with lowercase input."""
        decoder = DNADecoder()

        result = decoder.decode_raw("aaaa", "quaternary")
        assert result == b"\x00"

    def test_decode_with_whitespace(self):
        """Test decoding ignores whitespace."""
        decoder = DNADecoder()

        result = decoder.decode_raw("AA AA", "quaternary")
        assert result == b"\x00"

    def test_binary_to_bytes(self):
        """Test binary to bytes conversion."""
        decoder = DNADecoder()

        assert decoder._binary_to_bytes("00000000") == b"\x00"
        assert decoder._binary_to_bytes("11111111") == b"\xFF"
        assert decoder._binary_to_bytes("01000001") == b"A"


class TestRoundtrip:
    """Test encode-decode roundtrip for various data types."""

    def test_roundtrip_text(self):
        """Test roundtrip with text data."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        original = b"The quick brown fox jumps over the lazy dog."
        encoded = encoder.encode(original, filename="text.txt")
        result = decoder.decode(encoded)

        assert result.data == original

    def test_roundtrip_binary(self):
        """Test roundtrip with binary data."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        # Random binary data
        original = bytes(range(256))
        encoded = encoder.encode(original, filename="binary.bin")
        result = decoder.decode(encoded)

        assert result.data == original

    def test_roundtrip_all_schemes(self):
        """Test roundtrip with all encoding schemes."""
        decoder = DNADecoder()
        original = b"Test data for all schemes"

        for scheme in EncodingScheme:
            config = EncodingConfig(scheme=scheme)
            encoder = DNAEncoder(config)

            encoded = encoder.encode(original, filename="test.txt")
            result = decoder.decode(encoded)

            assert result.data == original, \
                f"Roundtrip failed for scheme {scheme.value}"

    def test_roundtrip_empty(self):
        """Test roundtrip with empty data."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        original = b""
        encoded = encoder.encode(original, filename="empty.txt")
        result = decoder.decode(encoded)

        assert result.data == original

    def test_roundtrip_large_data(self):
        """Test roundtrip with larger data."""
        encoder = DNAEncoder()
        decoder = DNADecoder()

        # 10KB of data
        original = b"X" * 10240
        encoded = encoder.encode(original, filename="large.bin")
        result = decoder.decode(encoded)

        assert result.data == original


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
