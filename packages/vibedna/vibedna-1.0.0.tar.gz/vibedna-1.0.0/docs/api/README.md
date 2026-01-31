# VibeDNA API Documentation

**Version 1.0.0** | Binary to DNA Encoding and Computation Platform

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [REST API Endpoints](#rest-api-endpoints)
4. [Python SDK Usage](#python-sdk-usage)
5. [CLI Commands Reference](#cli-commands-reference)
6. [Core Module APIs](#core-module-apis)
   - [Encoder API](#encoder-api)
   - [Decoder API](#decoder-api)
   - [Compute API](#compute-api)
   - [Storage API](#storage-api)
   - [Error Correction API](#error-correction-api)
7. [Request/Response Formats](#requestresponse-formats)
8. [Error Codes and Handling](#error-codes-and-handling)
9. [Rate Limits and Best Practices](#rate-limits-and-best-practices)
10. [Code Examples](#code-examples)

---

## Overview

VibeDNA is a comprehensive platform for converting binary data to DNA sequences, performing computations on DNA-encoded data, and managing files in a DNA-based virtual file system.

### Key Features

- **Encoding**: Convert any binary data to DNA sequences using multiple encoding schemes
- **Decoding**: Recover original data from DNA with automatic error correction
- **Computation**: Perform logic and arithmetic operations directly on DNA sequences
- **Storage**: Virtual file system with DNA-encoded storage backend
- **Error Correction**: Reed-Solomon based error correction optimized for DNA (GF(4))

### Encoding Schemes

| Scheme | Description | Density | Error Tolerance |
|--------|-------------|---------|-----------------|
| `quaternary` | Standard 2-bit per nucleotide (A=00, T=01, C=10, G=11) | High | Standard |
| `balanced_gc` | GC-content balanced encoding with rotation | Medium | Standard |
| `rll` | Run-length limited (prevents homopolymer runs) | Medium | High |
| `triplet` | Redundant triplet encoding (3 nucleotides per bit) | Low | Very High |

### Nucleotide Mappings

```
Standard Quaternary:
  00 -> A (Adenine)
  01 -> T (Thymine)
  10 -> C (Cytosine)
  11 -> G (Guanine)

Complement (NOT operation):
  A <-> G
  T <-> C
```

---

## Authentication

The VibeDNA REST API currently supports open access for development environments. For production deployments, configure authentication through environment variables:

```bash
# .env configuration
VIBEDNA_API_KEY=your-api-key
VIBEDNA_API_SECRET=your-api-secret
```

### API Key Authentication

```bash
curl -X POST https://api.vibedna.com/encode \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data": "SGVsbG8gV29ybGQh"}'
```

### SDK Authentication

```python
from vibedna import DNAEncoder

# Configure with API key for cloud operations
encoder = DNAEncoder(api_key="your-api-key")
```

---

## REST API Endpoints

### Base URL

```
Development: http://localhost:8000
Production:  https://api.vibedna.com
```

### Information Endpoints

#### GET /

API information and health check.

```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "name": "VibeDNA API",
  "version": "1.0.0",
  "status": "operational",
  "documentation": "/docs",
  "openapi": "/openapi.json",
  "copyright": "2026 VibeDNA powered by VibeCaaS.com"
}
```

#### GET /health

Health check endpoint.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-30T12:00:00.000000"
}
```

---

### Encoding Endpoints

#### POST /encode

Encode binary data to DNA sequence.

**Request:**
```bash
curl -X POST http://localhost:8000/encode \
  -H "Content-Type: application/json" \
  -d '{
    "data": "SGVsbG8gV29ybGQh",
    "filename": "hello.txt",
    "mime_type": "text/plain",
    "scheme": "quaternary",
    "error_correction": true
  }'
```

**Request Body Schema:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `data` | string | Yes | - | Base64-encoded binary data |
| `filename` | string | No | "untitled" | Original filename |
| `mime_type` | string | No | "application/octet-stream" | MIME type |
| `scheme` | string | No | "quaternary" | Encoding scheme |
| `error_correction` | boolean | No | true | Enable Reed-Solomon EC |

**Response:**
```json
{
  "dna_sequence": "ATCGATCGAAATAAAA...",
  "nucleotide_count": 1024,
  "compression_ratio": 0.5,
  "encoding_scheme": "quaternary",
  "checksum": "abc123def456"
}
```

#### POST /encode/file

Encode an uploaded file to DNA sequence.

```bash
curl -X POST http://localhost:8000/encode/file \
  -F "file=@document.pdf" \
  -F "scheme=quaternary" \
  -F "error_correction=true" \
  -F "output_format=fasta"
```

**Query Parameters:**
| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `scheme` | string | "quaternary" | quaternary, balanced_gc, rll, triplet |
| `error_correction` | boolean | true | true, false |
| `output_format` | string | "fasta" | fasta, raw, json |

**Response:** Returns downloadable file with DNA sequence in the specified format.

#### POST /quick/encode

Quick encode text to DNA without headers (raw encoding).

```bash
curl -X POST http://localhost:8000/quick/encode \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello World",
    "scheme": "quaternary"
  }'
```

**Response:**
```json
{
  "dna_sequence": "GCTAGCTACGATCGAT",
  "length": 16
}
```

---

### Decoding Endpoints

#### POST /decode

Decode DNA sequence to binary data.

```bash
curl -X POST http://localhost:8000/decode \
  -H "Content-Type: application/json" \
  -d '{
    "dna_sequence": "ATCGATCGAAATAAAA...",
    "verify_checksum": true
  }'
```

**Response:**
```json
{
  "data": "SGVsbG8gV29ybGQh",
  "filename": "hello.txt",
  "mime_type": "text/plain",
  "original_size": 12,
  "errors_corrected": 0,
  "integrity_valid": true
}
```

#### POST /decode/file

Decode a DNA file and return original binary.

```bash
curl -X POST http://localhost:8000/decode/file \
  -F "file=@sequence.fasta" \
  -F "verify=true" \
  -o recovered_file.bin
```

**Response Headers:**
- `X-VibeDNA-Errors-Corrected`: Number of corrected errors
- `X-VibeDNA-Integrity-Valid`: Checksum verification status

#### POST /quick/decode

Quick decode DNA to text without headers.

```bash
curl -X POST http://localhost:8000/quick/decode \
  -H "Content-Type: application/json" \
  -d '{
    "dna_sequence": "GCTAGCTACGATCGAT",
    "scheme": "quaternary"
  }'
```

**Response:**
```json
{
  "text": "Hello World",
  "size": 11
}
```

---

### Computation Endpoints

#### POST /compute

Perform computation on DNA sequences.

```bash
curl -X POST http://localhost:8000/compute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "XOR",
    "sequence_a": "ATCGATCG",
    "sequence_b": "GCTAGCTA"
  }'
```

**Supported Operations:**
| Operation | Type | Description |
|-----------|------|-------------|
| `AND` | Logic | min(nucleotide values) |
| `OR` | Logic | max(nucleotide values) |
| `XOR` | Logic | (a + b) mod 4 |
| `NOT` | Logic | complement (A<->G, T<->C) |
| `NAND` | Logic | NOT(AND) |
| `NOR` | Logic | NOT(OR) |
| `XNOR` | Logic | NOT(XOR) |
| `ADD` | Arithmetic | Quaternary addition |
| `SUB` | Arithmetic | Quaternary subtraction |
| `MUL` | Arithmetic | Quaternary multiplication |
| `DIV` | Arithmetic | Quaternary division |

**Response:**
```json
{
  "result": "CAGT...",
  "operation": "XOR",
  "overflow": false
}
```

#### POST /compute/gate

Apply a specific logic gate to DNA sequences.

```bash
curl -X POST http://localhost:8000/compute/gate \
  -H "Content-Type: application/json" \
  -d '{
    "gate": "XOR",
    "sequence_a": "ATCGATCG",
    "sequence_b": "GCTAGCTA"
  }'
```

#### POST /compute/arithmetic

Perform arithmetic operations on DNA sequences.

```bash
curl -X POST http://localhost:8000/compute/arithmetic \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "ADD",
    "sequence_a": "ATCGATCG",
    "sequence_b": "GCTAGCTA"
  }'
```

**Response (Division):**
```json
{
  "quotient": "ATCG",
  "remainder": "GCTA",
  "operation": "DIV"
}
```

---

### File System Endpoints

#### GET /fs/list

List files in DNA storage.

```bash
curl "http://localhost:8000/fs/list?path=/"
```

**Response:**
```json
{
  "path": "/",
  "files": [
    {
      "id": "abc123",
      "name": "hello.txt",
      "path": "/hello.txt",
      "original_size": 12,
      "dna_length": 1024,
      "mime_type": "text/plain",
      "created_at": "2026-01-30T12:00:00",
      "modified_at": "2026-01-30T12:00:00",
      "encoding_scheme": "quaternary",
      "tags": []
    }
  ],
  "directories": [],
  "total_items": 1
}
```

#### POST /fs/store

Store a file in DNA file system.

```bash
curl -X POST http://localhost:8000/fs/store \
  -F "file=@document.pdf" \
  -F "path=/documents" \
  -F "tags=important,archive"
```

#### GET /fs/retrieve/{file_path}

Retrieve a file from DNA storage.

```bash
curl http://localhost:8000/fs/retrieve/documents/report.pdf \
  -o report.pdf
```

#### DELETE /fs/delete/{file_path}

Delete a file from DNA storage.

```bash
curl -X DELETE http://localhost:8000/fs/delete/documents/old_file.txt
```

#### GET /fs/stats

Get DNA storage statistics.

```bash
curl http://localhost:8000/fs/stats
```

**Response:**
```json
{
  "total_files": 42,
  "total_directories": 5,
  "total_binary_size": 1048576,
  "total_dna_length": 2097152,
  "expansion_ratio": 2.0,
  "backend": "memory"
}
```

#### GET /fs/sequence/{file_path}

Get raw DNA sequence for a file.

```bash
curl http://localhost:8000/fs/sequence/hello.txt
```

---

### Validation Endpoints

#### POST /validate

Validate DNA sequence structure.

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": "ATCGATCGAAATAAAA...",
    "require_header": true,
    "require_footer": true
  }'
```

**Response:**
```json
{
  "is_valid": true,
  "issues": []
}
```

#### GET /info/{sequence}

Get detailed information about a DNA sequence.

```bash
curl http://localhost:8000/info/ATCGATCGATCGATCG
```

**Response:**
```json
{
  "length": 16,
  "gc_content": 0.5,
  "detected_scheme": "quaternary",
  "nucleotide_counts": {
    "A": 4,
    "T": 4,
    "C": 4,
    "G": 4
  },
  "has_header": false,
  "has_footer": false
}
```

---

## Python SDK Usage

### Installation

```bash
pip install vibedna
```

### Quick Start

```python
from vibedna import DNAEncoder, DNADecoder, EncodingConfig, EncodingScheme

# Basic encoding
encoder = DNAEncoder()
dna = encoder.encode(b"Hello World", filename="hello.txt")
print(f"Encoded to {len(dna)} nucleotides")

# Basic decoding
decoder = DNADecoder()
result = decoder.decode(dna)
print(f"Recovered: {result.data}")
print(f"Filename: {result.filename}")
print(f"Errors corrected: {result.errors_corrected}")
```

### Advanced Configuration

```python
from vibedna import DNAEncoder, EncodingConfig, EncodingScheme

# Configure balanced GC encoding
config = EncodingConfig(
    scheme=EncodingScheme.BALANCED_GC,
    block_size=512,
    error_correction=True,
    gc_balance_target=0.5,
    max_homopolymer_run=3
)

encoder = DNAEncoder(config)
dna = encoder.encode(b"Important data", filename="data.bin")
```

### Working with Files

```python
from vibedna import DNAFileSystem

# Create file system instance
fs = DNAFileSystem(storage_backend="memory")

# Create a file
fs.create_file("/documents/report.txt", b"Report content",
               mime_type="text/plain", tags=["important"])

# Read a file
data = fs.read_file("/documents/report.txt")

# List directory
contents = fs.list_directory("/documents")

# Search files
results = fs.search(query="report", mime_types=["text/plain"])

# Get storage stats
stats = fs.get_storage_stats()
print(f"Total files: {stats['total_files']}")
print(f"Expansion ratio: {stats['expansion_ratio']:.2f}x")
```

### DNA Computation

```python
from vibedna import DNAComputeEngine, DNALogicGate

engine = DNAComputeEngine()

# Logic gate operations
result = engine.apply_gate(DNALogicGate.XOR, "ATCGATCG", "GCTAGCTA")
print(f"XOR result: {result}")

# NOT operation (unary)
inverted = engine.apply_gate(DNALogicGate.NOT, "ATCGATCG")
print(f"NOT result: {inverted}")

# Arithmetic operations
sum_result, overflow = engine.add("ATCGATCG", "GCTAGCTA")
print(f"Sum: {sum_result}, Overflow: {overflow}")

diff_result, underflow = engine.subtract("GCTAGCTA", "ATCGATCG")
print(f"Difference: {diff_result}, Underflow: {underflow}")

product = engine.multiply("ATCG", "GCTA")
print(f"Product: {product}")

quotient, remainder = engine.divide("GCTAGCTA", "ATCG")
print(f"Quotient: {quotient}, Remainder: {remainder}")

# Compound expressions
result = engine.execute_expression(
    "(A AND B) XOR C",
    {"A": "ATCGATCG", "B": "GCTAGCTA", "C": "AATTCCGG"}
)
```

### Stream Encoding (Large Files)

```python
from vibedna import DNAEncoder

def file_chunks(filepath, chunk_size=8192):
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk

encoder = DNAEncoder()

# Stream encode large file
with open("output.dna", "w") as out:
    for dna_chunk in encoder.encode_stream(file_chunks("large_file.bin")):
        out.write(dna_chunk)
```

---

## CLI Commands Reference

### Global Options

```bash
vibedna --version          # Show version
vibedna --quiet            # Suppress banner output
vibedna --help             # Show help
```

### Encoding Commands

#### encode

Encode a file to DNA sequence.

```bash
# Basic encoding
vibedna encode document.pdf

# With options
vibedna encode image.png -o image.dna -s balanced_gc -f fasta

# All options
vibedna encode data.bin \
  --output output.dna \
  --scheme triplet \
  --error-correction \
  --format json
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output file path |
| `--scheme` | `-s` | Encoding scheme (quaternary, balanced_gc, rll, triplet) |
| `--error-correction/--no-error-correction` | `-e` | Enable Reed-Solomon EC |
| `--format` | `-f` | Output format (fasta, raw, json) |

#### decode

Decode DNA sequence back to binary.

```bash
# Basic decoding
vibedna decode document.dna

# With options
vibedna decode sequence.fasta -o recovered.pdf --verify
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output file path |
| `--verify/--no-verify` | | Verify checksum |

#### quick

Quick encode text to DNA (no headers).

```bash
vibedna quick "Hello World"
```

#### quickdecode

Quick decode DNA to text (no headers).

```bash
vibedna quickdecode GCTAGCTACGATCGAT
```

### File System Commands

#### fs ls

List directory contents.

```bash
vibedna fs ls /
vibedna fs ls /documents
```

#### fs cp

Copy file to DNA storage.

```bash
vibedna fs cp local_file.txt /remote/path/file.txt
```

#### fs export

Export file from DNA storage.

```bash
vibedna fs export /dna/path/file.txt ./local_file.txt
```

#### fs stats

Show storage statistics.

```bash
vibedna fs stats
```

### Computation Commands

#### compute gate

Apply logic gate to DNA sequences.

```bash
vibedna compute gate XOR ATCGATCG GCTAGCTA
vibedna compute gate NOT ATCGATCG
vibedna compute gate AND ATCGATCG GCTAGCTA
```

#### compute math

Perform arithmetic on DNA sequences.

```bash
vibedna compute math add ATCGATCG GCTAGCTA
vibedna compute math sub GCTAGCTA ATCGATCG
vibedna compute math mul ATCG GCTA
vibedna compute math div GCTAGCTA ATCG
```

### Utility Commands

#### validate

Validate DNA sequence format.

```bash
vibedna validate ATCGATCGAAATAAAA...
```

#### info

Display information about a DNA sequence.

```bash
vibedna info sequence.fasta
vibedna info ATCGATCGATCGATCG
```

---

## Core Module APIs

### Encoder API

#### Class: DNAEncoder

```python
class DNAEncoder:
    """Converts binary data to DNA sequences."""

    def __init__(self, config: Optional[EncodingConfig] = None):
        """
        Initialize DNA encoder.

        Args:
            config: Encoding configuration (uses defaults if None)
        """

    def encode(
        self,
        data: Union[bytes, str],
        filename: str = "untitled",
        mime_type: str = "application/octet-stream"
    ) -> str:
        """
        Encode binary data to complete DNA sequence.

        Args:
            data: Binary data or string to encode
            filename: Original filename for metadata
            mime_type: MIME type of content

        Returns:
            Complete DNA sequence with headers and error correction
        """

    def encode_stream(
        self,
        data_stream: Generator[bytes, None, None]
    ) -> Generator[str, None, None]:
        """
        Stream-encode for large files.

        Yields DNA chunks as they're encoded.
        """

    def encode_raw(self, data: Union[bytes, str]) -> str:
        """
        Encode without headers/footers (raw encoding).

        Returns:
            Raw DNA sequence without VibeDNA structure
        """
```

#### Class: EncodingConfig

```python
@dataclass
class EncodingConfig:
    """Configuration for DNA encoding operations."""

    scheme: EncodingScheme = EncodingScheme.QUATERNARY
    block_size: int = 512           # Bytes per block
    error_correction: bool = True   # Enable Reed-Solomon
    gc_balance_target: float = 0.5  # Target GC content (0.4-0.6)
    max_homopolymer_run: int = 3    # Max consecutive same nucleotides
```

#### Enum: EncodingScheme

```python
class EncodingScheme(Enum):
    QUATERNARY = "quaternary"           # Standard 2-bit per nucleotide
    BALANCED_GC = "balanced_gc"         # GC-content balanced
    RUN_LENGTH_LIMITED = "rll"          # No homopolymer runs
    REDUNDANT_TRIPLET = "triplet"       # Error-tolerant triplet
```

### Decoder API

#### Class: DNADecoder

```python
class DNADecoder:
    """Converts DNA sequences back to binary data."""

    def decode(self, dna_sequence: str) -> DecodeResult:
        """
        Decode DNA sequence to original binary data.

        Args:
            dna_sequence: Complete DNA sequence with headers

        Returns:
            DecodeResult with data and metadata

        Raises:
            InvalidSequenceError: Malformed sequence
            ChecksumError: Integrity check failed
            UncorrectableError: Errors exceed correction capability
        """

    def decode_raw(
        self,
        dna_sequence: str,
        scheme: str = "quaternary"
    ) -> bytes:
        """
        Decode raw DNA without headers.

        Args:
            dna_sequence: Raw DNA data
            scheme: Encoding scheme used

        Returns:
            Decoded binary data
        """

    def validate_sequence(
        self,
        dna_sequence: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate DNA sequence structure.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """

    def detect_encoding_scheme(self, dna_sequence: str) -> str:
        """Auto-detect encoding scheme from sequence."""
```

#### Class: DecodeResult

```python
@dataclass
class DecodeResult:
    """Result of DNA decoding operation."""

    data: bytes                     # Decoded binary data
    filename: str                   # Recovered filename
    mime_type: str                  # Recovered MIME type
    encoding_scheme: str            # Scheme used
    errors_detected: int = 0        # Errors found
    errors_corrected: int = 0       # Errors fixed
    integrity_valid: bool = True    # Checksum valid
    metadata: Dict[str, Any] = {}   # Additional metadata
```

### Compute API

#### Class: DNAComputeEngine

```python
class DNAComputeEngine:
    """Perform logical and arithmetic operations on DNA sequences."""

    def apply_gate(
        self,
        gate: DNALogicGate,
        seq_a: str,
        seq_b: Optional[str] = None
    ) -> str:
        """
        Apply logic gate to DNA sequence(s).

        Args:
            gate: Logic gate to apply
            seq_a: First DNA sequence
            seq_b: Second sequence (not needed for NOT)

        Returns:
            Result DNA sequence
        """

    def add(self, seq_a: str, seq_b: str) -> Tuple[str, bool]:
        """Quaternary addition. Returns (result, overflow)."""

    def subtract(self, seq_a: str, seq_b: str) -> Tuple[str, bool]:
        """Quaternary subtraction. Returns (result, underflow)."""

    def multiply(self, seq_a: str, seq_b: str) -> str:
        """Quaternary multiplication."""

    def divide(self, seq_a: str, seq_b: str) -> Tuple[str, str]:
        """Quaternary division. Returns (quotient, remainder)."""

    def compare(self, seq_a: str, seq_b: str) -> int:
        """Compare numerically. Returns -1, 0, or 1."""

    def shift_left(self, sequence: str, positions: int) -> str:
        """Shift left (multiply by 4^positions)."""

    def shift_right(self, sequence: str, positions: int) -> str:
        """Shift right (divide by 4^positions)."""

    def rotate_left(self, sequence: str, positions: int) -> str:
        """Circular left rotation."""

    def rotate_right(self, sequence: str, positions: int) -> str:
        """Circular right rotation."""

    def execute_expression(
        self,
        expression: str,
        variables: Dict[str, str]
    ) -> str:
        """
        Execute compound expression.

        Example:
            engine.execute_expression(
                "(A AND B) XOR C",
                {"A": "ATCG", "B": "GCTA", "C": "AATT"}
            )
        """
```

#### Enum: DNALogicGate

```python
class DNALogicGate(Enum):
    AND = "and"     # min(nucleotide values)
    OR = "or"       # max(nucleotide values)
    XOR = "xor"     # (a + b) mod 4
    NOT = "not"     # complement (A<->G, T<->C)
    NAND = "nand"   # NOT(AND)
    NOR = "nor"     # NOT(OR)
    XNOR = "xnor"   # NOT(XOR)
```

### Storage API

#### Class: DNAFileSystem

```python
class DNAFileSystem:
    """Virtual file system using DNA sequences for storage."""

    def __init__(self, storage_backend: str = "memory"):
        """
        Initialize DNA file system.

        Args:
            storage_backend: "memory", "sqlite", or "json"
        """

    # File Operations
    def create_file(
        self,
        path: str,
        data: bytes,
        mime_type: str = "application/octet-stream",
        encoding_scheme: str = "quaternary",
        tags: Optional[List[str]] = None
    ) -> DNAFile:
        """Create new file encoded as DNA."""

    def read_file(self, path: str) -> bytes:
        """Read and decode file from DNA storage."""

    def update_file(self, path: str, data: bytes) -> DNAFile:
        """Update existing file content."""

    def delete_file(self, path: str) -> bool:
        """Delete file from DNA storage."""

    def get_file_info(self, path: str) -> DNAFile:
        """Get file metadata without decoding."""

    def get_raw_sequence(self, path: str) -> str:
        """Get raw DNA sequence for file."""

    def file_exists(self, path: str) -> bool:
        """Check if file exists."""

    # Directory Operations
    def create_directory(self, path: str) -> DNADirectory:
        """Create new directory."""

    def list_directory(
        self,
        path: str = "/"
    ) -> List[Union[DNAFile, DNADirectory]]:
        """List directory contents."""

    def delete_directory(
        self,
        path: str,
        recursive: bool = False
    ) -> bool:
        """Delete directory."""

    def directory_exists(self, path: str) -> bool:
        """Check if directory exists."""

    # Search Operations
    def search(
        self,
        query: Optional[str] = None,
        path_prefix: str = "/",
        mime_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> List[DNAFile]:
        """Search for files matching criteria."""

    def find_by_sequence(self, sequence_fragment: str) -> List[DNAFile]:
        """Find files containing DNA fragment."""

    # Utility Operations
    def get_storage_stats(self) -> dict:
        """Get storage statistics."""

    def verify_integrity(self, path: Optional[str] = None) -> dict:
        """Verify stored file integrity."""

    def import_from_filesystem(
        self,
        source_path: str,
        target_path: str = "/"
    ) -> List[DNAFile]:
        """Import from traditional filesystem."""

    def export_to_filesystem(
        self,
        source_path: str,
        target_path: str
    ) -> None:
        """Export to traditional filesystem."""
```

#### Class: DNAFile

```python
@dataclass
class DNAFile:
    """Represents a file stored as DNA sequence."""

    id: str                         # Unique identifier
    name: str                       # File name
    path: str                       # Full path
    dna_sequence: str               # DNA encoded data
    original_size: int              # Original binary size
    dna_length: int                 # DNA sequence length
    mime_type: str                  # Content type
    created_at: datetime            # Creation timestamp
    modified_at: datetime           # Modification timestamp
    checksum: str                   # Integrity checksum
    encoding_scheme: str            # Encoding used
    tags: List[str]                 # Tags/labels
    metadata: Dict[str, Any]        # Additional metadata
```

### Error Correction API

#### Class: DNAReedSolomon

```python
class DNAReedSolomon:
    """
    Reed-Solomon error correction for DNA sequences.

    Uses GF(4) to match the 4 nucleotide bases.
    Default: 16 parity symbols, corrects up to 8 errors.
    """

    def __init__(self, nsym: int = 16):
        """
        Initialize RS codec.

        Args:
            nsym: Number of parity symbols (corrects nsym/2 errors)
        """

    def encode(self, sequence: str) -> str:
        """
        Add RS parity to DNA sequence.

        Args:
            sequence: Original DNA sequence

        Returns:
            Sequence with RS parity appended
        """

    def decode(self, sequence: str) -> CorrectionResult:
        """
        Decode and correct errors.

        Args:
            sequence: DNA sequence with RS parity

        Returns:
            CorrectionResult with corrected sequence
        """
```

#### Class: CorrectionResult

```python
@dataclass
class CorrectionResult:
    """Result of error correction operation."""

    corrected_sequence: str         # Corrected DNA
    errors_detected: int            # Errors found
    errors_corrected: int           # Errors fixed
    uncorrectable: bool             # Too many errors?
    error_positions: List[int]      # Positions of errors
    confidence: float               # Confidence (0.0-1.0)
```

---

## Request/Response Formats

### Standard Request Headers

```
Content-Type: application/json
Authorization: Bearer <api-key>
Accept: application/json
```

### Standard Response Format

**Success Response:**
```json
{
  "status": "success",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "code": "ERROR_CODE"
}
```

### File Upload Format

```
Content-Type: multipart/form-data
```

### DNA Sequence Formats

#### FASTA Format
```
>VibeDNA:filename.txt
ATCGATCGAAATAAAAAAATAAATAAAGATCGATCGATCGATCGATCGATCGATCGATCGATCG
GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA
```

#### JSON Format
```json
{
  "filename": "document.txt",
  "scheme": "quaternary",
  "sequence": "ATCGATCG...",
  "length": 1024,
  "original_size": 512
}
```

#### Raw Format
```
ATCGATCGAAATAAAAAAATAAATAAAGATCGATCGATCGATCGATCGATCGATCGATCGATCG
```

---

## Error Codes and Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing API key |
| 404 | Not Found - Resource doesn't exist |
| 413 | Payload Too Large - File exceeds limit |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### Error Classes

| Error | Description |
|-------|-------------|
| `InvalidSequenceError` | DNA sequence is malformed |
| `ChecksumError` | Integrity verification failed |
| `UncorrectableError` | Too many errors to correct |
| `FileNotFoundError` | File doesn't exist in DNA storage |
| `DirectoryNotFoundError` | Directory doesn't exist |
| `FileExistsError` | File/directory already exists |
| `FileSystemError` | General file system error |
| `ValidationError` | Input validation failed |

### Python Exception Handling

```python
from vibedna import DNADecoder
from vibedna.core.decoder import (
    InvalidSequenceError,
    ChecksumError,
    UncorrectableError
)

decoder = DNADecoder()

try:
    result = decoder.decode(dna_sequence)
except InvalidSequenceError as e:
    print(f"Invalid sequence format: {e}")
except ChecksumError as e:
    print(f"Data corruption detected: {e}")
except UncorrectableError as e:
    print(f"Too many errors to recover: {e}")
```

---

## Rate Limits and Best Practices

### Rate Limits

| Endpoint Category | Rate Limit |
|-------------------|------------|
| Encoding | 100 requests/minute |
| Decoding | 100 requests/minute |
| Computation | 500 requests/minute |
| File System | 200 requests/minute |
| Validation | 1000 requests/minute |

### File Size Limits

| Limit | Value |
|-------|-------|
| Maximum file size | 100 MB |
| Maximum sequence length | 200M nucleotides |
| Stream chunk size | 8 KB |

### Best Practices

1. **Use appropriate encoding schemes:**
   - `quaternary` for maximum storage density
   - `balanced_gc` for synthesis compatibility
   - `rll` for sequencing reliability
   - `triplet` for maximum error tolerance

2. **Enable error correction:**
   - Always enable for long-term storage
   - Can disable for quick operations on trusted data

3. **Batch operations:**
   - Use streaming for large files
   - Batch multiple small files when possible

4. **Handle errors gracefully:**
   - Check `errors_corrected` in decode results
   - Verify `integrity_valid` before using data

5. **Optimize GC content:**
   - Target 40-60% GC for synthesis
   - Use `balanced_gc` scheme for biological applications

6. **Validate before processing:**
   - Use `/validate` endpoint before decoding
   - Check `detect_encoding_scheme()` for unknown sequences

---

## Code Examples

### Example 1: Complete Encoding/Decoding Workflow

```python
from vibedna import (
    DNAEncoder, DNADecoder,
    EncodingConfig, EncodingScheme
)

# Configure encoder for synthesis-compatible output
config = EncodingConfig(
    scheme=EncodingScheme.BALANCED_GC,
    error_correction=True,
    gc_balance_target=0.5
)

encoder = DNAEncoder(config)
decoder = DNADecoder()

# Encode a file
with open("document.pdf", "rb") as f:
    data = f.read()

dna_sequence = encoder.encode(
    data,
    filename="document.pdf",
    mime_type="application/pdf"
)

# Save DNA sequence
with open("document.fasta", "w") as f:
    f.write(f">VibeDNA:document.pdf\n")
    for i in range(0, len(dna_sequence), 80):
        f.write(dna_sequence[i:i+80] + "\n")

print(f"Encoded {len(data)} bytes to {len(dna_sequence)} nucleotides")

# Later: Decode back
result = decoder.decode(dna_sequence)

with open("recovered.pdf", "wb") as f:
    f.write(result.data)

print(f"Recovered {len(result.data)} bytes")
print(f"Errors corrected: {result.errors_corrected}")
print(f"Integrity valid: {result.integrity_valid}")
```

### Example 2: DNA Virtual File System

```python
from vibedna import DNAFileSystem

# Initialize file system
fs = DNAFileSystem(storage_backend="memory")

# Create directory structure
fs.create_directory("/projects")
fs.create_directory("/projects/dna-computing")

# Store files
fs.create_file(
    "/projects/dna-computing/data.csv",
    b"id,value\n1,ATCG\n2,GCTA",
    mime_type="text/csv",
    tags=["data", "research"]
)

fs.create_file(
    "/projects/dna-computing/results.json",
    b'{"status": "complete", "score": 0.95}',
    mime_type="application/json",
    tags=["results", "research"]
)

# List directory
contents = fs.list_directory("/projects/dna-computing")
for item in contents:
    print(f"  {item.name} ({item.original_size} bytes)")

# Search files
research_files = fs.search(tags=["research"])
print(f"Found {len(research_files)} research files")

# Export to regular filesystem
fs.export_to_filesystem("/projects", "./exported_projects")

# Storage statistics
stats = fs.get_storage_stats()
print(f"Total files: {stats['total_files']}")
print(f"Total DNA length: {stats['total_dna_length']:,} nucleotides")
print(f"Expansion ratio: {stats['expansion_ratio']:.2f}x")
```

### Example 3: DNA Computation

```python
from vibedna import DNAComputeEngine, DNALogicGate

engine = DNAComputeEngine()

# Define DNA-encoded values
a = "ATCGATCG"  # Represents a number
b = "GCTAGCTA"  # Represents another number

# Logic operations
xor_result = engine.apply_gate(DNALogicGate.XOR, a, b)
print(f"{a} XOR {b} = {xor_result}")

# Build a simple circuit: (A AND B) OR (NOT A AND NOT B) = XNOR
not_a = engine.apply_gate(DNALogicGate.NOT, a)
not_b = engine.apply_gate(DNALogicGate.NOT, b)
a_and_b = engine.apply_gate(DNALogicGate.AND, a, b)
not_a_and_not_b = engine.apply_gate(DNALogicGate.AND, not_a, not_b)
xnor_manual = engine.apply_gate(DNALogicGate.OR, a_and_b, not_a_and_not_b)

# Or use compound expression
xnor_expr = engine.execute_expression(
    "(A AND B) OR (NOT A AND NOT B)",
    {"A": a, "B": b}
)

assert xnor_manual == xnor_expr
print(f"XNOR result: {xnor_expr}")

# Arithmetic
sum_result, overflow = engine.add(a, b)
print(f"{a} + {b} = {sum_result} (overflow: {overflow})")

# Comparison
cmp = engine.compare(a, b)
if cmp < 0:
    print(f"{a} < {b}")
elif cmp > 0:
    print(f"{a} > {b}")
else:
    print(f"{a} == {b}")
```

### Example 4: Error Correction

```python
from vibedna import DNAReedSolomon

# Initialize with 16 parity symbols (can correct 8 errors)
rs = DNAReedSolomon(nsym=16)

# Original sequence
original = "ATCGATCGATCGATCGATCGATCGATCGATCGATCG"

# Encode with error correction
encoded = rs.encode(original)
print(f"Original: {len(original)} nt -> Encoded: {len(encoded)} nt")

# Simulate errors (corrupt some nucleotides)
corrupted_list = list(encoded)
corrupted_list[5] = "G"   # Introduce error
corrupted_list[10] = "A"  # Introduce error
corrupted_list[15] = "C"  # Introduce error
corrupted = "".join(corrupted_list)

# Decode and correct
result = rs.decode(corrupted)

print(f"Errors detected: {result.errors_detected}")
print(f"Errors corrected: {result.errors_corrected}")
print(f"Error positions: {result.error_positions}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Corrected sequence matches original: {result.corrected_sequence == original}")
```

### Example 5: REST API with curl

```bash
#!/bin/bash

# Encode text to DNA
echo "Encoding 'Hello World' to DNA..."
curl -s -X POST http://localhost:8000/quick/encode \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World", "scheme": "quaternary"}' | jq .

# Encode a file
echo "Encoding file to DNA..."
curl -s -X POST http://localhost:8000/encode/file \
  -F "file=@document.pdf" \
  -F "scheme=balanced_gc" \
  -F "output_format=json" > encoded.json

# Decode DNA
echo "Decoding DNA..."
curl -s -X POST http://localhost:8000/decode \
  -H "Content-Type: application/json" \
  -d @- << EOF | jq .
{
  "dna_sequence": "ATCGATCGAAATAAAA...",
  "verify_checksum": true
}
EOF

# Perform XOR computation
echo "Computing XOR..."
curl -s -X POST http://localhost:8000/compute/gate \
  -H "Content-Type: application/json" \
  -d '{
    "gate": "XOR",
    "sequence_a": "ATCGATCG",
    "sequence_b": "GCTAGCTA"
  }' | jq .

# Store file in DNA filesystem
echo "Storing file in DNA filesystem..."
curl -s -X POST "http://localhost:8000/fs/store?path=/documents" \
  -F "file=@report.pdf" \
  -F "tags=important" | jq .

# List files
echo "Listing files..."
curl -s "http://localhost:8000/fs/list?path=/documents" | jq .

# Get storage stats
echo "Storage statistics..."
curl -s http://localhost:8000/fs/stats | jq .
```

### Example 6: Running the API Server

```python
# Start the server programmatically
from vibedna.api.rest_server import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
```

Or via command line:

```bash
# Using uvicorn directly
uvicorn vibedna.api.rest_server:app --host 0.0.0.0 --port 8000 --reload

# Using Docker
docker run -p 8000:8000 vibedna/api:latest
```

---

## Appendix: Constants Reference

### Nucleotide Mappings

```python
# Binary to nucleotide
BIT_TO_NUCLEOTIDE = {
    "00": "A",  # Adenine
    "01": "T",  # Thymine
    "10": "C",  # Cytosine
    "11": "G",  # Guanine
}

# Nucleotide numeric values
NUCLEOTIDE_VALUE = {"A": 0, "T": 1, "C": 2, "G": 3}

# Complement mapping
NUCLEOTIDE_COMPLEMENT = {"A": "G", "T": "C", "C": "T", "G": "A"}
```

### File Format Markers

```python
MAGIC_SEQUENCE = "ATCGATCG"  # File identifier (8 nt)
END_MARKER = "GCTAGCTA"      # File end marker (8 nt)
VERSION = "AAAT"             # Version 1.0 (4 nt)
```

### Structure Sizes

```python
HEADER_SIZE = 256           # Total header (nucleotides)
BLOCK_SIZE = 512            # Bytes per block
BLOCK_DNA_SIZE = 1024       # Nucleotides per block
BLOCK_HEADER_SIZE = 16      # Block header (nucleotides)
RS_PARITY_SIZE = 64         # Reed-Solomon parity per block
FOOTER_SIZE = 32            # Total footer (nucleotides)
MAX_FILE_SIZE = 104857600   # 100 MB limit
```

---

## Support and Resources

- **Documentation**: https://docs.vibedna.com
- **API Status**: https://status.vibedna.com
- **GitHub**: https://github.com/vibedna/vibedna
- **Support**: support@vibecaas.com

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
