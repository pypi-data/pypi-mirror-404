#!/usr/bin/env python3
"""
Comprehensive analysis script for Bucket_fact_odds_features.csv

This script performs data quality validation and analysis based on specific feedback
for the odds features dataset, checking:
1. Data structure and completeness (33 columns, bookmaker coverage)
2. NULL handling and missing data patterns
3. Data consistency (participant_ids, timestamp formats, boolean logic)
4. Feature completeness (CLV calculations, anomaly detection)
5. IN_GAME snapshot logical consistency
6. Temporal tracking validation

Based on feedback identifying issues with:
- IN_GAME snapshots showing TRUE for both is_true_opening and is_true_closing
- Missing CLV and odds movement calculations
- Anomaly detection not functioning
- Inconsistent timestamp formats
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

def load_csv(csv_path: str) -> pd.DataFrame:
    """Load the CSV file with error handling."""
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Successfully loaded CSV: {len(df):,} rows, {len(df.columns)} columns")
        return df
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR loading CSV: {e}")
        sys.exit(1)


def analyze_structure(df: pd.DataFrame) -> None:
    """Analyze basic structure and column availability."""
    print("\n" + "="*80)
    print("SECTION 1: DATA STRUCTURE ANALYSIS")
    print("="*80)
    
    print(f"\n📊 Dataset Overview:")
    print(f"  Total Rows: {len(df):,}")
    print(f"  Total Columns: {len(df.columns)}")
    print(f"  Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Expected columns from feedback
    EXPECTED_COLUMNS = [
        'event_id', 'snapshot_timestamp', 'bookmaker_key', 'market_key',
        'selection_type', 'participant_id', 'side', 'odds_price', 'odds_point',
        'implied_probability', 'rank_by_price', 'is_best_price',
        'is_first_snapshot', 'is_last_snapshot',
        'opening_line', 'opening_timestamp', 'closing_line', 'closing_timestamp',
        'closing_line_minutes_before_kickoff', 'is_true_opening', 'is_true_closing',
        'odds_change_from_previous', 'odds_change_direction',
        'line_moved_from_open', 'opening_to_close_movement', 'clv_vs_close',
        'is_anomalous', 'window_label', 'game_slot', '_computed_at',
        '_features_version', '_source_snapshot_count', '_data_quality_flags'
    ]
    
    print(f"\n🔍 Expected Columns (33 total):")
    print(f"{'Column Name':<40} {'Status':<15} {'Data Type':<20} {'Null Count':<15} {'Null %'}")
    print("-" * 105)
    
    for col in EXPECTED_COLUMNS:
        if col in df.columns:
            dtype = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df)) * 100
            status = "✅ FOUND"
            print(f"{col:<40} {status:<15} {dtype:<20} {null_count:<15,} {null_pct:>6.2f}%")
        else:
            print(f"{col:<40} ❌ MISSING")
    
    # Check for unexpected columns
    unexpected_cols = set(df.columns) - set(EXPECTED_COLUMNS)
    if unexpected_cols:
        print(f"\n⚠️  Unexpected columns found: {sorted(unexpected_cols)}")
    
    # Data type summary
    print(f"\n📋 Data Type Distribution:")
    dtype_counts = df.dtypes.value_counts()
    for dtype, count in dtype_counts.items():
        print(f"  {dtype}: {count} columns")


def analyze_bookmakers(df: pd.DataFrame) -> None:
    """Analyze bookmaker coverage and market types."""
    print("\n" + "="*80)
    print("SECTION 2: BOOKMAKER COVERAGE ANALYSIS")
    print("="*80)
    
    if 'bookmaker_key' not in df.columns:
        print("❌ bookmaker_key column not found")
        return
    
    bookmaker_counts = df['bookmaker_key'].value_counts()
    
    print(f"\n📊 Bookmaker Distribution:")
    print(f"  Unique Bookmakers: {df['bookmaker_key'].nunique()}")
    print(f"\n  Top Bookmakers by Record Count:")
    for bookmaker, count in bookmaker_counts.head(15).items():
        pct = (count / len(df)) * 100
        print(f"    {bookmaker:<25} {count:>8,} records ({pct:>5.2f}%)")
    
    # Expected bookmakers from feedback
    EXPECTED_BOOKMAKERS = [
        'betmgm', 'betonlineag', 'betrivers', 'betus', 'bovada',
        'draftkings', 'fanatics', 'fanduel', 'lowvig', 'mybookieag', 'williamhill_us'
    ]
    
    actual_bookmakers = set(df['bookmaker_key'].unique())
    expected_set = set(EXPECTED_BOOKMAKERS)
    
    missing_bookmakers = expected_set - actual_bookmakers
    extra_bookmakers = actual_bookmakers - expected_set
    
    print(f"\n🔍 Expected Bookmaker Validation:")
    print(f"  Expected bookmakers: {len(EXPECTED_BOOKMAKERS)}")
    print(f"  Found bookmakers: {len(actual_bookmakers)}")
    
    if missing_bookmakers:
        print(f"  ⚠️  Missing bookmakers: {sorted(missing_bookmakers)}")
    if extra_bookmakers:
        print(f"  ℹ️  Additional bookmakers: {sorted(extra_bookmakers)}")
    if not missing_bookmakers and not extra_bookmakers:
        print(f"  ✅ All expected bookmakers present")
    
    # Market type analysis
    if 'market_key' in df.columns:
        print(f"\n📊 Market Type Distribution:")
        market_counts = df['market_key'].value_counts()
        for market, count in market_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {market:<20} {count:>8,} records ({pct:>5.2f}%)")


def analyze_null_patterns(df: pd.DataFrame) -> None:
    """Analyze NULL patterns and missing data."""
    print("\n" + "="*80)
    print("SECTION 3: NULL HANDLING & MISSING DATA ANALYSIS")
    print("="*80)
    
    # Identify columns with high NULL rates
    null_summary = []
    for col in df.columns:
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100
        
        # Also check for empty strings
        empty_str_count = 0
        if df[col].dtype == 'object':
            empty_str_count = (df[col] == '').sum()
        
        null_summary.append({
            'column': col,
            'null_count': null_count,
            'null_pct': null_pct,
            'empty_str_count': empty_str_count
        })
    
    null_df = pd.DataFrame(null_summary).sort_values('null_pct', ascending=False)
    
    print(f"\n⚠️  Columns with NULL or Empty Values (Top 20):")
    print(f"{'Column Name':<40} {'NULL Count':<15} {'NULL %':<12} {'Empty Strings'}")
    print("-" * 85)
    
    for _, row in null_df.head(20).iterrows():
        if row['null_pct'] > 0 or row['empty_str_count'] > 0:
            print(f"{row['column']:<40} {row['null_count']:<15,.0f} {row['null_pct']:<12.2f} {row['empty_str_count']:<15,.0f}")
    
    # Specific issue from feedback: odds_point for h2h markets
    if 'market_key' in df.columns and 'odds_point' in df.columns:
        print(f"\n🔍 odds_point NULL Pattern by Market Type:")
        market_null_analysis = df.groupby('market_key').agg({
            'odds_point': lambda x: x.isnull().sum()
        }).rename(columns={'odds_point': 'null_count'})
        market_null_analysis['total'] = df.groupby('market_key').size()
        market_null_analysis['null_pct'] = (market_null_analysis['null_count'] / market_null_analysis['total']) * 100
        
        for market, row in market_null_analysis.iterrows():
            print(f"  {market:<20} {row['null_count']:>8,.0f} / {row['total']:>8,.0f} ({row['null_pct']:>6.2f}%)")
        
        # Check if h2h market has high NULL rate (expected for moneyline)
        if 'h2h' in market_null_analysis.index:
            h2h_null_pct = market_null_analysis.loc['h2h', 'null_pct']
            if pd.notna(h2h_null_pct) and h2h_null_pct > 90:  # type: ignore[operator]
                print(f"  ✅ Expected: h2h markets have NULL odds_point (moneyline doesn't use points)")
        
    # CLV and movement fields
    movement_fields = ['odds_change_from_previous', 'clv_vs_close', 'line_moved_from_open', 'opening_to_close_movement']
    print(f"\n🔍 Movement & CLV Fields NULL Analysis:")
    for field in movement_fields:
        if field in df.columns:
            null_count = df[field].isnull().sum()
            null_pct = (null_count / len(df)) * 100
            empty_str = (df[field] == '').sum() if df[field].dtype == 'object' else 0
            zero_count = (df[field] == 0).sum() if pd.api.types.is_numeric_dtype(df[field]) else 0
            
            print(f"  {field:<35} NULL: {null_count:>6,} ({null_pct:>5.2f}%), Empty: {empty_str:>6,}, Zero: {zero_count:>6,}")


def analyze_data_consistency(df: pd.DataFrame) -> None:
    """Analyze data consistency issues."""
    print("\n" + "="*80)
    print("SECTION 4: DATA CONSISTENCY ANALYSIS")
    print("="*80)
    
    # Participant ID validation
    if 'participant_id' in df.columns:
        print(f"\n🔍 participant_id Format Validation:")
        unique_participants = df['participant_id'].nunique()
        print(f"  Unique participant_ids: {unique_participants}")
        
        # Check ID format (expected: par_01hqmkr1...)
        sample_ids = df['participant_id'].dropna().head(10).tolist()
        print(f"  Sample IDs:")
        for pid in sample_ids[:5]:
            print(f"    {pid}")
        
        # Validate prefix pattern
        prefix_pattern = df['participant_id'].str.startswith('par_', na=False).sum()
        total_non_null = df['participant_id'].notna().sum()
        prefix_pct = (prefix_pattern / total_non_null) * 100 if total_non_null > 0 else 0
        
        print(f"  IDs with 'par_' prefix: {prefix_pattern:,} / {total_non_null:,} ({prefix_pct:.2f}%)")
        if prefix_pct > 95:
            print(f"  ✅ participant_id format consistent")
        else:
            print(f"  ⚠️  Some participant_ids don't follow expected format")
    
    # Boolean field validation
    boolean_fields = ['is_best_price', 'is_first_snapshot', 'is_last_snapshot',
                      'is_true_opening', 'is_true_closing', 'is_anomalous']
    
    print(f"\n🔍 Boolean Field Value Distribution:")
    for field in boolean_fields:
        if field in df.columns:
            value_counts = df[field].value_counts(dropna=False)
            print(f"\n  {field}:")
            for val, count in value_counts.items():
                pct = (count / len(df)) * 100
                print(f"    {val}: {count:,} ({pct:.2f}%)")
    
    # Selection type validation
    if 'selection_type' in df.columns:
        print(f"\n🔍 selection_type Distribution:")
        sel_counts = df['selection_type'].value_counts()
        for sel_type, count in sel_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {sel_type:<20} {count:>8,} ({pct:>6.2f}%)")


def analyze_timestamp_handling(df: pd.DataFrame) -> None:
    """Analyze timestamp formats and consistency."""
    print("\n" + "="*80)
    print("SECTION 5: TIMESTAMP HANDLING ANALYSIS")
    print("="*80)
    
    timestamp_fields = ['snapshot_timestamp', 'opening_timestamp', 'closing_timestamp', '_computed_at']
    
    for field in timestamp_fields:
        if field not in df.columns:
            continue
        
        print(f"\n🔍 {field} Analysis:")
        
        # Sample values
        sample_values = df[field].dropna().head(10).tolist()
        print(f"  Sample values:")
        for val in sample_values[:5]:
            print(f"    {val}")
        
        # Check for UTC offset patterns
        if df[field].dtype == 'object':
            has_utc_offset = df[field].str.contains(r'\+\d{2}:\d{2}', na=False, regex=True).sum()
            no_utc_offset = df[field].str.match(r'^\d{4}-\d{2}-\d{2}', na=False).sum()
            total_non_null = df[field].notna().sum()
            
            print(f"  With UTC offset (+XX:XX): {has_utc_offset:,}")
            print(f"  Without UTC offset: {no_utc_offset:,}")
            print(f"  Total non-NULL: {total_non_null:,}")
            
            if has_utc_offset > 0 and no_utc_offset > 0:
                print(f"  ⚠️  INCONSISTENT: Mixed timestamp formats detected")
            elif has_utc_offset > 0:
                print(f"  ✅ Consistent: All timestamps have UTC offset")
            elif no_utc_offset > 0:
                print(f"  ⚠️  WARNING: No UTC offset in timestamps")


def analyze_feature_completeness(df: pd.DataFrame) -> None:
    """Analyze feature engineering completeness."""
    print("\n" + "="*80)
    print("SECTION 6: FEATURE COMPLETENESS ANALYSIS")
    print("="*80)
    
    # CLV analysis (CRITICAL ISSUE from feedback)
    if 'clv_vs_close' in df.columns:
        print(f"\n🔍 CLV (Closing Line Value) Analysis:")
        
        clv_null = df['clv_vs_close'].isnull().sum()
        clv_zero = (df['clv_vs_close'] == 0).sum()
        clv_nonzero = ((df['clv_vs_close'] != 0) & df['clv_vs_close'].notna()).sum()
        
        print(f"  NULL values: {clv_null:,} ({clv_null/len(df)*100:.2f}%)")
        print(f"  Zero values: {clv_zero:,} ({clv_zero/len(df)*100:.2f}%)")
        print(f"  Non-zero values: {clv_nonzero:,} ({clv_nonzero/len(df)*100:.2f}%)")
        
        if clv_zero / len(df) > 0.5:
            print(f"  ⚠️  CRITICAL: {clv_zero/len(df)*100:.2f}% of CLV values are 0")
            print(f"     This indicates missing calculations or legitimately unchanged lines")
        
        if clv_nonzero > 0:
            print(f"\n  CLV Value Distribution (non-zero):")
            clv_stats = df[df['clv_vs_close'] != 0]['clv_vs_close'].describe()
            print(f"    Mean: {clv_stats['mean']:.4f}")
            print(f"    Std: {clv_stats['std']:.4f}")
            print(f"    Min: {clv_stats['min']:.4f}")
            print(f"    Max: {clv_stats['max']:.4f}")
    
    # Anomaly detection (CRITICAL ISSUE from feedback)
    if 'is_anomalous' in df.columns:
        print(f"\n🔍 Anomaly Detection Analysis:")
        
        anomaly_counts = df['is_anomalous'].value_counts()
        print(f"  Value distribution:")
        for val, count in anomaly_counts.items():
            pct = (count / len(df)) * 100
            print(f"    {val}: {count:,} ({pct:.2f}%)")
        
        anomalous_count = (df['is_anomalous'] == True).sum() if True in anomaly_counts else 0
        if anomalous_count == 0:
            print(f"  ⚠️  CRITICAL: NO anomalies detected - detection logic may not be working")
        else:
            print(f"  ✅ {anomalous_count:,} anomalies detected")
    
    # Implied probability validation
    if 'implied_probability' in df.columns:
        print(f"\n🔍 Implied Probability Validation:")
        
        prob_stats = df['implied_probability'].describe()
        print(f"  Range: {prob_stats['min']:.4f} to {prob_stats['max']:.4f}")
        print(f"  Mean: {prob_stats['mean']:.4f}")
        print(f"  Median: {prob_stats['50%']:.4f}")
        
        # Check for invalid probabilities
        invalid_prob = ((df['implied_probability'] < 0) | (df['implied_probability'] > 1)).sum()
        if invalid_prob > 0:
            print(f"  ⚠️  {invalid_prob:,} records with invalid probabilities (<0 or >1)")
        else:
            print(f"  ✅ All probabilities in valid range [0, 1]")
    
    # Window label coverage
    if 'window_label' in df.columns:
        print(f"\n🔍 Window Label Coverage:")
        window_counts = df['window_label'].value_counts()
        for window, count in window_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {window:<20} {count:>8,} ({pct:>6.2f}%)")
    
    # Game slot coverage
    if 'game_slot' in df.columns:
        print(f"\n🔍 Game Slot Coverage:")
        slot_counts = df['game_slot'].value_counts()
        for slot, count in slot_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {slot:<20} {count:>8,} ({pct:>6.2f}%)")


def analyze_ingame_snapshots(df: pd.DataFrame) -> None:
    """Analyze IN_GAME snapshot logical consistency (CRITICAL ISSUE)."""
    print("\n" + "="*80)
    print("SECTION 7: IN_GAME SNAPSHOT LOGIC VALIDATION")
    print("="*80)
    
    if 'window_label' not in df.columns:
        print("❌ window_label column not found")
        return
    
    # Filter IN_GAME snapshots
    ingame_df = df[df['window_label'] == 'IN_GAME'].copy()
    
    print(f"\n📊 IN_GAME Snapshot Overview:")
    print(f"  Total IN_GAME records: {len(ingame_df):,}")
    print(f"  Percentage of dataset: {len(ingame_df)/len(df)*100:.2f}%")
    
    if len(ingame_df) == 0:
        print("  ℹ️  No IN_GAME snapshots found")
        return
    
    # CRITICAL: Check is_true_opening and is_true_closing for IN_GAME
    if 'is_true_opening' in df.columns and 'is_true_closing' in df.columns:
        print(f"\n🔍 Boolean Logic Validation for IN_GAME:")
        
        both_true = ((ingame_df['is_true_opening'] == True) & 
                     (ingame_df['is_true_closing'] == True)).sum()
        opening_true = (ingame_df['is_true_opening'] == True).sum()
        closing_true = (ingame_df['is_true_closing'] == True).sum()
        both_false = ((ingame_df['is_true_opening'] == False) & 
                      (ingame_df['is_true_closing'] == False)).sum()
        
        print(f"  is_true_opening = TRUE: {opening_true:,} ({opening_true/len(ingame_df)*100:.2f}%)")
        print(f"  is_true_closing = TRUE: {closing_true:,} ({closing_true/len(ingame_df)*100:.2f}%)")
        print(f"  BOTH TRUE: {both_true:,} ({both_true/len(ingame_df)*100:.2f}%)")
        print(f"  BOTH FALSE: {both_false:,} ({both_false/len(ingame_df)*100:.2f}%)")
        
        if both_true > 0:
            print(f"\n  ⚠️  CRITICAL LOGIC ERROR:")
            print(f"     {both_true:,} IN_GAME records have BOTH is_true_opening AND is_true_closing = TRUE")
            print(f"     This is logically inconsistent - IN_GAME snapshots cannot be both opening and closing")
            print(f"     Expected: Both should be FALSE for IN_GAME snapshots")
    
    # Check closing_line_minutes_before_kickoff for IN_GAME
    if 'closing_line_minutes_before_kickoff' in df.columns:
        print(f"\n🔍 closing_line_minutes_before_kickoff for IN_GAME:")
        
        nan_count = ingame_df['closing_line_minutes_before_kickoff'].isna().sum()
        non_nan_count = ingame_df['closing_line_minutes_before_kickoff'].notna().sum()
        
        print(f"  NaN values: {nan_count:,} ({nan_count/len(ingame_df)*100:.2f}%)")
        print(f"  Non-NaN values: {non_nan_count:,} ({non_nan_count/len(ingame_df)*100:.2f}%)")
        
        if nan_count > len(ingame_df) * 0.9:
            print(f"  ✅ Expected: IN_GAME snapshots have NaN for closing_line_minutes_before_kickoff")
        elif non_nan_count > 0:
            print(f"  ⚠️  {non_nan_count:,} IN_GAME records have non-NaN closing_line_minutes_before_kickoff")
    
    # Sample IN_GAME records
    print(f"\n📋 Sample IN_GAME Records (first 5):")
    display_cols = [c for c in ['event_id', 'bookmaker_key', 'window_label', 
                                  'is_true_opening', 'is_true_closing', 
                                  'closing_line_minutes_before_kickoff'] 
                    if c in ingame_df.columns]
    if display_cols:
        print(ingame_df[display_cols].head(5).to_string(index=False))


def analyze_temporal_tracking(df: pd.DataFrame) -> None:
    """Analyze temporal tracking and line movement."""
    print("\n" + "="*80)
    print("SECTION 8: TEMPORAL TRACKING VALIDATION")
    print("="*80)
    
    # Window label progression
    if 'window_label' in df.columns and 'event_id' in df.columns:
        print(f"\n🔍 Window Label Progression by Event:")
        
        # Sample event with multiple windows
        event_counts = df.groupby('event_id')['window_label'].nunique()
        multi_window_events = event_counts[event_counts > 1]
        
        if len(multi_window_events) > 0:
            print(f"  Events with multiple windows: {len(multi_window_events):,}")
            print(f"  Max windows per event: {event_counts.max()}")
            
            # Show sample event progression
            sample_event = multi_window_events.index[0]
            sample_data = df[df['event_id'] == sample_event][
                ['event_id', 'window_label', 'bookmaker_key', 'odds_price']
            ].head(10)
            
            print(f"\n  Sample Event ({sample_event}) Window Progression:")
            print(sample_data.to_string(index=False))
    
    # Opening vs Closing analysis
    if all(col in df.columns for col in ['opening_line', 'closing_line', 'odds_price']):
        print(f"\n🔍 Opening vs Closing Line Analysis:")
        
        has_opening = df['opening_line'].notna().sum()
        has_closing = df['closing_line'].notna().sum()
        has_both = ((df['opening_line'].notna()) & (df['closing_line'].notna())).sum()
        
        print(f"  Records with opening_line: {has_opening:,} ({has_opening/len(df)*100:.2f}%)")
        print(f"  Records with closing_line: {has_closing:,} ({has_closing/len(df)*100:.2f}%)")
        print(f"  Records with BOTH: {has_both:,} ({has_both/len(df)*100:.2f}%)")
        
        # Calculate line movement for records with both
        if has_both > 0:
            movement_df = df[df['opening_line'].notna() & df['closing_line'].notna()].copy()
            movement_df['calc_movement'] = movement_df['closing_line'] - movement_df['opening_line']
            
            moved = (movement_df['calc_movement'] != 0).sum()
            unchanged = (movement_df['calc_movement'] == 0).sum()
            
            print(f"\n  Line Movement Statistics:")
            print(f"    Lines that moved: {moved:,} ({moved/len(movement_df)*100:.2f}%)")
            print(f"    Lines unchanged: {unchanged:,} ({unchanged/len(movement_df)*100:.2f}%)")
            
            if moved > 0:
                print(f"    Movement range: {movement_df['calc_movement'].min():.4f} to {movement_df['calc_movement'].max():.4f}")
                print(f"    Avg movement: {movement_df['calc_movement'].mean():.4f}")


def generate_summary_recommendations(df: pd.DataFrame) -> None:
    """Generate summary and recommendations."""
    print("\n" + "="*80)
    print("SECTION 9: SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    issues_found = []
    recommendations = []
    
    # Check critical issues from feedback
    
    # 1. IN_GAME boolean logic
    if 'window_label' in df.columns and 'is_true_opening' in df.columns:
        ingame_df = df[df['window_label'] == 'IN_GAME']
        if len(ingame_df) > 0:
            both_true = ((ingame_df['is_true_opening'] == True) & 
                        (ingame_df['is_true_closing'] == True)).sum()
            if both_true > 0:
                issues_found.append(f"IN_GAME snapshots: {both_true:,} have both is_true_opening AND is_true_closing = TRUE")
                recommendations.append("Fix IN_GAME boolean logic: Both flags should be FALSE for in-game snapshots")
    
    # 2. CLV calculations
    if 'clv_vs_close' in df.columns:
        clv_zero = (df['clv_vs_close'] == 0).sum()
        if clv_zero / len(df) > 0.5:
            issues_found.append(f"CLV calculations: {clv_zero/len(df)*100:.1f}% are zero")
            recommendations.append("Verify CLV calculation logic - high percentage of zero values")
    
    # 3. Anomaly detection
    if 'is_anomalous' in df.columns:
        anomalous = (df['is_anomalous'] == True).sum()
        if anomalous == 0:
            issues_found.append("Anomaly detection: No anomalies detected in dataset")
            recommendations.append("Review anomaly detection algorithm - may not be functioning")
    
    # 4. Missing movement data
    if 'odds_change_from_previous' in df.columns:
        empty_movement = (df['odds_change_from_previous'] == '').sum() if df['odds_change_from_previous'].dtype == 'object' else 0
        if empty_movement > len(df) * 0.3:
            issues_found.append(f"Odds movement: {empty_movement:,} records with empty odds_change_from_previous")
            recommendations.append("Verify odds movement calculation execution")
    
    # 5. Timestamp consistency
    has_timestamp_inconsistency = False
    if 'snapshot_timestamp' in df.columns and df['snapshot_timestamp'].dtype == 'object':
        has_utc = df['snapshot_timestamp'].str.contains(r'\+\d{2}:\d{2}', na=False, regex=True).sum()
        no_utc = df['snapshot_timestamp'].notna().sum() - has_utc
        if has_utc > 0 and no_utc > 0:
            has_timestamp_inconsistency = True
            issues_found.append("Timestamp formats: Mix of UTC offset and no offset")
            recommendations.append("Standardize timestamp format across all fields")
    
    # Print summary
    print(f"\n✅ STRENGTHS:")
    print(f"   • Comprehensive coverage: {df['bookmaker_key'].nunique()} bookmakers")
    print(f"   • Multiple market types: {df['market_key'].nunique() if 'market_key' in df.columns else 'N/A'}")
    print(f"   • Rich temporal tracking: {df['window_label'].nunique() if 'window_label' in df.columns else 'N/A'} window types")
    print(f"   • Good data volume: {len(df):,} records")
    
    if issues_found:
        print(f"\n⚠️  ISSUES FOUND ({len(issues_found)}):")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
    else:
        print(f"\n✅ NO CRITICAL ISSUES DETECTED")
    
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS ({len(recommendations)}):")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    # Additional recommendations
    print(f"\n📋 ADDITIONAL DATA QUALITY CHECKS:")
    print(f"   • Validate participant_id to team mappings")
    print(f"   • Add data quality checks for downstream ML processing")
    print(f"   • Consider implementing data validation rules for boolean logic")
    print(f"   • Monitor CLV calculations in production environment")


def main():
    """Main analysis execution."""
    print("\n" + "="*80)
    print("BUCKET_FACT_ODDS_FEATURES.CSV COMPREHENSIVE ANALYSIS")
    print("Based on detailed feedback and data quality requirements")
    print("="*80)
    
    # Get CSV path from command line or use default
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        # Default path - user can modify
        csv_path = Path.cwd() / "data" / "Bucket_fact_odds_features.csv"
        print(f"\nℹ️  No CSV path provided. Using default: {csv_path}")
        print(f"   Usage: python {Path(__file__).name} <path_to_csv>")
    
    # Load data
    df = load_csv(csv_path)
    
    # Run all analyses
    analyze_structure(df)
    analyze_bookmakers(df)
    analyze_null_patterns(df)
    analyze_data_consistency(df)
    analyze_timestamp_handling(df)
    analyze_feature_completeness(df)
    analyze_ingame_snapshots(df)
    analyze_temporal_tracking(df)
    generate_summary_recommendations(df)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\n💾 Analysis performed on: {len(df):,} rows, {len(df.columns)} columns")
    print(f"📅 Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
