"""Enhanced verification script to analyze play_by_play data for dim_game design."""
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger
import pandas as pd

logger = get_logger('verify_pbp')
bucket_adapter = get_bucket_adapter(logger=logger)

print("\n" + "="*80)
print("COMPREHENSIVE PLAY_BY_PLAY ANALYSIS FOR DIM_GAME DESIGN")
print("="*80)

# Read play_by_play from raw bucket
print("\n📦 Reading raw_nflfastr/play_by_play from bucket...")
pbp = bucket_adapter.read_data('play_by_play', 'raw_nflfastr')

print(f"✅ play_by_play loaded: {len(pbp):,} rows")
print(f"✅ Total columns: {len(pbp.columns)}")

# ============================================================================
# SECTION 1: GAME IDENTIFIERS & METADATA
# ============================================================================
print("\n" + "="*80)
print("SECTION 1: GAME IDENTIFIERS & METADATA")
print("="*80)

identifier_cols = ['game_id', 'season', 'week', 'game_date', 'season_type']
print(f"\n📋 Identifier Columns:")
for col in identifier_cols:
    if col in pbp.columns:
        dtype = pbp[col].dtype
        nulls = pbp[col].isnull().sum()
        null_pct = (nulls / len(pbp)) * 100
        unique = pbp[col].nunique()
        sample = pbp[col].dropna().head(3).tolist()
        print(f"\n  ✅ {col}")
        print(f"     Data type: {dtype}")
        print(f"     Unique values: {unique:,}")
        print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
        print(f"     Sample: {sample}")
    else:
        print(f"\n  ❌ {col} - NOT FOUND")

# Check game_id uniqueness
if 'game_id' in pbp.columns:
    unique_games = pbp['game_id'].nunique()
    total_rows = len(pbp)
    avg_plays_per_game = total_rows / unique_games
    print(f"\n📊 Game-level statistics:")
    print(f"   Unique games: {unique_games:,}")
    print(f"   Total plays: {total_rows:,}")
    print(f"   Avg plays per game: {avg_plays_per_game:.1f}")

# ============================================================================
# SECTION 2: TEAM INFORMATION
# ============================================================================
print("\n" + "="*80)
print("SECTION 2: TEAM INFORMATION")
print("="*80)

team_cols = ['home_team', 'away_team', 'posteam', 'defteam', 'home_coach', 'away_coach', 'div_game']
print(f"\n📋 Team Columns:")
for col in team_cols:
    if col in pbp.columns:
        dtype = pbp[col].dtype
        nulls = pbp[col].isnull().sum()
        null_pct = (nulls / len(pbp)) * 100
        unique = pbp[col].nunique()
        sample = pbp[col].dropna().head(3).tolist()
        print(f"\n  ✅ {col}")
        print(f"     Data type: {dtype}")
        print(f"     Unique values: {unique:,}")
        print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
        print(f"     Sample: {sample}")
    else:
        print(f"\n  ❌ {col} - NOT FOUND")

# ============================================================================
# SECTION 3: VENUE & WEATHER
# ============================================================================
print("\n" + "="*80)
print("SECTION 3: VENUE & WEATHER")
print("="*80)

venue_cols = ['stadium', 'stadium_id', 'game_stadium', 'location', 'roof', 'surface', 
              'temp', 'wind', 'weather']
print(f"\n📋 Venue/Weather Columns:")
for col in venue_cols:
    if col in pbp.columns:
        dtype = pbp[col].dtype
        nulls = pbp[col].isnull().sum()
        null_pct = (nulls / len(pbp)) * 100
        unique = pbp[col].nunique()
        sample = pbp[col].dropna().head(3).tolist()
        print(f"\n  ✅ {col}")
        print(f"     Data type: {dtype}")
        print(f"     Unique values: {unique:,}")
        print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
        print(f"     Sample: {sample}")
    else:
        print(f"\n  ❌ {col} - NOT FOUND")

# ============================================================================
# SECTION 4: SCORING & OUTCOMES
# ============================================================================
print("\n" + "="*80)
print("SECTION 4: SCORING & OUTCOMES")
print("="*80)

score_cols = ['total_home_score', 'total_away_score', 'result', 'total', 
              'spread_line', 'total_line']
print(f"\n📋 Scoring Columns:")
for col in score_cols:
    if col in pbp.columns:
        dtype = pbp[col].dtype
        nulls = pbp[col].isnull().sum()
        null_pct = (nulls / len(pbp)) * 100
        min_val = pbp[col].min() if pd.api.types.is_numeric_dtype(pbp[col]) else 'N/A'
        max_val = pbp[col].max() if pd.api.types.is_numeric_dtype(pbp[col]) else 'N/A'
        sample = pbp[col].dropna().head(3).tolist()
        print(f"\n  ✅ {col}")
        print(f"     Data type: {dtype}")
        print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
        print(f"     Range: {min_val} to {max_val}")
        print(f"     Sample: {sample}")
    else:
        print(f"\n  ❌ {col} - NOT FOUND")

# Check if scores accumulate correctly
if 'game_id' in pbp.columns and 'total_home_score' in pbp.columns:
    print(f"\n📊 Score accumulation check (sample game):")
    sample_game = pbp['game_id'].iloc[0]
    game_plays = pbp[pbp['game_id'] == sample_game][['game_id', 'total_home_score', 'total_away_score']].head(10)
    print(game_plays.to_string(index=False))

# ============================================================================
# SECTION 5: PLAY-LEVEL STATISTICS (FOR AGGREGATION)
# ============================================================================
print("\n" + "="*80)
print("SECTION 5: PLAY-LEVEL STATISTICS (FOR AGGREGATION)")
print("="*80)

stat_cols = ['yards_gained', 'touchdown', 'interception', 'fumble', 'fumble_lost',
             'field_goal_attempt', 'field_goal_result', 'punt_attempt', 
             'penalty', 'penalty_yards', 'epa', 'wpa']
print(f"\n📋 Play Statistics Columns:")
for col in stat_cols:
    if col in pbp.columns:
        dtype = pbp[col].dtype
        nulls = pbp[col].isnull().sum()
        null_pct = (nulls / len(pbp)) * 100
        unique = pbp[col].nunique()
        
        # For numeric columns, show distribution
        if pd.api.types.is_numeric_dtype(pbp[col]):
            non_null = pbp[col].dropna()
            if len(non_null) > 0:
                min_val = non_null.min()
                max_val = non_null.max()
                mean_val = non_null.mean()
                # Count non-zero values for binary columns
                if unique <= 10:
                    value_counts = pbp[col].value_counts().head(5).to_dict()
                    print(f"\n  ✅ {col}")
                    print(f"     Data type: {dtype}")
                    print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
                    print(f"     Value distribution: {value_counts}")
                else:
                    print(f"\n  ✅ {col}")
                    print(f"     Data type: {dtype}")
                    print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
                    print(f"     Range: {min_val} to {max_val}")
                    print(f"     Mean: {mean_val:.2f}")
        else:
            sample = pbp[col].dropna().head(3).tolist()
            print(f"\n  ✅ {col}")
            print(f"     Data type: {dtype}")
            print(f"     Unique values: {unique:,}")
            print(f"     Nulls: {nulls:,} ({null_pct:.2f}%)")
            print(f"     Sample: {sample}")
    else:
        print(f"\n  ❌ {col} - NOT FOUND")

# ============================================================================
# SECTION 6: AGGREGATION FEASIBILITY TEST
# ============================================================================
print("\n" + "="*80)
print("SECTION 6: AGGREGATION FEASIBILITY TEST")
print("="*80)

if 'game_id' in pbp.columns:
    print(f"\n🧪 Testing aggregation on sample game...")
    sample_game = pbp['game_id'].iloc[0]
    game_data = pbp[pbp['game_id'] == sample_game]
    
    print(f"\n   Game ID: {sample_game}")
    print(f"   Total plays: {len(game_data)}")
    
    # Test key aggregations
    agg_tests = {}
    
    if 'total_home_score' in pbp.columns:
        agg_tests['home_score (max)'] = game_data['total_home_score'].max()
    if 'total_away_score' in pbp.columns:
        agg_tests['away_score (max)'] = game_data['total_away_score'].max()
    if 'yards_gained' in pbp.columns:
        agg_tests['total_yards (sum)'] = game_data['yards_gained'].sum()
    if 'touchdown' in pbp.columns:
        agg_tests['total_touchdowns (sum)'] = game_data['touchdown'].sum()
    if 'interception' in pbp.columns:
        agg_tests['total_interceptions (sum)'] = game_data['interception'].sum()
    if 'fumble_lost' in pbp.columns:
        agg_tests['total_fumbles_lost (sum)'] = game_data['fumble_lost'].sum()
    
    print(f"\n   Aggregation results:")
    for metric, value in agg_tests.items():
        print(f"     {metric}: {value}")

# ============================================================================
# SECTION 7: DATA QUALITY SUMMARY
# ============================================================================
print("\n" + "="*80)
print("SECTION 7: DATA QUALITY SUMMARY")
print("="*80)

# Critical columns for dim_game
critical_cols = ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team',
                 'total_home_score', 'total_away_score']

print(f"\n✅ Critical columns check:")
all_critical_present = True
for col in critical_cols:
    if col in pbp.columns:
        nulls = pbp[col].isnull().sum()
        null_pct = (nulls / len(pbp)) * 100
        status = "✅" if nulls == 0 else "⚠️"
        print(f"   {status} {col}: {nulls:,} nulls ({null_pct:.2f}%)")
        if nulls > 0:
            all_critical_present = False
    else:
        print(f"   ❌ {col}: MISSING")
        all_critical_present = False

if all_critical_present:
    print(f"\n✅ All critical columns present with no nulls - ready for aggregation!")
else:
    print(f"\n⚠️  Some critical columns have issues - review before aggregation")

# ============================================================================
# SECTION 8: RECOMMENDED AGGREGATION STRATEGY
# ============================================================================
print("\n" + "="*80)
print("SECTION 8: RECOMMENDED AGGREGATION STRATEGY")
print("="*80)

print(f"""
Based on the data analysis above, here's the recommended aggregation strategy:

TAKE FIRST (constant per game):
  - game_id, season, week, game_date, season_type
  - home_team, away_team, home_coach, away_coach, div_game
  - stadium, stadium_id, roof, surface, location
  - temp, wind, weather
  - spread_line, total_line

TAKE MAX (accumulates to final value):
  - total_home_score → home_score
  - total_away_score → away_score

SUM (aggregate play-level stats):
  - yards_gained → total_yards
  - touchdown → total_touchdowns
  - interception → total_interceptions
  - fumble_lost → total_fumbles_lost
  - field_goal_attempt → total_field_goal_attempts
  - punt_attempt → total_punts
  - penalty → total_penalties
  - penalty_yards → total_penalty_yards

COUNT (derived):
  - COUNT(*) → total_plays

CALCULATE (post-aggregation):
  - result = home_score - away_score
  - total = home_score + away_score
  - total_turnovers = total_interceptions + total_fumbles_lost
  - home_team_won = (result > 0)
""")

print("="*80 + "\n")