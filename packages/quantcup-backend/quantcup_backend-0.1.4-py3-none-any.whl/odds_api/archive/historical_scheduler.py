import time
import pandas as pd
from typing import Dict, List, Any, Optional, Callable, Tuple, cast
from dateutil.parser import isoparse
from datetime import datetime, timezone, timedelta

from commonv2.core.logging import setup_logger
from odds_api.archive.nfl_helpers import calculate_nfl_week, classify_game_window
from odds_api.etl.extract.api import fetch_historical_events_data
from odds_api.config import get_settings
from odds_api.core.types import SportKey, EventID, OddsData, ISOTimestamp

# Setup logger
logger = setup_logger('odds_api.historical_scheduler', project_name='ODDS_API')

# Import Bucket utilities from ETL layer
from odds_api.etl.load.bucket import (
    read_odds_data,
    list_odds_files,
    normalize_timestamp,
    extract_date_part
)


def validate_and_log_config(cfg: Any) -> None:
    """Validate backfill configuration and log startup settings."""
    settings = get_settings()
    if not settings.paid_odds_api_key:
        raise ValueError("PAID_ODDS_API_KEY required for historical endpoints")
    
    if cfg.season_range[0] > cfg.season_range[1]:
        raise ValueError(f"Invalid cfg.season_range: {cfg.season_range[0]} > {cfg.season_range[1]}")
    
    if cfg.week_range[0] > cfg.week_range[1]:
        raise ValueError(f"Invalid cfg.week_range: {cfg.week_range[0]} > {cfg.week_range[1]}")
    
    if cfg.week_range[0] < 1 or cfg.week_range[1] > 22:
        raise ValueError(f"cfg.week_range must be between 1 and 22 (got {cfg.week_range})")
    
    # Log configuration
    logger.info("=" * 80)
    logger.info("EVENT-DRIVEN HISTORICAL ODDS BACKFILL")
    logger.info("=" * 80)
    logger.info(f"Sport: {cfg.sport_key}")
    logger.info(f"Markets: {', '.join(cfg.markets)}")
    logger.info(f"Seasons: {cfg.season_range[0]} to {cfg.season_range[1]}")
    logger.info(f"Weeks: {cfg.week_range[0]} to {cfg.week_range[1]}")
    logger.info(f"Week-Open Snapshot (T-6d): {'Enabled' if cfg.include_week_open_snapshot else 'Disabled'}")
    logger.info(f"Window-Start Snapshot (gameday): {'Enabled' if cfg.include_window_start_snapshot else 'Disabled'}")
    logger.info(f"In-Game Odds: {'Enabled' if cfg.include_in_game_odds else 'Disabled'}")
    logger.info(f"Closing Window: {cfg.closing_window_minutes} minutes before kickoff")
    logger.info(f"Rate Limiting: {cfg.delay_between_events}s between events, {cfg.delay_between_snapshots}s between snapshots")
    logger.info(f"Output: {'CSV' if cfg.save_to_csv else ''}{' + ' if cfg.save_to_csv and cfg.save_to_bucket else ''}{'Bucket' if cfg.save_to_bucket else ''}")
    logger.info(f"Quota Tracking: {'Enabled' if cfg.enable_quota_tracking else 'Disabled'}")
    logger.info("=" * 80)

def snapshot_exists(cfg: Any, event_id: EventID, snapshot_requested_ts: datetime, snapshot_role: str, save_to_bucket: bool, commence_time: ISOTimestamp) -> bool:
    """
    Check if snapshot already exists in bucket.
    
    FIXED: Now uses game's commence_time for partition lookup.
    
    Args:
        cfg: Backfill configuration
        event_id: Game event ID
        snapshot_requested_ts: Timestamp we requested (deterministic per role)
        snapshot_role: Semantic role (OPEN_T6D, WINDOW_START, CLOSE_T15M, IN_GAME)
        save_to_bucket: Whether bucket storage is enabled
        commence_time: Game kickoff time (ISO8601 string) - used for partition path
    
    Returns:
        True if snapshot exists, False if it doesn't exist or check fails
    """
    if not cfg.skip_existing_snapshots or cfg.force_refetch:
        return False
    
    if not save_to_bucket:
        return False
    
    try:
        # FIXED: Use commence_time for partition path (matches write logic)
        # Data is partitioned by game kickoff, not snapshot timestamp
        normalized_commence = normalize_timestamp(commence_time)
        date_part = extract_date_part(commence_time)
        
        # Build path to game's partition
        # Path structure: schema/table/date=YYYYMMDD/timestamp=<commence_time>/
        prefix = f"fact_odds_raw/date={date_part}/timestamp={normalized_commence}/"
        
        # Check if ANY files exist for this game
        files = list_odds_files(prefix=prefix)
        exists = len(files) > 0
        
        if exists:
            logger.debug(f"✓ Snapshot partition exists for game {event_id} at {normalized_commence}")
        
        return exists
        
    except Exception as e:
        # CRITICAL: On error, assume data exists to prevent quota waste
        # Better to skip a snapshot than waste quota re-fetching existing data
        logger.warning(f"⚠️  Failed to check snapshot existence: {e}")
        logger.warning(f"   Assuming snapshot exists to preserve quota")
        return True  # Conservative: skip rather than risk wasting quota

def collect_game_snapshots(cfg: Any, game: OddsData, save_to_bucket: bool = False) -> List[Dict[str, Any]]:
    """
    Collect required snapshot timestamps with semantic roles.
    
    Args:
        cfg: Backfill configuration
        game: Game dict with 'id' and 'commence_time' fields (ISO8601 string)
        save_to_bucket: Whether bucket storage is enabled
    
    Returns:
        List of dicts with 'timestamp', 'role', 'description', and 'window_label' keys
        
    Snapshot Roles:
        1. OPEN_T6D: Week-open snapshot (T-6 days before kickoff)
           - NOT the true sportsbook opener (which could be weeks earlier)
           - Consistent timing for cross-game comparison
           
        2. WINDOW_START: Gameday pregame window anchor
           - TNF/SNF/MNF: T-60 minutes before kickoff
           - Sun games (early/late): T-30 minutes before kickoff
           - Enables "gameday drift" analysis (window_start → close)
           
        3. CLOSE_T15M: Closing line snapshot (T-15 minutes before kickoff)
           - Designated close snapshot for CLV calculation
           
        4. IN_GAME: In-game snapshots (TODO) - if INCLUDE_IN_GAME_ODDS
    """
    commence_time_str = game.get('commence_time')
    if not commence_time_str:
        logger.warning(f"Game {game.get('event_id')} missing commence_time")
        return []
    
    kickoff = isoparse(commence_time_str)
    snapshots = []
    
    # Classify game window (for window-specific anchors)
    window_info = classify_game_window(kickoff)
    window_label = window_info['window_label']
    
    # 1. Week-open line (T-6d) - optional
    if cfg.include_week_open_snapshot:
        week_open_ts = kickoff - timedelta(days=6)
        snapshots.append({
            'timestamp': week_open_ts,
            'role': 'OPEN_T6D',
            'description': 'Week-open snapshot (T-6 days, not true sportsbook opener)',
            'window_label': window_label
        })
        logger.debug(f"  Week-open (T-6d): {week_open_ts.isoformat()}")
    
    # 2. WINDOW_START (gameday pregame anchor) - NEW!
    if cfg.include_window_start_snapshot:
        # Game-specific window anchor timing
        if window_label in ['TNF', 'SNF', 'MNF', 'THANKSGIVING']:
            window_start_minutes = 60  # Prime time: T-60min
        else:  # SUN_EARLY, SUN_LATE, SAT, OTHER
            window_start_minutes = 30  # Sunday: T-30min
        
        window_start_ts = kickoff - timedelta(minutes=window_start_minutes)
        snapshots.append({
            'timestamp': window_start_ts,
            'role': 'WINDOW_START',
            'description': f'{window_label} window open (T-{window_start_minutes}min)',
            'window_label': window_label
        })
        logger.debug(f"  Window-start ({window_label}): {window_start_ts.isoformat()}")
    
    # 3. Closing line (T-15min)
    closing_ts = kickoff - timedelta(minutes=cfg.closing_window_minutes)
    snapshots.append({
        'timestamp': closing_ts,
        'role': 'CLOSE_T15M',
        'description': f'Closing line (T-{cfg.closing_window_minutes}min)',
        'window_label': window_label
    })
    logger.debug(f"  Closing (T-{cfg.closing_window_minutes}min): {closing_ts.isoformat()}")
    
    # 4. In-game snapshots (backward crawl from game end)
    if cfg.include_in_game_odds:
        # Determine if we should collect in-game for this window
        should_collect_in_game = (
            cfg.in_game_collection_strategy == 'ALL' or
            (cfg.in_game_collection_strategy == 'PRIMETIME' and
             window_label in cfg.in_game_windows_filter)
        )
        
        # OPTIMIZATION: Early-exit if any snapshots exist for this game
        # Check game partition before expensive backward crawl
        if should_collect_in_game and snapshot_exists(
            cfg=cfg,
            event_id=game['id'],
            snapshot_requested_ts=kickoff,  # Use kickoff as representative timestamp
            snapshot_role='IN_GAME',
            save_to_bucket=save_to_bucket,
            commence_time=game.get('commence_time', '')
        ):
            logger.debug(f"  In-game snapshots already exist for this game, skipping crawl")
            should_collect_in_game = False
        
        if should_collect_in_game:
            game_end = kickoff + timedelta(hours=cfg.game_duration_hours)
            in_game_snapshots = backward_crawl_game_window(
                cfg=cfg,
                game_id=game['id'],
                start_time=kickoff,
                end_time=game_end,
                max_snapshots=None,  # Use adaptive count based on window_label
                window_label=window_label,
                save_to_bucket=save_to_bucket     # Pass flag for existence checks
            )
            # OPTIMIZED: backward_crawl now returns dicts with cached event data
            for ig_snap_dict in in_game_snapshots:
                snapshots.append({
                    'timestamp': ig_snap_dict['timestamp'],
                    'role': 'IN_GAME',
                    'description': 'In-game snapshot',
                    'window_label': window_label,
                    # Cache navigation and event data to avoid re-fetching
                    'snapshot_timestamp': ig_snap_dict['snapshot_timestamp'],
                    'previous_timestamp': ig_snap_dict['previous_timestamp'],
                    'next_timestamp': ig_snap_dict['next_timestamp'],
                    'game_event': ig_snap_dict['game_event']
                })
                logger.debug(f"  In-game: {ig_snap_dict['timestamp'].isoformat()}")
        else:
            logger.debug(f"  Skipping in-game collection for {window_label} (strategy={cfg.in_game_collection_strategy})")
    
    return snapshots

def calculate_in_game_snapshot_count(window_label: str) -> int:
    """
    Calculate optimal in-game snapshot count based on game type.
    
    Primetime games (TNF/SNF/MNF): More line movement, more snapshots
    Sunday games: Less volatile, fewer snapshots needed
    
    Args:
        window_label: Game window classification
    
    Returns:
        Optimal snapshot count for this window type
    """
    snapshot_strategy = {
        'TNF': 15,        # High volume, sharp money
        'SNF': 15,
        'MNF': 15,
        'THANKSGIVING': 12,
        'SUN_EARLY': 8,   # Lower volume
        'SUN_LATE': 8,
        'SAT': 10,
        'OTHER': 10
    }
    return snapshot_strategy.get(window_label, 10)

def backward_crawl_game_window(
    cfg: Any,
    game_id: EventID,
    start_time: datetime,
    end_time: datetime,
    max_snapshots: Optional[int] = None,
    window_label: Optional[str] = None,
    save_to_bucket: bool = False
) -> List[Dict[str, Any]]:
    """
    Backward crawl from game end to collect in-game odds snapshots.
    
    Strategy: Use API's previous_timestamp navigation to walk backward
    from estimated game end to kickoff, collecting snapshots along the way.
    
    OPTIMIZED TWICE:
    1. Returns full event data to avoid double API calls in main loop
    2. Checks bucket for existing snapshots BEFORE fetching to avoid redundant crawling
    
    FIXED: Rounds timestamps to 5-minute intervals (API snapshot boundaries)
    
    Args:
        cfg: Backfill configuration
        game_id: Event ID to track
        start_time: Kickoff time (don't crawl before this)
        end_time: Estimated game end (start crawling here)
        max_snapshots: Safety limit to prevent runaway crawls (default: adaptive based on window)
        window_label: Game window for adaptive snapshot count
        save_to_bucket: Whether bucket storage is enabled
    
    Returns:
        List of snapshot dicts with timestamp, navigation data, and event object.
        Each dict contains:
            - timestamp: Requested timestamp (datetime)
            - snapshot_timestamp: Actual API snapshot timestamp
            - previous_timestamp: Previous snapshot link
            - next_timestamp: Next snapshot link
            - game_event: Full event object from API
    """
    # If max_snapshots not provided, calculate based on window
    if max_snapshots is None and window_label:
        max_snapshots = calculate_in_game_snapshot_count(window_label)
    elif max_snapshots is None:
        max_snapshots = cfg.max_in_game_snapshots
    
    snapshots = []
    
    # Round end_time to nearest 5-minute boundary (API snapshot interval)
    # Historical snapshots are available at 5-minute intervals (per API docs)
    minutes = end_time.minute
    rounded_minutes = (minutes // 5) * 5  # Floor to 5-min boundary
    current_ts = end_time.replace(minute=rounded_minutes, second=0, microsecond=0)
    
    # If we rounded down past the game start, use next 5-min boundary after start
    if current_ts < start_time:
        current_ts = start_time.replace(second=0, microsecond=0)
        minutes_to_add = 5 - (current_ts.minute % 5) if current_ts.minute % 5 != 0 else 0
        if minutes_to_add > 0:
            current_ts = current_ts + timedelta(minutes=minutes_to_add)
    
    logger.debug(f"    Crawling in-game window: {start_time.isoformat()} → {end_time.isoformat()}")
    logger.debug(f"    Starting from rounded timestamp: {current_ts.isoformat()} (5-min interval)")
    logger.debug(f"    Max snapshots: {max_snapshots}")
    
    # Ensure max_snapshots is an int for range()
    loop_limit = int(max_snapshots) if max_snapshots is not None else 0
    
    for i in range(loop_limit):
        try:
            # Fetch historical events to get previous_timestamp navigation
            # API requires strict ISO8601 format with Z suffix
            timestamp_str = current_ts.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            response = fetch_historical_events_data(
                sport_key=cfg.sport_key,
                date=timestamp_str
            )
            
            previous_ts_str = response.get('previous_timestamp')
            if not previous_ts_str:
                logger.debug(f"      No previous_timestamp at {current_ts.isoformat()}, stopping crawl")
                break
            
            previous_ts = isoparse(previous_ts_str)
            
            # Stop if we've crawled past kickoff
            if previous_ts <= start_time:
                logger.debug(f"      Reached kickoff at {previous_ts.isoformat()}, stopping crawl")
                break
            
            # Check if game still exists in this snapshot
            events = response.get('data', [])
            game_event = next((e for e in events if e.get('event_id') == game_id), None)
            
            if game_event:
                # OPTIMIZATION: Check if this snapshot already exists in bucket before fetching odds
                # Extract commence_time from game_event
                game_commence_time = game_event.get('commence_time', '')
                if game_commence_time and snapshot_exists(cfg, game_id, previous_ts, 'IN_GAME', save_to_bucket, game_commence_time):
                    logger.debug(f"      Snapshot already exists, skipping: {previous_ts.isoformat()}")
                    current_ts = previous_ts
                    continue
                
                # Cache the full response data to avoid re-fetching in main loop
                snapshots.append({
                    'timestamp': previous_ts,
                    'snapshot_timestamp': response.get('timestamp'),
                    'previous_timestamp': response.get('previous_timestamp'),
                    'next_timestamp': response.get('next_timestamp'),
                    'game_event': game_event
                })
                logger.debug(f"      [{len(snapshots)}/{max_snapshots}] In-game snapshot: {previous_ts.isoformat()}")
            else:
                logger.debug(f"      Game {game_id} not found in snapshot at {previous_ts.isoformat()}")
            
            current_ts = previous_ts
            
            # Rate limit to avoid hammering API
            time.sleep(cfg.delay_between_snapshots)
            
        except Exception as e:
            logger.warning(f"      Error during backward crawl at {current_ts.isoformat()}: {e}")
            break
    
    logger.info(f"    Collected {len(snapshots)} in-game snapshots")
    return snapshots

def fetch_season_schedule_cached(cfg: Any, season: int, save_to_bucket: bool = False, week_range: Optional[Tuple[int, int]] = None) -> List[Dict[str, Any]]:
    """
    Fetch season schedule with bucket caching.
    
    Three-tier fallback strategy:
    1. PRIMARY: Load from bucket cache (0 credits)
    2. SECONDARY: Batch query midseason snapshot (1 credit)
    3. FALLBACK: Week-by-week discovery (22 credits)
    
    Args:
        cfg: Backfill configuration
        season: NFL season year (e.g., 2025)
        save_to_bucket: Whether to use bucket cache
        week_range: (start_week, end_week) to filter results
    
    Returns:
        List of game dicts with 'id', 'home_team', 'away_team', 'commence_time'
    """
    logger.info(f"\n{'─' * 80}")
    logger.info(f"📅 Fetching schedule for {season} NFL season")
    logger.info(f"{'─' * 80}")
    
    # TIER 1: Try bucket cache first
    if save_to_bucket:
        try:
            cached_df = read_odds_data(table_name='dim_oddapi_game')
            
            if cached_df is not None and not cached_df.empty:
                # Filter by season (commence_time starts with season year)
                season_games = cached_df[
                    cached_df['commence_time'].astype(str).str.startswith(str(season))
                ].copy()
                
                if not season_games.empty:
                    # Add week classification for filtering
                    season_games['kickoff_utc'] = pd.to_datetime(season_games['commence_time'])
                    season_games['week_num'] = season_games['kickoff_utc'].apply(
                        lambda kt: calculate_nfl_week(kt, season)
                    )
                    
                    # Filter by week range if provided
                    if week_range:
                        season_games = season_games[
                            (season_games['week_num'] >= week_range[0]) &
                            (season_games['week_num'] <= week_range[1])
                        ]
                    
                    if not season_games.empty:
                        logger.info(f"✓ CACHE HIT: Using {len(season_games):,} cached event IDs from bucket")
                        logger.info(f"{'─' * 80}\n")
                        
                        # Convert back to dict format expected by backfill loop
                        # Normalize column name: event_id → id (match API format)
                        if 'event_id' in season_games.columns:
                            season_games = season_games.rename(columns={'event_id': 'id'})
                        
                        return cast(List[Dict[str, Any]], season_games.to_dict('records'))
        
        except Exception as e:
            logger.debug(f"Cache lookup failed: {e}")
    
    # TIER 2: Cache miss - use optimized batch query
    logger.info("Cache miss - trying batch query...")
    return fetch_season_schedule_optimized(cfg, season)

def fetch_season_schedule_optimized(cfg: Any, season: int) -> List[Dict[str, Any]]:
    """
    Batch schedule fetch using single midseason snapshot.
    
    Savings: 21 credits vs week-by-week (22 → 1 call)
    
    Strategy: Query mid-October when full season schedule is published.
    Raises exception if batch query fails (no fallback to preserve quota).
    """
    logger.info("Using BATCH QUERY (1 API call)")
    
    # Use mid-October date when full schedule is available
    midseason_date = datetime(season, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
    date_str = midseason_date.isoformat().replace('+00:00', 'Z')
    
    response = fetch_historical_events_data(
        sport_key=cfg.sport_key,
        date=date_str,
    )
    
    events = response.get('data', [])
    logger.info(f"  ✓ Found {len(events):,} events in single query")
    logger.info(f"  💰 Saved 21 API credits vs week-by-week scan")
    logger.info(f"{'─' * 80}\n")
    
    # Deduplicate by event_id
    seen_ids = set()
    unique_events = []
    for event in events:
        event_id = event.get('event_id')
        if event_id and event_id not in seen_ids:
            seen_ids.add(event_id)
            unique_events.append(event)
    
    return unique_events

def estimate_backfill_cost(cfg: Any, games: List[Dict[str, Any]], used_cache: bool = False) -> Dict[str, int]:
    """
    Project total quota cost before execution.
    
    Returns cost breakdown for planning and variance analysis.
    
    Args:
        cfg: Backfill configuration
        games: List of games to process
        used_cache: Whether schedule came from cache (vs API)
    
    Returns:
        Dict with cost breakdown: {'schedule', 'base', 'in_game', 'total'}
    """
    games_count = len(games)
    
    # Schedule discovery cost
    schedule_cost = 0 if used_cache else 1  # Cached (0) or batch query (1)
    
    # Base snapshots per game
    base_snapshots = sum([
        cfg.include_week_open_snapshot,     # 1 if enabled
        cfg.include_window_start_snapshot,   # 1 if enabled
        1  # CLOSE_T15M always included
    ])
    
    # Estimate in-game snapshot count
    if cfg.include_in_game_odds and cfg.in_game_collection_strategy == 'PRIMETIME':
        primetime_ratio = 0.2  # ~20% of games are primetime (TNF/SNF/MNF)
        primetime_games = int(games_count * primetime_ratio)
        avg_in_game_snapshots = 12  # Average for primetime
        in_game_snapshots = primetime_games * avg_in_game_snapshots
    elif cfg.include_in_game_odds and cfg.in_game_collection_strategy == 'ALL':
        in_game_snapshots = games_count * 10  # Conservative average
    else:
        in_game_snapshots = 0
    
    # Calculate costs (30 credits per snapshot = 10 × 3 markets × 1 region)
    base_cost = (games_count * base_snapshots) * 30
    in_game_cost = in_game_snapshots * 30
    total = schedule_cost + base_cost + in_game_cost
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"ESTIMATED QUOTA COST")
    logger.info(f"{'=' * 80}")
    logger.info(f"Games to process: {games_count:,}")
    logger.info(f"Schedule discovery: {schedule_cost} credits {'(bucket cache)' if used_cache else '(batch query)'}")
    logger.info(f"Base snapshots: {base_cost:,} credits ({games_count} games × {base_snapshots} snapshots @ 30 credits)")
    logger.info(f"In-game snapshots: {in_game_cost:,} credits (~{in_game_snapshots} snapshots @ 30 credits)")
    logger.info(f"{'─' * 40}")
    logger.info(f"TOTAL ESTIMATED: {total:,} credits")
    logger.info(f"{'=' * 80}\n")
    
    return {
        'schedule': schedule_cost,
        'base': base_cost,
        'in_game': in_game_cost,
        'total': total
    }
