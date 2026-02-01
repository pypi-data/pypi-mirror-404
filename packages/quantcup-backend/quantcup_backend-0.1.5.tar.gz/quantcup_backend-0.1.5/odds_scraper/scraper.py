"""
Sportsbook Scraper for QuantCup Data Sources

⚠️ DEPRECATED - This module is deprecated and will be archived after validation period.

Please use the new clean architecture implementation:
    - CLI: `quantcup odds_scraper scrape-nfl`
    - Python API: `from odds_scraper.pipeline import SportsbookPipeline`

For migration guide, see: odds_scraper/README.md
For architecture details, see: odds_scraper/docs/REFACTORING_PLAN.md

Legacy module retained for backward compatibility only.
Original file: sports-books/Dev_DKScraper_PRD.py
"""

import warnings

# Issue deprecation warning when module is imported
warnings.warn(
    "odds_scraper.scraper is deprecated. Use 'odds_scraper.pipeline.SportsbookPipeline' "
    "or the CLI 'quantcup odds_scraper scrape-nfl' instead. "
    "See odds_scraper/README.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

import asyncio
import logging
from logging.handlers import RotatingFileHandler
import random
from datetime import datetime, timedelta
import re
import uuid
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
import agentql
import pandas as pd
import yaml
from playwright.async_api import Geolocation, ProxySettings, async_playwright
import pytz

from commonv2.persistence.bucket_adapter import BucketAdapter, get_bucket_adapter

class SportsbookScraper:
    """
    ⚠️ DEPRECATED - Sportsbook NFL odds scraper with bucket storage integration.
    
    This class is deprecated. Please use odds_scraper.pipeline.SportsbookPipeline instead.
    
    Migration:
        OLD: scraper = SportsbookScraper()
        NEW: pipeline = SportsbookPipeline()
        
        OLD: df = await scraper.scrape_nfl_odds()
        NEW: rows = pipeline.run()
    
    For full migration guide, see: odds_scraper/README.md
    
    Legacy Features:
    - Async web scraping with Playwright and AgentQL
    - Configurable browser settings and proxies
    - Data validation and processing
    - S3/Sevalla bucket storage integration
    - Comprehensive logging and error handling
    """
    
    def __init__(self, config_path: Optional[str] = None, bucket_adapter: Optional[BucketAdapter] = None):
        """
        Initialize the Sportsbook scraper.
        
        Args:
            config_path: Optional path to configuration file
            bucket_adapter: Optional BucketAdapter instance for storage
        """
        # Load environment variables
        load_dotenv()
        
        self.config = self._load_configurations(config_path)
        self.logger = self._setup_logging()
        self.data_pull_id = str(uuid.uuid4())
        
        # Initialize bucket adapter for storage
        self.bucket_adapter = bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        # Initialize scraping parameters
        self._setup_scraping_params()
        
        # Validate AgentQL API Key
        self._validate_agentql_key()
        
    def _validate_agentql_key(self):
        """Validate that AgentQL API key is set."""
        api_key = os.getenv('AGENTQL_API_KEY')
        if not api_key or api_key == 'your_agentql_api_key_here':
            self.logger.error("AgentQL API key is not set. Please set AGENTQL_API_KEY in your .env file.")
            self.logger.error("You can get a free key at https://dev.agentql.com")
            # We don't raise an exception here to allow the class to be instantiated,
            # but scraping will likely fail later.
        else:
            self.logger.info("AgentQL API key found and validated")

    def _load_configurations(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load and validate configurations from config files and environment."""
        
        # Try to load from legacy config.yaml if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as file:
                config = yaml.safe_load(file)
                return config.get('scraper', {})
        
        # Check for config.yaml in current directory
        config_file = "config.yaml"
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                config = yaml.safe_load(file)
                if config and 'scraper' in config:
                    return config['scraper']
        
        # Default configuration
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Sportsbook scraper."""
        return {
            'browser_args': [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ],
            'browser_ignored_args': ['--enable-automation'],
            'user_agents': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ],
            'locations': [
                {
                    'timezone': 'America/New_York',
                    'longitude': -74.0060,
                    'latitude': 40.7128
                }
            ],
            'referers': ['https://www.google.com/'],
            'accept_languages': ['en-US,en;q=0.9'],
            'proxies': [],
            'gameline_query': '''
            {
                games[] {
                    header
                    date
                    time
                    teams[] {
                        name
                        spread
                        spread_odds
                        moneyline
                    }
                    total_over
                    total_over_odds
                    total_under
                    total_under_odds
                    event_url
                }
            }
            '''
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if not logger.handlers:
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_file = Path("logs") / "odds_scraper_scraper.log"
            log_file.parent.mkdir(exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5*1024*1024, backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _setup_scraping_params(self):
        """Set up randomized scraping parameters."""
        # Randomly select configurations for this session
        self.user_agent = random.choice(self.config.get('user_agents', ['Mozilla/5.0']))
        self.header_dnt = random.choice(["0", "1"])
        
        # Location setup
        locations = self.config.get('locations', [])
        if locations:
            location_config = random.choice(locations)
            self.location = (
                location_config.get('timezone', 'America/New_York'),
                Geolocation(
                    longitude=location_config.get('longitude', -74.0060),
                    latitude=location_config.get('latitude', 40.7128)
                )
            )
        else:
            self.location = ('America/New_York', Geolocation(longitude=-74.0060, latitude=40.7128))
        
        self.referer = random.choice(self.config.get('referers', ['https://www.google.com/']))
        self.accept_language = random.choice(self.config.get('accept_languages', ['en-US,en;q=0.9']))
        
        # Proxy setup
        proxies = self.config.get('proxies', [])
        if proxies:
            proxy_config = random.choice(proxies)
            self.proxy = ProxySettings(
                server=proxy_config.get('server'),
                username=proxy_config.get('username'),
                password=proxy_config.get('password')
            )
        else:
            self.proxy = None
    
    async def scrape_nfl_odds(self, max_retries: int = 3) -> Optional[pd.DataFrame]:
        """
        Scrape NFL odds from Sportsbook with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            DataFrame with scraped odds data or None if failed
        """
        self.logger.info(f"Starting Sportsbook NFL odds scraping")
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Scraping attempt {attempt + 1}/{max_retries}")
                
                async with self._create_browser_context() as page:
                    # Navigate to Sportsbook NFL page
                    self.logger.info("Navigating to Sportsbook NFL page")
                    await page.goto(
                        "https://sportsbook.odds_scraper.com/leagues/football/nfl"
                    )
                    await page.wait_for_timeout(3000)  # Wait for initial page load
                    
                    # Scroll to load all games (handles lazy-loading)
                    self.logger.info("Scrolling to load all games")
                    for i in range(3):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1500)
                    
                    # Final wait to ensure all content is loaded
                    await page.wait_for_timeout(2000)
                    
                    # Scrape data
                    start_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    data = await self._query_odds_data(page)
                    end_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    
                    if not data:
                        self.logger.warning(f"No data returned on attempt {attempt + 1}")
                        continue
                    
                    # Process and validate data
                    df = self._process_odds_data(data, start_time, end_time)
                    
                    if df is not None and not df.empty:
                        self.logger.info(f"Successfully scraped {len(df)} records")
                        return df
                    else:
                        self.logger.warning(f"Data processing failed on attempt {attempt + 1}")
                        
            except Exception as e:
                self.logger.error(f"Scraping attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    self.logger.error("All scraping attempts failed")
                    return None
                
                # Wait before retry
                await asyncio.sleep(random.uniform(2, 5))
        
        return None
    
    @asynccontextmanager
    async def _create_browser_context(self):
        """Create and manage browser context for scraping."""
        browser = None
        context = None
        
        try:
            async with async_playwright() as playwright:
                # Launch browser
                browser = await playwright.chromium.launch(
                    headless=True,  # Set to False for debugging
                    args=self.config.get('browser_args', []),
                    ignore_default_args=self.config.get('browser_ignored_args', [])
                )
                
                # Create context
                context = await browser.new_context(
                    proxy=self.proxy,
                    locale="en-US,en,ru",
                    timezone_id=self.location[0],
                    extra_http_headers={
                        "Accept-Language": self.accept_language,
                        "Referer": self.referer,
                        "DNT": self.header_dnt,
                        "Connection": "keep-alive",
                        "Accept-Encoding": "gzip, deflate, br",
                    },
                    geolocation=self.location[1],
                    user_agent=self.user_agent,
                    permissions=["notifications"],
                    viewport={
                        "width": 1920 + random.randint(-50, 50),
                        "height": 1080 + random.randint(-50, 50),
                    },
                )
                
                # Create page with AgentQL
                page = await agentql.wrap_async(context.new_page())
                await page.enable_stealth_mode(nav_user_agent=self.user_agent)
                
                yield page
                
        except Exception as e:
            self.logger.error(f"Browser context error: {e}")
            raise
        finally:
            # Playwright's 'async with' block handles cleanup of browser and context.
            # Explicitly closing here can cause "Target closed" errors if the block has already exited.
            try:
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except Exception as e:
                # Ignore errors during cleanup as the 'async with' block will handle it
                self.logger.debug(f"Browser cleanup notice (safe to ignore): {e}")
    
    async def _query_odds_data(self, page) -> Optional[Dict]:
        """Query odds data from the page using AgentQL."""
        try:
            query = self.config.get('gameline_query', '{}')
            self.logger.debug("Executing AgentQL query")
            data = await page.query_data(query)
            self.logger.debug(f"Query returned: {len(data.get('games', []))} games")
            return data
        except Exception as e:
            self.logger.error(f"AgentQL query failed: {e}")
            return None
    
    def _process_odds_data(self, data: Dict, start_time: str, end_time: str) -> Optional[pd.DataFrame]:
        """Process raw odds data into structured DataFrame."""
        try:
            games = data.get("games", [])
            if not games:
                self.logger.warning("No games found in scraped data")
                return None
            
            rows = []
            
            for game in games:
                header = game.get('header', '')
                date_str = game.get("date", "")
                time_str = game.get("time", "")
                
                # Parse and convert date/time
                standardized_date = self._parse_date_string(date_str)
                if standardized_date:
                    converted = self._convert_time_to_eastern(standardized_date, time_str)
                    if converted:
                        date_converted, time_converted = converted
                    else:
                        date_converted, time_converted = date_str, time_str
                else:
                    date_converted, time_converted = date_str, time_str
                
                # Process teams
                teams = game.get("teams", [])
                for team in teams:
                    team_name = team.get("name", "")
                    if not team_name:
                        continue
                    
                    row = {
                        "Event ID": self._extract_event_id(game.get("event_url", "")),
                        "Header": header,
                        "Date": date_converted,
                        "Time (EST)": time_converted,
                        "Team": team_name,
                        "Spread": team.get("spread", ""),
                        "Spread Odds": team.get("spread_odds", ""),
                        "Moneyline": team.get("moneyline", ""),
                        "Total Over": game.get("total_over", ""),
                        "Total Over Odds": game.get("total_over_odds", ""),
                        "Total Under": game.get("total_under", ""),
                        "Total Under Odds": game.get("total_under_odds", ""),
                        "Event URL": game.get("event_url", ""),
                        "Bookmaker": "Sportsbook",
                        "Odds Format": "American",
                        "Data Pull Start Time": start_time,
                        "Data Pull End Time": end_time,
                        "Data Pull ID": self.data_pull_id,
                    }
                    rows.append(row)
            
            if not rows:
                self.logger.warning("No valid team data found")
                return None
            
            # Create DataFrame
            df = pd.DataFrame(rows)
            
            # Convert numeric columns
            numeric_columns = [
                "Spread", "Spread Odds", "Moneyline", 
                "Total Over", "Total Over Odds", "Total Under", "Total Under Odds"
            ]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Validate data
            if self._validate_dataframe(df):
                return df
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Data processing error: {e}")
            return None
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse various date string formats to standardized YYYY-MM-DD."""
        if not date_str:
            return None
        
        date_str_clean = date_str.strip()
        
        # Handle relative dates
        relative_days = {'TODAY': 0, 'TOMORROW': 1, 'YESTERDAY': -1}
        if date_str_clean.upper() in relative_days:
            target_date = datetime.now() + timedelta(days=relative_days[date_str_clean.upper()])
            return target_date.strftime('%Y-%m-%d')
        
        # Remove ordinal suffixes (1st, 2nd, 3rd, 4th...)
        clean_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str_clean, flags=re.IGNORECASE)
        
        # Remove time if present (e.g., "Mon Dec 29 8:15 PM" -> "Mon Dec 29")
        clean_str = re.sub(r'\s+\d{1,2}:\d{2}\s*(?:AM|PM).*$', '', clean_str, flags=re.IGNORECASE)
        
        # Try common formats first for speed and precision
        formats = [
            '%Y-%m-%d',       # 2025-12-27
            '%a %b %d',       # FRI NOV 15
            '%b %d, %Y',      # December 27, 2025
            '%m/%d/%Y',       # 12/27/2025
            '%d/%m/%Y',       # 27/12/2025
            '%Y/%m/%d',       # 2025/12/27
            '%b %d'           # NOV 15
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_str, fmt)
                if dt.year == 1900:  # If year was not in format
                    current_date = datetime.now()
                    dt = dt.replace(year=current_date.year)
                    # If the parsed date is more than 6 months in the past, it's likely next year
                    if (current_date - dt).days > 180:
                        dt = dt.replace(year=current_date.year + 1)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Fallback to pandas for more complex formats
        try:
            dt = pd.to_datetime(clean_str)
            if dt.year == 1900:
                current_date = datetime.now()
                dt = dt.replace(year=current_date.year)
                # If the parsed date is more than 6 months in the past, it's likely next year
                if (current_date - dt).days > 180:
                    dt = dt.replace(year=current_date.year + 1)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
            
        self.logger.warning(f"Unable to parse date string: '{date_str}'")
        return None
    
    def _convert_time_to_eastern(self, date_str: str, time_str: str) -> Optional[tuple]:
        """Convert time to Eastern timezone."""
        if not date_str or not time_str:
            return None
        
        try:
            # Clean time string: remove spaces and ensure uppercase AM/PM
            time_str_clean = time_str.strip().upper().replace(" ", "")
            
            # Handle cases where minutes might be missing (e.g., "4 PM" -> "4:00PM")
            if ":" not in time_str_clean:
                time_str_clean = re.sub(r'(\d+)(AM|PM)', r'\1:00\2', time_str_clean)
                
            # Ensure 2-digit hour for %I (e.g., "4:30PM" -> "04:30PM")
            if re.match(r'^\d:', time_str_clean):
                time_str_clean = "0" + time_str_clean
                
            datetime_str = f"{date_str} {time_str_clean}"
            
            # Try to parse the cleaned datetime string
            try:
                naive_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M%p")
            except ValueError:
                # Fallback to pandas if strptime fails
                naive_datetime = pd.to_datetime(datetime_str).to_pydatetime()
            
            # Assume GMT and convert to Eastern
            gmt_timezone = pytz.timezone('GMT')
            gmt_datetime = gmt_timezone.localize(naive_datetime)
            eastern_timezone = pytz.timezone('America/New_York')
            eastern_datetime = gmt_datetime.astimezone(eastern_timezone)
            
            converted_date = eastern_datetime.strftime("%m/%d/%Y")
            converted_time = eastern_datetime.strftime("%I:%M%p")
            
            return converted_date, converted_time
        except Exception as e:
            self.logger.error(f"Time conversion error: {e} (date: {date_str}, time: {time_str})")
            return None
    
    def _extract_event_id(self, event_url: str) -> Optional[int]:
        """Extract event ID from URL."""
        if not event_url:
            return None
        
        match = re.search(r'/([^/]+)$', event_url)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
    
    def _validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Validate the processed DataFrame."""
        try:
            required_columns = [
                "Event ID", "Header", "Date", "Time (EST)", "Team",
                "Spread", "Spread Odds", "Moneyline", "Total Over",
                "Total Over Odds", "Total Under", "Total Under Odds",
                "Event URL", "Bookmaker", "Odds Format",
                "Data Pull Start Time", "Data Pull End Time", "Data Pull ID"
            ]
            
            # Check for required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            # Check for empty DataFrame
            if df.empty:
                self.logger.error("DataFrame is empty")
                return False
            
            # Basic data validation
            if df['Team'].isnull().all():
                self.logger.error("No valid team names found")
                return False
            
            self.logger.info("Data validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False
    
    def save_to_csv(self, df: pd.DataFrame, export_dir: Optional[str] = None) -> Optional[Path]:
        """Save DataFrame to CSV file."""
        try:
            if export_dir:
                export_path = Path(export_dir)
            else:
                export_path = Path.cwd() / "data"
            
            export_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_path / f"odds_scraper_odds_{timestamp}.csv"
            
            df.to_csv(filename, index=False)
            self.logger.info(f"Data saved to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"CSV save error: {e}")
            return None
    
    def save_to_bucket(self, df: pd.DataFrame, table_name: str = "gamelines",
                       schema: str = "odds_scraper") -> bool:
        """
        Save DataFrame to bucket storage.
        
        Args:
            df: DataFrame to save
            table_name: Name of the table/dataset
            schema: Schema/namespace for organization (default: 'odds_scraper')
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Prepare DataFrame for storage
            df_storage = df.copy()
            
            # Rename columns to snake_case for consistency
            column_mapping = {
                'Event ID': 'event_id',
                'Header': 'header',
                'Date': 'date',
                'Time (EST)': 'time',
                'Team': 'team',
                'Spread': 'spread',
                'Spread Odds': 'spread_odds',
                'Moneyline': 'moneyline',
                'Total Over': 'total_over',
                'Total Over Odds': 'total_over_odds',
                'Total Under': 'total_under',
                'Total Under Odds': 'total_under_odds',
                'Event URL': 'event_url',
                'Bookmaker': 'bookmaker',
                'Odds Format': 'odds_format',
                'Data Pull Start Time': 'data_pull_start_time',
                'Data Pull End Time': 'data_pull_end_time',
                'Data Pull ID': 'data_pull_id'
            }
            df_storage.rename(columns=column_mapping, inplace=True)
            
            # Get timestamp from data_pull_start_time for partitioning
            timestamp = df_storage['data_pull_start_time'].iloc[0] if not df_storage.empty else None
            
            # Store in bucket with timestamp partitioning
            success = self.bucket_adapter.store_data(
                df=df_storage,
                table_name=table_name,
                schema=schema,
                timestamp=timestamp
            )
            
            if success:
                self.logger.info(f"Successfully saved {len(df_storage)} records to bucket: {schema}/{table_name}")
            else:
                self.logger.warning(f"Failed to save data to bucket: {schema}/{table_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Bucket save error: {e}")
            return False

# Convenience functions for backward compatibility
async def scrape_odds_scraper_odds(config_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Convenience function to scrape Sportsbook odds.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        DataFrame with odds data or None if failed
    """
    scraper = SportsbookScraper(config_path)
    return await scraper.scrape_nfl_odds()

def test_odds_scraper_scraper():
    """Test the Sportsbook scraper."""
    async def run_test():
        scraper = SportsbookScraper()
        df = await scraper.scrape_nfl_odds()
        
        if df is not None:
            print(f"Successfully scraped {len(df)} records")
            print("\nSample data:")
            print(df.head())
            
            # Save to CSV (local backup)
            csv_file = scraper.save_to_csv(df)
            if csv_file:
                print(f"Data saved to CSV: {csv_file}")
            
            # Save to bucket storage
            success = scraper.save_to_bucket(df)
            if success:
                print("Data saved to bucket storage")
            else:
                print("Warning: Bucket storage failed or not configured")
        else:
            print("Scraping failed")
    
    asyncio.run(run_test())

if __name__ == "__main__":
    test_odds_scraper_scraper()
