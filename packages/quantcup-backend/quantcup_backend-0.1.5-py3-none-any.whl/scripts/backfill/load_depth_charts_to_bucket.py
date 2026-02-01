#!/usr/bin/env python3
"""
One-off script to load historical depth chart data into bucket storage.

This script:
1. Loads depth charts from NFL Data Wrapper API (with rate limiting)
2. Saves to bucket as raw_nfldatapy/depth_chart/data.parquet
3. Handles rate limits with retries and delays

Usage:
    python scripts/load_depth_charts_to_bucket.py

Note: This may take a while due to API rate limits. The script will show progress.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger

logger = get_logger('load_depth_charts')

# Configuration
SCHEMA = 'raw_nfldatapy'
TABLE_NAME = 'depth_chart'
START_YEAR = 2009  # When injury data starts
CURRENT_YEAR = datetime.now().year
RETRY_DELAY = 5  # seconds between retries
MAX_RETRIES = 3

print('=' * 80)
print('LOADING DEPTH CHARTS TO BUCKET')
print('=' * 80)
print(f'Schema: {SCHEMA}')
print(f'Table: {TABLE_NAME}')
print(f'Years: {START_YEAR}-{CURRENT_YEAR}')
print('=' * 80)
print()

# Step 1: Load data from API
print('STEP 1: Loading depth charts from NFL Data Wrapper API')
print('-' * 80)

all_depth_charts = []
failed_years = []

try:
    from nfl_data_wrapper.etl.extract.api import import_depth_charts
    
    years_to_load = list(range(START_YEAR, CURRENT_YEAR + 1))
    total_years = len(years_to_load)
    
    print(f'Loading {total_years} years of depth chart data...')
    print('⚠️  This may take several minutes due to API rate limits')
    print()
    
    for i, year in enumerate(years_to_load, 1):
        print(f'[{i}/{total_years}] Loading {year}...', end=' ', flush=True)
        
        retry_count = 0
        success = False
        
        while retry_count < MAX_RETRIES and not success:
            try:
                df = import_depth_charts(years=[year])
                
                if not df.empty:
                    # Validate data quality - skip invalid/incomplete data
                    if 'season' not in df.columns or df['season'].isnull().all():
                        print(f'⚠️  Skipped - invalid/incomplete data (missing season)')
                        success = True
                        continue
                    
                    # Check for essential columns
                    essential_cols = ['club_code', 'week', 'position', 'depth_team']
                    missing_essential = [col for col in essential_cols if col not in df.columns]
                    if missing_essential:
                        print(f'⚠️  Skipped - missing essential columns: {missing_essential}')
                        success = True
                        continue
                    
                    # Check for 100% null columns
                    null_cols = [col for col in df.columns if df[col].isnull().all()]
                    if null_cols:
                        print(f'✓ {len(df):,} rows | ⚠️  {len(null_cols)} null columns: {null_cols}')
                    else:
                        print(f'✓ {len(df):,} rows')
                    
                    all_depth_charts.append(df)
                    success = True
                else:
                    print(f'⚠️  Empty (no data for {year})')
                    success = True  # Don't retry for empty data
                
                # Small delay to be nice to the API
                if i < total_years:
                    time.sleep(1)
                    
            except Exception as e:
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    print(f'✗ Error (retry {retry_count}/{MAX_RETRIES}): {e}')
                    time.sleep(RETRY_DELAY)
                else:
                    print(f'✗ Failed after {MAX_RETRIES} retries: {e}')
                    failed_years.append(year)
    
    print()
    
    if failed_years:
        print(f'⚠️  Failed to load {len(failed_years)} years: {failed_years}')
        print()
    
    if all_depth_charts:
        # Analyze column differences by year BEFORE concat
        print('\n📊 COLUMN ANALYSIS BY YEAR')
        print('-' * 80)
        base_cols = set()
        for i, df in enumerate(all_depth_charts):
            year = df['season'].iloc[0] if 'season' in df.columns and len(df) > 0 else 'unknown'
            print(f"Year {year}: {len(df.columns)} columns")
            if i == 0:
                base_cols = set(df.columns)
                print(f"  Base columns: {sorted(base_cols)}")
            else:
                new_cols = set(df.columns) - base_cols
                missing_cols = base_cols - set(df.columns)
                if new_cols:
                    print(f"  ⚠️  New columns not in base: {sorted(new_cols)}")
                if missing_cols:
                    print(f"  ⚠️  Missing columns from base: {sorted(missing_cols)}")
                base_cols = base_cols | set(df.columns)
        print()
        
        # Combine all years
        combined_df = pd.concat(all_depth_charts, ignore_index=True)
        
        # Analyze null columns across all data
        print('📊 NULL COLUMN ANALYSIS')
        print('-' * 80)
        null_percentages = {}
        for col in combined_df.columns:
            null_pct = (combined_df[col].isnull().sum() / len(combined_df)) * 100
            null_percentages[col] = null_pct

        # Report 100% null columns
        completely_null = [col for col, pct in null_percentages.items() if pct == 100.0]
        if completely_null:
            print(f'⚠️  Found {len(completely_null)} columns that are 100% NULL:')
            for col in completely_null:
                print(f'   - {col}')
            print()
            
            # Recommend dropping these columns
            print(f'💡 Recommendation: Drop these {len(completely_null)} null columns before saving')
            combined_df = combined_df.drop(columns=completely_null)
            print(f'✓ Dropped {len(completely_null)} null columns')
            print()

        # Report high null columns (>90% but <100%)
        high_null = [col for col, pct in null_percentages.items() if 90.0 < pct < 100.0]
        if high_null:
            print(f'⚠️  Found {len(high_null)} columns with >90% NULL values:')
            for col in high_null:
                print(f'   - {col}: {null_percentages[col]:.1f}% null')
            print()

        print(f'✓ Successfully loaded {len(combined_df):,} total rows')
        print(f'  Columns after cleanup: {len(combined_df.columns)}')
        print(f'  Seasons: {sorted(combined_df["season"].unique())}')
        print(f'  Teams: {combined_df["club_code"].nunique()}')
        print()
        
    else:
        print('✗ No data loaded - exiting')
        sys.exit(1)
        
except ImportError as e:
    print(f'✗ NFL Data Wrapper not available: {e}')
    print('  Install with: pip install nfl_data_wrapper')
    sys.exit(1)
except Exception as e:
    print(f'✗ Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Save to bucket
print('STEP 2: Saving to bucket storage')
print('-' * 80)

try:
    bucket_adapter = get_bucket_adapter(logger=logger)
    
    print(f'Saving {len(combined_df):,} rows to {SCHEMA}/{TABLE_NAME}...')
    
    # Save using bucket adapter's store_data method
    success = bucket_adapter.store_data(
        df=combined_df,
        table_name=TABLE_NAME,
        schema=SCHEMA
    )
    
    if not success:
        raise Exception("store_data returned False")
    
    print(f'✓ Successfully saved to bucket')
    print(f'  Location: {SCHEMA}/{TABLE_NAME}/data.parquet')
    print()
    
except Exception as e:
    print(f'✗ Failed to save to bucket: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Verify
print('STEP 3: Verifying saved data')
print('-' * 80)

try:
    # Read back from bucket
    verify_df = bucket_adapter.read_data(TABLE_NAME, SCHEMA)
    
    print(f'✓ Verification successful')
    print(f'  Rows in bucket: {len(verify_df):,}')
    print(f'  Rows saved: {len(combined_df):,}')
    print(f'  Match: {"✓" if len(verify_df) == len(combined_df) else "✗"}')
    print()
    
    # Show sample
    print('Sample data (first 3 rows):')
    print(verify_df.head(3).to_string())
    print()
    
except Exception as e:
    print(f'⚠️  Could not verify: {e}')
    print()

# Summary
print('=' * 80)
print('SUMMARY')
print('=' * 80)
print(f'✓ Loaded {len(combined_df):,} depth chart records')
print(f'✓ Saved to {SCHEMA}/{TABLE_NAME}/data.parquet')
if failed_years:
    print(f'⚠️  {len(failed_years)} years failed: {failed_years}')
else:
    print(f'✓ All years loaded successfully')
print()
print('Next steps:')
print('  1. Update injury_features.py to read from raw_nfldatapy/depth_chart')
print('  2. Re-run injury feature engineering')
print('  3. Verify starter availability features now have real data')
print('=' * 80)