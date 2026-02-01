#!/usr/bin/env python3
"""
Diagnostic Script: Analyze Available Snapshots for a Single Game

Pulls all available historical snapshots for a specific game and exports to CSV.
Useful for analyzing in-game snapshot availability and timing patterns.

Usage:
    python scripts/diagnostics/analyze_game_snapshots.py --event-id <event_id> --commence-time <kickoff_time>
    
Example:
    python scripts/diagnostics/analyze_game_snapshots.py \
        --event-id af6fbb0a2e996613bc393115276c60e2 \
        --commence-time "2025-09-28T20:25:00Z"
"""

import argparse
import csv
from datetime import datetime, timedelta
from dateutil.parser import isoparse
from typing import List, Dict, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from odds_api.etl.extract.api import fetch_historical_events_data
from commonv2.core.logging import setup_logger

logger = setup_logger('analyze_game_snapshots', project_name='ODDS_API')


def backward_crawl_all_snapshots(
    event_id: str,
    start_time: datetime,
    end_time: datetime,
    sport_key: str = 'americanfootball_nfl'
) -> List[Dict[str, Any]]:
    """
    Crawl backward from end_time to collect ALL available snapshots.
    
    Args:
        event_id: The game/event ID to search for
        start_time: Start of game (kickoff)
        end_time: End of game window (typically kickoff + 3-4 hours)
        sport_key: Sport identifier
    
    Returns:
        List of snapshot dictionaries with timestamp and game data
    """
    snapshots = []
    current_ts = end_time.replace(second=0, microsecond=0)
    
    logger.info(f"Starting backward crawl for Event ID: {event_id}")
    logger.info(f"  Window: {start_time.isoformat()} → {end_time.isoformat()}")
    
    iteration = 0
    max_iterations = 1000  # Safety limit
    
    while iteration < max_iterations:
        iteration += 1
        
        try:
            timestamp_str = current_ts.strftime('%Y-%m-%dT%H:%M:%SZ')
            logger.info(f"  [{iteration}] Fetching snapshot at {timestamp_str}")
            
            response = fetch_historical_events_data(
                sport_key=sport_key,
                date=timestamp_str
            )
            
            previous_ts_str = response.get('previous_timestamp')
            if not previous_ts_str:
                logger.info(f"  No previous timestamp found. Reached end of available data.")
                break
            
            previous_ts = isoparse(previous_ts_str)
            
            # Check if we've gone past the start time
            if previous_ts < start_time:
                logger.info(f"  Reached start time boundary. Stopping crawl.")
                break
            
            # Look for our event in this snapshot
            events = response.get('data', [])
            game_event = next(
                (e for e in events if e.get('id') == event_id or e.get('event_id') == event_id),
                None
            )
            
            snapshot_info = {
                'snapshot_timestamp': response.get('timestamp'),
                'previous_timestamp': previous_ts_str,
                'next_timestamp': response.get('next_timestamp'),
                'total_events_in_snapshot': len(events),
                'event_found': game_event is not None,
                'event_data': game_event
            }
            
            if game_event:
                logger.info(f"    ✓ Event found in snapshot")
                # Count bookmakers and markets
                bookmakers = game_event.get('bookmakers', [])
                snapshot_info['bookmaker_count'] = len(bookmakers)
                snapshot_info['total_markets'] = sum(
                    len(bm.get('markets', [])) for bm in bookmakers
                )
            else:
                logger.info(f"    ✗ Event NOT found in snapshot")
                snapshot_info['bookmaker_count'] = 0
                snapshot_info['total_markets'] = 0
            
            snapshots.append(snapshot_info)
            
            # Move to previous timestamp
            current_ts = previous_ts
            
        except Exception as e:
            logger.error(f"  Error during crawl at {current_ts.isoformat()}: {e}")
            break
    
    logger.info(f"Crawl complete. Found {len(snapshots)} snapshots.")
    return snapshots


def export_to_csv(snapshots: List[Dict[str, Any]], output_file: str):
    """Export snapshot analysis to CSV."""
    
    if not snapshots:
        logger.warning("No snapshots to export")
        return
    
    fieldnames = [
        'snapshot_timestamp',
        'previous_timestamp',
        'next_timestamp',
        'total_events_in_snapshot',
        'event_found',
        'bookmaker_count',
        'total_markets'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for snap in snapshots:
            row = {k: snap.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    logger.info(f"✓ Exported {len(snapshots)} snapshots to {output_file}")


def export_detailed_csv(snapshots: List[Dict[str, Any]], output_file: str):
    """Export detailed snapshot data including bookmaker/market breakdown."""
    
    if not snapshots:
        logger.warning("No snapshots to export")
        return
    
    rows = []
    
    for snap in snapshots:
        event_data = snap.get('event_data')
        if not event_data:
            # No event data, create basic row
            rows.append({
                'snapshot_timestamp': snap.get('snapshot_timestamp', ''),
                'event_found': False,
                'bookmaker': '',
                'market_key': '',
                'last_update': ''
            })
            continue
        
        bookmakers = event_data.get('bookmakers', [])
        
        if not bookmakers:
            # Event found but no bookmakers
            rows.append({
                'snapshot_timestamp': snap.get('snapshot_timestamp', ''),
                'event_found': True,
                'bookmaker': '',
                'market_key': '',
                'last_update': ''
            })
            continue
        
        # Create row for each bookmaker/market combination
        for bm in bookmakers:
            bm_key = bm.get('key', 'unknown')
            markets = bm.get('markets', [])
            
            if not markets:
                rows.append({
                    'snapshot_timestamp': snap.get('snapshot_timestamp', ''),
                    'event_found': True,
                    'bookmaker': bm_key,
                    'market_key': '',
                    'last_update': bm.get('last_update', '')
                })
            else:
                for market in markets:
                    rows.append({
                        'snapshot_timestamp': snap.get('snapshot_timestamp', ''),
                        'event_found': True,
                        'bookmaker': bm_key,
                        'market_key': market.get('key', ''),
                        'last_update': market.get('last_update', '')
                    })
    
    fieldnames = ['snapshot_timestamp', 'event_found', 'bookmaker', 'market_key', 'last_update']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"✓ Exported {len(rows)} detail rows to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze available snapshots for a single NFL game'
    )
    parser.add_argument(
        '--event-id',
        required=True,
        help='Game event ID (e.g., af6fbb0a2e996613bc393115276c60e2)'
    )
    parser.add_argument(
        '--commence-time',
        required=True,
        help='Game kickoff time in ISO format (e.g., 2025-09-28T20:25:00Z)'
    )
    parser.add_argument(
        '--duration-hours',
        type=float,
        default=4.0,
        help='Game duration/window to scan in hours (default: 4.0)'
    )
    parser.add_argument(
        '--output-dir',
        default='reports',
        help='Output directory for CSV files (default: reports)'
    )
    parser.add_argument(
        '--sport-key',
        default='americanfootball_nfl',
        help='Sport key (default: americanfootball_nfl)'
    )
    
    args = parser.parse_args()
    
    # Parse commence time
    try:
        kickoff = isoparse(args.commence_time)
    except Exception as e:
        logger.error(f"Invalid commence-time format: {e}")
        sys.exit(1)
    
    # Calculate game window
    game_end = kickoff + timedelta(hours=args.duration_hours)
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"GAME SNAPSHOT ANALYSIS")
    logger.info(f"{'=' * 80}")
    logger.info(f"Event ID: {args.event_id}")
    logger.info(f"Kickoff: {kickoff.isoformat()}")
    logger.info(f"Analysis Window: {args.duration_hours} hours")
    logger.info(f"End Time: {game_end.isoformat()}")
    logger.info(f"{'=' * 80}\n")
    
    # Crawl for snapshots
    snapshots = backward_crawl_all_snapshots(
        event_id=args.event_id,
        start_time=kickoff,
        end_time=game_end,
        sport_key=args.sport_key
    )
    
    if not snapshots:
        logger.warning("No snapshots found for this game")
        sys.exit(0)
    
    # Create output directory if needed
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate output filenames
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = os.path.join(
        args.output_dir,
        f'snapshot_analysis_{args.event_id}_{timestamp_str}_summary.csv'
    )
    detail_file = os.path.join(
        args.output_dir,
        f'snapshot_analysis_{args.event_id}_{timestamp_str}_detail.csv'
    )
    
    # Export both summary and detailed views
    export_to_csv(snapshots, summary_file)
    export_detailed_csv(snapshots, detail_file)
    
    # Print summary stats
    total_snapshots = len(snapshots)
    snapshots_with_event = sum(1 for s in snapshots if s.get('event_found'))
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"ANALYSIS SUMMARY")
    logger.info(f"{'=' * 80}")
    logger.info(f"Total Snapshots Found: {total_snapshots}")
    logger.info(f"Snapshots with Event: {snapshots_with_event}")
    logger.info(f"Snapshots without Event: {total_snapshots - snapshots_with_event}")
    logger.info(f"\nOutput Files:")
    logger.info(f"  Summary: {summary_file}")
    logger.info(f"  Detail:  {detail_file}")
    logger.info(f"{'=' * 80}\n")


if __name__ == '__main__':
    main()
