"""Sportsbook configuration using pydantic-settings."""
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Optional


class ProxyConfig(BaseSettings):
    """Proxy configuration with secure credential handling."""
    server: str
    username: Optional[SecretStr] = None
    password: Optional[SecretStr] = None


class LocationConfig(BaseSettings):
    """Geolocation configuration for anti-detection."""
    timezone: str = 'America/New_York'
    longitude: float = -74.0060
    latitude: float = 40.7128


class BrowserConfig(BaseSettings):
    """Browser settings for Playwright."""
    headless: bool = Field(default=True, description="Run browser headless")
    
    browser_args: List[str] = Field(
        default=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage'
        ],
        description="Chromium launch arguments"
    )
    
    browser_ignored_args: List[str] = Field(
        default=['--enable-automation'],
        description="Arguments to remove from default Chromium args"
    )
    
    user_agents: List[str] = Field(
        default=[
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ],
        description="Randomized user agents"
    )
    
    locations: List[LocationConfig] = Field(
        default_factory=lambda: [LocationConfig()],
        description="Randomized geolocations"
    )
    
    referers: List[str] = Field(
        default=['https://www.google.com/', 'https://www.bing.com/'],
        description="Randomized referers"
    )
    
    accept_languages: List[str] = Field(
        default=['en-US,en;q=0.9'],
        description="Accept-Language headers"
    )
    
    proxies: List[ProxyConfig] = Field(
        default_factory=list,
        description="Proxy configurations (optional)"
    )


class SportsbookSettings(BaseSettings):
    """Main Sportsbook scraper settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="ODDS_SCRAPER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__"
    )
    
    browser: BrowserConfig = BrowserConfig()
    
    gameline_query: str = Field(
        default='''
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
        description="AgentQL query for odds data"
    )
    
    update_interval: int = Field(
        default=300,
        description="Minimum seconds between scrapes (5 min default)"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed scrapes"
    )


# Singleton instance
_settings: Optional[SportsbookSettings] = None


def get_odds_scraper_settings() -> SportsbookSettings:
    """Get Sportsbook settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = SportsbookSettings()
    return _settings
