# Package Management Algorithm

Detailed explanation of how XPyCode manages Python packages.

## : material-cog-sync: Installation Logic

XPyCode builds a **real-virtual environment**. 

This means it doesn't create a separate Python environment with its own binaries, core modules, and packages. Instead, on top of the current environment that launched it, XPyCode adds references to additional package locations.

This logic includes packages directly requested by the user (the **Packages List**) and their dependencies. For optimization and to avoid inconsistency, packages already installed in the Python environment are not re-downloaded—XPyCode uses them directly. 

## :material-harddisk: Impacts

Downloaded packages are cached in: 

```
~/. xpycode/. xpycode_packages/
```

!!! warning "Disk Space"
    Duplicating multiple versions of heavy packages can lead to significant disk space usage. 

! !! note "Package Compatibility"
    This methodology allows installation of packages without wheels that may need local setup at installation. Nevertheless, there may be edge cases not well managed.  We are at the early stages of this project—please report any issues you encounter.

## :material-arrow-right:  Next Steps

- [Data Analysis Tutorial](../../tutorials/data-analysis.md) - Use pandas with Excel
- [Package Management Overview](overview.md) - Return to the overview