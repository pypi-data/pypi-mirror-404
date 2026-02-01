"""
NFL.com Injuries Backfill - 2025 Full Season

Scrapes all available 2025 weeks from NFL.com:
- Regular season: Weeks 1-18 (reg1 through reg18)
- Playoffs: Wild Card, Divisional, Conference, Super Bowl

Saves to CSV for analysis before bucket integration.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from odds_scraper.scraperv2 import GenericScraperV2, ScraperConfigV2


# Week configuration for 2025 season
WEEKS_CONFIG = [
    # Regular season (weeks 1-18)
    *[(f'reg{w}', 'REG', w) for w in range(1, 19)],
    
    # Playoffs (NFL.com uses post1, post2, post3, post4)
    ('post1', 'POST', 19),      # Wild Card Round
    ('post2', 'POST', 20),      # Divisional Playoffs
    ('post3', 'POST', 21),      # Conference Championships (AFC/NFC)
    ('post4', 'POST', 22),      # Super Bowl
]


def _process_nfl_injuries(raw_item: Dict) -> List[Dict[str, Any]]:
    """
    Process NFL.com injury data from a game matchup.
    
    Same processor as test script - extracts game metadata + player injuries.
    """
    rows = []
    
    # Extract game-level metadata
    game_header = raw_item.get('game_header', '')
    game_datetime = raw_item.get('game_datetime', '')
    broadcast_info = raw_item.get('broadcast_info', '')
    matchup = raw_item.get('matchup', '')
    
    # Process both teams
    teams = raw_item.get('teams', [])
    
    for team in teams:
        team_name = team.get('team_name', '')
        players = team.get('players', [])
        
        for player in players:
            rows.append({
                # Game metadata
                'game_header': game_header,
                'game_datetime': game_datetime,
                'broadcast_info': broadcast_info,
                'matchup': matchup,
                
                # Team info
                'team': team_name,
                
                # Player injury details
                'player_name': player.get('player_name', ''),
                'position': player.get('position', ''),
                'injury': player.get('injury', ''),
                'practice_status': player.get('practice_status', ''),
                'game_status': player.get('game_status', ''),
            })
    
    return rows


async def scrape_week(week_slug: str, game_type: str, week_num: int, season: int = 2025) -> Optional[pd.DataFrame]:
    """
    Scrape injuries for a specific week.
    
    Args:
        week_slug: URL slug (e.g., 'reg1', 'wildcard', 'superbowl')
        game_type: 'REG' or 'POST'
        week_num: Numeric week identifier (1-22)
        season: NFL season year
        
    Returns:
        DataFrame with injury data or None if failed
    """
    url = f'https://www.nfl.com/injuries/league/{season}/{week_slug}'
    
    # Create config for this week
    config = ScraperConfigV2(
        bookmaker_name='NFL_Com',
        market_type=f'injuries_{week_slug}',
        url=url,
        response_root_key='games',
        agentql_query='''
        {
            games[] {
                game_header
                game_datetime
                broadcast_info
                matchup
                teams[] {
                    team_name
                    players[] {
                        player_name
                        position
                        injury
                        practice_status
                        game_status
                    }
                }
            }
        }
        ''',
        field_mapping={
            'game_header': 'game_header',
            'game_datetime': 'game_datetime',
            'broadcast_info': 'broadcast_info',
            'matchup': 'matchup',
            'teams': 'teams'
        },
        processor_fn=_process_nfl_injuries
    )
    
    print(f"\n{'='*80}")
    print(f"Scraping: {week_slug.upper()} (Week {week_num}, {game_type})")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    scraper = GenericScraperV2(config)
    
    try:
        df = await scraper.scrape(max_retries=2)
        
        if df is not None and not df.empty:
            # Add metadata
            df['season'] = season
            df['week'] = week_num
            df['week_slug'] = week_slug
            df['game_type'] = game_type
            
            print(f"✅ Success: {len(df)} injuries from {df['team'].nunique()} teams")
            print(f"   Teams: {', '.join(sorted(df['team'].unique()[:10]))}")
            if df['team'].nunique() > 10:
                print(f"   ... and {df['team'].nunique() - 10} more")
            
            return df
        else:
            print(f"⚠️  No data returned (may be because week hasn't been played yet)")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def backfill_all_weeks(season: int = 2025, delay_between_weeks: float = 3.0):
    """
    Backfill all available weeks for 2025 season.
    
    Args:
        season: NFL season year
        delay_between_weeks: Seconds to wait between scrapes (be polite to NFL.com)
    """
    print("\n" + "="*80)
    print(f"NFL.COM INJURIES BACKFILL - {season} SEASON")
    print("="*80)
    print(f"Target weeks: {len(WEEKS_CONFIG)} total")
    print(f"  - Regular season: 18 weeks (reg1 through reg18)")
    print(f"  - Playoffs: 4 rounds (wildcard, divisional, conference, superbowl)")
    print(f"Delay between scrapes: {delay_between_weeks}s")
    print("="*80 + "\n")
    
    successful_weeks = []
    failed_weeks = []
    all_dataframes = []
    
    for week_slug, game_type, week_num in WEEKS_CONFIG:
        df = await scrape_week(week_slug, game_type, week_num, season)
        
        if df is not None:
            successful_weeks.append((week_slug, len(df)))
            all_dataframes.append(df)
            
            # Save individual week CSV (for debugging/analysis)
            week_csv_path = Path(f"data/nfl_injuries_backfill/individual_weeks/{season}_{week_slug}.csv")
            week_csv_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(week_csv_path, index=False)
            print(f"   💾 Saved to: {week_csv_path}")
        else:
            failed_weeks.append(week_slug)
        
        # Polite delay (except after last week)
        if week_slug != WEEKS_CONFIG[-1][0]:
            print(f"   ⏳ Waiting {delay_between_weeks}s before next week...")
            await asyncio.sleep(delay_between_weeks)
    
    # Summary
    print("\n" + "="*80)
    print("BACKFILL SUMMARY")
    print("="*80)
    print(f"✅ Successful: {len(successful_weeks)} weeks")
    for week_slug, count in successful_weeks:
        print(f"   - {week_slug}: {count} injuries")
    
    if failed_weeks:
        print(f"\n⚠️  Failed/Unavailable: {len(failed_weeks)} weeks")
        for week_slug in failed_weeks:
            print(f"   - {week_slug} (likely not played yet)")
    
    # Combine all weeks into master file
    if all_dataframes:
        print("\n" + "="*80)
        print("CREATING COMBINED DATASET")
        print("="*80)
        
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        print(f"📊 Total records: {len(combined_df):,}")
        print(f"🏈 Total teams: {combined_df['team'].nunique()}")
        print(f"📅 Weeks covered: {combined_df['week_slug'].nunique()}")
        print(f"🤕 Unique players injured: {combined_df['player_name'].nunique()}")
        
        # Save combined CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_csv_path = Path(f"data/nfl_injuries_backfill/nfl_injuries_{season}_combined_{timestamp}.csv")
        combined_csv_path.parent.mkdir(parents=True, exist_ok=True)
        combined_df.to_csv(combined_csv_path, index=False)
        
        print(f"\n💾 Combined dataset saved:")
        print(f"   {combined_csv_path}")
        print(f"   Size: {combined_csv_path.stat().st_size / 1024:.1f} KB")
        
        # Show statistics
        print("\n" + "="*80)
        print("DATASET STATISTICS")
        print("="*80)
        
        print("\nInjuries by week:")
        week_counts = combined_df.groupby(['week_slug', 'game_type']).size().reset_index(name='count')
        print(week_counts.to_string(index=False))
        
        print("\nTop 10 most injured teams:")
        team_counts = combined_df['team'].value_counts().head(10)
        print(team_counts.to_string())
        
        print("\nTop 10 injury types:")
        injury_counts = combined_df['injury'].value_counts().head(10)
        print(injury_counts.to_string())
        
        print("\nGame status distribution:")
        status_counts = combined_df['game_status'].value_counts()
        print(status_counts.to_string())
        
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("1. ✓ Analyze combined CSV to validate data quality")
        print("2. → Transform to nflverse schema (team abbreviations, etc.)")
        print("3. → Save to bucket (raw_nflcom/injuries)")
        print("4. → Integrate with injury_features.py")
        print("="*80 + "\n")
        
        return combined_df
    else:
        print("\n❌ No data collected - all weeks failed")
        return None


async def main():
    """Main entry point."""
    await backfill_all_weeks(season=2025, delay_between_weeks=3.0)


if __name__ == "__main__":
    asyncio.run(main())
