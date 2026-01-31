# VibeDNA

**Where Digital Meets Biological**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/vibedna/vibedna)
[![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

VibeDNA is a comprehensive binary-to-DNA and DNA-to-binary encoding system that enables computation and file management using DNA sequences as the storage and processing medium.

## Features

- **Multi-Scheme Encoding**: Support for 4 encoding schemes optimized for different use cases
  - **Quaternary**: Standard 2-bit per nucleotide (highest density)
  - **Balanced GC**: Maintains 40-60% GC content for synthesis compatibility
  - **Run-Length Limited (RLL)**: Prevents homopolymer runs for sequencing accuracy
  - **Redundant Triplet**: 3x redundancy for maximum error tolerance

- **Error Correction**: Reed-Solomon error correction adapted for GF(4) arithmetic
  - Corrects up to 8 nucleotide errors per block
  - Automatic error detection and correction
  - Configurable redundancy levels

- **DNA Computation**: Perform computations directly on DNA-encoded data
  - Logic gates: AND, OR, XOR, NOT, NAND, NOR, XNOR
  - Arithmetic: Addition, subtraction, multiplication, division
  - Comparison and bitwise shift operations

- **DNA File System**: Virtual file system with DNA sequence storage
  - Full CRUD operations
  - Hierarchical directory structure
  - Search and indexing capabilities

- **CLI & REST API**: Multiple interfaces for integration
  - Feature-rich command-line interface
  - RESTful API with OpenAPI documentation

## Installation

### From PyPI (Recommended)

```bash
# Install from PyPI
pip install vibedna

# Verify installation
vibedna --version
```

### From Source

```bash
# Clone the repository
git clone https://github.com/ttracx/VibeDNA.git
cd VibeDNA

# Install with pip
pip install .

# Or install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Requirements

- Python 3.10 or higher
- pip 21.0 or higher (for PEP 517 support)

## Quick Start

### Command Line

```bash
# Encode a file to DNA
vibedna encode document.pdf -o document.dna

# Decode back to original
vibedna decode document.dna -o recovered.pdf

# Quick text encoding (no headers)
vibedna quick "Hello, DNA World!"

# Perform DNA computation
vibedna compute gate XOR ATCG GCTA

# Store file in DNA file system
vibedna fs cp ./report.docx /documents/report.docx
```

### Python SDK

```python
from vibedna import DNAEncoder, DNADecoder, DNAFileSystem

# Encode data
encoder = DNAEncoder()
dna_sequence = encoder.encode(b"Hello World", filename="hello.txt")
print(f"Encoded: {dna_sequence[:50]}...")

# Decode back
decoder = DNADecoder()
result = decoder.decode(dna_sequence)
print(f"Decoded: {result.data}")
print(f"Filename: {result.filename}")

# File system operations
fs = DNAFileSystem()
fs.create_file("/hello.txt", b"Hello DNA!")
data = fs.read_file("/hello.txt")
print(f"Read from DNA FS: {data}")
```

### REST API

```bash
# Start the API server
uvicorn vibedna.api.rest_server:app --host 0.0.0.0 --port 8000

# Encode data
curl -X POST "http://localhost:8000/encode" \
  -H "Content-Type: application/json" \
  -d '{"data": "SGVsbG8gV29ybGQh", "filename": "hello.txt"}'

# Quick encode text
curl -X POST "http://localhost:8000/quick/encode" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

## Encoding Specification

### Primary Mapping (Quaternary)

| Binary | DNA |
|--------|-----|
| 00 | A (Adenine) |
| 01 | T (Thymine) |
| 10 | C (Cytosine) |
| 11 | G (Guanine) |

### DNA Sequence Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        DNA FILE FORMAT                          │
├─────────────────────────────────────────────────────────────────┤
│ HEADER (256 nucleotides)                                        │
│ ├── Magic: ATCGATCG (8 nt)                                      │
│ ├── Version: 4 nt                                               │
│ ├── Scheme: 4 nt                                                │
│ ├── File Size: 32 nt                                            │
│ ├── Filename: 128 nt                                            │
│ ├── MIME Type: 32 nt                                            │
│ ├── Checksum: 32 nt                                             │
│ └── Reserved: 16 nt                                             │
├─────────────────────────────────────────────────────────────────┤
│ DATA BLOCKS (Variable)                                          │
│ ├── Block Header: 16 nt per block                               │
│ └── Block Data: 1024 nt per block                               │
├─────────────────────────────────────────────────────────────────┤
│ ERROR CORRECTION                                                │
│ └── Reed-Solomon Parity: 64 nt per block                        │
├─────────────────────────────────────────────────────────────────┤
│ FOOTER (32 nucleotides)                                         │
│ ├── End Marker: GCTAGCTA (8 nt)                                 │
│ ├── Block Count: 8 nt                                           │
│ └── Checksum: 16 nt                                             │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
vibedna/
├── core/               # Encoding/decoding engines
├── storage/            # DNA file system
├── error_correction/   # Reed-Solomon, Hamming codes
├── compute/            # DNA logic gates and arithmetic
├── cli/                # Command-line interface
├── api/                # REST API
├── utils/              # Utilities and constants
└── tests/              # Test suite
```

## API Documentation

Full API documentation is available at `/docs` when running the API server.

Key endpoints:
- `POST /encode` - Encode data to DNA
- `POST /decode` - Decode DNA to data
- `POST /compute` - Perform DNA computations
- `GET /fs/list` - List files in DNA storage
- `POST /fs/store` - Store file in DNA storage

## Docker

```bash
# Build the image
docker build -t vibedna .

# Run the API server
docker run -p 8000:8000 vibedna
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vibedna

# Run specific test file
pytest tests/unit/test_encoder.py
```

## Encoding Scheme Comparison

| Scheme | Bits/nt | GC Balanced | Homopolymer Safe | Error Tolerance |
|--------|---------|-------------|------------------|-----------------|
| Quaternary | 2.0 | No | No | None |
| Balanced GC | 2.0 | Yes | No | None |
| RLL | ~1.8 | No | Yes | None |
| Triplet | 0.33 | No | No | High |

## Performance

- Encoding: ~200 KB/s (quaternary scheme)
- Decoding: ~250 KB/s
- Error correction: Up to 8 errors per 1024 nucleotides

## Contributing

This is proprietary software. Please contact NeuralQuantum.ai for licensing information.

## License

Proprietary - All Rights Reserved

## Support

For support and inquiries:
- Website: https://vibecaas.com
- Email: contact@neuralquantum.ai

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
