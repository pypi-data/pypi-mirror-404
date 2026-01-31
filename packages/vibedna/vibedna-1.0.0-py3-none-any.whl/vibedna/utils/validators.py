"""
VibeDNA Validators

Input validation utilities for DNA sequences and binary data.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Tuple, List, Optional
import re

from vibedna.utils.constants import (
    NUCLEOTIDES,
    MAGIC_SEQUENCE,
    END_MARKER,
    HEADER_SIZE,
    FOOTER_SIZE,
)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def is_valid_nucleotide(char: str) -> bool:
    """
    Check if a character is a valid nucleotide.

    Args:
        char: Single character to validate

    Returns:
        True if valid nucleotide (A, T, C, G), False otherwise
    """
    return char.upper() in NUCLEOTIDES


def validate_dna_sequence(
    sequence: str,
    require_header: bool = False,
    require_footer: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validate a DNA sequence for format and content.

    Args:
        sequence: DNA sequence to validate
        require_header: If True, validates VibeDNA header presence
        require_footer: If True, validates VibeDNA footer presence

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues: List[str] = []

    if not sequence:
        issues.append("Sequence is empty")
        return False, issues

    # Normalize to uppercase
    sequence = sequence.upper()

    # Check for valid characters
    invalid_chars = set()
    for i, char in enumerate(sequence):
        if char not in NUCLEOTIDES:
            invalid_chars.add(f"'{char}' at position {i}")

    if invalid_chars:
        issues.append(f"Invalid characters found: {', '.join(list(invalid_chars)[:10])}")
        if len(invalid_chars) > 10:
            issues.append(f"... and {len(invalid_chars) - 10} more invalid characters")

    # Check minimum length
    min_length = 4  # At least 1 byte encoded
    if require_header:
        min_length += HEADER_SIZE
    if require_footer:
        min_length += FOOTER_SIZE

    if len(sequence) < min_length:
        issues.append(f"Sequence too short: {len(sequence)} < {min_length} nucleotides")

    # Validate header if required
    if require_header:
        if not sequence.startswith(MAGIC_SEQUENCE):
            issues.append(f"Missing or invalid magic sequence (expected '{MAGIC_SEQUENCE}')")

    # Validate footer if required
    if require_footer:
        footer_start = len(sequence) - FOOTER_SIZE
        if footer_start >= 0:
            footer = sequence[footer_start:]
            if not footer.startswith(END_MARKER):
                issues.append(f"Missing or invalid end marker (expected '{END_MARKER}')")

    return len(issues) == 0, issues


def validate_binary_string(binary: str) -> Tuple[bool, List[str]]:
    """
    Validate a binary string representation.

    Args:
        binary: String containing only '0' and '1' characters

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues: List[str] = []

    if not binary:
        issues.append("Binary string is empty")
        return False, issues

    # Check for valid characters
    invalid_pattern = re.compile(r"[^01]")
    matches = invalid_pattern.findall(binary)
    if matches:
        unique_invalid = set(matches)
        issues.append(f"Invalid characters in binary string: {unique_invalid}")

    # Check for byte alignment
    if len(binary) % 8 != 0:
        issues.append(f"Binary string length ({len(binary)}) is not byte-aligned (not divisible by 8)")

    return len(issues) == 0, issues


def validate_encoding_scheme(scheme: str) -> bool:
    """
    Validate that an encoding scheme name is valid.

    Args:
        scheme: Encoding scheme name

    Returns:
        True if valid scheme name
    """
    valid_schemes = {"quaternary", "balanced_gc", "rll", "triplet"}
    return scheme.lower() in valid_schemes


def validate_gc_content(sequence: str, min_ratio: float = 0.3, max_ratio: float = 0.7) -> bool:
    """
    Validate that a DNA sequence has acceptable GC content.

    Args:
        sequence: DNA sequence to check
        min_ratio: Minimum acceptable GC ratio
        max_ratio: Maximum acceptable GC ratio

    Returns:
        True if GC content is within acceptable range
    """
    if not sequence:
        return False

    sequence = sequence.upper()
    gc_count = sum(1 for n in sequence if n in ("G", "C"))
    gc_ratio = gc_count / len(sequence)

    return min_ratio <= gc_ratio <= max_ratio


def validate_homopolymer_runs(sequence: str, max_run: int = 3) -> Tuple[bool, List[int]]:
    """
    Check for homopolymer runs exceeding the maximum allowed length.

    Args:
        sequence: DNA sequence to check
        max_run: Maximum allowed consecutive identical nucleotides

    Returns:
        Tuple of (is_valid, list_of_positions_where_runs_exceed_limit)
    """
    if not sequence:
        return True, []

    sequence = sequence.upper()
    violations: List[int] = []

    current_run = 1
    run_start = 0

    for i in range(1, len(sequence)):
        if sequence[i] == sequence[i - 1]:
            current_run += 1
        else:
            if current_run > max_run:
                violations.append(run_start)
            current_run = 1
            run_start = i

    # Check last run
    if current_run > max_run:
        violations.append(run_start)

    return len(violations) == 0, violations


def validate_file_path(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a DNA file system path.

    Args:
        path: File system path to validate

    Returns:
        Tuple of (is_valid, error_message_or_none)
    """
    if not path:
        return False, "Path cannot be empty"

    if not path.startswith("/"):
        return False, "Path must be absolute (start with /)"

    # Check for invalid characters
    invalid_chars = re.compile(r'[<>:"|?*\x00-\x1f]')
    if invalid_chars.search(path):
        return False, "Path contains invalid characters"

    # Check for path traversal attempts
    if ".." in path:
        return False, "Path traversal (..) is not allowed"

    # Check path component length
    components = path.split("/")
    for component in components:
        if len(component) > 255:
            return False, f"Path component too long: {component[:50]}..."

    return True, None


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
