# VibeDNA Core MCP Server
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Core MCP Server for VibeDNA encoding and decoding operations.

Provides tools for:
- Binary to DNA encoding
- DNA to binary decoding
- Sequence validation
- Sequence information retrieval
"""

import base64
from typing import Any, Dict, Optional

from vibedna.agents.mcp_servers.base_server import (
    BaseMCPServer,
    MCPServerConfig,
    MCPTool,
    MCPToolParameter,
    MCPResource,
    MCPPrompt,
    TransportType,
)
from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme
from vibedna.core.decoder import DNADecoder


class VibeDNACoreMCPServer(BaseMCPServer):
    """
    Core MCP Server for VibeDNA encoding/decoding operations.

    Tools:
    - encode_binary: Encode binary data to DNA sequence
    - decode_dna: Decode DNA sequence to binary
    - validate_sequence: Validate DNA sequence format
    - get_sequence_info: Get information about a DNA sequence

    Resources:
    - encoding_schemes: Available encoding schemes
    """

    def __init__(self, config: Optional[MCPServerConfig] = None):
        """Initialize the Core MCP server."""
        if config is None:
            config = MCPServerConfig(
                name="vibedna-core",
                version="1.0.0",
                description="Core VibeDNA encoding/decoding MCP server",
                transport=TransportType.SSE,
                url="https://mcp.vibedna.vibecaas.com/core",
                port=8090,
            )
        super().__init__(config)

        # Initialize core components
        self._encoder = DNAEncoder()
        self._decoder = DNADecoder()

    def _register_tools(self) -> None:
        """Register core encoding/decoding tools."""

        # encode_binary tool
        self.register_tool(MCPTool(
            name="encode_binary",
            description="Encode binary data to DNA sequence using specified scheme",
            parameters=[
                MCPToolParameter(
                    name="data",
                    param_type="string",
                    description="Base64-encoded binary data to encode",
                    required=True,
                ),
                MCPToolParameter(
                    name="scheme",
                    param_type="string",
                    description="Encoding scheme to use",
                    required=False,
                    default="quaternary",
                    enum=["quaternary", "balanced_gc", "rll", "triplet"],
                ),
                MCPToolParameter(
                    name="filename",
                    param_type="string",
                    description="Original filename for metadata",
                    required=False,
                    default="untitled",
                ),
                MCPToolParameter(
                    name="add_error_correction",
                    param_type="boolean",
                    description="Whether to add error correction",
                    required=False,
                    default=True,
                ),
            ],
            handler=self._encode_binary,
        ))

        # decode_dna tool
        self.register_tool(MCPTool(
            name="decode_dna",
            description="Decode DNA sequence back to binary data",
            parameters=[
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence to decode",
                    required=True,
                ),
                MCPToolParameter(
                    name="verify",
                    param_type="boolean",
                    description="Whether to verify checksum",
                    required=False,
                    default=True,
                ),
            ],
            handler=self._decode_dna,
        ))

        # validate_sequence tool
        self.register_tool(MCPTool(
            name="validate_sequence",
            description="Validate DNA sequence format and structure",
            parameters=[
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence to validate",
                    required=True,
                ),
            ],
            handler=self._validate_sequence,
        ))

        # get_sequence_info tool
        self.register_tool(MCPTool(
            name="get_sequence_info",
            description="Get information about a DNA sequence",
            parameters=[
                MCPToolParameter(
                    name="sequence",
                    param_type="string",
                    description="DNA sequence to analyze",
                    required=True,
                ),
            ],
            handler=self._get_sequence_info,
        ))

    def _register_resources(self) -> None:
        """Register core resources."""

        # encoding_schemes resource
        self.register_resource(MCPResource(
            name="encoding_schemes",
            description="Available encoding schemes and their properties",
            uri="vibedna://schemes",
            mime_type="application/json",
            handler=self._get_encoding_schemes,
        ))

    def _register_prompts(self) -> None:
        """Register core prompts."""

        self.register_prompt(MCPPrompt(
            name="encode_file",
            description="Encode a file with optimal settings based on type",
            arguments=[
                {"name": "file_type", "description": "Type of file being encoded", "required": True},
            ],
            template="""Encode a {file_type} file to DNA:

1. For text files: Use quaternary encoding for maximum density
2. For images: Use balanced_gc encoding for synthesis compatibility
3. For sensitive data: Use triplet encoding for maximum error tolerance
4. For streaming: Use rll encoding for sequencing accuracy

Please provide the file data as base64 and I will encode it appropriately.""",
        ))

    async def _encode_binary(
        self,
        data: str,
        scheme: str = "quaternary",
        filename: str = "untitled",
        add_error_correction: bool = True,
    ) -> Dict[str, Any]:
        """Encode binary data to DNA sequence."""
        try:
            # Decode base64 input
            binary_data = base64.b64decode(data)

            # Map scheme string to enum
            scheme_map = {
                "quaternary": EncodingScheme.QUATERNARY,
                "balanced_gc": EncodingScheme.BALANCED_GC,
                "rll": EncodingScheme.RUN_LENGTH_LIMITED,
                "triplet": EncodingScheme.REDUNDANT_TRIPLET,
            }
            encoding_scheme = scheme_map.get(scheme, EncodingScheme.QUATERNARY)

            # Configure encoder
            config = EncodingConfig(
                scheme=encoding_scheme,
                filename=filename,
                add_error_correction=add_error_correction,
            )
            encoder = DNAEncoder(config)

            # Encode
            result = encoder.encode(binary_data)

            return {
                "sequence": result.sequence,
                "nucleotide_count": len(result.sequence),
                "block_count": result.block_count,
                "scheme": scheme,
                "checksum": result.checksum,
                "metadata": {
                    "original_size": len(binary_data),
                    "filename": filename,
                    "gc_content": self._calculate_gc(result.sequence),
                },
            }
        except Exception as e:
            raise ValueError(f"Encoding failed: {str(e)}")

    async def _decode_dna(
        self,
        sequence: str,
        verify: bool = True,
    ) -> Dict[str, Any]:
        """Decode DNA sequence to binary data."""
        try:
            # Validate sequence
            sequence = sequence.upper().strip()
            if not all(c in "ATCG" for c in sequence):
                raise ValueError("Invalid DNA sequence: contains non-ATCG characters")

            # Decode
            result = self._decoder.decode(sequence, verify_checksum=verify)

            return {
                "data": base64.b64encode(result.data).decode("utf-8"),
                "metadata": {
                    "filename": result.filename,
                    "mime_type": result.mime_type,
                    "original_size": len(result.data),
                    "scheme": result.scheme,
                    "errors_corrected": result.errors_corrected,
                },
            }
        except Exception as e:
            raise ValueError(f"Decoding failed: {str(e)}")

    async def _validate_sequence(self, sequence: str) -> Dict[str, Any]:
        """Validate DNA sequence format."""
        issues = []
        warnings = []

        sequence = sequence.upper().strip()

        # Check for invalid characters
        invalid_chars = set(sequence) - set("ATCG")
        if invalid_chars:
            issues.append({
                "code": "INVALID_CHARS",
                "severity": "error",
                "message": f"Invalid characters found: {invalid_chars}",
            })

        # Check minimum length
        if len(sequence) < 256:
            issues.append({
                "code": "TOO_SHORT",
                "severity": "error",
                "message": "Sequence too short to contain valid header",
            })
        else:
            # Check magic sequence
            if sequence[:8] != "ATCGATCG":
                issues.append({
                    "code": "MAGIC_MISSING",
                    "severity": "error",
                    "message": "VibeDNA magic sequence not found",
                })

            # Check footer
            if len(sequence) >= 32 and sequence[-32:-24] != "GCTAGCTA":
                issues.append({
                    "code": "FOOTER_MISSING",
                    "severity": "error",
                    "message": "VibeDNA footer marker not found",
                })

        # GC content warning
        gc_content = self._calculate_gc(sequence)
        if gc_content < 0.3 or gc_content > 0.7:
            warnings.append({
                "code": "GC_IMBALANCE",
                "severity": "warning",
                "message": f"GC content ({gc_content:.1%}) outside optimal range",
            })

        # Homopolymer check
        max_run = self._find_max_run(sequence)
        if max_run > 5:
            warnings.append({
                "code": "LONG_HOMOPOLYMER",
                "severity": "warning",
                "message": f"Long homopolymer run detected: {max_run} nucleotides",
            })

        is_valid = not any(i["severity"] == "error" for i in issues)

        return {
            "valid": is_valid,
            "issues": issues + warnings,
            "metadata": {
                "length": len(sequence),
                "gc_content": gc_content,
                "max_homopolymer": max_run,
            },
        }

    async def _get_sequence_info(self, sequence: str) -> Dict[str, Any]:
        """Get detailed information about a DNA sequence."""
        sequence = sequence.upper().strip()

        # Calculate nucleotide distribution
        counts = {"A": 0, "T": 0, "C": 0, "G": 0}
        for nuc in sequence:
            if nuc in counts:
                counts[nuc] += 1

        total = len(sequence)
        distribution = {k: v / total if total > 0 else 0 for k, v in counts.items()}

        # GC content
        gc_content = (counts["G"] + counts["C"]) / total if total > 0 else 0

        # Try to detect encoding scheme
        detected_scheme = self._detect_scheme(sequence)

        # Try to parse header info
        header_info = {}
        if len(sequence) >= 256:
            header_info = self._parse_header_info(sequence[:256])

        return {
            "length": total,
            "gc_content": gc_content,
            "nucleotide_distribution": distribution,
            "max_homopolymer": self._find_max_run(sequence),
            "detected_scheme": detected_scheme,
            "header_info": header_info,
            "encoding_valid": len(sequence) >= 256 and sequence[:8] == "ATCGATCG",
        }

    def _get_encoding_schemes(self) -> Dict[str, Any]:
        """Get information about available encoding schemes."""
        return {
            "schemes": [
                {
                    "id": "quaternary",
                    "name": "Quaternary",
                    "description": "2 bits per nucleotide, maximum density",
                    "density_bits_per_nt": 2.0,
                    "error_tolerance": "low",
                    "synthesis_compatible": True,
                    "mapping": {"00": "A", "01": "T", "10": "C", "11": "G"},
                },
                {
                    "id": "balanced_gc",
                    "name": "Balanced GC",
                    "description": "Rotating mapping to maintain 40-60% GC content",
                    "density_bits_per_nt": 1.9,
                    "error_tolerance": "medium",
                    "synthesis_compatible": True,
                    "use_case": "DNA synthesis compatibility",
                },
                {
                    "id": "rll",
                    "name": "Run-Length Limited",
                    "description": "Inserts spacers to prevent homopolymer runs > 3",
                    "density_bits_per_nt": 1.7,
                    "error_tolerance": "medium",
                    "synthesis_compatible": True,
                    "use_case": "Sequencing accuracy",
                },
                {
                    "id": "triplet",
                    "name": "Redundant Triplet",
                    "description": "Each bit encoded as 3 nucleotides for redundancy",
                    "density_bits_per_nt": 0.67,
                    "error_tolerance": "high",
                    "synthesis_compatible": True,
                    "mapping": {"0": "ATC", "1": "GAC"},
                    "use_case": "Maximum error tolerance",
                },
            ],
        }

    def _calculate_gc(self, sequence: str) -> float:
        """Calculate GC content of a sequence."""
        if not sequence:
            return 0.0
        gc_count = sum(1 for c in sequence.upper() if c in "GC")
        return gc_count / len(sequence)

    def _find_max_run(self, sequence: str) -> int:
        """Find the maximum homopolymer run length."""
        if not sequence:
            return 0

        max_run = 1
        current_run = 1

        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i - 1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1

        return max_run

    def _detect_scheme(self, sequence: str) -> str:
        """Attempt to detect the encoding scheme used."""
        if len(sequence) < 256:
            return "unknown"

        # Try to read from header
        scheme_code = sequence[12:16]
        scheme_map = {
            "AAAA": "quaternary",
            "AAAT": "balanced_gc",
            "AATC": "rll",
            "AATG": "triplet",
        }

        if scheme_code in scheme_map:
            return scheme_map[scheme_code]

        # Statistical detection
        gc = self._calculate_gc(sequence)
        max_run = self._find_max_run(sequence)

        # Triplet detection: look for ATC/GAC patterns
        atc_count = sequence.count("ATC")
        gac_count = sequence.count("GAC")
        triplet_ratio = (atc_count + gac_count) / (len(sequence) / 3) if len(sequence) >= 3 else 0

        if triplet_ratio > 0.8:
            return "triplet"
        if max_run <= 3:
            return "rll"
        if 0.45 <= gc <= 0.55:
            return "balanced_gc"

        return "quaternary"

    def _parse_header_info(self, header: str) -> Dict[str, Any]:
        """Parse header information from sequence."""
        info = {}

        if len(header) >= 8:
            info["magic"] = header[:8]
            info["magic_valid"] = header[:8] == "ATCGATCG"

        if len(header) >= 12:
            info["version"] = header[8:12]

        if len(header) >= 16:
            info["scheme_code"] = header[12:16]

        return info
