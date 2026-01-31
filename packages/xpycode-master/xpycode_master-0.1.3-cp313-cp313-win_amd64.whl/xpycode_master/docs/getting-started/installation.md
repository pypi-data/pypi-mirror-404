# Installation

This guide will walk you through installing XPyCode and setting up your development environment.

## :material-check-all: Prerequisites

Before installing XPyCode, ensure your system meets these requirements:

### System Requirements

- **Operating System**: Windows 10/11 (64-bit) or other platforms (experimental)
- **Python**: Version 3.10 or higher
- **Microsoft Excel**: 2016 or later with Office.js Add-in support (365, 2019, 2021)
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Disk Space**: 500MB for XPyCode plus additional space for packages

### Verify Python Installation

Check that Python is installed and meets the minimum version:

```bash
python --version
```

You should see output like `Python 3.10.x` or higher. If not, download Python from [python.org](https://www.python.org/downloads/).

!!! tip "Python Installation Tips"
    - Make sure to check "Add Python to PATH" during installation
    - On Windows, use the 64-bit installer for best performance
    - Verify `pip` is available by running `pip --version`

## :material-download: Installing XPyCode

Install XPyCode using pip:

```bash
pip install xpycode_master
```

!!! tip "Alternative Launch Methods"
    You can also launch XPyCode using:
    
    - Windows: `xpycode_master.exe` in the Scripts directory
    - Other platforms: Equivalent executable in the Scripts/bin directory

This will install XPyCode and all its dependencies including:

- FastAPI and Uvicorn (web framework and server)
- PySide6 (Qt bindings for the IDE)
- Jedi (Python autocompletion)
- WebSockets (communication layer)
- And other required packages

!!! info "Installation Time"
    First-time installation may take 2-5 minutes as pip downloads and installs all dependencies. Subsequent updates will be faster.

### Verify Installation

Confirm XPyCode is installed correctly:

```bash
python -m xpycode_master --version
```

## :material-rocket: Launching XPyCode

### Start the XPyCode Server

Launch the XPyCode Master server from your terminal:

```bash
python -m xpycode_master
```

You should see output indicating the server has started:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

!!! success "Server Running"
    Keep this terminal window open. The server must be running for XPyCode to work in Excel.

### Access the Excel Add-in

1. **Open Microsoft Excel**
2. Navigate to **Home** tab → **Add-ins** → **More Add-ins**
3. Click on **Shared Folder** tab
4. Look for **XPyCode** in the list
5. Click **Add** to enable the add-in

<!-- SCREENSHOT: excel-addin-location.png -->
<figure markdown>
  ![Excel Add-in Location](../assets/screenshots/excel/excel-addin-location.png){ width="700" }
  <figcaption>XPyCode add-in in Excel's Shared Folder</figcaption>
</figure>

!!! note "Add-in Registration"
    The add-in is automatically registered when you first start the XPyCode server. If you don't see it, try restarting Excel.

!!! warning "Manual Certificate Installation"
    On non-Windows platforms or if you encounter certificate issues, you may need to manually install the self-signed certificate located in `~/.xpycode/certs` (or `%USERPROFILE%\.xpycode\certs` on Windows).

!!! note "Manual Manifest Sideloading"
    For Excel Desktop on non-Windows platforms or Excel for Web, you'll need to manually sideload the manifest file located in `~/.xpycode/manifest` (or `%USERPROFILE%\.xpycode\manifest` on Windows).


### Open the XPyCode Console

Once the add-in is loaded:

1. You'll see a **XPyCode** tab in the Excel ribbon
2. Click **Open Console** to launch the XPyCode IDE

<!-- SCREENSHOT: xpycode-ribbon.png -->
<figure markdown>
  ![XPyCode Ribbon](../assets/screenshots/excel/xpycode-ribbon.png){ width="200" }
  <figcaption>XPyCode ribbon tab in Excel</figcaption>
</figure>

The XPyCode IDE window will open, showing:

- **Welcome screen** with quick links
- **Project Explorer** on the left
- **Code Editor** in the center
- **Console** at the bottom
- **Utilities tabs** on the right

<!-- SCREENSHOT: ide-first-launch.png -->
<figure markdown>
  ![IDE First Launch](../assets/screenshots/ide/ide-first-launch.png){ width="700" }
  <figcaption>XPyCode IDE on first launch</figcaption>
</figure>

## :material-cog: Configuration

### Default Settings

XPyCode comes with sensible defaults, but you can customize it through **File → Settings**:

See the [Settings](../user-guide/settings.md) guide for detailed configuration options.

### First-Time Setup

On first launch, XPyCode will:

1. Create configuration directories in your user folder
2. Set up the default theme (XPC Dark)
3. Initialize the package cache directory
4. Register the self-signed certificates for HTTPS protocol (Windows only - manual installation required on other platforms)
5. Register the Excel add-in manifest (Windows Excel Desktop only - manual sideloading required for other platforms)

## :material-sync: Updating XPyCode

To update to the latest version:

```bash
pip install --upgrade xpycode_master
```

After updating:

1. Close all Excel workbooks
2. Restart the XPyCode server
3. Reopen Excel

!!! warning "Version Compatibility"
    Always restart the server after updating. Running an old server with new add-ins may cause compatibility issues.

## :material-cloud-outline: Addin Hosting Modes

XPyCode supports two modes for running the Excel add-in. Both modes run the Python kernel locally on your machine - only the add-in UI hosting differs.

### Local Mode (Default)

In local mode, the add-in UI is served from a local HTTPS server on your machine.

```bash
python -m xpycode_master
```

**Advantages:**

- Works completely offline (no internet required)
- Full control over the add-in version
- Lower latency

**Requirements:**

- Self-signed certificate (automatically managed on Windows)

### External Mode

In external mode, the add-in UI is served from `https://addin.xpycode.com`. The Python kernel and business layer still run locally.

```bash
python -m xpycode_master --use-external-addin
```

**Advantages:**

- No local certificate management required
- Simpler setup process
- Easier troubleshooting (fewer moving parts)

**Requirements:**

- Internet connection (for loading add-in UI assets)

!!! warning "Mode Switch Cache Clearing"
    When switching between local and external modes, XPyCode will automatically clear the Office add-in cache. This affects all Office add-ins, not just XPyCode. You may need to restart Excel after switching modes.

## :material-alert-circle: Troubleshooting Installation

### Python Not Found

If you get "Python not found" error:

1. Verify Python is installed: `python --version`
2. Check Python is in your PATH environment variable
3. Try using `python3` instead of `python`

### Pip Installation Fails

If `pip install` fails with network errors:

```bash
# Use a different PyPI mirror
pip install xpycode_master --index-url https://pypi.org/simple

# Or install with verbose output to see what's failing
pip install -v xpycode_master
```

### Add-in Not Appearing in Excel

If the add-in doesn't appear:

1. Ensure the XPyCode server is running
2. Check Excel trusts add-ins from shared folders:
   - **File → Options → Trust Center → Trust Center Settings → Trusted Add-in Catalogs**
3. Restart Excel completely (close all workbooks)
4. Manually add the manifest location if needed (check server logs for the path)

### Port Auto-Discovery

XPyCode automatically scans for available ports to avoid conflicts. You can override this behavior by specifying ports manually:


```bash
# Use a different port
python -m xpycode_master --addin-port 8001 --server-port 9001 --watchdog-port 8100
```

Then update the add-in configuration to match the new port with **Add-ins** → **More Add-ins** → **Shared Folder** → **Refresh**

### Firewall Issues

Windows Firewall may block the connection:

1. Click "Allow access" when prompted
2. Or manually add an exception for Python in Windows Firewall settings

## :material-progress-check: Next Steps

Now that XPyCode is installed and running:

1. **[Quick Start](quick-start.md)** - Take a 5-minute tour of key features
2. **[First Function](first-function.md)** - Create your first Python function in Excel
3. **[User Guide](../user-guide/ide/overview.md)** - Explore all IDE capabilities

---

!!! question "Need Help?"
    If you encounter issues not covered here, check the [Troubleshooting Guide](../reference/troubleshooting.md) or [open an issue](https://xpycode.com/issues) on GitHub.
