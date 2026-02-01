"""
Test script to verify schedule data validation logic.

This tests the validation that the API endpoint uses to check data quality.
"""

from commonv2.domain.schedules import get_upcoming_games, validate_schedule_data
from commonv2.core.logging import get_logger

logger = get_logger('test_validation')

print("=" * 60)
print("Testing Schedule Data Validation")
print("=" * 60)

# Test 1: Get data and check basic info
print("\n" + "=" * 60)
print("TEST 1: Get upcoming games data")
print("=" * 60)
try:
    games = get_upcoming_games(weeks_ahead=1, logger=logger)
    
    print(f"DataFrame Info:")
    print(f"  - Rows: {len(games)}")
    print(f"  - Empty: {games.empty}")
    
    if not games.empty:
        print(f"  - Columns ({len(games.columns)}): {games.columns.tolist()}")
        print(f"\nColumn types:")
        for col in ['home_team', 'away_team', 'gameday', 'week', 'season']:
            if col in games.columns:
                print(f"  - {col}: {games[col].dtype}")
        
        print(f"\nNull value check:")
        for col in ['home_team', 'away_team', 'game_id', 'season', 'week']:
            if col in games.columns:
                null_count = games[col].isnull().sum()
                print(f"  - {col}: {null_count} nulls / {len(games)} total ({null_count/len(games)*100:.1f}%)")
    else:
        print(f"⚠️  WARNING: DataFrame is EMPTY - validation will fail!")
        
except Exception as e:
    print(f"❌ ERROR getting data: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    games = None

# Test 2: Run validation
print("\n" + "=" * 60)
print("TEST 2: Run validate_schedule_data()")
print("=" * 60)

if games is not None:
    try:
        is_valid = validate_schedule_data(games, logger=logger)
        
        if is_valid:
            print(f"✅ VALIDATION PASSED")
            print(f"   The data meets all requirements:")
            print(f"   - DataFrame is not empty")
            print(f"   - Has 'home_team' column")
            print(f"   - Has 'away_team' column")
        else:
            print(f"❌ VALIDATION FAILED")
            print(f"   This is why the API returns 500 error!")
            print(f"\n   Checking what failed:")
            print(f"   - DataFrame empty: {games.empty}")
            print(f"   - Has 'home_team': {'home_team' in games.columns}")
            print(f"   - Has 'away_team': {'away_team' in games.columns}")
            
            if games.empty:
                print(f"\n   ❌ ISSUE: Empty DataFrame - no games returned")
                print(f"      This means the upstream data source (nfl_data_py) is not returning data")
            elif 'home_team' not in games.columns or 'away_team' not in games.columns:
                print(f"\n   ❌ ISSUE: Missing required columns")
                print(f"      Available columns: {games.columns.tolist()}")
                print(f"      This means there's a mismatch in expected column names")
                
    except Exception as e:
        print(f"❌ ERROR during validation: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"⚠️  Cannot run validation - no data retrieved")

# Test 3: Manual validation check
print("\n" + "=" * 60)
print("TEST 3: Manual validation logic check")
print("=" * 60)

if games is not None:
    print("Running the same checks the validator uses:")
    
    # Check 1: Empty DataFrame
    if games.empty:
        print("❌ Check 1 FAILED: DataFrame is empty")
    else:
        print(f"✅ Check 1 PASSED: DataFrame has {len(games)} rows")
    
    # Check 2: Required columns
    required_columns = ['home_team', 'away_team']
    missing_columns = [col for col in required_columns if col not in games.columns]
    
    if missing_columns:
        print(f"❌ Check 2 FAILED: Missing required columns: {missing_columns}")
    else:
        print(f"✅ Check 2 PASSED: All required columns present")
        
        # Additional check: Are they populated?
        for col in required_columns:
            null_count = games[col].isnull().sum()
            if null_count > 0:
                print(f"   ⚠️  WARNING: Column '{col}' has {null_count} null values")
            else:
                print(f"   ✅ Column '{col}' is fully populated")

print("\n" + "=" * 60)
print("Test complete")
print("=" * 60)

print("\n🔍 Summary:")
print("  If validation PASSED but API fails: Issue is in API layer (serialization/response)")
print("  If validation FAILED due to empty DataFrame: Issue is with nfl_data_py data fetching")
print("  If validation FAILED due to missing columns: Issue is with data transformation")
