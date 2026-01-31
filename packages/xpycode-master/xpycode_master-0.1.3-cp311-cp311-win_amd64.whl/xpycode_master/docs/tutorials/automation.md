# Excel Automation

Automate Excel tasks using Python events and scheduled operations.

## :material-target: Tutorial Goals

- Respond to Excel events automatically
- Validate and transform data on entry
- Create automated reporting workflows
- Build interactive dashboards

## :material-numeric-1-circle: Auto-Calculate Totals

Create an event handler that calculates totals automatically:

```python
import xpycode

def auto_calculate_totals(event):
    """Auto-calculate row totals when data changes."""
    # Get worksheet (Office.js method)
    ws = xpycode.worksheets.getItem(event_args.worksheetId)

    # Only handle Data sheet, columns B and C
    if ws.name != "Data":
        return
    
    if not (event.address.startswith("B") or event.address.startswith("C")):
        return
    
    # Extract row number
    row = int(''.join(filter(str.isdigit, event.address)))
    
    # Get values (returns 2D array when reading)
    qty = ws.getRange(f"B{row}").values[0][0] or 0
    price = ws.getRange(f"C{row}").values[0][0] or 0
    
    # Calculate and write total (can use scalar for single cell)
    total = qty * price
    ws.getRange(f"D{row}").values = total
    
    print(f"Updated total for row {row}: {total}")
```

Register this function for `onChanged` of `Data` worksheet event in Event Manager.

!!! tip "Using Bindings for Targeted Events"
    You can also create a binding on specific cells using the add-in and add an event handler on this binding to trigger the event only when those cells change, providing more targeted event handling.

## :material-numeric-2-circle: Data Validation

Validate input automatically:

```python
import xpycode

def validate_email(event):
    """Validate email addresses as they're entered."""
    # Only validate column D (Email)
    if not event.address.startswith("D"):
        return
    
    # Get worksheet and range
    ws = xpycode.worksheets.getItem(event_args.worksheetId)
    email_cell = ws.getRange(event.address)
    email = email_cell.values[0][0]
    
    if email is None or email == "":
        return
    
    # Simple email validation
    if "@" not in email or "." not in email.split("@")[1]:
        # Invalid email - clear cell and show message
        email_cell.values = [[None]]
        print(f"Invalid email format: {email}")
        
        # Optionally write error to adjacent cell
        row = int(''.join(filter(str.isdigit, event.address)))
        ws.getRange(f"E{row}").values = [["Invalid email"]]
    else:
        # Valid email - clear any previous error
        row = int(''.join(filter(str.isdigit, event.address)))
        ws.getRange(f"E{row}").values = [[""]]
        print(f"Valid email: {email}")
```

Register for `onChanged` of the requested worksheet event in Event Manager.

!!! tip "Using Bindings for Targeted Events"
    You can also create a binding on specific cells using the add-in and add an event handler on this binding to trigger the event only when those cells change, providing more targeted event handling.

## :material-numeric-3-circle: Dynamic Reports

Generate reports automatically:

```python
import xpycode
import pandas as pd
from datetime import datetime

def generate_daily_report(event):
    """Generate report when Summary sheet is activated."""
    # Get worksheet (Office.js method)
    ws = xpycode.worksheets.getItem(event_args.worksheetId)

    if ws.name != "Summary":
        return
    
    # Get worksheets (Office.js method)
    wb = xpycode.workbook
    ws_data = wb.worksheets.getItem("Data")
    ws_summary = wb.worksheets.getItem("Summary")
    
    # Load data (values is 2D array)
    data = ws_data.getRange("A1:D100").values
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Generate summary
    summary = df.groupby('Category').agg({
        'Amount': ['sum', 'mean', 'count']
    }).reset_index()
    
    # Write to summary sheet (2D array for ranges, or scalar for single cells)
    ws_summary.getRange("A1").values = f"Report Generated: {datetime.now()}"
    output_data = [summary.columns.tolist()] + summary.values.tolist()
    ws_summary.getRange("A3").values = output_data
    
    print("Report generated successfully!")
```

Register for `onActivated` event.

## :material-numeric-4-circle: Interactive Dashboard

Create an interactive dashboard:

```python
import xpycode

def update_dashboard(event):
    """Update dashboard charts when selection changes."""
    # Get worksheet (Office.js method)
    ws = xpycode.worksheets.getItem(event_args.worksheetId)

    if ws.name != "Dashboard":
        return
    
    # Get selected category from dropdown cell (values is 2D array)
    selected_category = ws.getRange("B1").values[0][0]
    
    if selected_category is None:
        return
    
    # Load and filter data
    ws_data = xpycode.workbook.worksheets.getItem("Data")
    data = ws_data.getRange("A1:D100").values
    
    # Filter for selected category (data[0] is headers)
    filtered = [row for row in data[1:] if row[0] == selected_category]
    
    # Write filtered data for chart (include headers)
    output_data = [data[0]] + filtered
    ws.getRange("A5").values = output_data
    
    print(f"Dashboard updated for: {selected_category}")
```

Register for `onSelectionChanged` event.

## :material-check-all: Complete Workflow

Combine multiple automation techniques:

```python
import xpycode
import pandas as pd
from datetime import datetime

# 1. Validate inputs
def validate_input(event):
    """Validate data as it's entered."""
    # Validation logic here
    pass

# 2. Auto-calculate
def auto_calculate(event):
    """Calculate dependent values."""
    # Calculation logic here
    pass

# 3. Update summary
def update_summary(event):
    """Update summary when data changes."""
    ws = xpycode.workbook.worksheets.getItem(event.worksheet)
    
    # Recalculate totals (values returns 2D array when reading)
    data = ws.getRange("A2:D100").values
    total = sum(row[3] for row in data if row[3] is not None)
    
    # Write totals (can use scalar for single cells)
    ws.getRange("F2").values = total
    ws.getRange("F1").values = f"Last Updated: {datetime.now()}"

# Register all handlers in Event Manager
```

## :material-arrow-right: Next Steps

- [Events Guide](../user-guide/excel-integration/events.md) - Learn about all event types
- [Excel Objects](../user-guide/excel-integration/objects.md) - Master Excel object manipulation
- [Custom Functions](../user-guide/excel-integration/custom-functions.md) - Create automated functions
