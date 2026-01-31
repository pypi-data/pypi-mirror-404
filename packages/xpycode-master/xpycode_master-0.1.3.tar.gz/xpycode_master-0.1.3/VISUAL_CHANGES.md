# Visual Changes - ExpandableGroupBox Implementation

## What Changed

The Package Manager now has expandable/collapsible groups that can be maximized to fill the entire area.

## Before (QGroupBox)

```
┌─────────────────────────────────────────┐
│ Workbook: [dropdown]                    │
├─────────────────────────────────────────┤
│ ╔═══════════════════════════════════╗   │
│ ║ Add Package                       ║   │
│ ╚═══════════════════════════════════╝   │
│   [Package search and add controls]     │
├─────────────────────────────────────────┤
│ ╔═══════════════════════════════════╗   │
│ ║ Packages                          ║   │
│ ╚═══════════════════════════════════╝   │
│   [Package table with install status]   │
├─────────────────────────────────────────┤
│ ╔═══════════════════════════════════╗   │
│ ║ Python Paths                      ║   │
│ ╚═══════════════════════════════════╝   │
│   [Paths table]                         │
├─────────────────────────────────────────┤
│ ╔═══════════════════════════════════╗   │
│ ║ Pip Output                        ║   │
│ ╚═══════════════════════════════════╝   │
│   [Console output - limited height]     │
└─────────────────────────────────────────┘

Issues:
- Fixed height sections
- Hard to see full content
- No way to focus on one section
- Scrolling required for large outputs
```

## After (ExpandableGroupBox) - Normal View

```
┌─────────────────────────────────────────┐
│ Workbook: [dropdown]                    │
├─────────────────────────────────────────┤
│ ╔═══════════════════════════════[🗖]═╗   │
│ ║ Add Package                         ║   │
│ ╚═════════════════════════════════════╝   │
│   [Package search and add controls]     │
├─────────────────────────────────────────┤
│ ╔═══════════════════════════════[🗖]═╗   │
│ ║ Packages                            ║   │
│ ╚═════════════════════════════════════╝   │
│   [Package table with install status]   │
├─────────────────────────────────────────┤
│ ╔═══════════════════════════════[🗖]═╗   │
│ ║ Python Paths                        ║   │
│ ╚═════════════════════════════════════╝   │
│   [Paths table]                         │
├─────────────────────────────────────────┤
│ ╔═══════════════════════════════[🗖]═╗   │
│ ║ Pip Output                          ║   │
│ ╚═════════════════════════════════════╝   │
│   [Console output]                      │
└─────────────────────────────────────────┘

New Features:
✅ Maximize button [🗖] in each title bar
✅ Same layout as before (backward compatible)
✅ Hover effect on buttons
✅ Visual consistency maintained
```

## After - Maximized View (Example: Pip Output)

```
┌─────────────────────────────────────────┐
│ Workbook: [dropdown]                    │
├─────────────────────────────────────────┤
│ ╔═══════════════════════════════[🗗]═╗   │
│ ║ Pip Output                          ║   │
│ ╚═════════════════════════════════════╝   │
│                                          │
│ > Installing pandas...                  │
│ > Collecting pandas                     │
│ >   Downloading pandas-2.0.0.whl        │
│ >     100% ████████████████████         │
│ > Collecting numpy>=1.21.0              │
│ >   Using cached numpy-1.24.0.whl       │
│ > Installing collected packages:        │
│ >   numpy, pandas                       │
│ > Successfully installed numpy-1.24.0   │
│ >   pandas-2.0.0                        │
│                                          │
│ (Full height available - no scrolling)  │
│                                          │
│                                          │
│                                          │
│                                          │
└─────────────────────────────────────────┘

Benefits:
✅ Full area for focused content
✅ No scrolling needed
✅ Easy to restore with [🗗] button
✅ Other groups hidden (not deleted)
✅ Workbook selector always visible
```

## Key Visual Elements

### Title Bar
- **Before:** Standard QGroupBox title (text only)
- **After:** Enhanced title bar with maximize button
  - Title aligned left
  - Button aligned right
  - Orange theme (#F17730) maintained
  - 20x20px button with hover effect

### Button Icons
- **Maximize:** 🗖 (window icon)
- **Restore:** 🗗 (overlapping windows)
- Unicode characters for cross-platform support
- Tooltips: "Maximize this section" / "Restore to normal view"

### Interaction
1. **Click maximize [🗖]:**
   - Selected group expands
   - Other groups hide
   - Button changes to [🗗]
   
2. **Click restore [🗗]:**
   - All groups become visible
   - Normal layout restored
   - Button changes to [🗖]

## Color Scheme

```css
Border Color:    rgba(241, 119, 48, 0.3)  /* Semi-transparent orange */
Text Color:      #F17730                  /* XPyCode orange */
Hover BG:        rgba(241, 119, 48, 0.2)  /* Light orange tint */
Button Border:   rgba(241, 119, 48, 0.3)  /* Matching border */
```

## Implementation Details

### Component Structure
```
PackageManager
├── Workbook Dropdown (always visible)
└── ExpandableGroupContainer
    ├── ExpandableGroupBox ("Add Package")
    │   ├── Title Bar [Title] [🗖]
    │   └── Content Frame
    │       └── [Search controls...]
    ├── ExpandableGroupBox ("Packages")
    │   ├── Title Bar [Title] [🗖]
    │   └── Content Frame
    │       └── [Package table...]
    ├── ExpandableGroupBox ("Python Paths")
    │   ├── Title Bar [Title] [🗖]
    │   └── Content Frame
    │       └── [Paths table...]
    └── ExpandableGroupBox ("Pip Output")
        ├── Title Bar [Title] [🗗] (if maximized)
        └── Content Frame
            └── [Console output...]
```

### Signal Flow
```
User Click → ExpandableGroupBox.maximize_requested
           → ExpandableGroupContainer._on_maximize_requested()
           → Hide sibling groups
           → Show only maximized group

User Click → ExpandableGroupBox.restore_requested
           → ExpandableGroupContainer._on_restore_requested()
           → Show all groups
           → Return to normal layout
```

## Backward Compatibility

✅ All existing functionality preserved
✅ Same signals and slots
✅ Same method names and signatures
✅ Layout structure compatible
✅ No breaking changes

## Testing Checklist

Manual testing should verify:
- [ ] All 4 groups visible initially
- [ ] Each group has maximize button
- [ ] Button shows correct icon (🗖)
- [ ] Clicking maximize expands group
- [ ] Other groups hide when one maximized
- [ ] Button changes to restore icon (🗗)
- [ ] Clicking restore shows all groups
- [ ] Button returns to maximize icon (🗖)
- [ ] Workbook selector always visible
- [ ] No visual glitches during transitions
- [ ] Package management still works correctly
- [ ] All buttons and controls functional

## Browser/Platform Compatibility

- **Windows:** ✅ Unicode icons supported
- **macOS:** ✅ Unicode icons supported
- **Linux:** ✅ Unicode icons supported
- **PySide6:** ✅ Required version 6.6.0+

## Future Improvements

Possible enhancements:
1. 🎨 Replace Unicode icons with custom SVG/PNG icons
2. ⌨️ Add keyboard shortcuts (F11 for maximize)
3. 💾 Remember maximized state across sessions
4. ✨ Add smooth transition animations
5. ⚙️ Allow button position customization
6. 🎯 Double-click title to maximize
