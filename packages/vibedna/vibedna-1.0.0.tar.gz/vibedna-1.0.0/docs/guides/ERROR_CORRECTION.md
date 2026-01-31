# VibeDNA Error Correction Guide

This comprehensive guide explains the error correction mechanisms implemented in VibeDNA for ensuring data integrity in DNA-based storage.

---

## Table of Contents

1. [Why Error Correction Matters](#1-why-error-correction-matters)
2. [Reed-Solomon Codes Overview](#2-reed-solomon-codes-overview)
3. [VibeDNA's Implementation](#3-vibednas-implementation)
4. [GF(4) Mathematics](#4-gf4-mathematics)
5. [Encoding Process](#5-encoding-process)
6. [Decoding and Error Detection](#6-decoding-and-error-detection)
7. [Configuration Options](#7-configuration-options)
8. [Using Error Correction in VibeDNA](#8-using-error-correction-in-vibedna)

---

## 1. Why Error Correction Matters

DNA storage offers remarkable density and longevity, but it faces unique challenges that make error correction essential.

### 1.1 DNA Degradation Over Time

DNA molecules naturally degrade through several mechanisms:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DNA DEGRADATION SOURCES                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│   │  Hydrolysis  │   │  Oxidation   │   │  UV Damage   │        │
│   │              │   │              │   │              │        │
│   │  Breaks DNA  │   │  Modifies    │   │  Creates     │        │
│   │  backbone    │   │  bases       │   │  thymine     │        │
│   │              │   │  (G → 8-oxoG)│   │  dimers      │        │
│   └──────────────┘   └──────────────┘   └──────────────┘        │
│                                                                  │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│   │ Depurination │   │  Deamination │   │ Temperature  │        │
│   │              │   │              │   │  Fluctuation │        │
│   │  Loss of     │   │  C → U       │   │              │        │
│   │  A or G      │   │  (reads as T)│   │  Accelerates │        │
│   │  bases       │   │              │   │  all damage  │        │
│   └──────────────┘   └──────────────┘   └──────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Typical error rates over time:**
- Freshly synthesized DNA: 0.01-0.1% error rate
- 1 year storage (optimal conditions): 0.1-0.5%
- 10 years storage: 1-5%
- 100+ years (archived): 5-20%

### 1.2 Synthesis and Sequencing Errors

Modern DNA synthesis and sequencing introduce errors at multiple stages:

```
┌───────────────────────────────────────────────────────────────────────┐
│                     DNA DATA PIPELINE ERRORS                          │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ENCODING         SYNTHESIS         STORAGE         SEQUENCING       │
│  ────────         ─────────         ───────         ──────────       │
│                                                                       │
│  ┌─────┐         ┌─────────┐       ┌───────┐       ┌──────────┐      │
│  │Data │  ──►    │ Oligo   │  ──►  │ DNA   │  ──►  │ Reads    │      │
│  │     │         │Synthesis│       │Sample │       │          │      │
│  └─────┘         └─────────┘       └───────┘       └──────────┘      │
│                       │                │                │            │
│                       ▼                ▼                ▼            │
│                  ┌─────────┐     ┌──────────┐    ┌───────────┐       │
│                  │~0.1-1%  │     │ 0.01-5%  │    │ 0.1-15%   │       │
│                  │error    │     │ error    │    │ error     │       │
│                  │rate     │     │ rate     │    │ rate      │       │
│                  └─────────┘     └──────────┘    └───────────┘       │
│                                                                       │
│  Error Types:                                                         │
│  • Substitutions: A→G, T→C (transitions most common)                 │
│  • Insertions: Extra nucleotides in homopolymer runs                 │
│  • Deletions: Missing nucleotides                                    │
│  • Truncations: Incomplete sequences                                 │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 1.3 Data Integrity Requirements

For reliable data storage, VibeDNA must guarantee:

| Requirement | Target | Mechanism |
|-------------|--------|-----------|
| Bit-perfect recovery | 100% | Reed-Solomon codes |
| Error detection | Up to 16 errors/block | Syndrome computation |
| Error correction | Up to 8 errors/block | Forney algorithm |
| Integrity verification | Always | SHA-256 checksums |

---

## 2. Reed-Solomon Codes Overview

Reed-Solomon (RS) codes are a class of error-correcting codes that are particularly well-suited for DNA storage due to their ability to correct burst errors.

### 2.1 How Reed-Solomon Works

```
┌────────────────────────────────────────────────────────────────────────┐
│                    REED-SOLOMON ENCODING OVERVIEW                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│    ORIGINAL DATA                    ENCODED DATA WITH PARITY           │
│    ─────────────                    ─────────────────────────          │
│                                                                        │
│    ┌─────────────────────┐          ┌─────────────────────┬─────────┐ │
│    │ d₁ d₂ d₃ ... d_k   │   ──►    │ d₁ d₂ d₃ ... d_k   │ p₁...pₙ │ │
│    └─────────────────────┘          └─────────────────────┴─────────┘ │
│           k symbols                      k data + n parity symbols     │
│                                                                        │
│    Properties:                                                         │
│    • Can detect up to 2t errors                                       │
│    • Can correct up to t errors                                       │
│    • Where n = 2t parity symbols                                       │
│                                                                        │
│    VibeDNA Default: n = 16 parity symbols → t = 8 correctable errors  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**Key concepts:**
1. **Systematic encoding**: Data remains unchanged; parity is appended
2. **Polynomial representation**: Data treated as coefficients of a polynomial
3. **Generator polynomial**: Defines the encoding/decoding algorithm
4. **Syndromes**: Values computed during decoding to detect/locate errors

### 2.2 Finite Fields (Galois Fields)

Reed-Solomon codes operate over finite fields, also called Galois Fields (GF).

```
┌──────────────────────────────────────────────────────────────────────┐
│                        GALOIS FIELD BASICS                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  A Galois Field GF(p^m) contains exactly p^m elements where:         │
│                                                                       │
│    • p = prime number (characteristic)                                │
│    • m = extension degree                                             │
│    • All arithmetic is closed within the field                        │
│                                                                       │
│  Common fields in error correction:                                   │
│                                                                       │
│    GF(2)     = {0, 1}                 → Binary                       │
│    GF(2^8)   = {0, 1, ..., 255}       → Traditional RS (bytes)       │
│    GF(4)     = {0, 1, α, α+1}         → DNA (4 nucleotides)          │
│                                                                       │
│  Why GF(4) for DNA?                                                  │
│  ─────────────────                                                    │
│  DNA has exactly 4 bases: A, T, C, G                                 │
│  GF(4) has exactly 4 elements                                        │
│  Perfect match! Each nucleotide = one GF(4) element                  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.3 GF(4) for DNA (4 Nucleotides)

VibeDNA uses GF(4) = GF(2^2), the Galois Field with 4 elements:

```
┌───────────────────────────────────────────────────────────────────────┐
│                        GF(4) ↔ DNA MAPPING                            │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│        GF(4) Element    │  Symbol  │  Nucleotide  │  Binary          │
│        ──────────────────┼──────────┼──────────────┼──────────        │
│             0           │    0     │      A       │   00             │
│             1           │    1     │      T       │   01             │
│             α           │    2     │      C       │   10             │
│           α + 1         │    3     │      G       │   11             │
│                                                                       │
│   Where α is a root of the primitive polynomial: x² + x + 1 = 0      │
│   (α² = α + 1, or equivalently, α² + α + 1 = 0)                      │
│                                                                       │
│   Visualization:                                                      │
│                                                                       │
│          A (0) ─────────── T (1)                                     │
│            │                 │                                        │
│            │    GF(4)        │                                        │
│            │   Elements      │                                        │
│            │                 │                                        │
│          C (α) ─────────── G (α+1)                                   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. VibeDNA's Implementation

### 3.1 Block Structure (1024 Nucleotides)

VibeDNA processes data in fixed-size blocks for efficient error correction:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           DNA BLOCK STRUCTURE                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   One Block = 512 bytes binary data = 1024 nucleotides (base encoding)    │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                        BLOCK HEADER (16 nt)                       │    │
│   ├────────────────────────────┬─────────────────────────────────────┤    │
│   │   Block Index (8 nt)       │   Block Checksum (8 nt)             │    │
│   │   Supports up to 65,535    │   Fast integrity check              │    │
│   │   blocks per file          │                                     │    │
│   └────────────────────────────┴─────────────────────────────────────┘    │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                      DATA NUCLEOTIDES                             │    │
│   │                                                                   │    │
│   │    ┌──────────────────────────────────────────────────────────┐  │    │
│   │    │ ATCGATCG GCTAGCTA ATCGATCG GCTAGCTA ... (1024 nt data)  │  │    │
│   │    └──────────────────────────────────────────────────────────┘  │    │
│   │                                                                   │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                    RS PARITY (16 nt default)                      │    │
│   │                                                                   │    │
│   │    ┌──────────────────────────────────────────────────────────┐  │    │
│   │    │ p₁ p₂ p₃ p₄ p₅ p₆ p₇ p₈ p₉ p₁₀ p₁₁ p₁₂ p₁₃ p₁₄ p₁₅ p₁₆│  │    │
│   │    └──────────────────────────────────────────────────────────┘  │    │
│   │                                                                   │    │
│   │    Correction capacity: nsym/2 = 8 errors                        │    │
│   │    Detection capacity: nsym = 16 errors                          │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│   Total block size: 16 + 1024 + 16 = 1056 nucleotides                     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Parity Symbols (Default: 16)

The number of parity symbols determines the error correction capability:

| Parity Symbols (nsym) | Errors Detected | Errors Corrected | Overhead |
|-----------------------|-----------------|------------------|----------|
| 8                     | 8               | 4                | ~0.8%    |
| **16 (default)**      | **16**          | **8**            | **~1.5%** |
| 32                    | 32              | 16               | ~3.1%    |
| 64                    | 64              | 32               | ~6.3%    |

### 3.3 Error Correction Capacity

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ERROR CORRECTION CAPACITY                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   With 16 parity nucleotides per block:                                │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │   Detection: d = nsym = 16 errors                              │  │
│   │                                                                 │  │
│   │   Correction: t = nsym / 2 = 8 errors                          │  │
│   │                                                                 │  │
│   │   ┌───────┬───────┬───────┬───────┬───────┬───────┬───────┐    │  │
│   │   │ 1     │ 2     │ 3     │ 4     │ 5     │ 6     │ 7     │    │  │
│   │   │error  │errors │errors │errors │errors │errors │errors │    │  │
│   │   │  ✓    │  ✓    │  ✓    │  ✓    │  ✓    │  ✓    │  ✓    │    │  │
│   │   └───────┴───────┴───────┴───────┴───────┴───────┴───────┘    │  │
│   │                                                                 │  │
│   │   ┌───────┬───────┬───────┬───────┬───────┬───────┬───────┐    │  │
│   │   │ 8     │ 9     │ 10    │ 11    │ 12    │ 13-16 │ >16   │    │  │
│   │   │errors │errors │errors │errors │errors │errors │errors │    │  │
│   │   │  ✓    │detect │detect │detect │detect │detect │ ✗     │    │  │
│   │   │       │ only  │ only  │ only  │ only  │ only  │       │    │  │
│   │   └───────┴───────┴───────┴───────┴───────┴───────┴───────┘    │  │
│   │                                                                 │  │
│   │   ✓ = Fully corrected    detect only = Flagged, not fixed      │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. GF(4) Mathematics

### 4.1 Field Elements: {A, T, C, G} = {0, 1, alpha, alpha+1}

GF(4) is constructed using the primitive polynomial p(x) = x^2 + x + 1:

```python
# VibeDNA GF(4) Element Mapping
# From vibedna/error_correction/reed_solomon_dna.py

NUCLEOTIDE_VALUE = {
    "A": 0,      # Zero element
    "T": 1,      # Unity element
    "C": 2,      # α (primitive element)
    "G": 3,      # α + 1
}

VALUE_NUCLEOTIDE = {
    0: "A",
    1: "T",
    2: "C",
    3: "G",
}
```

### 4.2 Addition Table

Addition in GF(4) is equivalent to XOR operation on the binary representations:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GF(4) ADDITION TABLE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   In GF(2^2), addition is component-wise XOR                           │
│                                                                         │
│         +   │   A(0)    T(1)    C(α)    G(α+1)                          │
│        ─────┼────────────────────────────────────                       │
│        A(0) │   A       T       C       G                               │
│        T(1) │   T       A       G       C                               │
│        C(α) │   C       G       A       T                               │
│      G(α+1) │   G       C       T       A                               │
│                                                                         │
│   Example calculations:                                                 │
│   • T + C = 1 + α = 01 XOR 10 = 11 = α+1 = G                           │
│   • G + G = (α+1) + (α+1) = 0 = A  (self-inverse)                      │
│   • C + T = α + 1 = G                                                  │
│                                                                         │
│   Note: Subtraction equals addition in GF(4): a - b = a + b            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Numeric representation (from code):**

```python
# GF4.ADD_TABLE from reed_solomon_dna.py
ADD_TABLE = [
    [0, 1, 2, 3],  # A + {A,T,C,G} = {A,T,C,G}
    [1, 0, 3, 2],  # T + {A,T,C,G} = {T,A,G,C}
    [2, 3, 0, 1],  # C + {A,T,C,G} = {C,G,A,T}
    [3, 2, 1, 0],  # G + {A,T,C,G} = {G,C,T,A}
]
```

### 4.3 Multiplication Table

Multiplication uses the primitive polynomial x^2 + x + 1 for reduction:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      GF(4) MULTIPLICATION TABLE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Using primitive polynomial: α² = α + 1                               │
│                                                                         │
│         ×   │   A(0)    T(1)    C(α)    G(α+1)                          │
│        ─────┼────────────────────────────────────                       │
│        A(0) │   A       A       A       A                               │
│        T(1) │   A       T       C       G                               │
│        C(α) │   A       C       G       T                               │
│      G(α+1) │   A       G       T       C                               │
│                                                                         │
│   Example calculations:                                                 │
│   • C × C = α × α = α² = α + 1 = G                                     │
│   • C × G = α × (α+1) = α² + α = (α+1) + α = 1 = T                     │
│   • G × G = (α+1) × (α+1) = α² + 2α + 1 = α² + 1 = α = C              │
│     (Remember: 2 = 0 in GF(2), so 2α = 0)                              │
│                                                                         │
│   Multiplicative inverses:                                              │
│   • inv(T) = T    (1 × 1 = 1)                                          │
│   • inv(C) = G    (α × (α+1) = 1)                                      │
│   • inv(G) = C    ((α+1) × α = 1)                                      │
│   • inv(A) = undefined (0 has no inverse)                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Numeric representation (from code):**

```python
# GF4.MUL_TABLE from reed_solomon_dna.py
MUL_TABLE = [
    [0, 0, 0, 0],  # A × {A,T,C,G} = {A,A,A,A}
    [0, 1, 2, 3],  # T × {A,T,C,G} = {A,T,C,G}
    [0, 2, 3, 1],  # C × {A,T,C,G} = {A,C,G,T}
    [0, 3, 1, 2],  # G × {A,T,C,G} = {A,G,T,C}
]

# Multiplicative inverse table
INV_TABLE = [0, 1, 3, 2]  # inv(A)=undefined, inv(T)=T, inv(C)=G, inv(G)=C
```

### 4.4 Code Examples

```python
from vibedna.error_correction.reed_solomon_dna import GF4

# Addition examples
result = GF4.add(1, 2)  # T + C
print(f"T + C = {result}")  # Output: 3 (G)

result = GF4.add(3, 3)  # G + G
print(f"G + G = {result}")  # Output: 0 (A)

# Multiplication examples
result = GF4.mul(2, 2)  # C × C
print(f"C × C = {result}")  # Output: 3 (G)

result = GF4.mul(2, 3)  # C × G
print(f"C × G = {result}")  # Output: 1 (T)

# Division example
result = GF4.div(3, 2)  # G / C
print(f"G / C = {result}")  # Output: 1 (T)

# Power example
result = GF4.pow(2, 3)  # C³ = α³
print(f"C³ = {result}")  # Output: 2 (C), since α³ = α (period 3)

# Polynomial evaluation
coeffs = [1, 2, 3]  # Represents 1 + 2x + 3x²
result = GF4.eval_poly(coeffs, 2)  # Evaluate at x = C
print(f"P(C) = {result}")
```

---

## 5. Encoding Process

### 5.1 Adding Parity to Data Blocks

The Reed-Solomon encoding process adds parity symbols to the end of each data block:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REED-SOLOMON ENCODING PROCESS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Step 1: Represent data as polynomial                                      │
│   ─────────────────────────────────────                                     │
│   Data: ATCG → [0, 1, 2, 3] → d(x) = 0 + 1x + 2x² + 3x³                    │
│                                                                             │
│   Step 2: Multiply by x^nsym                                                │
│   ─────────────────────────────                                             │
│   Shift data to make room for parity: d(x) · x^16                          │
│                                                                             │
│   Step 3: Compute generator polynomial                                      │
│   ─────────────────────────────────────                                     │
│   g(x) = (x - α⁰)(x - α¹)(x - α²)...(x - α^(nsym-1))                       │
│                                                                             │
│   Step 4: Calculate remainder                                               │
│   ─────────────────────────────                                             │
│   parity(x) = [d(x) · x^nsym] mod g(x)                                     │
│                                                                             │
│   Step 5: Form codeword                                                     │
│   ─────────────────────────                                                 │
│   c(x) = d(x) · x^nsym + parity(x)                                         │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │  INPUT:   │ A  T  C  G  ...  (data nucleotides)  │                │    │
│   │           └──────────────────────────────────────┘                │    │
│   │                          │                                        │    │
│   │                          ▼                                        │    │
│   │           ┌────────────────────────────────────┐                  │    │
│   │           │     Generator Polynomial g(x)      │                  │    │
│   │           │     Polynomial Division            │                  │    │
│   │           └────────────────────────────────────┘                  │    │
│   │                          │                                        │    │
│   │                          ▼                                        │    │
│   │  OUTPUT:  │ A  T  C  G  ... │ p₁ p₂ ... p₁₆ │                    │    │
│   │           └─────────────────┴────────────────┘                    │    │
│   │               Original Data       Parity                          │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Step-by-Step Example

Let's encode a short sequence "ATCG" with 4 parity symbols:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENCODING EXAMPLE: "ATCG" with nsym=4                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUT: ATCG → [0, 1, 2, 3]                                               │
│                                                                             │
│   Step 1: Data polynomial                                                   │
│   ──────────────────────────                                                │
│   d(x) = 0 + 1x + 2x² + 3x³                                                │
│                                                                             │
│   Step 2: Shift by x^4 (nsym = 4)                                          │
│   ─────────────────────────────                                             │
│   d(x)·x⁴ = 0·x⁴ + 1·x⁵ + 2·x⁶ + 3·x⁷                                     │
│           = [0, 0, 0, 0, 0, 1, 2, 3]  (coefficients)                       │
│                                                                             │
│   Step 3: Generator polynomial for nsym=4                                   │
│   ─────────────────────────────────────────                                 │
│   g(x) = (x-1)(x-α)(x-α²)(x-α³)                                            │
│        = (x-1)(x-2)(x-3)(x-1)   [using our mapping]                        │
│        = x⁴ + ...               [after expansion]                          │
│                                                                             │
│   Step 4: Polynomial division                                               │
│   ─────────────────────────────                                             │
│                    ┌────────────────────────────┐                           │
│   [0,0,0,0,0,1,2,3]│ ÷ generator polynomial g(x)│                           │
│                    └────────────────────────────┘                           │
│                              │                                              │
│                              ▼                                              │
│   Remainder = [r₀, r₁, r₂, r₃] → parity nucleotides                        │
│                                                                             │
│   Step 5: Final codeword                                                    │
│   ──────────────────────                                                    │
│   codeword = [0, 1, 2, 3, r₀, r₁, r₂, r₃]                                  │
│            = ATCG + [parity as nucleotides]                                 │
│                                                                             │
│   OUTPUT: ATCGXXXX  (where X's are computed parity)                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Python implementation:**

```python
from vibedna.error_correction import DNAReedSolomon

# Create encoder with 16 parity symbols (default)
rs = DNAReedSolomon(nsym=16)

# Encode a DNA sequence
original = "ATCGATCGATCGATCG"  # 16 nucleotides
encoded = rs.encode(original)

print(f"Original: {original} ({len(original)} nt)")
print(f"Encoded:  {encoded} ({len(encoded)} nt)")
print(f"Parity:   {encoded[len(original):]} ({len(encoded) - len(original)} nt)")

# Output:
# Original: ATCGATCGATCGATCG (16 nt)
# Encoded:  ATCGATCGATCGATCGXXXXXXXXXXXX (32 nt)
# Parity:   XXXXXXXXXXXX (16 nt)
```

---

## 6. Decoding and Error Detection

### 6.1 Syndrome Calculation

Syndromes are the first step in detecting whether errors are present:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SYNDROME CALCULATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Received sequence r(x) = c(x) + e(x)                                     │
│   where c(x) is codeword, e(x) is error polynomial                         │
│                                                                             │
│   Syndrome S_i = r(α^i) for i = 0, 1, ..., nsym-1                          │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  If all S_i = 0:  NO ERRORS DETECTED                            │      │
│   │  If any S_i ≠ 0:  ERRORS PRESENT                                │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   Example:                                                                  │
│   ─────────                                                                 │
│   Received: ATGGATCGATCGATCGPPPPPPPPPPPPPPPP  (G instead of C at pos 2)    │
│                 ↑                                                           │
│             error here                                                      │
│                                                                             │
│   S₀ = r(α⁰) = r(1) = sum of all received values                           │
│   S₁ = r(α¹) = r(α) = weighted sum                                         │
│   S₂ = r(α²) = ...                                                         │
│   ...                                                                       │
│   S₁₅ = r(α¹⁵)                                                             │
│                                                                             │
│   Non-zero syndromes indicate error presence and help locate errors        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Error Location (Berlekamp-Massey Algorithm)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ERROR LOCATOR POLYNOMIAL                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   The Berlekamp-Massey algorithm finds the error locator polynomial:       │
│                                                                             │
│   Λ(x) = 1 + Λ₁x + Λ₂x² + ... + Λ_t x^t                                   │
│                                                                             │
│   where t = number of errors                                               │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    BERLEKAMP-MASSEY ITERATION                       │  │
│   ├─────────────────────────────────────────────────────────────────────┤  │
│   │                                                                     │  │
│   │   Initialize: C(x) = 1, B(x) = 1, L = 0, m = 1, b = 1              │  │
│   │                                                                     │  │
│   │   For r = 0 to nsym-1:                                             │  │
│   │       1. Compute discrepancy d                                     │  │
│   │       2. If d = 0: m = m + 1                                       │  │
│   │       3. Else if 2L <= r:                                          │  │
│   │          - T = C                                                   │  │
│   │          - C = C - (d/b) · x^m · B                                 │  │
│   │          - L = r + 1 - L                                           │  │
│   │          - B = T, b = d, m = 1                                     │  │
│   │       4. Else:                                                     │  │
│   │          - C = C - (d/b) · x^m · B                                 │  │
│   │          - m = m + 1                                               │  │
│   │                                                                     │  │
│   │   Result: Error locator polynomial Λ(x) = C(x)                     │  │
│   │           Number of errors = degree of Λ(x)                        │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Chien Search (Finding Error Positions)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CHIEN SEARCH                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Once we have Λ(x), find its roots to locate errors:                      │
│                                                                             │
│   For each position i in the received sequence:                            │
│       Evaluate Λ(α^(-i))                                                   │
│       If Λ(α^(-i)) = 0, position i has an error                           │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │              SEARCHING FOR ERROR POSITIONS                          │  │
│   ├─────────────────────────────────────────────────────────────────────┤  │
│   │                                                                     │  │
│   │   Position:  0   1   2   3   4   5   6   7   8   9  ...            │  │
│   │   Sequence:  A   T   G   G   A   T   C   G   A   T  ...            │  │
│   │                   ↑                                                 │  │
│   │                 error                                               │  │
│   │                                                                     │  │
│   │   Λ(α⁰)  = ?  → not zero → no error at position 0                  │  │
│   │   Λ(α⁻¹) = ?  → not zero → no error at position 1                  │  │
│   │   Λ(α⁻²) = 0  → ZERO!    → ERROR at position 2                     │  │
│   │   Λ(α⁻³) = ?  → not zero → no error at position 3                  │  │
│   │   ...                                                               │  │
│   │                                                                     │  │
│   │   Found errors at positions: [2]                                   │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.4 Error Correction (Forney Algorithm)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FORNEY ALGORITHM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   After finding error positions, compute error magnitudes:                  │
│                                                                             │
│   1. Compute error evaluator polynomial:                                   │
│      Ω(x) = S(x) · Λ(x) mod x^nsym                                         │
│                                                                             │
│   2. Compute formal derivative of error locator:                           │
│      Λ'(x) = derivative of Λ(x)                                            │
│                                                                             │
│   3. For each error position j with X_j = α^(-position):                   │
│      Error magnitude e_j = -X_j · Ω(X_j^(-1)) / Λ'(X_j^(-1))              │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                   ERROR CORRECTION EXAMPLE                          │  │
│   ├─────────────────────────────────────────────────────────────────────┤  │
│   │                                                                     │  │
│   │   Received:    A  T  G  G  A  T  C  G  ...                         │  │
│   │   Position:    0  1  2  3  4  5  6  7                              │  │
│   │                      ↑                                              │  │
│   │                  error at 2                                         │  │
│   │                                                                     │  │
│   │   Error position:  j = 2                                           │  │
│   │   Error magnitude: e_j = computed value (say, 1)                   │  │
│   │                                                                     │  │
│   │   Correction: received[2] = received[2] - e_j                      │  │
│   │               G - 1 = 3 - 1 = 2 = C                                │  │
│   │                                                                     │  │
│   │   Corrected:   A  T  C  G  A  T  C  G  ...                         │  │
│   │                      ↑                                              │  │
│   │                  fixed!                                             │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.5 Complete Decoding Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     COMPLETE DECODING WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐                                                      │
│   │ Received Sequence│                                                      │
│   └────────┬─────────┘                                                      │
│            │                                                                │
│            ▼                                                                │
│   ┌──────────────────┐                                                      │
│   │ Compute Syndromes│──────────────┐                                       │
│   │ S₀, S₁, ..., S₁₅ │              │                                       │
│   └────────┬─────────┘              │                                       │
│            │                        │                                       │
│            ▼                        ▼                                       │
│   ┌──────────────────┐     ┌────────────────┐                              │
│   │ All Sᵢ = 0 ?     │─Yes→│ Return: No     │                              │
│   │                  │     │ errors detected│                              │
│   └────────┬─────────┘     └────────────────┘                              │
│            │ No                                                             │
│            ▼                                                                │
│   ┌──────────────────┐                                                      │
│   │ Berlekamp-Massey │                                                      │
│   │ Find Λ(x)        │                                                      │
│   └────────┬─────────┘                                                      │
│            │                                                                │
│            ▼                                                                │
│   ┌──────────────────┐                                                      │
│   │ Chien Search     │                                                      │
│   │ Find positions   │                                                      │
│   └────────┬─────────┘                                                      │
│            │                                                                │
│            ▼                                                                │
│   ┌──────────────────┐     ┌────────────────────┐                          │
│   │ errors > t ?     │─Yes→│ Return: Uncorrect- │                          │
│   │ (too many)       │     │ able, # detected   │                          │
│   └────────┬─────────┘     └────────────────────┘                          │
│            │ No                                                             │
│            ▼                                                                │
│   ┌──────────────────┐                                                      │
│   │ Forney Algorithm │                                                      │
│   │ Find magnitudes  │                                                      │
│   └────────┬─────────┘                                                      │
│            │                                                                │
│            ▼                                                                │
│   ┌──────────────────┐                                                      │
│   │ Apply Corrections│                                                      │
│   │ r[pos] -= mag    │                                                      │
│   └────────┬─────────┘                                                      │
│            │                                                                │
│            ▼                                                                │
│   ┌──────────────────┐                                                      │
│   │ Return: Corrected│                                                      │
│   │ sequence + report│                                                      │
│   └──────────────────┘                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Configuration Options

### 7.1 Adjusting Parity Symbols

```python
from vibedna.error_correction import DNAReedSolomon

# Low redundancy (faster, less protection)
rs_low = DNAReedSolomon(nsym=8)    # Corrects 4 errors

# Default (balanced)
rs_default = DNAReedSolomon(nsym=16)  # Corrects 8 errors

# High redundancy (slower, more protection)
rs_high = DNAReedSolomon(nsym=32)   # Corrects 16 errors

# Maximum protection
rs_max = DNAReedSolomon(nsym=64)    # Corrects 32 errors
```

### 7.2 Trade-offs: Redundancy vs Capacity

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     REDUNDANCY VS CAPACITY TRADE-OFFS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   nsym     │ Correction │ Detection │ Overhead │ Best For                   │
│   ─────────┼────────────┼───────────┼──────────┼─────────────────────────── │
│     8      │    4       │    8      │   0.8%   │ Fresh synthesis, fast      │
│    16      │    8       │   16      │   1.6%   │ General storage (default)  │
│    32      │   16       │   32      │   3.1%   │ Long-term archival         │
│    64      │   32       │   64      │   6.3%   │ Harsh conditions           │
│   128      │   64       │  128      │  12.5%   │ Critical data, decades     │
│                                                                             │
│                                                                             │
│   Visualization of overhead:                                                │
│                                                                             │
│   ┌────────────────────────────────────────────────────────┬──┐            │
│   │████████████████████████████████████████████████████████│  │ nsym=8    │
│   │                         Data                           │P │ 99.2% eff │
│   └────────────────────────────────────────────────────────┴──┘            │
│                                                                             │
│   ┌────────────────────────────────────────────────────────┬────┐          │
│   │██████████████████████████████████████████████████████  │    │ nsym=16  │
│   │                         Data                           │ P  │ 98.4% eff│
│   └────────────────────────────────────────────────────────┴────┘          │
│                                                                             │
│   ┌──────────────────────────────────────────────────────┬────────┐        │
│   │████████████████████████████████████████████████████  │        │ nsym=32│
│   │                         Data                         │ Parity │ 96.9%  │
│   └──────────────────────────────────────────────────────┴────────┘        │
│                                                                             │
│   ┌────────────────────────────────────────────────────┬────────────┐      │
│   │██████████████████████████████████████████████████  │            │nsym=64│
│   │                         Data                       │   Parity   │93.7% │
│   └────────────────────────────────────────────────────┴────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Choosing the Right Configuration

| Use Case | Recommended nsym | Reasoning |
|----------|-----------------|-----------|
| Real-time applications | 8 | Minimal overhead |
| Standard storage | 16 (default) | Good balance |
| 5-10 year archival | 32 | Extra margin for degradation |
| 50+ year archival | 64-128 | Maximum protection |
| Harsh environments | 64+ | Higher error rates expected |
| Redundant copies | 8-16 | Errors can be cross-checked |

---

## 8. Using Error Correction in VibeDNA

### 8.1 API Usage Examples

#### Basic Encoding and Decoding

```python
from vibedna.error_correction import DNAReedSolomon, CorrectionResult

# Initialize the codec
rs = DNAReedSolomon(nsym=16)

# Encode a sequence (adds parity)
original = "ATCGATCGATCGATCGATCGATCGATCGATCG"
protected = rs.encode(original)

print(f"Original length: {len(original)} nt")
print(f"Protected length: {len(protected)} nt")
print(f"Parity added: {len(protected) - len(original)} nt")

# Simulate errors (corrupt 3 positions)
corrupted = list(protected)
corrupted[5] = 'G'   # Change position 5
corrupted[10] = 'A'  # Change position 10
corrupted[20] = 'T'  # Change position 20
corrupted = ''.join(corrupted)

# Decode and correct
result: CorrectionResult = rs.decode(corrupted)

print(f"\nCorrection Results:")
print(f"  Errors detected: {result.errors_detected}")
print(f"  Errors corrected: {result.errors_corrected}")
print(f"  Error positions: {result.error_positions}")
print(f"  Uncorrectable: {result.uncorrectable}")
print(f"  Confidence: {result.confidence:.2%}")
print(f"  Corrected sequence matches original: {result.corrected_sequence == original}")
```

#### Using the Mutation Detector

```python
from vibedna.error_correction import MutationDetector, MutationType

# Initialize detector
detector = MutationDetector(context_size=3)

# Compare two sequences
reference = "ATCGATCGATCGATCG"
mutated   = "ATGGATCAATCGATCG"

report = detector.compare(reference, mutated)

print(f"Total mutations: {report.mutation_count}")
print(f"Mutation rate: {report.mutation_rate:.2%}")
print(f"Transitions: {report.transition_count}")
print(f"Transversions: {report.transversion_count}")
print(f"Likely corrupted: {report.is_likely_corrupted}")

for m in report.mutations:
    print(f"  Position {m.position}: {m.original} -> {m.mutated} ({m.mutation_type.value})")
```

#### Using Checksums for Integrity

```python
from vibedna.error_correction import ChecksumGenerator
from vibedna.error_correction.checksum_generator import ChecksumAlgorithm

# CRC-8 checksum (default, fast)
gen = ChecksumGenerator(ChecksumAlgorithm.CRC8)
sequence = "ATCGATCGATCGATCG"
checksum = gen.compute(sequence)
print(f"CRC-8 checksum: {checksum}")

# Verify integrity
is_valid = gen.verify(sequence, checksum)
print(f"Valid: {is_valid}")

# Append checksum to sequence
protected = gen.compute_and_append(sequence)
print(f"Protected: {protected}")

# Verify and strip checksum
is_valid, data = gen.verify_and_strip(protected)
print(f"Recovered: {data}, Valid: {is_valid}")
```

### 8.2 CLI Options

The VibeDNA command-line interface provides error correction options:

```bash
# Encode with error correction (default: enabled)
vibedna encode myfile.pdf

# Encode without error correction (smaller output)
vibedna encode myfile.pdf --no-error-correction

# Decode with automatic error correction
vibedna decode myfile.dna

# Check sequence info (shows error correction status)
vibedna info myfile.dna

# Validate sequence integrity
vibedna validate "ATCGATCG..."
```

#### CLI Examples

```bash
# Encode a file with error correction
$ vibedna encode document.pdf -o document.dna
╔═══════════════════════════════════════════════════════════════╗
║     VibeDNA - Binary ↔ DNA Encoding System                    ║
╚═══════════════════════════════════════════════════════════════╝

✓ Encoded successfully!

Input:  document.pdf (1,234,567 bytes)
Output: document.dna (2,593,591 nucleotides)
Scheme: quaternary
Format: fasta
Ratio:  2.10x

# Decode with error correction
$ vibedna decode document.dna
╔═══════════════════════════════════════════════════════════════╗
║     VibeDNA - Binary ↔ DNA Encoding System                    ║
╚═══════════════════════════════════════════════════════════════╝

✓ Decoded successfully!

Input:    document.dna (2,593,591 nucleotides)
Output:   document.pdf (1,234,567 bytes)
Errors:   3 detected, 3 corrected
Valid:    Yes
```

### 8.3 Agent Integration

VibeDNA's agent system includes a dedicated Error Correction Agent:

```python
from vibedna.agents.specialist import ErrorCorrectionAgent
from vibedna.agents.base.message import TaskRequest
import asyncio

async def main():
    # Initialize the agent
    agent = ErrorCorrectionAgent()

    # Request: Apply error correction
    encode_request = TaskRequest(
        request_id="encode-001",
        task_type="error_correction",
        parameters={
            "action": "encode",
            "sequence": "ATCGATCGATCGATCGATCGATCGATCGATCG"
        }
    )

    result = await agent.handle_task(encode_request)
    print(f"Protected sequence: {result.data['sequence']}")
    print(f"Correction capacity: {result.data['correction_capacity']} errors")

    # Request: Decode with correction
    decode_request = TaskRequest(
        request_id="decode-001",
        task_type="error_correction",
        parameters={
            "action": "decode",
            "sequence": result.data['sequence']  # Use protected sequence
        }
    )

    decode_result = await agent.handle_task(decode_request)
    print(f"Decoded: {decode_result.data['sequence']}")
    print(f"Errors corrected: {decode_result.data['errors_corrected']}")

asyncio.run(main())
```

#### Agent Workflow Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AGENT ORCHESTRATION WITH ERROR CORRECTION                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐                                                      │
│   │ Master           │                                                      │
│   │ Orchestrator     │                                                      │
│   └────────┬─────────┘                                                      │
│            │                                                                │
│            ▼                                                                │
│   ┌──────────────────┐                                                      │
│   │ Workflow         │ Manages encoding/decoding pipelines                  │
│   │ Orchestrator     │                                                      │
│   └────────┬─────────┘                                                      │
│            │                                                                │
│            ├────────────────────┐                                           │
│            │                    │                                           │
│            ▼                    ▼                                           │
│   ┌──────────────────┐ ┌──────────────────┐                                │
│   │ Encoder Agent    │ │ Error Correction │                                │
│   │                  │ │ Agent            │                                │
│   │ Converts binary  │ │                  │                                │
│   │ to DNA sequence  │ │ Applies RS codes │                                │
│   └──────────────────┘ │ Detects errors   │                                │
│                        │ Corrects errors  │                                │
│                        └──────────────────┘                                │
│                                                                             │
│   Agent Communication:                                                      │
│   • Encoder → ErrorCorrection: "Add parity to encoded data"                │
│   • ErrorCorrection → Encoder: "Protected sequence ready"                  │
│   • Decoder → ErrorCorrection: "Verify and correct this sequence"          │
│   • ErrorCorrection → Decoder: "Corrected sequence + error report"         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.4 Full Integration Example

```python
"""
Complete example: Encode a file with error correction,
simulate degradation, and recover the data.
"""

from vibedna.core.encoder import DNAEncoder, EncodingConfig, EncodingScheme
from vibedna.core.decoder import DNADecoder
from vibedna.error_correction import DNAReedSolomon
import random

# Configuration
config = EncodingConfig(
    scheme=EncodingScheme.QUATERNARY,
    error_correction=True,  # Enable RS codes
)

# Encode a message
encoder = DNAEncoder(config)
original_data = b"VibeDNA: Where Digital Meets Biological!"

dna_sequence = encoder.encode(
    original_data,
    filename="message.txt",
    mime_type="text/plain"
)

print(f"Original message: {original_data.decode()}")
print(f"DNA length: {len(dna_sequence)} nucleotides")

# Simulate degradation (0.5% error rate)
degraded = list(dna_sequence)
nucleotides = ['A', 'T', 'C', 'G']
error_count = 0

for i in range(len(degraded)):
    if random.random() < 0.005:  # 0.5% chance
        original = degraded[i]
        # Mutate to different nucleotide
        degraded[i] = random.choice([n for n in nucleotides if n != original])
        error_count += 1

degraded_sequence = ''.join(degraded)
print(f"\nSimulated {error_count} errors ({error_count/len(dna_sequence)*100:.2f}%)")

# Decode with error correction
decoder = DNADecoder()
result = decoder.decode(degraded_sequence)

print(f"\nDecoding results:")
print(f"  Errors detected: {result.errors_detected}")
print(f"  Errors corrected: {result.errors_corrected}")
print(f"  Integrity valid: {result.integrity_valid}")
print(f"  Recovered message: {result.data.decode()}")
print(f"  Perfect recovery: {result.data == original_data}")
```

---

## Summary

VibeDNA's error correction system provides robust protection for DNA-encoded data:

| Feature | Implementation | Benefit |
|---------|---------------|---------|
| Reed-Solomon in GF(4) | Native DNA arithmetic | Efficient correction |
| 16 parity symbols (default) | 8 error correction | Handles typical degradation |
| Block-based encoding | 1024 nt per block | Localized error handling |
| Syndrome-based detection | O(n) complexity | Fast error detection |
| Berlekamp-Massey | Optimal locator finding | Proven algorithm |
| Forney correction | Algebraic solution | Exact error values |
| Configurable redundancy | 8-128 parity symbols | Flexible protection |
| Agent integration | ErrorCorrectionAgent | Automated workflows |

For most applications, the default configuration (16 parity symbols) provides an excellent balance between storage efficiency and error protection, capable of correcting up to 8 nucleotide errors per block while detecting up to 16.

---

## References

- Reed, I. S., & Solomon, G. (1960). "Polynomial Codes Over Certain Finite Fields"
- Berlekamp, E. R. (1968). "Algebraic Coding Theory"
- Massey, J. L. (1969). "Shift-register synthesis and BCH decoding"
- Forney, G. D. (1965). "On decoding BCH codes"
- Church, G. M., et al. (2012). "Next-Generation Digital Information Storage in DNA"
- Erlich, Y., & Zielinski, D. (2017). "DNA Fountain enables a robust and efficient storage architecture"

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
