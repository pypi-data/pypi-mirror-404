# Contributing to VibeDNA

Thank you for your interest in contributing to VibeDNA! This document provides guidelines and instructions for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Code Style](#code-style)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Submitting Changes](#submitting-changes)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. All contributors are expected to:

- Be respectful and constructive in communications
- Focus on the technical merits of contributions
- Accept constructive criticism gracefully
- Prioritize the project's best interests

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Docker (optional, for containerized development)

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/vibedna.git
cd vibedna
git remote add upstream https://github.com/neuralquantum/vibedna.git
```

---

## Development Setup

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
# Install in development mode with all extras
pip install -e ".[dev,test,docs]"
```

### Verify Installation

```bash
# Run tests to verify setup
pytest tests/

# Check code style
ruff check vibedna/
mypy vibedna/
```

---

## Making Changes

### Branch Naming

Create a feature branch from `main`:

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/modifications

### Commit Messages

Follow conventional commit format:

```
type(scope): brief description

Longer description if needed.

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Example:
```
feat(encoder): add streaming support for large files

Implement chunked encoding to handle files larger than available memory.
Uses configurable chunk size with default of 10MB.

Fixes #42
```

---

## Code Style

### Python Style Guide

We follow PEP 8 with these specifics:

- **Line length**: 100 characters maximum
- **Quotes**: Double quotes for strings
- **Imports**: Sorted with `isort`, grouped (stdlib, third-party, local)
- **Type hints**: Required for all public functions
- **Docstrings**: Google style

### Example

```python
"""Module docstring describing the module's purpose."""

from typing import List, Optional

from vibedna.core import BaseEncoder


def encode_data(
    data: bytes,
    scheme: str = "quaternary",
    block_size: int = 1024,
) -> str:
    """Encode binary data to DNA sequence.

    Args:
        data: Binary data to encode.
        scheme: Encoding scheme to use.
        block_size: Size of each encoding block.

    Returns:
        DNA sequence as a string of nucleotides.

    Raises:
        ValueError: If scheme is not recognized.

    Example:
        >>> encode_data(b"Hello")
        'TACATGTCTGCA'
    """
    # Implementation here
    pass
```

### Linting

```bash
# Check code style
ruff check vibedna/

# Auto-fix issues
ruff check --fix vibedna/

# Type checking
mypy vibedna/
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vibedna --cov-report=html

# Run specific test file
pytest tests/test_encoder.py

# Run specific test
pytest tests/test_encoder.py::test_quaternary_encoding

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in `tests/` directory
- Mirror the source structure (`vibedna/encoder/` → `tests/test_encoder/`)
- Use descriptive test names
- Include docstrings explaining what's being tested

```python
"""Tests for the quaternary encoder."""

import pytest
from vibedna.encoder import Encoder


class TestQuaternaryEncoder:
    """Tests for quaternary encoding scheme."""

    def test_encode_simple_byte(self):
        """Test encoding a single byte produces correct DNA."""
        encoder = Encoder(scheme="quaternary")
        result = encoder.encode(b"H")
        assert result == "TACA"

    def test_encode_empty_raises_error(self):
        """Test that encoding empty data raises ValueError."""
        encoder = Encoder(scheme="quaternary")
        with pytest.raises(ValueError, match="empty"):
            encoder.encode(b"")

    @pytest.mark.parametrize("data,expected", [
        (b"A", "ATCT"),
        (b"B", "ATCC"),
        (b"C", "ATCG"),
    ])
    def test_encode_parametrized(self, data, expected):
        """Test encoding various single bytes."""
        encoder = Encoder(scheme="quaternary")
        assert encoder.encode(data) == expected
```

### Test Coverage

- Aim for >90% code coverage
- All public functions must have tests
- Edge cases and error conditions must be tested

---

## Documentation

### Docstrings

All public modules, classes, functions, and methods must have docstrings:

```python
def my_function(param1: str, param2: int = 10) -> bool:
    """Brief one-line description.

    Longer description if needed, explaining the function's
    purpose and behavior in more detail.

    Args:
        param1: Description of param1.
        param2: Description of param2. Defaults to 10.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is empty.

    Example:
        >>> my_function("test", 5)
        True
    """
```

### Documentation Files

- Update relevant docs in `docs/` for feature changes
- Add new guides for significant features
- Keep README.md current

---

## Submitting Changes

### Before Submitting

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   # Linting
   ruff check vibedna/
   mypy vibedna/

   # Tests
   pytest --cov=vibedna

   # Build docs (if changed)
   cd docs && make html
   ```

3. **Update documentation** if needed

4. **Add changelog entry** for user-facing changes

### Pull Request Process

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a Pull Request on GitHub

3. Fill out the PR template:
   - Description of changes
   - Related issues
   - Testing performed
   - Documentation updates

4. Request review from maintainers

5. Address review feedback

6. Once approved, maintainers will merge

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Changelog entry added
- [ ] All CI checks pass
- [ ] No merge conflicts

---

## Questions?

- Open a GitHub Discussion for questions
- Join our community at [community.vibecaas.com](https://community.vibecaas.com)
- Email: developers@neuralquantum.ai

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
