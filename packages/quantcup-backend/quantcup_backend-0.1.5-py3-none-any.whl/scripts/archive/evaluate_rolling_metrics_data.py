"""Enhanced verification script to analyze rolling_metrics feature data."""
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger
import pandas as pd

logger = get_logger('verify_rolling_metrics')
bucket_adapter = get_bucket_adapter(logger=logger)

print("\n" + "="*80)
print("COMPREHENSIVE ROLLING METRICS ANALYSIS FOR FEATURE VALIDATION")
print("="*80)

# Read rolling_metrics from features bucket
print("\n📦 Reading features/rolling_metrics_v1 from bucket...")
try:
    rm = bucket_adapter.read_data('rolling_metrics_v1', 'features')
    print(f"✅ rolling_metrics_v1 loaded: {len(rm):,} rows")
    print(f"✅ Total columns: {len(rm.columns)}")
except Exception as e:
    print(f"❌ Failed to load rolling_metrics_v1: {e}")
    print("\n💡 Generating fresh rolling metrics data...")
    from nflfastRv3.features.ml_pipeline.feature_sets.rolling_metrics import create_rolling_metrics_features
    
    rm_service = create_rolling_metrics_features(logger=logger, bucket_adapter=bucket_adapter)
    result = rm_service.build_features(seasons=[2023], save_to_db=False)
    
    if result['status'] == 'success':
        print(f"✅ Generated rolling metrics: {result['features_built']:,} team-games")
        # Re-read from bucket after generation
        rm = bucket_adapter.read_data('rolling_metrics_v1', 'features')
    else:
        print(f"❌ Failed to generate rolling metrics: {result.get('message', 'Unknown error')}")
        exit(1)

# ============================================================================
# SECTION 1: TEAM-GAME IDENTIFIERS & METADATA
# ============================================================================
print("\n" + "="*80)
print("SECTION 1: TEAM-GAME IDENTIFIERS & METADATA")
print("="*80)

identifier_cols = ['game_id', 'team', 'season', 'week', 'game_date', 'venue']
print(f"\n📋 Identifier Columns:")
for col in identifier_cols:
    if col in rm.columns:
        dtype = rm[col].dtype
        nulls = rm[col].isnull().sum()
        null_pct = (nulls / len(rm)) * 100
        unique = rm[col].nunique()
        sample = rm[col].dropna().head(3).tolist()
        print(f"\n  ✅ {col}")
        print(f"     Data type: {dtype}")
        print(f"     Unique values: {unique:,}")
        print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
        print(f"     Sample: {sample}")
    else:
        print(f"\n  ❌ {col} - NOT FOUND")

# Check grain: team + game_id should be unique
if 'game_id' in rm.columns and 'team' in rm.columns:
    grain_check = rm.groupby(['game_id', 'team']).size()
    duplicates = grain_check[grain_check > 1]
    print(f"\n📊 Grain validation (team + game_id):")
    print(f"   Unique team-games: {len(grain_check):,}")
    print(f"   Duplicate team-games: {len(duplicates):,}")
    if len(duplicates) > 0:
        print(f"   ⚠️  WARNING: Found duplicate team-game combinations!")
        print(f"   Sample duplicates:\n{duplicates.head()}")
    else:
        print(f"   ✅ No duplicates - grain is correct!")

# Team coverage
if 'team' in rm.columns and 'season' in rm.columns:
    teams_per_season = rm.groupby('season')['team'].nunique()
    print(f"\n📊 Team coverage by season:")
    for season, team_count in teams_per_season.items():
        print(f"   Season {season}: {team_count} teams")

# ============================================================================
# SECTION 2: BASE PERFORMANCE METRICS
# ============================================================================
print("\n" + "="*80)
print("SECTION 2: BASE PERFORMANCE METRICS")
print("="*80)

base_metrics = ['points_for', 'points_against', 'point_differential', 'win',
                'offensive_epa', 'defensive_epa', 'epa_per_play_offense', 
                'epa_per_play_defense', 'turnovers_lost', 'turnovers_forced',
                'turnover_differential']
print(f"\n📋 Base Performance Columns:")
for col in base_metrics:
    if col in rm.columns:
        dtype = rm[col].dtype
        nulls = rm[col].isnull().sum()
        null_pct = (nulls / len(rm)) * 100
        
        if pd.api.types.is_numeric_dtype(rm[col]):
            non_null = rm[col].dropna()
            if len(non_null) > 0:
                min_val = non_null.min()
                max_val = non_null.max()
                mean_val = non_null.mean()
                print(f"\n  ✅ {col}")
                print(f"     Data type: {dtype}")
                print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
                print(f"     Range: {min_val:.4f} to {max_val:.4f}")
                print(f"     Mean: {mean_val:.4f}")
        else:
            unique = rm[col].nunique()
            sample = rm[col].dropna().head(3).tolist()
            print(f"\n  ✅ {col}")
            print(f"     Data type: {dtype}")
            print(f"     Unique values: {unique:,}")
            print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
            print(f"     Sample: {sample}")
    else:
        print(f"\n  ❌ {col} - NOT FOUND")

# ============================================================================
# SECTION 3: ROLLING WINDOW METRICS (4, 8, 16 GAMES)
# ============================================================================
print("\n" + "="*80)
print("SECTION 3: ROLLING WINDOW METRICS (4, 8, 16 GAMES)")
print("="*80)

rolling_windows = [4, 8, 16]
rolling_metrics = ['epa_offense', 'epa_defense', 'points_for', 'points_against',
                   'point_diff', 'win_rate', 'turnover_diff', 'red_zone_eff', 
                   'third_down_eff']

print(f"\n📋 Rolling Window Columns:")
for window in rolling_windows:
    print(f"\n  🔄 {window}-Game Rolling Averages:")
    for metric in rolling_metrics:
        col = f'rolling_{window}g_{metric}'
        if col in rm.columns:
            nulls = rm[col].isnull().sum()
            null_pct = (nulls / len(rm)) * 100
            non_null = rm[col].dropna()
            if len(non_null) > 0:
                min_val = non_null.min()
                max_val = non_null.max()
                mean_val = non_null.mean()
                print(f"     ✅ {col}: Range [{min_val:.4f}, {max_val:.4f}], Mean {mean_val:.4f}, Nulls {null_pct:.2f}%")
            else:
                print(f"     ⚠️  {col}: All nulls")
        else:
            print(f"     ❌ {col} - NOT FOUND")

# ============================================================================
# SECTION 4: MOMENTUM INDICATORS
# ============================================================================
print("\n" + "="*80)
print("SECTION 4: MOMENTUM INDICATORS")
print("="*80)

momentum_cols = ['recent_4g_win_rate', 'recent_4g_avg_margin', 'recent_4g_epa_trend',
                 'win_loss_streak', 'epa_per_play_offense_trending', 
                 'epa_per_play_defense_trending', 'point_differential_trending']
print(f"\n📋 Momentum Indicator Columns:")
for col in momentum_cols:
    if col in rm.columns:
        dtype = rm[col].dtype
        nulls = rm[col].isnull().sum()
        null_pct = (nulls / len(rm)) * 100
        non_null = rm[col].dropna()
        if len(non_null) > 0:
            min_val = non_null.min()
            max_val = non_null.max()
            mean_val = non_null.mean()
            print(f"\n  ✅ {col}")
            print(f"     Data type: {dtype}")
            print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
            print(f"     Range: {min_val:.4f} to {max_val:.4f}")
            print(f"     Mean: {mean_val:.4f}")
            
            # Special analysis for win_loss_streak
            if col == 'win_loss_streak':
                positive_streaks = (rm[col] > 0).sum()
                negative_streaks = (rm[col] < 0).sum()
                print(f"     Win streaks (positive): {positive_streaks:,}")
                print(f"     Loss streaks (negative): {negative_streaks:,}")
    else:
        print(f"\n  ❌ {col} - NOT FOUND")

# ============================================================================
# SECTION 5: CONSISTENCY METRICS
# ============================================================================
print("\n" + "="*80)
print("SECTION 5: CONSISTENCY METRICS")
print("="*80)

consistency_cols = ['rolling_4g_epa_offense_std', 'rolling_8g_epa_offense_std',
                    'rolling_4g_point_diff_std', 'rolling_8g_point_diff_std',
                    'rolling_4g_points_for_std', 'rolling_8g_points_for_std',
                    'home_field_advantage', 'outdoor_performance', 'grass_performance']
print(f"\n📋 Consistency Metric Columns:")
for col in consistency_cols:
    if col in rm.columns:
        dtype = rm[col].dtype
        nulls = rm[col].isnull().sum()
        null_pct = (nulls / len(rm)) * 100
        non_null = rm[col].dropna()
        if len(non_null) > 0:
            min_val = non_null.min()
            max_val = non_null.max()
            mean_val = non_null.mean()
            print(f"\n  ✅ {col}")
            print(f"     Data type: {dtype}")
            print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
            print(f"     Range: {min_val:.4f} to {max_val:.4f}")
            print(f"     Mean: {mean_val:.4f}")
    else:
        print(f"\n  ❌ {col} - NOT FOUND")

# ============================================================================
# SECTION 6: SAMPLE TEAM ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("SECTION 6: SAMPLE TEAM ANALYSIS")
print("="*80)

if 'team' in rm.columns and 'season' in rm.columns:
    # Pick a sample team with most games
    team_game_counts = rm['team'].value_counts()
    sample_team = team_game_counts.index[0]
    sample_season = rm[rm['team'] == sample_team]['season'].max()
    
    print(f"\n🏈 Analyzing team: {sample_team} (Season {sample_season})")
    team_data = rm[(rm['team'] == sample_team) & (rm['season'] == sample_season)].sort_values('week')
    
    print(f"\n   Total games: {len(team_data)}")
    
    # Show progression of rolling metrics
    if len(team_data) > 0:
        display_cols = ['week', 'win', 'points_for', 'points_against', 
                       'rolling_4g_win_rate', 'rolling_4g_epa_offense', 
                       'win_loss_streak']
        available_cols = [c for c in display_cols if c in team_data.columns]
        
        print(f"\n   Rolling metrics progression:")
        print(team_data[available_cols].head(10).to_string(index=False))
        
        # Check for proper rolling calculation
        if 'rolling_4g_win_rate' in team_data.columns and 'win' in team_data.columns:
            print(f"\n   🧪 Rolling calculation validation (first 5 games):")
            for idx in range(min(5, len(team_data))):
                game_num = idx + 1
                actual_rolling = team_data.iloc[idx]['rolling_4g_win_rate']
                # Calculate expected rolling average
                wins_so_far = team_data.iloc[:game_num]['win'].sum()
                expected_rolling = wins_so_far / game_num
                print(f"      Game {game_num}: Actual={actual_rolling:.4f}, Expected={expected_rolling:.4f}, Match={abs(actual_rolling - expected_rolling) < 0.001}")

# ============================================================================
# SECTION 7: DATA QUALITY SUMMARY
# ============================================================================
print("\n" + "="*80)
print("SECTION 7: DATA QUALITY SUMMARY")
print("="*80)

# Critical columns for rolling metrics
critical_cols = ['game_id', 'team', 'season', 'week', 'game_date',
                 'points_for', 'points_against', 'win', 'epa_per_play_offense',
                 'rolling_4g_epa_offense', 'rolling_8g_epa_offense', 
                 'rolling_16g_epa_offense', 'win_loss_streak']

print(f"\n✅ Critical columns check:")
all_critical_present = True
for col in critical_cols:
    if col in rm.columns:
        nulls = rm[col].isnull().sum()
        null_pct = (nulls / len(rm)) * 100
        status = "✅" if nulls == 0 else "⚠️"
        print(f"   {status} {col}: {nulls:,} nulls ({null_pct:.2f}%)")
        if nulls > 0:
            all_critical_present = False
    else:
        print(f"   ❌ {col}: MISSING")
        all_critical_present = False

if all_critical_present:
    print(f"\n✅ All critical columns present with no nulls - features ready for ML!")
else:
    print(f"\n⚠️  Some critical columns have issues - review before using in models")

# Check for chronological ordering
if 'team' in rm.columns and 'season' in rm.columns and 'week' in rm.columns:
    print(f"\n📊 Chronological ordering check:")
    # Sample a few teams and verify they're sorted
    sample_teams = rm['team'].unique()[:3]
    all_sorted = True
    for team in sample_teams:
        team_data = rm[rm['team'] == team][['season', 'week']].reset_index(drop=True)
        is_sorted = (team_data['season'].is_monotonic_increasing or 
                    (team_data.groupby('season')['week'].apply(lambda x: x.is_monotonic_increasing).all()))
        print(f"   Team {team}: {'✅ Sorted' if is_sorted else '❌ NOT sorted'}")
        if not is_sorted:
            all_sorted = False
    
    if all_sorted:
        print(f"\n✅ Data is properly sorted by team, season, week")
    else:
        print(f"\n⚠️  Data may not be properly sorted - rolling calculations could be incorrect!")

# ============================================================================
# SECTION 8: FEATURE COMPLETENESS REPORT
# ============================================================================
print("\n" + "="*80)
print("SECTION 8: FEATURE COMPLETENESS REPORT")
print("="*80)

print(f"""
Based on the data analysis above, here's the feature completeness summary:

EXPECTED FEATURE CATEGORIES:
1. Base Performance Metrics (11 features)
   - Points, EPA, turnovers, efficiency metrics
   
2. Rolling Window Metrics (27 features = 9 metrics × 3 windows)
   - 4-game, 8-game, 16-game rolling averages
   - EPA offense/defense, points, win rate, etc.
   
3. Momentum Indicators (7 features)
   - Recent form (4-game), win/loss streaks, trending metrics
   
4. Consistency Metrics (9 features)
   - Standard deviations (4g, 8g), home/away splits, context performance

TOTAL EXPECTED FEATURES: ~54 feature columns + identifiers

ACTUAL COLUMNS IN DATA: {len(rm.columns)}

FEATURE USAGE RECOMMENDATIONS:
- Use rolling_4g_* for recent form (last month)
- Use rolling_8g_* for medium-term trends (half season)
- Use rolling_16g_* for full season performance
- Use *_trending metrics to identify improving/declining teams
- Use *_std metrics to identify consistent vs volatile teams
- Use win_loss_streak for momentum-based predictions
- Use home_field_advantage for venue-specific adjustments
""")

# List all columns for reference
print(f"\n📋 All columns in rolling_metrics_v1 ({len(rm.columns)} total):")
for i, col in enumerate(sorted(rm.columns), 1):
    print(f"   {i:2d}. {col}")

print("\n" + "="*80 + "\n")