import json
import os
import time
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from commonv2.core.logging import setup_logger
from odds_api.core import setup_quota_tracker, QuotaExceededException
from odds_api.etl.load.bucket import (
    read_odds_data,
    store_odds_data,
    setup_bucket_adapter,
    normalize_timestamp,
    extract_date_part
)
from odds_api.utils.schedulers.base import BaseScheduler
from odds_api.etl.extract import api
from odds_api.etl.transform.historical import normalize_to_star_schema
from odds_api.etl.transform.odds import flatten_event_odds
from dateutil.parser import isoparse
from commonv2.utils.decorators import retry_with_backoff

logger = setup_logger('odds_api.etl.backfill', project_name='ODDS_API')

class BackfillContext:
    """
    Stateful tracking of backfill progress with JSON persistence.
    """
    def __init__(self, cfg: Any, state_path: str = ".backfill_state"):
        self.cfg = cfg
        self.state_path = Path(state_path)
        self.run_id = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        self.state = {
            "season": None,
            "last_game_idx": 0,
            "processed_game_ids": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "quota_consumed": 0,
            "quota_at_start": 0,
            "estimated_quota": 0
        }
        
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
        
        # Runtime counters
        self.total_games = 0
        self.total_snapshots = 0
        self.total_events_processed = 0
        self.skipped_snapshots = 0
        
        # Snapshot cost tracking
        self.snapshot_costs_by_type = {
            'OPEN_T6D': [],
            'PREGAME_SCHEDULED': [],
            'IN_GAME': []
        }
        self.snapshot_counts_by_type = {
            'OPEN_T6D': 0,
            'PREGAME_SCHEDULED': 0,
            'IN_GAME': 0
        }
        self.estimated_in_game_count = 0
        self.actual_in_game_count = 0
        
        self.quota_tracker = setup_quota_tracker(cfg)
        
        # Track starting quota usage
        if self.quota_tracker:
            summary = self.quota_tracker.get_usage_summary()
            self.state["quota_at_start"] = summary['requests_used']

    def save(self):
        """Atomic write of state to JSON file."""
        temp_path = self.state_path.with_suffix(".tmp")
        with open(temp_path, 'w') as f:
            json.dump(self.state, f, indent=4)
        os.replace(temp_path, self.state_path)
        logger.info(f"State saved to {self.state_path}")

    def load(self) -> bool:
        """Load state from JSON file if it exists."""
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r') as f:
                    self.state = json.load(f)
                logger.info(f"Resuming from state: Season {self.state['season']}, Game Index {self.state['last_game_idx']}")
                return True
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        return False

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

    def clear_accumulators(self):
        """Clear in-memory records after flushing to storage."""
        for key in self.dim_accumulators:
            self.dim_accumulators[key] = []
        self.fact_raw_records = []
        self.fact_features_records = []

class BackfillWriter:
    """
    Handles partitioned storage in the bucket and CSV exports.
    """
    def __init__(self, cfg: Any, save_to_bucket: bool):
        self.cfg = cfg
        self.save_to_bucket = save_to_bucket

    def flush(self, context: BackfillContext):
        """Flush all accumulated data to storage."""
        logger.info("💾 Flushing accumulated data to storage...")
        
        # Write Dimensions
        self.write_dimensions(context.dim_accumulators, run_id=context.run_id)
        
        # Write Facts
        self.write_facts(context.fact_raw_records, 'fact_odds_raw')
        self.write_facts(context.fact_features_records, 'fact_odds_features')
        
        # Clear context to free memory
        context.clear_accumulators()

    def write_dimensions(self, dim_accumulators: Dict[str, List[pd.DataFrame]], run_id: Optional[str] = None):
        """Write dimension tables with merging and deduplication."""
        for table_name, df_list in dim_accumulators.items():
            if not df_list:
                continue
            
            new_df = pd.concat(df_list, ignore_index=True)
            
            # Metadata Enrichment
            if run_id:
                new_df['_backfill_run_id'] = run_id
            
            if hasattr(self.cfg, 'season_range'):
                new_df['_season_range_start'] = self.cfg.season_range[0]
                new_df['_season_range_end'] = self.cfg.season_range[1]
            
            # Load existing if bucket enabled
            existing_df = None
            if self.save_to_bucket:
                try:
                    existing_df = read_odds_data(table_name=table_name, schema=self.cfg.bucket_schema)
                except Exception:
                    pass
            
            combined_df = pd.concat([existing_df, new_df], ignore_index=True) if existing_df is not None else new_df
            
            # Deduplicate
            pk_map = {
                'dim_oddapi_game': 'event_id',
                'dim_team': 'team_id',
                'dim_bookmaker': 'bookmaker_key',
                'dim_market': 'market_key',
                'dim_date': 'date'
            }
            pk_col = pk_map.get(table_name)
            if pk_col and pk_col in combined_df.columns:
                if '_extracted_at' in combined_df.columns:
                    combined_df = combined_df.sort_values('_extracted_at')
                combined_df = combined_df.drop_duplicates(subset=[pk_col], keep='last')
            
            # Save to bucket
            if self.save_to_bucket:
                try:
                    store_odds_data(df=combined_df, table_name=table_name, schema=self.cfg.bucket_schema)
                except Exception as e:
                    logger.error(f"Failed to write {table_name} to bucket: {e}")
            
            # Save to CSV
            if self.cfg.save_to_csv:
                from odds_api.etl.transform.core import write_to_csv
                write_to_csv(combined_df, f"{table_name}_latest")

    def write_facts(self, records: List[Dict[str, Any]], table_name: str):
        """Write fact tables with event-based partitioning."""
        if not records:
            return
            
        df = pd.DataFrame(records)
        df['commence_time'] = pd.to_datetime(df['commence_time']).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        for commence_time, group_df in df.groupby('commence_time'):
            if self.save_to_bucket:
                try:
                    store_odds_data(
                        df=group_df,
                        table_name=table_name,
                        schema=self.cfg.bucket_schema,
                        timestamp=str(commence_time)
                    )
                except Exception as e:
                    logger.error(f"Failed to write {table_name} partition {commence_time} to bucket: {e}")
        
        if self.cfg.save_to_csv:
            from odds_api.etl.transform.core import write_to_csv
            write_to_csv(df, f"{table_name}_{int(time.time())}")

class BackfillOrchestrator:
    """
    Main class managing the backfill lifecycle.

    Note: Concurrent backfills to the same season are not supported.
    """
    def __init__(self, cfg: Any, scheduler: BaseScheduler):
        self.cfg = cfg
        self.scheduler = scheduler
        self.context = BackfillContext(cfg)
        _, self.save_to_bucket = setup_bucket_adapter(cfg)
        self.writer = BackfillWriter(cfg, self.save_to_bucket)

    def _report_summary(self):
        """Log final summary of the backfill run with enhanced quota reconciliation."""
        duration = datetime.now(timezone.utc) - isoparse(self.context.state["started_at"])
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"BACKFILL SUMMARY REPORT")
        logger.info(f"{'=' * 80}")
        logger.info(f"Run ID: {self.context.run_id}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Seasons Processed: {self.cfg.season_range[0]}-{self.cfg.season_range[1]}")
        logger.info(f"Total Games Processed: {self.context.total_games}")
        logger.info(f"Total Snapshots Processed: {self.context.total_events_processed}")
        logger.info(f"Skipped Snapshots: {self.context.skipped_snapshots}")
        
        # Snapshot breakdown by type
        logger.info("")
        logger.info("SNAPSHOT BREAKDOWN")
        logger.info("─" * 80)
        for snapshot_type, count in self.context.snapshot_counts_by_type.items():
            if count > 0:
                logger.info(f"{snapshot_type:20s} {count:4d} snapshots")
        logger.info("─" * 80)
        
        # In-game collection efficiency
        if self.context.estimated_in_game_count > 0 or self.context.actual_in_game_count > 0:
            logger.info("")
            logger.info("IN-GAME SNAPSHOT COLLECTION")
            logger.info("─" * 80)
            logger.info(f"Estimated In-Game Snapshots: {self.context.estimated_in_game_count}")
            logger.info(f"Actual In-Game Snapshots:    {self.context.actual_in_game_count}")
            if self.context.estimated_in_game_count > 0:
                efficiency = (self.context.actual_in_game_count / self.context.estimated_in_game_count) * 100
                logger.info(f"Collection Efficiency:       {efficiency:.1f}%")
            logger.info("─" * 80)
        
        # Snapshot cost analysis
        has_cost_data = any(len(costs) > 0 for costs in self.context.snapshot_costs_by_type.values())
        if has_cost_data:
            logger.info("")
            logger.info("SNAPSHOT COST ANALYSIS")
            logger.info("─" * 80)
            for snapshot_type, costs in self.context.snapshot_costs_by_type.items():
                if costs:
                    avg_cost = sum(costs) / len(costs)
                    min_cost = min(costs)
                    max_cost = max(costs)
                    logger.info(f"{snapshot_type:20s} | Count: {len(costs):3d} | Avg: {avg_cost:5.1f} | Min: {min_cost:2d} | Max: {max_cost:2d}")
            logger.info("─" * 80)
        
        # Quota reconciliation
        logger.info("")
        logger.info("QUOTA TRACKING RECONCILIATION")
        logger.info("─" * 80)
        
        quota_at_start = self.context.state.get('quota_at_start', 0)
        quota_at_end = self.context.state.get('quota_consumed', 0)
        actual_quota_consumed = quota_at_end - quota_at_start
        estimated_quota = self.context.state.get('estimated_quota', 0)
        
        logger.info(f"Pre-Run Estimate:     {estimated_quota:>6,} credits")
        logger.info(f"Actual Consumption:   {actual_quota_consumed:>6,} credits")
        
        if estimated_quota > 0:
            variance = actual_quota_consumed - estimated_quota
            variance_pct = (variance / estimated_quota) * 100
            variance_indicator = "✓" if abs(variance_pct) < 10 else "⚠"
            logger.info(f"Variance:             {variance:>+6,} credits ({variance_pct:>+5.1f}%) {variance_indicator}")
            
            # Estimation quality
            if abs(variance_pct) < 5:
                logger.info(f"Estimation Quality:   Excellent (<5% variance)")
            elif abs(variance_pct) < 10:
                logger.info(f"Estimation Quality:   Good (<10% variance)")
            elif abs(variance_pct) < 15:
                logger.info(f"Estimation Quality:   Acceptable (<15% variance)")
            else:
                logger.info(f"Estimation Quality:   Needs Review (≥15% variance)")
                logger.warning(
                    f"⚠️  QUOTA ESTIMATION VARIANCE EXCEEDED 15% ⚠️\n"
                    f"   This may indicate:\n"
                    f"   - Unusual bookmaker availability patterns\n"
                    f"   - API pricing changes\n"
                    f"   - Configuration mismatch\n"
                    f"   Consider reviewing estimation parameters"
                )
        
        logger.info("─" * 80)
        
        logger.info("")
        logger.info(f"{'=' * 80}\n")

    def _validate_config(self):
        """Validate backfill configuration and API keys."""
        from odds_api.config import get_settings
        settings = get_settings()
        if not settings.paid_odds_api_key:
            raise ValueError("PAID_ODDS_API_KEY required for historical endpoints")
        
        if self.cfg.season_range[0] > self.cfg.season_range[1]:
            raise ValueError(f"Invalid season_range: {self.cfg.season_range[0]} > {self.cfg.season_range[1]}")
        
        if hasattr(self.cfg, 'week_range'):
            if self.cfg.week_range[0] > self.cfg.week_range[1]:
                raise ValueError(f"Invalid week_range: {self.cfg.week_range[0]} > {self.cfg.week_range[1]}")
            if self.cfg.week_range[0] < 1 or self.cfg.week_range[1] > 22:
                raise ValueError(f"week_range must be between 1 and 22 (got {self.cfg.week_range})")

    def _log_startup_banner(self):
        """Log detailed configuration and startup settings."""
        logger.info("=" * 80)
        logger.info("EVENT-DRIVEN HISTORICAL ODDS BACKFILL")
        logger.info("=" * 80)
        logger.info(f"Sport: {self.cfg.sport_key}")
        logger.info(f"Markets: {', '.join(self.cfg.markets)}")
        logger.info(f"Seasons: {self.cfg.season_range[0]} to {self.cfg.season_range[1]}")
        if hasattr(self.cfg, 'week_range'):
            logger.info(f"Weeks: {self.cfg.week_range[0]} to {self.cfg.week_range[1]}")
        logger.info(f"Week-Open Snapshot (T-6d): {'Enabled' if self.cfg.include_week_open_snapshot else 'Disabled'}")
        logger.info(f"In-Game Odds: {'Enabled' if self.cfg.include_in_game_odds else 'Disabled'}")
        logger.info(f"Pre-game Scheduled: {self.cfg.pregame_scheduled_minutes} minutes before kickoff (target)")
        logger.info(f"Rate Limiting: {self.cfg.delay_between_events}s between events, {self.cfg.delay_between_snapshots}s between snapshots")
        
        # Output destination (mutually exclusive)
        if self.save_to_bucket:
            logger.info("Output: Bucket")
        elif self.cfg.save_to_csv:
            logger.info("Output: CSV")
        else:
            logger.info("Output: None (no output!)")
        
        if hasattr(self.cfg, 'enable_quota_tracking'):
            logger.info(f"Quota Tracking: {'Enabled' if self.cfg.enable_quota_tracking else 'Disabled'}")
        logger.info("=" * 80)

    def _process_season(self, season: int):
        """Process all games in a single season."""
        games = self.scheduler.get_schedule(season)
        if games:
            logger.info(f"Sample game data structure (first game):")
            logger.info(f"  Available keys: {list(games[0].keys())}")
            logger.info(f"  Full game data: {games[0]}")
        total_games = len(games)
        start_idx = self.context.state["last_game_idx"]
        
        for idx in range(start_idx, total_games):
            game = games[idx]
            self._process_game(game, idx + 1, total_games)
            
            game_id = game.get('id')
            event_id = game.get('event_id', game_id)
            self.context.state["last_game_idx"] = idx + 1
            self.context.state["processed_game_ids"].append(game_id)
            logger.info(f"  Completed game {idx}/{total_games}: ID={game_id}, Event ID={event_id}")
            
            # Save state after each game
            self.context.save()
            
            # Periodic flush every 50 games
            if (idx + 1) % 50 == 0:
                self.writer.flush(self.context)

    def _process_game(self, game: Dict[str, Any], idx: int, total: int):
        """Process all snapshots for a single game."""
        self.context.total_games += 1
        
        week_info = ""
        if 'week_num' in game:
            week_info = f" [Week {game['week_num']} | {game.get('window_label', 'UNK')}]"

        game_id = game.get('id', 'UNKNOWN')
        event_id = game.get('event_id', game_id)  # Fallback to 'id' if 'event_id' not present
        commence_time = game.get('commence_time', 'UNKNOWN')
        logger.info(f"[{idx}/{total}] Processing game: {game.get('away_team')} @ {game.get('home_team')} | Kickoff: {commence_time} | ID: {game_id} | Event ID: {event_id}{week_info}")
        
        all_snapshots = self.scheduler.get_snapshots(game, save_to_bucket=self.save_to_bucket)
        
        # Filter existing snapshots
        pending = []
        for s in all_snapshots:
            if not self.scheduler.snapshot_exists(game_id, game.get('commence_time'), s['timestamp'], s['role']):
                pending.append(s)
            else:
                logger.info(f"    ⏭️  Skipping {s['role']} snapshot (already exists in bucket)")
                self.context.skipped_snapshots += 1
        
        if not pending:
            logger.info(f"  ⏭️  All {len(all_snapshots)} snapshots exist, skipping")
            return

        if len(pending) < len(all_snapshots):
            logger.info(f"  Snapshots to process: {len(pending)}/{len(all_snapshots)} ({len(all_snapshots)-len(pending)} exist)")

        # Collect all records for the game across all snapshots
        game_flat_records = []
        snapshots_with_data = 0

        for s_idx, snap in enumerate(pending, 1):
            snap_records = self._fetch_snapshot_records(snap, game_id, s_idx, len(pending))
            if snap_records:
                game_flat_records.extend(snap_records)
                snapshots_with_data += 1
            time.sleep(self.cfg.delay_between_snapshots)
        
        if game_flat_records:
            # Normalize all snapshots for this game together!
            # This allows add_opening_closing_lines to see the full history for accurate CLV.
            normalized = normalize_to_star_schema(game_flat_records)
            self.context.add_normalized_data(normalized)
            self.context.total_events_processed += snapshots_with_data
            logger.info(f"    ✓ Processed {snapshots_with_data} snapshots for Game ID: {game.get('id')}")
            
            # Market-level diagnostic snapshot counts
            self._log_market_snapshot_diagnostics(game_flat_records, event_id)
        
        time.sleep(self.cfg.delay_between_events)

    def _log_market_snapshot_diagnostics(self, flat_records: List[Dict[str, Any]], event_id: str):
        """
        Log snapshot counts per bookmaker/market/role for diagnostic purposes.
        
        Example output:
            Event ID: 8dcb2a6bf542ccb7e6bc58f83c8fc2ac
              fanduel | h2h     | OPEN_T6D: 2, PREGAME_SCHEDULED: 2, IN_GAME: 6
              fanduel | spreads | OPEN_T6D: 2, PREGAME_SCHEDULED: 2, IN_GAME: 6
              draftkings | h2h  | OPEN_T6D: 2, PREGAME_SCHEDULED: 2, IN_GAME: 8
        """
        from collections import defaultdict
        
        # Group by (bookmaker, market, snapshot_role)
        snapshot_counts = defaultdict(lambda: defaultdict(int))
        
        for record in flat_records:
            bookmaker = record.get('bookmaker_key', 'unknown')
            market = record.get('market_key', 'unknown')
            role = record.get('snapshot_role', 'unknown')
            key = (bookmaker, market)
            snapshot_counts[key][role] += 1
        
        if snapshot_counts:
            logger.info(f"    Market-level snapshot counts for Event ID: {event_id}")
            for (bookmaker, market), role_counts in sorted(snapshot_counts.items()):
                # Format role counts as "OPEN_T6D: 2, PREGAME_SCHEDULED: 2, IN_GAME: 8"
                role_summary = ', '.join([f"{role}: {count}" for role, count in sorted(role_counts.items())])
                logger.info(f"      {bookmaker:12s} | {market:8s} | {role_summary}")
    
    def _fetch_snapshot_records(self, snap: Dict[str, Any], event_id: str, idx: int, total: int) -> List[Dict[str, Any]]:
        """Fetch and flatten data for a single snapshot."""
        snapshot_ts = snap['timestamp']
        snapshot_role = snap['role']
        window_label = snap['window_label']
        snapshot_str = snapshot_ts.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        logger.info(f"    [{idx}/{total}] {snapshot_role}: {snapshot_str} | Event ID: {event_id}")
        
        # Track quota before this snapshot
        quota_before = 0
        if self.context.quota_tracker:
            summary = self.context.quota_tracker.get_usage_summary()
            quota_before = summary['requests_used']
        
        try:
            if 'game_event' in snap:
                # Use cached data from crawl
                game_event = snap['game_event']
                snapshot_timestamp = snap['snapshot_timestamp']
                previous_timestamp = snap['previous_timestamp']
                next_timestamp = snap['next_timestamp']
            else:
                @retry_with_backoff(max_retries=3)
                def fetch_data():
                    return api.fetch_historical_events_data(sport_key=self.cfg.sport_key, date=snapshot_str)
                
                resp = fetch_data()
                snapshot_timestamp = resp.get('timestamp')
                previous_timestamp = resp.get('previous_timestamp')
                next_timestamp = resp.get('next_timestamp')
                
                events = resp.get('data', [])
                # Check both 'id' and 'event_id' as different endpoints use different keys
                game_event = next((e for e in events if e.get('id') == event_id or e.get('event_id') == event_id), None)
                
                if not game_event:
                    logger.warning(f"      Game {event_id} not found in snapshot (Total events: {len(events)})")
                    if events:
                        sample_ids = [e.get('id') or e.get('event_id') for e in events[:5]]
                        logger.info(f"      Sample IDs in snapshot: {sample_ids}")
                        # Check if it's a sport mismatch
                        sample_sports = list(set([e.get('sport_key') for e in events[:5]]))
                        logger.info(f"      Sample sports in snapshot: {sample_sports}")
                    return []

            # Fetch detailed odds for the event
            @retry_with_backoff(max_retries=3)
            def fetch_odds():
                return api.fetch_historical_event_odds_data(
                    sport_key=self.cfg.sport_key,
                    event_id=event_id,
                    date=snapshot_str,
                    markets=self.cfg.markets
                )
            
            odds_resp = fetch_odds()
            event_data = odds_resp.get('data', {})
            
            flat_records = flatten_event_odds(
                event_data=event_data,
                snapshot_timestamp=str(snapshot_timestamp or ''),
                snapshot_requested_ts=snapshot_str,
                snapshot_role=snapshot_role,
                window_label=window_label,
                previous_timestamp=str(previous_timestamp or ''),
                next_timestamp=str(next_timestamp or '')
            )
            
            if flat_records:
                logger.info(f"      ✓ Extracted {len(flat_records)} odds records for Event ID: {event_id}")
            
            # Update quota tracking and calculate cost for this snapshot
            if self.context.quota_tracker:
                summary = self.context.quota_tracker.get_usage_summary()
                quota_after = summary['requests_used']
                snapshot_cost = quota_after - quota_before
                
                # Track cost by snapshot type
                if snapshot_role in self.context.snapshot_costs_by_type:
                    self.context.snapshot_costs_by_type[snapshot_role].append(snapshot_cost)
                
                # Track snapshot counts
                if snapshot_role in self.context.snapshot_counts_by_type:
                    self.context.snapshot_counts_by_type[snapshot_role] += 1
                
                # Track in-game specifically
                if snapshot_role == 'IN_GAME':
                    self.context.actual_in_game_count += 1
                
                self.context.state["quota_consumed"] = quota_after
            
            return flat_records

        except QuotaExceededException:
            raise
        except Exception as e:
            logger.error(f"      ❌ Error fetching snapshot: {e}")
            return []

    def _handle_interruption(self, reason: str):
        """Handle process interruption by flushing data and saving state."""
        logger.info(f"⚠️ Handling interruption: {reason}")
        self.writer.flush(self.context)
        self.context.save()
        logger.info(f"Resume with: --resume (Season: {self.context.state['season']}, Game Index: {self.context.state['last_game_idx']})")

    def run(self, resume: bool = False, confirm_cost: bool = False):
        """Main entry point for the backfill process."""
        self._validate_config()
        self._log_startup_banner()
        
        if resume:
            self.context.load()
        
        try:
            start_season = self.context.state["season"] or self.cfg.season_range[0]
            for season in range(start_season, self.cfg.season_range[1] + 1):
                self.context.state["season"] = season
                
                # Budget Guard
                if self.context.state["last_game_idx"] == 0:
                    games = self.scheduler.get_schedule(season)
                    cost = self.scheduler.estimate_cost(games)
                    logger.info(f"Estimated cost for season {season}: {cost['total']:,} credits")
                    
                    if cost['total'] > 5000 and not confirm_cost:
                        logger.warning(f"⚠️ High cost detected ({cost['total']:,} > 5,000). Use --confirm to proceed.")
                        return
                
                self._process_season(season)
                # Prepare state for next season
                self.context.state["season"] = season + 1
                self.context.state["last_game_idx"] = 0
                self.context.save()
            
            # Final flush
            self.writer.flush(self.context)
            self._report_summary()
            logger.info("✅ Backfill completed successfully.")
            
        except QuotaExceededException as e:
            logger.error(f"❌ Quota exceeded: {e}")
            self._handle_interruption("Quota Exceeded")
            raise
        except KeyboardInterrupt:
            logger.warning("⚠️ Backfill interrupted by user.")
            self._handle_interruption("User Interruption")
        except Exception as e:
            logger.error(f"❌ Backfill failed: {e}", exc_info=True)
            self._handle_interruption(f"Error: {str(e)}")
            raise
