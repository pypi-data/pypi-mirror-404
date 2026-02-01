#!/usr/bin/env python3
"""
Script to backfill historical odds data by:
1. Fetching historical events for a given date/time
2. Looping through each event to fetch detailed odds
3. Normalizing data into star schema tables
4. Saving to CSV and/or uploading to Sevalla bucket

This demonstrates the efficient pattern of using fetch_historical_events_data
to get event IDs, then calling fetch_historical_event_odds_data for each event.

WAREHOUSE-GRADE Normalized Schema (oddsapi):

DIMENSIONS:
- dim_oddapi_game: Game reference (event_id PK)
- dim_team: Team reference (team_id PK) - from /participants endpoint
- dim_bookmaker: Bookmaker reference (bookmaker_key PK) with region
- dim_market: Market type reference (market_key PK)
- dim_date: Date dimension (date PK) for temporal analysis
- dim_snapshot_navigation: Temporal navigation (snapshot_timestamp PK)

FACTS (LAYERED ARCHITECTURE):
- fact_odds_raw: TRUTH LAYER - Immutable API data with stable selection keys
  * Composite PK: (event_id, snapshot_timestamp, bookmaker_key, market_key, selection_type, participant_id, side, odds_point)
  * Fields: odds_price, odds_point, player_name, bookmaker_last_update, market_last_update
  * Stable selection keys: selection_type ('team'|'total'|'prop'), participant_id (from /participants), side ('home'|'away'|'over'|'under')
  * NEVER contains derived fields - this is your source of truth!

- fact_odds_features: ANALYTICS LAYER - Recomputable derived metrics
  * Same PK as fact_odds_raw
  * Fields: implied_probability (0-1 scale), rank_by_price, is_best_price,
           odds_change_from_previous, odds_change_direction, opening_line, closing_line,
           line_moved_from_open, opening_to_close_movement, clv_vs_close,
           is_first_snapshot, is_last_snapshot, is_true_opening, is_true_closing,
           closing_line_minutes_before_kickoff, is_anomalous
  * Versioned with _features_version for formula tracking
  * Can be regenerated any time from fact_odds_raw without API calls
"""
import sys
import time
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, Tuple, Callable
from dateutil.parser import isoparse
from odds_api.core.types import SportKey, EventID, ISOTimestamp

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from odds_api.etl.extract import api
from odds_api.config import get_settings
from odds_api.core import get_team_registry, QuotaTracker, QuotaExceededException, setup_quota_tracker
from odds_api.etl.transform.historical import normalize_to_star_schema
from odds_api.archive.nfl_helpers import calculate_nfl_week, classify_game_window
from commonv2.utils.decorators import retry_with_backoff
from odds_api.etl.transform.odds import flatten_event_odds
from odds_api.archive.historical_scheduler import (
    collect_game_snapshots,
    fetch_season_schedule_cached,
    snapshot_exists,
    validate_and_log_config, 
    estimate_backfill_cost,
)
from commonv2.core.logging import setup_logger

# Setup logger
logger = setup_logger('odds_api.backfill_historical_odds', project_name='ODDS_API')

# Initialize team registry for stable participant ID lookups
TEAM_REGISTRY = get_team_registry()

# Import Bucket utilities from ETL layer
from odds_api.etl.load.bucket import (
    get_odds_bucket_adapter,
    read_odds_data,
    store_odds_data,
    setup_bucket_adapter,
    normalize_timestamp,
    extract_date_part
)

# ============================================================================
# STANDALONE UTILITIES
# ============================================================================

def _process_single_event(
    event: Dict[str, Any], 
    timestamp_str: ISOTimestamp, 
    snapshot_ts: Any, 
    snapshot_role: str, 
    window_label: str, 
    previous_ts: Any, 
    next_ts: Any, 
    cfg: Any
) -> List[Dict[str, Any]]:
    """
    Process odds for a single event with role metadata.
    
    Args:
        event: Event data dict
        timestamp_str: ISO timestamp string for API call
        snapshot_ts: Actual snapshot timestamp from API
        snapshot_role: Semantic role (OPEN_T6D, WINDOW_START, CLOSE_T15M)
        window_label: Game window (TNF, SNF, MNF, SUN_EARLY, etc.)
        previous_ts: Previous snapshot timestamp (from API navigation)
        next_ts: Next snapshot timestamp (from API navigation)
        cfg: Backfill configuration
    
    Returns:
        List of flattened odds records with role metadata
    """
    event_id = event['id']
    
    @retry_with_backoff(max_retries=3)
    def fetch_event_odds():
        return api.fetch_historical_event_odds_data(
            sport_key=cfg.sport_key,
            event_id=event_id,
            date=timestamp_str,
            markets=cfg.markets
        )
    
    odds_response = fetch_event_odds()
    event_data = odds_response.get('data', {})
    
    flat_records = flatten_event_odds(
        event_data=event_data,
        snapshot_timestamp=snapshot_ts,
        snapshot_requested_ts=isoparse(timestamp_str), # type: ignore
        snapshot_role=snapshot_role,
        window_label=window_label,
        previous_timestamp=previous_ts,
        next_timestamp=next_ts
    )
    
    return flat_records

# ============================================================================
# BACKFILL COMPONENTS
# ============================================================================

class BackfillContext:
    """Holds state for the backfill process."""
    def __init__(self, cfg: Any):
        self.cfg = cfg
        self.dim_accumulators = {
            'dim_oddapi_game': [],
            'dim_team': [],
            'dim_bookmaker': [],
            'dim_market': [],
            'dim_date': [],
            'dim_snapshot_navigation': []
        }
        self.fact_raw_records = []
        self.fact_features_records = []
        
        # Counters
        self.total_games = 0
        self.total_snapshots = 0
        self.total_events_processed = 0
        self.skipped_snapshots = 0
        
        # Quota tracking
        self.quota_tracker = setup_quota_tracker(cfg)
        self.starting_quota: Optional[Dict[str, int]] = None
        if self.quota_tracker:
            status = self.quota_tracker.get_usage_summary()
            self.starting_quota = {'used': status['requests_used'], 'remaining': status['remaining']}
        
        self.estimated_cost: Optional[Dict[str, int]] = None
        self.used_cache = False

    def add_normalized_data(self, normalized: Dict[str, pd.DataFrame]):
        """Accumulate normalized data into state."""
        for table_name, df in normalized.items():
            if table_name.startswith('dim_'):
                if table_name in self.dim_accumulators:
                    self.dim_accumulators[table_name].append(df)
            elif table_name == 'fact_odds_raw':
                self.fact_raw_records.extend(df.to_dict('records'))
            elif table_name == 'fact_odds_features':
                self.fact_features_records.extend(df.to_dict('records'))

class BackfillWriter:
    """Handles data persistence to CSV and Bucket."""
    def __init__(self, cfg: Any, save_to_bucket: bool):
        self.cfg = cfg
        self.save_to_bucket = save_to_bucket

    def write_dimensions(self, dim_accumulators: Dict[str, List[pd.DataFrame]]):
        """Write complete dimension tables with merging and deduplication."""
        if not dim_accumulators:
            return
        
        logger.info(f"\n{'─' * 80}")
        logger.info("💾 Writing accumulated dimension tables (with merge)...")
        logger.info(f"{'─' * 80}")
        
        for table_name, df_list in dim_accumulators.items():
            if not df_list:
                continue
                
            # Merge all snapshots' dimensions from current run
            new_df = pd.concat(df_list, ignore_index=True)
            
            # Load existing dimension data from bucket (if exists)
            existing_df = None
            if self.save_to_bucket:
                try:
                    existing_df = read_odds_data(table_name=table_name, schema=self.cfg.bucket_schema)
                    if existing_df is not None and not existing_df.empty:
                        logger.info(f"  {table_name}: Loaded {len(existing_df):,} existing rows from bucket")
                except Exception:
                    logger.info(f"  {table_name}: No existing data found (new dimension table)")
            
            # Merge existing + new data
            if existing_df is not None and not existing_df.empty:
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                logger.info(f"  {table_name}: Merging {len(existing_df):,} existing + {len(new_df):,} new rows")
            else:
                combined_df = new_df
                logger.info(f"  {table_name}: Creating new dimension with {len(new_df):,} rows")
            
            # Add backfill run tracking metadata
            if '_backfill_run_id' not in combined_df.columns:
                combined_df['_backfill_run_id'] = pd.Timestamp.now(tz=timezone.utc).isoformat()
            if '_season_range_start' not in combined_df.columns:
                combined_df['_season_range_start'] = self.cfg.season_range[0]
            if '_season_range_end' not in combined_df.columns:
                combined_df['_season_range_end'] = self.cfg.season_range[1]
            
            # Deduplicate based on primary key
            pk_map = {
                'dim_oddapi_game': 'event_id',
                'dim_team': 'team_id',
                'dim_bookmaker': 'bookmaker_key',
                'dim_market': 'market_key',
                'dim_date': 'date'
            }
            pk_col = pk_map.get(table_name)
            
            if pk_col and pk_col in combined_df.columns:
                before_count = len(combined_df)
                if '_extracted_at' in combined_df.columns:
                    combined_df = combined_df.sort_values('_extracted_at')
                combined_df = combined_df.drop_duplicates(subset=[pk_col], keep='last')
                after_count = len(combined_df)
                logger.info(f"  {table_name}: {before_count:,} → {after_count:,} rows (deduped by {pk_col})")
            else:
                logger.info(f"  {table_name}: {len(combined_df):,} rows (no dedup)")
            
            # Save to CSV
            if self.cfg.save_to_csv:
                data_dir = Path.cwd() / "data"
                data_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_path = data_dir / f"{table_name}_complete_{timestamp}.csv"
                combined_df.to_csv(csv_path, index=False)
                logger.info(f"    ✓ CSV: {csv_path}")
            
            # Save to bucket
            if self.save_to_bucket:
                try:
                    success = store_odds_data(df=combined_df, table_name=table_name, schema=self.cfg.bucket_schema)
                    if success:
                        logger.info(f"    ✓ Bucket: {len(combined_df):,} rows uploaded")
                except Exception as e:
                    logger.error(f"    ❌ Bucket error: {e}")

    def write_facts(self, records: List[Dict[str, Any]], table_name: str):
        """Write fact tables with event-based timestamp partitioning."""
        if not records:
            return
            
        logger.info(f"\n💾 Writing {table_name} with event-based partitioning...")
        df = pd.DataFrame(records)
        
        # Normalize commence_time to standard ISO format for consistent partitioning
        df['commence_time'] = pd.to_datetime(df['commence_time']).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Group by commence_time (kickoff) - one partition per game
        for commence_time, group_df in df.groupby('commence_time'):
            if self.save_to_bucket:
                success = store_odds_data(
                    df=group_df,
                    table_name=table_name,
                    schema=self.cfg.bucket_schema,
                    timestamp=str(commence_time)
                )
                if success:
                    logger.info(f"  ✓ Stored {len(group_df):,} rows for game {commence_time}")
        
        # Also save CSV if enabled
        if self.cfg.save_to_csv:
            data_dir = Path.cwd() / "data"
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_path = data_dir / f"{table_name}_{timestamp}.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"  ✓ CSV: {csv_path}")

class BackfillOrchestrator:
    """Orchestrates the backfill process using a stateful context and modular components."""
    def __init__(self, cfg: Any):
        self.cfg = cfg
        self.context = BackfillContext(cfg)
        _, self.save_to_bucket = setup_bucket_adapter(cfg)
        self.writer = BackfillWriter(cfg, self.save_to_bucket)

    def run(self):
        """Main entry point for the backfill process."""
        validate_and_log_config(self.cfg)
        
        try:
            # Iterate through seasons
            for season in range(self.cfg.season_range[0], self.cfg.season_range[1] + 1):
                self._process_season(season)
            
            # Log completion summary
            self._report_summary()
            
            # Write accumulated data
            self.writer.write_dimensions(self.context.dim_accumulators)
            self.writer.write_facts(self.context.fact_raw_records, 'fact_odds_raw')
            self.writer.write_facts(self.context.fact_features_records, 'fact_odds_features')
            
            logger.info(f"\n{'=' * 80}\n✅ ALL DATA WRITTEN SUCCESSFULLY\n{'=' * 80}\n")
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Backfill interrupted by user")
        except Exception as e:
            logger.error(f"\n❌ Backfill failed: {e}", exc_info=True)
            raise

    def _process_season(self, season: int):
        """Process all games in a single season."""
        logger.info(f"\n{'='*80}\n🏈 PROCESSING SEASON {season}\n{'='*80}")
        
        all_games = fetch_season_schedule_cached(
            cfg=self.cfg,
            season=season,
            save_to_bucket=self.save_to_bucket,
            week_range=self.cfg.week_range
        )
        
        if not all_games:
            logger.warning(f"No games found for {season} season")
            return

        # Track if cache was used (for cost estimation)
        if self.save_to_bucket:
            try:
                cached_df = read_odds_data(table_name='dim_oddapi_game', schema=self.cfg.bucket_schema)
                if cached_df is not None and not cached_df.empty:
                    season_games = cached_df[cached_df['commence_time'].astype(str).str.startswith(str(season))]
                    self.context.used_cache = not season_games.empty
            except Exception:
                self.context.used_cache = False

        # Filter games by week range
        games = []
        for game in all_games:
            commence_time = game.get('commence_time')
            if not commence_time: continue
            
            week_num = game.get('week_num') or calculate_nfl_week(isoparse(commence_time), season)
            if self.cfg.week_range[0] <= week_num <= self.cfg.week_range[1]:
                games.append(game)
        
        logger.info(f"\n✓ Filtered to {len(games)} games in weeks {self.cfg.week_range[0]}-{self.cfg.week_range[1]}")
        
        if not self.context.estimated_cost:
            self.context.estimated_cost = estimate_backfill_cost(self.cfg, games, used_cache=self.context.used_cache)
        
        self.context.total_games += len(games)
        
        for idx, game in enumerate(games, 1):
            self._process_game(game, idx, len(games), season)

    def _process_game(self, game: Dict[str, Any], idx: int, total: int, season: int):
        """Process all snapshots for a single game."""
        game_id = game.get('id')
        commence_time = game.get('commence_time')
        if not game_id or not commence_time:
            return

        kickoff_utc = isoparse(commence_time)
        week_num = calculate_nfl_week(kickoff_utc, season)
        window_info = classify_game_window(kickoff_utc)
        
        logger.info(f"\n[{idx}/{total}] {game.get('away_team')} @ {game.get('home_team')}")
        logger.info(f"  Event ID: {game_id} | Kickoff: {commence_time} | Week: {week_num} | Window: {window_info['window_label']}")
        
        all_snapshots = collect_game_snapshots(self.cfg, game, save_to_bucket=self.save_to_bucket)
        
        # Filter existing snapshots
        pending = []
        for s in all_snapshots:
            if not snapshot_exists(self.cfg, game_id, s['timestamp'], s['role'], self.save_to_bucket, commence_time):
                pending.append(s)
            else:
                self.context.skipped_snapshots += 1
        
        if not pending:
            logger.info(f"  ⏭️  All {len(all_snapshots)} snapshots exist, skipping")
            return

        if len(pending) < len(all_snapshots):
            logger.info(f"  Snapshots to process: {len(pending)}/{len(all_snapshots)} ({len(all_snapshots)-len(pending)} exist)")

        for s_idx, snap in enumerate(pending, 1):
            self._process_snapshot(snap, game_id, s_idx, len(pending))
            time.sleep(self.cfg.delay_between_snapshots)
        
        time.sleep(self.cfg.delay_between_events)

    def _process_snapshot(self, snap: Dict[str, Any], game_id: EventID, idx: int, total: int):
        """Fetch, normalize, and accumulate data for a single snapshot."""
        self.context.total_snapshots += 1
        snapshot_ts = snap['timestamp']
        snapshot_role = snap['role']
        window_label = snap['window_label']
        snapshot_str = snapshot_ts.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        logger.info(f"    [{idx}/{total}] {snapshot_role}: {snapshot_str}")
        
        try:
            if 'game_event' in snap:
                game_event = snap['game_event']
                snapshot_timestamp = snap['snapshot_timestamp']
                previous_timestamp = snap['previous_timestamp']
                next_timestamp = snap['next_timestamp']
            else:
                resp = api.fetch_historical_events_data(sport_key=self.cfg.sport_key, date=snapshot_str)
                snapshot_timestamp = resp.get('timestamp')
                previous_timestamp = resp.get('previous_timestamp')
                next_timestamp = resp.get('next_timestamp')
                game_event = next((e for e in resp.get('data', []) if e.get('event_id') == game_id), None)

            if not game_event:
                logger.warning(f"      Game {game_id} not found in snapshot")
                return

            flat_records = _process_single_event(
                event=game_event,
                timestamp_str=snapshot_str,
                snapshot_ts=snapshot_timestamp,
                snapshot_role=snapshot_role,
                window_label=window_label,
                previous_ts=previous_timestamp,
                next_ts=next_timestamp,
                cfg=self.cfg
            )
            
            if flat_records:
                self.context.total_events_processed += 1
                normalized = normalize_to_star_schema(flat_records)
                self.context.add_normalized_data(normalized)
                logger.info(f"      ✓ Extracted {len(flat_records)} odds records")

        except QuotaExceededException as e:
            logger.error(f"      ❌ Quota exceeded: {e}")
            raise
        except Exception as e:
            logger.error(f"      ❌ Error processing snapshot: {e}")

    def _report_summary(self):
        """Log final backfill and quota summary."""
        logger.info(f"\n{'=' * 80}\nBACKFILL COMPLETE\n{'=' * 80}")
        logger.info(f"Total Games: {self.context.total_games}")
        logger.info(f"Total Snapshots: {self.context.total_snapshots}")
        logger.info(f"Events Processed: {self.context.total_events_processed}")
        logger.info(f"Skipped Snapshots: {self.context.skipped_snapshots}")
        logger.info(f"Fact Records (Raw): {len(self.context.fact_raw_records)}")
        logger.info(f"Fact Records (Features): {len(self.context.fact_features_records)}")
        
        if self.context.quota_tracker and self.context.starting_quota:
            status = self.context.quota_tracker.get_usage_summary()
            actual = status['requests_used'] - self.context.starting_quota['used']
            logger.info(f"\n{'=' * 80}\nQUOTA USAGE SUMMARY\n{'=' * 80}")
            logger.info(f"ACTUAL CONSUMED: {actual:,} credits")
            if self.context.estimated_cost:
                logger.info(f"ESTIMATED COST:  {self.context.estimated_cost['total']:,} credits")
            logger.info(f"{'=' * 80}\n")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def backfill_historical_odds():
    """Entry point for the backfill script."""
    cfg = get_settings().backfill
    orchestrator = BackfillOrchestrator(cfg)
    orchestrator.run()

if __name__ == "__main__":
    backfill_historical_odds()
