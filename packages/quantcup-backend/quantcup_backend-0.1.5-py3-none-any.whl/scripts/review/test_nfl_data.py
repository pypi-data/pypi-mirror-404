"""
Test script to verify nfl_data_py is working correctly.

This tests the external data source directly to see if it's returning schedule data.
"""

import nfl_data_py as nfl
from datetime import datetime

print("=" * 60)
print("Testing nfl_data_py.import_schedules()")
print("=" * 60)

# Test current and next season
current_year = datetime.now().year
seasons_to_test = [current_year - 1, current_year, current_year + 1]

print(f"\nTesting seasons: {seasons_to_test}")
print(f"Current date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    schedule_df = nfl.import_schedules(seasons_to_test)
    print(f"\n✅ SUCCESS - Retrieved {len(schedule_df)} games")
    
    if schedule_df.empty:
        print(f"\n⚠️  WARNING: DataFrame is EMPTY!")
    else:
        print(f"\nColumns available ({len(schedule_df.columns)} total):")
        print(f"  {schedule_df.columns.tolist()}")
        
        print(f"\nKey columns present:")
        print(f"  - season: {'✅' if 'season' in schedule_df.columns else '❌'}")
        print(f"  - week: {'✅' if 'week' in schedule_df.columns else '❌'}")
        print(f"  - gameday: {'✅' if 'gameday' in schedule_df.columns else '❌'}")
        print(f"  - home_team: {'✅' if 'home_team' in schedule_df.columns else '❌'}")
        print(f"  - away_team: {'✅' if 'away_team' in schedule_df.columns else '❌'}")
        
        print(f"\nSeasons found: {sorted(schedule_df['season'].unique())}")
        print(f"\nGames per season:")
        for season in sorted(schedule_df['season'].unique()):
            season_games = len(schedule_df[schedule_df['season'] == season])
            print(f"  - {season}: {season_games} games")
        
        print(f"\nFirst 5 games:")
        print(schedule_df[['season', 'week', 'gameday', 'home_team', 'away_team']].head())
        
        # Check for upcoming games
        from datetime import datetime
        import pandas as pd
        today = pd.Timestamp.today().normalize()
        upcoming = schedule_df[pd.to_datetime(schedule_df['gameday']) >= today]
        print(f"\nUpcoming games (from today): {len(upcoming)} games")
        if len(upcoming) > 0:
            print(f"Next game: {upcoming.iloc[0]['gameday']} - {upcoming.iloc[0]['away_team']} @ {upcoming.iloc[0]['home_team']}")
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    
print("\n" + "=" * 60)
print("Test complete")
print("=" * 60)
