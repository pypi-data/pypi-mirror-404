# Project Explorer

The Project Explorer is your primary navigation tool in XPyCode, providing a hierarchical view of open workbooks, their worksheets, and Python modules.

## :material-file-tree: Overview

<!-- SCREENSHOT: project-explorer-main.png -->
<figure markdown>
  ![Project Explorer](../../assets/screenshots/ide/project-explorer-main.png){ width="200" }
  <figcaption>Project Explorer showing workbooks and modules</figcaption>
</figure>

The Project Explorer displays:

- **Workbooks** - Each open Excel workbook
- **Worksheets** - Excel sheets within each workbook (for reference)
- **Modules** - Python .py files attached to the workbook

## :material-folder-open: Tree Structure

```
📗 Sales_Report.xlsx
├── 🐍 analysis (module)
├── 🐍 report (module)

📗 Budget_2024.xlsx
└── 🐍 budget_calcs (module)
```

### Workbook Node

Top-level items representing open Excel files:

- **Icon**: 📗 Excel workbook icon
- **Name**: Filename of the Excel workbook
- **Expandable**: Click to show modules

### Module Nodes

Python files containing your code:

- **Icon**: 🐍 Python file icon
- **Name**: In-memory Module (e.g., `analysis`)
- **Double-click**: Opens the module in the editor

## :material-plus: Adding Modules

Create new Python modules:

### Context Menu

1. Right-click on a workbook name
2. Select **New Module**
3. Enter module name (without `.py` extension)
4. Press Enter

<!-- SCREENSHOT: add-module.png -->
<figure markdown>
  ![Add Module Context Menu](../../assets/screenshots/ide/add-module.png){ width="500" }
  <figcaption>Adding a module via right-click context menu</figcaption>
</figure>

!!! tip "Module Naming"
    Use descriptive names like `data_analysis`, `helpers`, `calculations`. Follow Python naming conventions (lowercase with underscores).

## :material-file-edit: Modules

### Double-Click

Double-click a module in the tree to open it in the editor.

### Right-Click Menu

Right-click a module:

- **Rename** - Change module name
- **Delete** - Remove module (with confirmation)

### Keyboard Navigation

1. Use arrow keys to navigate the tree
2. Press ++enter++ to open selected module
3. Press ++f2++ to rename (if supported)
4. Press ++delete++ to delete (if supported)

## :material-pencil: Renaming Modules

To rename a module:

1. Right-click the module
2. Select **Rename**
3. Enter new name
4. Press Enter

!!! warning "Rename Effects"
    Renaming a module doesn't automatically update `import` statements in other modules—you'll need to update those manually. However, event handlers and UDFs that reference functions from this module are automatically updated.

## :material-delete: Deleting Modules

To delete a module:

1. Right-click the module
2. Select **Delete**
3. Confirm the deletion

!!! danger "Permanent Deletion"
    Deleted modules cannot be recovered. The code is removed from the business layer permanently. Additionally, event handlers and UDFs that use functions from the deleted module are also removed.

## :material-refresh: Refreshing the Tree

The tree updates automatically when:

- A new workbook is opened in Excel when the Add-in is opened
- A workbook is closed

## :material-folder-multiple: Working with Multiple Workbooks

XPyCode supports multiple workbooks simultaneously:

- Each workbook has its own **Python kernel**
- **Isolated environments** - No shared state
- **Independent packages** - Different workbooks can use different package versions
- **Separate modules** - Module names can duplicate across workbooks

<!-- SCREENSHOT: multiple-workbooks.png -->
<figure markdown>
  ![Multiple Workbooks](../../assets/screenshots/ide/multiple-workbooks.png){ width="200" }
  <figcaption>Project Explorer with multiple open workbooks</figcaption>
</figure>

!!! info "Kernel Isolation"
    When you run code in Workbook A, it doesn't affect the Python environment in Workbook B. This prevents conflicts and allows independent development.

## :material-help-circle: Troubleshooting

### Module Not Appearing

1. Check if the module was created successfully (look for confirmation message)
3. Verify the workbook is still connected (check add-in in Excel Workbook)

### Can't Open Module

1. Ensure the workbook is open in Excel (check add-in in Excel Workbook)
2. Check if the module exists (it may have been deleted)
3. Try closing and reopening the IDE (with **Exit**)
4. Look for error messages in the Console

### Tree Not Updating

2. Restart the IDE (with **Exit**)
3. Verify the XPyCode server is running

## :material-arrow-right: Next Steps

<div class="grid cards" markdown>

-   :material-code-braces: __Code Editor__

    ---

    Learn about Monaco Editor features and capabilities.

    [:octicons-arrow-right-24: Editor Guide](editor.md)

-   :material-console: __Console__

    ---

    View output and errors from your Python code.

    [:octicons-arrow-right-24: Console Guide](console.md)

-   :material-function: __Function Publisher__

    ---

    Publish your Python functions to Excel.

    [:octicons-arrow-right-24: Custom Functions](../excel-integration/custom-functions.md)

</div>

---

!!! success "Efficient Navigation"
    Master the Project Explorer to navigate large projects efficiently. Use keyboard shortcuts and context menus to speed up your workflow.
