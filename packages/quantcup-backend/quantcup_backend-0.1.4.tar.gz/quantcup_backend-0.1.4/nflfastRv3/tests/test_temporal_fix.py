"""Test script to verify temporal leakage fix in rolling metrics."""
from nflfastRv3.features.ml_pipeline.feature_sets.rolling_metrics import create_rolling_metrics_features
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger
import pandas as pd

logger = get_logger('test_temporal_fix')
bucket_adapter = get_bucket_adapter(logger=logger)

print("\n" + "="*80)
print("TESTING TEMPORAL LEAKAGE FIX")
print("="*80)

# Rebuild rolling metrics with the fix
print("\n📊 Rebuilding rolling_metrics_v1 with temporal fix...")
rm_service = create_rolling_metrics_features(logger=logger, bucket_adapter=bucket_adapter)
result = rm_service.build_features(seasons=[2024], save_to_db=True)

if result['status'] != 'success':
    print(f"❌ Failed to build features: {result.get('message', 'Unknown error')}")
    exit(1)

print(f"✅ Built {result['features_built']:,} team-games")

# Read back the features
print("\n📦 Reading rebuilt features from bucket...")
rm = bucket_adapter.read_data('rolling_metrics_v1', 'features', filters=[('season', '==', 2024)])
print(f"✅ Loaded {len(rm):,} rows for 2024 season")

# Test temporal correctness
print("\n🧪 TEMPORAL CORRECTNESS TEST")
print("="*80)

# Pick a team and check Week 1
sample_team = 'KC'
team_data = rm[(rm['team'] == sample_team) & (rm['season'] == 2024)].sort_values('week')

if len(team_data) > 0:
    print(f"\n🏈 Testing team: {sample_team} (2024 season)")
    print(f"   Total games: {len(team_data)}")
    
    # Check Week 1 - should have zero rolling metrics (no prior games)
    week1 = team_data[team_data['week'] == 1].iloc[0]
    
    print(f"\n   Week 1 Rolling Metrics (should all be 0.0):")
    rolling_cols = [c for c in team_data.columns if c.startswith('rolling_')]
    
    all_zero = True
    for col in rolling_cols[:5]:  # Check first 5 rolling metrics
        value = week1[col]
        is_zero = abs(value) < 0.0001
        status = "✅" if is_zero else "❌"
        print(f"      {status} {col}: {value:.4f}")
        if not is_zero:
            all_zero = False
    
    if all_zero:
        print(f"\n   ✅ PASS: Week 1 has zero rolling metrics (no temporal leakage)")
    else:
        print(f"\n   ❌ FAIL: Week 1 has non-zero rolling metrics (temporal leakage still present)")
    
    # Show progression for first 5 weeks
    print(f"\n   Rolling metrics progression (first 5 weeks):")
    display_cols = ['week', 'win', 'rolling_4g_win_rate', 'rolling_4g_epa_offense']
    available_cols = [c for c in display_cols if c in team_data.columns]
    print(team_data[available_cols].head(5).to_string(index=False))
    
    # Manual validation
    print(f"\n   Manual validation:")
    for idx in range(min(5, len(team_data))):
        week_num = team_data.iloc[idx]['week']
        rolling_win_rate = team_data.iloc[idx]['rolling_4g_win_rate']
        
        # For Week 1, should be 0.0 (no prior games)
        # For Week 2, should be win/loss from Week 1
        # For Week 3, should be average of Weeks 1-2
        # etc.
        
        if week_num == 1:
            expected = 0.0
            match = abs(rolling_win_rate - expected) < 0.0001
        else:
            # Calculate expected from prior weeks
            prior_weeks = team_data.iloc[:idx]
            expected = prior_weeks['win'].mean() if len(prior_weeks) > 0 else 0.0
            match = abs(rolling_win_rate - expected) < 0.01
        
        status = "✅" if match else "❌"
        print(f"      {status} Week {week_num}: rolling_4g_win_rate={rolling_win_rate:.4f}, expected≈{expected:.4f}")

else:
    print(f"❌ No data found for team {sample_team} in 2024")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80 + "\n")