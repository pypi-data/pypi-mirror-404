# VibeDNA PyPI Publishing Guide

**© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.**

This guide covers how to publish VibeDNA to the Python Package Index (PyPI) so users can install it with `pip install vibedna`.

---

## Quick Start (5 Steps)

```bash
# 1. Install build tools
pip install build twine

# 2. Build the package
python -m build

# 3. Check the package
twine check dist/*

# 4. Upload to TestPyPI (optional but recommended)
twine upload --repository testpypi dist/*

# 5. Upload to PyPI
twine upload dist/*
```

---

## Detailed Publishing Steps

### Step 1: Prerequisites

#### Create PyPI Accounts

1. **PyPI Account** (Production): https://pypi.org/account/register/
2. **TestPyPI Account** (Testing): https://test.pypi.org/account/register/

#### Generate API Tokens

1. Log in to PyPI → Account Settings → API Tokens
2. Create a token with scope "Entire account" (or project-specific after first upload)
3. Save the token securely (starts with `pypi-`)

#### Install Required Tools

```bash
pip install --upgrade build twine
```

### Step 2: Verify Package Configuration

Ensure `pyproject.toml` has correct metadata:

```bash
# Check the current version
grep "^version" pyproject.toml

# Verify package name is available on PyPI
pip index versions vibedna 2>/dev/null || echo "Package name available!"
```

### Step 3: Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build source distribution and wheel
python -m build

# Verify build outputs
ls -la dist/
# Expected:
#   vibedna-1.0.0.tar.gz        (source distribution)
#   vibedna-1.0.0-py3-none-any.whl  (wheel)
```

### Step 4: Validate the Package

```bash
# Check package metadata and structure
twine check dist/*

# Expected output:
# Checking dist/vibedna-1.0.0.tar.gz: PASSED
# Checking dist/vibedna-1.0.0-py3-none-any.whl: PASSED
```

### Step 5: Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Enter credentials when prompted:
#   Username: __token__
#   Password: <your-testpypi-token>

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    vibedna

# Verify it works
vibedna --version
python -c "from vibedna import DNAEncoder; print('Import OK')"
```

### Step 6: Publish to PyPI (Production)

```bash
# Upload to PyPI
twine upload dist/*

# Enter credentials when prompted:
#   Username: __token__
#   Password: <your-pypi-token>

# Verify on PyPI
# Visit: https://pypi.org/project/vibedna/
```

### Step 7: Verify Installation

```bash
# Install from PyPI
pip install vibedna

# Test CLI
vibedna --version
vibedna quick "Hello from PyPI!"

# Test SDK
python -c "
from vibedna import DNAEncoder, DNADecoder
encoder = DNAEncoder()
dna = encoder.encode(b'VibeDNA on PyPI!')
print(f'Success! DNA length: {len(dna)} nucleotides')
"
```

---

## Configuration Files

### ~/.pypirc (Optional - Store Credentials)

Create `~/.pypirc` to avoid entering credentials each time:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

**Security:** Restrict file permissions:
```bash
chmod 600 ~/.pypirc
```

---

## Version Management

### Updating Version for New Release

1. Update version in `pyproject.toml`:
   ```toml
   version = "1.1.0"
   ```

2. Update version in `vibedna/__init__.py`:
   ```python
   __version__ = "1.1.0"
   ```

3. Update `CHANGELOG.md` with new changes

4. Rebuild and upload:
   ```bash
   rm -rf dist/
   python -m build
   twine upload dist/*
   ```

### Semantic Versioning

Follow [SemVer](https://semver.org/):
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features, backward compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, backward compatible

---

## CI/CD Automation (GitHub Actions)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # For trusted publishing

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build tools
        run: pip install build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # Uses trusted publishing (no token needed if configured)
```

### Set Up Trusted Publishing (Recommended)

1. Go to PyPI → Your Project → Settings → Publishing
2. Add GitHub as a trusted publisher:
   - Owner: `ttracx`
   - Repository: `VibeDNA`
   - Workflow: `publish.yml`

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `Package name already exists` | Choose a different name or contact owner |
| `Invalid credentials` | Use `__token__` as username with API token |
| `Version already exists` | Increment version number |
| `Missing metadata` | Ensure all required fields in pyproject.toml |
| `twine check fails` | Fix README.md formatting (must be valid RST/MD) |

### Verify Package Contents

```bash
# List wheel contents
unzip -l dist/vibedna-*.whl

# Extract and inspect
mkdir -p /tmp/vibedna-check
unzip dist/vibedna-*.whl -d /tmp/vibedna-check
cat /tmp/vibedna-check/vibedna-*.dist-info/METADATA
```

---

## Post-Publishing Checklist

- [ ] Package visible on https://pypi.org/project/vibedna/
- [ ] `pip install vibedna` works
- [ ] CLI command `vibedna` works
- [ ] Python imports work
- [ ] Documentation links work
- [ ] Version badge updated in README
- [ ] Release notes published
- [ ] Announcement posted (if applicable)

---

## Support

For publishing assistance:
- **Website:** https://vibecaas.com
- **Email:** contact@neuralquantum.ai
- **Repository:** https://github.com/ttracx/VibeDNA

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
