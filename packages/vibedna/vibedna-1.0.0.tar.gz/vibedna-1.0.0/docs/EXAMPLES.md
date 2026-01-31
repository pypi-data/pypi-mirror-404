# VibeDNA Usage Examples

This document provides practical examples of using VibeDNA for various use cases.

## Table of Contents

1. [Basic Encoding/Decoding](#basic-encodingdecoding)
2. [Working with Files](#working-with-files)
3. [DNA Computation](#dna-computation)
4. [File System Operations](#file-system-operations)
5. [API Integration](#api-integration)
6. [Error Handling](#error-handling)

## Basic Encoding/Decoding

### Quick Text Encoding

```python
from vibedna import DNAEncoder, DNADecoder

# Simple text encoding
encoder = DNAEncoder()
dna = encoder.encode_raw("Hello World")
print(f"Encoded: {dna}")
# Output: GCTAGCTACGATCGATCGAT...

# Decode back
decoder = DNADecoder()
data = decoder.decode_raw(dna)
print(f"Decoded: {data.decode()}")
# Output: Hello World
```

### Full File Encoding with Metadata

```python
from vibedna import DNAEncoder, DNADecoder, EncodingConfig, EncodingScheme

# Read binary file
with open("document.pdf", "rb") as f:
    data = f.read()

# Configure encoder for balanced GC content
config = EncodingConfig(
    scheme=EncodingScheme.BALANCED_GC,
    error_correction=True,
)
encoder = DNAEncoder(config)

# Encode with metadata
dna = encoder.encode(
    data,
    filename="document.pdf",
    mime_type="application/pdf"
)

print(f"Original size: {len(data)} bytes")
print(f"DNA length: {len(dna)} nucleotides")
print(f"Expansion ratio: {len(dna) / len(data):.2f}x")

# Save to FASTA file
with open("document.dna", "w") as f:
    f.write(f">VibeDNA:document.pdf\n")
    for i in range(0, len(dna), 80):
        f.write(dna[i:i+80] + "\n")
```

### Decoding with Error Correction

```python
from vibedna import DNADecoder

# Read DNA file
with open("document.dna", "r") as f:
    content = f.read()

# Parse FASTA format
lines = content.strip().split("\n")
dna = "".join(line for line in lines[1:] if not line.startswith(">"))

# Decode
decoder = DNADecoder()
result = decoder.decode(dna)

print(f"Filename: {result.filename}")
print(f"MIME type: {result.mime_type}")
print(f"Original size: {len(result.data)} bytes")
print(f"Errors detected: {result.errors_detected}")
print(f"Errors corrected: {result.errors_corrected}")
print(f"Integrity valid: {result.integrity_valid}")

# Save decoded file
with open(result.filename, "wb") as f:
    f.write(result.data)
```

## Working with Files

### Using Different Encoding Schemes

```python
from vibedna import DNAEncoder, EncodingConfig, EncodingScheme

data = b"Test data for encoding comparison"

# Compare all schemes
for scheme in EncodingScheme:
    config = EncodingConfig(scheme=scheme, error_correction=False)
    encoder = DNAEncoder(config)

    dna = encoder.encode_raw(data)

    gc_count = sum(1 for n in dna if n in "GC")
    gc_ratio = gc_count / len(dna)

    print(f"{scheme.value:15} - Length: {len(dna):5} nt, GC: {gc_ratio:.2%}")

# Output:
# quaternary      - Length:  136 nt, GC: 48.53%
# balanced_gc     - Length:  136 nt, GC: 50.00%
# rll             - Length:  150 nt, GC: 44.00%
# triplet         - Length:  816 nt, GC: 33.33%
```

### Stream Encoding for Large Files

```python
from vibedna import DNAEncoder, EncodingConfig

def file_chunk_generator(filepath, chunk_size=8192):
    """Generate file chunks."""
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

# Stream encode a large file
config = EncodingConfig(error_correction=True)
encoder = DNAEncoder(config)

with open("large_file_encoded.dna", "w") as out:
    for dna_chunk in encoder.encode_stream(file_chunk_generator("large_file.bin")):
        out.write(dna_chunk)
```

## DNA Computation

### Logic Gate Operations

```python
from vibedna import DNAComputeEngine, DNALogicGate

engine = DNAComputeEngine()

# Define two DNA values
a = "ATCGATCG"
b = "GCTAGCTA"

# Apply various logic gates
print(f"A:       {a}")
print(f"B:       {b}")
print(f"A AND B: {engine.apply_gate(DNALogicGate.AND, a, b)}")
print(f"A OR B:  {engine.apply_gate(DNALogicGate.OR, a, b)}")
print(f"A XOR B: {engine.apply_gate(DNALogicGate.XOR, a, b)}")
print(f"NOT A:   {engine.apply_gate(DNALogicGate.NOT, a)}")
```

### Arithmetic Operations

```python
from vibedna import DNAComputeEngine

engine = DNAComputeEngine()

# DNA addition
a = "AATC"  # 6 in quaternary
b = "AACT"  # 5 in quaternary
result, overflow = engine.add(a, b)
print(f"{a} + {b} = {result} (overflow: {overflow})")

# DNA multiplication
result = engine.multiply(a, b)
print(f"{a} × {b} = {result}")

# DNA division
quotient, remainder = engine.divide("ATCG", "AATC")
print(f"ATCG ÷ AATC = {quotient} R {remainder}")
```

### Complex Expressions

```python
from vibedna import DNAComputeEngine

engine = DNAComputeEngine()

# Execute compound expression
result = engine.execute_expression(
    "(A AND B) XOR C",
    {
        "A": "ATCGATCG",
        "B": "GCTAGCTA",
        "C": "AATTCCGG"
    }
)
print(f"Result: {result}")
```

## File System Operations

### Basic CRUD Operations

```python
from vibedna import DNAFileSystem

# Initialize file system
fs = DNAFileSystem()

# Create directories
fs.create_directory("/documents")
fs.create_directory("/images")

# Create files
fs.create_file("/documents/report.txt", b"Annual Report 2026")
fs.create_file("/documents/notes.txt", b"Meeting notes")
fs.create_file("/images/logo.png", open("logo.png", "rb").read())

# List directory
print("Contents of /documents:")
for item in fs.list_directory("/documents"):
    print(f"  - {item.name} ({item.original_size} bytes)")

# Read file
data = fs.read_file("/documents/report.txt")
print(f"Content: {data.decode()}")

# Update file
fs.update_file("/documents/report.txt", b"Updated Annual Report 2026")

# Delete file
fs.delete_file("/documents/notes.txt")

# Get storage stats
stats = fs.get_storage_stats()
print(f"\nStorage Statistics:")
print(f"  Total files: {stats['total_files']}")
print(f"  Binary size: {stats['total_binary_size']} bytes")
print(f"  DNA length: {stats['total_dna_length']} nucleotides")
```

### Search and Indexing

```python
from vibedna import DNAFileSystem
from datetime import datetime, timedelta

fs = DNAFileSystem()

# Create some test files
fs.create_file("/data/file1.txt", b"Hello", tags=["important"])
fs.create_file("/data/file2.txt", b"World", tags=["draft"])
fs.create_file("/backup/file3.txt", b"Backup", tags=["important"])

# Search by path prefix
results = fs.search(path_prefix="/data")
print(f"Files in /data: {[f.name for f in results]}")

# Search by tags
results = fs.search(tags=["important"])
print(f"Important files: {[f.name for f in results]}")

# Search by date
yesterday = datetime.utcnow() - timedelta(days=1)
results = fs.search(created_after=yesterday)
print(f"Recent files: {[f.name for f in results]}")
```

## API Integration

### Using the REST API with Python

```python
import requests
import base64

BASE_URL = "http://localhost:8000"

# Encode data
data = b"Hello, VibeDNA API!"
response = requests.post(
    f"{BASE_URL}/encode",
    json={
        "data": base64.b64encode(data).decode(),
        "filename": "hello.txt",
        "scheme": "quaternary"
    }
)
result = response.json()
print(f"Encoded DNA: {result['dna_sequence'][:50]}...")

# Decode data
response = requests.post(
    f"{BASE_URL}/decode",
    json={
        "dna_sequence": result["dna_sequence"],
        "verify_checksum": True
    }
)
decoded = response.json()
print(f"Decoded: {base64.b64decode(decoded['data']).decode()}")

# Perform computation
response = requests.post(
    f"{BASE_URL}/compute",
    json={
        "operation": "XOR",
        "sequence_a": "ATCGATCG",
        "sequence_b": "GCTAGCTA"
    }
)
print(f"XOR result: {response.json()['result']}")
```

### Using cURL

```bash
# Quick encode
curl -X POST "http://localhost:8000/quick/encode" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'

# Upload and encode file
curl -X POST "http://localhost:8000/encode/file" \
  -F "file=@document.pdf" \
  -F "scheme=quaternary" \
  -o document.dna

# Store in DNA filesystem
curl -X POST "http://localhost:8000/fs/store?path=/documents" \
  -F "file=@report.txt"

# List files
curl "http://localhost:8000/fs/list?path=/documents"

# Get storage stats
curl "http://localhost:8000/fs/stats"
```

## Error Handling

### Handling Encoding Errors

```python
from vibedna import DNAEncoder, EncodingConfig
from vibedna.utils.validators import ValidationError

try:
    config = EncodingConfig(gc_balance_target=0.1)  # Invalid value
    encoder = DNAEncoder(config)
except ValueError as e:
    print(f"Configuration error: {e}")

# Correct approach
config = EncodingConfig(gc_balance_target=0.5)
encoder = DNAEncoder(config)
```

### Handling Decoding Errors

```python
from vibedna import DNADecoder
from vibedna.core.decoder import InvalidSequenceError, ChecksumError

decoder = DNADecoder()

# Invalid sequence
try:
    decoder.decode("INVALID_SEQUENCE")
except InvalidSequenceError as e:
    print(f"Invalid sequence: {e}")

# Corrupted data
try:
    # Sequence with too many errors to correct
    corrupted_dna = "XXXXXXXXXXXXXXXX"
    result = decoder.decode(corrupted_dna)
except ChecksumError as e:
    print(f"Checksum failed: {e}")
```

### Validating Sequences

```python
from vibedna.utils.validators import validate_dna_sequence

sequence = "ATCGATCG"
is_valid, issues = validate_dna_sequence(sequence)

if is_valid:
    print("Sequence is valid")
else:
    print(f"Validation issues: {issues}")

# Validate with header/footer requirements
is_valid, issues = validate_dna_sequence(
    sequence,
    require_header=True,
    require_footer=True
)
```

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
