"""
Sportsbook NFL scraping pipeline.

Implements Phase 2 of the refactoring plan: Standalone pipeline orchestration
using commonv2 utilities without dependency on odds_api module.

Lifecycle:
    1. fetch() - Browser setup → Scrape → Raw data extraction
    2. validate() - DataFrame column validation
    3. persist() - Bucket storage with 'odds_scraper' schema namespace
    4. post_process() - CSV export if requested
"""

import os
import json
import time
import psutil
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

from commonv2 import get_logger
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2.utils.decorators import log_execution_time
from commonv2.utils.validation import validate_dataframe
from odds_scraper.config.settings import get_odds_scraper_settings
from odds_scraper.core.browser import BrowserEngine
from odds_scraper.core.processor import OddsDataProcessor

logger = get_logger(__name__)


class SportsbookPipeline:
    """
    Sportsbook NFL odds scraping pipeline.
    
    Standalone implementation with state management, locking, and validation
    using commonv2 utilities directly (no odds_api dependency).
    
    Features:
        - Async browser-based scraping with anti-detection
        - Automatic data transformation and validation
        - Bucket storage with 'odds_scraper' schema namespace
        - Optional CSV export
        - PID-based locking (prevents concurrent runs)
        - Cooldown interval enforcement (prevents rate limiting)
        - State persistence for tracking last run
    
    Example:
        >>> pipeline = SportsbookPipeline()
        >>> rows = pipeline.run(markets=['spreads', 'totals', 'h2h'], write_csv=True)
        >>> print(f"Processed {rows} records")
    """
    
    def __init__(self):
        """
        Initialize the Sportsbook pipeline.
        
        Sets up:
            - State and lock directories
            - Sportsbook-specific configuration
            - Browser engine for scraping
            - Data processor for transformation
            - Bucket adapter for persistence
        """
        # State management directories
        self.state_dir = Path(".pipelines")
        self.lock_dir = Path(".pipelines/locks")
        self.state_dir.mkdir(exist_ok=True)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        
        # Sportsbook components
        self.settings = get_odds_scraper_settings()
        self.browser_engine = BrowserEngine(self.settings.browser)
        self.processor = OddsDataProcessor()
        
        # Bucket storage (lazy initialization)
        self._bucket_adapter = None
    
    @property
    def key(self) -> str:
        """
        Unique identifier for the pipeline.
        
        Used for:
            - State file naming (.pipelines/odds_scraper_nfl.json)
            - Lock file naming (.pipelines/locks/odds_scraper_nfl.lock)
            - Logging context
        
        Returns:
            str: 'odds_scraper_nfl'
        """
        return 'odds_scraper_nfl'
    
    @property
    def required_cols(self) -> List[str]:
        """
        Required columns for DataFrame validation.
        
        Validates that the processed data contains all essential fields
        before persistence.
        
        Returns:
            List[str]: Column names that must be present in the DataFrame
        """
        return [
            'event_id',
            'header',
            'date',
            'time',
            'team',
            'spread',
            'spread_odds',
            'moneyline',
            'total_over',
            'total_over_odds',
            'total_under',
            'total_under_odds',
            'bookmaker',
            'data_pull_id'
        ]
    
    @property
    def table_name(self) -> str:
        """
        Target bucket table name.
        
        Data is stored to: odds_scraper/gamelines/
        (Separate from odds_api namespace: oddsapi/*)
        
        Returns:
            str: 'gamelines'
        """
        return 'gamelines'
    
    @property
    def update_interval(self) -> int:
        """
        Minimum seconds between scrapes (cooldown period).
        
        Prevents rate limiting by enforcing a minimum interval between runs.
        Override with --force flag if needed.
        
        Returns:
            int: Seconds (default: 300 = 5 minutes)
        """
        return self.settings.update_interval
    
    @property
    def description(self) -> str:
        """
        Human-readable description for logging.
        
        Returns:
            str: Pipeline description
        """
        return "Sportsbook NFL odds scraping pipeline"
    
    @property
    def bucket_adapter(self):
        """
        Lazy-loaded bucket adapter instance.
        
        Returns:
            BucketAdapter: Configured for odds_scraper schema
        """
        if self._bucket_adapter is None:
            self._bucket_adapter = get_bucket_adapter(logger=logger)
        return self._bucket_adapter
    
    def fetch(self, **kwargs) -> pd.DataFrame:
        """
        Execute async scraping workflow and transform to DataFrame.
        
        Workflow:
            1. Run async browser scraping via _scrape_async()
            2. Transform raw AgentQL data to structured DataFrame via processor
            3. Return DataFrame for validation and persistence
        
        Args:
            **kwargs: Optional keyword arguments (currently unused)
                      - markets: List of markets (ignored - sportsbook shows all markets)
        
        Returns:
            pd.DataFrame: Processed odds data ready for validation
                          Empty DataFrame if scraping fails
        
        Raises:
            Exception: Propagates scraping or processing errors
        """
        logger.info("Starting Draft Kings NFL odds fetch")
        
        try:
            # Step 1: Run async scraping in event loop
            raw_data = asyncio.run(self._scrape_async())
            
            # Step 2: Transform to DataFrame
            df = self.processor.process(
                raw_data=raw_data,
                data_pull_id=self._generate_pull_id()
            )
            
            if df.empty:
                logger.warning("No games found in scraped data")
            else:
                logger.info(f"Successfully fetched {len(df)} team records from {len(raw_data.get('games', []))} games")
            
            return df
            
        except Exception as e:
            logger.error(f"Fetch failed: {e}", exc_info=True)
            # Return empty DataFrame to allow graceful handling
            return pd.DataFrame()
    
    async def _scrape_async(self) -> dict:
        """
        Async browser scraping logic.
        
        Uses BrowserEngine to:
            1. Launch Playwright browser with anti-detection
            2. Navigate to Sportsbook NFL page
            3. Execute AgentQL query to extract odds data
            4. Return structured dictionary
        
        Returns:
            dict: Raw scraped data with 'games' key
                  Format: {'games': [{'header': ..., 'teams': [...], ...}, ...]}
        
        Raises:
            Exception: Browser errors, navigation timeouts, AgentQL errors
        """
        async with self.browser_engine.create_context() as page:
            logger.info("Navigating to Sportsbook NFL page")
            
            # Navigate with random referer for anti-detection
            await page.goto(
                "https://sportsbook.odds_scraper.com/leagues/football/nfl"
            )
            
            # Wait for initial page load
            await page.wait_for_timeout(3000)
            
            # Scroll to load all games (handles lazy-loading)
            logger.info("Scrolling to load all games")
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)
            
            # Final wait to ensure all content is loaded
            await page.wait_for_timeout(2000)
            
            # Execute AgentQL query
            logger.debug("Executing AgentQL odds query")
            data = await page.query_data(self.settings.gameline_query)
            
            games_count = len(data.get('games', []))
            logger.info(f"Scraped {games_count} games from Sportsbook")
            
            return data
    
    def persist(self, df: pd.DataFrame, dry_run: bool = False) -> bool:
        """
        Persist DataFrame to bucket storage.
        
        Args:
            df: DataFrame to store
            dry_run: If True, skip actual storage
        
        Returns:
            bool: True if successful, False otherwise
        """
        if dry_run:
            logger.info("Dry run - skipping bucket storage")
            return True
        
        try:
            # Get timestamp from data_pull_start_time for partitioning
            timestamp = df['data_pull_start_time'].iloc[0] if not df.empty else None

            success = self.bucket_adapter.store_data(
                df=df,
                table_name=self.table_name,
                schema='odds_scraper',  # ✅ Separate namespace from oddsapi
                timestamp=timestamp,
                partition_by_year=False
            )
            
            if success:
                logger.info(f"✅ Stored to bucket: odds_scraper/{self.table_name} ({len(df):,} rows)")
            else:
                logger.warning(f"⚠️  Bucket storage failed for {self.table_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Bucket storage error: {e}", exc_info=True)
            return False
    
    def post_process(self, df: pd.DataFrame, **kwargs):
        """
        Optional post-processing after successful persistence.
        
        Args:
            df: The DataFrame that was successfully validated and persisted
            **kwargs: Optional keyword arguments
                      - write_csv (bool): Export to CSV if True
        """
        if kwargs.get('write_csv'):
            csv_path = self._export_to_csv(df)
            logger.info(f"📄 CSV exported: {csv_path}")
    
    def _export_to_csv(self, df: pd.DataFrame) -> str:
        """
        Export DataFrame to timestamped CSV file.
        
        Creates directory structure: data/odds_scraper/
        Filename format: odds_YYYYMMDD_HHMMSS.csv
        
        Args:
            df: DataFrame to export
        
        Returns:
            str: Path to exported CSV file
        
        Raises:
            OSError: If directory creation or file writing fails
        """
        export_dir = Path("data") / "odds_scraper"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = export_dir / f"odds_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        logger.debug(f"Exported {len(df)} rows to {filename}")
        
        return str(filename)
    
    def _generate_pull_id(self) -> str:
        """
        Generate unique data pull identifier.
        
        Used to track which records came from the same scraping session.
        Useful for debugging and data lineage tracking.
        
        Returns:
            str: UUID4 string
        """
        return str(uuid.uuid4())
    
    def _get_state_path(self) -> Path:
        """Get path to state file."""
        return self.state_dir / f"{self.key}.json"
    
    def _get_lock_path(self) -> Path:
        """Get path to lock file."""
        return self.lock_dir / f"{self.key}.lock"
    
    def _check_interval(self, force: bool = False) -> bool:
        """
        Check if the pipeline can run based on the update interval.
        
        Args:
            force: Bypass interval check if True
        
        Returns:
            bool: True if pipeline can run, False if cooling down
        """
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
        """
        Save the last run timestamp and status.
        
        Args:
            rows_processed: Number of rows processed in this run
        """
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
        """
        Implement PID-based file locking with stale lock detection.
        
        Returns:
            bool: True if lock acquired, False if already locked
        """
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
        """
        Orchestrate the pipeline execution.
        
        Workflow:
            1. Check cooldown interval (bypass with force=True)
            2. Acquire PID lock (prevent concurrent runs)
            3. Fetch data from Sportsbook
            4. Validate DataFrame columns
            5. Persist to bucket storage
            6. Post-process (e.g., CSV export)
            7. Save state and release lock
        
        Args:
            **kwargs: Optional keyword arguments
                      - force (bool): Bypass cooldown interval
                      - dry_run (bool): Skip bucket storage
                      - write_csv (bool): Export to CSV
        
        Returns:
            int: Number of rows processed, 0 if no data or cooldown active
        
        Raises:
            Exception: Propagates any unhandled errors after lock release
        """
        force = kwargs.get('force', False)
        dry_run = kwargs.get('dry_run', False)

        # Check cooldown interval
        if not self._check_interval(force):
            return 0

        # Acquire lock
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
            success = self.persist(df, dry_run=dry_run)
            if not success and not dry_run:
                logger.error("Persistence failed - aborting")
                return 0

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


# Expose pipeline instance for CLI / external use
__all__ = ['SportsbookPipeline']
