import requests
import pandas as pd
from dotenv import load_dotenv
import os
import time

def get_standings(api_key, season, league_value):
    url = "https://v2.nba.api-sports.io/standings"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v2.nba.api-sports.io'
    }
    params = {
        'season': int(season),
        'league': league_value
    }
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")  # Log the full response text to see what the API is returning

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and data['response']:
            standings_df = pd.json_normalize(data['response'])
            return standings_df
        else:
            print("No standings data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch standings: {response.status_code}")
        return pd.DataFrame()

def get_teams(api_key):
    url = "https://v2.nba.api-sports.io/teams"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v2.nba.api-sports.io'
    }
    response = requests.get(url, headers=headers)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")  # Log the full response text to see what the API is returning

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and data['response']:
            teams_df = pd.json_normalize(data['response'])
            return teams_df
        else:
            print("No teams data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch teams: {response.status_code}")
        return pd.DataFrame()

def get_players(api_key, player_id):
    url = "https://v2.nba.api-sports.io/players"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v2.nba.api-sports.io'
    }
    params = {
        'id': player_id
    }
    response = requests.get(url, headers=headers, params=params)
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response JSON: {response.text}")  # Log the full response text to see what the API is returning

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and data['response']:
            players_df = pd.DataFrame(data['response'])
            return players_df
        else:
            print("No player data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch player: {response.status_code}")
        return pd.DataFrame()

def get_seasons(api_key):
    url = "https://v2.nba.api-sports.io/seasons"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v2.nba.api-sports.io'
    }
    response = requests.get(url, headers=headers)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")  # Log the full response text to see what the API is returning

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and data['response']:
            seasons_df = pd.DataFrame(data['response'], columns=['Season'])
            return seasons_df
        else:
            print("No seasons data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch seasons: {response.status_code}")
        return pd.DataFrame()

def get_leagues(api_key):
    url = "https://v2.nba.api-sports.io/leagues"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v2.nba.api-sports.io'
    }
    response = requests.get(url, headers=headers)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response JSON: {response.text}")  # Log the full response text to see what the API is returning

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and data['response']:
            leagues_df = pd.DataFrame(data['response'], columns=['leagues'])
            return leagues_df
        else:
            print("No seasons data found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch seasons: {response.status_code}")
        return pd.DataFrame()

def get_games(api_key, season, league_value):
    url = "https://v2.nba.api-sports.io/games"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v2.nba.api-sports.io'
    }
    params = {
        'season': int(season),
        # 'id': team_id
        # 'date': date_value,
        'league': league_value
    }
    print(f"Making request with params: {params}")
    response = requests.get(url, headers=headers, params=params)
    # print(f"HTTP Status Code: {response.status_code}")
    # print(f"Response: {response.text}")  # This will show the full response body

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and data['response']:
            df = pd.json_normalize(data['response'])
            return df
        else:
            print("Response JSON contains no 'response' key or it's empty.")
            return pd.DataFrame()
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return pd.DataFrame()

def get_game_stats(api_key, game_id):
    url = "https://v2.nba.api-sports.io/games/statistics"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v2.nba.api-sports.io'
    }
    params = {
        'id': game_id
    }
    print(f"Making request with params: {params}")
    response = requests.get(url, headers=headers, params=params)
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response: {response.text}")  # This will show the full response body

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and data['response']:
            df = pd.json_normalize(data['response'])
            return df
        else:
            print("Response JSON contains no 'response' key or it's empty.")
            return pd.DataFrame()
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return pd.DataFrame()

def get_team_stats(api_key, season, team_id):
    url = "https://v2.nba.api-sports.io/teams/statistics"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v2.nba.api-sports.io'
    }
    params = {
        'season': int(season),
        'id': team_id
    }
    print(f"Making request with params: {params}")
    response = requests.get(url, headers=headers, params=params)
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response: {response.text}")  # This will show the full response body

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and data['response']:
            df = pd.json_normalize(data['response'])
            return df
        else:
            print("Response JSON contains no 'response' key or it's empty.")
            return pd.DataFrame()
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return pd.DataFrame()

def get_players_stats(api_key, season, player_id):
    url = "https://v2.nba.api-sports.io/players/statistics"
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v2.nba.api-sports.io'
    }
    params = {
        'season': int(season),
        'id': player_id
    }
    print(f"Making request with params: {params}")
    response = requests.get(url, headers=headers, params=params)
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response: {response.text}")  # This will show the full response body

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and data['response']:
            df = pd.json_normalize(data['response'])
            return df
        else:
            print("Response JSON contains no 'response' key or it's empty.")
            return pd.DataFrame()
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return pd.DataFrame()

# Load the environment variables from the .env file
load_dotenv()  

api_key = os.getenv('API_SPORTS_API_KEY')
#2023-2024
season=2023
team_id=25
# Regular NBA League
league_value = 'standard'
# LA vs Denver
game_id = 13948
# LeBron 
player_id=265

# all_seasons =  get_seasons(api_key)
# print(all_seasons)

# all_teams =  get_teams(api_key)
# print(all_teams)

# all_leagues =  get_leagues(api_key)
# print(all_leagues)

# all_games =  get_games(api_key, season, league_value)
# print(all_games)

# players =  get_players(api_key, player_id)
# print(players)

standings =  get_standings(api_key, season, league_value)
print(standings)

"""STATS RELATED BELOW"""
# game_stats =  get_game_stats(api_key, game_id)
# print(game_stats)

# team_stats = get_team_stats(api_key, season, team_id)
# print(team_stats)

# players_stats =  get_players_stats(api_key, season, player_id)
# print(players_stats)
