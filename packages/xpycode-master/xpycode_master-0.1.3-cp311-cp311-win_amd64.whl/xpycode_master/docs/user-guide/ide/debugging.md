# Debugging

XPyCode includes a full-featured debugger that lets you pause code execution, inspect variables, step through code line by line, and diagnose issues efficiently.

## :material-bug-outline: Overview

<!-- SCREENSHOT: debugging-overview.png -->
<figure markdown>
  ![Debugging Interface](../../assets/screenshots/ide/debugging.png){ width="600" }
  <figcaption>Debug panel with variables, call stack, and watch expressions</figcaption>
</figure>

The debugger provides:

- **Breakpoints** - Pause execution at specific lines
- **Step Controls** - Execute code one line/function at a time
- **Variable Inspection** - View current variable values
- **Call Stack** - See the execution path
- **Watch Expressions** - Monitor custom expressions
- **Debug Console** - Evaluate expressions during debugging

## :material-circle-medium: Breakpoints

### Setting Breakpoints

Add a breakpoint to pause execution:

**Method 1: Keyboard Shortcut**

Place cursor on a line and press ++f9++:

- Toggles breakpoint on/off

**Method 2: Debug Menu**

Place cursor on a line and menu **Debug** → **Toggle Breakpoint**

<!-- SCREENSHOT: setting-breakpoint.png -->
<figure markdown>
  ![Setting Breakpoint](../../assets/screenshots/ide/setting-breakpoint.png){ width="300" }
  <figcaption>Breakpoint indicator (red dot) in the editor</figcaption>
</figure>

!!! tip "Breakpoint Lines"
    Set breakpoints on executable lines (not on comments, blank lines, or decorators). The debugger may adjust the position slightly.

### Managing Breakpoints

**Remove a Breakpoint**

- Menu **Debug** → **Toggle Breakpoint**
- Or press ++f9++ on that line


## :material-play-circle: Starting a Debug Session

### Start Debugging

Run code in debug mode:

**Method 1: Keyboard**

Press ++shift+f5++

**Method 2: Toolbar**

Click the **Debug** button (🐛) in the toolbar

**Method 3: Menu**

**Debug → Start Debugging**

<!-- SCREENSHOT: start-debugging.png -->
<figure markdown>
  ![Start Debugging](../../assets/screenshots/ide/start-debugging.png){ width="700" }
  <figcaption>Starting a debug session with Shift+F5</figcaption>
</figure>

### What Happens

When debugging starts:

1. Code executes normally until it hits a breakpoint
2. Execution **pauses** at the breakpoint
3. The **Debug Panel** appears at the bottom
4. The current line is **highlighted in yellow**
5. Variables panel shows current values
6. Debug controls become active

## :material-step-forward: Step Controls

Once paused at a breakpoint, control execution with these commands:

### Continue (Shift+F5)

Resume execution until:

- Next breakpoint is hit
- Code completes
- An error occurs

Use when: You want to skip to the next breakpoint.

### Step Over (F10)

Execute the current line and move to the next line:

- **Functions** - Executes the entire function (doesn't step inside)
- **Simple statements** - Executes and moves to next line

Use when: You want to stay at the current level and don't care about function internals.

### Step Into (F11)

Step into function calls:

- **Function calls** - Enters the function and pauses on first line
- **Simple statements** - Same as Step Over

Use when: You want to debug inside a function being called.

```python
def calculate(x):  # Step Into goes here
    return x * 2

def main():
    result = calculate(5)  # Paused here, press F11
    return f'The result is: {result}'
```

!!! tip "Stepping Limitations"
    The debugger only steps into pure XPyCode in-memory modules. Stepping into an external module function will behave like a step over.

### Step Out (Shift+F11)

Finish the current function and return to the caller:

- Executes remaining lines in current function
- Pauses at the line after the function call

Use when: You've seen enough of the current function and want to return to the caller.

```python
def helper():
    x = 1  # Currently paused here
    y = 2  # Press Shift+F11
    return x + y  # Executes this

result = helper()  # Pauses here after Step Out
```

### Stop Debugging

End the debug session:

- **Debug → Stop Debugging**
- Or click the **Stop** button

Code execution halts immediately.

## :material-variable: Variables Panel

The Variables panel shows all variables in the current scope:

<!-- SCREENSHOT: variables-panel.png -->
<figure markdown>
  ![Variables Panel](../../assets/screenshots/ide/variables-panel.png){ width="600" }
  <figcaption>Variables panel showing current values</figcaption>
</figure>

### What's Displayed

- **Local variables** - Variables in the current function
- **Global variables** - Global variables in the current context

### Variable Information

For each variable, you see:

- **Name** - Variable identifier
- **Type** - Data type (`int`, `str`, `list`, etc.)
- **Value** - Current value (truncated if very long)


## :material-eye: Watch Expressions

Monitor custom expressions that update during debugging:

<!-- SCREENSHOT: watch-panel.png -->
<figure markdown>
  ![Watch Panel](../../assets/screenshots/ide/watch-panel.png){ width="600" }
  <figcaption>Watch panel with custom expressions</figcaption>
</figure>

### Adding Watch Expressions

1. Open the **Watch** panel (in Debug Panel)
2. Click **Add** or press ++enter++
3. Enter a Python expression
4. Press Enter

Examples:

```python
# Watch simple variables
x + y

# Watch computations
len(data) * 2

# Watch attributes
user.name

# Watch function calls
calculate_total(items)

# Watch conditions
balance > 1000
```

### Updating Watch Values

Watch expressions update automatically after each step:

- **Step Over** - Updates watches
- **Step Into** - Updates watches
- **Step Out** - Updates watches

## :material-call-split: Call Stack

The Call Stack shows the execution path—how you got to the current line:

<!-- SCREENSHOT: call-stack.png -->
<figure markdown>
  ![Call Stack Panel](../../assets/screenshots/ide/call-stack.png){ width="500" }
  <figcaption>Call stack showing function call hierarchy</figcaption>
</figure>

### Reading the Call Stack

From top to bottom:

- **Top** - Current function (where execution is paused)
- **Middle** - Functions that called the current function
- **Bottom** - The entry point (usually module level)

Example:

```
my_function() at line 42    ← Currently here
calculate() at line 30      ← Called my_function
process_data() at line 15   ← Called calculate
<module> at line 5          ← Entry point
```

### Navigating the Stack

Click on a stack frame to:

- View that function's code
- See local variables at that level
- Understand the calling context

!!! info "Stack Navigation"
    Clicking a lower stack frame doesn't change execution—it just shows you that frame's state.

## :material-console: Debug Console

Execute Python expressions in the current debug context:

### Using Debug Console

1. Pause at a breakpoint
2. Open the **Debug Console** tab (in Debug Panel)
3. Type Python code
4. Press Enter to execute

<!-- SCREENSHOT: debug-console.png -->
<figure markdown>
  ![Debug Console](../../assets/screenshots/ide/debug-console.png){ width="500" }
  <figcaption>Debug console for evaluating expressions</figcaption>
</figure>

### What You Can Do

**Inspect Variables**

```python
>>> print(x)
42
>>> type(data)
<class 'list'>
>>> len(items)
5
```

**Evaluate Expressions**

```python
>>> x + y
15
>>> max(scores)
95
>>> data[0]['name']
'Alice'
```

**Call Functions**

```python
>>> calculate_total(items)
1234.56
>>> helper_function(x, y)
'Result: ...'
```

!!! warning "Debug Console Limitations"
    The debug console operates in evaluation mode and cannot change variable values. It is a pure `eval()`, not `exec()`. Variable modification may be supported in future versions.

## :material-alert-circle: Troubleshooting

### Breakpoint Not Hitting

**Problem:** Code doesn't pause at breakpoint

**Solutions:**

1. Verify breakpoint is on an executable line (not comment/blank)
2. Ensure code path reaches that line
3. Check if using Debug mode (++shift+f5++), not Run (++f5++)
4. Remove and re-add the breakpoint

### Variables Not Showing

**Problem:** Variables panel is empty

**Solutions:**

1. Ensure execution is paused (not running)
2. Check if variables exist in current scope
3. Step Into a function to see its local variables

### Step Controls Not Working

**Problem:** F10/F11 don't step

**Solutions:**

1. Verify you're in an active debug session
2. Check if code is paused (not running)
3. Look for keyboard shortcut conflicts

### Debug Console Not Evaluating

**Problem:** Expressions don't execute

**Solutions:**

1. Ensure execution is paused at a breakpoint
2. Check syntax (must be valid Python)
3. Verify variable names are correct

## :material-arrow-right: Next Steps

<div class="grid cards" markdown>

-   :material-console: __Console__

    ---

    Learn to use console output for debugging.

    [:octicons-arrow-right-24: Console Guide](console.md)

-   :material-code-braces: __Editor__

    ---

    Master editor features to write better code.

    [:octicons-arrow-right-24: Editor Guide](editor.md)

-   :material-help-circle: __Troubleshooting__

    ---

    Solutions to common debugging issues.

    [:octicons-arrow-right-24: Troubleshooting](../../reference/troubleshooting.md)

</div>

---

!!! success "Master Debugging"
    The debugger is one of the most powerful tools for understanding and fixing code. Practice using it regularly to become proficient.
