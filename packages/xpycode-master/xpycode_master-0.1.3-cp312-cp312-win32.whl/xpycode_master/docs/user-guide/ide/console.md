# Console

The Console panel displays output, errors, and logging information from your Python code execution. It's an essential tool for debugging and monitoring code behavior.

## :material-console-line: Overview

<!-- SCREENSHOT: console-overview.png -->
<figure markdown>
  ![Console Panel](../../assets/screenshots/ide/console-overview.png){ width="800" }
  <figcaption>Console panel showing code output and errors</figcaption>
</figure>

The Console is located at the bottom of the IDE and shows:

- **Standard output** (`print()` statements)
- **Standard error** (exceptions and errors)
- **System messages** (IDE notifications)
- **Execution status** (running, completed, failed)

## :material-format-color-fill: Output Types

The console uses color-coding for different message types:

### Standard Output (White/Default)

Regular print statements and normal output:

```python
print("Hello, World!")  # White text
print("Calculation complete")  # White text
```

### Errors (Red)

Python exceptions and error messages:

```python
# Red text showing error
raise ValueError("Invalid input")
# Traceback in red
```

### Warnings (Yellow)

Warning messages from XPyCode core processes.

### Print Messages (Blue)

Informational logging:

```python
print("Starting data processing")  # Blue text
```

### Success Messages (Green)

Success indicators from the IDE:

```
Code execution completed successfully  # Green text
```

## :material-cog: Console Settings

Configure console behavior in **File → Settings → Console**:

### Output Level

Control which messages appear:

- **SIMPLE** - Messages for usual users
- **DETAILED** - More messages, including a more verbose communication for advanced users 
- **COMPLETE** - Show everything. Including some logging messages from all XPyCode components 

Default: **COMPLETE**

### Max Lines

Maximum number of lines to keep in console:

- Default: **1000**
- Range: 100-10000
- Older lines are automatically removed

Prevents memory issues with long-running scripts.

### Clear on Run

Automatically clear console when running code:

- Default: **Enabled**
- When disabled: Output accumulates across runs

### Console Only IDE

Show only messages for functions launched via the IDE:

- Default: **Disabled**
- When enabled: Hides messages (print, error, ....) from functions launched within Excel (functions and events) 
- Useful for cleaner output

<!-- SCREENSHOT: console-settings.png -->
<figure markdown>
  ![Console Settings](../../assets/screenshots/ide/console-settings.png){ width="400" }
  <figcaption>Console settings in Settings dialog</figcaption>
</figure>

## :material-feature-search: Console Features

### Auto-Scroll

Console automatically scrolls to show new output:

- Scrolls to bottom when new messages arrive
- Stop auto-scroll by manually scrolling up
- Resume auto-scroll by scrolling to bottom

### Text Selection

Select and copy console text:

- Click and drag to select
- ++ctrl+c++ to copy
- ++ctrl+a++ to select all
- Right-click → Copy

### Context Menu

Right-click in the console for quick actions:

- **Copy** - Copy selected text
- **Select All** - Select all text
- **Clear** - Remove all output

## :material-play: Execution Feedback

The console provides feedback during code execution:

### Before Execution

```
Running function: module_name.test_function() for workbook: Book1.xlsx
```

### During Execution

```python
print("Processing row 1...")
print("Processing row 2...")
print("Processing row 3...")
```

Output appears in real-time as code runs.

### After Execution

Success:
```
Out: 'This is a function return'
Execution completed successfully for test_function()
```

Error:
```
Traceback (most recent call last):
  File "D:\Project\xpycode_master_repo-main\xpycode_master\python_server\kernel.py", line 1993, in execute_function
    raise e
  File "D:\Project\xpycode_master_repo-main\xpycode_master\python_server\kernel.py", line 1967, in execute_function
    result = func(*deserialized_args)
  File "<virtual:todel2>", line 8, in dividingByZero
    a=1/0
      ~^~
ZeroDivisionError: division by zero
```

!!! note "Error Display"
    Errors appear in red in the actual console for easy identification.

## :material-bug: Error Messages

Python error messages are displayed in different locations depending on where the code was executed:

- **IDE Console**: Shows errors when code is run from the IDE, or when the **Console Only IDE** setting is disabled
- **Add-In Console**: Shows errors from UDFs (User Defined Functions) or event handlers triggered from Excel

## :material-code-braces: Using print() Effectively

### Basic Output

```python
print("Hello, World!")
print("Value:", 42)
```

### Formatted Output

```python
name = "Alice"
score = 95
print(f"{name} scored {score} points")
```

### Multiple Values

```python
print("Values:", 1, 2, 3, sep=", ")  # Values: 1, 2, 3
```

### Debug Information

```python
def calculate(x, y):
    print(f"calculate({x}, {y})")  # Debug: function called
    result = x + y
    print(f"  result = {result}")  # Debug: intermediate value
    return result
```


## :material-alert-circle: Troubleshooting

### Output Not Appearing

1. Check output level setting (should be "COMPLETE" to see everything)
2. Verify code is actually running (no syntax errors)
3. Ensure output commands are being reached (not inside unexecuted branches)
4. Check if "Console Only IDE" filter is hiding messages

### Too Much Output

1. Reduce output level (SIMPLE or DETAILED only)
2. Remove or comment out debug print statements
3. Increase "Max Lines" setting
4. Enable "Clear on Run" to start fresh each time

### Console Freezing

1. Very long lines can slow rendering—break them up
2. Too many messages too quickly can cause lag
3. Clear console if it has reached maximum capacity
4. Kill with **Exit** and restart the IDE (or used the advanced function in the add-in) 

## :material-arrow-right: Next Steps

<div class="grid cards" markdown>

-   :material-bug: __Debugging__

    ---

    Learn to use the debugger with breakpoints and variable inspection.

    [:octicons-arrow-right-24: Debugging Guide](debugging.md)

-   :material-cog: __Settings__

    ---

    Configure console output level, max lines, and filters.

    [:octicons-arrow-right-24: Settings Guide](../settings.md)

-   :material-help-circle: __Troubleshooting__

    ---

    Solutions to common console and output issues.

    [:octicons-arrow-right-24: Troubleshooting](../../reference/troubleshooting.md)

</div>

---

!!! tip "Effective Debugging"
    The console is your window into code execution. Use it actively with print statements and logging to understand what your code is doing.
