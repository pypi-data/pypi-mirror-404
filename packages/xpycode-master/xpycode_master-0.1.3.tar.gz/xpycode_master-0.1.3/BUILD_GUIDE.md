# XPyCode Build Guide

This guide provides step-by-step instructions for building and publishing XPyCode manually on your local PC.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step-by-Step Manual Build](#step-by-step-manual-build)
- [PowerShell Build Script](#powershell-build-script)

---

## Prerequisites

### 1. Python Build Dependencies

```powershell
pip install build wheel "Cython>=3.0.0" "setuptools>=61.0" twine
```

### 2. C Compiler (Required for Cython)

Download and install **Visual Studio Build Tools**:
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- During installation, select **"Desktop development with C++"**

### 3. Node.js (Required for Excel Add-in binaries)

- Download and install Node.js 18+ from: https://nodejs.org/
- After installation, install `pkg` globally: 

```powershell
npm install -g pkg
```

### 4. PyPI Account Setup

1. Create accounts on:
   - **TestPyPI**: https://test.pypi.org/account/register/
   - **PyPI**:  https://pypi.org/account/register/

2. Generate API tokens:
   - **TestPyPI**:  https://test.pypi.org/manage/account/token/
   - **PyPI**: https://pypi.org/manage/account/token/

---

## Step-by-Step Manual Build

### Step 1: Navigate to Project Root

```powershell
cd C:\path\to\xpycode_master_repo
```

### Step 2: Build Node.js Binaries (Excel Add-in)

```powershell
cd addin
.\build_binaries.bat
cd ..
```

Verify binaries were created: 

```powershell
dir xpycode_master\addin_launcher\bin\
```

You should see executable files for Windows, Linux, and macOS.

### Step 3: Build the Wheel (with Cython Compilation)

```powershell
python -m build --wheel
```

or

```powershell
set CIBW_BUILD=cp38-abi3-win_amd64
python -m cibuildwheel --output-dir dist
```


This will: 
- Compile the core modules with Cython → `.pyd` files (Windows) or `.so` files (Linux/macOS)
- Package everything into a `.whl` file in the `dist/` folder

---

## Platform-Specific Builds

By default, the wheel build automatically detects your platform and includes only the matching Node.js binary, reducing the wheel size by ~100MB.

**When Binary Cleanup Occurs:**
- **Wheel builds (`bdist_wheel`)**: Binaries for other platforms are removed (only target platform kept)
- **Install from sdist**: Binaries for other platforms are removed during installation
- **Source distribution (`sdist`)**: All 3 binaries are preserved in the tarball

### Environment Variable: XPYCODE_TARGET_PLATFORM

You can override the platform detection using the `XPYCODE_TARGET_PLATFORM` environment variable:

| Value | Description | Binary Kept |
|-------|-------------|-------------|
| `win` or `windows` | Build for Windows | `addin-server-win.exe` |
| `mac` or `macos` or `darwin` | Build for macOS | `addin-server-macos` |
| `linux` | Build for Linux | `addin-server-linux` |
| `all` | Keep all binaries | All three binaries |
| *(not set)* | Auto-detect platform | Current platform's binary |

### Usage Examples

**Windows (PowerShell):**
```powershell
# Auto-detect (Windows binary only)
python -m build --wheel

# Force Linux binary only
$env:XPYCODE_TARGET_PLATFORM = "linux"
python -m build --wheel

# Keep all binaries for cross-platform distribution
$env:XPYCODE_TARGET_PLATFORM = "all"
python -m build --wheel
```

**Linux/macOS (Bash):**
```bash
# Auto-detect (current platform binary only)
python -m build --wheel

# Force Windows binary only
XPYCODE_TARGET_PLATFORM=win python -m build --wheel

# Keep all binaries for cross-platform distribution
XPYCODE_TARGET_PLATFORM=all python -m build --wheel
```

---

### Step 4: (Optional) Build Source Distribution

> ⚠️ **WARNING**: The source distribution includes your Python source code!   
> Only build this if you want to distribute source code.

```powershell
$env:SKIP_CYTHON = "1"
python -m build --sdist
Remove-Item Env:SKIP_CYTHON
```

**Note**: The source distribution (sdist) contains **all 3 platform binaries** (Windows, Linux, macOS). The platform-specific binary cleanup only occurs during wheel builds or when installing from sdist. This ensures that users can install from sdist on any platform.

### Step 5: Verify the Build

```powershell
dir dist\
```

You should see:
- `xpycode_master-0.1.0-cp310-cp310-win_amd64.whl` (or similar, depending on Python version)
- `xpycode_master-0.1.0.tar. gz` (only if you built sdist)

### Step 6: Upload to TestPyPI

First, set your TestPyPI API token:

```powershell
$env:TWINE_PASSWORD = "pypi-xxxxx-your-test-pypi-token"
```

Then upload: 

```powershell
twine upload --repository-url https://test.pypi.org/legacy/ --username __token__ dist\*
```

Or use the helper script:

```powershell
python scripts\upload_pypi.py --target testpypi
```

#### Test Installation from TestPyPI

```powershell
pip install --index-url https://pypi.org/simple/ --extra-index-url https://test.pypi.org/simple/ --prefer-binary xpycode_master
```

> **Note**: The index order matters! PyPI is the primary index (to get real dependencies like `fastapi`), and TestPyPI is the extra index (to get `xpycode_master`). The `--prefer-binary` flag ensures pip prefers wheels over source distributions, avoiding fake/malicious source packages that may exist on TestPyPI.

### Step 7: Upload to Production PyPI

First, set your PyPI API token: 

```powershell
$env:TWINE_PASSWORD = "pypi-xxxxx-your-pypi-token"
```

Then upload: 

```powershell
twine upload --username __token__ dist\*
```

Or use the helper script:

```powershell
python scripts\upload_pypi.py --target pypi
```

---

## PowerShell Build Script

Save this as `build_and_upload.ps1` in your project root for automated builds: 

```powershell
<#
.SYNOPSIS
    XPyCode Build and Upload Script

.DESCRIPTION
    This script automates the complete build and upload process for XPyCode. 
    It builds Node.js binaries, compiles Python with Cython, and uploads to PyPI.

. PARAMETER SkipBinaries
    Skip building Node.js binaries (use if already built)

.PARAMETER SkipWheel
    Skip building the wheel

.PARAMETER SkipSdist
    Skip building source distribution

.PARAMETER UploadTarget
    Upload target:  'none', 'testpypi', or 'pypi' (default: none)

.PARAMETER TestPyPIToken
    API token for TestPyPI (can also be set via $env:TEST_PYPI_TOKEN)

.PARAMETER PyPIToken
    API token for PyPI (can also be set via $env: PYPI_TOKEN)

.EXAMPLE
    .\build_and_upload.ps1
    # Build everything, no upload

.EXAMPLE
    .\build_and_upload.ps1 -SkipBinaries -UploadTarget testpypi
    # Build wheel and sdist, upload to TestPyPI

. EXAMPLE
    .\build_and_upload.ps1 -UploadTarget pypi -PyPIToken "pypi-xxxx"
    # Full build and upload to production PyPI
#>

param(
    [switch]$SkipBinaries,
    [switch]$SkipWheel,
    [switch]$SkipSdist,
    [ValidateSet('none', 'testpypi', 'pypi')]
    [string]$UploadTarget = 'none',
    [string]$TestPyPIToken = $env:TEST_PYPI_TOKEN,
    [string]$PyPIToken = $env:PYPI_TOKEN
)

# Configuration
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

# Colors for output
function Write-Step {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Check prerequisites
function Test-Prerequisites {
    Write-Step "Checking Prerequisites"
    
    $missing = @()
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "Python:  $pythonVersion"
    } catch {
        $missing += "Python 3.10+"
    }
    
    # Check pip packages
    $requiredPackages = @("build", "wheel", "Cython", "twine")
    foreach ($pkg in $requiredPackages) {
        $installed = pip show $pkg 2>$null
        if ($installed) {
            Write-Success "Package: $pkg installed"
        } else {
            Write-Warning "Package:  $pkg not installed"
            Write-Host "Installing $pkg..." -ForegroundColor Yellow
            pip install $pkg
        }
    }
    
    # Check Node.js (only if building binaries)
    if (-not $SkipBinaries) {
        try {
            $nodeVersion = node --version 2>&1
            Write-Success "Node. js: $nodeVersion"
        } catch {
            $missing += "Node.js 18+"
        }
        
        # Check pkg
        try {
            $pkgVersion = pkg --version 2>&1
            Write-Success "pkg: $pkgVersion"
        } catch {
            Write-Warning "pkg not installed, installing..."
            npm install -g pkg
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Error "Missing prerequisites: $($missing -join ', ')"
        exit 1
    }
    
    Write-Success "All prerequisites satisfied"
}

# Build Node.js binaries
function Build-NodeBinaries {
    Write-Step "Building Node.js Binaries"
    
    $addinDir = Join-Path $ProjectRoot "addin"
    
    if (-not (Test-Path $addinDir)) {
        Write-Error "Addin directory not found:  $addinDir"
        exit 1
    }
    
    Push-Location $addinDir
    try {
        $buildScript = Join-Path $addinDir "build_binaries.bat"
        if (Test-Path $buildScript) {
            & cmd /c $buildScript
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Binary build failed"
                exit 1
            }
        } else {
            Write-Error "Build script not found:  $buildScript"
            exit 1
        }
    } finally {
        Pop-Location
    }
    
    # Verify binaries
    $binDir = Join-Path $ProjectRoot "xpycode_master\addin_launcher\bin"
    if (Test-Path $binDir) {
        $binaries = Get-ChildItem $binDir -File
        Write-Success "Built $($binaries.Count) binary files"
        foreach ($bin in $binaries) {
            Write-Host "  - $($bin.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Warning "Binary directory not found: $binDir"
    }
}

# Clean previous builds
function Clear-BuildArtifacts {
    Write-Step "Cleaning Previous Build Artifacts"
    
    $dirsToClean = @("dist", "build", "*. egg-info")
    
    foreach ($pattern in $dirsToClean) {
        $items = Get-ChildItem -Path $ProjectRoot -Filter $pattern -Directory -ErrorAction SilentlyContinue
        foreach ($item in $items) {
            Remove-Item $item. FullName -Recurse -Force
            Write-Host "  Removed: $($item.Name)" -ForegroundColor Gray
        }
    }
    
    # Also clean . pyd files from previous Cython builds
    $pydFiles = Get-ChildItem -Path (Join-Path $ProjectRoot "xpycode_master") -Filter "*.pyd" -Recurse -ErrorAction SilentlyContinue
    foreach ($pyd in $pydFiles) {
        Remove-Item $pyd.FullName -Force
        Write-Host "  Removed:  $($pyd. Name)" -ForegroundColor Gray
    }
    
    Write-Success "Clean complete"
}

# Build wheel
function Build-Wheel {
    Write-Step "Building Wheel (with Cython compilation)"
    
    Push-Location $ProjectRoot
    try {
        python -m build --wheel
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Wheel build failed"
            exit 1
        }
    } finally {
        Pop-Location
    }
    
    # Verify wheel
    $wheels = Get-ChildItem -Path (Join-Path $ProjectRoot "dist") -Filter "*.whl"
    if ($wheels.Count -gt 0) {
        foreach ($wheel in $wheels) {
            $sizeMB = [math]::Round($wheel.Length / 1MB, 2)
            Write-Success "Built:  $($wheel.Name) ($sizeMB MB)"
        }
    } else {
        Write-Error "No wheel files found in dist/"
        exit 1
    }
}

# Build source distribution
function Build-Sdist {
    Write-Step "Building Source Distribution"
    
    Write-Warning "Source distribution will include Python source code!"
    
    Push-Location $ProjectRoot
    try {
        $env:SKIP_CYTHON = "1"
        python -m build --sdist
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Sdist build failed"
            exit 1
        }
    } finally {
        Remove-Item Env:SKIP_CYTHON -ErrorAction SilentlyContinue
        Pop-Location
    }
    
    # Verify sdist
    $sdists = Get-ChildItem -Path (Join-Path $ProjectRoot "dist") -Filter "*.tar.gz"
    if ($sdists.Count -gt 0) {
        foreach ($sdist in $sdists) {
            $sizeMB = [math]::Round($sdist.Length / 1MB, 2)
            Write-Success "Built:  $($sdist. Name) ($sizeMB MB)"
        }
    }
}

# Upload to PyPI
function Upload-ToPyPI {
    param(
        [string]$Target,
        [string]$Token
    )
    
    Write-Step "Uploading to $Target"
    
    if (-not $Token) {
        Write-Error "No API token provided for $Target"
        Write-Host "Set the token via parameter or environment variable" -ForegroundColor Yellow
        exit 1
    }
    
    $distDir = Join-Path $ProjectRoot "dist"
    $wheels = Get-ChildItem -Path $distDir -Filter "*. whl"
    
    if ($wheels.Count -eq 0) {
        Write-Error "No wheel files found in dist/"
        exit 1
    }
    
    Write-Host "Files to upload:" -ForegroundColor Gray
    foreach ($wheel in $wheels) {
        Write-Host "  - $($wheel.Name)" -ForegroundColor Gray
    }
    
    $env:TWINE_PASSWORD = $Token
    
    try {
        if ($Target -eq "testpypi") {
            twine upload --repository-url https://test.pypi.org/legacy/ --username __token__ "$distDir\*.whl"
        } else {
            twine upload --username __token__ "$distDir\*.whl"
        }
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Upload failed"
            exit 1
        }
        
        Write-Success "Upload to $Target complete!"
        
        if ($Target -eq "testpypi") {
            Write-Host "`nTo install from TestPyPI:" -ForegroundColor Cyan
            Write-Host "  pip install --index-url https://pypi.org/simple/ --extra-index-url https://test.pypi.org/simple/ --prefer-binary xpycode_master" -ForegroundColor White
        } else {
            Write-Host "`nTo install from PyPI:" -ForegroundColor Cyan
            Write-Host "  pip install xpycode_master" -ForegroundColor White
        }
    } finally {
        Remove-Item Env: TWINE_PASSWORD -ErrorAction SilentlyContinue
    }
}

# Main execution
function Main {
    Write-Host "`n"
    Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║       XPyCode Build & Upload Script      ║" -ForegroundColor Magenta
    Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Magenta
    
    # Check prerequisites
    Test-Prerequisites
    
    # Clean previous builds
    Clear-BuildArtifacts
    
    # Build Node.js binaries
    if (-not $SkipBinaries) {
        Build-NodeBinaries
    } else {
        Write-Warning "Skipping Node.js binary build"
    }
    
    # Build wheel
    if (-not $SkipWheel) {
        Build-Wheel
    } else {
        Write-Warning "Skipping wheel build"
    }
    
    # Build sdist
    if (-not $SkipSdist) {
        Build-Sdist
    } else {
        Write-Warning "Skipping source distribution build"
    }
    
    # Show build summary
    Write-Step "Build Summary"
    $distDir = Join-Path $ProjectRoot "dist"
    if (Test-Path $distDir) {
        $files = Get-ChildItem $distDir
        Write-Host "Files in dist/:" -ForegroundColor Gray
        foreach ($file in $files) {
            $sizeMB = [math]::Round($file.Length / 1MB, 2)
            Write-Host "  $($file.Name) ($sizeMB MB)" -ForegroundColor White
        }
    }
    
    # Upload if requested
    if ($UploadTarget -ne "none") {
        if ($UploadTarget -eq "testpypi") {
            Upload-ToPyPI -Target "testpypi" -Token $TestPyPIToken
        } elseif ($UploadTarget -eq "pypi") {
            Upload-ToPyPI -Target "pypi" -Token $PyPIToken
        }
    }
    
    Write-Host "`n"
    Write-Success "Build process complete!"
    Write-Host "`n"
}

# Run main
Main
```

### Usage Examples

```powershell
# Build everything (no upload)
.\build_and_upload. ps1

# Build wheel only, skip binaries and sdist
.\build_and_upload. ps1 -SkipBinaries -SkipSdist

# Build and upload to TestPyPI
.\build_and_upload.ps1 -UploadTarget testpypi -TestPyPIToken "pypi-xxxxx"

# Build and upload to production PyPI
.\build_and_upload. ps1 -UploadTarget pypi -PyPIToken "pypi-xxxxx"

# Quick rebuild (skip binaries) and upload to TestPyPI
.\build_and_upload.ps1 -SkipBinaries -UploadTarget testpypi
```

---

## Troubleshooting

### Cython Compilation Fails

**Problem**: Error about missing C compiler

**Solution**:  Install Visual Studio Build Tools with "Desktop development with C++" workload

### Node.js Binary Build Fails

**Problem**: `pkg` command not found

**Solution**: 
```powershell
npm install -g pkg
```

### Upload Authentication Fails

**Problem**:  403 Forbidden or authentication error

**Solution**: 
- Verify your API token is correct
- Ensure the token has appropriate scope (entire account or project-specific)
- Check that you're using `__token__` as the username

### Version Already Exists

**Problem**: Cannot upload - version already exists on PyPI

**Solution**: 
- Increment the version in `pyproject.toml`
- Clean and rebuild:  `.\build_and_upload.ps1`
