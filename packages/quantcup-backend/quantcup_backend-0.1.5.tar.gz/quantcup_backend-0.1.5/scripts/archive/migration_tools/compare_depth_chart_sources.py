"""
Compare depth chart data from NFL Data Wrapper API vs Bucket storage.

This script helps identify schema differences and data availability
between the two sources to understand why starter availability features
aren't working with bucket data.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger

logger = get_logger('compare_depth_charts')

print('=' * 80)
print('DEPTH CHART DATA SOURCE COMPARISON')
print('=' * 80)
print()

# Test season
TEST_SEASON = 2024

# ============================================================================
# PART 1: Load from NFL Data Wrapper API
# ============================================================================
print('PART 1: NFL Data Wrapper API')
print('-' * 80)

api_depth_chart = None
try:
    from nfl_data_wrapper.etl.extract.api import import_depth_charts
    
    print(f'Loading depth charts for season {TEST_SEASON} from API...')
    api_depth_chart = import_depth_charts(years=[TEST_SEASON])
    
    if not api_depth_chart.empty:
        print(f'✓ Loaded {len(api_depth_chart):,} rows from API')
        print(f'\nAPI Columns ({len(api_depth_chart.columns)}):')
        print(f'  {list(api_depth_chart.columns)}')
        
        print(f'\nAPI Sample Data (first 3 rows):')
        print(api_depth_chart.head(3).to_string())
        
        # Check for key columns
        key_columns = ['season', 'week', 'game_type', 'club_code', 'team', 
                      'pos_abb', 'position', 'pos_rank', 'depth_order']
        print(f'\nKey Column Availability:')
        for col in key_columns:
            status = '✓' if col in api_depth_chart.columns else '✗'
            print(f'  {status} {col}')
        
        # Data coverage
        if 'season' in api_depth_chart.columns:
            seasons = sorted(api_depth_chart['season'].dropna().unique())
            print(f'\nSeasons: {seasons}')
        
        if 'week' in api_depth_chart.columns:
            weeks = sorted(api_depth_chart['week'].dropna().unique())
            print(f'Weeks: {weeks}')
        
        if 'game_type' in api_depth_chart.columns:
            game_types = api_depth_chart['game_type'].unique()
            print(f'Game types: {game_types}')
            
        team_col = 'club_code' if 'club_code' in api_depth_chart.columns else 'team'
        if team_col in api_depth_chart.columns:
            teams = api_depth_chart[team_col].nunique()
            print(f'Teams: {teams}')
            
    else:
        print('⚠️  API returned empty DataFrame')
        
except ImportError as e:
    print(f'✗ NFL Data Wrapper not available: {e}')
except Exception as e:
    print(f'✗ Failed to load from API: {e}')
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# PART 2: Load from Bucket
# ============================================================================
print('PART 2: Bucket Storage (raw_nflfastr/depth_chart)')
print('-' * 80)

bucket_depth_chart = None
try:
    bucket_adapter = get_bucket_adapter(logger=logger)
    
    print(f'Loading depth charts from bucket...')
    bucket_depth_chart = bucket_adapter.read_data('depth_chart', 'raw_nflfastr')
    
    if not bucket_depth_chart.empty:
        print(f'✓ Loaded {len(bucket_depth_chart):,} rows from bucket')
        print(f'\nBucket Columns ({len(bucket_depth_chart.columns)}):')
        print(f'  {list(bucket_depth_chart.columns)}')
        
        print(f'\nBucket Sample Data (first 3 rows):')
        print(bucket_depth_chart.head(3).to_string())
        
        # Check for key columns
        key_columns = ['season', 'week', 'game_type', 'club_code', 'team', 
                      'pos_abb', 'position', 'pos_rank', 'depth_order', 'dt']
        print(f'\nKey Column Availability:')
        for col in key_columns:
            status = '✓' if col in bucket_depth_chart.columns else '✗'
            print(f'  {status} {col}')
        
        # Data coverage
        if 'season' in bucket_depth_chart.columns:
            seasons = sorted(bucket_depth_chart['season'].dropna().unique())
            print(f'\nSeasons: {seasons}')
        elif 'dt' in bucket_depth_chart.columns:
            print(f'\nTimestamp range:')
            print(f'  Earliest: {bucket_depth_chart["dt"].min()}')
            print(f'  Latest: {bucket_depth_chart["dt"].max()}')
        
        if 'week' in bucket_depth_chart.columns:
            weeks = sorted(bucket_depth_chart['week'].dropna().unique())
            print(f'Weeks: {weeks}')
        
        if 'game_type' in bucket_depth_chart.columns:
            game_types = bucket_depth_chart['game_type'].unique()
            print(f'Game types: {game_types}')
            
        if 'team' in bucket_depth_chart.columns:
            teams = bucket_depth_chart['team'].nunique()
            print(f'Teams: {teams}')
            
    else:
        print('⚠️  Bucket returned empty DataFrame')
        
except Exception as e:
    print(f'✗ Failed to load from bucket: {e}')
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# PART 3: Schema Comparison
# ============================================================================
print('PART 3: Schema Comparison')
print('-' * 80)

if api_depth_chart is not None and bucket_depth_chart is not None:
    api_cols = set(api_depth_chart.columns)
    bucket_cols = set(bucket_depth_chart.columns)
    
    # Columns only in API
    api_only = api_cols - bucket_cols
    if api_only:
        print(f'\nColumns ONLY in API ({len(api_only)}):')
        for col in sorted(api_only):
            print(f'  - {col}')
    
    # Columns only in Bucket
    bucket_only = bucket_cols - api_cols
    if bucket_only:
        print(f'\nColumns ONLY in Bucket ({len(bucket_only)}):')
        for col in sorted(bucket_only):
            print(f'  - {col}')
    
    # Common columns
    common = api_cols & bucket_cols
    if common:
        print(f'\nCommon Columns ({len(common)}):')
        for col in sorted(common):
            print(f'  - {col}')
    
    # Critical missing columns for injury features
    required_for_injury = ['season', 'week', 'game_type', 'pos_rank']
    print(f'\nRequired Columns for Injury Features:')
    for col in required_for_injury:
        api_has = '✓' if col in api_cols else '✗'
        bucket_has = '✓' if col in bucket_cols else '✗'
        print(f'  {col:20s} | API: {api_has} | Bucket: {bucket_has}')

else:
    print('⚠️  Cannot compare - one or both sources failed to load')

print()

# ============================================================================
# PART 4: Recommendations
# ============================================================================
print('PART 4: Recommendations')
print('-' * 80)

if bucket_depth_chart is not None and not bucket_depth_chart.empty:
    missing_critical = []
    for col in ['season', 'week', 'game_type']:
        if col not in bucket_depth_chart.columns:
            missing_critical.append(col)
    
    if missing_critical:
        print(f'\n⚠️  Bucket depth chart is missing critical columns: {missing_critical}')
        print(f'\nThis explains why starter availability features return zeros.')
        print(f'\nOptions:')
        print(f'  1. Update ETL to include season/week/game_type in bucket depth charts')
        print(f'  2. Use API data for depth charts (keep bucket for injuries)')
        print(f'  3. Use alternative data source (rosters, snap counts) for starter identification')
    else:
        print(f'\n✓ Bucket depth chart has all required columns')
        print(f'   Starter availability features should work')

print()
print('=' * 80)
print('COMPARISON COMPLETE')
print('=' * 80)