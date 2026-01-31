# xpycode API Reference

## Overview

The `xpycode` module provides Python access to Excel through an API that mirrors Microsoft's Office.js Excel API. If you're familiar with Office.js, you'll feel right at home.

**Key difference from Office.js JavaScript:** You don't need to call `context.sync()` - xpycode handles synchronization automatically.

## Module Entry Points

```python
import xpycode

xpycode.workbook      # Excel.Workbook - the active workbook
xpycode.worksheets    # Excel.WorksheetCollection - shortcut to workbook.worksheets
xpycode.context       # Excel.RequestContext (rarely needed)
```

## Working with Workbooks

```python
# Get workbook properties
name = xpycode.workbook.name

# Access worksheets collection
worksheets = xpycode.workbook.worksheets
```

## Working with Worksheets

```python
# Get active worksheet
ws = xpycode.workbook.worksheets.getActiveWorksheet()

# Get worksheet by name
ws = xpycode.workbook.worksheets.getItem("Sheet1")

# Get worksheet by index (0-based)
ws = xpycode.workbook.worksheets.getItemAt(0)

# Get worksheet name
print(ws.name)

# Add a new worksheet
new_ws = xpycode.workbook.worksheets.add("NewSheet")
```

## Working with Ranges

```python
# Get a range from worksheet
ws = xpycode.workbook.worksheets.getActiveWorksheet()

# Single cell
cell = ws.getRange("A1")

# Range of cells
range_obj = ws.getRange("A1:C10")

# Get range address
print(range_obj.address)

# Read values (returns 2D array)
values = range_obj.values
# Example: [["Header1", "Header2"], [1, 2], [3, 4]]

# Write values (2D array for ranges)
range_obj.values = [["Hello", "World"]]

# Single cell write (can use scalar or 2D array)
cell.values = 42  # Scalar works for single cells
# or: cell.values = [[42]]  # 2D array also works

# Get range dimensions
row_count = range_obj.rowCount
col_count = range_obj.columnCount
```

## Working with Tables

```python
# Get tables collection
tables = ws.tables

# Get table by name
table = ws.tables.getItem("MyTable")

# Get table range
table_range = table.getRange()
data = table_range.values
```

## Event Arguments Helper

For event handlers, use `getEventArgsRange()` to get the Range object:

```python
import xpycode

def on_selection_changed(event_args):
    # Get the Range object from event arguments
    selected_range = xpycode.EventManager.getEventArgsRange(event_args)
    
    # Now use Office.js Range methods
    values = selected_range.values
    address = selected_range.address
    print(f"Selected {address}: {values}")
```

## Utility Functions

### Object Storage
```python
# Save objects between executions
xpycode.Objects.saveObject("my_data", [1, 2, 3])
data = xpycode.Objects.getObject("my_data")
xpycode.Objects.clearObject("my_data")
xpycode.Objects.clearAllObjects()
```

### Message Boxes
```python
xpycode.Messages.showMessageBox("Hello!", "Title")
xpycode.Messages.showMessageBoxInfo("Information message")
xpycode.Messages.showMessageBoxWarning("Warning message")
xpycode.Messages.showMessageBoxError("Error message")
```

## Type Hints

xpycode includes type stubs for IDE autocompletion. You can use type hints:

```python
from xpycode import Excel

def process_range(ws: Excel.Worksheet) -> None:
    range_obj: Excel.Range = ws.getRange("A1:B10")
    values = range_obj.values
    # ...
```

## :material-code-braces: Code Examples

### Read and Write

```python
import xpycode

def read_and_write():
    # Get active sheet
    ws = xpycode.workbook.worksheets.getActiveWorksheet()

    # Read single cell (returns 2D array)
    value = ws.getRange("A1").values[0][0]

    # Write single cell (can use scalar or 2D array)
    ws.getRange("B1").values = "Hello, Excel!"  # Scalar for single cell
    # or: ws.getRange("B1").values = [["Hello, Excel!"]]  # 2D array also works

    # Read range (returns 2D array)
    data = ws.getRange("A1:C10").values

    # Write range (must be 2D array)
    ws.getRange("E1").values = [[1, 2], [3, 4], [5, 6]]
```

### Work with DataFrames

```python
import pandas as pd
import xpycode

def work_with_dataframe():
    # Read from Excel
    ws = xpycode.workbook.worksheets.getActiveWorksheet()
    data = ws.getRange("A1:D100").values

    # Create DataFrame (first row is headers)
    df = pd.DataFrame(data[1:], columns=data[0])

    # Process data
    df_filtered = df[df['Score'] > 80]

    # Write back to Excel
    ws.getRange(f"F1:I{len(output_data)}").getResizedRange(len(df_filtered.index),len(df_filtered.columns)-1).values = df_filtered
```

### Event Handlers

```python
import xpycode

def auto_update(event):
    """Update summary when data changes."""
    # Get the Range object from event arguments
    selected_range = xpycode.EventManager.getEventArgsRange(event)
    
    # Get worksheet
    ws = xpycode.workbook.worksheets.getItem(event.worksheet)
    
    # Get changed cell values
    cell_values = selected_range.values
    
    # Update summary
    ws.getRange("Z1").values = [[f"Last changed: {event.address} = {cell_values}"]]
```

## :material-help-circle: Common Patterns

### Iterate Over Range

```python
# Read range (returns 2D array)
ws = xpycode.workbook.worksheets.getActiveWorksheet()
data = ws.getRange("A1:A10").values

# Iterate
for row in data:
    cell_value = row[0]
    print(cell_value)
```

### Find Last Row

```python
ws = xpycode.workbook.worksheets.getActiveWorksheet()

# Simple approach: check until empty
row = 1
while ws.getRange(f"A{row}").values[0][0] is not None:
    row += 1
last_row = row - 1

print(f"Last row with data: {last_row}")
```

### Bulk Update

```python
ws = xpycode.workbook.worksheets.getActiveWorksheet()

# Prepare data (2D array)
data = [[i, i*2, i*3] for i in range(1, 101)]

# Write in one operation (faster than cell-by-cell)
ws.getRange("A1").getResizedRange(len(data)-1,len(data[0])-1).values = data
```

## Office.js Reference

For complete API documentation, refer to:
- [Excel JavaScript API Reference](https://docs.microsoft.com/en-us/javascript/api/excel)
- [Office.js Overview](https://docs.microsoft.com/en-us/office/dev/add-ins/reference/javascript-api-for-office)

The xpycode API mirrors the Office.js Excel API, so methods and properties documented there apply to xpycode.

**Remember:** Unlike Office.js JavaScript, you don't need to call `context.sync()` - xpycode handles synchronization automatically!

## :material-arrow-right: Related

- [Excel Objects Guide](../user-guide/excel-integration/objects.md) - Detailed object usage
- [Custom Functions](../user-guide/excel-integration/custom-functions.md) - Using xpycode in UDFs
- [Events](../user-guide/excel-integration/events.md) - Event handling patterns
