#!/usr/bin/env python3
"""
Dynamic Games -> Teams -> Injuries Extraction Script

This script dynamically extracts NFL data in a pipeline fashion:
1. Fetches games for a given season and league
2. Extracts unique team IDs from those games
3. Fetches injury data for each team

This provides a data-driven approach to injury tracking based on actual games.
"""

import sys
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import time

# Add the parent directory to sys.path to import api_sports
sys.path.insert(0, str(Path(__file__).parent.parent))

import api_sports.NFL.NFL_endpoints as nfl_endpoints

# Load environment variables
load_dotenv()
api_key = os.getenv('API_SPORTS_API_KEY')

if not api_key:
    raise ValueError("API_SPORTS_API_KEY environment variable not found. Please set it in your .env file.")

# CONFIG - Customize these parameters
SEASON = 2025  # Current season
LEAGUE_ID = 1  # 1 = NFL, 2 = NCAA
RATE_LIMIT_DELAY = 0.5  # Seconds between API calls to avoid rate limiting
UPCOMING_ONLY = True  # Only extract upcoming/scheduled games (not completed)


def extract_games(api_key, season, league_id, upcoming_only=False):
    """
    Extract games for a given season and league.
    
    Args:
        api_key: API Sports API key
        season: Season year (e.g., 2025)
        league_id: League ID (1 for NFL)
        upcoming_only: If True, only return games that haven't been played yet
        
    Returns:
        DataFrame containing game data
    """
    print(f"\n{'='*60}")
    print(f"STEP 1: Extracting games for season {season}, league {league_id}")
    if upcoming_only:
        print(f"          (Filtering for upcoming games only)")
    print(f"{'='*60}")
    
    games_df = nfl_endpoints.get_games(api_key, season=season, league=league_id)
    
    if games_df.empty:
        print("⚠️  No games found!")
        return games_df
    
    print(f"✓ Found {len(games_df)} total games")
    
    # Filter for upcoming games if requested
    if upcoming_only and 'game.status.short' in games_df.columns:
        # Common status values:
        # 'NS' = Not Started (upcoming)
        # 'FT' = Full Time (completed)
        # 'CANC' = Cancelled
        # 'SUSP' = Suspended
        # 'Q1', 'Q2', 'Q3', 'Q4', 'OT' = In Progress
        
        original_count = len(games_df)
        games_df = games_df[games_df['game.status.short'] == 'NS'].copy()
        filtered_count = len(games_df)
        
        print(f"✓ Filtered to {filtered_count} upcoming games (from {original_count} total)")
        
        if games_df.empty:
            print("⚠️  No upcoming games found!")
            return games_df
    
    print(f"✓ Columns: {list(games_df.columns)}")
    return games_df


def extract_teams_from_games(games_df):
    """
    Extract unique team IDs from games data.
    
    Args:
        games_df: DataFrame containing games data
        
    Returns:
        List of unique team IDs
    """
    print(f"\n{'='*60}")
    print(f"STEP 2: Extracting unique teams from games")
    print(f"{'='*60}")
    
    if games_df.empty:
        print("⚠️  No games data to extract teams from!")
        return []
    
    # Extract team IDs from various possible column structures
    # API Sports returns nested JSON that gets normalized into columns like:
    # teams.home.id, teams.away.id OR game.teams.home.id, game.teams.away.id
    
    team_ids = set()
    
    # Try different column naming patterns
    possible_home_cols = ['teams.home.id', 'game.teams.home.id', 'teams.home', 'home_team_id']
    possible_away_cols = ['teams.away.id', 'game.teams.away.id', 'teams.away', 'away_team_id']
    
    for col in possible_home_cols:
        if col in games_df.columns:
            team_ids.update(games_df[col].dropna().unique())
            print(f"✓ Found home teams in column: {col}")
            break
    
    for col in possible_away_cols:
        if col in games_df.columns:
            team_ids.update(games_df[col].dropna().unique())
            print(f"✓ Found away teams in column: {col}")
            break
    
    # If no teams found with specific columns, show available columns
    if not team_ids:
        print("⚠️  Could not find team IDs with expected column names")
        print(f"Available columns: {list(games_df.columns)}")
        print("\nFirst game structure:")
        print(games_df.head(1).to_dict('records'))
        return []
    
    team_ids = sorted([int(tid) for tid in team_ids if pd.notna(tid)])
    print(f"✓ Found {len(team_ids)} unique teams: {team_ids}")
    
    return team_ids


def extract_injuries_for_teams(api_key, team_ids, rate_limit_delay=0.5):
    """
    Extract injury data for each team.
    
    Args:
        api_key: API Sports API key
        team_ids: List of team IDs to fetch injuries for
        rate_limit_delay: Seconds to wait between API calls
        
    Returns:
        DataFrame containing all injuries data
    """
    print(f"\n{'='*60}")
    print(f"STEP 3: Extracting injuries for {len(team_ids)} teams")
    print(f"{'='*60}")
    
    all_injuries = []
    
    for i, team_id in enumerate(team_ids, 1):
        print(f"\n[{i}/{len(team_ids)}] Fetching injuries for team {team_id}...", end=" ")
        
        try:
            injuries_df = nfl_endpoints.get_injuries(api_key, team=team_id)
            
            if injuries_df.empty:
                print("No injuries")
            else:
                all_injuries.append(injuries_df)
                print(f"✓ {len(injuries_df)} injuries found")
            
            # Rate limiting
            if i < len(team_ids):  # Don't delay after last call
                time.sleep(rate_limit_delay)
                
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {str(e)}")
            continue
    
    if not all_injuries:
        print("\n⚠️  No injury data found for any team")
        return pd.DataFrame()
    
    # Combine all injuries into single DataFrame
    combined_injuries = pd.concat(all_injuries, ignore_index=True)
    print(f"\n✓ Total injuries collected: {len(combined_injuries)}")
    
    return combined_injuries


def save_results(games_df, team_ids, injuries_df):
    """
    Save all extracted data to CSV files.
    
    Args:
        games_df: DataFrame containing games data
        team_ids: List of team IDs
        injuries_df: DataFrame containing injuries data
    """
    print(f"\n{'='*60}")
    print(f"STEP 4: Saving results")
    print(f"{'='*60}")
    
    # Create data directory if it doesn't exist
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_suffix = "upcoming" if UPCOMING_ONLY else "all"
    
    # Save games
    if not games_df.empty:
        games_file = data_dir / f"apisports_nfl_games_{mode_suffix}_s{SEASON}_{timestamp}.csv"
        games_df.to_csv(games_file, index=False)
        print(f"✓ Games saved to: {games_file} ({len(games_df)} records)")
    
    # Save injuries
    if not injuries_df.empty:
        injuries_file = data_dir / f"apisports_nfl_injuries_{mode_suffix}_s{SEASON}_{timestamp}.csv"
        injuries_df.to_csv(injuries_file, index=False)
        print(f"✓ Injuries saved to: {injuries_file} ({len(injuries_df)} records)")
    
    print(f"\n✓ All files saved to: {data_dir}")


def display_summary(games_df, team_ids, injuries_df):
    """
    Display a summary of the extracted data.
    
    Args:
        games_df: DataFrame containing games data
        team_ids: List of team IDs
        injuries_df: DataFrame containing injuries data
    """
    print(f"\n{'='*60}")
    print(f"DATA SUMMARY")
    print(f"{'='*60}")
    
    # Games summary
    print(f"\n📊 GAMES ({len(games_df)} total):")
    if not games_df.empty:
        # Try to show some game details
        if 'game.date.date' in games_df.columns:
            print(f"   Date range: {games_df['game.date.date'].min()} to {games_df['game.date.date'].max()}")
        if 'game.stage' in games_df.columns:
            print(f"   Stages: {games_df['game.stage'].unique()}")
        if 'game.week' in games_df.columns:
            print(f"   Weeks: {sorted(games_df['game.week'].dropna().unique())}")
        
        print("\n   Sample games:")
        display_cols = [col for col in ['game.date.date', 'game.week', 'game.stage', 'teams.home.name', 'teams.away.name'] 
                       if col in games_df.columns]
        if display_cols:
            print(games_df[display_cols].head(5).to_string(index=False))
        else:
            print(games_df.head(3))
    
    # Teams summary
    print(f"\n👥 TEAMS ({len(team_ids)} unique):")
    if team_ids:
        print(f"   Team IDs: {team_ids}")
    
    # Injuries summary
    print(f"\n🏥 INJURIES ({len(injuries_df)} total):")
    if not injuries_df.empty:
        print(f"   Columns: {list(injuries_df.columns)}")
        
        # Show injury statistics
        if 'team.name' in injuries_df.columns:
            print(f"\n   Injuries by team:")
            team_injury_counts = injuries_df['team.name'].value_counts()
            for team, count in team_injury_counts.head(10).items():
                print(f"      {team}: {count}")
        
        if 'player.status' in injuries_df.columns:
            print(f"\n   Injuries by status:")
            for status, count in injuries_df['player.status'].value_counts().items():
                print(f"      {status}: {count}")
        
        print("\n   Sample injuries:")
        display_cols = [col for col in ['team.name', 'player.name', 'player.injury', 'player.status'] 
                       if col in injuries_df.columns]
        if display_cols:
            print(injuries_df[display_cols].head(10).to_string(index=False))
        else:
            print(injuries_df.head(5))


def main():
    """Main execution function."""
    print(f"\n{'#'*60}")
    print(f"# NFL DYNAMIC GAMES -> TEAMS -> INJURIES EXTRACTION")
    print(f"# Season: {SEASON} | League: {LEAGUE_ID} (NFL)")
    if UPCOMING_ONLY:
        print(f"# Mode: UPCOMING GAMES ONLY")
    else:
        print(f"# Mode: ALL GAMES")
    print(f"{'#'*60}")
    
    # Step 1: Extract games
    games_df = extract_games(api_key, SEASON, LEAGUE_ID, upcoming_only=UPCOMING_ONLY)
    
    if games_df.empty:
        print("\n❌ No games found. Cannot proceed with team and injury extraction.")
        return
    
    # Step 2: Extract teams from games
    team_ids = extract_teams_from_games(games_df)
    
    if not team_ids:
        print("\n❌ No teams found in games data. Cannot proceed with injury extraction.")
        print("\n💡 TIP: Check if your API subscription covers this season ({SEASON})")
        return
    
    # Step 3: Extract injuries for each team
    injuries_df = extract_injuries_for_teams(api_key, team_ids, RATE_LIMIT_DELAY)
    
    # Step 4: Save results
    save_results(games_df, team_ids, injuries_df)
    
    # Step 5: Display summary
    display_summary(games_df, team_ids, injuries_df)
    
    print(f"\n{'#'*60}")
    print(f"# ✓ EXTRACTION COMPLETE!")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
