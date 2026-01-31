# Code Editor

The XPyCode code editor is powered by Microsoft's Monaco Editor—the same editor that powers Visual Studio Code. It provides a professional coding experience with advanced features for Python development.

## :material-file-code: Overview

<!-- SCREENSHOT: editor-main.png -->
<figure markdown>
  ![Monaco Editor](../../assets/screenshots/ide/editor-main.png){ width="800" }
  <figcaption>Monaco Editor with Python code and IntelliSense</figcaption>
</figure>

The editor is embedded directly in the IDE using PySide6's WebEngine, providing:

- Full Monaco Editor feature set
- Seamless integration with Python Language Server
- Real-time syntax checking and diagnostics
- Code completion and signature help
- Hover documentation
- Multi-cursor editing

## :material-feature-search-outline: Core Features

### Syntax Highlighting

Python syntax is highlighted automatically:

- **Keywords** - `def`, `class`, `if`, `for`, etc.
- **Strings** - Different colors for single/double quoted
- **Numbers** - Integers and floats
- **Comments** - Dimmed text for readability
- **Functions** - Method and function names
- **Decorators** - `@property`, `@staticmethod`, etc.

The color scheme adapts to your selected editor theme.

### IntelliSense / Code Completion

Press ++ctrl+space++ or start typing to trigger autocomplete:

<!-- SCREENSHOT: intellisense.png -->
<figure markdown>
  ![IntelliSense](../../assets/screenshots/ide/intellisense.png){ width="600" }
  <figcaption>IntelliSense showing code completion suggestions</figcaption>
</figure>

Completion suggestions include:

- **Variables** - From current scope
- **Functions** - Defined in your module or imported
- **Methods** - On objects (e.g., `list.append()`)
- **Modules** - When typing import statements
- **Keywords** - Python language keywords
- **Snippets** - Code templates (e.g., `def`, `class`, `if`)

!!! tip "Smart Completions"
    The Language Server analyzes your code context and ranks suggestions by relevance. Press ++tab++ or ++enter++ to accept.

### Signature Help

When typing function calls, signature help appears automatically:

```python
calculate_interest(█
```

Shows: `calculate_interest(principal: float, rate: float, years: int) -> float`

<!-- SCREENSHOT: signature-help.png -->
<figure markdown>
  ![Signature Help](../../assets/screenshots/ide/signature-help.png){ width="600" }
  <figcaption>Parameter hints for function calls</figcaption>
</figure>

- Displays parameter names and types
- Shows docstring description
- Highlights current parameter as you type

### Hover Documentation

Hover over any symbol to see:

- Type information
- Docstrings
- Function signatures
- Module documentation

<!-- SCREENSHOT: hover-info.png -->
<figure markdown>
  ![Hover Info](../../assets/screenshots/ide/hover-info.png){ width="600" }
  <figcaption>Hover documentation showing function details</figcaption>
</figure>

Two hover modes available in Settings:

- **Compact** - Brief summary only
- **Detailed** - Full docstring with examples

### Real-Time Diagnostics

Errors and warnings appear as you type:

- **Red underlines** - Syntax errors, undefined names
- **Yellow underlines** - Warnings, unused variables
- **Blue underlines** - Info-level messages

<!-- SCREENSHOT: diagnostics.png -->
<figure markdown>
  ![Diagnostics](../../assets/screenshots/ide/diagnostics.png){ width="600" }
  <figcaption>Real-time error detection with red underlines</figcaption>
</figure>

Hover over underlined code to see the error message:

```python
result = undefined_function()  # Red: 'undefined_function' is not defined
```

<!-- SCREENSHOT: diagnostics_warning.png -->
<figure markdown>
  ![Diagnostics](../../assets/screenshots/ide/diagnostics_warning.png){ width="600" }
  <figcaption>Real-time error detection with red underlines</figcaption>
</figure>

## :material-pencil: Editing Features

### Multi-Cursor Editing

Edit multiple locations simultaneously:

1. Hold ++alt++ and click to add cursors
2. Or use ++ctrl+alt+down++ / ++ctrl+alt+up++ to add cursors above/below
3. Type to edit all locations at once
4. Press ++esc++ to return to single cursor

Perfect for:
- Renaming variables in multiple places
- Adding similar lines
- Bulk editing

### Column (Box) Selection

Select a rectangular block of text:

- Hold ++shift+alt++ and drag with mouse
- Or use ++shift+alt+arrow-keys++

Useful for:
- Editing aligned data
- Adding prefixes/suffixes to multiple lines
- Deleting columns of text

### Find and Replace

**Find** (++ctrl+f++):

- Search in current file
- Case-sensitive/insensitive options
- Whole word matching
- Regular expression support

**Replace** (++ctrl+h++):

- Replace single occurrence
- Replace all occurrences
- Preview before replacing
- Regex capture group support

### Go to Line

Press ++ctrl+g++ and type a line number to jump directly:

```
:42  → Jump to line 42
```

### Code Folding

Collapse code blocks to focus on what matters:

- Click the arrow in the gutter next to a function or class
- Or use ++ctrl+shift+bracketleft++ to fold
- ++ctrl+shift+bracketright++ to unfold

Fold these constructs:
- Function definitions
- Class definitions
- Multi-line strings/comments
- Import groups

!!! tip "Fold Arrow Visibility"
    The fold arrow may not always be visible. Click on the space between the line number and the code at function, class, or other foldable definitions to reveal it.

### Commenting

Toggle line comments:

- ++ctrl+slash++ - Comment/uncomment current line or selection
- Works with multi-line selections

```python
# Commented line
def my_function():  # This will be commented
    pass            # This too
```

### Indentation

Adjust indentation level:

- ++tab++ - Indent line or selection
- ++shift+tab++ - Unindent line or selection

!!! info "Spaces vs Tabs"
    Configure in **Settings → Editor → Insert Spaces**. Default is 4 spaces (PEP 8 compliant).

### Smart Brackets

Auto-closing brackets, quotes, and parentheses:

- Type `(` → Gets `(█)` (cursor in middle)
- Type `"` → Gets `"█"`
- Type `[` → Gets `[█]`

Delete both brackets at once with ++backspace++ if nothing is between them.

### Auto-Indent

Automatic indentation after:

- Function definitions
- Class definitions
- Control structures (`if`, `for`, `while`)
- `try`/`except` blocks

```python
def my_function():
    █  # Cursor automatically indented
```

## :material-format-text: Formatting

### Line Numbers

Always visible in the left gutter. Click a line number to:

- **Single click** - Place cursor on that line
- **F9 on that line** - Toggle breakpoint

### Minimap

A code overview on the right side shows:

- Entire file structure
- Current viewport position
- Error/warning locations

Enable/disable in **Settings → Editor → Show Minimap**.

### Word Wrap

Wrap long lines to avoid horizontal scrolling:

- Enable in **Settings → Editor → Word Wrap**
- Or toggle from editor context menu

Useful for:
- Docstrings
- Long comments
- Reading code without scrolling

### Font Size

Adjust font size:

- **Settings → Editor → Font Size** (permanent)
- ++ctrl+plus++ / ++ctrl+minus++ - Zoom in/out (temporary)
- ++ctrl+0++ - Reset zoom

### Whitespace Visibility

Show spaces and tabs:

- Toggle from editor context menu: **View Whitespace**
- Useful for debugging indentation issues

## :material-keyboard: Keyboard Shortcuts

Essential editor shortcuts:

| Action | Shortcut | Description |
|--------|----------|-------------|
| Find | ++ctrl+f++ | Search in file |
| Replace | ++ctrl+h++ | Find and replace |
| Go to Line | ++ctrl+g++ | Jump to line number |
| Indent | ++tab++ | Indent selection |
| Unindent | ++shift+tab++ | Unindent selection |
| Duplicate Line | ++shift+alt+down++ | Copy line down |
| Move Line | ++alt+up/down++ | Move line up/down |
| Delete Line | ++ctrl+shift+k++ | Delete entire line |
| Multi-cursor | ++alt+click++ | Add cursor |
| Select All Occurrences | ++ctrl+shift+l++ | Multi-select word |
| Trigger Suggest | ++ctrl+space++ | Show completions |

## :material-cog: Editor Settings

Configure the editor through **File → Settings → Editor**:

### Tab Size

Number of spaces per indentation level:

- Default: **4** (PEP 8 standard)
- Range: 2-8

### Insert Spaces

Use spaces instead of tab characters:

- Default: **Enabled** (recommended for Python)
- When disabled: Uses actual tab characters

### Word Wrap

Wrap long lines:

- Default: **Disabled**
- Enable for better readability without horizontal scrolling

### Minimap

Code overview sidebar:

- Default: **Enabled**
- Disable to maximize editing space

<!-- SCREENSHOT: editor-themes.png -->
<figure markdown>
  ![Editor Themes](../../assets/screenshots/ide/editor-settings.png){ width="400" }
  <figcaption>Different editor themes: VS Dark, VS Light, High Contrast</figcaption>
</figure>

## :material-link: Integration Features

### Breakpoint Support

Click in the gutter or press ++f9++ to toggle breakpoints:

- **Red dot** - Active breakpoint
- Code pauses here during debugging
- Breakpoints are module-specific

### Current Execution Line

During debugging, the current line is highlighted:

- **Yellow background** - Current execution position
- Automatically scrolls into view
- Updates as you step through code

### Excel Integration

The editor knows about the `xpycode` module:

```python
import xpycode

def thisIsATest():
    # IntelliSense works for xpycode.workbook
    wb = xpycode.workbook  # Autocomplete available
    ws = wb.worksheets.getActiveWorksheet()  # Office.js methods
```

The Language Server includes type stubs for the xpycode module, providing accurate completions and type checking.

## :material-alert-circle: Troubleshooting

### Completions Not Working or Incorrect Syntax Highlighting

1. Ensure code is syntactically valid
2. Try restarting the Kernel
3. Restart the IDE (use **File → Exit** and reopen via the Add-In)

### Slow Typing Response

1. Disable minimap if file is very large
2. Close unused tabs
3. Reduce font size (renders faster)
4. Check if diagnostics are overwhelming the system

## :material-arrow-right: Next Steps

<div class="grid cards" markdown>

-   :material-file-tree: __Project Explorer__

    ---

    Learn to organize and navigate your Python modules.

    [:octicons-arrow-right-24: Project Explorer](project-explorer.md)

-   :material-bug: __Debugging__

    ---

    Master debugging with breakpoints and variable inspection.

    [:octicons-arrow-right-24: Debugging Guide](debugging.md)

-   :material-keyboard: __Keyboard Shortcuts__

    ---

    Complete reference of all keyboard shortcuts.

    [:octicons-arrow-right-24: Shortcuts Reference](../../reference/keyboard-shortcuts.md)

</div>

---

!!! tip "Learn by Doing"
    The best way to master the editor is through practice. Try different features as you write Python code!
