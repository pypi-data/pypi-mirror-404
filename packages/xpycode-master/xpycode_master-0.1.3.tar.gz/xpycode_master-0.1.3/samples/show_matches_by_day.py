"""
Display matches for a specific match day in the Football Championship Tracker.

This script displays match data for a specific match day within a championship,
including details like home team, away team, score, time. Fetches and displays
data based on user input.
"""

import xpycode
from fetch_championship_data import get_cached_data, fetch_championship_data


def show_matches_by_day(match_day=None, championship_name=None):
    """
    Display all matches for a specific match day in the Match Day View worksheet.
    
    Args:
        match_day: Match day number (1, 2, 3, etc.)
                  If None, reads from cell E2 in the worksheet
        championship_name: Name of the championship
                          If None, reads from cell B2 in the worksheet
    """
    ws = xpycode.worksheets.getItem("Match Day View")
    ws.activate()

    # Get championship name from worksheet if not provided
    if championship_name is None:
        championship_name = ws.getRange("B2").values[0][0]
        if not championship_name:
            championship_name = "France"
    
    # Get match day from worksheet if not provided
    if match_day is None:
        match_day_value = ws.getRange("E2").values[0][0]
        if match_day_value is None or match_day_value == "":
            match_day = 1
        else:
            try:
                match_day = int(match_day_value)
            except (ValueError, TypeError):
                xpycode.Messages.showMessageBoxError(
                    "Invalid match day value. Please enter a number.",
                    "Error"
                )
                return
    
    # Update the worksheet cells
    ws.getRange("B2").values = championship_name
    ws.getRange("E2").values = match_day
    
    # Get cached data
    data = get_cached_data(championship_name)
    if data is None:
        data = fetch_championship_data(championship_name)
    
    matches = data["matches"]
    
    # Filter matches for the selected match day
    day_matches = [
        match for match in matches
        if match["match_day"] == match_day
    ]
    
    # Sort by time
    day_matches.sort(key=lambda x: x["time"])
    
    # Clear previous data (keep headers)
    if len(day_matches) > 0:
        last_row = 5 + len(day_matches)
        clear_range = ws.getRange(f"A5:H{last_row}")
        clear_range.clear()
    
    # Prepare data for Excel (2D array)
    table_data = []
    for match in day_matches:
        row = [
            match["time"],
            match["home_team"],
            match["home_logo"],
            "'"+match["score"],
            match["away_logo"],
            match["away_team"],
            match["venue"],
            match["status"],
        ]
        table_data.append(row)
    
    # Write data to worksheet
    if table_data:
        start_row = 5
        end_row = start_row + len(table_data) - 1
        data_range = ws.getRange(f"A{start_row}:H{end_row}")
        data_range.values = table_data
        
        # Apply formatting
        _format_match_day_table(ws, start_row, end_row)
        
        # Count in-progress matches
        in_progress_count = sum(1 for m in day_matches if m["status"] == "In Progress")
        
        if in_progress_count > 0:
            xpycode.Messages.showMessageBoxInfo(
                f"Match Day {match_day} for {championship_name} updated!\n\n"
                f"Showing {len(day_matches)} matches.\n"
                f"{in_progress_count} match(es) in progress.\n\n"
                f"Consider using streaming_updates.py for live updates.",
                "Match Day Updated"
            )
        else:
            xpycode.Messages.showMessageBoxInfo(
                f"Match Day {match_day} for {championship_name} updated!\n\n"
                f"Showing {len(day_matches)} matches.",
                "Match Day Updated"
            )
    else:
        ws.getRange("A5").values = f"No matches found for Match Day {match_day}."


def _format_match_day_table(ws, start_row, end_row):
    """
    Apply professional formatting to the match day table.
    
    Args:
        ws: Worksheet object
        start_row: First data row
        end_row: Last data row
    """
    # Apply alternating row colors
    for row in range(start_row, end_row + 1):
        row_range = ws.getRange(f"A{row}:H{row}")
        if (row - start_row) % 2 == 0:
            row_range.format.fill.color = "#F2F2F2"
        else:
            row_range.format.fill.color = "#FFFFFF"
    
    # Center align most columns
    for col in ["A", "C", "D", "E", "H"]:
        col_range = ws.getRange(f"{col}{start_row}:{col}{end_row}")
        col_range.format.horizontalAlignment = "Center"
    
    # Left align team name columns
    for col in ["B", "F", "G"]:
        col_range = ws.getRange(f"{col}{start_row}:{col}{end_row}")
        col_range.format.horizontalAlignment = "Left"
    
    # Make score column bold and larger
    score_range = ws.getRange(f"D{start_row}:D{end_row}")
    score_range.format.font.bold = True
    score_range.format.font.size = 12
    
    # Color code status column
    for row in range(start_row, end_row + 1):
        status_cell = ws.getRange(f"H{row}")
        status = status_cell.values[0][0]
        
        if status == "Finished":
            status_cell.format.fill.color = "#D3D3D3"  # Gray
        elif status == "In Progress":
            # Highlight entire row for in-progress matches
            row_range = ws.getRange(f"A{row}:H{row}")
            row_range.format.fill.color = "#FFFFE0"  # Light yellow
            status_cell.format.fill.color = "#FFFF00"  # Yellow
            status_cell.format.font.bold = True
        elif status == "Scheduled":
            status_cell.format.fill.color = "#ADD8E6"  # Light blue
    
    # Apply borders
    data_range = ws.getRange(f"A{start_row}:H{end_row}")
    data_range.format.borders.getItem("InsideHorizontal").style = "Continuous"
    data_range.format.borders.getItem("InsideVertical").style = "Continuous"
    data_range.format.borders.getItem("EdgeTop").style = "Continuous"
    data_range.format.borders.getItem("EdgeBottom").style = "Continuous"
    data_range.format.borders.getItem("EdgeLeft").style = "Continuous"
    data_range.format.borders.getItem("EdgeRight").style = "Continuous"


def get_match_day_info(championship_name=None, match_day=None):
    """
    Get information about a specific match day.
    
    Args:
        championship_name: Name of the championship
        match_day: Match day number
    
    Returns:
        Dictionary with match day statistics
    """
    if championship_name is None:
        ws = xpycode.worksheets.getItem("Match Day View")
        championship_name = ws.getRange("B2").values[0][0]
    
    if match_day is None:
        ws = xpycode.worksheets.getItem("Match Day View")
        try:
            match_day = int(ws.getRange("E2").values[0][0])
        except (ValueError, TypeError):
            xpycode.Messages.showMessageBoxError(
                "Invalid match day value. Please enter a number.",
                "Error"
            )
            return None
    
    data = get_cached_data(championship_name)
    if data is None:
        return None
    
    matches = data["matches"]
    day_matches = [m for m in matches if m["match_day"] == match_day]
    
    finished = sum(1 for m in day_matches if m["status"] == "Finished")
    in_progress = sum(1 for m in day_matches if m["status"] == "In Progress")
    scheduled = sum(1 for m in day_matches if m["status"] == "Scheduled")
    
    return {
        "total_matches": len(day_matches),
        "finished": finished,
        "in_progress": in_progress,
        "scheduled": scheduled,
        "all_finished": in_progress == 0 and scheduled == 0,
    }


