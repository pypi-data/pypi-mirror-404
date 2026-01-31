# IDE Overview

The XPyCode IDE is a full-featured development environment built specifically for Python-in-Excel workflows. It provides everything you need to write, debug, and manage Python code within your Excel workbooks.

## :material-view-dashboard: Main Window Layout

The IDE uses a flexible dock-based layout with these main components:

<!-- SCREENSHOT: ide-main-layout.png -->
<figure markdown>
  ![IDE Main Layout](../../assets/screenshots/ide/ide-overview.png){ width="800" }
  <figcaption>XPyCode IDE main window with all panels visible</figcaption>
</figure>

### Left Dock: Navigation

The left side houses on panel:

- **Project Explorer** - Navigate workbooks, sheets, and modules

### Right Dock: Utilities

The right side houses multiple tabbed panels:

- **Functions** - Publish Python functions to Excel
- **Packages** - Install and manage Python packages
- **Events** - Configure Excel event handlers
- **Objects** - View and manage Python objects in memory

### Center: Code Editor

The central area displays:

- **Welcome Tab** - Quick start guide and recent files
- **Monaco Editor Tabs** - One tab per open Python module
- Powered by Microsoft's Monaco Editor (same as VS Code)
- Full syntax highlighting, IntelliSense, and diagnostics

### Bottom Dock: Console and Debug

The bottom section contains:

- **Console** - Output, errors, and execution logs
- **Debug Panel** - Variables, call stack, watch expressions, and debug console (visible during debugging)

### Top: Menu Bar and Toolbar

- **File** - Settings, exit
- **Run** - Run functions
- **Debug** - Start debugging, step controls, breakpoint management
- **View** - Views setup
- **Advanced** - Advanced functions (Restart Kernel, ...)
- **Help** - About, documentation links

## :material-feature-search: Key Features

### 1. Workbook-Centric Organization

Each Excel workbook has its own:

- Python kernel (isolated execution environment)
- Set of Python modules
- Package installation
- Published functions and events
- Objects keeper (save and reuse python objects)

This prevents conflicts between different Excel projects and allows each workbook to have different dependencies.

### 2. Auto-Save

XPyCode automatically saves your code changes with no action required from you, except saving the Excel workbook itself.

!!! info "Auto-Save Behavior"
    Changes are saved to the kernel for immediate use and also saved immediately in Excel. Your code will be persisted when you save the workbook.

### 3. Smart Code Execution

The IDE intelligently determines which function to run based on your cursor position:

- If the cursor is within a function definition, that function is executed
- If not, a warning is displayed in the console

!!! warning "Mandatory Arguments"
    If the selected function has mandatory arguments, an error will be raised. Ensure all required parameters are provided or use default values.

### 4. Integrated Debugging

Full debugging support with:

- Breakpoints (++f9++ to toggle)
- Step over (++f10++), step into (++f11++), step out (++shift+f11++)
- Variable inspection
- Watch expressions
- Call stack navigation

### 5. Real-Time Feedback

As you type, you get:

- **Syntax errors** - Underlined in red
- **Warnings** - Underlined in yellow
- **Code completion** - Suggests functions, variables, methods
- **Hover information** - Shows documentation and type info
- **Signature help** - Parameter hints for functions

## :material-palette: Themes and Appearance

XPyCode supports full theming:

### IDE Themes

- **XPC Dark** (default) - Dark theme optimized for long coding sessions
- **XPC Light** - Light theme for bright environments
- **Midnight blue** - Dark theme using dark blue instead of black
- **High Contrast** - Maximum contrast for accessibility

### Editor Themes

- **VS Dark** - Visual Studio Code dark theme
- **VS Light** - Visual Studio Code light theme
- **High Contrast Black** - Maximum contrast for accessibility
- **High Contrast Light** - Light high contrast theme
- **XPC Midnight blue** - Dark theme using dark blue instead of black

Change themes in **File → Settings → View → Themes & Appearance**.

<!-- SCREENSHOT: theme-switcher.png -->
<figure markdown>
  ![Theme Settings](../../assets/screenshots/ide/theme-switcher.png){ width="400" }
  <figcaption>Theme selection in Settings dialog</figcaption>
</figure>

## :material-monitor: Window Management

### Dock Panels

All panels can be:

- **Resized** - Drag the splitters between panels
- **Closed** - Click the X button (reopen from View menu)
- **Moved** - Drag the title bar to dock elsewhere
- **Floated** - Undock to create floating windows
- **Tabbed** - Combine multiple panels in one dock area

### Tab Management

Editor tabs support:

- **Multiple files open** - Switch between modules with ++ctrl+tab++

## :material-cog-outline: Quick Actions

The toolbar provides one-click access to common operations:

| Icon | Action | Shortcut | Description |
|------|--------|----------|-------------|
| ▶️ | Run | ++f5++ / ++ctrl+r++ | Execute current code |
| 🐛 | Debug | ++shift+f5++ | Start debugging |


## :material-file-tree: Project Structure

XPyCode organizes code hierarchically:

```
 📗 WorkbookName.xlsx
  ├── 🐍 module1.
  ├── 🐍 module2.
  └── 🐍 helpers.
```

- **Workbooks** - Top-level items (one per open Excel file)
- **Modules** - Python in-memory modules containing your code

## :material-keyboard-variant: Keyboard Shortcuts

Essential shortcuts for efficient coding:

| Action | Shortcut |
|--------|----------|
| Run code | ++f5++ or ++ctrl+r++ |
| Debug code | ++shift+f5++ |
| Toggle breakpoint | ++f9++ |
| Step over | ++f10++ |
| Step into | ++f11++ |
| Step out | ++shift+f11++ |
| Continue | ++shift+f5++ |
| Find | ++ctrl+f++ |
| Replace | ++ctrl+h++ |
| Go to line | ++ctrl+g++ |

See the complete [Keyboard Shortcuts Reference](../../reference/keyboard-shortcuts.md) for all shortcuts.

## :material-puzzle: Extensions and Integrations

### Language Server Protocol

XPyCode includes a Python Language Server for:

- Real-time linting with pyflakes
- Advanced code completion with Jedi
- Go to definition
- Find references
- Symbol search

### Monaco Editor

The code editor is powered by Monaco Editor (from VS Code):

- Multi-cursor editing
- Column selection
- Rich IntelliSense
- Bracket matching
- Code folding
- Minimap (optional)

## :material-speedometer: Performance Tips

### For Large Modules

- Use code folding to collapse functions
- Disable minimap if it slows rendering: **Settings → Editor → Minimap**
- Split large modules into smaller, focused files

### For Many Workbooks

- Close workbooks you're not actively using
- Each workbook has its own kernel, which uses memory
- The IDE shows only open workbooks

## :material-arrow-right: Next Steps

Explore each IDE component in detail:

<div class="grid cards" markdown>

-   :material-code-braces: __Code Editor__

    ---

    Deep dive into Monaco Editor features and capabilities.

    [:octicons-arrow-right-24: Editor Guide](editor.md)

-   :material-file-tree: __Project Explorer__

    ---

    Learn to navigate and organize your Python modules.

    [:octicons-arrow-right-24: Project Explorer](project-explorer.md)

-   :material-console: __Console__

    ---

    Understanding console output and log filtering.

    [:octicons-arrow-right-24: Console Guide](console.md)

-   :material-bug: __Debugging__

    ---

    Master the debugger with breakpoints and inspection.

    [:octicons-arrow-right-24: Debugging Guide](debugging.md)

</div>

---

!!! question "Need Help?"
    If you encounter issues, check the [Troubleshooting Guide](../../reference/troubleshooting.md) or consult the specific component guides above.
