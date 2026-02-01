#!/usr/bin/env python3
"""
Compare team data from bucket vs Sevalla database.

Compares:
- Bucket: dim_team from raw_nflfastr schema
- Database: teams table from raw_nflfastr schema

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
from commonv2._data.database import create_db_engine_from_env
from commonv2.core.config import DatabasePrefixes

# Config
BUCKET_SCHEMA = 'warehouse'
BUCKET_TABLE = 'dim_team'
DB_SCHEMA = 'raw_nflfastr'
DB_TABLE = 'teams'


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
        print(df.head(n).to_string(index=False))


def main():
    """Compare team data from bucket and database."""
    
    print_section("TEAM DATA COMPARISON: Bucket vs Sevalla Database")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Get bucket data
    print_section("1. Loading Bucket Data")
    try:
        bucket = get_bucket_adapter()
        df_bucket = bucket.read_data(BUCKET_TABLE, BUCKET_SCHEMA)
        print(f"✓ Loaded bucket data: {len(df_bucket):,} rows from {BUCKET_SCHEMA}.{BUCKET_TABLE}")
    except Exception as e:
        print(f"❌ Failed to load bucket data: {e}")
        df_bucket = pd.DataFrame()
    
    # 2. Get database data
    print_section("2. Loading Database Data")
    try:
        engine = create_db_engine_from_env(DatabasePrefixes.API_PRODUCTION)
        query = f"SELECT * FROM {DB_SCHEMA}.{DB_TABLE}"
        df_db = pd.read_sql(query, engine)
        print(f"✓ Loaded database data: {len(df_db):,} rows from {DB_SCHEMA}.{DB_TABLE}")
        engine.dispose()
    except Exception as e:
        print(f"❌ Failed to load database data: {e}")
        df_db = pd.DataFrame()
    
    # 3. Compare the data
    print_section("3. Data Comparison")
    
    if df_bucket.empty and df_db.empty:
        print("❌ Both sources are empty - cannot compare")
        return
    elif df_bucket.empty:
        print("⚠️  Bucket data is empty")
        show_sample_data(df_db, "Database", 5)
        return
    elif df_db.empty:
        print("⚠️  Database data is empty")
        show_sample_data(df_bucket, "Bucket", 5)
        return
    
    compare_dataframes(df_bucket, df_db, "Bucket", "Database")
    
    # 4. Show sample data
    print_section("4. Sample Data")
    show_sample_data(df_bucket, "Bucket", 3)
    show_sample_data(df_db, "Database", 3)
    
    # 5. Check for team_abbr differences (if column exists)
    if 'team_abbr' in df_bucket.columns and 'team_abbr' in df_db.columns:
        print_section("5. Team Abbreviation Comparison")
        
        teams_bucket = set(df_bucket['team_abbr'].dropna().unique())
        teams_db = set(df_db['team_abbr'].dropna().unique())
        
        print(f"Unique teams in bucket: {len(teams_bucket)}")
        print(f"Unique teams in database: {len(teams_db)}")
        
        only_bucket = teams_bucket - teams_db
        only_db = teams_db - teams_bucket
        
        if only_bucket:
            print(f"\n⚠️  Teams only in bucket: {sorted(only_bucket)}")
        if only_db:
            print(f"⚠️  Teams only in database: {sorted(only_db)}")
        if not only_bucket and not only_db:
            print("✓ Both sources have the same teams")
    
    # 6. Save comparison report
    print_section("6. Saving Comparison Report")
    
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if not df_bucket.empty:
        # Limit export to MAX_EXPORT_RECORDS
        df_export = df_bucket.head(MAX_EXPORT_RECORDS)
        bucket_path = data_dir / f"team_comparison_bucket_{timestamp}.csv"
        df_export.to_csv(bucket_path, index=False)
        
        if len(df_bucket) > MAX_EXPORT_RECORDS:
            print(f"⚠️  Limited export to {MAX_EXPORT_RECORDS:,} of {len(df_bucket):,} total records")
        print(f"✓ Saved bucket data to: {bucket_path} ({len(df_export):,} records)")
    
    if not df_db.empty:
        # Limit export to MAX_EXPORT_RECORDS
        df_export = df_db.head(MAX_EXPORT_RECORDS)
        db_path = data_dir / f"team_comparison_database_{timestamp}.csv"
        df_export.to_csv(db_path, index=False)
        
        if len(df_db) > MAX_EXPORT_RECORDS:
            print(f"⚠️  Limited export to {MAX_EXPORT_RECORDS:,} of {len(df_db):,} total records")
        print(f"✓ Saved database data to: {db_path} ({len(df_export):,} records)")
    
    print_section("COMPARISON COMPLETE")
    print("Review the data directory for detailed CSV files.")


if __name__ == "__main__":
    main()