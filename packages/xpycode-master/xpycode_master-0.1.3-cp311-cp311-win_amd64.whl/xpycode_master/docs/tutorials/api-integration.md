# API Integration

Learn to fetch data from REST APIs and display it in Excel.

## :material-target: Tutorial Goals

- Make HTTP requests from Python
- Parse JSON responses
- Write API data to Excel
- Create custom functions that fetch live data

## :material-numeric-1-circle: Setup

### Install Requests

```python
# In Package Manager, install: requests
```

### Create Module

Create `api_functions.py` module.

## :material-numeric-2-circle: Basic API Request

```python
import requests
import xpycode

def fetch_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Fetch currency exchange rate from API."""
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
    
    response = requests.get(url)
    data = response.json()
    
    rate = data['rates'][to_currency]
    return rate
```

## :material-numeric-3-circle: Write to Excel

```python
import requests
import xpycode

def update_exchange_rates():
    """Fetch and update exchange rates in Excel."""
    currencies = ["EUR", "GBP", "JPY", "CAD"]
    ws = xpycode.workbook.worksheets.getActiveWorksheet()
    
    # Write headers (scalars work for single cells)
    ws.getRange("A1").values = "Currency"
    ws.getRange("B1").values = "Rate"
    
    # Fetch and write rates
    for i, currency in enumerate(currencies, start=2):
        rate = fetch_exchange_rate("USD", currency)
        ws.getRange(f"A{i}").values = currency
        ws.getRange(f"B{i}").values = rate
    
    print("Exchange rates updated!")
```

## :material-numeric-4-circle: Publish as Function

Create a custom function:

```python
def GET_EXCHANGE_RATE(from_curr: str, to_curr: str) -> float:
    """Get current exchange rate.
    
    Args:
        from_curr: Source currency code (e.g., "USD")
        to_curr: Target currency code (e.g., "EUR")
    
    Returns:
        Exchange rate
    """
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['rates'][to_curr]
    except Exception as e:
        return f"#N/A: {str(e)}"
```

Publish using Function Publisher as `GET_EXCHANGE_RATE`.

Use in Excel:
```
=GET_EXCHANGE_RATE("USD", "EUR")
```

## :material-numeric-5-circle: Publish as Streaming Function

Create a custom function:

```python
import requests
import datetime
import time

def GET_ISS_POSITION_UNTIL(until):
    """Get the current ISS position repeatedly.

    Args:
        until: A datetime, something convertible to datetime, or None.
               If conversion fails, runs forever.

    Yields:
        dict with latitude, longitude, and timestamp
    """

    # Try to normalize `until` to a datetime
    infinite = False
    if until is None:
        infinite = True
    else:
        try:
            if not isinstance(until, datetime.datetime):
                until = datetime.datetime.fromisoformat(str(until))
        except Exception:
            infinite = True

    while infinite or datetime.datetime.utcnow() < until:
        try:
            url = "http://api.open-notify.org/iss-now.json"
            response = requests.get(url, timeout=5)
            data = response.json()

            position = {
                "latitude": float(data["iss_position"]["latitude"]),
                "longitude": float(data["iss_position"]["longitude"]),
                "timestamp": datetime.datetime.utcfromtimestamp(
                    int(data["timestamp"])
                )
            }

            yield f"{position['latitude']} x {position['longitude']}"

        except Exception as e:
            yield str({"error": str(e)})

        time.sleep(5)
```

Publish using Function Publisher as `GET_ISS_POSITION_UNTIL`.

Use in Excel:
```
=GET_ISS_POSITION_UNTIL("2024-12-31T23:59:59")
```

!!! note "Passing None Values"
    To pass `None` to a Python function from Excel, include the argument position but leave it empty. For example, `=MY_FUNCTION(A1, , B1)` passes `None` as the second argument.

## :material-arrow-right: Next Steps

- [Data Analysis Tutorial](data-analysis.md) - Process API data with pandas
- [Automation Tutorial](automation.md) - Schedule automatic updates
