"""
VibeDNA API Schemas

Pydantic models for request/response validation.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class EncodingScheme(str, Enum):
    """Available encoding schemes."""
    quaternary = "quaternary"
    balanced_gc = "balanced_gc"
    rll = "rll"
    triplet = "triplet"


# ═══════════════════════════════════════════════════════════════
# Encoding Schemas
# ═══════════════════════════════════════════════════════════════

class EncodeRequest(BaseModel):
    """Request to encode data to DNA."""
    data: str = Field(..., description="Base64-encoded binary data")
    filename: Optional[str] = Field("untitled", description="Original filename")
    mime_type: Optional[str] = Field("application/octet-stream")
    scheme: EncodingScheme = Field(EncodingScheme.quaternary)
    error_correction: bool = Field(True, description="Enable RS error correction")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": "SGVsbG8gV29ybGQh",
                    "filename": "hello.txt",
                    "mime_type": "text/plain",
                    "scheme": "quaternary",
                    "error_correction": True,
                }
            ]
        }
    }


class EncodeResponse(BaseModel):
    """Response from encoding operation."""
    dna_sequence: str
    nucleotide_count: int
    compression_ratio: float
    encoding_scheme: str
    checksum: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "dna_sequence": "ATCGATCG...",
                    "nucleotide_count": 1024,
                    "compression_ratio": 0.5,
                    "encoding_scheme": "quaternary",
                    "checksum": "abc123",
                }
            ]
        }
    }


class DecodeRequest(BaseModel):
    """Request to decode DNA to binary."""
    dna_sequence: str = Field(..., description="DNA sequence to decode")
    verify_checksum: bool = Field(True)


class DecodeResponse(BaseModel):
    """Response from decoding operation."""
    data: str  # Base64-encoded
    filename: str
    mime_type: str
    original_size: int
    errors_corrected: int
    integrity_valid: bool


class QuickEncodeRequest(BaseModel):
    """Request for quick encoding (no headers)."""
    text: str = Field(..., description="Text to encode")
    scheme: EncodingScheme = Field(EncodingScheme.quaternary)


class QuickDecodeRequest(BaseModel):
    """Request for quick decoding (no headers)."""
    dna_sequence: str = Field(..., description="DNA sequence")
    scheme: EncodingScheme = Field(EncodingScheme.quaternary)


# ═══════════════════════════════════════════════════════════════
# Computation Schemas
# ═══════════════════════════════════════════════════════════════

class LogicGate(str, Enum):
    """Available logic gates."""
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    NOT = "NOT"
    NAND = "NAND"
    NOR = "NOR"
    XNOR = "XNOR"


class ArithmeticOperation(str, Enum):
    """Available arithmetic operations."""
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"


class ComputeRequest(BaseModel):
    """Request for DNA computation."""
    operation: str = Field(..., description="Operation: AND, OR, XOR, NOT, ADD, etc.")
    sequence_a: str = Field(..., description="First DNA sequence")
    sequence_b: Optional[str] = Field(None, description="Second DNA sequence")


class ComputeResponse(BaseModel):
    """Response from computation."""
    result: str
    operation: str
    overflow: Optional[bool] = None


class GateRequest(BaseModel):
    """Request for logic gate operation."""
    gate: LogicGate
    sequence_a: str
    sequence_b: Optional[str] = None


class ArithmeticRequest(BaseModel):
    """Request for arithmetic operation."""
    operation: ArithmeticOperation
    sequence_a: str
    sequence_b: str


# ═══════════════════════════════════════════════════════════════
# File System Schemas
# ═══════════════════════════════════════════════════════════════

class FileInfo(BaseModel):
    """File information."""
    id: str
    name: str
    path: str
    original_size: int
    dna_length: int
    mime_type: str
    created_at: datetime
    modified_at: datetime
    encoding_scheme: str
    tags: List[str] = []


class DirectoryInfo(BaseModel):
    """Directory information."""
    id: str
    name: str
    path: str
    created_at: datetime


class CreateFileRequest(BaseModel):
    """Request to create a file."""
    path: str = Field(..., description="File path in DNA filesystem")
    data: str = Field(..., description="Base64-encoded data")
    mime_type: Optional[str] = Field("application/octet-stream")
    encoding_scheme: Optional[str] = Field("quaternary")
    tags: Optional[List[str]] = Field(default_factory=list)


class StorageStats(BaseModel):
    """Storage statistics."""
    total_files: int
    total_directories: int
    total_binary_size: int
    total_dna_length: int
    expansion_ratio: float
    backend: str


# ═══════════════════════════════════════════════════════════════
# Validation Schemas
# ═══════════════════════════════════════════════════════════════

class ValidateRequest(BaseModel):
    """Request to validate a sequence."""
    sequence: str = Field(..., description="DNA sequence to validate")
    require_header: bool = Field(False)
    require_footer: bool = Field(False)


class ValidateResponse(BaseModel):
    """Response from validation."""
    is_valid: bool
    issues: List[str]


class SequenceInfo(BaseModel):
    """Information about a DNA sequence."""
    length: int
    gc_content: float
    detected_scheme: str
    nucleotide_counts: Dict[str, int]
    has_header: bool
    has_footer: bool


# ═══════════════════════════════════════════════════════════════
# Error Schemas
# ═══════════════════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
