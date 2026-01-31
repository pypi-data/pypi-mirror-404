# VibeDNA Quick Start Guide

Get up and running with VibeDNA in minutes. This guide covers installation, basic usage, and key features.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
3. [Your First Encoding](#3-your-first-encoding)
4. [Decoding DNA](#4-decoding-dna)
5. [Using the File System](#5-using-the-file-system)
6. [DNA Computing Basics](#6-dna-computing-basics)
7. [Using the CLI](#7-using-the-cli)
8. [Using the Python API](#8-using-the-python-api)
9. [Next Steps](#9-next-steps)

---

## 1. Introduction

### What is VibeDNA?

VibeDNA is a comprehensive binary-to-DNA encoding system that enables you to:

- **Encode** any binary data (files, text, images) into DNA sequences
- **Decode** DNA sequences back to their original binary form
- **Compute** directly on DNA-encoded data using logic gates and arithmetic
- **Store** files in a virtual DNA-based file system

DNA encoding maps binary data to the four nucleotides: Adenine (A), Thymine (T), Cytosine (C), and Guanine (G).

### What You'll Learn

By the end of this guide, you will know how to:

- Install VibeDNA via pip or from source
- Encode text and files to DNA sequences
- Decode DNA back to original data
- Use the DNA file system for storage
- Perform basic DNA computations
- Use both CLI and Python API

---

## 2. Installation

### Prerequisites

- Python 3.11 or higher (3.10+ supported)
- pip 21.0 or higher

Verify your Python version:

```bash
python --version
# Python 3.11.x or higher
```

### Method 1: Install from PyPI (Recommended)

```bash
pip install vibedna
```

Verify the installation:

```bash
vibedna --version
# VibeDNA, version 1.0.0
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/ttracx/VibeDNA.git
cd VibeDNA

# Install the package
pip install .

# Or install in development mode
pip install -e .

# Install with development dependencies (optional)
pip install -e ".[dev]"
```

### Method 3: Docker Installation

```bash
# Build the Docker image
docker build -t vibedna .

# Run the API server
docker run -p 8000:8000 vibedna

# Run CLI commands
docker run vibedna vibedna --help
```

---

## 3. Your First Encoding

### Encoding a String to DNA

The simplest way to encode text is using the `encode_raw()` method:

```python
from vibedna import DNAEncoder

encoder = DNAEncoder()

# Encode a simple string
dna = encoder.encode_raw("Hello World")
print(f"DNA: {dna}")
# Output: GCTAGCTACGATCGATCGATCGAT...
```

The default encoding uses the **quaternary scheme** where:
- `00` = A (Adenine)
- `01` = T (Thymine)
- `10` = C (Cytosine)
- `11` = G (Guanine)

### Encoding a File to DNA

For files, use the `encode()` method which adds headers and metadata:

```python
from vibedna import DNAEncoder

# Read your file
with open("document.pdf", "rb") as f:
    data = f.read()

# Encode with metadata
encoder = DNAEncoder()
dna_sequence = encoder.encode(
    data,
    filename="document.pdf",
    mime_type="application/pdf"
)

print(f"Original size: {len(data):,} bytes")
print(f"DNA length: {len(dna_sequence):,} nucleotides")
print(f"Expansion ratio: {len(dna_sequence) / len(data):.2f}x")
```

Save the encoded DNA to a file:

```python
# Save as FASTA format
with open("document.dna", "w") as f:
    f.write(f">VibeDNA:document.pdf\n")
    for i in range(0, len(dna_sequence), 80):
        f.write(dna_sequence[i:i+80] + "\n")
```

### Understanding the Output

A VibeDNA-encoded sequence contains:

| Section | Size | Purpose |
|---------|------|---------|
| Header | 256 nt | Magic number, version, scheme, filename, checksum |
| Data Blocks | Variable | Encoded binary data with block headers |
| Error Correction | 64 nt/block | Reed-Solomon parity for error recovery |
| Footer | 32 nt | End marker, block count, final checksum |

The **magic sequence** `ATCGATCG` identifies VibeDNA files.

---

## 4. Decoding DNA

### Decoding DNA Back to Binary

```python
from vibedna import DNADecoder

decoder = DNADecoder()

# Decode a complete DNA sequence (with headers)
result = decoder.decode(dna_sequence)

print(f"Filename: {result.filename}")
print(f"MIME type: {result.mime_type}")
print(f"Data size: {len(result.data):,} bytes")
print(f"Errors corrected: {result.errors_corrected}")
print(f"Integrity valid: {result.integrity_valid}")

# Save the decoded file
with open(result.filename, "wb") as f:
    f.write(result.data)
```

For raw sequences (without headers):

```python
# Decode raw DNA (no metadata)
data = decoder.decode_raw("GCTAGCTACGATCGAT")
print(data)  # bytes object
```

### Verifying Integrity

The `DecodeResult` object provides integrity information:

```python
result = decoder.decode(dna_sequence)

if result.integrity_valid:
    print("Data integrity verified!")
else:
    print(f"Warning: {result.errors_detected} errors detected")
    print(f"Corrected: {result.errors_corrected} errors")
```

Reed-Solomon error correction can fix up to **8 nucleotide errors per block**.

---

## 5. Using the File System

VibeDNA includes a virtual file system that stores all data as DNA sequences.

### Creating DNA Files

```python
from vibedna import DNAFileSystem

# Initialize file system
fs = DNAFileSystem()

# Create a file
file = fs.create_file("/hello.txt", b"Hello DNA World!")
print(f"Created: {file.name}")
print(f"Original size: {file.original_size} bytes")
print(f"DNA length: {file.dna_length} nucleotides")
```

### Reading DNA Files

```python
# Read file contents
data = fs.read_file("/hello.txt")
print(data.decode())  # "Hello DNA World!"
```

### Listing and Searching

```python
# Create a directory structure
fs.create_directory("/documents")
fs.create_file("/documents/report.txt", b"Annual Report")
fs.create_file("/documents/notes.txt", b"Meeting Notes")

# List directory contents
for item in fs.list_directory("/documents"):
    print(f"  {item.name} - {item.original_size} bytes")

# Search for files
results = fs.search(query="report", path_prefix="/documents")
for file in results:
    print(f"Found: {file.path}")

# Get storage statistics
stats = fs.get_storage_stats()
print(f"Total files: {stats['total_files']}")
print(f"Total DNA: {stats['total_dna_length']:,} nucleotides")
```

---

## 6. DNA Computing Basics

VibeDNA allows computation directly on DNA-encoded data.

### Simple Logic Operations

```python
from vibedna import DNAComputeEngine, DNALogicGate

engine = DNAComputeEngine()

# Define DNA values
a = "ATCG"
b = "GCTA"

# Apply logic gates
print(f"A:       {a}")
print(f"B:       {b}")
print(f"A AND B: {engine.apply_gate(DNALogicGate.AND, a, b)}")
print(f"A OR B:  {engine.apply_gate(DNALogicGate.OR, a, b)}")
print(f"A XOR B: {engine.apply_gate(DNALogicGate.XOR, a, b)}")
print(f"NOT A:   {engine.apply_gate(DNALogicGate.NOT, a)}")
```

Available gates: `AND`, `OR`, `XOR`, `NOT`, `NAND`, `NOR`, `XNOR`

### Arithmetic on DNA

DNA sequences can represent numbers in base-4 (quaternary):

```python
engine = DNAComputeEngine()

# A=0, T=1, C=2, G=3
# "TC" = 2*4 + 1 = 9 in decimal
# "AT" = 0*4 + 1 = 1 in decimal

a = "AATC"  # 6 in decimal
b = "AACT"  # 5 in decimal

# Addition
result, overflow = engine.add(a, b)
print(f"{a} + {b} = {result}")  # AATG (11)

# Multiplication
product = engine.multiply(a, b)
print(f"{a} x {b} = {product}")  # Result: 30

# Division
quotient, remainder = engine.divide("ATCG", "AATC")
print(f"ATCG / AATC = {quotient} remainder {remainder}")
```

---

## 7. Using the CLI

VibeDNA provides a full-featured command-line interface.

### Common Commands

```bash
# Show help
vibedna --help

# Encode a file
vibedna encode document.pdf -o document.dna

# Decode a file
vibedna decode document.dna -o recovered.pdf

# Quick encode text (no headers)
vibedna quick "Hello World"

# Quick decode DNA
vibedna quickdecode GCTAGCTACGATCGAT

# Get sequence information
vibedna info document.dna

# Validate a sequence
vibedna validate ATCGATCGATCGATCG
```

### File System Commands

```bash
# List files in DNA storage
vibedna fs ls /

# Copy file to DNA storage
vibedna fs cp ./report.pdf /documents/report.pdf

# Export file from DNA storage
vibedna fs export /documents/report.pdf ./recovered.pdf

# Show storage statistics
vibedna fs stats
```

### Compute Commands

```bash
# Apply a logic gate
vibedna compute gate XOR ATCGATCG GCTAGCTA

# Perform arithmetic
vibedna compute math add AATC AACT
vibedna compute math mul ATCG GCTA
```

### Examples

```bash
# Encode with balanced GC content
vibedna encode image.png -s balanced_gc -o image.dna

# Encode with maximum error tolerance
vibedna encode critical.dat -s triplet --format fasta

# Encode without error correction (smaller output)
vibedna encode data.bin --no-error-correction

# Suppress banner output
vibedna -q encode file.txt
```

---

## 8. Using the Python API

### Import Statements

```python
# Core encoding/decoding
from vibedna import DNAEncoder, DNADecoder

# Configuration
from vibedna import EncodingConfig, EncodingScheme

# Decode results
from vibedna import DecodeResult

# File system
from vibedna import DNAFileSystem, DNAFile, DNADirectory

# Computing
from vibedna import DNAComputeEngine, DNALogicGate

# Error correction
from vibedna import DNAReedSolomon
```

### Basic Operations with Code Examples

**Complete encode-decode roundtrip:**

```python
from vibedna import DNAEncoder, DNADecoder, EncodingConfig, EncodingScheme

# Configure encoder with balanced GC content
config = EncodingConfig(
    scheme=EncodingScheme.BALANCED_GC,
    error_correction=True,
)
encoder = DNAEncoder(config)

# Original data
original = b"VibeDNA makes DNA storage easy!"

# Encode
dna = encoder.encode(original, filename="message.txt")
print(f"Encoded to {len(dna)} nucleotides")

# Decode
decoder = DNADecoder()
result = decoder.decode(dna)

# Verify
assert result.data == original
print(f"Roundtrip successful!")
print(f"Filename: {result.filename}")
```

**Working with different encoding schemes:**

```python
from vibedna import DNAEncoder, EncodingConfig, EncodingScheme

data = b"Test data"

schemes = [
    EncodingScheme.QUATERNARY,      # Highest density (2 bits/nt)
    EncodingScheme.BALANCED_GC,     # Better for synthesis
    EncodingScheme.RUN_LENGTH_LIMITED,  # No homopolymer runs
    EncodingScheme.REDUNDANT_TRIPLET,   # Maximum error tolerance
]

for scheme in schemes:
    config = EncodingConfig(scheme=scheme)
    encoder = DNAEncoder(config)
    dna = encoder.encode_raw(data)
    print(f"{scheme.value:20} -> {len(dna):4} nucleotides")
```

**File system with tagging:**

```python
from vibedna import DNAFileSystem

fs = DNAFileSystem()

# Create tagged files
fs.create_directory("/projects")
fs.create_file(
    "/projects/code.py",
    b"print('hello')",
    tags=["python", "source"]
)
fs.create_file(
    "/projects/data.json",
    b'{"key": "value"}',
    tags=["json", "config"]
)

# Search by tags
python_files = fs.search(tags=["python"])
for f in python_files:
    print(f"Python file: {f.path}")
```

---

## 9. Next Steps

### Detailed Documentation

- **[API Reference](../API.md)** - Complete API documentation
- **[Encoding Specification](../ENCODING_SPEC.md)** - Technical encoding details
- **[Examples](../EXAMPLES.md)** - More usage examples

### Agent System

VibeDNA includes a powerful multi-agent orchestration system for complex workflows:

```python
from vibedna.agents import MasterOrchestrator, EncoderAgent

# Agents handle distributed encoding, validation, and more
# See docs/agents/ for full documentation
```

The agent system provides:

- **Orchestration Tier**: Workflow coordination and resource management
- **Specialist Tier**: Encoding, decoding, error correction, compute agents
- **Support Tier**: Logging, metrics, security, and documentation agents

### REST API

Start the API server for web integration:

```bash
uvicorn vibedna.api.rest_server:app --host 0.0.0.0 --port 8000
```

Access the interactive documentation at `http://localhost:8000/docs`.

### Getting Help

- **Website**: https://vibecaas.com
- **Issues**: https://github.com/ttracx/VibeDNA/issues
- **Email**: contact@neuralquantum.ai

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
