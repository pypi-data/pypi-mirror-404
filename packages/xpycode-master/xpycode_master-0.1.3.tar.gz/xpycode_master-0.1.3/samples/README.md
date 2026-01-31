# Football Championship Tracker - XPyCode Sample Scripts

This folder contains a complete sample application demonstrating the Football Championship Tracker built with XPyCode. The application showcases key XPyCode features including object caching, event handling, 2D data streaming, and professional Excel formatting.

## Overview

The Football Championship Tracker is an Excel-based tool that allows users to:
- View championship standings and rankings
- Explore match details for specific teams
- Display all matches for a given match day
- Stream live score updates for ongoing matches

## Files

### 1. `init_workbook.py`
**Purpose**: Initialize the workbook structure with professional formatting.

**Features**:
- Creates three worksheets: "Championship Rankings", "Match Details", and "Match Day View"
- Applies professional formatting (bold headers, colored sections, appropriate column widths)
- Sets up the initial structure for data display

**Usage**:
```python
import init_workbook
init_workbook.init_workbook()
```

### 2. `fetch_championship_data.py`
**Purpose**: Fetch and cache championship data using `xpycode.objects`.

**Features**:
- Generates mock championship data (teams, standings, matches)
- Caches data using `xpycode.objects` for reuse across scripts
- Supports multiple championships (France, England, Spain)

**Usage**:
```python
import fetch_championship_data

# Fetch and cache data
data = fetch_championship_data.fetch_championship_data("France")

# Retrieve cached data
cached_data = fetch_championship_data.get_cached_data("France")

# Clear cache
fetch_championship_data.clear_cache("France")
```

**Key XPyCode Features Demonstrated**:
- `xpycode.Objects.saveObject()` - Cache data for reuse
- `xpycode.Objects.getObject()` - Retrieve cached data
- `xpycode.Objects.clearObject()` - Clear specific cached data

### 3. `show_rankings.py`
**Purpose**: Display championship standings with interactive team selection.

**Features**:
- Displays standings table with position, points, wins, draws, losses, etc.
- Professional formatting with alternating row colors
- Highlights top 3 teams (gold, silver, bronze)
- Event handler for team selection (triggers match details view)

**Usage**:
```python
import show_rankings

# Show rankings for a specific championship
show_rankings.show_rankings("France")

# Or let it read from the worksheet
show_rankings.show_rankings()
```

**Event Handler**:
To enable automatic match details when clicking on a team:
1. Register `on_team_selected` as an event handler for the "Championship Rankings" worksheet
2. Event: `onSelectionChanged`

**Key XPyCode Features Demonstrated**:
- Reading/writing 2D data arrays
- Range formatting (colors, fonts, borders)
- Event handling with `xpycode.EventManager.getEventArgsRange()`

### 4. `show_match_details.py`
**Purpose**: Display match information for a selected team.

**Features**:
- Shows all matches (past and upcoming) for a specific team
- Highlights the selected team's name
- Color-codes match status (finished, in progress, scheduled)
- Displays home/away information with venue details

**Usage**:
```python
import show_match_details

# Show matches for a specific team
show_match_details.show_match_details("Paris Saint-Germain", "France")

# Or let it read from the worksheet
show_match_details.show_match_details()
```

**Key XPyCode Features Demonstrated**:
- Filtering and sorting data
- Conditional formatting based on data values
- Professional table styling

### 5. `show_matches_by_day.py`
**Purpose**: Display all matches for a specific match day.

**Features**:
- Shows all matches scheduled for a particular match day
- Highlights in-progress matches
- Color-codes match status
- Provides match day statistics (finished, in-progress, scheduled)

**Usage**:
```python
import show_matches_by_day

# Show matches for a specific match day
show_matches_by_day.show_matches_by_day(match_day=4, championship_name="France")

# Or let it read from the worksheet
show_matches_by_day.show_matches_by_day()

# Get match day information
info = show_matches_by_day.get_match_day_info("France", 4)
print(f"Total matches: {info['total_matches']}")
print(f"In progress: {info['in_progress']}")
```

**Key XPyCode Features Demonstrated**:
- Reading input parameters from worksheets
- Data filtering and sorting
- Conditional row highlighting

### 6. `streaming_updates.py`
**Purpose**: Implement live score updates using streaming.

**Features**:
- Simulates live score updates for in-progress matches
- Generator-based streaming function for Excel custom functions
- Automatic stop when all matches are finished
- Manual update and continuous streaming modes

**Usage**:

**Single Update**:
```python
import streaming_updates
streaming_updates.update_live_scores_once()
```

**Continuous Streaming** (runs in a loop):
```python
import streaming_updates
streaming_updates.start_live_streaming()

# To stop:
streaming_updates.stop_live_streaming()
```

**As Custom Streaming Function** (publish in Function Publisher):
```python
# Publish GET_LIVE_MATCH_STATUS as a custom function
# Then use in Excel:
# =GET_LIVE_MATCH_STATUS("France", 4)
```

**Key XPyCode Features Demonstrated**:
- Generator functions for streaming data
- Periodic updates with `time.sleep()`
- Custom streaming functions for Excel
- State management with `xpycode.Objects`

## Quick Start Guide

### Step 1: Initialize the Workbook
```python
import init_workbook
init_workbook.init_workbook()
```

### Step 2: Fetch Championship Data
```python
import fetch_championship_data
fetch_championship_data.fetch_championship_data("France")
```

### Step 3: Display Rankings
```python
import show_rankings
show_rankings.show_rankings("France")
```

### Step 4: View Matches by Day
```python
import show_matches_by_day
show_matches_by_day.show_matches_by_day(match_day=4, championship_name="France")
```

### Step 5: Enable Live Updates (Optional)
```python
import streaming_updates
streaming_updates.update_live_scores_once()
```

## Workflow

1. **Initialize**: Run `init_workbook.py` to set up the worksheets
2. **Fetch Data**: Run `fetch_championship_data.py` to load championship information
3. **View Rankings**: Run `show_rankings.py` to see the standings table
4. **Select Team**: Click on a team name in the Championship Rankings sheet
5. **View Team Matches**: The Match Details sheet automatically updates (if event handler is registered)
6. **View Match Day**: Run `show_matches_by_day.py` to see all matches for a specific day
7. **Live Updates**: Use `streaming_updates.py` to get live score updates

## Key XPyCode Concepts Demonstrated

### 1. Object Caching (`xpycode.Objects`)
- Store championship data for reuse
- Avoid redundant data fetching
- Share data between different scripts

### 2. 2D Data Arrays
- All range operations use 2D arrays: `[[row1_col1, row1_col2], [row2_col1, row2_col2]]`
- Single cells can accept scalars or 2D arrays

### 3. Event Handling
- React to user interactions (e.g., clicking on cells)
- Use `xpycode.EventManager.getEventArgsRange()` to get the selected range
- Register handlers through the Event Manager in the IDE

### 4. Streaming Functions
- Generator functions that `yield` data continuously
- Publish as custom functions in Excel
- Automatic updates until completion

### 5. Professional Formatting
- Apply colors, fonts, borders to ranges
- Use conditional formatting based on data values
- Create visually appealing spreadsheets

## Customization

### Using Real Football Data

To use real football data instead of mock data, modify `fetch_championship_data.py`:

```python
import requests

def fetch_championship_data(championship_name="France"):
    # Example using football-data.org API
    api_key = "YOUR_API_KEY"
    competition_id = "FL1"  # Ligue 1 for France
    
    headers = {"X-Auth-Token": api_key}
    
    # Fetch standings
    standings_url = f"https://api.football-data.org/v4/competitions/{competition_id}/standings"
    standings_response = requests.get(standings_url, headers=headers)
    standings_data = standings_response.json()
    
    # Fetch matches
    matches_url = f"https://api.football-data.org/v4/competitions/{competition_id}/matches"
    matches_response = requests.get(matches_url, headers=headers)
    matches_data = matches_response.json()
    
    # Process and cache data
    data = _process_api_data(standings_data, matches_data)
    xpycode.Objects.saveObject(f"championship_data_{championship_name}", data)
    
    return data
```

### Adding More Championships

To support additional championships, update the `teams_data` dictionary in `fetch_championship_data.py`:

```python
teams_data = {
    "France": [...],
    "England": [...],
    "Spain": [...],
    "Germany": [
        {"name": "Bayern Munich", "logo": "FCB", "id": 31},
        # ... more teams
    ],
    "Italy": [
        {"name": "Inter Milan", "logo": "INT", "id": 41},
        # ... more teams
    ],
}
```

## Notes

- **Mock Data**: The current implementation uses mock data for demonstration. In production, integrate with a real football data API.
- **Error Handling**: Add appropriate error handling for API failures, network issues, etc.
- **Rate Limiting**: If using real APIs, implement rate limiting to avoid exceeding API quotas.
- **Authentication**: Secure API keys using environment variables or secure storage.

## Support

For more information about XPyCode:
- [API Reference](../xpycode_master/docs/reference/xpycode-api.md)
- [Tutorials](../xpycode_master/docs/tutorials/)
- [User Guide](../xpycode_master/docs/user-guide/)

## License

This sample application is provided as-is for educational and demonstration purposes.
