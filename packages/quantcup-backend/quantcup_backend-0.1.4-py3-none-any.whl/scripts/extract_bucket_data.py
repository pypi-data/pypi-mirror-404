#!/usr/bin/env python3
"""
Config-driven script to extract data from Sevalla bucket and save as CSV files.
Saves results as CSV files in the reports directory.

Following REFACTORING_SPECS.md:
- Maximum 2 complexity points (DI + business logic)
- Simple dependency injection with fallbacks
- 2 layers: Script → BucketAdapter → S3

NOTE: Exports are limited to 50 records maximum to prevent large file sizes.
"""

# Maximum records to export to CSV (prevents large file sizes)
MAX_EXPORT_RECORDS = 1000000  # Increased for fact table auditing

import sys
import os
import io
import pandas as pd
from pathlib import Path

# Add the project root to sys.path to import nflfastRv3
sys.path.insert(0, str(Path(__file__).parent.parent))

from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger

logger = get_logger('extract_bucket_data')

# Config at the top - easily modifiable
# Format: 'table_name' OR ('table_name', {'season': year}) for partitioned tables
TABLES_TO_EXTRACT = [
    # ============= ODDS API TABLES =============
    # Dimensions (small, quick to extract)
    # 'dim_oddapi_game',           # Game reference
    # 'dim_team',                  # Team reference with participant IDs
    # 'dim_bookmaker',             # Bookmaker metadata
    # 'dim_market',                # Market types (h2h, spreads, totals)
    # 'dim_date',                  # Date dimension
    # 'dim_snapshot_navigation',   # Temporal navigation links
    
    # Fact Tables (large, may hit MAX_EXPORT_RECORDS limit)
    # 'fact_odds_raw',             # TRUTH LAYER - immutable API data
    # 'fact_odds_features',        # ANALYTICS LAYER - derived metrics
    
    # ============= NFLFASTR TABLES (commented out) =============
    # 'contracts',
    # 'pfr_adv_stats',
    # 'ff_rankings',
    # 'depth_chart',
    # 'espn_qbr_wk',
    # 'espn_qbr_season'
    # 'injuries',
    # 'player_availability',
    # 'nextgen',
    # 'wkly_rosters',
    # 'snap_counts',
    # 'fact_play',
    # 'fact_player_play',
    # 'fact_player_stats',
    # 'dim_game',
    'dim_game_weather',
    # 'dim_drive',
    # 'dim_date',
    # 'dim_player',
    # 'dim_team',
    # 'weather_features_v1',
    # 'odds_features_game_v1',
    # 'rolling_metrics_v1',
    # 'injury_features_v1',
    # 'nextgen_features_v1',
    # 'player_availability_v1',
    # 'participation',
    # 'players',
    
    # Play by play is year-partitioned: use (table_name, {'season': year}) format
    # ('play_by_play', {'season': 2025})
    # ('odds_features_game_v1', {'season': 2025})
]

# Schema selection (matches backfill_historical_odds.py BUCKET_SCHEMA)
# SCHEMA = 'oddsapi'
# SCHEMA = 'raw_nflfastr'
SCHEMA = 'warehouse'
# SCHEMA = 'features'
# SCHEMA = 'raw_nfldatapy'

def main():
    """Extract bucket data and save to CSV."""

    # Create data/bucket directory if it doesn't exist
    data_dir = Path.cwd() / "data" / "bucket"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Get bucket adapter with simple DI (1 complexity point)
    bucket = get_bucket_adapter()

    print(f"Extracting {len(TABLES_TO_EXTRACT)} tables from bucket schema '{SCHEMA}'...")

    for table_config in TABLES_TO_EXTRACT:
        # Handle both 'table_name' and ('table_name', {'season': year}) formats
        if isinstance(table_config, tuple):
            table_name, filters = table_config
            season = filters.get('season')
            display_name = f"{table_name}_{season}" if season else table_name
            filter_list = [('season', '==', season)] if season else None
        else:
            table_name = table_config
            display_name = table_name
            filter_list = None

        print(f"\nExtracting {display_name}...")

        try:
            # Detect timestamp-partitioned fact tables
            if table_name in ['fact_odds_raw', 'fact_odds_features']:
                df = bucket.read_timestamp_partitioned_table(table_name, SCHEMA, MAX_EXPORT_RECORDS)
            elif filter_list is not None:
                # Read with filters for partitioned tables
                df = bucket.read_data(table_name, SCHEMA, filters=filter_list)
            else:
                # Standard read for non-partitioned tables
                df = bucket.read_data(table_name, SCHEMA)

            if df.empty:
                print(f"⚠️  No data found for {display_name}")
                continue
        except Exception as e:
            print(f"❌ Error reading {display_name}: {e}")
            logger.error(f"Failed to extract {display_name}: {e}", exc_info=True)
            continue

        print(f"✓ {display_name}: {len(df):,} rows, {len(df.columns)} columns")

        # Limit export to MAX_EXPORT_RECORDS
        df_export = df.head(MAX_EXPORT_RECORDS)
        
        # Save to CSV
        csv_path = data_dir / f"Bucket_{display_name}.csv"
        df_export.to_csv(csv_path, index=False)
        
        if len(df) > MAX_EXPORT_RECORDS:
            print(f"⚠️  Limited export to {MAX_EXPORT_RECORDS:,} of {len(df):,} total records")
        print(f"✓ Saved {display_name} to: {csv_path} ({len(df_export):,} records)")

        # Show sample data
        print(f"\n{display_name.upper()} Sample:")
        print(df_export.head(3))
        print("-" * 50)

    print("\n🎉 Bucket data extraction completed!")
    print(f"Files saved to: {data_dir}")

if __name__ == "__main__":
    main()