"""
Fetch championship data for the Football Championship Tracker.

This script fetches championship data including teams, logos, standings, and matches.
Data is cached using xpycode.Objects for reuse across scripts.

Note: This is a demonstration script. In a real application, you would fetch data 
from actual football APIs (e.g., football-data.org, api-football.com).
For this sample, we use mock data.
"""

import xpycode
from datetime import datetime, timedelta
import random
import math

def fetch_championship_data(championship_name="France"):
    """
    Fetch championship data and cache it using xpycode.Objects.
    
    Args:
        championship_name: Name of the championship (e.g., "France", "England", "Spain")
    
    Returns:
        Dictionary containing teams, standings, and matches data
    """
    # In a real application, you would fetch from an API like:
    # response = requests.get(f"https://api.football-data.org/v4/competitions/{competition_id}/standings")
    # data = response.json()
    
    # For this sample, we'll use mock data
    data = _generate_mock_data(championship_name)
    
    # Cache the data using xpycode.Objects
    cache_key = f"championship_data_{championship_name}"
    xpycode.Objects.saveObject(cache_key, data)
    
    xpycode.Messages.showMessageBoxInfo(
        f"Championship data for {championship_name} fetched and cached successfully!",
        "Data Fetch Complete"
    )
    
    return data


def get_cached_data(championship_name="France"):
    """
    Retrieve cached championship data.
    
    Args:
        championship_name: Name of the championship
    
    Returns:
        Cached data dictionary or None if not found
    """
    cache_key = f"championship_data_{championship_name}"
    
    data=xpycode.Objects.getObject(cache_key)
    if data:
        return data
    return fetch_championship_data(championship_name)


def clear_cache(championship_name=None):
    """
    Clear cached championship data.
    
    Args:
        championship_name: Name of championship to clear, or None to clear all
    """
    if championship_name:
        cache_key = f"championship_data_{championship_name}"
        xpycode.Objects.clearObject(cache_key)
        xpycode.Messages.showMessageBoxInfo(
            f"Cache cleared for {championship_name}",
            "Cache Cleared"
        )
    else:
        xpycode.Objects.clearAllObjects()
        xpycode.Messages.showMessageBoxInfo(
            "All cached data cleared",
            "Cache Cleared"
        )


def _generate_mock_data(championship_name):
    """
    Generate mock championship data for demonstration.
    
    In a real application, this would be replaced with actual API calls.
    """
    # Mock teams based on championship
    teams_data = {
        "France": [
            {"name": "Paris Saint-Germain", "logo": "PSG", "id": 1},
            {"name": "Olympique Marseille", "logo": "OM", "id": 2},
            {"name": "AS Monaco", "logo": "ASM", "id": 3},
            {"name": "Olympique Lyonnais", "logo": "OL", "id": 4},
            {"name": "RC Lens", "logo": "RCL", "id": 5},
            {"name": "Lille OSC", "logo": "LOSC", "id": 6},
            {"name": "Stade Rennais", "logo": "SRF", "id": 7},
            {"name": "OGC Nice", "logo": "OGCN", "id": 8},
        ],
        "England": [
            {"name": "Manchester City", "logo": "MCI", "id": 11},
            {"name": "Arsenal", "logo": "ARS", "id": 12},
            {"name": "Liverpool", "logo": "LIV", "id": 13},
            {"name": "Manchester United", "logo": "MUN", "id": 14},
            {"name": "Chelsea", "logo": "CHE", "id": 15},
            {"name": "Tottenham", "logo": "TOT", "id": 16},
            {"name": "Newcastle", "logo": "NEW", "id": 17},
            {"name": "Aston Villa", "logo": "AVL", "id": 18},
        ],
        "Spain": [
            {"name": "Real Madrid", "logo": "RMA", "id": 21},
            {"name": "Barcelona", "logo": "FCB", "id": 22},
            {"name": "Atletico Madrid", "logo": "ATM", "id": 23},
            {"name": "Sevilla", "logo": "SEV", "id": 24},
            {"name": "Real Sociedad", "logo": "RSO", "id": 25},
            {"name": "Real Betis", "logo": "BET", "id": 26},
            {"name": "Villarreal", "logo": "VIL", "id": 27},
            {"name": "Valencia", "logo": "VAL", "id": 28},
        ],
    }
    
    teams = teams_data.get(championship_name, teams_data["France"])
    
    # Generate standings
    standings = []
    for i, team in enumerate(teams):
        # Generate realistic stats
        played = 20
        wins = 15 - i
        draws = min(3 + (i % 3), played - wins)
        losses = played - wins - draws
        goals_for = 35 - (i * 3)
        goals_against = 15 + (i * 2)
        goal_diff = goals_for - goals_against
        points = (wins * 3) + draws
        
        standings.append({
            "position": i + 1,
            "team": team["name"],
            "team_id": team["id"],
            "logo": team["logo"],
            "played": played,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goal_diff,
            "points": points,
        })
    
    # Generate matches
    matches = _generate_mock_matches(teams)
    
    return {
        "championship": championship_name,
        "teams": teams,
        "standings": standings,
        "matches": matches,
        "last_updated": datetime.now().isoformat(),
    }


def round_robin(players):
    '''
    Generate all matches
    '''
    players = list(players)
    if len(players) % 2 != 0:
        players.append(None)  # not needed here, but keeps it generic

    n = len(players)
    rounds = []

    for _ in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            a = players[i]
            b = players[n - 1 - i]
            if a is not None and b is not None:
                round_matches.append([a, b])
        rounds.append(round_matches)

        # rotate players (keep first fixed)
        players = [players[0]] + [players[-1]] + players[1:-1]

    return rounds

def _generate_mock_matches(teams):
    """Generate mock match data."""
    matches = []
    match_id = 1
    
    # Generate matches for the while chamionship
    day_matches_list=round_robin(range(0,8))
    for match_num,match_list in enumerate(day_matches_list):
        match_day=match_num+1
        day_offset = (match_day - 1) * 7  # One week apart
        
        # Create matches (round-robin style)
        for match in match_list:
            home_team = teams[match[0]]
            away_team = teams[match[1]]
                
            # Past matches (match days 1-3) have scores
            is_past = match_day <= 3
            
            # Match day 4 is today (in progress)
            is_today = match_day == 4
            
            match_date = datetime.now() - timedelta(days=day_offset)
            
            if is_past:
                status = "Finished"
                home_score = int(math.sqrt(random.random())*5)
                away_score = int(math.sqrt(random.random())*5)
                score = f"{home_score} - {away_score}"
            elif is_today:
                status = "In Progress"
                home_score = int(math.sqrt(random.random())*2)
                away_score = int(math.sqrt(random.random())*2)
                score = f"{home_score} - {away_score}"
            else:
                status = "Scheduled"
                score = "vs"
            
            matches.append({
                "match_id": match_id,
                "match_day": match_day,
                "date": match_date.strftime("%Y-%m-%d"),
                "time": "20:00" if match[0] % 2 == 0 else "17:00",
                "home_team": home_team["name"],
                "home_team_id": home_team["id"],
                "home_logo": home_team["logo"],
                "away_team": away_team["name"],
                "away_team_id": away_team["id"],
                "away_logo": away_team["logo"],
                "score": score,
                "venue": f"{home_team['name']} Stadium",
                "status": status,
            })
            
            match_id += 1

            match_day2=match_day+7*7

            home_team = teams[match[1]]
            away_team = teams[match[0]]
                
            # Past matches (match days 1-3) have scores
            is_past = match_day2 <= 3
            
            # Match day 4 is today (in progress)
            is_today = match_day2 == 4
            
            match_date = datetime.now() - timedelta(days=day_offset+7*7)
            
            if is_past:
                status = "Finished"
                home_score = int(math.sqrt(random.random())*5)
                away_score = int(math.sqrt(random.random())*5)
                score = f"{home_score} - {away_score}"
            elif is_today:
                status = "In Progress"
                home_score = int(math.sqrt(random.random())*2)
                away_score = int(math.sqrt(random.random())*2)
                score = f"{home_score} - {away_score}"
            else:
                status = "Scheduled"
                score = "vs"
            
            matches.append({
                "match_id": match_id,
                "match_day": match_day2,
                "date": match_date.strftime("%Y-%m-%d"),
                "time": "20:00" if match[0] % 2 == 0 else "17:00",
                "home_team": home_team["name"],
                "home_team_id": home_team["id"],
                "home_logo": home_team["logo"],
                "away_team": away_team["name"],
                "away_team_id": away_team["id"],
                "away_logo": away_team["logo"],
                "score": score,
                "venue": f"{home_team['name']} Stadium",
                "status": status,
            })
            
            match_id += 1

    
    return matches


