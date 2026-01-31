# Frequently Asked Questions

Find answers to common questions about XPyCode.

## :material-calendar-clock: Events

### Why don't I see all the events I was used to having in VBA?

XPyCode uses events provided by Microsoft's Office.js JavaScript API, which is a newer technology than VBA. The available events are determined by Microsoft, not XPyCode. As Microsoft adds more events to Office.js, they will become available in XPyCode.

### All my events are deactivated, why?

You have probably set the EnableEvents setting to False. You can turn it back to True via the Add-in Settings (⚙️ icon in the taskpane header).

### Where are double-click events?

Double-click events are not available in Office.js. Consider adapting your workflow to be more "web-oriented" by using single clicks instead of double clicks.

### When an error occurs on a binding onDataChanged event, all the binding events stop working

This is a known issue currently under investigation. As a workaround, close and reopen the workbook to restore event functionality.

### Why does the sample use worksheet events instead of bindings?

Binding events (especially `onDataChanged`) have some behaviors that are not yet fully managed by XPyCode. While bindings provide more targeted event handling, they can raise unexpected issues. Using worksheet events with range intersection checks is currently more reliable, though slightly slower.

---

## :material-connection: Connection & Startup

### My connection is closed and the add-in reconnects when I don't use Excel for a while

This occurs because Excel puts the add-in in pause mode when not actively used. This is a Microsoft behavior that XPyCode cannot bypass at this time.

### At opening, I have a streaming function raising an error like "AttributeError: Attribute worksheets not found on OfficeJs object"

This happens because the streaming function runs while Excel is still initializing. To fix this, enable the **"Start XPyCode when workbook opens"** setting in the taskpane Settings (⚙️). This ensures the add-in is ready before functions execute.

### When opening an Excel file, I see the workbook appearing and disappearing repeatedly in the Editor

This occurs when a function or streaming function tries to run while the add-in is not yet open. Enable the **"Start XPyCode when workbook opens"** setting to resolve this issue.

### All the events and functions I created are not working when I open the workbook

This happens because the add-in has not been launched. Click the **Open Console** button in the Excel Ribbon to start XPyCode, or enable **"Start XPyCode when workbook opens"** in the Settings so the add-in starts automatically with the workbook.

---

## :material-alert-circle: Errors & Troubleshooting

### My registered custom functions are not recognized when I open a saved workbook

This can occurs if it is the first workbook using XPyCode Add-in and it has **"Start XPyCode when workbook opens"**  enabled.
It is a known issue under resolution.

In this case close and reopen the workbook or open an empty workbook and activate the Add-in with **Show Console** before opening your saved workbook.
 

### I have this error: "Cannot use the object across different request contexts." What does it mean?

This error typically occurs when you try to set an attribute (like Range values) using an Excel object (like a Range) instead of a standard Python type (string, float, list, etc.). 

**Example of what causes the error:**
```python
# Wrong - passing a Range object
source_range = ws.getRange("A1:B10")
target_range.values = source_range  # Error!
```

**Correct approach:**
```python
# Right - passing the values (a Python list)
source_range = ws.getRange("A1:B10")
target_range.values = source_range.values  # Works!
```

### I have too many dialog boxes queued up. How can I dismiss them all at once?

Go to **Add-in Advanced Actions** (⚡ icon), select the **Add-in** tab, and click **"Flush Messages"** to clear all pending dialogs.

### My streaming function is blocked

Check if Excel is in manual calculation mode. When you set calculation to manual while updating cells, don't forget to set it back to automatic. It's best practice to use a try/finally block to ensure calculation mode is restored even if an error occurs:

```python
import xpycode

def my_streaming_function():
    # Save current calculation mode
    calc_mode = xpycode.workbook.application.calculationMode
    try:
        # Set to manual for bulk updates
        xpycode.workbook.application.calculationMode = "Manual"
        # ... your updates here ...
    finally:
        # Always restore calculation mode
        xpycode.workbook.application.calculationMode = calc_mode
```

### How do I reset the Python kernel if it's stuck?

You can restart the kernel in two ways:

1. **From the Add-in**: Go to Advanced Actions (⚡ icon) and click **Restart Kernel**
2. **From the IDE**: Go to **Advanced** menu → **Restart Kernel**

Note that restarting the kernel will clear all Python objects in memory, including those saved in the Objects Keeper.

---

## :material-code-braces: API & Code

### Why does the xpycode module have both "excel" and "Excel" attributes?

- **`Excel`** (uppercase) is the class used for type hints and IntelliSense/autocompletion in your IDE
- **`excel`** (lowercase) is used to access static methods and enums of the class (think of it as the singleton instance, even though it's not technically one on the Office.js side)

### Why are Union and Intersect in xpycode.Tools when they exist in workbook.application?

The Office.js `Union` and `Intersect` methods have reliability issues in the context of XPyCode, so we've implemented more robust versions in `xpycode.Tools`. Use these instead for consistent behavior.

### How can I make my code run faster?

Here are some performance tips:

1. **Batch read operations**: Getting data has a fixed time cost regardless of size. Prefer reading a range of data at once and parsing it in Python rather than reading cell by cell.

   ```python
   # Slow - cell by cell
   for i in range(100):
       value = ws.getRange(f"A{i+1}").values[0][0]
   
   # Fast - batch read
   all_values = ws.getRange("A1:A100").values
   for row in all_values:
       value = row[0]
   ```

2. **Batch write operations**: Set values for entire ranges instead of cell by cell.

   ```python
   # Slow - cell by cell
   for i, value in enumerate(data):
       ws.getRange(f"A{i+1}").values = [[value]]
   
   # Fast - batch write
   ws.getRange(f"A1:A{len(data)}").values = [[v] for v in data]
   ```

3. **Batch formatting**: Use `xpycode.Tools.Union` to format multiple ranges at once instead of formatting cell by cell.

### Can I use multiple workbooks with XPyCode at the same time?

Yes! Each workbook has its own isolated Python kernel, set of modules, installed packages, and published functions. This prevents conflicts between different Excel projects and allows each workbook to have different dependencies.

---

## :material-cloud-sync: Addin Modes

### What's the difference between local and external addin modes?

- **Local mode** (default): The add-in UI is served from a local HTTPS server on your machine. Requires self-signed certificates but works offline.
- **External mode** (`--use-external-addin`): The add-in UI is served from `https://addin.xpycode.com`. Requires internet but no certificate setup.

In both modes, the Python kernel runs locally on your machine.

### I switched between local and external mode and now the add-in doesn't work

When switching modes, you need to:

1. Close all Excel workbooks before starting xpycode_master with the new mode
2. Clear the Office add-in cache folder:
   - **Windows**: `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\`
   - **macOS**: `~/Library/Containers/com.microsoft.Excel/Data/Documents/wef/`
3. Restart Excel and re-add XPyCode from Shared Folder

### Which mode should I use?

- Use **local mode** if you need to work offline or want full control
- Use **external mode** if you're having certificate issues or want simpler setup

---

## :material-help-circle: Getting Help

If your question isn't answered here:

1. Check the [Troubleshooting Guide](../reference/troubleshooting.md) for common issues
2. Review the [User Guide](../user-guide/index.md) for detailed feature documentation
3. Report issues on our [GitHub Issues page](https://xpycode.com/issues)
