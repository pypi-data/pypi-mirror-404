# Troubleshooting

Solutions to common issues and problems in XPyCode.

## :material-connection: Connection Issues

### Server Won't Start

**Problem:** `python -m xpycode_master` fails or exits immediately

**Solutions:**

1. Check Python version: `python --version` (must be 3.10+)
2. Verify installation: `pip show xpycode_master`
3. Check for port conflicts: Try different port with `--port 8001`
4. Look for error messages in terminal
5. Reinstall: `pip install --upgrade --force-reinstall xpycode_master`

### IDE Won't Connect

**Problem:** IDE not opening

**Solutions:**

1. Verify server is running
2. Check firewall isn't blocking Python
3. kill and Restart the IDE via the Add-In
4. Check WebSocket connection in console logs

### Add-in Not Loading in Excel

**Problem:** XPyCode add-in doesn't appear in Excel

**Solutions:**

1. Ensure the XPyCode server is running before opening Excel
2. Check **Home → Add-ins → More Add-ins → Shared Folder**
3. Click **Refresh** to reload the add-in list
4. Verify manifest file location (check server logs):
   - Windows: `%USERPROFILE%\.xpycode\manifest`
   - macOS/Linux: `~/.xpycode/manifest`
5. On non-Windows platforms, manually install the certificate from `~/.xpycode/certs`
6. Add manifest path to **Trust Center → Trusted Add-in Catalogs** or use platform-specific sideloading methods recommended by Microsoft
7. Restart Excel completely (close all workbooks)
8. Re-register the add-in by restarting the XPyCode server

## :material-code-braces: Code Execution Issues

### Code Won't Run

**Problem:** Pressing F5 does nothing or shows errors

**Solutions:**

1. Check for syntax errors (red underlines in editor)
2. Kill and restart the Kernel (via IDE or Add-In)
3. Check console for error messages
4. Save the module first (Ctrl+S)
5. Try closing and reopening the module tab

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'xxx'`

**Solutions:**

1. Install package via Package Manager
2. Verify installation completed successfully
3. Check package name spelling
4. Restart kernel if needed

### Code Runs But No Output

**Problem:** Code executes but console shows nothing

**Solutions:**

1. Add `print()` statements to verify execution
2. Check Console output level (should be "All")
3. Verify code path is being reached
4. Check if "Console Only IDE" filter is hiding output

## :material-bug: Debugging Issues

### Breakpoints Not Hitting

**Problem:** Debugger doesn't stop at breakpoints

**Solutions:**

1. Verify using Debug (Shift+F5), not Run (F5)
2. Ensure breakpoint is on executable line (not comments/blanks)
3. Check if code path reaches the breakpoint
4. Remove and re-add the breakpoint
5. Restart debugging session

### Variables Not Showing

**Problem:** Variables panel is empty during debugging

**Solutions:**

1. Ensure execution is paused at a breakpoint
2. Check if variables exist in current scope
3. Step Into a function to see its local variables

### Step Commands Not Working

**Problem:** F10/F11 don't advance execution

**Solutions:**

1. Verify in active debug session
2. Check if execution is paused (not running)
3. Look for keyboard shortcut conflicts with other software

## :material-function: Function Publishing Issues

### Function Not Appearing in Excel

**Problem:** Published function shows #NAME? error

**Solutions:**

1. Verify function was published (check Function Publisher status)
2. Click on "Sync to Excel" 
3. Close and reopen workbook
4. Force Excel recalculation: Ctrl+Alt+F9
5. Check console for publishing errors

### Function Returns Wrong Results

**Problem:** Excel formula returns incorrect values

**Solutions:**

1. Test function directly in IDE first
2. Check dimension setting (Scalar/Array/Broadcast/Full)
3. Verify type conversions (Python ↔ Excel)
4. Add debug print statements
5. Check for None/null values

### Function is Slow

**Problem:** Excel formulas take long to calculate

**Solutions:**

1. Optimize Python code (use numpy for arrays)
2. Check if dimension is correct for use case
3. Avoid expensive operations in scalar functions
4. Cache results if appropriate
5. Profile code to find bottlenecks
6. Kill and Restart the Kernel

## :material-package: Package Management Issues

### Package Installation Fails

**Problem:** Package Manager shows installation errors

**Solutions:**

1. Check internet connection
2. Try different PyPI mirror (see settings)
3. Check package name and version exist
4. Look for compilation errors (C extensions)
5. Install dependencies manually if needed

### Dependency Conflicts

**Problem:** Installing package breaks others

**Solutions:**

1. Check version compatibility
2. Use Package Manager to install compatible versions
3. Consider using different workbooks for conflicting dependencies

## :material-console: Console Issues

### Console Not Showing Output

**Problem:** print() statements don't appear

**Solutions:**

1. Check output level setting (should be "COMPLETE" for nothing filtered)
2. Verify code is executing (no errors)
3. Disable "Console Only IDE" filter
4. Check if console is cleared automatically

### Console Text Corrupted

**Problem:** Garbled or missing characters

**Solutions:**

1. Clear console and run again
2. Check encoding settings
3. Restart IDE if persistent (via the Add-In or use **File → Exit**)

## :material-cog: Settings Issues

### Settings Not Saving

**Problem:** Changes revert after closing

**Solutions:**

1. Ensure clicking OK/Apply in settings dialog
2. Check file permissions for config directory
3. Verify settings file isn't read-only

### Theme Not Applying

**Problem:** Theme change doesn't take effect

**Solutions:**

1. Restart IDE after theme change
2. Check theme files exist in resources
3. Try default theme first

## :material-speedometer: Performance Issues

### IDE Slow or Laggy

**Problem:** UI is unresponsive

**Solutions:**

1. Close unused workbooks
2. Disable minimap in editor
3. Reduce max console lines
4. Close unused IDE panels
5. Kill and Restart the IDE (via Add-IN or **File → Exit**)
5. Check system resources (CPU, memory)

### Large File Editing Slow

**Problem:** Editor lags with big files

**Solutions:**

1. Split into smaller modules
2. Disable unnecessary editor features
3. Use code folding to collapse sections

## :material-microsoft-excel: Excel Integration Issues

### Excel Formulas Not Recalculating

**Problem:** Function results don't update

**Solutions:**

1. Force recalc: Ctrl+Alt+F9
2. Check if calculation mode is Manual
3. Re-publish function (**Sync to Excel**)
4. Verify function code was saved

### Excel Events Not Firing

**Problem:** Event handlers don't execute

**Solutions:**

1. Verify handler is registered in Event Manager
2. Check event name and target worksheet
3. Look for errors in event handler code
4. Add error handling to event function
5. Check console for event-related errors

## :material-cached: Clearing the Office Add-in Cache

If the add-in behaves unexpectedly after updates or mode switches, clearing the cache often helps:

### Windows

1. Close all Excel workbooks
2. Navigate to: `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\`
3. Delete all contents of this folder
4. Restart Excel

### macOS

1. Close all Excel workbooks  
2. Navigate to: `~/Library/Containers/com.microsoft.Excel/Data/Documents/wef/`
3. Delete all contents of this folder
4. Restart Excel

### After Clearing Cache

After clearing the cache:

1. Start xpycode_master: `python -m xpycode_master`
2. Open Excel
3. Go to **Add-ins → More Add-ins → Shared Folder**
4. Click **Refresh** if XPyCode doesn't appear
5. Add XPyCode to your workbook

## :material-network: Network Issues

### Behind Corporate Proxy

**Problem:** Can't access PyPI or external services

**Solutions:**

1. Configure proxy in Settings **Package Management**
2. Use internal PyPI mirror if available via Settings
3. Download packages manually and use **Python Paths**
4. Contact IT for proxy whitelist

### SSL/Certificate Errors

**Problem:** SSL verification failures with messages like:
- `SSL: CERTIFICATE_VERIFY_FAILED`
- `SSLError: [SSL] certificate verify failed`
- `unable to get local issuer certificate`

**Solutions:**

1. Manually install the self-signed certificate:
   - **Windows**: Run the XPyCode server which automatically registers the certificate
   - **macOS/Linux**: Import the certificate from `~/.xpycode/certs` into your system's certificate store
2. Verify the certificate is trusted by your system
3. Restart Excel after installing the certificate
4. If issues persist, check that the certificate hasn't expired

## :material-help: Getting More Help

### Reporting Bugs

1. Check if issue is already reported on GitHub Issues
2. Include:
   - XPyCode version
   - Python version
   - Excel version
   - Operating system
   - Steps to reproduce
   - Error messages/logs
3. Create minimal reproducible example

### Community Support

- [GitHub Issues](https://xpycode.com/issues)
- Check documentation thoroughly first
- Search existing issues before creating new ones

## :material-arrow-right: Related

- [Installation Guide](../getting-started/installation.md) - Setup help
- [IDE Overview](../user-guide/ide/overview.md) - Learn IDE features
- [API Reference](xpycode-api.md) - Complete API documentation
