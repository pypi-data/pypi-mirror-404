"""
Application settings using pydantic-settings.
Centralizes environment variable handling with type safety.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List, Tuple

__all__ = ['Settings', 'BackfillSettings', 'get_settings']


class BackfillSettings(BaseSettings):
    """Historical odds backfill configuration."""
    
    # Sport & Markets
    sport_key: str = 'americanfootball_nfl'
    markets: List[str] = ['h2h', 'spreads', 'totals']
    
    # Date Range
    season_range: Tuple[int, int] = (2025, 2025)
    week_range: Tuple[int, int] = (1, 1)
    
    # Event Filtering (for testing)
    event_id_filter: Optional[str] = None
    
    # Snapshot Collection Strategy
    include_week_open_snapshot: bool = True
    include_in_game_odds: bool = True
    pregame_scheduled_minutes: int = 15  # Target minutes before kickoff (not guaranteed exact due to API granularity)
    game_duration_hours: int = 4
    max_in_game_snapshots: int = 50
    
    # Incremental Mode
    skip_existing_snapshots: bool = True
    force_refetch: bool = False
    
    # Rate Limiting
    delay_between_events: float = 0.2
    delay_between_snapshots: float = 1.0
    
    # Output Options
    max_events_per_snapshot: Optional[int] = None
    save_to_csv: bool = False
    save_to_bucket: bool = True
    bucket_schema: str = 'oddsapi'
    batch_size: int = 1000
    
    # API Quota
    enable_quota_tracking: bool = True
    daily_quota_limit: int = 10000
    quota_warn_threshold: float = 0.8
    
    model_config = {
        "env_prefix": "BACKFILL_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Odds API settings
    odds_api_key: str = ""  # Free tier API key
    paid_odds_api_key: str = ""  # Paid tier API key (for premium endpoints)
    
    # Backfill settings
    backfill: BackfillSettings = BackfillSettings()
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Allow stray env vars (like nflfastr_* variables)
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings