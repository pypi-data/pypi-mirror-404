# Cross-Module Code Sample

Learn how to call functions from one in-memory module within another module in the same workbook.

## Codes

**from_module**
```python
def hardcoding_a_return_value():
    return "A First Value"
```

**to_module_good**
```python
def using_another_module_good():
    import from_module
    return from_module.hardcoding_a_return_value()
```

**to_module_bad**
```python
import from_module
def using_another_module_bad():
    return from_module.hardcoding_a_return_value()
```

!!! tip "Import Best Practice"
    Always import in-memory modules **within** functions, not at the module level. This ensures you always get the latest version of the module. You'll understand why this matters in the example below.

Publish the functions **using_another_module_good** and **using_another_module_bad**.

In Excel:
```
=USING_ANOTHER_MODULE_GOOD()  → returns "A First Value"
=USING_ANOTHER_MODULE_BAD()   → returns "A First Value"
```

## Development Action

Now the XPyCode user changes **from_module**:

**from_module**
```python
def hardcoding_a_return_value():
    return "A Second Value"
```

Force function recomputation (++ctrl+alt+f9++).

In Excel:
```
=USING_ANOTHER_MODULE_GOOD()  → returns "A Second Value"
=USING_ANOTHER_MODULE_BAD()   → returns "A First Value"
```

## Why Does This Happen?

XPyCode automatically updates **from_module** when the code changes.

However, in **to_module_bad**, the module itself was not changed, so it wasn't reloaded. The `from_module` variable at the module level still references the old compiled version of the module.

In **to_module_good**, the `from_module` variable inside the function is retrieved from `sys.modules` at each function call, ensuring you always get the latest version.

