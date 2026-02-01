#!/usr/bin/env python3
"""
Config-driven script to extract data from College Football Data API and save as CSV files.
Saves results as CSV files in the reports directory.

Following the pattern of nfl_data_wrapper/extract_wrapper_data.py:
- Config-driven with FUNCTIONS_TO_EXTRACT dict
- Flexible and easily modifiable
- Uses CFDB_API_KEY from .env file

NOTE: Exports are limited to 10,000 records maximum to prevent large file sizes.
"""

# Maximum records to export to CSV (prevents large file sizes)
MAX_EXPORT_RECORDS = 10000

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to import cfd
sys.path.insert(0, str(Path(__file__).parent.parent))

import cfd

# Config at the top - easily modifiable
# Functions with their required arguments
FUNCTIONS_TO_EXTRACT = {
    # Games - current season
    'get_games': {'year': 2024, 'week': 10},
    'get_calendar': {'year': 2024},
    
    # Teams
    'get_teams': {},
    'get_fbs_teams': {'year': 2024},
    
    # Conferences
    'get_conferences': {},
    
    # Rankings - current week
    'get_rankings': {'year': 2024, 'week': 10},
    
    # Betting lines - current week
    'get_lines': {'year': 2024, 'week': 10},
    
    # Ratings - current season
    'get_sp_ratings': {'year': 2024},
    'get_fpi_ratings': {'year': 2024},
    'get_elo_ratings': {'year': 2024, 'week': 10},
    
    # Team stats - current season
    'get_team_season_stats': {'year': 2024},
    
    # Recruiting - latest class
    'get_recruiting_teams': {'year': 2024},
    
    # Venues
    'get_venues': {},
}

def main():
    """Extract data and save to CSV."""
    
    # Create data directory if it doesn't exist
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(exist_ok=True)
    
    print(f"Extracting {len(FUNCTIONS_TO_EXTRACT)} datasets from College Football Data API...")
    print("=" * 70)
    
    for func_name, kwargs in FUNCTIONS_TO_EXTRACT.items():
        print(f"\nExtracting {func_name}...")
        
        # Get the function dynamically
        func = getattr(cfd, func_name)
        
        # Call the function to get data with arguments
        df = func(**kwargs)
        
        if df.empty:
            print(f"⚠️  No data found for {func_name}")
            continue
        
        print(f"✓ {func_name}: {len(df):,} rows, {len(df.columns)} columns")
        
        # Limit export to MAX_EXPORT_RECORDS
        df_export = df.head(MAX_EXPORT_RECORDS)
        
        # Save to CSV
        csv_name = f"cfd_{func_name.replace('get_', '')}.csv"
        csv_path = data_dir / csv_name
        df_export.to_csv(csv_path, index=False)
        
        if len(df) > MAX_EXPORT_RECORDS:
            print(f"⚠️  Limited export to {MAX_EXPORT_RECORDS:,} of {len(df):,} total records")
        print(f"✓ Saved to: {csv_path} ({len(df_export):,} records)")
        
        # Show sample data
        print(f"\n{func_name.upper()} Sample:")
        print(df_export.head(3))
        print("-" * 70)
    
    print("\n🎉 Data extraction completed!")
    print(f"Files saved to: {data_dir}")

if __name__ == "__main__":
    main()