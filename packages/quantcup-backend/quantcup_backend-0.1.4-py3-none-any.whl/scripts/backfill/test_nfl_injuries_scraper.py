"""
NFL.com Injuries Scraper - Test Script (Single Week)

Based on odds_scraper/scraperv2.py architecture.
Tests scraping one week to validate AgentQL query and field extraction.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from odds_scraper.scraperv2 import GenericScraperV2, ScraperConfigV2


def _process_nfl_injuries(raw_item: Dict) -> List[Dict[str, Any]]:
    """
    Process NFL.com injury data from a game matchup.
    
    NFL.com structure:
    - Each page shows games for a specific week
    - Each game has two team sections (home and away)
    - Each team section has a table of injured players
    
    Args:
        raw_item: Raw game data from AgentQL
        
    Returns:
        List of player injury records (one per player)
    """
    rows = []
    
    # Extract game-level metadata
    game_header = raw_item.get('game_header', '')  # e.g., "THURSDAY, SEPTEMBER 4TH"
    game_datetime = raw_item.get('game_datetime', '')  # e.g., "8:20 PM EDT"
    broadcast_info = raw_item.get('broadcast_info', '')  # e.g., "NBC, TELEMUNDO, UNIVERSO"
    
    # Extract matchup info
    matchup = raw_item.get('matchup', '')  # e.g., "(7-9-1) Cowboys @ Eagles (11-6)"
    
    # Process both teams (Cowboys and Eagles sections)
    teams = raw_item.get('teams', [])
    
    for team in teams:
        team_name = team.get('team_name', '')  # e.g., "Cowboys"
        
        # Process each player in the team's injury table
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


# NFL.com Injuries Configuration
NFL_COM_INJURIES = ScraperConfigV2(
    bookmaker_name='NFL_Com',
    market_type='injuries',
    url='https://www.nfl.com/injuries/league/2025/reg1',  # Will test week 1
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


async def test_week_1():
    """Test scraping NFL injuries for 2025 week 1."""
    
    print("\n" + "="*80)
    print("NFL.com Injuries Scraper - Week 1 Test")
    print("="*80 + "\n")
    
    print(f"📡 Target URL: {NFL_COM_INJURIES.url}")
    print(f"🔍 Extracting: Game metadata + Team injury tables")
    print(f"⚙️  Using: AgentQL natural language query\n")
    
    # Create scraper
    scraper = GenericScraperV2(NFL_COM_INJURIES)
    
    # Scrape data
    df = await scraper.scrape()
    
    if df is not None and not df.empty:
        print("\n" + "="*80)
        print("✅ SCRAPING SUCCESS")
        print("="*80 + "\n")
        
        # Add season/week metadata
        df['season'] = 2025
        df['week'] = 1
        df['game_type'] = 'REG'
        
        # Display results
        print(f"📊 Total records: {len(df)}")
        print(f"🏈 Teams found: {df['team'].nunique()}")
        print(f"📋 Columns: {list(df.columns)}\n")
        
        # Show sample data
        print("="*80)
        print("SAMPLE DATA (First 5 records)")
        print("="*80)
        print(df[['team', 'player_name', 'position', 'injury', 'practice_status', 'game_status']].head(5).to_string())
        print()
        
        # Show statistics
        print("="*80)
        print("STATISTICS")
        print("="*80)
        print(f"Players by team:")
        print(df['team'].value_counts().to_string())
        print()
        
        print(f"Injury types:")
        injury_counts = df['injury'].value_counts().head(10)
        print(injury_counts.to_string())
        print()
        
        print(f"Game status distribution:")
        status_counts = df['game_status'].value_counts()
        print(status_counts.to_string())
        print()
        
        # Save to CSV for inspection
        csv_path = scraper.save_to_csv(df, export_dir="data/nfl_injuries_test")
        print(f"💾 CSV exported: {csv_path}\n")
        
        # Save to bucket
        print("☁️  Saving to bucket...")
        bucket_success = scraper.save_to_bucket(
            df=df,
            table_name='injuries_week1_test',
            schema='raw_nflcom'
        )
        
        if bucket_success:
            print("✓ Bucket storage successful\n")
        else:
            print("⚠️  Bucket storage failed (check bucket configuration)\n")
        
        return df
    
    else:
        print("\n" + "="*80)
        print("❌ SCRAPING FAILED")
        print("="*80 + "\n")
        print("Possible issues:")
        print("  - Page structure changed (AgentQL query needs update)")
        print("  - Network error (check connection)")
        print("  - AgentQL API key missing or invalid")
        print("  - Page requires authentication or geo-blocking")
        print("\nCheck logs for detailed error messages.\n")
        return None


async def main():
    """Main entry point."""
    df = await test_week_1()
    
    if df is not None:
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("1. ✓ Validate scraped data in CSV export")
        print("2. ✓ Check bucket storage (raw_nflcom/injuries_week1_test)")
        print("3. → If successful, run full backfill for weeks 1-20")
        print("4. → Integrate with injury_features.py for ML pipeline")
        print()


if __name__ == "__main__":
    asyncio.run(main())
