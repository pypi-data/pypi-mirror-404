"""
Initialize the Football Championship Tracker workbook.

This script sets up the workbook structure with three worksheets:
- Championship Rankings: Display championship standings and team details
- Match Details: Display past and future matches for a selected team
- Match Day View: Display all matches for a selected match day with live updates

Professional formatting is applied to all worksheets.
"""

import xpycode


def init_workbook():
    """
    Set up the Football Championship Tracker workbook structure.
    
    Creates three worksheets with professional formatting:
    1. Championship Rankings - for displaying standings
    2. Match Details - for team-specific match information
    3. Match Day View - for displaying all matches on a specific match day
    """
    wb = xpycode.workbook
    ws_collection = wb.worksheets
    
    # Clear existing worksheets if they exist and create new ones
    sheet_names = ["Championship Rankings", "Match Details", "Match Day View", "Match Day View Streaming"]
    
    # Get existing worksheet names
    existing_count = ws_collection.getCount()
    existing_sheets = []
    for i in range(existing_count):
        ws = ws_collection.getItemAt(i)
        existing_sheets.append(ws.name)
    
    # Create or get worksheets
    for sheet_name in sheet_names:
        if sheet_name in existing_sheets:
            # Clear existing sheet
            ws = ws_collection.getItem(sheet_name)
            used_range = ws.getUsedRange()
            if used_range:
                used_range.clear()
        else:
            # Create new sheet
            ws = ws_collection.add(sheet_name)
    
    # Initialize Championship Rankings sheet
    _init_rankings_sheet()
    
    # Initialize Match Details sheet
    _init_match_details_sheet()
    
    # Initialize Match Day View sheet
    _init_match_day_sheet()
    
    # Activate the Championship Rankings sheet
    rankings_ws = ws_collection.getItem("Championship Rankings")
    rankings_ws.activate()
    
    xpycode.messages.showMessageBoxInfo(
        "Workbook initialized successfully!\n\n"
        "Three worksheets have been created:\n"
        "1. Championship Rankings\n"
        "2. Match Details\n"
        "3. Match Day View\n"
        "4. Match Day View Streaming",
        "Football Championship Tracker"
    )


def _init_rankings_sheet():
    """Initialize the Championship Rankings worksheet."""
    ws = xpycode.worksheets.getItem("Championship Rankings")
    
    # Set up header section
    ws.getRange("A1").values = "Football Championship Tracker"
    ws.getRange("A1").format.font.bold = True
    ws.getRange("A1").format.font.size = 16
    ws.getRange("A1").format.font.color = "#1F4E78"
    
    ws.getRange("A2").values = "Select Championship:"
    ws.getRange("B2").dataValidation.rule = {
        "list":
        {
            "inCellDropDown":True,
            "source":'France,England,Spain'
        }
    }
    ws.getRange("B2").format.fill.color = "#E7E6E6"
    
    # Set up column headers for rankings table
    headers = [["Pos", "Team", "Logo", "Played", "Wins", "Draws", "Losses", "GF", "GA", "GD", "Points"]]
    ws.getRange("A4:K4").values = headers
    
    # Format headers
    header_range = ws.getRange("A4:K4")
    header_range.format.fill.color = "#4472C4"
    header_range.format.font.color = "#FFFFFF"
    header_range.format.font.bold = True
    header_range.format.horizontalAlignment = "Center"
    
    # Set column widths
    ws.getRange("A:A").format.columnWidth = 50   # Pos
    ws.getRange("B:B").format.columnWidth = 150  # Team
    ws.getRange("C:C").format.columnWidth = 80   # Logo
    ws.getRange("D:K").format.columnWidth = 70   # Stats columns
    
    # Add instruction
    ws.getRange("A3").values = "Click on a team name to view match details"
    ws.getRange("A3").format.font.italic = True
    ws.getRange("A3").format.font.size = 9


def _init_match_details_sheet():
    """Initialize the Match Details worksheet."""
    ws = xpycode.worksheets.getItem("Match Details")
    
    # Set up header section
    ws.getRange("A1").values = "Match Details"
    ws.getRange("A1").format.font.bold = True
    ws.getRange("A1").format.font.size = 16
    ws.getRange("A1").format.font.color = "#1F4E78"
    
    ws.getRange("A2").values = "Team:"
    ws.getRange("B2").values = "Select a team from Championship Rankings"
    ws.getRange("B2").format.font.italic = True
    ws.getRange("B2").format.fill.color = "#E7E6E6"
    
    # Set up column headers for match details table
    headers = [["Match Day", "Date", "Time", "Home Team", "Away Team", "Score", "Venue", "Status"]]
    ws.getRange("A4:H4").values = headers
    
    # Format headers
    header_range = ws.getRange("A4:H4")
    header_range.format.fill.color = "#70AD47"
    header_range.format.font.color = "#FFFFFF"
    header_range.format.font.bold = True
    header_range.format.horizontalAlignment = "Center"
    
    # Set column widths
    ws.getRange("A:A").format.columnWidth = 80   # Match Day
    ws.getRange("B:B").format.columnWidth = 100  # Date
    ws.getRange("C:C").format.columnWidth = 70   # Time
    ws.getRange("D:D").format.columnWidth = 150  # Home Team
    ws.getRange("E:E").format.columnWidth = 150  # Away Team
    ws.getRange("F:F").format.columnWidth = 80   # Score
    ws.getRange("G:G").format.columnWidth = 150  # Venue
    ws.getRange("H:H").format.columnWidth = 100  # Status
    
    # Add instruction
    ws.getRange("A3").values = "Past and upcoming matches for the selected team"
    ws.getRange("A3").format.font.italic = True
    ws.getRange("A3").format.font.size = 9


def _init_match_day_sheet():
    """Initialize the Match Day View worksheet."""
    ws = xpycode.worksheets.getItem("Match Day View")
    
    # Set up header section
    ws.getRange("A1").values = "Match Day View"
    ws.getRange("A1").format.font.bold = True
    ws.getRange("A1").format.font.size = 16
    ws.getRange("A1").format.font.color = "#1F4E78"
    
    ws.getRange("A2").values = "Championship:"
    ws.getRange("B2").dataValidation.rule = {
        "list":
        {
            "inCellDropDown":True,
            "source":'France,England,Spain'
        }
    }
    ws.getRange("B2").format.fill.color = "#E7E6E6"
    
    ws.getRange("D2").values = "Match Day:"
    ws.getRange("E2").values = 1  # Default match day
    ws.getRange("E2").format.fill.color = "#E7E6E6"
    
    # Set up column headers for match day table
    headers = [["Time", "Home Team", "Home Logo", "Score", "Away Logo", "Away Team", "Venue", "Status"]]
    ws.getRange("A4:H4").values = headers
    
    # Format headers
    header_range = ws.getRange("A4:H4")
    header_range.format.fill.color = "#FFC000"
    header_range.format.font.color = "#000000"
    header_range.format.font.bold = True
    header_range.format.horizontalAlignment = "Center"
    
    # Set column widths
    ws.getRange("A:A").format.columnWidth = 70   # Time
    ws.getRange("B:B").format.columnWidth = 150  # Home Team
    ws.getRange("C:C").format.columnWidth = 80   # Home Logo
    ws.getRange("D:D").format.columnWidth = 100  # Score
    ws.getRange("E:E").format.columnWidth = 80   # Away Logo
    ws.getRange("F:F").format.columnWidth = 150  # Away Team
    ws.getRange("G:G").format.columnWidth = 150  # Venue
    ws.getRange("H:H").format.columnWidth = 100  # Status
    
    # Add instruction
    ws.getRange("A3").values = "All matches for the selected match day"
    ws.getRange("A3").format.font.italic = True
    ws.getRange("A3").format.font.size = 9

def _init_match_day_streaming_sheet():
    """Initialize the Match Day View worksheet."""
    ws = xpycode.worksheets.getItem("Match Day View Streaming")
    
    # Set up header section
    ws.getRange("A1").values = "Match Day View Streaming"
    ws.getRange("A1").format.font.bold = True
    ws.getRange("A1").format.font.size = 16
    ws.getRange("A1").format.font.color = "#1F4E78"
    
    ws.getRange("A2").values = "Championship:"
    ws.getRange("B2").dataValidation.rule = {
        "list":
        {
            "inCellDropDown":True,
            "source":'France,England,Spain'
        }
    }
    ws.getRange("B2").format.fill.color = "#E7E6E6"
    
    ws.getRange("D2").values = "Match Day:"
    ws.getRange("E2").values = 4  # Default match day
    ws.getRange("E2").format.fill.color = "#E7E6E6"
    
    ws.getRange("G2").values = "Start Live"
    ws.getRange("G2").format.fill.color = "#E7E6E6"
    ws.getRange("G2").format.horizontalAlignment = "Center"

    # Format headers
    header_range = ws.getRange("A5:D5")
    header_range.format.fill.color = "#FFC000"
    header_range.format.font.color = "#000000"
    header_range.format.font.bold = True
    header_range.format.horizontalAlignment = "Center"
    
    # Set column widths
    ws.getRange("A:A").format.columnWidth = 150  # Home Team
    ws.getRange("B:B").format.columnWidth = 100  # Score
    ws.getRange("C:C").format.columnWidth = 150  # Away Team
    ws.getRange("D:D").format.columnWidth = 100  # Status
    ws.getRange("G:G").format.columnWidth = 70  # Status
    


    # Add instruction
    ws.getRange("A3").values = "All matches for the selected match day with live updates"
    ws.getRange("A3").format.font.italic = True
    ws.getRange("A3").format.font.size = 9

    ws.getRange("A4").formulas='=GET_LIVE_MATCH_STATUS(B2,E2)'


    # Apply borders
    data_range = ws.getRange("A6:D9")
    data_range.format.fill.color="#FFFFE0"
    data_range.format.borders.getItem("InsideHorizontal").style = "Continuous"
    data_range.format.borders.getItem("InsideVertical").style = "Continuous"
    data_range.format.borders.getItem("EdgeTop").style = "Continuous"
    data_range.format.borders.getItem("EdgeBottom").style = "Continuous"
    data_range.format.borders.getItem("EdgeLeft").style = "Continuous"
    data_range.format.borders.getItem("EdgeRight").style = "Continuous"
    data_range.format.horizontalAlignment = "Center"


