# Architecture Comparison: Before vs After

## Before: Welcome Tab Architecture

```
MainWindow
└── Central Widget: QTabWidget (editor_tabs)
    ├── Tab 0: MonacoEditor [WELCOME] ← Pseudo-tab, skipped in loops
    ├── Tab 1: MonacoEditor [module1.py]
    ├── Tab 2: MonacoEditor [module2.py]
    └── ...

Startup Flow:
1. MainWindow.__init__()
2. _setup_central_widget()
3. editor_tabs = QTabWidget()
4. _add_welcome_tab() ← Creates "WELCOME" tab
5. setCentralWidget(editor_tabs)

Tab Management:
- Add tab: insert at appropriate index, welcome tab stays
- Close tab: if last tab, call _add_welcome_tab() again
- Close all for workbook: if no tabs remain, call _add_welcome_tab()

Problems:
❌ Welcome tab is a pseudo-tab mixed with real editor tabs
❌ Need to skip welcome tab in many loops (minimap, settings, debug)
❌ Special WELCOME_TAB_ID checks throughout codebase
❌ Welcome content is plain Monaco editor (less attractive)
❌ Confusing UX: welcome appears as a closable tab
```

## After: Stacked Widget Architecture

```
MainWindow
└── Central Widget: QStackedWidget (central_stack)
    ├── Index 0: WelcomeWidget ← Dedicated welcome screen
    │   ├── Logo
    │   ├── Getting Started section
    │   ├── Settings button
    │   └── Keyboard shortcuts
    │
    └── Index 1: QTabWidget (editor_tabs)
        ├── Tab 0: MonacoEditor [module1.py]
        ├── Tab 1: MonacoEditor [module2.py]
        └── ...

Startup Flow:
1. MainWindow.__init__()
2. _setup_central_widget()
3. central_stack = QStackedWidget()
4. welcome_widget = WelcomeWidget() ← Separate widget
5. central_stack.addWidget(welcome_widget)    # Index 0
6. editor_tabs = QTabWidget()
7. central_stack.addWidget(editor_tabs)        # Index 1
8. central_stack.setCurrentIndex(0)            # Show welcome
9. setCentralWidget(central_stack)

Tab Management:
- Add tab: switch to index 1 (editor_tabs)
- Close tab: if last tab removed, _on_tab_changed(index=-1) switches to index 0
- Close all for workbook: if no tabs remain, automatic switch to index 0

Benefits:
✅ Clean separation: welcome is not a tab
✅ No special handling needed in loops
✅ Fewer WELCOME_TAB_ID checks
✅ Attractive custom welcome widget
✅ Clear UX: welcome is a separate screen, not a tab
```

## Key Method Changes

### `_setup_central_widget()`

**Before** (11 lines):
```python
def _setup_central_widget(self):
    """Setup the central editor tab widget."""
    self.editor_tabs = QTabWidget()
    self.editor_tabs.setTabsClosable(True)
    self.editor_tabs.setMovable(True)
    self.editor_tabs.tabCloseRequested.connect(self._close_editor_tab)
    self.editor_tabs.currentChanged.connect(self._on_tab_changed)
    
    self._add_welcome_tab()  # Add welcome pseudo-tab
    
    self.setCentralWidget(self.editor_tabs)
```

**After** (22 lines):
```python
def _setup_central_widget(self):
    """Setup the central widget with stacked layout for welcome/editor views."""
    # Create the stacked widget as central widget
    self.central_stack = QStackedWidget()
    
    # Index 0: Welcome Widget
    self.welcome_widget = WelcomeWidget()
    self.welcome_widget.open_settings_requested.connect(self._open_settings_dialog)
    self.central_stack.addWidget(self.welcome_widget)
    
    # Index 1: Editor Tabs
    self.editor_tabs = QTabWidget()
    self.editor_tabs.setTabsClosable(True)
    self.editor_tabs.setMovable(True)
    self.editor_tabs.tabCloseRequested.connect(self._close_editor_tab)
    self.editor_tabs.currentChanged.connect(self._on_tab_changed)
    self.central_stack.addWidget(self.editor_tabs)
    
    # Start with welcome widget (index 0)
    self.central_stack.setCurrentIndex(0)
    
    self.setCentralWidget(self.central_stack)
```

### `_on_tab_changed(index)`

**Before** (22 lines):
```python
def _on_tab_changed(self, index: int):
    """Handle tab change events to sync Project Explorer selection."""
    if not hasattr(self, 'project_explorer'):
        return
    
    if index < 0:
        return
    
    tab_widget = self.editor_tabs.widget(index)
    if not isinstance(tab_widget, MonacoEditor):
        return
    
    workbook_id = tab_widget.workbook_id
    if not workbook_id or workbook_id == self.WELCOME_TAB_ID:  # Skip welcome tab
        self.project_explorer.clearSelection()
        return
    
    module_name = self.editor_tabs.tabText(index)
    self._select_module_in_project_explorer(workbook_id, module_name)
```

**After** (28 lines):
```python
def _on_tab_changed(self, index: int):
    """
    Handle tab change events.
    Switches central stack between welcome widget (when no tabs) and editor tabs.
    """
    # Switch stack based on whether we have tabs
    if index == -1:
        # No tabs - show welcome widget
        self.central_stack.setCurrentIndex(0)
        return
    else:
        # Has tabs - show editor tabs
        self.central_stack.setCurrentIndex(1)
    
    # Safety check: Project explorer might not be initialized yet
    if not hasattr(self, 'project_explorer'):
        return
    
    tab_widget = self.editor_tabs.widget(index)
    if not isinstance(tab_widget, MonacoEditor):
        return
    
    workbook_id = tab_widget.workbook_id
    if not workbook_id:  # No need to check WELCOME_TAB_ID
        self.project_explorer.clearSelection()
        return
    
    module_name = self.editor_tabs.tabText(index)
    self._select_module_in_project_explorer(workbook_id, module_name)
```

### `_close_editor_tab(index)`

**Before** (11 lines):
```python
def _close_editor_tab(self, index: int):
    """Close an editor tab."""
    if self.editor_tabs.count() > 1:
        self.editor_tabs.removeTab(index)
    else:
        # If it's the last tab, close it and re-open the welcome tab
        self.editor_tabs.removeTab(index)
        self._add_welcome_tab()  # Re-add welcome pseudo-tab
```

**After** (6 lines):
```python
def _close_editor_tab(self, index: int):
    """Close an editor tab."""
    self.editor_tabs.removeTab(index)
    # Note: _on_tab_changed will be called automatically with index=-1
    # when the last tab is closed, which will show the welcome widget
```

### `_toggle_minimap()`

**Before** (8 lines with skip logic):
```python
def _toggle_minimap(self):
    """Toggle minimap visibility for all editors except welcome tab."""
    self._minimap_visible = self.minimap_action.isChecked()
    
    for i in range(self.editor_tabs.count()):
        tab_widget = self.editor_tabs.widget(i)
        if isinstance(tab_widget, MonacoEditor):
            if tab_widget.workbook_id != self.WELCOME_TAB_ID:  # Skip welcome
                tab_widget.set_minimap_visible(self._minimap_visible)
```

**After** (6 lines without skip logic):
```python
def _toggle_minimap(self):
    """Toggle minimap visibility for all editors."""
    self._minimap_visible = self.minimap_action.isChecked()
    
    for i in range(self.editor_tabs.count()):
        tab_widget = self.editor_tabs.widget(i)
        if isinstance(tab_widget, MonacoEditor):
            tab_widget.set_minimap_visible(self._minimap_visible)  # No skip needed
```

## Code Complexity Reduction

### WELCOME_TAB_ID Checks Removed

**8 methods simplified** by removing `if tab_widget.workbook_id != self.WELCOME_TAB_ID:` checks:
1. `_toggle_minimap()` - minimap visibility
2. `_apply_minimap()` - settings application
3. `_apply_font_size()` - font size settings
4. `_apply_insert_spaces()` - insert spaces settings
5. `_apply_tab_size()` - tab size settings
6. `_apply_word_wrap()` - word wrap settings
7. `_set_debug_state()` - readonly during debug
8. `add_editor_tab()` - applying settings to new tabs

**Result**: ~40 lines of conditional logic removed

### WELCOME_TAB_ID Checks Kept (7 locations)

Defensive checks kept for workbook validation (backward compatibility):
```python
if not workbook_id or workbook_id == self.WELCOME_TAB_ID:
    # Handle case where workbook_id is invalid
```

These checks are in methods that deal with workbook-specific operations:
- Run/debug code
- Language server requests (completion, signature help, hover, diagnostics)
- Breakpoint operations

## Summary Statistics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Central widget type | QTabWidget | QStackedWidget | Changed |
| Welcome implementation | Monaco tab | Custom widget | Improved |
| Lines in main_window.py | - | - | -48 net |
| New files created | 0 | 1 | +267 lines |
| WELCOME_TAB_ID skip checks | 15 | 7 | -8 locations |
| Code complexity | Higher | Lower | Simplified |
| UX quality | Basic | Enhanced | Much better |

## Conclusion

The refactor successfully achieves:
- ✅ Cleaner architecture with proper separation
- ✅ Simplified code with fewer special cases
- ✅ Better UX with styled welcome widget
- ✅ Easier maintenance with modular design
- ✅ Backward compatibility maintained
