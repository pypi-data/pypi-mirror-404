# Quick Start

This 5-minute guide will help you understand XPyCode's core features and workflow.

## :material-numeric-1-circle: Launch XPyCode

If you haven't already, start the XPyCode server:

```bash
python -m xpycode_master
```

Open Excel and click **Open Console** in the XPyCode ribbon tehn launch the IDE by clicking on **<>**.

<!-- SCREENSHOT: ide-overview.png -->
<figure markdown>
  ![IDE Overview](../assets/screenshots/ide/ide-overview.png){ width="700" }
  <figcaption>XPyCode IDE main window</figcaption>
</figure>

## :material-numeric-2-circle: Create a Python Module

In the Project Explorer (left panel):

1. Right-click on your workbook name
2. Select **New Module**
3. Name it `hello` (don't add a .py exetension)

<!-- SCREENSHOT: add-module.png -->
<figure markdown>
  ![Add Module](../assets/screenshots/ide/add-module.png){ width="300" }
  <figcaption>Creating a new Python module</figcaption>
</figure>

The Monaco editor will open with your new module.

## :material-numeric-3-circle: Write Simple Python Code

Type this code in the editor:

```python
def printHelloAndReturnBonjour():
	"""Print 'Hello' in console and return 'Bonjour'

	Returns:
		Hard coded 'Bonjour' string (Hello in french)
	""" 
	print('Hello')
	return 'Bonjour'
```

!!! tip "IntelliSense Support"
    As you type, you'll see code completion suggestions. Press ++tab++ or ++enter++ to accept them.

## :material-numeric-4-circle: Run Your Code

Execute the code by:

- Pressing ++f5++
- Or clicking the **Run** button in the toolbar
- Or pressing ++ctrl+r++

<!-- SCREENSHOT: run-code.png -->
<figure markdown>
  ![Run Code](../assets/screenshots/ide/run-code.png){ width="700" }
  <figcaption>Running Python code in the IDE</figcaption>
</figure>

The output appears in the Console panel at the bottom:

```
Out: 'Bonjour'
```

!!! success "Code Executed"
    Your Python code runs in an isolated kernel attached to your Excel workbook. Each workbook has its own Python environment.

## :material-numeric-5-circle: Access Excel Objects

Now let's interact with Excel. Update your code:

```python
import xpycode

def write_hello_to_excel():
    """Write a greeting to the active worksheet."""
    # Get the active worksheet (Office.js method)
    ws = xpycode.workbook.worksheets.getActiveWorksheet()
    
    # Write to a cell (single cells can use scalar values)
    ws.getRange("A1").values = "Hello from Python!"
    
    # Read from a cell (returns 2D array)
    cell_values = ws.getRange("A1").values
    print(f"Cell A1 contains: {cell_values[0][0]}")
    
    # Work with ranges (values is 2D array)
    ws.getRange("B1:B5").values = [[1], [2], [3], [4], [5]]
    
    # Read and sum the range
    data = ws.getRange("B1:B5").values
    total = sum(row[0] for row in data)
    print(f"Sum of B1:B5: {total}")
```

Run this code (++f5++) and watch it interact with your Excel worksheet!

<!-- SCREENSHOT: excel-interaction.png -->
<figure markdown>
  ![Excel Interaction](../assets/screenshots/excel/excel-interaction.png){ width="700" }
  <figcaption>Python code writing to Excel cells</figcaption>
</figure>

!!! info "The xpycode Module"
    The `xpycode` module is automatically available in your Python environment. It provides access to Excel through an **Office.js-compatible API**. No `context.sync()` needed!

## :material-numeric-6-circle: Install a Package

Let's install pandas to work with data:

1. Click the **Packages** tab in the left dock
2. Type `pandas` in the search box in **Add Package**
3. Click **Search**
4. Select the latest version
5. Click **Add to List**
6. Click **Install/Update** in **Packages**

!!! note "pandas Already Installed"
    pandas is included in the default requirements, so it's already installed. This example demonstrates the package installation process for other libraries you might need.

<!-- SCREENSHOT: package-manager.png -->
<figure markdown>
  ![Package Manager](../assets/screenshots/ide/package-manager.png){ width="600" }
  <figcaption>Installing pandas through Package Manager</figcaption>
</figure>

Wait for the installation to complete (you'll see progress in the console).

!!! note "Per-Workbook Packages"
    Packages are installed per workbook, not globally. This prevents conflicts between different Excel projects.

## :material-numeric-7-circle: Use Pandas with Excel

Now use pandas in your code:

```python
import pandas as pd
import xpycode

def write_dataframe_to_excel():
    """Write a pandas DataFrame to the active worksheet."""
    # Create a DataFrame
    data = {
        'Name': ['Alice', 'Bob', 'Charlie', 'Diana'],
        'Score': [85, 92, 78, 95],
        'Grade': ['B', 'A', 'C', 'A']
    }
    df = pd.DataFrame(data)
    
    # Write DataFrame to Excel starting at A1 (df is converted to 2D list by xpycode)
    ws = xpycode.workbook.worksheets.getActiveWorksheet()
    ws.getRange("A1").getResizedRange(len(df.index),len(df.columns)-1).values = df
    
    print(f"Wrote {len(df)} rows to Excel")
    print(f"Average score: {df['Score'].mean():.1f}")
```

Run the code (++f5++) to see your data appear in Excel!

<!-- SCREENSHOT: pandas-excel.png -->
<figure markdown>
  ![Pandas and Excel](../assets/screenshots/excel/pandas-excel.png){ width="700" }
  <figcaption>Writing a pandas DataFrame to Excel</figcaption>
</figure>

!!! tip "Pandas Conversion"
    pandas Series and DataFrame objects are automatically converted to 2D arrays (list of lists) when sent to Excel. Column names are included, but index names and values are not.

## :material-numeric-8-circle: Debug Your Code

Let's try debugging:

1. Click ++f9+ to line 15 of your code (where `df = pd.DataFrame(data)` is)
2. A red dot appears - this is a **breakpoint**
3. Press ++shift+f5++ to **Debug** (instead of Run)

<!-- SCREENSHOT: debugging.png -->
<figure markdown>
  ![Debugging](../assets/screenshots/ide/debugging.png){ width="700" }
  <figcaption>Debugging with breakpoints</figcaption>
</figure>

The code execution pauses at your breakpoint. The Debug Panel shows:

- **Variables**: Current values of `data`, `df`, etc.
- **Call Stack**: The execution path
- **Watch**: Custom expressions to monitor

Use the debug controls:

- ++f10++ **Step Over**: Execute the current line
- ++f11++ **Step Into**: Enter function calls
- ++shift+f11++ **Step Out**: Exit current function
- ++shift+f5++ **Continue**: Resume execution

!!! tip "Debug Like a Pro"
    Set breakpoints on lines where you want to inspect state. Use the Watch panel to monitor specific variable expressions.

## :material-numeric-9-circle: Publish a Function to Excel

Now let's make a function available as an Excel formula:

```python
def calculate_tax(amount: float, rate: float = 0.1) -> float:
    """Calculate tax on an amount.
    
    Args:
        amount: The base amount
        rate: Tax rate as decimal (default 10%)
    
    Returns:
        The tax amount
    """
    return amount * rate
```

1. Click the **Functions** tab
2. Click **Add Publication**
3. Select the module and then `calculate_tax` from the list
4. Change the name if you which (default is the function name in capital letter `CALCULATE_TAX`)
5. Set dimension to "Scalar" (it is the default dimension)

<!-- SCREENSHOT: function-publisher.png -->
<figure markdown>
  ![Function Publisher](../assets/screenshots/ide/function-publisher.png){ width="600" }
  <figcaption>Publishing a Python function to Excel</figcaption>
</figure>

Now you can use it in Excel as a formula:

```
=CALCULATE_TAX(100, 0.2)  → 20
=CALCULATE_TAX(500)        → 50 (uses default rate)
```

!!! success "Custom Functions Created"
    Your Python functions are now Excel UDFs! They recalculate automatically when inputs change.

!!! note "Function Publication"
    Functions are published immediately when added to the list. Code modifications are automatically picked up at the next computation—no need to republish. Use the **Sync to Excel** button to force resynchronization if you encounter issues or change a function's signature.

!!! warning "Recomputation Impact"
    Publishing a new function or clicking **Sync to Excel** forces recomputation of all XPyCode functions in the workbook and reinitializes all streaming functions.


## :material-numeric-10-circle: Customize Your Environment

Open settings to personalize XPyCode:

1. Go to **File → Settings**
2. Try different themes:
   - IDE Theme: XPC Dark / XPC Light / And several other themes to suit your preference
   - Editor Theme: VS Dark / VS Light / Plus additional editor themes to match your coding style
3. Adjust font sizes
4. Configure editor behavior (tabs, word wrap, minimap)

<!-- SCREENSHOT: settings-dialog.png -->
<figure markdown>
  ![Settings Dialog](../assets/screenshots/ide/settings-dialog.png){ width="200" }
  <figcaption>Customizing IDE settings</figcaption>
</figure>

## :material-check-all: What You've Learned

In just 5 minutes, you've learned to:

- ✅ Create and run Python modules
- ✅ Access Excel objects from Python
- ✅ Install packages (pandas) per workbook
- ✅ Use pandas to work with Excel data
- ✅ Debug code with breakpoints
- ✅ Publish Python functions as Excel UDFs
- ✅ Customize the IDE appearance

## :material-arrow-right: Next Steps

Ready to go deeper? Here's what to explore next:

<div class="grid cards" markdown>

-   :material-function: __Create Your First Function__

    ---

    Learn function publishing in detail with types, dimensions, and streaming.

    [:octicons-arrow-right-24: First Function](first-function.md)

-   :material-book-open-variant: __User Guide__

    ---

    Comprehensive guide to all IDE features and capabilities.

    [:octicons-arrow-right-24: IDE Overview](../user-guide/ide/overview.md)

-   :material-school: __Tutorials__

    ---

    Hands-on tutorials for real-world scenarios.

    [:octicons-arrow-right-24: Data Analysis Tutorial](../tutorials/data-analysis.md)

-   :material-keyboard: __Keyboard Shortcuts__

    ---

    Master the IDE with keyboard shortcuts reference.

    [:octicons-arrow-right-24: Shortcuts Reference](../reference/keyboard-shortcuts.md)

</div>

---

!!! example "Try This Next"
    Experiment with Excel events! Use the Event Manager to run Python code when cells change. See the [Events Guide](../user-guide/excel-integration/events.md).
