# VibeDNA Encoding Specification

## Version 1.0

This document specifies the VibeDNA binary-to-DNA encoding format and protocols.

## 1. Overview

VibeDNA encodes binary data as DNA sequences using a structured format that includes:
- File metadata header
- Data blocks with checksums
- Reed-Solomon error correction
- File footer with integrity verification

## 2. Nucleotide Encoding

### 2.1 Primary Mapping (Quaternary)

The primary encoding uses a 2-bit to nucleotide mapping:

| Binary | Decimal | Nucleotide | Name |
|--------|---------|------------|------|
| 00 | 0 | A | Adenine |
| 01 | 1 | T | Thymine |
| 10 | 2 | C | Cytosine |
| 11 | 3 | G | Guanine |

This provides the maximum storage density of 2 bits per nucleotide.

### 2.2 Balanced GC Encoding

To maintain GC content between 40-60% (optimal for DNA synthesis), a rotating mapping scheme is used:

**Rotation 0 (positions 0-3):**
| Binary | Nucleotide |
|--------|------------|
| 00 | A |
| 01 | T |
| 10 | G |
| 11 | C |

**Rotation 1 (positions 4-7):**
| Binary | Nucleotide |
|--------|------------|
| 00 | T |
| 01 | A |
| 10 | C |
| 11 | G |

The rotation cycles every 4 nucleotides.

### 2.3 Run-Length Limited (RLL) Encoding

To prevent homopolymer runs (consecutive identical nucleotides) that cause sequencing errors:

- Maximum run length: 3 consecutive identical nucleotides
- When a run would exceed 3, insert a spacer nucleotide
- Spacer selection: Use complement (A↔C, T↔G)

Example:
- Input: AAAA (would be 4 A's)
- Output: AAAC (spacer C inserted after 3 A's)

### 2.4 Redundant Triplet Encoding

For maximum error tolerance, each bit is encoded as 3 nucleotides:

| Bit | Triplet |
|-----|---------|
| 0 | ATC |
| 1 | GAC |

Decoding uses majority voting to recover from single-nucleotide errors within a triplet.

## 3. File Format Structure

### 3.1 Complete Structure

```
┌────────────────────────────────────────────────────┐
│ HEADER (256 nucleotides)                           │
├────────────────────────────────────────────────────┤
│ DATA BLOCK 1                                       │
│   Block Header (16 nt)                             │
│   Block Data (1024 nt)                             │
│   Error Correction (64 nt)                         │
├────────────────────────────────────────────────────┤
│ DATA BLOCK 2                                       │
│   ...                                              │
├────────────────────────────────────────────────────┤
│ DATA BLOCK N                                       │
│   ...                                              │
├────────────────────────────────────────────────────┤
│ FOOTER (32 nucleotides)                            │
└────────────────────────────────────────────────────┘
```

### 3.2 Header Structure (256 nucleotides)

| Field | Size (nt) | Description |
|-------|-----------|-------------|
| Magic | 8 | File identifier: `ATCGATCG` |
| Version | 4 | Format version (encoded) |
| Scheme | 4 | Encoding scheme identifier |
| File Size | 32 | Original binary size (64 bits) |
| Filename | 128 | Encoded filename (32 bytes) |
| MIME Type | 32 | Content type (8 bytes) |
| Checksum | 32 | Header integrity (SHA-256 fragment) |
| Reserved | 16 | Future use (all A's) |

**Scheme Identifiers:**
| Scheme | ID |
|--------|-----|
| Quaternary | AAAA |
| Balanced GC | AAAT |
| RLL | AATC |
| Triplet | AATG |

### 3.3 Block Structure

Each data block contains:

**Block Header (16 nucleotides):**
| Field | Size (nt) | Description |
|-------|-----------|-------------|
| Index | 8 | Block sequence number (0-65535) |
| Checksum | 8 | Block data integrity |

**Block Data:**
- Standard: 1024 nucleotides (512 bytes)
- Last block: Variable length

**Error Correction:**
- 64 nucleotides Reed-Solomon parity per block
- Can correct up to 8 nucleotide errors

### 3.4 Footer Structure (32 nucleotides)

| Field | Size (nt) | Description |
|-------|-----------|-------------|
| End Marker | 8 | File end: `GCTAGCTA` |
| Block Count | 8 | Total number of blocks |
| Checksum | 16 | Final integrity check |

## 4. Error Correction

### 4.1 Reed-Solomon in GF(4)

VibeDNA uses Reed-Solomon error correction adapted for GF(4):

- Field: GF(4) = {0, 1, α, α+1} mapped to {A, T, C, G}
- Generator polynomial: Product of (x - α^i) for i = 0 to nsym-1
- Default nsym = 16 provides correction of 8 errors

**GF(4) Addition Table:**
```
  + | A  T  C  G
----+------------
  A | A  T  C  G
  T | T  A  G  C
  C | C  G  A  T
  G | G  C  T  A
```

**GF(4) Multiplication Table:**
```
  × | A  T  C  G
----+------------
  A | A  A  A  A
  T | A  T  C  G
  C | A  C  G  T
  G | A  G  T  C
```

### 4.2 Checksum Algorithm

Checksums use SHA-256 truncated and encoded as DNA:

1. Compute SHA-256 of input sequence
2. Take first N bytes
3. Encode as quaternary DNA

## 5. DNA Computation

### 5.1 Logic Gates

Operations on DNA-encoded values using nucleotide arithmetic:

| Gate | Operation |
|------|-----------|
| AND | min(a, b) |
| OR | max(a, b) |
| XOR | (a + b) mod 4 |
| NOT | complement (A↔G, T↔C) |

### 5.2 Arithmetic

Quaternary (base-4) arithmetic:

- Addition: With carry propagation
- Subtraction: With borrow
- Multiplication: Shift-and-add
- Division: With quotient and remainder

## 6. Constraints

### 6.1 Synthesis Constraints

For DNA synthesis compatibility:
- GC content: 40-60% (balanced_gc scheme)
- No homopolymer runs > 3 (rll scheme)
- Avoid restriction enzyme sites

### 6.2 Size Limits

- Maximum file size: 100 MB (recommended)
- Maximum sequence length: ~800 million nucleotides
- Block size: 512 bytes (1024 nucleotides)

## 7. Examples

### 7.1 Encoding "Hi"

Input: `Hi` = `0x48 0x69`
Binary: `01001000 01101001`

**Quaternary encoding:**
```
01 00 10 00 01 10 10 01
T  A  C  A  T  C  C  T
```

Result: `TACATCCT`

### 7.2 Complete File

Encoding "Hello" with quaternary scheme:

```
ATCGATCG                    # Magic
AAAT                        # Version 1.0
AAAA                        # Quaternary scheme
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA  # File size (5 bytes)
[128 nt filename]           # "Hello"
[32 nt MIME type]           # "application/octet-stream"
[32 nt checksum]            # Header checksum
AAAAAAAAAAAAAAAA           # Reserved
[Block 0 header]            # Index 0, block checksum
GCTAGCTACGATCGATCGAT       # "Hello" encoded
[64 nt Reed-Solomon parity] # Error correction
GCTAGCTA                    # End marker
AAAAAAAT                    # Block count (1)
[16 nt final checksum]      # Final checksum
```

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
