#!/usr/bin/env python3
"""
Config-driven script to extract data from nfl_data_wrapper and save as CSV files.
Saves results as CSV files in the reports directory.

Following the pattern of scripts/extract_bucket_data.py:
- Config-driven with FUNCTIONS_TO_EXTRACT list
- Flexible and easily modifiable

NOTE: Exports are limited to 10,000 records maximum to prevent large file sizes.
"""

# ============================================================================
# CONFIGURATION - Modify these values as needed
# ============================================================================

# Maximum records to export to CSV (prevents large file sizes)
MAX_EXPORT_RECORDS = 100000

# Seasons to extract (default: current season + previous season for context)
# Options:
#   - None: Auto-detect current season using SeasonParser
#   - [2024, 2025]: Specific years
#   - [2023, 2024, 2025]: Multiple years
SEASONS_TO_EXTRACT = 2025  # Default: auto-detect current season

# ============================================================================

import sys
import os
import pandas as pd
from pathlib import Path

# Add the parent directory to sys.path to import nfl_data_wrapper
sys.path.insert(0, str(Path(__file__).parent.parent))

import nfl_data_wrapper
from commonv2.domain.schedules import SeasonParser

# Determine seasons to use
if SEASONS_TO_EXTRACT is None:
    # Auto-detect current season
    current_season = SeasonParser.get_current_season()
    SEASONS = [current_season]
    print(f"📅 Auto-detected current season: {current_season}")
else:
    SEASONS = SEASONS_TO_EXTRACT
    print(f"📅 Using configured seasons: {SEASONS}")

# Config at the top - easily modifiable
# Functions with their required arguments
FUNCTIONS_TO_EXTRACT = {
    # 'import_win_totals': {'years': SEASONS},
    # 'import_sc_lines': {'years': SEASONS},
    # Uncomment and modify as needed:
    'import_depth_charts': {'years': SEASONS},
    # 'import_seasonal_data': {'years': SEASONS, 's_type': 'REG'},
    # 'import_weekly_rosters': {'years': SEASONS},
    # 'import_seasonal_rosters': {'years': SEASONS},
    # 'import_injuries': {'years': SEASONS}
}

def main():
    """Extract data and save to CSV."""

    # Create data directory if it doesn't exist
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(exist_ok=True)

    print(f"Extracting {len(FUNCTIONS_TO_EXTRACT)} datasets from nfl_data_wrapper...")

    for func_name, kwargs in FUNCTIONS_TO_EXTRACT.items():
        print(f"\nExtracting {func_name}...")

        # Get the function dynamically
        func = getattr(nfl_data_wrapper, func_name)

        # Call the function to get data with arguments
        df = func(**kwargs)

        if df.empty:
            print(f"⚠️  No data found for {func_name}")
            continue

        print(f"✓ {func_name}: {len(df):,} rows, {len(df.columns)} columns")

        # Limit export to MAX_EXPORT_RECORDS
        df_export = df.head(MAX_EXPORT_RECORDS)
        
        # Save to CSV
        csv_name = f"nfl_data_wrapper_{func_name.replace('import_', '')}.csv"
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