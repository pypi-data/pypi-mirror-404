from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

class BaseScheduler(ABC):
    """
    Abstract Base Class for sport-specific backfill schedulers.
    
    Schedulers are responsible for:
    1. Fetching the schedule for a given season/range.
    2. Determining which snapshots to fetch for each game.
    3. Estimating the quota cost for a set of games.
    """
    
    @abstractmethod
    def get_schedule(self, season: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch the schedule for a given season.
        
        Args:
            season: The season year (e.g., 2023).
            **kwargs: Additional filters (e.g., week_range, date_range).
            
        Returns:
            List of game dictionaries.
        """
        pass

    @abstractmethod
    def get_snapshots(self, game: Dict[str, Any], save_to_bucket: bool = False) -> List[Dict[str, Any]]:
        """
        Determine the required snapshots for a single game.
        
        Args:
            game: Game dictionary with 'id' and 'commence_time'.
            save_to_bucket: Whether to check for existing snapshots in bucket.
            
        Returns:
            List of snapshot dictionaries with 'timestamp', 'role', etc.
        """
        pass

    @abstractmethod
    def snapshot_exists(self, event_id: str, commence_time: str, snapshot_ts: datetime, role: str) -> bool:
        """
        Check if a specific snapshot already exists in storage.
        """
        pass

    @abstractmethod
    def estimate_cost(self, games: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Estimate the quota cost for processing a list of games.
        
        Args:
            games: List of games to process.
            
        Returns:
            Dictionary with cost breakdown (e.g., {'base': 100, 'in_game': 50, 'total': 150}).
        """
        pass
