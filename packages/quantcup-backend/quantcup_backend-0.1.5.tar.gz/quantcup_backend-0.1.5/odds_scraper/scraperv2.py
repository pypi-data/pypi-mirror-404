"""
Generic Sportsbook Scraper v2
Supports multiple sportsbooks and market types with configurable field mapping.

This scraper is designed for testing different sportsbooks (Sportsbook, FanDuel, BetMGM, etc.)
and market types (game lines, player props, futures) without code duplication.

Usage:
    # Sportsbook game lines
    scraper = GenericScraperV2(SPORTSBOOK_NFL_GAMELINES)
    df = await scraper.scrape()
    
    # FanDuel player props  
    scraper = GenericScraperV2(FANDUEL_NFL_PROPS)
    df = await scraper.scrape()
    
    # Custom config
    config = ScraperConfigV2(
        bookmaker_name='BetMGM',
        market_type='futures',
        url='...',
        agentql_query='...',
        response_root_key='futures',
        field_mapping={'team':'team_name', 'odds':'win_odds'}
    )
    scraper = GenericScraperV2(config)
    df = await scraper.scrape()
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
import uuid
import os
import random
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
import agentql
import pandas as pd
from playwright.async_api import async_playwright, Geolocation, ProxySettings

from commonv2 import get_logger
from commonv2.persistence.bucket_adapter import get_bucket_adapter


class ScraperConfigV2:
    """
    Configuration for a specific sportsbook + market combination.
    
    This class defines what to scrape and how to process it:
    - Where to navigate (url)
    - What data to extract (agentql_query)
    - How to structure the response (field_mapping)
    - How to process individual records (processor_fn)
    
    Attributes:
        bookmaker_name: Sportsbook identifier (e.g., 'Sportsbook', 'FanDuel')
        market_type: Market category (e.g., 'gamelines', 'props', 'futures')
        url: Full URL to scrape
        agentql_query: AgentQL query string for data extraction
        response_root_key: Top-level key in AgentQL response (e.g., 'games', 'props')
        field_mapping: Dict mapping AgentQL fields to output column names
        processor_fn: Optional custom function to process each record
    """
    
    def __init__(
        self,
        bookmaker_name: str,
        market_type: str,
        url: str,
        agentql_query: str,
        response_root_key: str,
        field_mapping: Dict[str, str],
        processor_fn: Optional[Callable[[Dict], Union[Dict[str, Any], List[Dict[str, Any]]]]] = None
    ):
        self.bookmaker_name = bookmaker_name
        self.market_type = market_type
        self.url = url
        self.agentql_query = agentql_query
        self.response_root_key = response_root_key
        self.field_mapping = field_mapping
        self.processor_fn = processor_fn or self._default_processor
    
    def _default_processor(self, raw_item: Dict) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Default processor: Simple field mapping with no transformations.
        
        For simple cases where you just need to rename fields, this is sufficient.
        For complex logic (nested data, calculations, odds conversion), provide
        a custom processor_fn when creating the config.
        
        Args:
            raw_item: Raw record from AgentQL response
            
        Returns:
            Dict with mapped field names
        """
        processed = {}
        for source_field, target_field in self.field_mapping.items():
            # Handle nested fields with dot notation (e.g., 'team.name')
            if '.' in source_field:
                keys = source_field.split('.')
                value = raw_item
                for key in keys:
                    value = value.get(key, {}) if isinstance(value, dict) else None
                    if value is None:
                        break
                processed[target_field] = value
            else:
                processed[target_field] = raw_item.get(source_field)
        
        return processed


class GenericScraperV2:
    """
    Generic sportsbook scraper supporting any bookmaker + market type.
    
    This scraper handles:
    - Browser automation with Playwright + AgentQL
    - Anti-detection (stealth mode, random user agents)
    - Data extraction via configurable AgentQL queries
    - Flexible data processing via field mapping
    - Bucket storage integration
    - CSV export
    
    The scraper is stateless - all configuration comes from ScraperConfigV2.
    This allows easy testing of different sportsbooks/markets without code changes.
    """
    
    def __init__(self, config: ScraperConfigV2):
        """
        Initialize scraper with specific configuration.
        
        Args:
            config: ScraperConfigV2 instance defining what/how to scrape
        """
        load_dotenv()
        
        self.config = config
        self.logger = self._setup_logging()
        self.data_pull_id = str(uuid.uuid4())
        
        # Bucket storage (lazy initialization)
        self._bucket_adapter = None
        
        # Validate AgentQL API key
        self._validate_agentql_key()
    
    @property
    def bucket_adapter(self):
        """Lazy-loaded bucket adapter instance."""
        if self._bucket_adapter is None:
            self._bucket_adapter = get_bucket_adapter(logger=self.logger)
        return self._bucket_adapter
    
    def _validate_agentql_key(self):
        """Validate that AgentQL API key is set."""
        api_key = os.getenv('AGENTQL_API_KEY')
        if not api_key or api_key == 'your_agentql_api_key_here':
            self.logger.error("AgentQL API key is not set. Please set AGENTQL_API_KEY in your .env file.")
            self.logger.error("You can get a free key at https://dev.agentql.com")
        else:
            self.logger.info("AgentQL API key found and validated")
    
    def _setup_logging(self):
        """Set up logging configuration using centralized logger."""
        logger_name = f"{__name__}.{self.config.bookmaker_name}.{self.config.market_type}"
        return get_logger(logger_name)
    
    async def scrape(self, max_retries: int = 3) -> Optional[pd.DataFrame]:
        """
        Main scraping entry point with retry logic.
        
        Workflow:
            1. Launch browser with anti-detection
            2. Navigate to configured URL
            3. Execute AgentQL query
            4. Process response to DataFrame
            5. Return results
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            DataFrame with scraped data, or None if all retries failed
        """
        self.logger.info(
            f"Starting {self.config.bookmaker_name} - {self.config.market_type} scrape"
        )
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Scraping attempt {attempt + 1}/{max_retries}")
                
                async with self._create_browser_context() as page:
                    # Navigate to target page
                    self.logger.info(f"Navigating to {self.config.url}")
                    await page.goto(self.config.url)
                    await page.wait_for_page_ready_state()
                    await page.wait_for_timeout(3000)  # Initial page load
                    
                    # Scroll to load all content (handles lazy-loading)
                    self.logger.info("Scrolling to load dynamic content")
                    for i in range(3):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1500)
                    
                    # Final wait
                    await page.wait_for_timeout(2000)
                    
                    # Execute AgentQL query
                    start_time = datetime.now().isoformat()
                    self.logger.debug(f"Executing AgentQL query: {self.config.agentql_query[:100]}...")
                    raw_data = await page.query_data(self.config.agentql_query)
                    end_time = datetime.now().isoformat()
                    
                    if not raw_data:
                        self.logger.warning(f"No data returned on attempt {attempt + 1}")
                        continue
                    
                    # Process response to DataFrame
                    df = self._process_response(raw_data, start_time, end_time)
                    
                    if df is not None and not df.empty:
                        self.logger.info(f"Successfully scraped {len(df)} records")
                        return df
                    else:
                        self.logger.warning(f"Data processing failed on attempt {attempt + 1}")
                
            except Exception as e:
                self.logger.error(f"Scraping attempt {attempt + 1} failed: {e}", exc_info=True)
                if attempt == max_retries - 1:
                    self.logger.error("All scraping attempts failed")
                    return None
                
                # Wait before retry
                await asyncio.sleep(random.uniform(2, 5))
        
        return None
    
    @asynccontextmanager
    async def _create_browser_context(self):
        """
        Create and manage browser context for scraping.
        
        Features:
        - Random user agent
        - Stealth mode (via AgentQL)
        - Random viewport size
        - Anti-detection headers
        
        Yields:
            AgentQL-wrapped Playwright page
        """
        browser = None
        context = None
        
        try:
            async with async_playwright() as playwright:
                # Launch browser
                browser = await playwright.chromium.launch(
                    headless=False,  # Set to False for debugging
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage'
                    ],
                    ignore_default_args=['--enable-automation']
                )
                
                # Random user agent for anti-detection
                user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                
                # Create context with anti-detection
                context = await browser.new_context(
                    locale="en-US,en,ru",
                    timezone_id="America/New_York",
                    extra_http_headers={
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": "https://www.google.com/",
                        "DNT": random.choice(["0", "1"]),
                        "Connection": "keep-alive",
                        "Accept-Encoding": "gzip, deflate, br",
                    },
                    geolocation=Geolocation(longitude=-74.0060, latitude=40.7128),
                    user_agent=user_agent,
                    permissions=["notifications"],
                    viewport={
                        "width": 1920 + random.randint(-50, 50),
                        "height": 1080 + random.randint(-50, 50),
                    },
                )
                
                # Create page with AgentQL
                page = await agentql.wrap_async(context.new_page())
                await page.enable_stealth_mode(nav_user_agent=user_agent)
                
                self.logger.debug(f"Browser context created with UA: {user_agent[:50]}...")
                yield page
                
        except Exception as e:
            self.logger.error(f"Browser context error: {e}", exc_info=True)
            raise
        finally:
            # Cleanup
            try:
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except Exception as e:
                self.logger.debug(f"Browser cleanup notice: {e}")
    
    def _process_response(
        self, 
        raw_data: Dict, 
        start_time: str, 
        end_time: str
    ) -> Optional[pd.DataFrame]:
        """
        Process raw AgentQL response to DataFrame using config's field mapping.
        
        This is the key method that makes v2 flexible - it uses the config's
        field_mapping and processor_fn instead of hardcoded schema.
        
        Args:
            raw_data: Raw dictionary from AgentQL query
            start_time: ISO timestamp when scraping started
            end_time: ISO timestamp when scraping ended
            
        Returns:
            Processed DataFrame or None if processing failed
        """
        try:
            # Extract items using configured root key
            items = raw_data.get(self.config.response_root_key, [])
            
            if not items:
                self.logger.warning(
                    f"No {self.config.response_root_key} found in response. "
                    f"Available keys: {list(raw_data.keys())}"
                )
                return None
            
            self.logger.info(f"Processing {len(items)} {self.config.response_root_key} items")
            
            rows = []
            for item in items:
                # Use config's processor function
                # This allows market-specific logic (e.g., props need team expansion)
                processed = self.config.processor_fn(item)
                
                # Handle processors that return list of dicts (e.g., team expansion)
                items_to_add = processed if isinstance(processed, list) else [processed]
                
                # Add standard metadata to each processed item
                for processed_item in items_to_add:
                    processed_item['bookmaker'] = self.config.bookmaker_name
                    processed_item['market_type'] = self.config.market_type
                    processed_item['data_pull_id'] = self.data_pull_id
                    processed_item['data_pull_start_time'] = start_time
                    processed_item['data_pull_end_time'] = end_time
                    
                    rows.append(processed_item)
            
            if not rows:
                self.logger.warning("No valid records after processing")
                return None
            
            # Create DataFrame
            df = pd.DataFrame(rows)
            
            # Auto-detect and convert numeric columns
            self._convert_numeric_columns(df)
            
            self.logger.info(
                f"Successfully processed {len(df)} {self.config.market_type} records "
                f"with {len(df.columns)} columns"
            )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Response processing error: {e}", exc_info=True)
            return None
    
    def _convert_numeric_columns(self, df: pd.DataFrame):
        """
        Auto-detect and convert numeric columns.
        
        Looks for common odds/line field patterns and converts them to numeric.
        Logs warnings if conversion fails.
        """
        # Common numeric field patterns
        numeric_patterns = ['odds', 'line', 'price', 'spread', 'total', 'over', 'under']
        
        for col in df.columns:
            # Check if column name contains numeric pattern
            if any(pattern in col.lower() for pattern in numeric_patterns):
                before_nulls = df[col].isnull().sum()
                df[col] = pd.to_numeric(df[col], errors='coerce')
                after_nulls = df[col].isnull().sum()
                
                if after_nulls > before_nulls:
                    failed = after_nulls - before_nulls
                    self.logger.warning(
                        f"Column '{col}': {failed} values failed numeric conversion"
                    )
    
    def save_to_csv(self, df: pd.DataFrame, export_dir: Optional[str] = None) -> Optional[Path]:
        """
        Save DataFrame to CSV file.
        
        Args:
            df: DataFrame to export
            export_dir: Optional directory path (default: data/{bookmaker}/)
            
        Returns:
            Path to saved CSV file, or None if failed
        """
        try:
            if export_dir:
                export_path = Path(export_dir)
            else:
                export_path = Path("data") / self.config.bookmaker_name.lower() / self.config.market_type
            
            export_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_path / f"{self.config.bookmaker_name}_{self.config.market_type}_{timestamp}.csv"
            
            df.to_csv(filename, index=False)
            self.logger.info(f"Data saved to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"CSV save error: {e}", exc_info=True)
            return None
    
    def save_to_bucket(
        self, 
        df: pd.DataFrame, 
        table_name: Optional[str] = None,
        schema: Optional[str] = None
    ) -> bool:
        """
        Save DataFrame to bucket storage.
        
        Args:
            df: DataFrame to save
            table_name: Optional table name (default: {market_type}_data)
            schema: Optional schema/namespace (default: bookmaker name)
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Default table name and schema from config
            table_name = table_name or f"{self.config.market_type}_data"
            schema = schema or self.config.bookmaker_name.lower()
            
            # Get timestamp from data_pull_start_time for partitioning
            timestamp = df['data_pull_start_time'].iloc[0] if not df.empty else None
            
            # Store in bucket
            success = self.bucket_adapter.store_data(
                df=df,
                table_name=table_name,
                schema=schema,
                timestamp=timestamp,
                partition_by_year=False
            )
            
            if success:
                self.logger.info(
                    f"Successfully saved {len(df)} records to bucket: {schema}/{table_name}"
                )
            else:
                self.logger.warning(f"Failed to save data to bucket: {schema}/{table_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Bucket save error: {e}", exc_info=True)
            return False


# ============================================================================
# MARKET CONFIGURATIONS
# Define different sportsbook + market combinations here
# ============================================================================

def _process_odds_scraper_gamelines(raw_item: Dict) -> List[Dict[str, Any]]:
    """
    Custom processor for Sportsbook game lines.
    
    Expands teams array into separate records (one per team).
    Returns a list of dicts (one per team) instead of single dict.
    """
    rows = []
    teams = raw_item.get('teams', [])
    
    for team in teams:
        row = {
            'game_header': raw_item.get('header', ''),
            'game_date': raw_item.get('date', ''),
            'game_time': raw_item.get('time', ''),
            'team_name': team.get('name', ''),
            'spread': team.get('spread', ''),
            'spread_odds': team.get('spread_odds', ''),
            'moneyline': team.get('moneyline', ''),
            'total_over': raw_item.get('total_over', ''),
            'total_over_odds': raw_item.get('total_over_odds', ''),
            'total_under': raw_item.get('total_under', ''),
            'total_under_odds': raw_item.get('total_under_odds', ''),
            'event_url': raw_item.get('event_url', '')
        }
        rows.append(row)
    
    return rows


# Sportsbook NFL Game Lines
SPORTSBOOK_NFL_GAMELINES = ScraperConfigV2(
    bookmaker_name='Sportsbook',
    market_type='gamelines',
    url='https://sportsbook.odds_scraper.com/leagues/football/nfl',
    response_root_key='games',
    agentql_query='''
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
    ''',
    field_mapping={
        'header': 'game_header',
        'date': 'game_date',
        'time': 'game_time',
        'teams': 'teams_data',
        'event_url': 'event_url'
    },
    processor_fn=_process_odds_scraper_gamelines
)

# Sportsbook NFL Player Props
SPORTSBOOK_NFL_PROPS = ScraperConfigV2(
    bookmaker_name='Sportsbook',
    market_type='player_props',
    url='https://sportsbook.odds_scraper.com/leagues/football/nfl?category=player-props',
    response_root_key='props',
    agentql_query='''
    {
        props[] {
            player_name
            prop_type
            line
            over_odds
            under_odds
            game_info
        }
    }
    ''',
    field_mapping={
        'player_name': 'player',
        'prop_type': 'market',
        'line': 'line_value',
        'over_odds': 'over',
        'under_odds': 'under',
        'game_info': 'game'
    }
)

# FanDuel NFL Game Lines
FANDUEL_NFL_GAMELINES = ScraperConfigV2(
    bookmaker_name='FanDuel',
    market_type='gamelines',
    url='https://sportsbook.fanduel.com/navigation/nfl',
    response_root_key='events',
    agentql_query='''
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
    ''',
    field_mapping={
        'header': 'game_header',
        'date': 'game_date',
        'time': 'game_time',
        'teams': 'teams_data',
        'event_url': 'event_url'
    },
    processor_fn=_process_odds_scraper_gamelines
)

# BetMGM NFL Game Lines
BETMGM_NFL_GAMELINES = ScraperConfigV2(
    bookmaker_name='BetMGM',
    market_type='gamelines',
    url='https://sports.betmgm.com/en/sports/football-11/betting/usa-9/nfl-35',
    response_root_key='games',
    agentql_query='''
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
    ''',
    field_mapping={
        'header': 'game_header',
        'date': 'game_date',
        'time': 'game_time',
        'teams': 'teams_data',
        'event_url': 'event_url'
    },
    processor_fn=_process_odds_scraper_gamelines
)


# ============================================================================
# TESTING / CLI ENTRY POINT
# ============================================================================

async def test_scraper(config: ScraperConfigV2, write_csv: bool = False):
    """
    Test scraper with specific configuration.
    
    Args:
        config: ScraperConfigV2 instance
        write_csv: If True, save results to CSV
    """
    print(f"\n{'='*70}")
    print(f"Testing: {config.bookmaker_name} - {config.market_type}")
    print(f"URL: {config.url}")
    print(f"{'='*70}\n")
    
    scraper = GenericScraperV2(config)
    df = await scraper.scrape()
    
    if df is not None:
        print(f"\n✅ Success! Scraped {len(df)} records")
        print(f"\nColumns: {list(df.columns)}")
        print(f"\nSample data (first 3 rows):")
        print(df.head(3).to_string())
        print(f"\nDataFrame shape: {df.shape}")
        
        if write_csv:
            csv_path = scraper.save_to_csv(df)
            print(f"\n📄 CSV exported to: {csv_path}")
        
        return df
    else:
        print(f"\n❌ Failed to scrape data")
        return None


async def main():
    """Test scraper with different configurations."""
    
    # Test 1: Sportsbook game lines
    df_dk = await test_scraper(SPORTSBOOK_NFL_GAMELINES, write_csv=True)

    # Uncomment to test other markets:
    # df_props = await test_scraper(SPORTSBOOK_NFL_PROPS, write_csv=True)
    # df_fd = await test_scraper(FANDUEL_NFL_GAMELINES, write_csv=True)
    # df_mgm = await test_scraper(BETMGM_NFL_GAMELINES, write_csv=True)


if __name__ == "__main__":
    asyncio.run(main())
