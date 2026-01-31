# VibeDNA API Documentation

## Overview

The VibeDNA API provides RESTful endpoints for DNA encoding, decoding, computation, and file system operations.

**Base URL**: `http://localhost:8000`

**Interactive Documentation**: Available at `/docs` (Swagger UI) or `/redoc` (ReDoc)

## Authentication

Currently, the API does not require authentication. In production deployments, implement appropriate authentication mechanisms.

## Endpoints

### Info

#### GET /
Health check and API information.

**Response:**
```json
{
  "name": "VibeDNA API",
  "version": "1.0.0",
  "status": "operational",
  "documentation": "/docs",
  "copyright": "© 2026 VibeDNA..."
}
```

### Encoding

#### POST /encode
Encode binary data to DNA sequence.

**Request Body:**
```json
{
  "data": "SGVsbG8gV29ybGQh",  // Base64-encoded data
  "filename": "hello.txt",
  "mime_type": "text/plain",
  "scheme": "quaternary",
  "error_correction": true
}
```

**Response:**
```json
{
  "dna_sequence": "ATCGATCG...",
  "nucleotide_count": 1024,
  "compression_ratio": 4.0,
  "encoding_scheme": "quaternary",
  "checksum": "abc123def456"
}
```

#### POST /encode/file
Upload and encode a file.

**Parameters:**
- `file`: File upload (multipart/form-data)
- `scheme`: Encoding scheme (optional, default: "quaternary")
- `error_correction`: Enable error correction (optional, default: true)
- `output_format`: Output format - "fasta", "raw", or "json" (optional, default: "fasta")

**Response:** File download with encoded DNA sequence

#### POST /quick/encode
Quick encode text without headers.

**Request Body:**
```json
{
  "text": "Hello World",
  "scheme": "quaternary"
}
```

**Response:**
```json
{
  "dna_sequence": "GCTAGCTACGATCGAT...",
  "length": 44
}
```

### Decoding

#### POST /decode
Decode DNA sequence to binary data.

**Request Body:**
```json
{
  "dna_sequence": "ATCGATCG...",
  "verify_checksum": true
}
```

**Response:**
```json
{
  "data": "SGVsbG8gV29ybGQh",  // Base64-encoded
  "filename": "hello.txt",
  "mime_type": "text/plain",
  "original_size": 12,
  "errors_corrected": 0,
  "integrity_valid": true
}
```

#### POST /decode/file
Upload DNA file and decode to original binary.

**Parameters:**
- `file`: FASTA or raw DNA file (multipart/form-data)
- `verify`: Verify checksum (optional, default: true)

**Response:** Original file download

#### POST /quick/decode
Quick decode DNA without headers.

**Request Body:**
```json
{
  "dna_sequence": "GCTAGCTACGATCGAT...",
  "scheme": "quaternary"
}
```

**Response:**
```json
{
  "text": "Hello World",
  "size": 11
}
```

### Computation

#### POST /compute
Perform computation on DNA sequences.

**Request Body:**
```json
{
  "operation": "XOR",  // AND, OR, XOR, NOT, NAND, NOR, XNOR, ADD, SUB, MUL, DIV
  "sequence_a": "ATCGATCG",
  "sequence_b": "GCTAGCTA"
}
```

**Response:**
```json
{
  "result": "CGATCGAT",
  "operation": "XOR",
  "overflow": false
}
```

#### POST /compute/gate
Apply logic gate to sequences.

**Request Body:**
```json
{
  "gate": "XOR",
  "sequence_a": "ATCG",
  "sequence_b": "GCTA"
}
```

#### POST /compute/arithmetic
Perform arithmetic operation.

**Request Body:**
```json
{
  "operation": "ADD",
  "sequence_a": "ATCG",
  "sequence_b": "AAAT"
}
```

### File System

#### GET /fs/list
List files and directories.

**Parameters:**
- `path`: Directory path (optional, default: "/")

**Response:**
```json
{
  "path": "/",
  "files": [
    {
      "id": "abc123",
      "name": "test.txt",
      "path": "/test.txt",
      "original_size": 100,
      "dna_length": 400,
      "mime_type": "text/plain",
      "created_at": "2026-01-30T12:00:00Z"
    }
  ],
  "directories": [
    {
      "id": "def456",
      "name": "documents",
      "path": "/documents",
      "created_at": "2026-01-30T12:00:00Z"
    }
  ],
  "total_items": 2
}
```

#### POST /fs/store
Store a file in DNA storage.

**Parameters:**
- `file`: File upload (multipart/form-data)
- `path`: Target directory path (optional, default: "/")
- `tags`: List of tags (optional)

**Response:** File metadata

#### GET /fs/retrieve/{file_path}
Retrieve a file from DNA storage.

**Response:** File download

#### DELETE /fs/delete/{file_path}
Delete a file from DNA storage.

**Response:**
```json
{
  "message": "Deleted /test.txt",
  "success": true
}
```

#### GET /fs/stats
Get storage statistics.

**Response:**
```json
{
  "total_files": 10,
  "total_directories": 3,
  "total_binary_size": 10240,
  "total_dna_length": 40960,
  "expansion_ratio": 4.0,
  "backend": "memory"
}
```

#### GET /fs/sequence/{file_path}
Get raw DNA sequence for a file.

**Response:**
```json
{
  "path": "/test.txt",
  "sequence": "ATCGATCG...",
  "length": 400
}
```

### Validation

#### POST /validate
Validate DNA sequence structure.

**Request Body:**
```json
{
  "sequence": "ATCGATCG...",
  "require_header": true,
  "require_footer": true
}
```

**Response:**
```json
{
  "is_valid": true,
  "issues": []
}
```

#### GET /info/{sequence}
Get information about a DNA sequence.

**Response:**
```json
{
  "length": 1024,
  "gc_content": 0.5,
  "detected_scheme": "quaternary",
  "nucleotide_counts": {
    "A": 256,
    "T": 256,
    "C": 256,
    "G": 256
  },
  "has_header": true,
  "has_footer": true
}
```

## Error Handling

All errors return a JSON response with the following structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

HTTP Status Codes:
- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Rate Limiting

No rate limiting is currently implemented. Production deployments should implement appropriate rate limiting.

## Encoding Schemes

| Scheme | Value | Description |
|--------|-------|-------------|
| Quaternary | `quaternary` | Standard 2-bit per nucleotide |
| Balanced GC | `balanced_gc` | GC-content balanced |
| RLL | `rll` | Run-length limited |
| Triplet | `triplet` | Redundant triplet encoding |

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
