# Welcome to XPyCode

<div style="text-align: center;">
  <img src="assets/icons/xpycode-logo.png" alt="XPyCode Logo" width="200" style="display: none;">
  <!-- Logo placeholder - add logo image to docs/assets/icons/ -->
</div>

**XPyCode** is a powerful Excel-Python integration platform that brings the full power of Python directly into Microsoft Excel. Write, execute, and manage Python code seamlessly within your workbooks with a professional IDE, custom function publishing, comprehensive package management, and real-time debugging capabilities.

## :material-star: Key Features

<div class="grid cards" markdown>

-   :fontawesome-brands-python: __Python in Excel__

    ---

    Execute Python code with full access to Excel objects. Work with workbooks, worksheets, ranges, and more through an intuitive API.

-   :material-code-braces: __Integrated IDE__

    ---

    Monaco-based code editor with IntelliSense, syntax highlighting, code completion, and integrated debugging tools.

-   :material-package-variant: __Package Manager__

    ---

    Install and manage Python packages per workbook with automatic dependency resolution. Isolated environments for each workbook.

-   :material-function-variant: __Custom Functions__

    ---

    Publish Python functions as Excel User Defined Functions (UDFs). Use them like native Excel formulas with full type support.

-   :material-lightning-bolt: __Event Handling__

    ---

    React to Excel events (worksheet changes, selections, calculations) with Python code. Build interactive spreadsheets.

-   :material-bug: __Debugger__

    ---

    Set breakpoints, step through code, inspect variables, and debug your Python scripts directly in the IDE.

-   :material-palette: __Customizable Themes__

    ---

    Dark and light themes for both the IDE and editor. Customize fonts, colors, and layout to match your preferences.

-   :material-cube-outline: __Object Management__

    ---

    Save Python objects in the kernel and reuse them across code executions. Perfect for data analysis workflows.

</div>

## :rocket: Quick Start

Get started with XPyCode in just a few steps:

```bash
# Install XPyCode
pip install xpycode_master

# Launch the server
python -m xpycode_master
```

Then open Excel and access XPyCode through **Add-ins → More AddIns → Shared Folder → XPyCode**.

[Get Started →](getting-started/installation.md){ .md-button .md-button--primary }
[View Tutorials →](tutorials/data-analysis.md){ .md-button }

## :material-application: What Can You Build?

XPyCode enables a wide range of Excel automation and data analysis scenarios:

- **Data Analysis**: Use pandas, numpy, and scikit-learn with Excel data and return result in Excel
- **API Integration**: Fetch data from REST APIs and display in worksheets
- **Custom Calculations**: Build complex financial models with Python libraries
- **Report Automation**: Generate formatted reports from Excel data
- **Machine Learning**: Train models and make predictions within Excel
- **Database Connectivity**: Query SQL databases and load results into Excel

## :material-school: Learning Path

<div class="grid" markdown>

1. **[Installation Guide](getting-started/installation.md)** - Install XPyCode and set up your environment
2. **[Quick Start](getting-started/quick-start.md)** - 5-minute walkthrough of core features
3. **[First Function](getting-started/first-function.md)** - Create and publish your first Excel function
4. **[User Guide](user-guide/ide/overview.md)** - Deep dive into IDE features and capabilities
5. **[Tutorials](tutorials/data-analysis.md)** - Step-by-step practical examples

</div>

## :material-file-document: Documentation Sections

<div class="grid cards" markdown>

-   :material-rocket-launch: __Getting Started__

    ---

    Installation, quick start guide, and creating your first function.

    [:octicons-arrow-right-24: Getting Started](getting-started/installation.md)

-   :material-book-open-variant: __User Guide__

    ---

    Complete guide to IDE features, Excel integration, and package management.

    [:octicons-arrow-right-24: User Guide](user-guide/ide/overview.md)

-   :material-school: __Tutorials__

    ---

    Practical step-by-step tutorials for common use cases.

    [:octicons-arrow-right-24: Tutorials](tutorials/data-analysis.md)

-   :material-book-alphabet: __Reference__

    ---

    Keyboard shortcuts, API reference, and troubleshooting guide.

    [:octicons-arrow-right-24: Reference](reference/keyboard-shortcuts.md)

</div>

## :material-handshake: System Requirements

- **Operating System**: Windows 10/11 (64-bit recommended)
- **Python**: 3.10 or higher
- **Microsoft Excel**: 2016 or later with Office.js Add-in support
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Disk Space**: 500MB for installation plus space for packages

!!! info "Platform Support"
    While XPyCode is primarily designed for Windows, other platforms are enabled but not extensively tested. Community feedback welcome!

## :material-help-circle: Getting Help

- **[Troubleshooting Guide](reference/troubleshooting.md)** - Common issues and solutions
- **[GitHub Issues](https://xpycode.com/issues)** - Report bugs or request features
- **[Contributing](donate/supporting.md)** - Help improve XPyCode

## :material-license: License

XPyCode is licensed under the **MIT License with Commons Clause**. You are free to use, modify, and distribute the software for any purpose, but you may not sell it as a commercial product.

See the [License](about/license.md) page for full details.

---

<div style="text-align: center; margin-top: 2em;">
    <p><strong>Ready to supercharge Excel with Python?</strong></p>
    <p>
        <a href="getting-started/installation" class="md-button md-button--primary">Get Started Now</a>
    </p>
</div>
