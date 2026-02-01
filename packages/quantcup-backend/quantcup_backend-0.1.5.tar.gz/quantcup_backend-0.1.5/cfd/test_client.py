#!/usr/bin/env python3
"""
Simple test script for College Football Data API wrapper.
Tests a few key endpoints to verify the wrapper is working.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cfd

def test_basic_endpoints():
    """Test basic endpoints to verify API connectivity."""
    
    print("Testing College Football Data API Wrapper")
    print("=" * 70)
    
    # Test 1: Get conferences (no parameters required)
    print("\n1. Testing get_conferences()...")
    conferences = cfd.get_conferences()
    if not conferences.empty:
        print(f"✓ Success: Found {len(conferences)} conferences")
        print(f"  Sample: {conferences['name'].head(3).tolist()}")
    else:
        print("✗ Failed: No conferences found")
    
    # Test 2: Get FBS teams
    print("\n2. Testing get_fbs_teams(year=2024)...")
    teams = cfd.get_fbs_teams(year=2024)
    if not teams.empty:
        print(f"✓ Success: Found {len(teams)} FBS teams")
        print(f"  Sample: {teams['school'].head(3).tolist()}")
    else:
        print("✗ Failed: No teams found")
    
    # Test 3: Get venues
    print("\n3. Testing get_venues()...")
    venues = cfd.get_venues()
    if not venues.empty:
        print(f"✓ Success: Found {len(venues)} venues")
        print(f"  Sample: {venues['name'].head(3).tolist()}")
    else:
        print("✗ Failed: No venues found")
    
    # Test 4: Get calendar
    print("\n4. Testing get_calendar(year=2024)...")
    calendar = cfd.get_calendar(year=2024)
    if not calendar.empty:
        print(f"✓ Success: Found {len(calendar)} weeks")
        print(f"  Weeks: {calendar['week'].tolist()}")
    else:
        print("✗ Failed: No calendar found")
    
    # Test 5: Get rankings (if available)
    print("\n5. Testing get_rankings(year=2024, week=10)...")
    rankings = cfd.get_rankings(year=2024, week=10)
    if not rankings.empty:
        print(f"✓ Success: Found {len(rankings)} poll rankings")
        # Show top 5 if available
        if 'rank' in rankings.columns and 'school' in rankings.columns:
            top_5 = rankings[rankings['rank'] <= 5].sort_values('rank')
            if not top_5.empty:
                print("  Top 5:")
                for _, row in top_5.iterrows():
                    print(f"    {row['rank']}. {row['school']}")
    else:
        print("⚠️  No rankings found (may not be available yet)")
    
    # Test 6: Get games
    print("\n6. Testing get_games(year=2024, week=10)...")
    games = cfd.get_games(year=2024, week=10)
    if not games.empty:
        print(f"✓ Success: Found {len(games)} games")
        if 'home_team' in games.columns and 'away_team' in games.columns:
            print(f"  Sample matchups:")
            for _, game in games.head(3).iterrows():
                print(f"    {game['away_team']} @ {game['home_team']}")
    else:
        print("⚠️  No games found (may not be available yet)")
    
    print("\n" + "=" * 70)
    print("Testing complete!")
    print("\nNote: Some endpoints may return no data depending on the current")
    print("season and week. This is normal and doesn't indicate an error.")

if __name__ == "__main__":
    test_basic_endpoints()