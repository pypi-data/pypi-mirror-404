"""
Test script to verify CommonV2 backend functions are working correctly.

This tests the domain facade functions that the API uses.
"""

from commonv2.domain.schedules import get_upcoming_games, SeasonParser, get_games_by_week
from commonv2.core.logging import get_logger

logger = get_logger('test_backend')

print("=" * 60)
print("Testing CommonV2 Backend Functions")
print("=" * 60)

# Test 1: Season detection
print("\n" + "=" * 60)
print("TEST 1: SeasonParser.get_current_season()")
print("=" * 60)
try:
    current_season = SeasonParser.get_current_season(logger)
    print(f"✅ Current season: {current_season}")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Upcoming games with weeks_ahead=1
print("\n" + "=" * 60)
print("TEST 2: get_upcoming_games(weeks_ahead=1)")
print("=" * 60)
try:
    games = get_upcoming_games(weeks_ahead=1, logger=logger)
    print(f"✅ Retrieved {len(games)} games")
    
    if games.empty:
        print(f"⚠️  WARNING: DataFrame is EMPTY")
        print(f"   This is likely why the API is failing!")
    else:
        print(f"\nDataFrame Info:")
        print(f"  - Rows: {len(games)}")
        print(f"  - Columns ({len(games.columns)}): {games.columns.tolist()}")
        
        print(f"\nRequired columns check:")
        print(f"  - home_team: {'✅' if 'home_team' in games.columns else '❌ MISSING'}")
        print(f"  - away_team: {'✅' if 'away_team' in games.columns else '❌ MISSING'}")
        print(f"  - gameday: {'✅' if 'gameday' in games.columns else '❌ MISSING'}")
        
        print(f"\nSample games:")
        display_cols = ['game_id', 'season', 'week', 'home_team', 'away_team', 'gameday']
        available_cols = [col for col in display_cols if col in games.columns]
        print(games[available_cols].head())
        
        # Check for null values in critical columns
        if 'home_team' in games.columns:
            null_home = games['home_team'].isnull().sum()
            print(f"\n  - Null home_team values: {null_home}")
        if 'away_team' in games.columns:
            null_away = games['away_team'].isnull().sum()
            print(f"  - Null away_team values: {null_away}")
            
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

# Test 3: Upcoming games with weeks_ahead=4 (what the frontend actually uses)
print("\n" + "=" * 60)
print("TEST 3: get_upcoming_games(weeks_ahead=4) [FRONTEND DEFAULT]")
print("=" * 60)
try:
    games = get_upcoming_games(weeks_ahead=4, logger=logger)
    print(f"✅ Retrieved {len(games)} games")
    
    if games.empty:
        print(f"⚠️  WARNING: DataFrame is EMPTY")
    else:
        print(f"  - Has required columns: home_team={'✅' if 'home_team' in games.columns else '❌'}, away_team={'✅' if 'away_team' in games.columns else '❌'}")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

# Test 4: Get games by week
print("\n" + "=" * 60)
print("TEST 4: get_games_by_week(week=1, season=current)")
print("=" * 60)
try:
    current_season = SeasonParser.get_current_season(logger)
    week_games = get_games_by_week(week=1, season=current_season, logger=logger)
    print(f"✅ Retrieved {len(week_games)} games for Week 1, {current_season}")
    
    if week_games.empty:
        print(f"⚠️  WARNING: DataFrame is EMPTY")
    else:
        print(f"  - Has required columns: home_team={'✅' if 'home_team' in week_games.columns else '❌'}, away_team={'✅' if 'away_team' in week_games.columns else '❌'}")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Test complete")
print("=" * 60)
print("\n🔍 Analysis:")
print("  If all tests show EMPTY DataFrames, the issue is with data fetching (nfl_data_py)")
print("  If tests show data but missing columns, the issue is with data transformation")
print("  If tests succeed but API fails, the issue is in the API layer validation")
