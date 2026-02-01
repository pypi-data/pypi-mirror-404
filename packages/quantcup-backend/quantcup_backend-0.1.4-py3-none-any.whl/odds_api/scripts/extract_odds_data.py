#!/usr/bin/env python3
"""
Config-driven script to extract data from The Odds API and save as CSV files.
Saves results as CSV files in the reports directory.

Following the pattern of nfl_data_wrapper/extract_wrapper_data.py:
- Config-driven with FUNCTIONS_TO_EXTRACT dict
- Flexible and easily modifiable
- Uses ODDS_API_KEY from .env file

NOTE: Exports are limited to 10,000 records maximum to prevent large file sizes.
      Some endpoints use API quota - check comments before running.
"""

# ============================================================================
# CONFIGURATION - Modify these values as needed
# ============================================================================

# Maximum records to export to CSV (prevents large file sizes)
MAX_EXPORT_RECORDS = 1000

# Sport to extract data for
# Options: americanfootball_nfl, basketball_nba, basketball_ncaab, 
#          americanfootball_ncaaf, baseball_mlb, icehockey_nhl
SPORT_KEY = 'americanfootball_nfl'

# Markets for odds data (h2h, spreads, totals)
MARKETS = ['h2h', 'spreads', 'totals']

# Historical data configuration
# ISO8601 format timestamp for historical snapshots (e.g., '2021-10-18T12:00:00Z')
# Available from 2020-06-06, snapshots at 10min intervals (5min after Sept 2022)
HISTORICAL_DATE = '2024-12-01T12:00:00Z'  # Example: Dec 1, 2024 at noon UTC

# ============================================================================

import sys
import os
import pandas as pd
from pathlib import Path

# Add the parent directory to sys.path to import odds_api
sys.path.insert(0, str(Path(__file__).parent.parent))

from odds_api.etl.extract import api
from odds_api.config import get_settings

# Validate API keys are available
settings = get_settings()

# Check which API keys are available
has_free_key = bool(settings.odds_api_key)
has_paid_key = bool(settings.paid_odds_api_key)

if not has_free_key and not has_paid_key:
    raise ValueError(
        "No Odds API keys found. Please set ODDS_API_KEY and/or PAID_ODDS_API_KEY "
        "in your .env file or environment."
    )

print(f"API Keys Status:")
print(f"  🆓 Free Key (ODDS_API_KEY): {'✓ Available' if has_free_key else '✗ Not Set'}")
print(f"  💰 Paid Key (PAID_ODDS_API_KEY): {'✓ Available' if has_paid_key else '✗ Not Set'}")
print()

# Config at the top - easily modifiable
# Functions with their required arguments
# 🆓 = Free (no quota usage, uses ODDS_API_KEY)
# 💰 = Paid (uses API quota, uses PAID_ODDS_API_KEY)
# 💰💰 = Historical (uses 10x API quota, uses PAID_ODDS_API_KEY)
FUNCTIONS_TO_EXTRACT = {
    # 🆓 FREE ENDPOINTS (Uses free ODDS_API_KEY, no quota cost)
    # 'fetch_sports_data': {},                           # List all available sports
    # 'fetch_events_data': {'sport_key': SPORT_KEY},     # Upcoming events/games
    # 'fetch_participants_data': {'sport_key': SPORT_KEY},  # Teams/participants
    
    # 💰 PAID ENDPOINTS (Uses PAID_ODDS_API_KEY and API quota - uncomment to use)
    # 'fetch_odds_data': {'sport_key': SPORT_KEY, 'markets': MARKETS},  # Current odds
    # 'fetch_scores_data': {'sport_key': SPORT_KEY, 'days_from': 3},    # Recent scores
    
    # 💰💰 HISTORICAL ENDPOINTS (Uses PAID_ODDS_API_KEY and 10x API quota - EXPENSIVE!)
    # ⚠️  WARNING: Historical endpoints cost 10x more quota than current endpoints!
    # Cost: 10 x [markets] x [regions]. Example: 3 markets x 1 region = 30 credits per request
    # 'fetch_historical_odds_data': {'sport_key': SPORT_KEY, 'date': HISTORICAL_DATE, 'markets': MARKETS},
    # 'fetch_historical_events_data': {'sport_key': SPORT_KEY, 'date': HISTORICAL_DATE},  # Cost: 1 credit
    
    # 💰💰 HISTORICAL EVENT ODDS - Auto-fetches events first, then loops through each event
    # This pattern: 1) Calls fetch_historical_events_data to get event IDs
    #               2) Loops through each event calling fetch_historical_event_odds_data
    # Note: 'max_events' is a SCRIPT parameter (not an API param) - limits processing
    'fetch_historical_event_odds_data': {
        'sport_key': SPORT_KEY,
        'date': HISTORICAL_DATE,
        'markets': MARKETS,
        # Script control params (not passed to API):
        'max_events': 3,  # Limit number of events to process (None = all)
    },
    
    # Note: fetch_event_odds_data requires specific event_id, not included by default
    # Usage: 'fetch_event_odds_data': {'sport_key': SPORT_KEY, 'event_id': 'abc123', 'markets': MARKETS}
}

# Script-level parameters that should NOT be passed to API functions
SCRIPT_PARAMS = {'max_events'}

def main():
    """Extract data and save to CSV."""
    import time
    
    # Create data directory if it doesn't exist
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(exist_ok=True)
    
    print(f"Extracting {len(FUNCTIONS_TO_EXTRACT)} datasets from The Odds API...")
    print(f"Sport: {SPORT_KEY}")
    print("=" * 70)
    
    for func_name, config_kwargs in FUNCTIONS_TO_EXTRACT.items():
        # Make a copy and separate script-level params from API params
        kwargs = {k: v for k, v in config_kwargs.items() if k not in SCRIPT_PARAMS}
        max_events = config_kwargs.get('max_events', None)
        
        # Determine which key this endpoint will use
        is_historical = func_name.startswith('fetch_historical_')
        is_paid_endpoint = func_name in ['fetch_odds_data', 'fetch_scores_data', 'fetch_event_odds_data'] or is_historical
        
        if is_historical:
            key_type = "💰💰 HISTORICAL (10x cost)"
        elif is_paid_endpoint:
            key_type = "💰 PAID"
        else:
            key_type = "🆓 FREE"
        
        if is_paid_endpoint and not has_paid_key:
            print(f"\n⚠️  Skipping {func_name} - PAID_ODDS_API_KEY not set")
            continue
        elif not is_paid_endpoint and not has_free_key:
            print(f"\n⚠️  Skipping {func_name} - ODDS_API_KEY not set")
            continue
            
        print(f"\n{key_type} | Extracting {func_name}...")
        
        # Special handling for fetch_historical_event_odds_data
        # This function needs event IDs, so we fetch events first, then loop through them
        if func_name == 'fetch_historical_event_odds_data':
            try:
                # STEP 1: Fetch historical events to get event IDs
                print(f"  Step 1: Fetching historical events to get event IDs...")
                events_response = api.fetch_historical_events_data(
                    sport_key=kwargs.get('sport_key', SPORT_KEY),
                    date=kwargs.get('date', HISTORICAL_DATE)
                )
                
                events = events_response.get('data', [])
                snapshot_ts = events_response.get('timestamp')
                previous_ts = events_response.get('previous_timestamp')
                next_ts = events_response.get('next_timestamp')
                
                print(f"  ✓ Found {len(events)} events at snapshot {snapshot_ts}")
                
                if max_events:
                    events = events[:max_events]
                    print(f"  ⚠️  Limited to first {max_events} events")
                
                if not events:
                    print(f"  ⚠️  No events found")
                    continue
                
                # STEP 2: Loop through events and fetch odds for each
                print(f"  Step 2: Fetching odds for {len(events)} events...")
                all_event_data = []
                
                for idx, event in enumerate(events, 1):
                    event_id = event['id']
                    home_team = event.get('home_team', 'Unknown')
                    away_team = event.get('away_team', 'Unknown')
                    
                    print(f"    [{idx}/{len(events)}] {away_team} @ {home_team} (ID: {event_id[:12]}...)")
                    
                    try:
                        # Fetch historical event odds
                        event_odds_response = api.fetch_historical_event_odds_data(
                            sport_key=kwargs.get('sport_key', SPORT_KEY),
                            event_id=event_id,
                            date=kwargs.get('date', HISTORICAL_DATE),
                            markets=kwargs.get('markets', MARKETS)
                        )
                        
                        # Extract the event data
                        event_data = event_odds_response.get('data', {})
                        if event_data:
                            # Add snapshot metadata to event data
                            event_data['_snapshot_timestamp'] = snapshot_ts
                            event_data['_previous_timestamp'] = previous_ts
                            event_data['_next_timestamp'] = next_ts
                            all_event_data.append(event_data)
                            print(f"      ✓ Odds extracted")
                        
                        # Rate limiting - small delay between requests
                        time.sleep(0.2)
                        
                    except Exception as e:
                        print(f"      ❌ Error: {e}")
                        continue
                
                # Convert all events to a combined structure
                if all_event_data:
                    # Create a wrapper similar to historical odds response
                    data = {
                        'timestamp': snapshot_ts,
                        'previous_timestamp': previous_ts,
                        'next_timestamp': next_ts,
                        'data': all_event_data  # List of all events with their odds
                    }
                else:
                    print(f"  ⚠️  No event odds data collected")
                    continue
                    
            except Exception as e:
                print(f"❌ Error in historical event odds workflow: {e}")
                continue
        else:
            # Standard single function call
            func = getattr(api, func_name)
            
            try:
                # Call the function to get data with arguments
                # kwargs only contains valid API parameters (script params removed above)
                data = func(**kwargs)
            except Exception as e:
                print(f"❌ Error extracting {func_name}: {e}")
                continue
        
        # Convert to DataFrame (common for both historical event odds and standard calls)
        try:
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Handle historical endpoint response format
                if 'timestamp' in data and 'data' in data:
                    # Historical endpoints return {timestamp, previous_timestamp, next_timestamp, data}
                    df = pd.DataFrame(data['data'])
                    # Add metadata about the snapshot
                    df['_snapshot_timestamp'] = data.get('timestamp')
                    df['_previous_timestamp'] = data.get('previous_timestamp')
                    df['_next_timestamp'] = data.get('next_timestamp')
                    print(f"📸 Historical Snapshot: {data.get('timestamp')}")
                    print(f"   Previous: {data.get('previous_timestamp')}")
                    print(f"   Next: {data.get('next_timestamp')}")
                # Handle case where API returns dict with 'data' key
                elif 'data' in data:
                    df = pd.DataFrame(data['data'])
                else:
                    df = pd.DataFrame([data])
            else:
                df = pd.DataFrame()
            
            if df.empty:
                print(f"⚠️  No data found for {func_name}")
                continue
            
            print(f"✓ {func_name}: {len(df):,} rows, {len(df.columns)} columns")
            
            # Add extraction metadata
            df['_extracted_at'] = pd.Timestamp.now()
            df['_source_function'] = func_name
            
            # Limit export to MAX_EXPORT_RECORDS
            df_export = df.head(MAX_EXPORT_RECORDS)
            
            # Save to CSV
            csv_name = f"odds_api_{func_name.replace('fetch_', '').replace('_data', '')}.csv"
            csv_path = data_dir / csv_name
            df_export.to_csv(csv_path, index=False)
            
            if len(df) > MAX_EXPORT_RECORDS:
                print(f"⚠️  Limited export to {MAX_EXPORT_RECORDS:,} of {len(df):,} total records")
            print(f"✓ Saved to: {csv_path} ({len(df_export):,} records)")
            
            # Show sample data
            print(f"\n{func_name.upper()} Sample:")
            print(df_export.head(3))
            print("-" * 70)
            
        except Exception as e:
            print(f"❌ Error processing data for {func_name}: {e}")
            continue
    
    print("\n🎉 Data extraction completed!")
    print(f"Files saved to: {data_dir}")
    print("\n💡 Tips:")
    print("  - 🆓 FREE endpoints use ODDS_API_KEY (no quota cost)")
    print("  - 💰 PAID endpoints use PAID_ODDS_API_KEY (uses API quota)")
    print("  - 💰💰 HISTORICAL endpoints use PAID_ODDS_API_KEY (10x quota cost!)")
    print("  - To extract data, uncomment desired endpoints in FUNCTIONS_TO_EXTRACT")
    print("  - For historical data, set HISTORICAL_DATE to desired ISO8601 timestamp")
    print("  - Historical snapshots available from 2020-06-06 at 5-10min intervals")

if __name__ == "__main__":
    main()