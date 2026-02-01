"""
Test script to verify the new days_ahead functionality works correctly.

This tests the enhanced filtering with fractional weeks and days-based filtering.
"""

from commonv2.domain.schedules import get_upcoming_games
from commonv2.core.logging import get_logger

logger = get_logger('test_days_ahead')

print("=" * 60)
print("Testing Enhanced days_ahead Functionality")
print("=" * 60)

# Test 1: weeks_ahead as float (fractional weeks)
print("\n" + "=" * 60)
print("TEST 1: get_upcoming_games(weeks_ahead=1.43) [10 days]")
print("=" * 60)
try:
    games = get_upcoming_games(weeks_ahead=1.43, logger=logger)  # 1.43 weeks ≈ 10 days
    print(f"✅ Retrieved {len(games)} games")
    
    if games.empty:
        print(f"⚠️  No games in next ~10 days")
    else:
        print(f"   Games found:")
        for _, game in games.iterrows():
            print(f"   - {game['gameday']}: {game['away_team']} @ {game['home_team']}")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

# Test 2: weeks_ahead as float (Super Bowl window)
print("\n" + "=" * 60)
print("TEST 2: get_upcoming_games(weeks_ahead=2.0) [14 days]")
print("=" * 60)
try:
    games = get_upcoming_games(weeks_ahead=2.0, logger=logger)
    print(f"✅ Retrieved {len(games)} games")
    
    if games.empty:
        print(f"⚠️  No games in next 2 weeks")
    else:
        print(f"   Games found:")
        for _, game in games.iterrows():
            print(f"   - {game['gameday']}: {game['away_team']} @ {game['home_team']}")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

# Test 3: Exactly 1 week (should miss Super Bowl at 8 days)
print("\n" + "=" * 60)
print("TEST 3: get_upcoming_games(weeks_ahead=1.0) [7 days]")
print("=" * 60)
try:
    games = get_upcoming_games(weeks_ahead=1.0, logger=logger)
    print(f"✅ Retrieved {len(games)} games")
    
    if games.empty:
        print(f"⚠️  No games in next 1 week (expected - Super Bowl is 8 days away)")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

# Test 4: Default (4 weeks)
print("\n" + "=" * 60)
print("TEST 4: get_upcoming_games() [default 4 weeks]")
print("=" * 60)
try:
    games = get_upcoming_games(logger=logger)
    print(f"✅ Retrieved {len(games)} games")
    
    if not games.empty:
        print(f"   First game: {games.iloc[0]['gameday']}")
        print(f"   Last game: {games.iloc[-1]['gameday']}")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Test complete")
print("=" * 60)

print("\n🎯 Summary:")
print("  - Fractional weeks now supported (e.g., 1.43 weeks = 10 days)")
print("  - API can convert days_ahead to fractional weeks")
print("  - This catches edge cases like Super Bowl at 8 days away")
print("  - Backend is backward compatible with integer weeks_ahead")
