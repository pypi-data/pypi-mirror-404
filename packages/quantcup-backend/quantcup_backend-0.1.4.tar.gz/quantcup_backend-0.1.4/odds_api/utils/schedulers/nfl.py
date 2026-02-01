import time
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Tuple, Optional, cast
from datetime import datetime, timezone, timedelta
from dateutil.parser import isoparse
import pandas as pd

from commonv2.core.logging import setup_logger
from odds_api.utils.schedulers.base import BaseScheduler
from odds_api.etl.extract.api import fetch_historical_events_data
from odds_api.etl.load.bucket import (
    read_odds_data,
    list_odds_files,
    normalize_timestamp,
    extract_date_part
)

logger = setup_logger('odds_api.schedulers.nfl', project_name='ODDS_API')

class NFLScheduler(BaseScheduler):
    """
    NFL-specific implementation of BaseScheduler.
    
    Handles NFL week calculations, primetime window classification,
    and optimized schedule fetching.
    """
    
    def __init__(self, cfg: Any, save_to_bucket: bool = False):
        self.cfg = cfg
        self.save_to_bucket = save_to_bucket

    def get_schedule(self, season: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch NFL schedule with bucket caching and week filtering.
        
        Fetches all games for the season, then groups them into weeks based on
        natural Thursday-to-Monday boundaries rather than calculating from dates.
        """
        week_range = kwargs.get('week_range', self.cfg.week_range)
        
        logger.info(f"📅 Fetching NFL schedule for {season} season (Weeks {week_range[0]}-{week_range[1]})")
        
        # TIER 1: Try bucket cache first
        if self.save_to_bucket:
            try:
                cached_df = read_odds_data(table_name='dim_oddapi_game')
                if cached_df is not None and not cached_df.empty:
                    # Filter for this season's games
                    season_games = cached_df[
                        pd.to_datetime(cached_df['commence_time']).dt.year == season
                    ].copy()
                    
                    if not season_games.empty:
                        season_games['kickoff_utc'] = pd.to_datetime(season_games['commence_time'])
                        
                        # Assign weeks by grouping games into Thursday-Monday windows
                        season_games = self._assign_weeks_by_boundaries(season_games)
                        
                        season_games['window_label'] = season_games['kickoff_utc'].apply(
                            lambda kt: self._classify_window(kt)['window_label']
                        )
                        
                        if week_range:
                            season_games = season_games[
                                (season_games['week_num'] >= week_range[0]) &
                                (season_games['week_num'] <= week_range[1])
                            ]
                        
                        # Filter to specific event if requested (for testing)
                        if hasattr(self.cfg, 'event_id_filter') and self.cfg.event_id_filter:
                            event_id = self.cfg.event_id_filter
                            season_games = season_games[season_games['id'] == event_id]
                            if season_games.empty:
                                logger.warning(f"⚠️  Event ID '{event_id}' not found in cache")
                            else:
                                logger.info(f"✓ CACHE HIT: Filtered to single event: {event_id}")
                                return cast(List[Dict[str, Any]], season_games.to_dict('records'))
                        
                        if not season_games.empty:
                            found_weeks = sorted([int(w) for w in season_games['week_num'].unique()])
                            logger.info(f"✓ CACHE HIT: Found {len(season_games):,} games in bucket for weeks: {found_weeks}")
                            
                            # Check if we have all requested weeks
                            requested_weeks = set(range(week_range[0], week_range[1] + 1))
                            missing_weeks = requested_weeks - set(found_weeks)
                            
                            if not missing_weeks:
                                return cast(List[Dict[str, Any]], season_games.to_dict('records'))
                            else:
                                logger.info(f"  Cache incomplete. Missing weeks: {sorted(list(missing_weeks))}. Fetching from API.")
            except Exception as e:
                logger.debug(f"Cache lookup failed: {e}")
        
        # TIER 2: Fetch all season games from Odds API
        logger.info("Cache miss - fetching full season from Odds API")
        
        # Fetch entire season using date range (Sept 1 - Feb 28 covers regular season + playoffs)
        commence_from = f"{season}-09-01T00:00:00Z"
        commence_to = f"{season + 1}-02-28T23:59:59Z"
        
        logger.info(f"  Fetching games from {commence_from} to {commence_to}")
        
        try:
            response = fetch_historical_events_data(
                sport_key=self.cfg.sport_key,
                date=commence_from,
            )
            
            all_events = response.get('data', [])
            logger.info(f"  Retrieved {len(all_events):,} events from API")
            
            if not all_events:
                logger.warning("No events found for season")
                return []
            
            # Convert to DataFrame for easier week grouping
            df = pd.DataFrame(all_events)
            df['kickoff_utc'] = pd.to_datetime(df['commence_time'])
            df = df.sort_values('kickoff_utc').reset_index(drop=True)
            
            # Assign weeks based on Thursday-Monday boundaries
            df = self._assign_weeks_by_boundaries(df)
            
            # Add window labels
            df['window_label'] = df['kickoff_utc'].apply(
                lambda kt: self._classify_window(kt)['window_label']
            )
            
            # Filter to requested weeks
            if week_range:
                df = df[
                    (df['week_num'] >= week_range[0]) &
                    (df['week_num'] <= week_range[1])
                ]
            
            # Filter to specific event if requested (for testing)
            if hasattr(self.cfg, 'event_id_filter') and self.cfg.event_id_filter:
                event_id = self.cfg.event_id_filter
                df = df[df['id'] == event_id]
                if df.empty:
                    logger.warning(f"⚠️  Event ID '{event_id}' not found in schedule")
                    logger.warning(f"   Check that the event exists in the specified season/week range")
                    return []
                else:
                    logger.info(f"✓ Filtered to single event: {event_id}")
            
            logger.info(f"✓ Found {len(df):,} games for weeks {week_range[0]}-{week_range[1]}")
            
            return cast(List[Dict[str, Any]], df.to_dict('records'))
            
        except Exception as e:
            logger.error(f"Failed to fetch season schedule: {e}")
            return []

    def snapshot_exists(self, event_id: str, commence_time: str, snapshot_ts: datetime, role: str) -> bool:
        """
        Check if snapshot already exists in bucket for THIS SPECIFIC EVENT.
        
        CRITICAL FIX: Include event_id in path to prevent MNF doubleheader collisions
        where two games with similar kickoff times would incorrectly share the same partition.
        """
        if not self.cfg.skip_existing_snapshots or self.cfg.force_refetch:
            return False
        
        if not self.save_to_bucket:
            return False
        
        try:
            normalized_commence = normalize_timestamp(commence_time)
            date_part = extract_date_part(commence_time)
            
            # Build EVENT-SPECIFIC path to prevent doubleheader collision
            # Each event gets its own subdirectory within the timestamp partition
            prefix = f"fact_odds_raw/date={date_part}/timestamp={normalized_commence}/event_id={event_id}/"
            
            # Check if ANY files exist for this specific event
            files = list_odds_files(prefix=prefix)
            exists = len(files) > 0
            
            if exists:
                logger.debug(f"✓ Snapshot partition exists for Event ID: {event_id} at {normalized_commence} ({len(files)} files)")
            
            return exists
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to check snapshot existence for Event ID {event_id}: {e}")
            return True  # Conservative: skip rather than risk wasting quota

    def get_snapshots(self, game: Dict[str, Any], save_to_bucket: bool = False) -> List[Dict[str, Any]]:
        """
        Collect required NFL snapshot timestamps (Open, Close, In-Game).
        """
        commence_time_str = game.get('commence_time')
        if not commence_time_str:
            return []
        
        kickoff = isoparse(commence_time_str)
        snapshots = []
        
        window_info = self._classify_window(kickoff)
        window_label = window_info['window_label']
        
        # 1. Week-open line (T-6d)
        if self.cfg.include_week_open_snapshot:
            snapshots.append({
                'timestamp': kickoff - timedelta(days=6),
                'role': 'OPEN_T6D',
                'description': 'Week-open snapshot (T-6 days)',
                'window_label': window_label
            })
        
        # 2. Pre-game scheduled snapshot (target timing, not guaranteed exact due to API granularity)
        snapshots.append({
            'timestamp': kickoff - timedelta(minutes=self.cfg.pregame_scheduled_minutes),
            'role': 'PREGAME_SCHEDULED',
            'description': f'Pre-game scheduled snapshot (T-{self.cfg.pregame_scheduled_minutes}min target)',
            'window_label': window_label
        })
        
        # 4. In-game snapshots (Backward Crawl)
        if self.cfg.include_in_game_odds:
                game_id = game['id']
                event_id = game.get('event_id', game_id)
                # Check if snapshots already exist before crawling
                if self.snapshot_exists(game_id, commence_time_str, kickoff, 'IN_GAME'):
                    logger.warning(f"⚠️  SKIPPING CRAWL: In-game snapshots already exist for Event ID: {event_id}, Game ID: {game_id}")
                    logger.warning(f"   Commence time: {commence_time_str}")
                    logger.warning(f"   Window: {window_label}")
                    logger.warning(f"   If this is unexpected, check for doubleheader collision or set skip_existing_snapshots=False")
                else:
                    logger.info(f"  ✓ Collecting in-game snapshots for Event ID: {event_id}, Game ID: {game_id}")
                    game_end = kickoff + timedelta(hours=self.cfg.game_duration_hours)
                    in_game_snapshots = self.backward_crawl_game_window(
                        event_id=game_id,
                        start_time=kickoff,
                        end_time=game_end,
                        window_label=window_label
                    )
                    for ig_snap_dict in in_game_snapshots:
                        snapshots.append({
                            'timestamp': ig_snap_dict['timestamp'],
                            'role': 'IN_GAME',
                            'description': 'In-game snapshot',
                            'window_label': window_label,
                            'snapshot_timestamp': ig_snap_dict['snapshot_timestamp'],
                            'previous_timestamp': ig_snap_dict['previous_timestamp'],
                            'next_timestamp': ig_snap_dict['next_timestamp'],
                            'game_event': ig_snap_dict['game_event']
                        })
        
        return snapshots

    def _assign_weeks_by_boundaries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign week numbers to NFL games based on natural Thursday-to-Monday boundaries.
        
        This approach groups games by detecting when a new week starts (Thursday games)
        rather than calculating from a hardcoded season start date.
        
        Args:
            df: DataFrame with 'kickoff_utc' column (datetime)
        
        Returns:
            DataFrame with added 'week_num' column
        
        Logic:
            - NFL weeks run Thursday-Monday (weekday 3-0)
            - Identify week boundaries by finding Thursday games
            - Sequentially number weeks 1, 2, 3, etc.
            - Handle edge cases (Wed games, playoff gaps)
        """
        if df.empty:
            df['week_num'] = []
            return df
        
        df = df.sort_values('kickoff_utc').reset_index(drop=True)
        
        # Convert to Eastern Time for accurate weekday detection
        et_zone = ZoneInfo('America/New_York')
        df['kickoff_et'] = df['kickoff_utc'].dt.tz_convert(et_zone)
        df['weekday'] = df['kickoff_et'].dt.weekday  # 0=Mon, 3=Thu, 6=Sun
        
        # Identify week boundaries (Thursday games mark new week starts)
        # Also handle edge case of Wednesday games or gaps
        week_num = 1
        weeks = []
        last_weekday = None
        
        for idx, row in df.iterrows():
            current_weekday = row['weekday']
            
            # Detect new week: Thursday after Monday, or significant time gap
            if last_weekday is not None:
                # If we see Thursday after we saw Monday/Tuesday, it's a new week
                if current_weekday == 3 and last_weekday in [0, 1, 2]:
                    week_num += 1
                # If we see Thursday after Sunday, and it's been a week, it's a new week
                elif current_weekday == 3 and last_weekday == 6:
                    if idx > 0:
                        days_gap = (row['kickoff_utc'] - df.loc[idx-1, 'kickoff_utc']).days
                        if days_gap >= 3:  # New week if gap is 3+ days
                            week_num += 1
            
            weeks.append(week_num)
            last_weekday = current_weekday
        
        df['week_num'] = weeks
        df = df.drop(columns=['kickoff_et', 'weekday'], errors='ignore')
        
        return df

    def _classify_window(self, kickoff_utc: datetime) -> Dict[str, Any]:
        """
        Classify game into betting window (TNF, SNF, MNF, etc.).
        
        Args:
            kickoff_utc: Game kickoff time in UTC
        
        Returns:
            Dict with 'window_label' and 'kickoff_et' keys
            
        Window Labels:
            - TNF: Thursday Night Football
            - MNF: Monday Night Football
            - SNF: Sunday Night Football
            - SAT: Saturday games (late season)
            - SUN_EARLY: Sunday 1pm ET slot
            - SUN_LATE: Sunday 4pm ET slot
            - THANKSGIVING: Thanksgiving Day games
            - OTHER: All other games
        """
        et = kickoff_utc.astimezone(ZoneInfo('America/New_York'))
        
        weekday = et.weekday()  # 0=Monday, 6=Sunday
        hour = et.hour
        month = et.month
        day = et.day
        
        # Thanksgiving (4th Thursday in November - around Nov 22-28)
        if weekday == 3 and month == 11 and 22 <= day <= 28:
            return {'window_label': 'THANKSGIVING', 'kickoff_et': et}
        
        # Thursday Night Football
        if weekday == 3:
            return {'window_label': 'TNF', 'kickoff_et': et}
        
        # Monday Night Football
        elif weekday == 0:
            return {'window_label': 'MNF', 'kickoff_et': et}
        
        # Saturday games (late season)
        elif weekday == 5:
            return {'window_label': 'SAT', 'kickoff_et': et}
        
        # Sunday games
        elif weekday == 6:
            if hour < 16:
                return {'window_label': 'SUN_EARLY', 'kickoff_et': et}  # 9:30am London or 1pm ET
            elif 16 <= hour < 20:
                return {'window_label': 'SUN_LATE', 'kickoff_et': et}  # 4pm ET slot
            else:
                return {'window_label': 'SNF', 'kickoff_et': et}  # Sunday Night Football
        
        # Catch-all for other times (Christmas, etc.)
        else:
            return {'window_label': 'OTHER', 'kickoff_et': et}

    def calculate_in_game_snapshot_count(self, window_label: str) -> int:
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
        self,
        event_id: str,
        start_time: datetime,
        end_time: datetime,
        window_label: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Backward crawl from game end to collect in-game odds snapshots.
        """
        max_snapshots = self.calculate_in_game_snapshot_count(window_label) if window_label else self.cfg.max_in_game_snapshots
        snapshots = []
        
        # Round end_time to nearest 5-minute boundary
        minutes = end_time.minute
        rounded_minutes = (minutes // 5) * 5
        current_ts = end_time.replace(minute=rounded_minutes, second=0, microsecond=0)
        
        if current_ts < start_time:
            current_ts = start_time.replace(second=0, microsecond=0)
            minutes_to_add = 5 - (current_ts.minute % 5) if current_ts.minute % 5 != 0 else 0
            if minutes_to_add > 0:
                current_ts = current_ts + timedelta(minutes=minutes_to_add)
        
        for i in range(int(max_snapshots)):
            try:
                timestamp_str = current_ts.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                response = fetch_historical_events_data(sport_key=self.cfg.sport_key, date=timestamp_str)
                
                previous_ts_str = response.get('previous_timestamp')
                if not previous_ts_str:
                    break
                
                previous_ts = isoparse(previous_ts_str)
                if previous_ts <= start_time:
                    break
                
                events = response.get('data', [])
                # Check both 'id' and 'event_id' as different endpoints use different keys
                game_event = next((e for e in events if e.get('id') == event_id or e.get('event_id') == event_id), None)
                
                if game_event:
                    game_event_id = game_event.get('event_id', game_event.get('id', event_id))
                    # OPTIMIZATION: Check if this snapshot already exists in bucket before fetching odds
                    game_commence_time = game_event.get('commence_time', '')
                    if game_commence_time and self.snapshot_exists(event_id, game_commence_time, previous_ts, 'IN_GAME'):
                        logger.info(f"      Snapshot already exists for Event ID: {game_event_id}, skipping: {previous_ts.isoformat()}")
                        current_ts = previous_ts
                        continue

                    logger.info(f"      Found in-game snapshot for Event ID: {game_event_id} at {previous_ts.isoformat()}")
                    snapshots.append({
                        'timestamp': previous_ts,
                        'snapshot_timestamp': response.get('timestamp'),
                        'previous_timestamp': response.get('previous_timestamp'),
                        'next_timestamp': response.get('next_timestamp'),
                        'game_event': game_event
                    })
                else:
                    logger.debug(f"      Event ID {event_id} not found in crawl snapshot at {timestamp_str} (Total events: {len(events)})")
                
                current_ts = previous_ts
                time.sleep(self.cfg.delay_between_snapshots)
                
            except Exception as e:
                logger.warning(f"      Error during backward crawl at {current_ts.isoformat()}: {e}")
                break
        
        return snapshots

    def estimate_cost(self, games: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Project total quota cost for NFL backfill.
        """
        games_count = len(games)
        
        # Schedule discovery cost (1 credit for batch query)
        # We assume batch query is used if not hitting cache
        schedule_cost = 1
        
        # Base snapshots per game
        base_snapshots = sum([
            self.cfg.include_week_open_snapshot,
            1  # PREGAME_SCHEDULED
        ])
        
        # Estimate in-game snapshot count (average ~10 snapshots per game)
        in_game_snapshots = 0
        if self.cfg.include_in_game_odds:
            in_game_snapshots = games_count * 10
        
        # 30 credits per snapshot (10 x 3 markets x 1 region)
        base_cost = (games_count * base_snapshots) * 30
        in_game_cost = in_game_snapshots * 30
        total = schedule_cost + base_cost + in_game_cost
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"ESTIMATED QUOTA COST (NFL)")
        logger.info(f"{'=' * 80}")
        logger.info(f"Games to process: {games_count:,}")
        logger.info(f"Schedule discovery: {schedule_cost} credits")
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
