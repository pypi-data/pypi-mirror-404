"""
Display match details for a selected team in the Football Championship Tracker.

This script dynamically displays match data for a clicked team, including columns
such as date, score, opponent, venue. Uses event handling to react to user clicks.
"""

import xpycode
from fetch_championship_data import get_cached_data, fetch_championship_data


def show_match_details(team_name=None, championship_name=None):
    """
    Display match details for a specific team in the Match Details worksheet.
    
    Args:
        team_name: Name of the team to show matches for
                  If None, reads from cell B2 in the Match Details worksheet
        championship_name: Name of the championship
                          If None, reads from Championship Rankings sheet
    """
    ws = xpycode.worksheets.getItem("Match Details")
    ws.activate()

    # Get team name from worksheet if not provided
    if team_name is None:
        team_name = ws.getRange("B2").values[0][0]
        if not team_name or team_name == "Select a team from Championship Rankings":
            xpycode.Messages.showMessageBoxWarning(
                "Please select a team from the Championship Rankings sheet first.",
                "No Team Selected"
            )
            return
    
    # Get championship name if not provided
    if championship_name is None:
        rankings_ws = xpycode.worksheets.getItem("Championship Rankings")
        championship_name = rankings_ws.getRange("B2").values[0][0]
        if not championship_name:
            championship_name = "France"
    
    # Update the team name cell
    ws.getRange("B2").values = team_name
    ws.getRange("B2").format.font.italic = False
    ws.getRange("B2").format.font.bold = True
    
    # Get cached data
    data = get_cached_data(championship_name)
    if data is None:
        data = fetch_championship_data(championship_name)
    
    matches = data["matches"]
    
    # Filter matches for the selected team
    team_matches = [
        match for match in matches
        if match["home_team"] == team_name or match["away_team"] == team_name
    ]
    
    # Sort by match day
    team_matches.sort(key=lambda x: x["match_day"])
    
    # Clear previous data (keep headers)
    if len(team_matches) > 0:
        last_row = 5 + len(team_matches)
        clear_range = ws.getRange(f"A5:H{last_row}")
        clear_range.clear()
    
    # Prepare data for Excel (2D array)
    table_data = []
    for match in team_matches:
        # Determine if team is home or away
        is_home = match["home_team"] == team_name
        opponent = match["away_team"] if is_home else match["home_team"]
        venue = match["venue"] if is_home else f"{opponent} Stadium (Away)"
        
        row = [
            match["match_day"],
            match["date"],
            match["time"],
            match["home_team"],
            match["away_team"],
            "'"+match["score"],
            venue,
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
        _format_match_details_table(ws, start_row, end_row, team_name)
    else:
        ws.getRange("A5").values = "No matches found for this team."
    
    xpycode.Messages.showMessageBoxInfo(
        f"Match details for {team_name} updated successfully!\n\n"
        f"Showing {len(team_matches)} matches.",
        "Match Details Updated"
    )


def _format_match_details_table(ws, start_row, end_row, team_name):
    """
    Apply professional formatting to the match details table.
    
    Args:
        ws: Worksheet object
        start_row: First data row
        end_row: Last data row
        team_name: Name of the selected team (for highlighting)
    """
    # Apply alternating row colors

    to_gray=[]
    to_white=[]

    for row in range(start_row, end_row + 1):
        row_range = ws.getRange(f"A{row}:H{row}")
        if (row - start_row) % 2 == 0:
            to_gray.append(row_range)
        else:
            to_white.append(row_range)
            row_range.format.fill.color = "#FFFFFF"

    if to_gray:
        xpycode.Tools.Union(*to_gray).format.fill.color = "#F2F2F2"
    if to_white:
        xpycode.Tools.Union(*to_white).format.fill.color = "#FFFFFF"


    # Center align numeric columns
    to_align=[]
    for col in ["A", "B", "C", "F", "H"]:
        col_range = ws.getRange(f"{col}{start_row}:{col}{end_row}")
        to_align.append(col_range)
    xpycode.Tools.Union(*to_align).format.horizontalAlignment = "Center"
    
    # Left align text columns
    to_left=[]
    for col in ["D", "E", "G"]:
        col_range = ws.getRange(f"{col}{start_row}:{col}{end_row}")
        to_left.append(col_range)
    xpycode.Tools.Union(*to_left).format.horizontalAlignment = "Left"

    
    # Highlight the selected team's name in home and away columns
    to_hightlight=[]
    for row in range(start_row, end_row + 1):
        # Check home team
        home_cell = ws.getRange(f"D{row}")
        if home_cell.values[0][0] == team_name:
            to_hightlight.append(home_cell)
        
        # Check away team
        away_cell = ws.getRange(f"E{row}")
        if away_cell.values[0][0] == team_name:
            to_hightlight.append(away_cell)

    h_cells=xpycode.Tools.Union(*to_hightlight)
    h_cells.format.font.bold = True
    h_cells.format.fill.color = "#C6EFCE"


    # Color code status column
    to_gray=[]
    to_yellow=[]
    to_blue=[]
    for row in range(start_row, end_row + 1):
        status_cell = ws.getRange(f"H{row}")
        status = status_cell.values[0][0]
        
        if status == "Finished":
            to_gray.append(status_cell)
        elif status == "In Progress":
            to_yellow.append(status_cell)
        elif status == "Scheduled":
            to_blue.append(status_cell)

    xpycode.Tools.Union(*to_gray).format.fill.color = "#D3D3D3"  # Gray
    xpycode.Tools.Union(*to_yellow).format.fill.color = "#FFFF00"  # Yellow
    xpycode.Tools.Union(*to_yellow).format.font.bold = True
    xpycode.Tools.Union(*to_blue).format.fill.color = "#ADD8E6"  # Light blue

    # Apply borders
    data_range = ws.getRange(f"A{start_row}:H{end_row}")
    borders=data_range.format.borders
    borders.getItem("InsideHorizontal").style = "Continuous"
    borders.getItem("InsideVertical").style = "Continuous"
    borders.getItem("EdgeTop").style = "Continuous"
    borders.getItem("EdgeBottom").style = "Continuous"
    borders.getItem("EdgeLeft").style = "Continuous"
    borders.getItem("EdgeRight").style = "Continuous"


