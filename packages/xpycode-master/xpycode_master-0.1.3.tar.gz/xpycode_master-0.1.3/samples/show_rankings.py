"""
Display championship rankings in the Football Championship Tracker.

This script displays standings for a user-selected championship with columns
such as position, team, points, wins, draws, losses, etc. When a team is clicked,
it triggers updates in the Match Details worksheet.

Uses event handling to react to user clicks on team names.
"""

import xpycode
import re
from fetch_championship_data import fetch_championship_data, get_cached_data


def show_rankings(championship_name=None):
    """
    Display championship standings in the Championship Rankings worksheet.
    
    Args:
        championship_name: Name of championship to display (e.g., "France", "England")
                          If None, reads from cell B2 in the worksheet
    """
    calculation=xpycode.workbook.application.calculationMode
    xpycode.workbook.application.calculationMode=xpycode.excel.CalculationMode.manual
    ws = xpycode.worksheets.getItem("Championship Rankings")
    
    # Get championship name from worksheet if not provided
    if championship_name is None:
        championship_name = ws.getRange("B2").values[0][0]
        if not championship_name:
            championship_name = "France"
    
    # Update the championship selection cell
    ws.getRange("B2").values = championship_name
    
    # Get cached data or fetch new data
    data = get_cached_data(championship_name)
    if data is None:
        data = fetch_championship_data(championship_name)
    
    standings = data["standings"]
    
    # Clear previous data (keep headers)
    if len(standings) > 0:
        clear_range = ws.getRange("A5").getResizedRange(len(standings)-1,10)
        clear_range.clear()
    
    # Prepare data for Excel (2D array)
    table_data = []
    for standing in standings:
        row = [
            standing["position"],
            standing["team"],
            standing["logo"],
            standing["played"],
            standing["wins"],
            standing["draws"],
            standing["losses"],
            standing["goals_for"],
            standing["goals_against"],
            standing["goal_difference"],
            standing["points"],
        ]
        table_data.append(row)
    
    # Write data to worksheet
    if table_data:
        start_row = 5
        end_row = start_row + len(table_data) - 1
        data_range = ws.getRange("A5").getResizedRange(len(table_data)-1,10)
        data_range.values = table_data
        
        # Apply formatting
        _format_standings_table(ws, start_row, end_row)
    
    xpycode.Messages.showMessageBoxInfo(
        f"Rankings for {championship_name} updated successfully!\n\n"
        f"Click on a team name to view match details.",
        "Rankings Updated"
    )
    xpycode.workbook.application.calculationMode=calculation
    

def _format_standings_table(ws, start_row, end_row):
    """
    Apply professional formatting to the standings table.
    
    Args:
        ws: Worksheet object
        start_row: First data row
        end_row: Last data row
    """
    # Apply alternating row colors

    to_white=[]
    to_gray=[]


    for row in range(start_row, end_row + 1):
        row_range = ws.getRange(f"A{row}:K{row}")
        if (row - start_row) % 2 == 0:
            to_gray.append(row_range)
        else:
            to_white.append(row_range)
    
    
    if to_gray:
        r_gray=xpycode.Tools.Union(*to_gray)
        r_gray.format.fill.color="#F2F2F2"
    if to_white:
        r_white=xpycode.Tools.Union(*to_white)
        r_white.format.fill.color="#FFFFFF"
    

    # Center align numeric columns
    numeric_cols = ["A", "D", "E", "F", "G", "H", "I", "J", "K"]
    to_align=[]
    for col in numeric_cols:
        col_range = ws.getRange(f"{col}{start_row}:{col}{end_row}")
        to_align.append(col_range)
    xpycode.Tools.Union(*to_align).format.horizontalAlignment = "Center"
    
    # Left align text columns
    text_cols = ["B", "C"]
    to_left=[]
    for col in text_cols:
        col_range = ws.getRange(f"{col}{start_row}:{col}{end_row}")
        to_left.append(col_range)
    xpycode.Tools.Union(*to_left).format.horizontalAlignment = "Left"
    
    # Highlight top 3 teams
    if end_row >= start_row + 2:
        top3_range = ws.getRange(f"A{start_row}:K{start_row + 2}")
        top3_range.format.font.bold = True
        
        # Gold for 1st
        ws.getRange(f"A{start_row}:K{start_row}").format.fill.color = "#FFD700"
        # Silver for 2nd
        ws.getRange(f"A{start_row + 1}:K{start_row + 1}").format.fill.color = "#C0C0C0"
        # Bronze for 3rd
        ws.getRange(f"A{start_row + 2}:K{start_row + 2}").format.fill.color = "#CD7F32"
    
    # Apply borders
    data_range = ws.getRange(f"A{start_row}:K{end_row}")
    borders=data_range.format.borders
    borders.getItem("InsideHorizontal").style = "Continuous"
    borders.getItem("InsideVertical").style = "Continuous"
    borders.getItem("EdgeTop").style = "Continuous"
    borders.getItem("EdgeBottom").style = "Continuous"
    borders.getItem("EdgeLeft").style = "Continuous"
    borders.getItem("EdgeRight").style = "Continuous"


def on_team_selected(event):
    """
    Event handler for when a team is clicked in the rankings table.
    
    This function is meant to be registered as a selection changed event handler
    for the Championship Rankings worksheet.
    
    Args:
        event: Event arguments containing worksheetId and address
    """
    # Get the selected range
    selected_range = xpycode.getEventArgsRange(event)
    address = event.address
    
    # Check if the selection is in column B (team names) and row >= 5 (data rows)
    # Address format examples: "B5", "B5:B5", "B5:B10"
    match = re.match(r'^B(\d+)', address)
    if match:
        row_num = int(match.group(1))
        # Only process if row is 5 or greater (data rows start at row 5)
        if row_num >= 5:
            # Get the selected team name
            team_name = selected_range.values[0][0]
            
            if team_name and isinstance(team_name, str):
                # Import show_match_details to trigger the update
                # Note: In a real scenario, you would call the show_match_details function directly
                # For this sample, we'll update the Match Details sheet
                
                # Get the championship name
                ws = xpycode.worksheets.getItem("Championship Rankings")
                championship_name = ws.getRange("B2").values[0][0]
                
                # Update Match Details sheet
                match_ws = xpycode.worksheets.getItem("Match Details")
                match_ws.getRange("B2").values = team_name
                
                # Import and call show_match_details
                from show_match_details import show_match_details
                show_match_details(team_name, championship_name)


