"""
Streaming live score updates for the Football Championship Tracker.

This script implements a 2D streaming system for displaying live score updates
while match day games are ongoing. Automatically stops when all matches are finished.

This demonstrates the use of generator functions with xpycode for live updates.
"""

import xpycode
import time
import random
from datetime import datetime


def stream_live_scores(championship_name=None, match_day=None, update_interval=5):
    """
    Stream live score updates for matches in progress.
    
    This is a generator function that yields score updates for ongoing matches.
    It can be published as a custom function in Excel for live streaming.
    
    Args:
        championship_name: Name of the championship
        match_day: Match day number
        update_interval: Seconds between updates (default: 5)
    
    Yields:
        String with match status and score updates
    """
    # Get championship and match day from Match Day View worksheet if not provided
    from fetch_championship_data import get_cached_data
    from show_matches_by_day import get_match_day_info


    ws = xpycode.worksheets.getItem("Match Day View Streaming")
    
    if championship_name is None:
        championship_name = ws.getRange("B2").values[0][0]
        if not championship_name:
            championship_name = "France"
    
    if match_day is None:
        match_day_value = ws.getRange("E2").values[0][0]
        if match_day_value is None or match_day_value == "":
            match_day = 1
        else:
            try:
                match_day = int(match_day_value)
            except (ValueError, TypeError):
                match_day = 1
    
    iteration = 0
    
    while True:
        iteration += 1
        
        # Get match day info
        info = get_match_day_info(championship_name, match_day)
        
        if info is None:
            yield "Error: Championship data not found"
            break
        
        
        # Get cached data
        data = get_cached_data(championship_name)
        if data is None:
            yield [["Error: No data available"]]
            break
        
        to_yield=[]
        
        # Check if all matches are finished
        if info["all_finished"]:
            to_yield.append([f"All matches finished!","","",""])
        else:
            to_yield.append(['Match Day in Progress',"","",""])
        

        matches = data["matches"]
        day_matches = [m for m in matches if m["match_day"] == match_day]
        
        
        # Add details for in-progress matches
        in_progress_matches = [m for m in day_matches if m["status"] == "In Progress"]
        to_yield.append(["Home Team","Score","Away Team","Status"])
        if day_matches:
            for match in day_matches:
                to_yield.append(
                    [match['home_team'],match['score'],match['away_team'],match['status']]
                )
        yield to_yield
        
        # Wait before next update
        time.sleep(update_interval)


def update_live_scores_once():
    """
    Perform a single update of live scores in the Match Day View worksheet.
    
    This function updates the scores for in-progress matches and can be called
    repeatedly from a timer or manual trigger.
    """
    from fetch_championship_data import get_cached_data
    from show_matches_by_day import get_match_day_info

    ws = xpycode.worksheets.getItem("Match Day View Streaming")
    
    # Get championship and match day
    championship_name = ws.getRange("B2").values[0][0]
    match_day = int(ws.getRange("E2").values[0][0])
    
    # Get match day info
    info = get_match_day_info(championship_name, match_day)
    
    if info is None or info["all_finished"]:
        xpycode.Messages.showMessageBoxInfo(
            "All matches are finished. No live updates needed.",
            "Live Updates"
        )
        return
    
    # Get cached data
    data = get_cached_data(championship_name)
    matches = data["matches"]
    day_matches = [m for m in matches if m["match_day"] == match_day]
    
    # Simulate score updates for in-progress matches
    # In a real application, this would fetch from an API
    updated_count = 0
    for i, match in enumerate(day_matches):
        if match["status"] == "In Progress":
            # Simulate a score change (in real app, fetch from API)
            if random.random() > 0.7:  # 30% chance of goal
                scores = match["score"].split(" - ")
                if len(scores) == 2:
                    home_score = int(scores[0])
                    away_score = int(scores[1])
                    
                    # Random goal for either team
                    if random.random() > 0.5:
                        home_score += 1
                    else:
                        away_score += 1
                    
                    match["score"] = f"{home_score} - {away_score}"
                    updated_count += 1
                   


def onLiveUpdateChanges():
    """
    Change the cell color and text to tell the status"
    """
    r=xpycode.worksheets.getItem("Match Day View Streaming").getRange("G2")
    is_live=xpycode.Objects.getObject("streaming_active")
    if is_live:
        r.values="Stop Live"
        r.format.fill.color="#83CCEB"
    else:
        r.values="Start Live"
        r.format.fill.color="#E7E6E6"
    

def start_live_streaming():
    """
    Start continuous live score streaming.
    
    This function demonstrates using a loop to update scores periodically.
    In a real application, you might want to run this in a background thread
    or use Excel's custom streaming functions.
    """
    from show_matches_by_day import get_match_day_info

    if xpycode.Objects.getObject("streaming_active"):
        # Streaming is already runninig
        return

    ws = xpycode.worksheets.getItem("Match Day View")
    
    # Get championship and match day
    championship_name = ws.getRange("B2").values[0][0]
    try:
        match_day = int(ws.getRange("E2").values[0][0])
    except (ValueError, TypeError):
        xpycode.Messages.showMessageBoxError(
            "Invalid match day value. Please enter a number.",
            "Error"
        )
        return
    
    xpycode.Messages.showMessageBoxInfo(
        f"Starting live streaming for Match Day {match_day}...\n\n"
        "Updates will occur every 10 seconds.\n"
        "Run stop_live_streaming() to stop.",
        "Live Streaming Started"
    )
    
    # Save streaming state
    xpycode.Objects.saveObject("streaming_active", True)
    onLiveUpdateChanges()

    update_count = 0
    max_updates = 20  # Stop after 20 updates for safety
    

    while update_count < max_updates:
        # Check if streaming is still active
        if not xpycode.Objects.getObject("streaming_active"):
            break
        
        # Check if all matches finished
        info = get_match_day_info(championship_name, match_day)
        if info and info["all_finished"]:
            xpycode.Messages.showMessageBoxInfo(
                "All matches finished! Streaming stopped.",
                "Live Streaming Complete"
            )
            break
        
        # Update scores
        update_live_scores_once()
        update_count += 1
        
        # Wait before next update
        time.sleep(10)
    
    # Clear streaming state
    xpycode.Objects.saveObject("streaming_active", False)
    onLiveUpdateChanges()

    if update_count >= max_updates:
        xpycode.Messages.showMessageBoxInfo(
            f"Live streaming stopped after {max_updates} updates.\n\n"
            "Run start_live_streaming() again to continue.",
            "Live Streaming Stopped"
        )


def stop_live_streaming():
    """Stop the live streaming process."""
    xpycode.Objects.saveObject("streaming_active", False)
    onLiveUpdateChanges()
    xpycode.Messages.showMessageBoxInfo(
        "Live streaming will stop after the current update.",
        "Stopping Live Streaming"
    )



# Custom streaming function for Excel
def GET_LIVE_MATCH_STATUS(championship_name: str, match_day: int) -> str:
    """
    Streaming custom function for Excel that provides live match updates.
    
    This function can be published as a custom function in Excel.
    It will continuously update the cell with live match information.
    
    Args:
        championship_name: Name of the championship (e.g., "France")
        match_day: Match day number (e.g., 4)
    
    Yields:
        Current match status with live scores
    
    Example:
        In Excel: =GET_LIVE_MATCH_STATUS("France", 4)
    """
    from fetch_championship_data import fetch_championship_data
    # Force to start from scratch the day 
    fetch_championship_data(championship_name)
    for update in stream_live_scores(championship_name, match_day, update_interval=10):
       yield update

