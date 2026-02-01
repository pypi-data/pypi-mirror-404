#!/usr/bin/env python3
"""
Compare schedule data from bucket vs Sevalla database.

Compares:
- Bucket: schedules from raw_nflfastr schema
- Database: schedules table from raw_nflfastr schema
- Database: dim_date table (if exists)

Shows differences in row counts, columns, and data quality.

NOTE: Exports are limited to 10,000 records maximum to prevent large file sizes.
"""

# Maximum records to export to CSV (prevents large file sizes)
MAX_EXPORT_RECORDS = 10000

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2._data.database import create_db_engine_from_env, table_exists
from commonv2.core.config import DatabasePrefixes

# Config
BUCKET_SCHEMA = 'raw_nflfastr'
BUCKET_TABLE = 'schedules'
BUCKET_DIM_DATE_SCHEMA = 'warehouse'
BUCKET_DIM_DATE_TABLE = 'dim_date'
DB_SCHEMA = 'raw_nflfastr'
DB_TABLE = 'schedules'


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, name1: str, name2: str):
    """Compare two DataFrames and print differences."""
    
    print(f"\n📊 Row Counts:")
    print(f"  {name1}: {len(df1):,} rows")
    print(f"  {name2}: {len(df2):,} rows")
    print(f"  Difference: {abs(len(df1) - len(df2)):,} rows")
    
    print(f"\n📋 Column Comparison:")
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    
    print(f"  {name1} columns ({len(cols1)}): {sorted(cols1)}")
    print(f"  {name2} columns ({len(cols2)}): {sorted(cols2)}")
    
    only_in_1 = cols1 - cols2
    only_in_2 = cols2 - cols1
    common = cols1 & cols2
    
    if only_in_1:
        print(f"\n  ⚠️  Only in {name1}: {sorted(only_in_1)}")
    if only_in_2:
        print(f"  ⚠️  Only in {name2}: {sorted(only_in_2)}")
    print(f"  ✓ Common columns: {len(common)}")
    
    # Compare common columns
    if common and not df1.empty and not df2.empty:
        print(f"\n🔍 Data Quality (Common Columns):")
        
        for col in sorted(common):
            null_count_1 = df1[col].isna().sum()
            null_count_2 = df2[col].isna().sum()
            
            if null_count_1 > 0 or null_count_2 > 0:
                print(f"  {col}:")
                print(f"    {name1} nulls: {null_count_1:,} ({null_count_1/len(df1)*100:.1f}%)")
                print(f"    {name2} nulls: {null_count_2:,} ({null_count_2/len(df2)*100:.1f}%)")


def show_sample_data(df: pd.DataFrame, name: str, n: int = 5):
    """Show sample data from DataFrame."""
    print(f"\n📄 Sample Data from {name} (first {n} rows):")
    if df.empty:
        print("  (No data)")
    else:
        # Show subset of columns if too many
        if len(df.columns) > 10:
            cols_to_show = list(df.columns[:10])
            print(f"  (Showing first 10 of {len(df.columns)} columns)")
            print(df[cols_to_show].head(n).to_string(index=False))
        else:
            print(df.head(n).to_string(index=False))


def analyze_date_coverage(df: pd.DataFrame, name: str):
    """Analyze date coverage in schedule data."""
    date_cols = ['gameday', 'game_date', 'date']
    date_col = None
    
    for col in date_cols:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col:
        print(f"  ⚠️  No date column found in {name}")
        return
    
    try:
        dates = pd.to_datetime(df[date_col], errors='coerce')
        valid_dates = dates.dropna()
        
        if len(valid_dates) == 0:
            print(f"  ⚠️  No valid dates in {name}")
            return
        
        print(f"\n📅 Date Coverage in {name}:")
        print(f"  Date column: {date_col}")
        print(f"  Valid dates: {len(valid_dates):,} / {len(df):,}")
        print(f"  Date range: {valid_dates.min()} to {valid_dates.max()}")
        
        # Season coverage
        if 'season' in df.columns:
            seasons = df['season'].dropna().unique()
            print(f"  Seasons: {sorted(seasons)}")
        
        # Week coverage
        if 'week' in df.columns:
            weeks = df['week'].dropna().unique()
            print(f"  Weeks: {sorted(weeks)}")
            
    except Exception as e:
        print(f"  ⚠️  Error analyzing dates: {e}")


def main():
    """Compare schedule data from bucket and database."""
    
    print_section("SCHEDULE DATA COMPARISON: Bucket vs Sevalla Database")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Get bucket data
    print_section("1. Loading Bucket Schedule Data")
    bucket = None
    try:
        bucket = get_bucket_adapter()
        df_bucket = bucket.read_data(BUCKET_TABLE, BUCKET_SCHEMA)
        print(f"✓ Loaded bucket data: {len(df_bucket):,} rows from {BUCKET_SCHEMA}.{BUCKET_TABLE}")
    except Exception as e:
        print(f"❌ Failed to load bucket data: {e}")
        df_bucket = pd.DataFrame()
    
    # 2. Get database schedule data
    print_section("2. Loading Database Schedule Data")
    try:
        engine = create_db_engine_from_env(DatabasePrefixes.API_PRODUCTION)
        query = f"SELECT * FROM {DB_SCHEMA}.{DB_TABLE}"
        df_db = pd.read_sql(query, engine)
        print(f"✓ Loaded database data: {len(df_db):,} rows from {DB_SCHEMA}.{DB_TABLE}")
    except Exception as e:
        print(f"❌ Failed to load database schedule data: {e}")
        df_db = pd.DataFrame()
        engine = None
    
    # 3. Get bucket dim_date data
    print_section("3. Loading Bucket dim_date Data")
    df_dim_date = pd.DataFrame()
    
    if bucket:
        try:
            df_dim_date = bucket.read_data(BUCKET_DIM_DATE_TABLE, BUCKET_DIM_DATE_SCHEMA)
            print(f"✓ Loaded bucket dim_date: {len(df_dim_date):,} rows from {BUCKET_DIM_DATE_SCHEMA}.{BUCKET_DIM_DATE_TABLE}")
        except Exception as e:
            print(f"❌ Failed to load bucket dim_date: {e}")
    else:
        print("⚠️  Bucket adapter not available, skipping dim_date")
    
    # Dispose database engine
    if engine:
        engine.dispose()
    
    # 4. Compare bucket vs database schedules
    print_section("4. Bucket vs Database Schedule Comparison")
    
    if df_bucket.empty and df_db.empty:
        print("❌ Both sources are empty - cannot compare")
    elif df_bucket.empty:
        print("⚠️  Bucket data is empty")
        show_sample_data(df_db, "Database", 3)
        analyze_date_coverage(df_db, "Database")
    elif df_db.empty:
        print("⚠️  Database data is empty")
        show_sample_data(df_bucket, "Bucket", 3)
        analyze_date_coverage(df_bucket, "Bucket")
    else:
        compare_dataframes(df_bucket, df_db, "Bucket", "Database")
        analyze_date_coverage(df_bucket, "Bucket")
        analyze_date_coverage(df_db, "Database")
    
    # 5. Show sample data
    if not df_bucket.empty or not df_db.empty:
        print_section("5. Sample Data")
        if not df_bucket.empty:
            show_sample_data(df_bucket, "Bucket", 3)
        if not df_db.empty:
            show_sample_data(df_db, "Database", 3)
    
    # 6. Analyze dim_date if available
    if not df_dim_date.empty:
        print_section("6. dim_date Analysis")
        print(f"Total dates in dim_date: {len(df_dim_date):,}")
        print(f"Columns: {sorted(df_dim_date.columns)}")
        
        # Check date range
        if 'date' in df_dim_date.columns:
            try:
                dates = pd.to_datetime(df_dim_date['date'], errors='coerce')
                valid_dates = dates.dropna()
                if len(valid_dates) > 0:
                    print(f"Date range: {valid_dates.min()} to {valid_dates.max()}")
            except Exception as e:
                print(f"⚠️  Error analyzing dim_date dates: {e}")
        
        show_sample_data(df_dim_date, "dim_date", 3)
    
    # 7. Check for game_id overlap (if column exists)
    if 'game_id' in df_bucket.columns and 'game_id' in df_db.columns:
        print_section("7. Game ID Overlap Analysis")
        
        games_bucket = set(df_bucket['game_id'].dropna().unique())
        games_db = set(df_db['game_id'].dropna().unique())
        
        print(f"Unique games in bucket: {len(games_bucket):,}")
        print(f"Unique games in database: {len(games_db):,}")
        
        overlap = games_bucket & games_db
        only_bucket = games_bucket - games_db
        only_db = games_db - games_bucket
        
        print(f"Games in both: {len(overlap):,}")
        
        if only_bucket:
            print(f"\n⚠️  Games only in bucket: {len(only_bucket):,}")
            if len(only_bucket) <= 10:
                print(f"    {sorted(only_bucket)}")
        if only_db:
            print(f"⚠️  Games only in database: {len(only_db):,}")
            if len(only_db) <= 10:
                print(f"    {sorted(only_db)}")
        if not only_bucket and not only_db:
            print("✓ Both sources have the same games")
    
    # 8. Save comparison report
    print_section("8. Saving Comparison Report")
    
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if not df_bucket.empty:
        # Limit export to MAX_EXPORT_RECORDS
        df_export = df_bucket.head(MAX_EXPORT_RECORDS)
        bucket_path = data_dir / f"schedule_comparison_bucket_{timestamp}.csv"
        df_export.to_csv(bucket_path, index=False)
        
        if len(df_bucket) > MAX_EXPORT_RECORDS:
            print(f"⚠️  Limited export to {MAX_EXPORT_RECORDS:,} of {len(df_bucket):,} total records")
        print(f"✓ Saved bucket data to: {bucket_path} ({len(df_export):,} records)")
    
    if not df_db.empty:
        # Limit export to MAX_EXPORT_RECORDS
        df_export = df_db.head(MAX_EXPORT_RECORDS)
        db_path = data_dir / f"schedule_comparison_database_{timestamp}.csv"
        df_export.to_csv(db_path, index=False)
        
        if len(df_db) > MAX_EXPORT_RECORDS:
            print(f"⚠️  Limited export to {MAX_EXPORT_RECORDS:,} of {len(df_db):,} total records")
        print(f"✓ Saved database data to: {db_path} ({len(df_export):,} records)")
    
    if not df_dim_date.empty:
        # Limit export to MAX_EXPORT_RECORDS
        df_export = df_dim_date.head(MAX_EXPORT_RECORDS)
        dim_date_path = data_dir / f"schedule_comparison_dim_date_{timestamp}.csv"
        df_export.to_csv(dim_date_path, index=False)
        
        if len(df_dim_date) > MAX_EXPORT_RECORDS:
            print(f"⚠️  Limited export to {MAX_EXPORT_RECORDS:,} of {len(df_dim_date):,} total records")
        print(f"✓ Saved dim_date data to: {dim_date_path} ({len(df_export):,} records)")
    
    print_section("COMPARISON COMPLETE")
    print("Review the data directory for detailed CSV files.")


if __name__ == "__main__":
    main()