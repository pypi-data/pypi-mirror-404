"""
Pipeline orchestration - handles ETL workflows without CLI dependencies.
Decoupled from command-line interface for reusability in other contexts.
"""

import os
import json
import time
import psutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

from commonv2 import get_logger
from odds_api.etl.load import store_odds_data
from commonv2.utils.decorators import log_execution_time
from commonv2.utils.validation import validate_dataframe
from odds_api.config.pipelines import PIPELINES

logger = get_logger(__name__)

class DataPipeline(ABC):
    """Abstract Base Class for all data pipelines."""
    
    def __init__(self):
        self.state_dir = Path(".pipelines")
        self.lock_dir = Path(".pipelines/locks")
        self.state_dir.mkdir(exist_ok=True)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.config = PIPELINES.get(self.key, {})

    @property
    @abstractmethod
    def key(self) -> str:
        """Unique identifier for the pipeline."""
        pass

    @property
    def required_cols(self) -> List[str]:
        """List of columns for validation."""
        return self.config.get('required_cols', [])

    @property
    def table_name(self) -> str:
        """Target bucket/database table."""
        return self.config.get('table', self.key)

    @property
    def update_interval(self) -> int:
        """Minimum seconds between runs."""
        return self.config.get('update_interval', 60)

    @property
    def description(self) -> str:
        """Human-readable description."""
        return self.config.get('description', f"{self.key} pipeline")

    @abstractmethod
    def fetch(self, **kwargs) -> pd.DataFrame:
        """Concrete implementation of data retrieval."""
        pass

    def post_process(self, df: pd.DataFrame, **kwargs):
        """Hook for pipeline-specific logic (e.g., CSV exports)."""
        if kwargs.get('write_csv'):
            from odds_api.etl.transform.core import write_to_csv
            write_to_csv(df, self.table_name)

    def _get_state_path(self) -> Path:
        return self.state_dir / f"{self.key}.json"

    def _get_lock_path(self) -> Path:
        return self.lock_dir / f"{self.key}.lock"

    def _check_interval(self, force: bool = False) -> bool:
        """Check if the pipeline can run based on the update interval."""
        state_path = self._get_state_path()
        if not state_path.exists() or force:
            return True

        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
                last_run = state.get('last_run', 0)
                elapsed = time.time() - last_run
                if elapsed < self.update_interval:
                    logger.warning(
                        f"Pipeline '{self.key}' cooling down. "
                        f"Elapsed: {int(elapsed)}s, Required: {self.update_interval}s. "
                        "Use --force to bypass."
                    )
                    return False
        except Exception as e:
            logger.warning(f"Failed to read state for {self.key}: {e}")
        
        return True

    def _save_state(self, rows_processed: int):
        """Save the last run timestamp and status."""
        state_path = self._get_state_path()
        state = {
            'last_run': time.time(),
            'last_rows': rows_processed,
            'status': 'success'
        }
        try:
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state for {self.key}: {e}")

    def _acquire_lock(self) -> bool:
        """Implement PID-based file locking with stale lock detection."""
        lock_path = self._get_lock_path()
        if lock_path.exists():
            try:
                with open(lock_path, 'r') as f:
                    pid = int(f.read().strip())
                
                if psutil.pid_exists(pid):
                    logger.error(f"Pipeline '{self.key}' is already running (PID: {pid})")
                    return False
                else:
                    logger.warning(f"Clearing stale lock for '{self.key}' (PID {pid} not found)")
                    lock_path.unlink()
            except (ValueError, OSError) as e:
                logger.warning(f"Failed to read/clear lock for {self.key}: {e}")
                lock_path.unlink(missing_ok=True)

        try:
            with open(lock_path, 'w') as f:
                f.write(str(os.getpid()))
            return True
        except Exception as e:
            logger.error(f"Failed to acquire lock for {self.key}: {e}")
            return False

    def _release_lock(self):
        """Release the PID-based lock."""
        lock_path = self._get_lock_path()
        if lock_path.exists():
            lock_path.unlink(missing_ok=True)

    @log_execution_time
    def run(self, **kwargs) -> int:
        """Orchestrate the pipeline execution."""
        force = kwargs.get('force', False)
        dry_run = kwargs.get('dry_run', False)

        if not self._check_interval(force):
            return 0

        if not self._acquire_lock():
            return 0

        try:
            logger.info(f"Starting {self.description}...")
            
            # Step 1: Fetch
            df = self.fetch(**kwargs)
            
            if df.empty:
                logger.warning(f"No data returned for {self.key}")
                self._save_state(0)
                return 0

            # Step 2: Validate
            validate_dataframe(df, self.required_cols)
            logger.info(f"Processed {len(df)} {self.key} records")

            # Step 3: Persist
            if not dry_run:
                timestamp = kwargs.get('timestamp')
                success = store_odds_data(
                    df=df,
                    table_name=self.table_name,
                    timestamp=timestamp
                )
                if success:
                    logger.info(f"✅ Stored to bucket: oddsapi/{self.table_name} ({len(df):,} rows)")
                else:
                    logger.warning(f"⚠️  Bucket storage failed for {self.table_name}")
            else:
                logger.info("Dry run - skipping bucket storage")

            # Step 4: Post-process
            self.post_process(df, **kwargs)

            if not dry_run:
                self._save_state(len(df))
            
            return len(df)

        except Exception as e:
            logger.error(f"❌ {self.description} failed: {str(e)}", exc_info=True)
            raise
        finally:
            self._release_lock()

class LeaguesPipeline(DataPipeline):
    @property
    def key(self) -> str: return 'leagues'
    @property
    def required_cols(self) -> List[str]: return ['sport_key', 'title', 'active']
    @property
    def table_name(self) -> str: return 'leagues'
    
    def fetch(self, **kwargs) -> pd.DataFrame:
        from odds_api.etl.transform.leagues import get_leagues_data
        return get_leagues_data()

class TeamsPipeline(DataPipeline):
    @property
    def key(self) -> str: return 'teams'
    @property
    def required_cols(self) -> List[str]: return ['participant_id', 'sport_key', 'full_name']
    @property
    def table_name(self) -> str: return 'teams'
    
    def fetch(self, **kwargs) -> pd.DataFrame:
        from odds_api.etl.transform.teams import get_teams_data
        sport_key = kwargs.get('sport_key', 'americanfootball_nfl')
        return get_teams_data(sport_key)

class SchedulePipeline(DataPipeline):
    @property
    def key(self) -> str: return 'schedule'
    @property
    def required_cols(self) -> List[str]: return ['event_id', 'sport_key', 'commence_time', 'home_team', 'away_team']
    @property
    def table_name(self) -> str: return 'schedule'
    
    def fetch(self, **kwargs) -> pd.DataFrame:
        from odds_api.etl.transform.schedule import get_schedule_data
        sport_key = kwargs.get('sport_key', 'americanfootball_nfl')
        return get_schedule_data(sport_key)

class ResultsPipeline(DataPipeline):
    @property
    def key(self) -> str: return 'results'
    @property
    def required_cols(self) -> List[str]: return ['event_id', 'sport_key', 'commence_time', 'home_team', 'away_team']
    @property
    def table_name(self) -> str: return 'results'
    
    def fetch(self, **kwargs) -> pd.DataFrame:
        from odds_api.etl.transform.results import get_results_data
        sport_key = kwargs.get('sport_key', 'americanfootball_nfl')
        days_from = kwargs.get('days_from')
        return get_results_data(sport_key, days_from)

class PropsPipeline(DataPipeline):
    @property
    def key(self) -> str: return 'props'
    @property
    def required_cols(self) -> List[str]: return ['event_id', 'sport_key', 'bookmaker_key', 'market_key']
    @property
    def table_name(self) -> str: return 'props'
    
    def fetch(self, **kwargs) -> pd.DataFrame:
        from odds_api.etl.transform.props import get_props_data
        sport_key = kwargs.get('sport_key', 'americanfootball_nfl')
        event_id = kwargs.get('event_id')
        markets = kwargs.get('markets')
        return get_props_data(sport_key, event_id, markets)

class OddsPipeline(DataPipeline):
    @property
    def key(self) -> str: return 'odds'
    @property
    def required_cols(self) -> List[str]: return ['event_id', 'sport_key', 'bookmaker_key', 'market_key']
    @property
    def table_name(self) -> str: return 'odds'
    
    def fetch(self, **kwargs) -> pd.DataFrame:
        from odds_api.etl.transform.odds import get_odds
        sport_key = kwargs.get('sport_key', 'americanfootball_nfl')
        markets = kwargs.get('markets')
        return get_odds(sport_key=sport_key, markets=markets)

    def post_process(self, df: pd.DataFrame, **kwargs):
        if kwargs.get('write_csv'):
            from odds_api.etl.transform.core import write_to_csv
            # Leverage the source of truth with market splitting enabled
            write_to_csv(df, "odds", split_by_market=True)

class BackfillPipeline(DataPipeline):
    @property
    def key(self) -> str: return 'backfill'
    @property
    def required_cols(self) -> List[str]: return [] # Backfill summary might be different
    @property
    def table_name(self) -> str: return 'backfill_summary'
    
    def fetch(self, **kwargs) -> pd.DataFrame:
        from odds_api.etl.backfill import BackfillOrchestrator
        from odds_api.utils.schedulers.nfl import NFLScheduler
        from odds_api.config.settings import get_settings
        
        cfg = get_settings().backfill
        # Dependency Injection: NFLScheduler is default for now
        scheduler = NFLScheduler(cfg=cfg)
        orchestrator = BackfillOrchestrator(cfg=cfg, scheduler=scheduler)
        
        # Run backfill and return summary as DataFrame
        summary = orchestrator.run(**kwargs)
        return pd.DataFrame([summary])

# Registry of pipeline instances
PIPELINE_REGISTRY: Dict[str, DataPipeline] = {
    'leagues': LeaguesPipeline(),
    'teams': TeamsPipeline(),
    'schedule': SchedulePipeline(),
    'results': ResultsPipeline(),
    'props': PropsPipeline(),
    'odds': OddsPipeline(),
    'backfill': BackfillPipeline()
}

def run_pipeline(pipeline_key: str, **kwargs) -> int:
    """Generic pipeline orchestrator that handles any endpoint."""
    if pipeline_key not in PIPELINE_REGISTRY:
        raise ValueError(f"Unknown pipeline: {pipeline_key}. Available: {list(PIPELINE_REGISTRY.keys())}")
    
    pipeline = PIPELINE_REGISTRY[pipeline_key]
    return pipeline.run(**kwargs)

