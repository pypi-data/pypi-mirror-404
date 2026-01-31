# VibeDNA v1.0.0

**Where Digital Meets Biological**

The first official release of VibeDNA - a comprehensive binary-to-DNA and DNA-to-binary encoding system.

## Installation

```bash
pip install vibedna
```

## Highlights

### Core Features
- **Multi-Scheme Encoding**: 4 encoding schemes optimized for different use cases
  - Quaternary (highest density - 2 bits/nucleotide)
  - Balanced GC (synthesis compatible)
  - Run-Length Limited (sequencing accurate)
  - Redundant Triplet (maximum error tolerance)

### Error Correction
- Reed-Solomon error correction in GF(4) arithmetic
- Corrects up to 8 nucleotide errors per 1024 nucleotide block
- Hamming code support for DNA sequences

### DNA Computation
- Logic gates: AND, OR, XOR, NOT, NAND, NOR, XNOR
- Arithmetic: addition, subtraction, multiplication, division
- Bitwise operations and comparisons

### DNA File System
- Virtual file system with DNA sequence storage
- Full CRUD operations
- Hierarchical directory structure
- Search and indexing capabilities

### Multiple Interfaces
- **CLI**: Feature-rich command-line interface
- **REST API**: FastAPI-based server with OpenAPI docs
- **Python SDK**: Full programmatic access

## Quick Start

```python
from vibedna import DNAEncoder, DNADecoder

# Encode data to DNA
encoder = DNAEncoder()
dna = encoder.encode(b"Hello World", filename="hello.txt")

# Decode back to binary
decoder = DNADecoder()
result = decoder.decode(dna)
print(result.data)  # b'Hello World'
```

## CLI Examples

```bash
# Encode a file
vibedna encode document.pdf -o document.dna

# Decode back
vibedna decode document.dna -o recovered.pdf

# Quick text encoding
vibedna quick "Hello DNA World!"

# DNA computation
vibedna compute gate XOR ATCG GCTA
```

## Requirements

- Python 3.10+
- pip 21.0+ (for PEP 517 support)

## Documentation

- [README](https://github.com/ttracx/VibeDNA#readme)
- [API Documentation](https://github.com/ttracx/VibeDNA/blob/main/docs/API.md)
- [Examples](https://github.com/ttracx/VibeDNA/blob/main/docs/EXAMPLES.md)
- [Publishing Guide](https://github.com/ttracx/VibeDNA/blob/main/PUBLISHING.md)

## What's Included

- `vibedna` - Python package with full SDK
- `vibedna` CLI command for terminal usage
- REST API server (FastAPI)
- Comprehensive test suite
- Full documentation

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
