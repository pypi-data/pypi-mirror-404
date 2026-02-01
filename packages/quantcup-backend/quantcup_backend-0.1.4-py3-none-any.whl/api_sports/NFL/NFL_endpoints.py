import requests
import pandas as pd
from dotenv import load_dotenv
import os
import time

def get_timezone(api_key):
    url = "https://v1.american-football.api-sports.io/timezone"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    response = requests.get(url, headers=headers)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            timezone_df = pd.DataFrame(data['response'], columns=['Timezone'])
            return timezone_df
        else:
            print("No timezone data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch timezone: {response.status_code}")
        return pd.DataFrame()

def get_seasons(api_key):
    url = "https://v1.american-football.api-sports.io/seasons"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    response = requests.get(url, headers=headers)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            seasons_df = pd.DataFrame(data['response'], columns=['Season'])
            return seasons_df
        else:
            print("No seasons data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch seasons: {response.status_code}")
        return pd.DataFrame()

def get_leagues(api_key, league_id=None, season=None, current=None):
    """
    Fetch league information from the NFL API.
    
    Returns comprehensive league data including detailed season information.
    The seasons data helps you:
    - Choose the right season for your data extraction
    - Understand data availability before making API calls
    - Plan your analysis based on what data exists
    - Avoid API errors by selecting seasons with available data
    
    Args:
        api_key (str): Your API Sports API key
        league_id (int, optional): Specific league ID (1 for NFL, 2 for NCAA)
        season (int, optional): Filter by specific season year
        current (bool, optional): Filter for current seasons only
        
    Returns:
        pandas.DataFrame: League information with season details and data availability
    """
    url = "https://v1.american-football.api-sports.io/leagues"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {}
    if league_id:
        params['id'] = league_id
    if season:
        params['season'] = season
    if current:
        params['current'] = current
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            leagues_df = pd.json_normalize(data['response'])
            return leagues_df
        else:
            print("No leagues data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch leagues: {response.status_code}")
        return pd.DataFrame()

def get_teams(api_key, team_id=None, league=None, season=None, name=None, code=None, search=None):
    url = "https://v1.american-football.api-sports.io/teams"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {}
    if team_id:
        params['id'] = team_id
    if league:
        params['league'] = league
    if season:
        params['season'] = season
    if name:
        params['name'] = name
    if code:
        params['code'] = code
    if search:
        params['search'] = search
    
    print(f"API URL: {url}")
    print(f"Parameters: {params}")
    print(f"Headers: {headers}")
    
    response = requests.get(url, headers=headers, params=params)
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            teams_df = pd.json_normalize(data['response'])
            return teams_df
        else:
            print("No teams data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch teams: {response.status_code}")
        return pd.DataFrame()

def get_players(api_key, player_id=None, name=None, team=None, season=None, search=None):
    url = "https://v1.american-football.api-sports.io/players"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {}
    if player_id:
        params['id'] = player_id
    if name:
        params['name'] = name
    if team:
        params['team'] = team
    if season:
        params['season'] = season
    if search:
        params['search'] = search
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            players_df = pd.json_normalize(data['response'])
            return players_df
        else:
            print("No players data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch players: {response.status_code}")
        return pd.DataFrame()

def get_players_statistics(api_key, player_id=None, team=None, season=None):
    url = "https://v1.american-football.api-sports.io/players/statistics"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {}
    if player_id:
        params['id'] = player_id
    if team:
        params['team'] = team
    if season:
        params['season'] = season
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            stats_df = pd.json_normalize(data['response'])
            return stats_df
        else:
            print("No players statistics data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch players statistics: {response.status_code}")
        return pd.DataFrame()

def get_injuries(api_key, player=None, team=None):
    url = "https://v1.american-football.api-sports.io/injuries"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {}
    if player:
        params['player'] = player
    if team:
        params['team'] = team
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            injuries_df = pd.json_normalize(data['response'])
            return injuries_df
        else:
            print("No injuries data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch injuries: {response.status_code}")
        return pd.DataFrame()

def get_games(api_key, game_id=None, date=None, league=None, season=None, team=None, h2h=None, live=None, timezone=None):
    url = "https://v1.american-football.api-sports.io/games"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {}
    if game_id:
        params['id'] = game_id
    if date:
        params['date'] = date
    if league:
        params['league'] = league
    if season:
        params['season'] = season
    if team:
        params['team'] = team
    if h2h:
        params['h2h'] = h2h
    if live:
        params['live'] = live
    if timezone:
        params['timezone'] = timezone
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            games_df = pd.json_normalize(data['response'])
            return games_df
        else:
            print("No games data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch games: {response.status_code}")
        return pd.DataFrame()

def get_games_events(api_key, game_id):
    url = "https://v1.american-football.api-sports.io/games/events"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {
        'id': game_id
    }
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            events_df = pd.json_normalize(data['response'])
            return events_df
        else:
            print("No games events data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch games events: {response.status_code}")
        return pd.DataFrame()

def get_games_statistics_teams(api_key, game_id, team=None):
    url = "https://v1.american-football.api-sports.io/games/statistics/teams"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {
        'id': game_id
    }
    if team:
        params['team'] = team
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            stats_df = pd.json_normalize(data['response'])
            return stats_df
        else:
            print("No games statistics teams data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch games statistics teams: {response.status_code}")
        return pd.DataFrame()

def get_games_statistics_players(api_key, game_id, group=None, team=None, player=None):
    url = "https://v1.american-football.api-sports.io/games/statistics/players"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {
        'id': game_id
    }
    if group:
        params['group'] = group
    if team:
        params['team'] = team
    if player:
        params['player'] = player
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            stats_df = pd.json_normalize(data['response'])
            return stats_df
        else:
            print("No games statistics players data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch games statistics players: {response.status_code}")
        return pd.DataFrame()

def get_standings(api_key, league, season, team=None, conference=None, division=None):
    url = "https://v1.american-football.api-sports.io/standings"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {
        'league': league,
        'season': season
    }
    if team:
        params['team'] = team
    if conference:
        params['conference'] = conference
    if division:
        params['division'] = division
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            standings_df = pd.json_normalize(data['response'])
            return standings_df
        else:
            print("No standings data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch standings: {response.status_code}")
        return pd.DataFrame()

def get_standings_conferences(api_key, league, season):
    url = "https://v1.american-football.api-sports.io/standings/conferences"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {
        'league': league,
        'season': season
    }
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            conferences_df = pd.DataFrame(data['response'], columns=['Conference'])
            return conferences_df
        else:
            print("No standings conferences data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch standings conferences: {response.status_code}")
        return pd.DataFrame()

def get_standings_divisions(api_key, league, season):
    url = "https://v1.american-football.api-sports.io/standings/divisions"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {
        'league': league,
        'season': season
    }
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            divisions_df = pd.DataFrame(data['response'], columns=['Division'])
            return divisions_df
        else:
            print("No standings divisions data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch standings divisions: {response.status_code}")
        return pd.DataFrame()

def get_odds(api_key, game, bookmaker=None, bet=None):
    url = "https://v1.american-football.api-sports.io/odds"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {
        'game': game
    }
    if bookmaker:
        params['bookmaker'] = bookmaker
    if bet:
        params['bet'] = bet
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            odds_df = pd.json_normalize(data['response'])
            return odds_df
        else:
            print("No odds data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch odds: {response.status_code}")
        return pd.DataFrame()

def get_odds_bets(api_key, bet_id=None, search=None):
    url = "https://v1.american-football.api-sports.io/odds/bets"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {}
    if bet_id:
        params['id'] = bet_id
    if search:
        params['search'] = search
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            bets_df = pd.json_normalize(data['response'])
            return bets_df
        else:
            print("No odds bets data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch odds bets: {response.status_code}")
        return pd.DataFrame()

def get_odds_bookmakers(api_key, bookmaker_id=None, search=None):
    url = "https://v1.american-football.api-sports.io/odds/bookmakers"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v1.american-football.api-sports.io'
    }
    params = {}
    if bookmaker_id:
        params['id'] = bookmaker_id
    if search:
        params['search'] = search
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")

    if response.status_code == 200:
        data = response.json()
        
        # Check for API errors
        if 'errors' in data and data['errors']:
            print(f"API Error: {data['errors']}")
            return pd.DataFrame()
        
        if 'response' in data and data['response']:
            bookmakers_df = pd.json_normalize(data['response'])
            return bookmakers_df
        else:
            print("No odds bookmakers data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch odds bookmakers: {response.status_code}")
        return pd.DataFrame()

# Load the environment variables from the .env file
load_dotenv()

api_key = os.getenv('API_SPORTS_API_KEY')
# Example parameters
season = 2022
league = 1
team_id = 1
player_id = 1
game_id = 1985
bet_id = 1
bookmaker_id = 1

# Example usage (uncomment to test)
# timezone = get_timezone(api_key)
# print(timezone)

# seasons = get_seasons(api_key)
# print(seasons)

# leagues = get_leagues(api_key)
# print(leagues)

# teams = get_teams(api_key, team_id=team_id)
# print(teams)

# players = get_players(api_key, player_id=player_id)
# print(players)

# players_stats = get_players_statistics(api_key, player_id=player_id, season=season)
# print(players_stats)

# injuries = get_injuries(api_key, player=player_id)
# print(injuries)

# games = get_games(api_key, date='2022-09-30')
# print(games)

# games_events = get_games_events(api_key, game_id)
# print(games_events)

# games_stats_teams = get_games_statistics_teams(api_key, game_id)
# print(games_stats_teams)

# games_stats_players = get_games_statistics_players(api_key, game_id)
# print(games_stats_players)

# standings = get_standings(api_key, league, season)
# print(standings)

# standings_conferences = get_standings_conferences(api_key, league, season)
# print(standings_conferences)

# standings_divisions = get_standings_divisions(api_key, league, season)
# print(standings_divisions)

# odds = get_odds(api_key, game_id)
# print(odds)

# odds_bets = get_odds_bets(api_key)
# print(odds_bets)

# odds_bookmakers = get_odds_bookmakers(api_key)
# print(odds_bookmakers)