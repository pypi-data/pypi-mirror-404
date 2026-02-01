#!/usr/bin/env python3
"""
Config-driven script to extract data from api_sports/NFL_endpoints.py and save as CSV files.
Saves results as CSV files in the reports directory.

Following the pattern of nfl_data_wrapper/extract_wrapper_data.py:
- Config-driven with FUNCTIONS_TO_EXTRACT list
- Flexible and easily modifiable

NOTE: Exports are limited to 10,000 records maximum to prevent large file sizes.
"""

# Maximum records to export to CSV (prevents large file sizes)
MAX_EXPORT_RECORDS = 1000

import sys
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path to import api_sports
sys.path.insert(0, str(Path(__file__).parent.parent))

import api_sports.NFL.NFL_endpoints as nfl_endpoints

# Load environment variables
load_dotenv()
api_key = os.getenv('API_SPORTS_API_KEY')

if not api_key:
    raise ValueError("API_SPORTS_API_KEY environment variable not found. Please set it in your .env file.")

# Config at the top - easily modifiable
# Functions with their required arguments (excluding api_key which is passed automatically)
FUNCTIONS_TO_EXTRACT = {
    # 'get_timezone': {}, # List of timezones
    # 'get_seasons': {}, # starting from 2010
    # 'get_leagues': {}, # league_id 1 = NFL and league_id 2 = NCAA
    # 'get_teams': {'league': 1, 'season': 2025},  # Get all teams (2024 & 2025 require subscription)
    'get_injuries': {'team': 23},  # Get injuries for Carolina Panthers (team ID: 19)
    # 'get_games': {'season': 2025, 'league': 1},  # NFL games (2024 & 2025 require subscription)
    # 'get_standings': {'league': 1, 'season': 2023},  # NFL standings (2024 & 2025 require subscription)
    # 'get_standings_conferences': {'league': 1, 'season': 2023}, # (2024 & 2025 require subscription)
    # 'get_standings_divisions': {'league': 1, 'season': 2023}, # (2024 & 2025 require subscription)
    # 'get_odds_bets': {},  # Get all available bet types (market list)
    # 'get_odds_bookmakers': {},  # Get all available bookmakers (bookmakers list)
    # 'get_players': {'player_id': 14095},
    # 'get_odds': {'game': 17537},  # Odds may not be available - only kept 1-7 days before game + 7 day history
    # Note: Odds availability is limited. Old game IDs won't have odds data.
    # Note: To get odds, use a game ID from a recent/upcoming game (within 1-7 days)
    # Note: get_games_events, get_games_statistics_* require specific game_ids
    # Note: get_players_statistics requires season parameter
    # Note: get_players may return limited results without specific parameters
}

def main():
    """Extract data and save to CSV."""

    # Create data directory if it doesn't exist
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(exist_ok=True)

    print(f"Extracting {len(FUNCTIONS_TO_EXTRACT)} datasets from NFL API endpoints...")
    if api_key:
        print(f"Using API key: {api_key[:8]}...")
    else:
        print("Warning: API key not found!")

    for func_name, kwargs in FUNCTIONS_TO_EXTRACT.items():
        print(f"\nExtracting {func_name}...")
        print(f"Parameters: {kwargs}")

        try:
            # Get the function dynamically
            func = getattr(nfl_endpoints, func_name)

            # Call the function with api_key and additional arguments
            df = func(api_key, **kwargs)

            if df.empty:
                print(f"⚠️  No data found for {func_name}")
                print(f"   This could mean:")
                print(f"   - No data available for these parameters")
                print(f"   - Invalid game/team/player ID")
                print(f"   - API subscription limitation")
                continue

            print(f"✓ {func_name}: {len(df):,} rows, {len(df.columns)} columns")
        
        except Exception as e:
            print(f"❌ Error extracting {func_name}: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            continue

        # Limit export to MAX_EXPORT_RECORDS
        df_export = df.head(MAX_EXPORT_RECORDS)
        
        # Save to CSV
        csv_name = f"nfl_api_{func_name.replace('get_', '')}.csv"
        csv_path = data_dir / csv_name
        df_export.to_csv(csv_path, index=False)
        
        if len(df) > MAX_EXPORT_RECORDS:
            print(f"⚠️  Limited export to {MAX_EXPORT_RECORDS:,} of {len(df):,} total records")
        print(f"✓ Saved {func_name} to: {csv_path} ({len(df_export):,} records)")

        # Show sample data
        print(f"\n{func_name.upper()} Sample:")
        print(df_export.head(3))
        print("-" * 50)

    print("\n🎉 Data extraction completed!")
    print(f"Files saved to: {data_dir}")

if __name__ == "__main__":
    main()