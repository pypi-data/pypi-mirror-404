# Excel Objects

Work with Excel workbooks, worksheets, ranges, and cells using the xpycode module in Python.

## :material-microsoft-excel: The xpycode Module

The `xpycode` module provides embedded objects that mirror [Office.js objects](https://learn.microsoft.com/en-us/javascript/api/excel), enabling seamless Excel integration from Python.

Users can directly access:

- **xpycode.context**: A RequestContext object, the foundation for Office.js interaction with Excel. Note that there is no need to use `context.sync()` or `.load()` methods—synchronization is handled automatically.
- **xpycode.workbook**: The workbook object containing the Python module. Unlike COM objects, Office.js only provides access to the current workbook.
- **xpycode.worksheets**: The worksheet collection of the workbook.

For detailed information on available methods and properties, refer to the [Excel JavaScript API documentation](https://learn.microsoft.com/en-us/javascript/api/excel).



## :material-arrow-right: Next Steps

- [Custom Functions](custom-functions.md) - Publish functions to Excel
- [Events](events.md) - Handle Excel events
- [Data Analysis Tutorial](../../tutorials/data-analysis.md) - Practical examples

---

!!! tip "Office.js Reference"
    For more details on available methods and properties, see the [Excel JavaScript API Reference](https://docs.microsoft.com/en-us/javascript/api/excel). Remember: xpycode mirrors Office.js, and you don't need to call `context.sync()`!
