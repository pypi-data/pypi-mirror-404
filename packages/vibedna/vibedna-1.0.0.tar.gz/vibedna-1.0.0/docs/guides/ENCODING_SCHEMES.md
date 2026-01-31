# VibeDNA Encoding Schemes Guide

A comprehensive guide to the binary-to-DNA encoding schemes available in VibeDNA.

---

## Table of Contents

1. [Overview of DNA Encoding](#1-overview-of-dna-encoding)
2. [Quaternary Encoding (Standard)](#2-quaternary-encoding-standard)
3. [Balanced GC Encoding](#3-balanced-gc-encoding)
4. [Run-Length Limited (RLL) Encoding](#4-run-length-limited-rll-encoding)
5. [Redundant Triplet Encoding](#5-redundant-triplet-encoding)
6. [Choosing the Right Scheme](#6-choosing-the-right-scheme)
7. [Custom Encoding Schemes](#7-custom-encoding-schemes)

---

## 1. Overview of DNA Encoding

### Why Encode Binary to DNA?

DNA (Deoxyribonucleic Acid) offers remarkable properties for data storage:

```
+----------------------------------+-----------------------------+
|           DNA Storage            |      Traditional Storage    |
+----------------------------------+-----------------------------+
| Density: ~215 petabytes/gram     | Density: ~1 TB per device   |
| Durability: Thousands of years   | Durability: 5-20 years      |
| Energy: Zero (passive storage)   | Energy: Constant power      |
| Replication: Enzymatic copying   | Replication: Manual copying |
+----------------------------------+-----------------------------+
```

DNA uses four nucleotide bases to store information:

```
        Purines                    Pyrimidines
    +-----------+               +-----------+
    |     A     |               |     T     |
    | (Adenine) |  <-- pairs -> | (Thymine) |
    +-----------+               +-----------+

    +-----------+               +-----------+
    |     G     |               |     C     |
    | (Guanine) |  <-- pairs -> | (Cytosine)|
    +-----------+               +-----------+
```

### Base-4 vs Base-2 Comparison

DNA naturally represents a **quaternary (base-4) system**, making it ideal for binary encoding:

```
    Binary (Base-2)                Quaternary (Base-4)
    ---------------                -------------------
    0, 1                           A, T, C, G

    1 bit = 2 states               1 nucleotide = 4 states
    1 byte = 8 bits                1 byte = 4 nucleotides

    +-----------------------------+-----------------------------+
    |   Binary Representation     |   DNA Representation        |
    +-----------------------------+-----------------------------+
    |   00 00 00 00  (8 bits)     |   A  A  A  A  (4 nt)        |
    |   11 11 11 11  (8 bits)     |   G  G  G  G  (4 nt)        |
    |   01 00 10 11  (8 bits)     |   T  A  C  G  (4 nt)        |
    +-----------------------------+-----------------------------+
```

**Information Density:**
- 1 nucleotide encodes 2 bits (log2(4) = 2)
- 1 byte (8 bits) requires 4 nucleotides
- Compression ratio: 4:1 (bits to nucleotides)

---

## 2. Quaternary Encoding (Standard)

### How It Works

Quaternary encoding is VibeDNA's default scheme, mapping every 2 bits to exactly one nucleotide:

```
    +--------+--------------+-------------+
    |  Bits  |  Nucleotide  |    Base     |
    +--------+--------------+-------------+
    |   00   |      A       |   Adenine   |
    |   01   |      T       |   Thymine   |
    |   10   |      C       |   Cytosine  |
    |   11   |      G       |   Guanine   |
    +--------+--------------+-------------+
```

**Encoding Process:**

```
    Input: "Hi" (ASCII)

    Step 1: Convert to binary
    +---------+-----------+------------------+
    | Char    | ASCII     | Binary           |
    +---------+-----------+------------------+
    | 'H'     | 72        | 01001000         |
    | 'i'     | 105       | 01101001         |
    +---------+-----------+------------------+

    Step 2: Group into 2-bit chunks
    +----------------------------------------+
    | 01 | 00 | 10 | 00 | 01 | 10 | 10 | 01 |
    +----------------------------------------+

    Step 3: Map to nucleotides
    +----------------------------------------+
    |  T |  A |  C |  A |  T |  C |  C |  T |
    +----------------------------------------+

    Result: "TACATCCT"
```

### Density

- **2 bits per nucleotide** (maximum theoretical density)
- 1 byte = 4 nucleotides
- 1 KB = 4,096 nucleotides
- 1 MB = 4,194,304 nucleotides

### Use Cases

- **Maximum storage density** - When space efficiency is critical
- **Simple applications** - Quick prototyping and testing
- **Non-synthesis workflows** - Computational DNA storage simulations
- **Low-error environments** - When data integrity is guaranteed

### Code Example

```python
from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme

# Create encoder with quaternary scheme (default)
config = EncodingConfig(scheme=EncodingScheme.QUATERNARY)
encoder = DNAEncoder(config)

# Encode data
data = b"Hello, DNA!"
dna_sequence = encoder.encode(data, filename="hello.txt")

# Raw encoding without headers
raw_dna = encoder.encode_raw(b"Hi")
print(raw_dna)  # Output: "TACATCCT"

# Verify known mappings
assert encoder.encode_raw(b"\x00") == "AAAA"  # 00000000 -> AAAA
assert encoder.encode_raw(b"\xFF") == "GGGG"  # 11111111 -> GGGG
assert encoder.encode_raw(b"\xAA") == "CCCC"  # 10101010 -> CCCC
assert encoder.encode_raw(b"\x55") == "TTTT"  # 01010101 -> TTTT
```

---

## 3. Balanced GC Encoding

### Purpose: Synthesis Compatibility

DNA synthesis and sequencing technologies have optimal performance when the **GC content** (ratio of G and C nucleotides) is balanced. Extreme GC ratios cause:

```
    GC Content Problems:
    +-------------------+--------------------------------+
    | Low GC (<30%)     | Poor synthesis yields          |
    |                   | Weak secondary structures      |
    +-------------------+--------------------------------+
    | High GC (>70%)    | Strong secondary structures    |
    |                   | Polymerase stalling            |
    |                   | Sequencing errors              |
    +-------------------+--------------------------------+
    | Balanced (40-60%) | Optimal synthesis              |
    |                   | Reliable sequencing            |
    |                   | Stable storage                 |
    +-------------------+--------------------------------+
```

### How GC Content is Balanced

VibeDNA uses **rotating mappings** that cycle through four different bit-to-nucleotide tables:

```
    Rotation 0 (Standard):     Rotation 1:
    +------+-----+             +------+-----+
    |  00  |  A  |             |  00  |  T  |
    |  01  |  T  |             |  01  |  A  |
    |  10  |  G  |             |  10  |  C  |
    |  11  |  C  |             |  11  |  G  |
    +------+-----+             +------+-----+

    Rotation 2:                Rotation 3:
    +------+-----+             +------+-----+
    |  00  |  G  |             |  00  |  C  |
    |  01  |  C  |             |  01  |  G  |
    |  10  |  A  |             |  10  |  T  |
    |  11  |  T  |             |  11  |  A  |
    +------+-----+             +------+-----+
```

**Rotation Pattern:**

```
    Position:  1   2   3   4   5   6   7   8   9  10  11  12 ...
    Rotation:  0   0   0   0   1   1   1   1   2   2   2   2 ...
              |___________|   |___________|   |___________|
                Group 1         Group 2         Group 3

    - Rotation changes every 4 nucleotides
    - Ensures each rotation contributes equally
    - Balances GC content over windows
```

**Encoding Example:**

```
    Input: 0x00 0x00 (16 bits = 8 nucleotides)
    Binary: 00 00 00 00 | 00 00 00 00
            |           |
            v           v
    Rot 0:  A  A  A  A  |
    Rot 1:              |  T  T  T  T

    Result: "AAAATTTT"
    GC Content: 0% (still unbalanced for this input)

    Input: 0x55 0xAA (alternating pattern)
    Binary: 01 01 01 01 | 10 10 10 10
            |           |
            v           v
    Rot 0:  T  T  T  T  |
    Rot 1:              |  C  C  C  C

    Result: "TTTTCCCC"
    GC Content: 50% (balanced!)
```

### Target: 40-60% GC

The encoder aims for GC content within the optimal synthesis range:

```
    0%        30%       40%       50%       60%       70%      100%
    |----------|---------|=========|=========|---------|---------|
    |   Bad    | Marginal|       Optimal      | Marginal|   Bad   |
    |          |         |      Range         |         |         |
```

### Use Cases

- **DNA synthesis** - Preparing sequences for physical synthesis
- **Long-term storage** - Sequences that will be physically stored
- **Sequencing workflows** - Data meant for Illumina/Nanopore sequencing
- **Biological compatibility** - Sequences used in living systems

### Code Example

```python
from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme

# Create encoder with balanced GC scheme
config = EncodingConfig(
    scheme=EncodingScheme.BALANCED_GC,
    gc_balance_target=0.5  # Target 50% GC content
)
encoder = DNAEncoder(config)

# Encode data
data = b"AAAA"  # Would be all A's in quaternary
dna_sequence = encoder.encode_raw(data)

# Verify GC balance
gc_count = sum(1 for n in dna_sequence if n in "GC")
gc_ratio = gc_count / len(dna_sequence)
print(f"GC Content: {gc_ratio * 100:.1f}%")

# Full encoding with headers
result = encoder.encode(data, filename="balanced.txt")
```

---

## 4. Run-Length Limited (RLL) Encoding

### Purpose: Sequencing Accuracy

**Homopolymer runs** (consecutive identical nucleotides) cause significant problems:

```
    Homopolymer Run Example:
    +------------------------------------------+
    |  A A A A A A A A A A A A A A A A A A    |
    |  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  |
    |         18 consecutive Adenines          |
    +------------------------------------------+

    Problems:
    +----------------------+--------------------------------+
    | Polymerase slippage  | Incorrect length during copy   |
    | Synthesis errors     | Insertions/deletions           |
    | Sequencing errors    | Nanopore miscounts run length  |
    | Signal degradation   | Weak signal differentiation    |
    +----------------------+--------------------------------+
```

### How Homopolymer Runs are Avoided

RLL encoding inserts **spacer nucleotides** when runs would exceed the maximum allowed length:

```
    Spacer Selection:
    +-------------+-------------+
    | Current nt  | Spacer nt   |
    +-------------+-------------+
    |      A      |      C      |
    |      T      |      G      |
    |      C      |      A      |
    |      G      |      T      |
    +-------------+-------------+

    Encoding Process:
    +-------------------------------------------------+
    | Input binary: 00 00 00 00 00 00 00 00           |
    | Standard:     A  A  A  A  A  A  A  A            |
    |               ^^^^^^^^^^^^^^^^^^^^^^^^          |
    |               8 consecutive A's (too long!)     |
    +-------------------------------------------------+
                            |
                            v
    +-------------------------------------------------+
    | RLL Encoded:  A  A  A  C  A  A  A  C            |
    |               ^^^^^^^    ^^^^^^^                |
    |               3 A's  |   3 A's  |               |
    |                   spacer     spacer             |
    +-------------------------------------------------+
```

### Max Run Length Constraints

VibeDNA enforces a maximum homopolymer run of **3 nucleotides**:

```
    Allowed:            Not Allowed:
    +----------+        +----------+
    |   AAA    |        |  AAAA    |
    |   TTT    |        |  TTTTT   |
    |   CCC    |        |  CCCCCC  |
    |   GGG    |        |  GGGGGGG |
    +----------+        +----------+

    Run Length Detection and Breaking:

    Input: AAAAAA (6 A's)

    Processing:
    Position 1: A, run=1 -> output A
    Position 2: A, run=2 -> output A
    Position 3: A, run=3 -> output A (max reached)
    Position 4: A, run=4 -> insert C, output A, run=1
    Position 5: A, run=2 -> output A
    Position 6: A, run=3 -> output A

    Result: AAACAAA
```

### Use Cases

- **Nanopore sequencing** - Highly susceptible to homopolymer errors
- **Long-read sequencing** - PacBio and similar technologies
- **Error-sensitive applications** - When accuracy is critical
- **Synthesis optimization** - Reducing synthesis failures

### Code Example

```python
from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme

# Create encoder with RLL scheme
config = EncodingConfig(
    scheme=EncodingScheme.RUN_LENGTH_LIMITED,
    max_homopolymer_run=3  # Maximum 3 consecutive same nucleotides
)
encoder = DNAEncoder(config)

# Encode data that would create long runs
data = b"\x00\x00\x00\x00"  # Would be AAAAAAAAAAAAAAAA in quaternary
dna_sequence = encoder.encode_raw(data)

# Verify no long runs
def max_run_length(seq):
    max_run = 1
    current = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i-1]:
            current += 1
            max_run = max(max_run, current)
        else:
            current = 1
    return max_run

run_length = max_run_length(dna_sequence)
print(f"Maximum run length: {run_length}")  # Should be <= 3
assert run_length <= 3

# Full encoding
result = encoder.encode(data, filename="rll_encoded.txt")
```

---

## 5. Redundant Triplet Encoding

### Purpose: Maximum Error Tolerance

Triplet encoding provides **3x redundancy** for each bit, enabling error recovery through majority voting:

```
    Standard vs Triplet:
    +-------------------+-------------------+
    |     Standard      |      Triplet      |
    +-------------------+-------------------+
    | 1 bit -> 1/2 nt   | 1 bit -> 3 nt     |
    | No redundancy     | 3x redundancy     |
    | Error = data loss | Error = recoverable|
    +-------------------+-------------------+
```

### How Redundancy Works

Each binary bit is encoded as a triplet of nucleotides:

```
    Triplet Mapping:
    +------+------------+-----------------------+
    | Bit  |  Triplet   |  Interpretation       |
    +------+------------+-----------------------+
    |  0   |    ATC     | Adenine-Thymine-Cytos |
    |  1   |    GAC     | Guanine-Adenine-Cytos |
    +------+------------+-----------------------+

    Encoding Example:
    Input byte: 0x41 (ASCII 'A')
    Binary:     01000001

    Bit-by-bit encoding:
    +-----+--------+----------+
    | Bit | Value  | Triplet  |
    +-----+--------+----------+
    |  1  |   0    |   ATC    |
    |  2  |   1    |   GAC    |
    |  3  |   0    |   ATC    |
    |  4  |   0    |   ATC    |
    |  5  |   0    |   ATC    |
    |  6  |   0    |   ATC    |
    |  7  |   0    |   ATC    |
    |  8  |   1    |   GAC    |
    +-----+--------+----------+

    Result: ATCGACATCATCATCATCATCGAC (24 nucleotides)
```

### Majority Voting for Decoding

When errors occur, majority voting recovers the original bit:

```
    Error Recovery Example:

    Original triplet for bit "0": ATC

    Scenario 1: No errors
    +-----+-----+-----+
    |  A  |  T  |  C  |
    +-----+-----+-----+
    Matches ATC: 3/3 -> Decoded as 0 (correct)

    Scenario 2: One error (T mutated to G)
    +-----+-----+-----+
    |  A  |  G  |  C  |  <- Error!
    +-----+-----+-----+
    Compare to ATC: A=A, G!=T, C=C -> 2/3 match
    Compare to GAC: A!=G, G=A?, C=C -> 1/3 match
    Decoded as 0 (correct despite error!)

    Scenario 3: Two errors (catastrophic)
    +-----+-----+-----+
    |  G  |  A  |  C  |  <- Two errors!
    +-----+-----+-----+
    Matches GAC: 3/3 -> Decoded as 1 (WRONG)

    Error Tolerance: Survives 1 error per triplet (33% error rate)
```

**Majority Voting Algorithm:**

```
    Input: Possibly corrupted triplet

    +--------------------------------+
    | Calculate ATC match score:     |
    | score_0 = matches(triplet,ATC) |
    +--------------------------------+
              |
              v
    +--------------------------------+
    | Calculate GAC match score:     |
    | score_1 = matches(triplet,GAC) |
    +--------------------------------+
              |
              v
    +--------------------------------+
    | if score_1 > score_0:          |
    |     return "1"                 |
    | else:                          |
    |     return "0"                 |
    +--------------------------------+
```

### Use Cases

- **Archival storage** - Data stored for centuries
- **Harsh environments** - High radiation or temperature
- **Critical data** - Medical records, legal documents
- **Degraded samples** - Ancient DNA recovery workflows
- **Proof of concept** - Testing error correction

### Code Example

```python
from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme

# Create encoder with triplet scheme
config = EncodingConfig(scheme=EncodingScheme.REDUNDANT_TRIPLET)
encoder = DNAEncoder(config)

# Encode data
data = b"A"  # Single byte
dna_sequence = encoder.encode_raw(data)

# Verify expansion: 1 byte = 8 bits = 24 nucleotides
print(f"Input: 1 byte")
print(f"Output: {len(dna_sequence)} nucleotides")
assert len(dna_sequence) == 24

# Demonstrate error tolerance
from vibedna.core.decoder import DNADecoder

decoder = DNADecoder()

# Original triplet for bit "0" is "ATC"
# Introduce an error: change T to G
original = "ATC"
corrupted = "AGC"  # One error

# Decode using majority voting (internal mechanism)
decoded_original = decoder.decode_raw(original + original + original, scheme="triplet")
decoded_corrupted = decoder.decode_raw(corrupted + corrupted + corrupted, scheme="triplet")

print(f"Original decodes to: {decoded_original}")
print(f"Corrupted decodes to: {decoded_corrupted}")  # Still correct!
```

---

## 6. Choosing the Right Scheme

### Decision Matrix

Use this flowchart to select the optimal encoding scheme:

```
                        START
                          |
                          v
              +------------------------+
              | Will DNA be physically |
              |      synthesized?      |
              +------------------------+
                    |           |
                   YES          NO
                    |           |
                    v           v
    +------------------+    +------------------+
    | Is GC balance    |    | Is maximum       |
    | critical for     |    | density needed?  |
    | synthesis?       |    +------------------+
    +------------------+          |       |
          |       |              YES      NO
         YES      NO              |       |
          |       |               v       v
          v       v          +---------+  |
    +-----------+ |          |QUATERNARY  |
    |BALANCED_GC| |          +---------+  |
    +-----------+ |                       |
                  v                       |
    +------------------------+            |
    | Using Nanopore or      |            |
    | homopolymer-sensitive  |<-----------+
    | sequencing?            |
    +------------------------+
          |       |
         YES      NO
          |       |
          v       v
    +-------+   +------------------------+
    |  RLL  |   | Is data critical and   |
    +-------+   | error tolerance needed?|
                +------------------------+
                      |       |
                     YES      NO
                      |       |
                      v       v
                +---------+  +-----------+
                | TRIPLET |  | QUATERNARY|
                +---------+  +-----------+
```

### Trade-offs Comparison Table

```
+----------------+----------+------------+-----------+-------------+
|    Scheme      | Density  | GC Balance | No Homo-  | Error       |
|                | (bits/nt)|            | polymers  | Tolerance   |
+----------------+----------+------------+-----------+-------------+
| QUATERNARY     |   2.0    |     No     |    No     |    None     |
| (Standard)     |          |            |           |             |
+----------------+----------+------------+-----------+-------------+
| BALANCED_GC    |   2.0    |    Yes     |    No     |    None     |
|                |          | (40-60%)   |           |             |
+----------------+----------+------------+-----------+-------------+
| RLL            |   ~1.8   |     No     |   Yes     |    None     |
| (Run-Limited)  | (-10%)   |            | (max 3)   |             |
+----------------+----------+------------+-----------+-------------+
| TRIPLET        |   0.33   |     No     |    No     |    High     |
| (Redundant)    | (1/3)    |            |           | (1 err/bit) |
+----------------+----------+------------+-----------+-------------+
```

### Detailed Comparison

```
    Storage Efficiency (1 MB file):
    +----------------+------------------+------------------+
    |    Scheme      | Nucleotides      | Relative Size    |
    +----------------+------------------+------------------+
    | QUATERNARY     |   4,194,304      |      1.0x        |
    | BALANCED_GC    |   4,194,304      |      1.0x        |
    | RLL            |  ~4,600,000      |     ~1.1x        |
    | TRIPLET        |  25,165,824      |      6.0x        |
    +----------------+------------------+------------------+

    Synthesis Compatibility:
    +----------------+-------+-------+-------+-------+-------+
    |    Scheme      | Twist | IDT   | Genscr| Custom| Cloud |
    +----------------+-------+-------+-------+-------+-------+
    | QUATERNARY     |   ?   |   ?   |   ?   |   ?   |   ?   |
    | BALANCED_GC    |  +++  |  +++  |  +++  |  +++  |  +++  |
    | RLL            |  ++   |  ++   |  ++   |  ++   |  ++   |
    | TRIPLET        |   +   |   +   |   +   |   +   |   +   |
    +----------------+-------+-------+-------+-------+-------+
    Legend: +++ Excellent, ++ Good, + Acceptable, ? Variable

    Sequencing Accuracy:
    +----------------+-----------+-----------+-----------+
    |    Scheme      | Illumina  | Nanopore  |  PacBio   |
    +----------------+-----------+-----------+-----------+
    | QUATERNARY     |   Good    |   Poor    |   Poor    |
    | BALANCED_GC    |   Good    |   Poor    |   Poor    |
    | RLL            |   Good    |   Good    |   Good    |
    | TRIPLET        |   Good    |   Fair    |   Fair    |
    +----------------+-----------+-----------+-----------+
```

### Quick Reference

| Scenario | Recommended Scheme |
|----------|-------------------|
| Computational simulation | QUATERNARY |
| DNA synthesis order | BALANCED_GC |
| Nanopore sequencing | RLL |
| Archival storage (100+ years) | TRIPLET |
| General purpose | QUATERNARY |
| Medical/legal records | TRIPLET + Error Correction |

---

## 7. Custom Encoding Schemes

### How to Implement Custom Schemes

VibeDNA's `CodecRegistry` allows you to register custom encoding schemes:

```
    Custom Scheme Architecture:

    +------------------+
    |   CodecRegistry  |
    +------------------+
            |
            | register()
            v
    +------------------+       +-----------------+
    |    CodecInfo     |------>| Custom Encoder  |
    |   - name         |       | (binary -> DNA) |
    |   - encoder      |       +-----------------+
    |   - decoder      |
    |   - metadata     |       +-----------------+
    +------------------+------>| Custom Decoder  |
                               | (DNA -> binary) |
                               +-----------------+
```

### Implementation Steps

```python
from vibedna.core.codec_registry import CodecRegistry, CodecInfo

# Step 1: Define encoder function
def my_custom_encoder(binary: str) -> str:
    """
    Custom encoder: binary string to DNA sequence.

    Args:
        binary: String of '0' and '1' characters

    Returns:
        DNA sequence string (A, T, C, G characters)
    """
    # Example: Simple XOR-based encoding for obfuscation
    result = []
    xor_pattern = [0, 1, 1, 0]  # XOR pattern

    # Pad to even length
    if len(binary) % 2 != 0:
        binary += "0"

    for i in range(0, len(binary), 2):
        bits = binary[i:i + 2]
        # Apply XOR
        b0 = int(bits[0]) ^ xor_pattern[i % 4]
        b1 = int(bits[1]) ^ xor_pattern[(i + 1) % 4]
        xored = f"{b0}{b1}"

        # Map to nucleotide
        mapping = {"00": "A", "01": "T", "10": "C", "11": "G"}
        result.append(mapping[xored])

    return "".join(result)

# Step 2: Define decoder function
def my_custom_decoder(dna: str) -> str:
    """
    Custom decoder: DNA sequence to binary string.

    Args:
        dna: DNA sequence string

    Returns:
        Binary string
    """
    result = []
    xor_pattern = [0, 1, 1, 0]
    mapping = {"A": "00", "T": "01", "C": "10", "G": "11"}

    for i, nucleotide in enumerate(dna.upper()):
        if nucleotide not in mapping:
            continue
        bits = mapping[nucleotide]

        # Reverse XOR
        b0 = int(bits[0]) ^ xor_pattern[(i * 2) % 4]
        b1 = int(bits[1]) ^ xor_pattern[(i * 2 + 1) % 4]
        result.append(f"{b0}{b1}")

    return "".join(result)

# Step 3: Register the custom codec
registry = CodecRegistry()
registry.register(
    name="xor_obfuscated",
    description="XOR-obfuscated quaternary encoding",
    bits_per_nucleotide=2.0,
    error_tolerance="none",
    gc_balanced=False,
    homopolymer_safe=False,
    encoder=my_custom_encoder,
    decoder=my_custom_decoder,
)

# Step 4: Use the custom codec
codec = registry.get("xor_obfuscated")

# Encode
binary_data = "01001000"  # ASCII 'H'
encoded = codec.encoder(binary_data)
print(f"Encoded: {encoded}")

# Decode
decoded = codec.decoder(encoded)
print(f"Decoded: {decoded}")
assert decoded == binary_data
```

### Custom Scheme Template

```python
"""
Custom Encoding Scheme Template
"""

from typing import Callable
from vibedna.core.codec_registry import CodecRegistry


class CustomScheme:
    """Template for creating custom encoding schemes."""

    # Scheme metadata
    NAME = "custom_scheme"
    DESCRIPTION = "Description of your custom scheme"
    BITS_PER_NUCLEOTIDE = 2.0  # Adjust based on your scheme
    ERROR_TOLERANCE = "none"   # "none", "low", "medium", "high"
    GC_BALANCED = False
    HOMOPOLYMER_SAFE = False

    @classmethod
    def encode(cls, binary: str) -> str:
        """
        Encode binary string to DNA.

        Args:
            binary: Binary string (e.g., "01001000")

        Returns:
            DNA sequence (e.g., "ATCG")
        """
        # Implement your encoding logic here
        raise NotImplementedError

    @classmethod
    def decode(cls, dna: str) -> str:
        """
        Decode DNA to binary string.

        Args:
            dna: DNA sequence (e.g., "ATCG")

        Returns:
            Binary string (e.g., "01001000")
        """
        # Implement your decoding logic here
        raise NotImplementedError

    @classmethod
    def register(cls, registry: CodecRegistry = None) -> None:
        """Register this scheme with the codec registry."""
        if registry is None:
            registry = CodecRegistry()

        registry.register(
            name=cls.NAME,
            description=cls.DESCRIPTION,
            bits_per_nucleotide=cls.BITS_PER_NUCLEOTIDE,
            error_tolerance=cls.ERROR_TOLERANCE,
            gc_balanced=cls.GC_BALANCED,
            homopolymer_safe=cls.HOMOPOLYMER_SAFE,
            encoder=cls.encode,
            decoder=cls.decode,
        )


# Example: Implementing a Fountain Code-based scheme
class FountainCodeScheme(CustomScheme):
    """
    Fountain code encoding for rateless error correction.

    Generates unlimited encoded symbols from finite data,
    allowing recovery from any sufficient subset.
    """

    NAME = "fountain"
    DESCRIPTION = "Fountain code rateless erasure encoding"
    BITS_PER_NUCLEOTIDE = 1.5  # Variable due to overhead
    ERROR_TOLERANCE = "high"
    GC_BALANCED = True
    HOMOPOLYMER_SAFE = True

    @classmethod
    def encode(cls, binary: str) -> str:
        # Fountain code implementation
        # (Simplified example - real implementation would use LT codes)
        pass

    @classmethod
    def decode(cls, dna: str) -> str:
        # Fountain code decoding
        pass
```

### Best Practices for Custom Schemes

```
    Design Considerations:
    +----------------------------------------------------------+
    | 1. Reversibility                                          |
    |    - Ensure encode(decode(x)) == x for all valid x       |
    |    - Handle edge cases (empty input, padding)            |
    +----------------------------------------------------------+
    | 2. Error Handling                                         |
    |    - Validate input (only 0/1 for binary, ATCG for DNA)  |
    |    - Graceful degradation for corrupted sequences        |
    +----------------------------------------------------------+
    | 3. Performance                                            |
    |    - Optimize for streaming (avoid loading all in memory)|
    |    - Use generators for large datasets                   |
    +----------------------------------------------------------+
    | 4. Documentation                                          |
    |    - Document the mapping clearly                        |
    |    - Specify density and trade-offs                      |
    |    - Provide test vectors                                |
    +----------------------------------------------------------+
```

---

## Summary

VibeDNA provides four encoding schemes optimized for different use cases:

```
    +---------------+----------------------------------------+
    | QUATERNARY    | Maximum density, simple implementation |
    +---------------+----------------------------------------+
    | BALANCED_GC   | Optimal for DNA synthesis             |
    +---------------+----------------------------------------+
    | RLL           | Prevents sequencing errors            |
    +---------------+----------------------------------------+
    | TRIPLET       | Maximum error tolerance               |
    +---------------+----------------------------------------+
```

Choose based on your specific requirements for density, synthesis compatibility, sequencing accuracy, and error tolerance.

---

## See Also

- [VibeDNA Core API Documentation](/docs/api/core.md)
- [Error Correction Guide](/docs/guides/ERROR_CORRECTION.md)
- [Codec Registry Reference](/docs/api/codec_registry.md)

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
