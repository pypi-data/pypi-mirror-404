# Changelog

All notable changes to VibeDNA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-30

### Added

- **Core Encoding/Decoding**
  - Binary to DNA encoding with multiple encoding schemes
  - DNA to binary decoding with automatic scheme detection
  - Four encoding schemes: Quaternary, Balanced GC, Run-Length Limited, Redundant Triplet

- **Error Correction**
  - Reed-Solomon error correction adapted for GF(4) arithmetic
  - Corrects up to 8 nucleotide errors per 1024 nucleotide block
  - Hamming code support for DNA sequences
  - Checksum generation and validation

- **DNA Computation**
  - Logic gates: AND, OR, XOR, NOT, NAND, NOR, XNOR
  - Arithmetic operations: addition, subtraction, multiplication, division
  - Bitwise operations and comparisons
  - Parallel strand processing

- **DNA File System**
  - Virtual file system with DNA sequence storage
  - Full CRUD operations (Create, Read, Update, Delete)
  - Hierarchical directory structure
  - Search and indexing capabilities

- **Command Line Interface**
  - `vibedna encode` - Encode files to DNA sequences
  - `vibedna decode` - Decode DNA sequences to files
  - `vibedna quick` - Quick text encoding/decoding
  - `vibedna compute` - DNA computation operations
  - `vibedna fs` - File system operations

- **REST API**
  - FastAPI-based REST server
  - OpenAPI documentation
  - Endpoints for encoding, decoding, computation, and storage

- **Python SDK**
  - `DNAEncoder` - Encode binary data to DNA
  - `DNADecoder` - Decode DNA to binary data
  - `DNAFileSystem` - Manage files in DNA storage
  - `DNAComputeEngine` - Perform DNA computations
  - `DNAReedSolomon` - Error correction utilities

### Technical Details

- Python 3.10+ required
- Hatchling build system
- Type hints with py.typed marker
- Comprehensive test suite

---

(c) 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
