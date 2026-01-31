"""
VibeDNA Encoder Tests

Unit tests for the DNA encoder module.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

import pytest
from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme


class TestDNAEncoder:
    """Test suite for DNA encoder."""

    def test_init_default_config(self):
        """Test encoder initialization with default config."""
        encoder = DNAEncoder()
        assert encoder.config.scheme == EncodingScheme.QUATERNARY
        assert encoder.config.error_correction is True

    def test_init_custom_config(self):
        """Test encoder initialization with custom config."""
        config = EncodingConfig(
            scheme=EncodingScheme.BALANCED_GC,
            error_correction=False,
        )
        encoder = DNAEncoder(config)
        assert encoder.config.scheme == EncodingScheme.BALANCED_GC
        assert encoder.config.error_correction is False

    def test_encode_empty_data(self):
        """Encoding empty data should produce valid header-only sequence."""
        encoder = DNAEncoder()
        result = encoder.encode(b"", filename="empty.txt")
        assert len(result) > 0
        assert result.startswith("ATCGATCG")  # Magic sequence

    def test_encode_single_byte(self):
        """Single byte should encode correctly."""
        encoder = DNAEncoder()
        # Raw encoding: 0x00 = 00000000 = AAAA
        result = encoder.encode_raw(b"\x00")
        assert result == "AAAA"

    def test_encode_known_values(self):
        """Test encoding of known binary-to-DNA mappings."""
        encoder = DNAEncoder()

        # 0x00 = 00000000 -> AAAA
        assert encoder.encode_raw(b"\x00") == "AAAA"

        # 0xFF = 11111111 -> GGGG
        assert encoder.encode_raw(b"\xFF") == "GGGG"

        # 0xAA = 10101010 -> CCCC
        assert encoder.encode_raw(b"\xAA") == "CCCC"

        # 0x55 = 01010101 -> TTTT
        assert encoder.encode_raw(b"\x55") == "TTTT"

    def test_encode_string(self):
        """Test encoding string input."""
        encoder = DNAEncoder()
        result = encoder.encode("Hello", filename="hello.txt")
        assert len(result) > 0
        assert isinstance(result, str)

    def test_encode_bytes(self):
        """Test encoding bytes input."""
        encoder = DNAEncoder()
        result = encoder.encode(b"Hello", filename="hello.txt")
        assert len(result) > 0
        assert isinstance(result, str)

    def test_encode_with_header(self):
        """Encoded sequence should have proper header."""
        encoder = DNAEncoder()
        result = encoder.encode(b"Test", filename="test.txt")

        # Check magic sequence
        assert result[:8] == "ATCGATCG"

    def test_quaternary_scheme(self):
        """Test quaternary encoding scheme."""
        config = EncodingConfig(scheme=EncodingScheme.QUATERNARY)
        encoder = DNAEncoder(config)

        result = encoder.encode_raw(b"AB")
        # A = 0x41 = 01000001 -> TAAT
        # B = 0x42 = 01000010 -> TAAC
        assert result == "TAATTAAC"

    def test_balanced_gc_scheme(self):
        """Test balanced GC encoding scheme."""
        config = EncodingConfig(scheme=EncodingScheme.BALANCED_GC)
        encoder = DNAEncoder(config)

        result = encoder.encode_raw(b"AAAA")  # 16 bytes to test rotation
        assert len(result) > 0

        # GC content should be relatively balanced
        gc_count = sum(1 for n in result if n in "GC")
        gc_ratio = gc_count / len(result)
        # Allow some tolerance
        assert 0.2 <= gc_ratio <= 0.8

    def test_rll_no_long_runs(self):
        """RLL encoding should prevent long homopolymer runs."""
        config = EncodingConfig(scheme=EncodingScheme.RUN_LENGTH_LIMITED)
        encoder = DNAEncoder(config)

        # Encode data that would normally create long runs
        result = encoder.encode_raw(b"\x00\x00\x00\x00")

        # Check for runs longer than 3
        max_run = 1
        current_run = 1
        for i in range(1, len(result)):
            if result[i] == result[i - 1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1

        assert max_run <= 3

    def test_triplet_redundancy(self):
        """Triplet encoding should use 3x nucleotides."""
        config = EncodingConfig(scheme=EncodingScheme.REDUNDANT_TRIPLET)
        encoder = DNAEncoder(config)

        # 1 byte = 8 bits, each bit = 3 nucleotides = 24 nucleotides
        result = encoder.encode_raw(b"A")
        assert len(result) == 24

    def test_bytes_to_binary(self):
        """Test bytes to binary conversion."""
        encoder = DNAEncoder()

        assert encoder._bytes_to_binary(b"\x00") == "00000000"
        assert encoder._bytes_to_binary(b"\xFF") == "11111111"
        assert encoder._bytes_to_binary(b"\x41") == "01000001"

    def test_checksum_generation(self):
        """Test checksum calculation."""
        encoder = DNAEncoder()

        checksum1 = encoder._calculate_checksum("ATCGATCG")
        checksum2 = encoder._calculate_checksum("ATCGATCG")
        checksum3 = encoder._calculate_checksum("GCTAGCTA")

        # Same input should produce same checksum
        assert checksum1 == checksum2

        # Different input should produce different checksum
        assert checksum1 != checksum3

    def test_config_validation_gc_balance(self):
        """Test config validation for GC balance."""
        with pytest.raises(ValueError):
            config = EncodingConfig(gc_balance_target=0.1)
            DNAEncoder(config)

    def test_config_validation_homopolymer(self):
        """Test config validation for homopolymer run."""
        with pytest.raises(ValueError):
            config = EncodingConfig(max_homopolymer_run=0)
            DNAEncoder(config)

    def test_config_validation_block_size(self):
        """Test config validation for block size."""
        with pytest.raises(ValueError):
            config = EncodingConfig(block_size=32)
            DNAEncoder(config)


class TestEncodingSchemes:
    """Test individual encoding schemes."""

    def test_all_schemes_produce_valid_dna(self):
        """All schemes should produce valid DNA sequences."""
        test_data = b"Test data for encoding"
        valid_nucleotides = set("ATCG")

        for scheme in EncodingScheme:
            config = EncodingConfig(scheme=scheme)
            encoder = DNAEncoder(config)
            result = encoder.encode_raw(test_data)

            # Check all characters are valid nucleotides
            assert all(n in valid_nucleotides for n in result), \
                f"Scheme {scheme.value} produced invalid nucleotides"

    def test_schemes_have_expected_expansion(self):
        """Test that schemes have expected expansion ratios."""
        test_data = b"X" * 100  # 100 bytes

        # Quaternary: 2 bits per nucleotide = 4x expansion (100 bytes = 800 bits = 400 nt)
        config = EncodingConfig(scheme=EncodingScheme.QUATERNARY, error_correction=False)
        encoder = DNAEncoder(config)
        result = encoder.encode_raw(test_data)
        assert len(result) == 400

        # Triplet: 1 bit per 3 nucleotides = 24x expansion (100 bytes = 800 bits = 2400 nt)
        config = EncodingConfig(scheme=EncodingScheme.REDUNDANT_TRIPLET, error_correction=False)
        encoder = DNAEncoder(config)
        result = encoder.encode_raw(test_data)
        assert len(result) == 2400


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
