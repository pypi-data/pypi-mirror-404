"""
Centralized API quota tracking and management.

This module provides a singleton QuotaTracker that monitors API usage
across all scripts to prevent quota overages and provide visibility
into API consumption patterns.

Usage:
    from odds_api.core.quota_tracker import QuotaTracker, QuotaExceededException
    
    tracker = QuotaTracker.get_instance()
    tracker.update_usage(key_id='paid', used=100, remaining=9900)
    tracker.check_quota_available(key_id='paid')
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .types import QuotaCost

from commonv2 import get_logger

logger = get_logger(__name__)

__all__ = ['QuotaTracker', 'QuotaExceededException', 'setup_quota_tracker']


class QuotaExceededException(Exception):
    """Raised when API quota is exceeded."""
    pass


class QuotaTracker:
    """
    Track API quota usage and prevent overages per API key.
    
    Implements singleton pattern to ensure consistent quota tracking
    across the entire application, regardless of how many scripts
    are running or how many times the tracker is instantiated.
    
    Features:
    - Per-key quota tracking (supports multiple API keys)
    - Daily quota limit enforcement with configurable thresholds
    - Automatic daily reset at midnight UTC
    - Support for variable quota costs (1x regular, 10x historical)
    - Warning notifications when approaching quota limits
    
    Example:
        tracker = QuotaTracker.get_instance(daily_limit=10000)
        tracker.update_usage(key_id='paid', used=100, remaining=9900)
        tracker.check_quota_available(key_id='paid')
    """
    
    _instance: Optional['QuotaTracker'] = None
    
    def __init__(self, daily_limit: int = 10000, warn_threshold: float = 0.8):
        """
        Initialize quota tracker.
        
        Args:
            daily_limit: Default maximum API requests allowed per day
            warn_threshold: Warning threshold as percentage (0.8 = 80%)
        """
        self.default_daily_limit = daily_limit
        self.warn_threshold = warn_threshold
        # Per-key quota tracking: key_id -> {daily_limit, requests_today, current_date}
        self.quotas: Dict[str, Dict[str, Any]] = {}
        logger.info(f"QuotaTracker initialized: {daily_limit} requests/day (default), warn at {warn_threshold*100:.0f}%")
    
    @classmethod
    def get_instance(cls, daily_limit: int = 10000, warn_threshold: float = 0.8) -> 'QuotaTracker':
        """
        Get singleton instance of QuotaTracker.
        
        Args:
            daily_limit: Maximum API requests allowed per day (default: 10000)
            warn_threshold: Warning threshold as percentage (default: 0.8 = 80%)
        
        Returns:
            QuotaTracker: Singleton instance
        """
        if cls._instance is None:
            cls._instance = cls(daily_limit, warn_threshold)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (useful for testing)."""
        cls._instance = None
    
    def _get_or_create_quota(self, key_id: str) -> Dict[str, Any]:
        """
        Get or create quota tracking for a specific API key.
        
        Args:
            key_id: Identifier for the API key (e.g., 'free', 'paid')
        
        Returns:
            Dict containing quota tracking data for this key
        """
        if key_id not in self.quotas:
            self.quotas[key_id] = {
                'daily_limit': self.default_daily_limit,
                'requests_today': 0,
                'current_date': datetime.now(timezone.utc).date()
            }
            logger.info(f"[{key_id}] Created quota tracker with default limit: {self.default_daily_limit}")
        return self.quotas[key_id]
    
    def check_quota_available(self, key_id: str = 'default', buffer: int = 100) -> bool:
        """
        Check if quota is likely available based on last known server state.
        
        This is a pre-flight check to fail fast if quota is exhausted.
        The actual quota is managed by the server and synced via response headers.
        
        Args:
            key_id: Identifier for the API key (e.g., 'free', 'paid')
            buffer: Safety buffer - require this many requests remaining (default: 100)
        
        Returns:
            bool: True if quota appears available, False otherwise
        """
        quota = self._get_or_create_quota(key_id)
        
        # Check if we've crossed into a new day (automatic reset)
        today = datetime.now(timezone.utc).date()
        if today != quota['current_date']:
            logger.info(f"[{key_id}] New day detected, resetting quota counter (was: {quota['requests_today']})")
            quota['requests_today'] = 0
            quota['current_date'] = today
        
        remaining = self.get_remaining(key_id)
        available = remaining > buffer
        
        if not available:
            logger.warning(
                f"[{key_id}] ⚠️  Quota may be exhausted: {remaining} remaining (buffer: {buffer})"
            )
        elif remaining < quota['daily_limit'] * (1 - self.warn_threshold):
            # Warn if we're past the warning threshold
            usage_pct = (quota['requests_today'] / quota['daily_limit']) * 100
            logger.warning(
                f"[{key_id}] ⚠️  Quota at {usage_pct:.1f}%: "
                f"{quota['requests_today']}/{quota['daily_limit']} requests used"
            )
        
        return available
    
    def update_usage(self, used: int, remaining: int, key_id: str = 'default') -> None:
        """
        Update local state with authoritative server-reported usage.
        
        Args:
            used: Usage from x-requests-used header
            remaining: Remaining from x-requests-remaining header
            key_id: Identifier for the API key (e.g., 'free', 'paid')
        """
        quota = self._get_or_create_quota(key_id)
        total = used + remaining
        quota['requests_today'] = used
        
        if total != quota['daily_limit']:
            logger.info(f"[{key_id}] Updating daily limit: {quota['daily_limit']} → {total}")
            quota['daily_limit'] = total
    
    def get_remaining(self, key_id: str = 'default') -> int:
        """
        Get remaining quota for today for a specific API key.
        
        Args:
            key_id: Identifier for the API key (e.g., 'free', 'paid')
        
        Returns:
            int: Number of remaining quota units (never negative)
        """
        quota = self._get_or_create_quota(key_id)
        return max(0, quota['daily_limit'] - quota['requests_today'])
    
    def get_usage_summary(self, key_id: str = 'default') -> Dict[str, Any]:
        """
        Get comprehensive quota usage summary for a specific API key.
        
        Args:
            key_id: Identifier for the API key (e.g., 'free', 'paid')
        
        Returns:
            Dict containing:
                - key_id: The API key identifier
                - requests_used: Number of quota units consumed today
                - daily_limit: Maximum allowed quota
                - remaining: Remaining quota
                - usage_pct: Usage percentage (0-100)
                - date: Current tracking date (UTC)
        """
        quota = self._get_or_create_quota(key_id)
        return {
            'key_id': key_id,
            'requests_used': quota['requests_today'],
            'daily_limit': quota['daily_limit'],
            'remaining': self.get_remaining(key_id),
            'usage_pct': (quota['requests_today'] / quota['daily_limit']) * 100,
            'date': quota['current_date'].isoformat()
        }
    
    def get_all_quotas_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get quota usage summary for all tracked API keys.
        
        Returns:
            Dict mapping key_id to usage summary for each tracked key
        """
        return {key_id: self.get_usage_summary(key_id) for key_id in self.quotas.keys()}


def setup_quota_tracker(cfg: Any) -> Optional[QuotaTracker]:
    """Initialize quota tracker if enabled."""
    quota_tracker = None
    if cfg.enable_quota_tracking:
        quota_tracker = QuotaTracker.get_instance(
            daily_limit=cfg.daily_quota_limit,
            warn_threshold=cfg.quota_warn_threshold
        )
        logger.info(f"✓ Quota tracker initialized: {cfg.daily_quota_limit} requests/day")
    return quota_tracker
