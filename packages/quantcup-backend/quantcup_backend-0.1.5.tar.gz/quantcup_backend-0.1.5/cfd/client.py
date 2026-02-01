"""
College Football Data API Client
Simple wrapper following the api_sports/NFL_endpoints.py pattern

API Documentation: https://api.collegefootballdata.com/
Free tier: 1000 requests per month
"""

import requests
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

BASE_URL = "https://api.collegefootballdata.com"

def _get_headers(api_key=None):
    """Get headers for API requests."""
    key = api_key or os.getenv('CFDB_API_KEY')
    return {
        'Authorization': f'Bearer {key}',
        'Accept': 'application/json'
    }

def _make_request(endpoint, params=None, api_key=None):
    """Make API request and return DataFrame."""
    url = f"{BASE_URL}{endpoint}"
    headers = _get_headers(api_key)
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            return pd.json_normalize(data)
        else:
            print(f"No data found for {endpoint}")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch {endpoint}: {response.status_code}")
        return pd.DataFrame()

# ============================================================================
# GAMES ENDPOINTS
# ============================================================================

def get_games(year, week=None, season_type=None, team=None, home=None, away=None, 
              conference=None, division=None, api_key=None):
    """
    Get game results and information.
    
    Args:
        year (int): Year/season (required)
        week (int): Week number
        season_type (str): 'regular', 'postseason', or 'both'
        team (str): Team name
        home (str): Home team
        away (str): Away team
        conference (str): Conference abbreviation
        division (str): Division classification (fbs/fcs/ii/iii)
    """
    params = {'year': year}
    if week: params['week'] = week
    if season_type: params['seasonType'] = season_type
    if team: params['team'] = team
    if home: params['home'] = home
    if away: params['away'] = away
    if conference: params['conference'] = conference
    if division: params['division'] = division
    
    return _make_request('/games', params, api_key)

def get_game_teams(year, week=None, season_type=None, team=None, api_key=None):
    """Get team statistics by game."""
    params = {'year': year}
    if week: params['week'] = week
    if season_type: params['seasonType'] = season_type
    if team: params['team'] = team
    
    return _make_request('/games/teams', params, api_key)

def get_game_players(year, week=None, season_type=None, team=None, 
                     category=None, api_key=None):
    """Get player statistics by game."""
    params = {'year': year}
    if week: params['week'] = week
    if season_type: params['seasonType'] = season_type
    if team: params['team'] = team
    if category: params['category'] = category
    
    return _make_request('/games/players', params, api_key)

def get_game_media(year, week=None, season_type=None, team=None, 
                   conference=None, media_type=None, api_key=None):
    """Get game media information (TV, radio, etc)."""
    params = {'year': year}
    if week: params['week'] = week
    if season_type: params['seasonType'] = season_type
    if team: params['team'] = team
    if conference: params['conference'] = conference
    if media_type: params['mediaType'] = media_type
    
    return _make_request('/games/media', params, api_key)

def get_calendar(year, api_key=None):
    """Get calendar of weeks for a season."""
    params = {'year': year}
    return _make_request('/calendar', params, api_key)

def get_scoreboard(classification=None, conference=None, api_key=None):
    """Get live scoreboard data."""
    params = {}
    if classification: params['classification'] = classification
    if conference: params['conference'] = conference
    
    return _make_request('/scoreboard', params, api_key)

# ============================================================================
# TEAMS ENDPOINTS
# ============================================================================

def get_teams(conference=None, api_key=None):
    """Get team information."""
    params = {}
    if conference: params['conference'] = conference
    
    return _make_request('/teams', params, api_key)

def get_fbs_teams(year=None, api_key=None):
    """Get FBS team list for a given year."""
    params = {}
    if year: params['year'] = year
    
    return _make_request('/teams/fbs', params, api_key)

def get_roster(team, year=None, api_key=None):
    """
    Get team roster.
    
    Args:
        team (str): Team name (required)
        year (int): Year
    """
    params = {'team': team}
    if year: params['year'] = year
    
    return _make_request('/roster', params, api_key)

def get_talent(year=None, api_key=None):
    """Get team talent composite rankings."""
    params = {}
    if year: params['year'] = year
    
    return _make_request('/talent', params, api_key)

def get_team_matchup(team1, team2, min_year=None, max_year=None, api_key=None):
    """
    Get matchup history between two teams.
    
    Args:
        team1 (str): First team (required)
        team2 (str): Second team (required)
        min_year (int): Minimum year
        max_year (int): Maximum year
    """
    params = {'team1': team1, 'team2': team2}
    if min_year: params['minYear'] = min_year
    if max_year: params['maxYear'] = max_year
    
    return _make_request('/teams/matchup', params, api_key)

# ============================================================================
# CONFERENCES ENDPOINTS
# ============================================================================

def get_conferences(api_key=None):
    """Get conference information."""
    return _make_request('/conferences', {}, api_key)

# ============================================================================
# RANKINGS ENDPOINTS
# ============================================================================

def get_rankings(year, week=None, season_type=None, api_key=None):
    """
    Get historical poll rankings.
    
    Args:
        year (int): Year (required)
        week (int): Week number
        season_type (str): 'regular' or 'postseason'
    """
    params = {'year': year}
    if week: params['week'] = week
    if season_type: params['seasonType'] = season_type
    
    return _make_request('/rankings', params, api_key)

# ============================================================================
# BETTING ENDPOINTS
# ============================================================================

def get_lines(year, week=None, season_type=None, team=None, home=None, 
              away=None, conference=None, api_key=None):
    """
    Get betting lines.
    
    Args:
        year (int): Year (required)
        week (int): Week number
        season_type (str): 'regular' or 'postseason'
        team (str): Team name
        home (str): Home team
        away (str): Away team
        conference (str): Conference abbreviation
    """
    params = {'year': year}
    if week: params['week'] = week
    if season_type: params['seasonType'] = season_type
    if team: params['team'] = team
    if home: params['home'] = home
    if away: params['away'] = away
    if conference: params['conference'] = conference
    
    return _make_request('/lines', params, api_key)

# ============================================================================
# RECRUITING ENDPOINTS
# ============================================================================

def get_recruiting_players(year=None, classification=None, position=None, 
                          state=None, team=None, api_key=None):
    """Get player recruiting rankings."""
    params = {}
    if year: params['year'] = year
    if classification: params['classification'] = classification
    if position: params['position'] = position
    if state: params['state'] = state
    if team: params['team'] = team
    
    return _make_request('/recruiting/players', params, api_key)

def get_recruiting_teams(year=None, team=None, api_key=None):
    """Get team recruiting rankings."""
    params = {}
    if year: params['year'] = year
    if team: params['team'] = team
    
    return _make_request('/recruiting/teams', params, api_key)

# ============================================================================
# RATINGS ENDPOINTS
# ============================================================================

def get_sp_ratings(year=None, team=None, api_key=None):
    """Get SP+ ratings."""
    params = {}
    if year: params['year'] = year
    if team: params['team'] = team
    
    return _make_request('/ratings/sp', params, api_key)

def get_srs_ratings(year=None, team=None, conference=None, api_key=None):
    """Get SRS (Simple Rating System) ratings."""
    params = {}
    if year: params['year'] = year
    if team: params['team'] = team
    if conference: params['conference'] = conference
    
    return _make_request('/ratings/srs', params, api_key)

def get_elo_ratings(year=None, week=None, season_type=None, team=None, 
                    conference=None, api_key=None):
    """Get ELO ratings."""
    params = {}
    if year: params['year'] = year
    if week: params['week'] = week
    if season_type: params['seasonType'] = season_type
    if team: params['team'] = team
    if conference: params['conference'] = conference
    
    return _make_request('/ratings/elo', params, api_key)

def get_fpi_ratings(year=None, team=None, conference=None, api_key=None):
    """Get FPI (Football Power Index) ratings."""
    params = {}
    if year: params['year'] = year
    if team: params['team'] = team
    if conference: params['conference'] = conference
    
    return _make_request('/ratings/fpi', params, api_key)

# ============================================================================
# STATS ENDPOINTS
# ============================================================================

def get_player_season_stats(year, season_type=None, team=None, conference=None,
                            start_week=None, end_week=None, category=None, 
                            api_key=None):
    """
    Get player season statistics.
    
    Args:
        year (int): Year (required)
        season_type (str): 'regular', 'postseason', or 'both'
        team (str): Team name
        conference (str): Conference abbreviation
        start_week (int): Starting week
        end_week (int): Ending week
        category (str): Stat category (passing, rushing, receiving, etc)
    """
    params = {'year': year}
    if season_type: params['seasonType'] = season_type
    if team: params['team'] = team
    if conference: params['conference'] = conference
    if start_week: params['startWeek'] = start_week
    if end_week: params['endWeek'] = end_week
    if category: params['category'] = category
    
    return _make_request('/stats/player/season', params, api_key)

def get_team_season_stats(year, team=None, conference=None, start_week=None,
                         end_week=None, api_key=None):
    """Get team season statistics."""
    params = {'year': year}
    if team: params['team'] = team
    if conference: params['conference'] = conference
    if start_week: params['startWeek'] = start_week
    if end_week: params['endWeek'] = end_week
    
    return _make_request('/stats/season', params, api_key)

def get_advanced_team_season_stats(year, team=None, exclude_garbage_time=None,
                                  start_week=None, end_week=None, api_key=None):
    """Get advanced team season statistics."""
    params = {'year': year}
    if team: params['team'] = team
    if exclude_garbage_time: params['excludeGarbageTime'] = exclude_garbage_time
    if start_week: params['startWeek'] = start_week
    if end_week: params['endWeek'] = end_week
    
    return _make_request('/stats/season/advanced', params, api_key)

# ============================================================================
# PLAYERS ENDPOINTS
# ============================================================================

def get_player_search(search_term, position=None, team=None, year=None, api_key=None):
    """
    Search for players.
    
    Args:
        search_term (str): Search term (required)
        position (str): Position abbreviation
        team (str): Team name
        year (int): Year
    """
    params = {'searchTerm': search_term}
    if position: params['position'] = position
    if team: params['team'] = team
    if year: params['year'] = year
    
    return _make_request('/player/search', params, api_key)

def get_player_usage(year, team=None, conference=None, position=None, 
                    player_id=None, exclude_garbage_time=None, api_key=None):
    """
    Get player usage metrics.
    
    Args:
        year (int): Year (required)
        team (str): Team name
        conference (str): Conference abbreviation
        position (str): Position abbreviation
        player_id (int): Player ID
        exclude_garbage_time (bool): Exclude garbage time
    """
    params = {'year': year}
    if team: params['team'] = team
    if conference: params['conference'] = conference
    if position: params['position'] = position
    if player_id: params['playerId'] = player_id
    if exclude_garbage_time: params['excludeGarbageTime'] = exclude_garbage_time
    
    return _make_request('/player/usage', params, api_key)

def get_returning_production(year=None, team=None, conference=None, api_key=None):
    """Get returning production metrics."""
    params = {}
    if year: params['year'] = year
    if team: params['team'] = team
    if conference: params['conference'] = conference
    
    return _make_request('/player/returning', params, api_key)

# ============================================================================
# DRIVES ENDPOINTS
# ============================================================================

def get_drives(year, season_type=None, week=None, team=None, offense=None,
              defense=None, conference=None, offense_conference=None,
              defense_conference=None, api_key=None):
    """
    Get drive data.
    
    Args:
        year (int): Year (required)
        season_type (str): 'regular' or 'postseason'
        week (int): Week number
        team (str): Team name
        offense (str): Offensive team
        defense (str): Defensive team
        conference (str): Conference abbreviation
        offense_conference (str): Offensive team conference
        defense_conference (str): Defensive team conference
    """
    params = {'year': year}
    if season_type: params['seasonType'] = season_type
    if week: params['week'] = week
    if team: params['team'] = team
    if offense: params['offense'] = offense
    if defense: params['defense'] = defense
    if conference: params['conference'] = conference
    if offense_conference: params['offenseConference'] = offense_conference
    if defense_conference: params['defenseConference'] = defense_conference
    
    return _make_request('/drives', params, api_key)

# ============================================================================
# PLAYS ENDPOINTS
# ============================================================================

def get_plays(year, week, season_type=None, team=None, offense=None, defense=None,
             conference=None, offense_conference=None, defense_conference=None,
             play_type=None, api_key=None):
    """
    Get play-by-play data.
    
    Args:
        year (int): Year (required)
        week (int): Week (required)
        season_type (str): 'regular' or 'postseason'
        team (str): Team name
        offense (str): Offensive team
        defense (str): Defensive team
        conference (str): Conference abbreviation
        offense_conference (str): Offensive team conference
        defense_conference (str): Defensive team conference
        play_type (int): Play type ID
    """
    params = {'year': year, 'week': week}
    if season_type: params['seasonType'] = season_type
    if team: params['team'] = team
    if offense: params['offense'] = offense
    if defense: params['defense'] = defense
    if conference: params['conference'] = conference
    if offense_conference: params['offenseConference'] = offense_conference
    if defense_conference: params['defenseConference'] = defense_conference
    if play_type: params['playType'] = play_type
    
    return _make_request('/plays', params, api_key)

def get_play_types(api_key=None):
    """Get play type information."""
    return _make_request('/plays/types', {}, api_key)

def get_play_stats(year=None, week=None, team=None, game_id=None, 
                  athlete_id=None, stat_type_id=None, season_type=None,
                  conference=None, api_key=None):
    """Get play statistics."""
    params = {}
    if year: params['year'] = year
    if week: params['week'] = week
    if team: params['team'] = team
    if game_id: params['gameId'] = game_id
    if athlete_id: params['athleteId'] = athlete_id
    if stat_type_id: params['statTypeId'] = stat_type_id
    if season_type: params['seasonType'] = season_type
    if conference: params['conference'] = conference
    
    return _make_request('/plays/stats', params, api_key)

# ============================================================================
# COACHES ENDPOINTS
# ============================================================================

def get_coaches(first_name=None, last_name=None, team=None, year=None,
               min_year=None, max_year=None, api_key=None):
    """Get coach information."""
    params = {}
    if first_name: params['firstName'] = first_name
    if last_name: params['lastName'] = last_name
    if team: params['team'] = team
    if year: params['year'] = year
    if min_year: params['minYear'] = min_year
    if max_year: params['maxYear'] = max_year
    
    return _make_request('/coaches', params, api_key)

# ============================================================================
# VENUES ENDPOINTS
# ============================================================================

def get_venues(api_key=None):
    """Get venue information."""
    return _make_request('/venues', {}, api_key)

# Example usage
if __name__ == "__main__":
    # Get current season games
    games = get_games(year=2024, week=10)
    print(f"Games: {len(games)} rows")
    
    # Get rankings
    rankings = get_rankings(year=2024, week=10)
    print(f"Rankings: {len(rankings)} rows")
    
    # Get betting lines
    lines = get_lines(year=2024, week=10)
    print(f"Lines: {len(lines)} rows")