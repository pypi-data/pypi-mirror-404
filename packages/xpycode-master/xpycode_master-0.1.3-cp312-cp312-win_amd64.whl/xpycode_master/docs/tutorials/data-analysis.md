# Data Analysis with Pandas

Learn to use pandas for data analysis in Excel with this hands-on tutorial.

## :material-target: Tutorial Goals

By the end of this tutorial, you'll be able to:

- Load data from Excel into pandas DataFrames
- Clean and transform data
- Perform statistical analysis
- Write results back to Excel

## :material-numeric-1-circle: Setup

### Install Pandas

1. Open Package Manager
2. Search for "pandas"
3. Install latest version

!!! info "Pre-installed Package"
    This tutorial uses pandas for demonstration purposes. Since pandas is a core XPyCode package, it's already installed by default—no installation needed!

### Create a New Module

1. Right-click your workbook in Project Explorer
2. Select **New Module**
3. Name it `data_analysis`

## :material-numeric-2-circle: Load Data from Excel

```python
import pandas as pd
import xpycode

def load_data_from_excel() -> pd.DataFrame:
    """Load data from active worksheet into a DataFrame.
    
    Returns:
        DataFrame with the loaded data
    """
    # Get active worksheet (Office.js method)
    ws = xpycode.workbook.worksheets.getActiveWorksheet()
    
    # Read data range (assuming headers in row 1)
    # values returns 2D array
    data = ws.getRange("A1:D100").values
    
    # Convert to DataFrame (first row is headers)
    df = pd.DataFrame(data[1:], columns=data[0])
    
    print(f"Loaded {len(df)} rows")
    print(df.head())
    return df
```

## :material-numeric-3-circle: Clean Data

```python
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the data by removing missing values and duplicates.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Cleaned DataFrame
    """
    # Remove missing values
    df = df.dropna()
    
    # Convert data types
    df['Age'] = df['Age'].astype(int)
    df['Score'] = df['Score'].astype(float)
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    print(f"After cleaning: {len(df)} rows")
    return df
```

## :material-numeric-4-circle: Analyze Data

```python
def analyze_data(df: pd.DataFrame) -> dict:
    """Analyze data with descriptive statistics.
    
    Args:
        df: DataFrame to analyze
    
    Returns:
        Dictionary with analysis results
    """
    # Descriptive statistics
    stats = df.describe()
    print(stats)
    
    # Group by and aggregate
    summary = df.groupby('Category').agg({
        'Score': ['mean', 'min', 'max', 'std'],
        'Age': 'mean'
    })
    print(summary)
    
    # Calculate correlations
    corr = df[['Age', 'Score']].corr()
    print(corr)
    
    return {'stats': stats, 'summary': summary, 'corr': corr}
```

## :material-numeric-5-circle: Write Results to Excel

```python
def write_results_to_excel(summary: pd.DataFrame):
    """Write analysis results to Excel.
    
    Args:
        summary: Summary DataFrame to write
    """
    # Get worksheet by name (Office.js method)
    ws_summary = xpycode.workbook.worksheets.getItem("Summary")
    
    # Convert summary to 2D array for writing
    summary_data = summary.reset_index()
    
    # Write to Excel (2D array for ranges)
    ws_summary.getRange("A1").getResizedRange(len(summary_data.index),len(summary_data.columns)-1).values = summary_data
    
    print("Results written to Summary sheet")
```

## :material-lightbulb: Tips

!!! tip "Office.js Range.values Requirements"
    1. The Office.js `Range` object's `values` attribute requires 2-D arrays with the exact size (or accepts a scalar if it represents only one cell)
    2. The `getResizedRange()` method takes "The number of rows and columns by which to **expand**..." — don't confuse it with COM Range object's `Resize` method that takes the size of the future range

## :material-arrow-right: Next Steps

- [API Integration Tutorial](api-integration.md) - Fetch external data
- [Automation Tutorial](automation.md) - Automate Excel tasks
- [Custom Functions](../user-guide/excel-integration/custom-functions.md) - Create pandas-powered functions
