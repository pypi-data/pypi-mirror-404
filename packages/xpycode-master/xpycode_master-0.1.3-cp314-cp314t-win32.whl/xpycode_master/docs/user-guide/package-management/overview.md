# Package Management Overview

XPyCode includes a built-in package manager that lets you install and manage Python packages per workbook with automatic dependency resolution.

## :material-package-variant: Key Features

- **Per-Workbook Isolation** - Each workbook has its own packages
- **Out of Python Environment** - Your python environment is not impacted by packages features
- **PyPI Integration** - Search and install from PyPI or another repository
- **Dependency Resolution** - Automatic dependency handling
- **Version Control** - Choose specific package versions
- **Extras Support** - Install with optional dependencies
- **Python Paths** - Manual addition of modules locations
- **Cache** - Local cache for all packages and versions


## :material-dock-left: Package Manager Panel

Access the Package Manager from the left dock:

1. Click the **Packages** tab
2. Search for packages
3. Select version and extras
4. Click **Install/Update**

## :material-magnify: Searching Packages

1. Type package name in search box
2. Click **Search**
3. Browse results
4. Select a package version and potential extras
5. Click **Add to List** to update the **Packages** list

## :material-download: Installing Packages

1. Click **Install/Update** in **Packages** sub-widget
2. Wait for installation to complete

!!! info "Batch Package Resolution"
    The entire packages list is resolved and updated at once. Nothing is installed or changed until the **Install/Update** button is clicked. This allows you to queue multiple package changes before applying them.

Installation progress appears in the Console.

## :material-refresh: Updating Packages

1. Find the installed package or double click on the package in the list
2. Select a newer version
3. Click **Add to List**
4. Click **Install/Update**

## :material-delete: Uninstalling Packages

1. Find the installed package in the list
2. Click **Remove**
3. Click **Install/Update**

## :material-cog: Configuring Package URLs

To configure custom package repositories:

1. Navigate to **File → Settings**
2. Select **Package Management** section
3. Configure the following options:
   - **Pip Settings**: Set custom repository URLs and proxy configuration
   - **API Mappings**: Configure API URLs for package repositories (optional). PyPI provides an API that facilitates metadata retrieval. You can add additional API URLs if they comply with the PyPI format. 


## :material-arrow-right: Next Steps

- [Packages Algorithm](algorithm.md) - Detailed package installation logic
