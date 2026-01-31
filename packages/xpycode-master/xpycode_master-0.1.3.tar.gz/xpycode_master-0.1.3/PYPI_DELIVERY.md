# PyPI Delivery Infrastructure

This document explains the build and release pipeline for the `xpycode-master` package.

## Overview

The `xpycode-master` package is distributed via PyPI and TestPyPI with the following features:

- **Multi-platform wheel builds**: Windows, macOS, Linux
- **Multi-Python version support**: Python 3.10, 3.11, 3.12
- **Cython-compiled core modules**: For code protection and performance
- **Pre-built Node.js binaries**: Cross-platform addin server executables included

## Package Structure

```
xpycode-master/
├── xpycode_master/              # Main Python package
│   ├── business_layer/          # Core business logic (partially compiled)
│   ├── python_server/           # Python kernel and server (partially compiled)
│   ├── addin_launcher/          # Addin server launcher
│   │   └── bin/                 # Pre-built Node.js binaries (~40-50MB each)
│   ├── ide/                     # IDE application
│   └── ...
├── pyproject.toml               # Package metadata and configuration
├── setup.py                     # Cython compilation setup
├── MANIFEST.in                  # Source distribution file list
└── scripts/
    ├── build_all.py            # Master build script
    └── upload_pypi.py          # Upload helper script
```

## Compiled Modules

The following modules are compiled with Cython for code protection and performance:

```python
xpycode_master/business_layer/server.py
xpycode_master/python_server/kernel.py
xpycode_master/python_server/xpycode/com_like.py
xpycode_master/python_server/lsp_bridge.py
xpycode_master/python_server/event_manager.py
xpycode_master/python_server/debugger.py
xpycode_master/business_layer/dependency_resolver.py
xpycode_master/business_layer/packages/package_index_client.py
xpycode_master/business_layer/packages/handlers.py
xpycode_master/business_layer/packages/manager.py
xpycode_master/launcher.py
xpycode_master/watchdog.py
```

### Files That Remain as .py (NOT Compiled)

The following files must remain as Python source files:

- All `__init__.py` files
- All `__main__.py` files
- `xpycode_master/python_server/xpycode/office_objects.py` (type stubs)
- All files in `xpycode_master/python_server/stubs/`
- `xpycode_master/addin_launcher/py.typed` (type marker)
- All `config.py` files
- All `exceptions.py` files

## Platform Support Matrix

| Platform | Python 3.10 | Python 3.11 | Python 3.12 |
|----------|-------------|-------------|-------------|
| Linux    | ✅          | ✅          | ✅          |
| Windows  | ✅          | ✅          | ✅          |
| macOS    | ✅          | ✅          | ✅          |

## Building Locally

### Prerequisites

- Python 3.10, 3.11, or 3.12
- Node.js 18+ (for building addin binaries)
- npm with `pkg` package
- C compiler (for Cython compilation)

### Full Build Process

1. **Build Node.js binaries**:
   ```bash
   cd addin
   # On Windows:
   build_binaries.bat
   
   # On Linux/macOS:
   bash build_binaries.sh
   ```

2. **Build everything** (binaries + wheel + sdist):
   ```bash
   python scripts/build_all.py
   ```

3. **Or build selectively**:
   ```bash
   # Skip binary build (if already built)
   python scripts/build_all.py --skip-binaries
   
   # Build only wheel
   python scripts/build_all.py --skip-binaries --skip-sdist
   
   # Build only sdist
   python scripts/build_all.py --skip-binaries --skip-wheel
   ```

### Manual Build Steps

1. **Install build dependencies**:
   ```bash
   pip install build wheel "Cython>=3.0.0" "setuptools>=61.0"
   ```

2. **Build wheel**:
   ```bash
   python -m build --wheel
   ```

3. **Build source distribution** (without Cython):
   ```bash
   SKIP_CYTHON=1 python -m build --sdist
   ```

## Uploading to PyPI

### Using the Upload Script

```bash
# Upload to TestPyPI (default)
python scripts/upload_pypi.py

# Upload to production PyPI
python scripts/upload_pypi.py --target pypi
```

### Manual Upload with Twine

```bash
# Install twine
pip install twine

# Upload to TestPyPI
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Upload to PyPI
twine upload dist/*
```

### API Token Configuration

#### For TestPyPI:
Set the `TEST_PYPI_API_TOKEN` environment variable:
```bash
export TEST_PYPI_API_TOKEN="pypi-..."
```

#### For Production PyPI:
Set the `PYPI_API_TOKEN` environment variable:
```bash
export PYPI_API_TOKEN="pypi-..."
```

## GitHub Actions CI/CD

### Workflow Triggers

The build workflow is triggered by:

1. **Pushing a tag** matching `v*` (e.g., `v0.1.0`)
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **Manual workflow dispatch** via GitHub Actions UI
   - Go to Actions → Build and Release → Run workflow
   - Optionally check "Publish to production PyPI"

### Workflow Jobs

The workflow consists of 5 jobs:

1. **build-node-binaries**: Builds Node.js binaries for all platforms
2. **build-wheels**: Builds wheels for each OS × Python version combination (9 total)
3. **build-sdist**: Builds source distribution
4. **publish-testpypi**: Publishes all distributions to TestPyPI (always runs)
5. **publish-pypi**: Publishes to production PyPI (only on tags or manual trigger)

### GitHub Secrets Required

Configure the following secrets in your GitHub repository:

- `TEST_PYPI_API_TOKEN`: API token for TestPyPI
- `PYPI_API_TOKEN`: API token for production PyPI

To add secrets:
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add the token name and value

### Obtaining PyPI API Tokens

1. **For TestPyPI**:
   - Go to https://test.pypi.org/manage/account/token/
   - Create a new API token
   - Scope: "Entire account" or specific to `xpycode-master`

2. **For Production PyPI**:
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Scope: "Entire account" or specific to `xpycode-master`

## Installation

### From PyPI (Production)

```bash
pip install xpycode-master

# With IDE support
pip install xpycode-master[ide]

# With data analysis support
pip install xpycode-master[data]

# With all optional dependencies
pip install xpycode-master[all]
```

### From TestPyPI

```bash
pip install --index-url https://pypi.org/simple/ \
    --extra-index-url https://test.pypi.org/simple/ \
    --prefer-binary xpycode_master
```

> **Note**: The index order is important! PyPI is the primary index (to get real dependencies like `fastapi`), and TestPyPI is the extra index (to get `xpycode_master`). The `--prefer-binary` flag ensures pip prefers wheels over source distributions, avoiding fake/malicious source packages that may exist on TestPyPI.

## Usage

After installation, you can run the application using:

```bash
# Command-line entry point
xpycode-master

# Or as a module
python -m xpycode_master
```

## Troubleshooting

### Build Issues

1. **Cython compilation fails**:
   - Ensure you have a C compiler installed
   - On Windows: Install Visual Studio Build Tools
   - On Linux: Install `build-essential` or `gcc`
   - On macOS: Install Xcode Command Line Tools

2. **Node.js binary build fails**:
   - Ensure Node.js 18+ is installed
   - Install `pkg` globally: `npm install -g pkg`
   - Check that you're in the `addin/` directory

3. **Missing binaries in wheel**:
   - Ensure binaries are built before running `python -m build`
   - Check that `xpycode_master/addin_launcher/bin/` contains the executables

### Upload Issues

1. **Authentication failed**:
   - Verify your API token is correct
   - Ensure the token has appropriate scope
   - Check that environment variable is set correctly

2. **Version already exists**:
   - Increment the version in `xpycode_master/__init__.py`
   - Update version in `pyproject.toml` if different
   - PyPI doesn't allow overwriting existing versions

## Version Management

The package version is defined in `xpycode_master/__init__.py`:

```python
__version__ = '0.1.0'
```

To release a new version:
1. Update `__version__` in `xpycode_master/__init__.py`
2. Update `version` in `pyproject.toml` (should match)
3. Commit the changes
4. Create and push a git tag: `git tag v0.1.0 && git push origin v0.1.0`

## Development Installation

For development, install in editable mode:

```bash
# Clone the repository
git clone https://github.com/gb-bge-advisory/xpycode_gemini_v3.git
cd xpycode_gemini_v3

# Install in editable mode
pip install -e .

# Or with optional dependencies
pip install -e ".[all]"
```

Note: In editable mode, Cython compilation is skipped by default.

## Binary Size Considerations

The Node.js binaries add significant size to the wheel:
- Each binary: ~40-50 MB
- 3 platform binaries: ~120-150 MB total
- Plus resources: ~5-10 MB

Typical wheel sizes:
- Windows wheel: ~50 MB (includes Windows binary only)
- macOS wheel: ~50 MB (includes macOS binary only)
- Linux wheel: ~50 MB (includes Linux binary only)
- Source distribution: ~150 MB (includes all binaries)

## License

This package is distributed under the MIT License. See LICENSE file for details.
