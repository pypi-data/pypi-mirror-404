"""
Team ID registry for stable participant identification.

Dynamically loads participants data from Odds API (no CSV dependency).
"""
import pandas as pd
from typing import Dict, List, Optional, TYPE_CHECKING
from functools import lru_cache

from commonv2.core.logging import setup_logger
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from odds_api.config.settings import get_settings, BackfillSettings
from odds_api.etl.extract.api import fetch_participants_data

if TYPE_CHECKING:
    from odds_api.config import Settings

logger = setup_logger('odds_api.team_registry', project_name='ODDS_API')


class TeamRegistry:
    """
    Map team name variants to stable participant IDs.
    
    Solves the "LA Chargers" vs "Los Angeles Chargers" problem by providing
    a single source of truth from the Odds API /participants endpoint.
    
    ARCHITECTURE:
    - Lazy-loads from API on first use (FREE endpoint, no quota cost)
    - Caches in memory for performance
    - No CSV dependency - always fresh data
    """
    
    def __init__(self, sport_key: str = 'americanfootball_nfl'):
        """
        Initialize team registry (lazy-load on first use).
        
        Args:
            sport_key: Sport identifier for API (default: 'americanfootball_nfl')
        """
        self._sport_key = sport_key
        self._cache_loaded = False
        self.teams = pd.DataFrame()
        self.name_to_id = {}
        self.id_to_name = {}

    def _load_cache(self) -> None:
        """Load team data from bucket (primary) or API (fallback)."""
        if self._cache_loaded:
            logger.debug("Team registry cache already loaded")
            return

        # Try bucket first
        try:
            settings = get_settings()
            backfill: BackfillSettings = settings.backfill
            bucket = get_bucket_adapter()
            
            logger.info(f"Attempting to load team registry from bucket ({backfill.bucket_schema}.dim_teams)...")
            df = bucket.read_data(table_name='dim_teams', schema=backfill.bucket_schema)
            
            if df is not None and not df.empty:
                # Normalize column names if needed (bucket might use team_id, API uses id)
                if 'team_id' in df.columns and 'id' not in df.columns:
                    df = df.rename(columns={'team_id': 'id'})
                
                self.teams = df
                self._build_lookups()
                self._cache_loaded = True
                logger.info(f"✓ Loaded {len(self.teams)} teams from bucket")
                return
        except Exception as e:
            logger.warning(f"Bucket load failed, falling back to API: {e}")

        # Fallback to API
        try:
            logger.info(f"Fetching fresh participants data from API for {self._sport_key}...")
            response = fetch_participants_data(sport_key=self._sport_key)
            
            # API returns a list of dicts directly or in a 'data' key
            data = response if isinstance(response, list) else response.get('data', [])
            
            if data:
                self.teams = pd.DataFrame(data)
                self._build_lookups()
                self._cache_loaded = True
                logger.info(f"✓ Loaded {len(self.teams)} teams from API")
                if not self.teams.empty:
                    logger.debug(f"Sample teams from API: {self.teams['full_name'].head().tolist()}")
            else:
                logger.warning("No participants data returned from API")
        except Exception as e:
            logger.error(f"Failed to load team registry from both bucket and API: {e}")

    def _build_lookups(self) -> None:
        """Build fast lookup dictionaries for team name variants."""
        self.name_to_id = {}
        self.id_to_name = {}
        
        for _, team in self.teams.iterrows():
            team_id = team['id']
            full_name = team['full_name']
            
            # Store official mapping
            self.id_to_name[team_id] = full_name
            
            # Build variant mappings for fuzzy matching
            variants = self._generate_name_variants(full_name)
            for variant in variants:
                self.name_to_id[variant.lower()] = team_id
        
        logger.info(f"   Generated {len(self.name_to_id)} name variants for matching")
    
    def _generate_name_variants(self, full_name: str) -> List[str]:
        """
        Generate common variants of a team name.
        
        Examples for "Los Angeles Chargers":
            - "Los Angeles Chargers" (official)
            - "LA Chargers" (abbreviated city)
            - "Chargers" (nickname only)
            - "los angeles chargers" (lowercase)
        """
        variants = [full_name]
        
        # Lowercase variant
        variants.append(full_name.lower())
        
        # City abbreviations
        city_abbrevs = {
            'Los Angeles': 'LA',
            'New York': 'NY',
            'New England': 'NE',
            'New Orleans': 'NO',
            'San Francisco': 'SF',
            'Tampa Bay': 'TB',
            'Kansas City': 'KC',
            'Green Bay': 'GB',
            'Las Vegas': 'LV',
        }
        
        for full_city, abbrev_city in city_abbrevs.items():
            if full_name.startswith(full_city):
                abbreviated = full_name.replace(full_city, abbrev_city)
                variants.append(abbreviated)
                variants.append(abbreviated.lower())
        
        # Nickname only (last word)
        parts = full_name.split()
        if len(parts) > 1:
            nickname = parts[-1]
            variants.append(nickname)
            variants.append(nickname.lower())
        
        return variants
    
    @lru_cache(maxsize=256)
    def get_participant_id(self, team_name: str) -> Optional[str]:
        """
        Get stable participant ID for a team name (handles variants).
        
        Args:
            team_name: Team name from API (e.g., "LA Chargers", "Los Angeles Chargers")
            
        Returns:
            Stable participant ID (e.g., "par_01hqmkr1yafvas6wtv3jfs9f7a")
            or None if not found
        """
        if not team_name:
            return None
        
        self._load_cache()
        
        # Try exact match first
        team_id = self.name_to_id.get(team_name.lower())
        if team_id:
            return team_id
        
        # Try fuzzy match (check if any variant appears in the name)
        team_lower = team_name.lower()
        for variant, team_id in self.name_to_id.items():
            # Check if variant is in the team name (handles extra text)
            if variant in team_lower or team_lower in variant:
                logger.debug(f"Fuzzy matched '{team_name}' → '{variant}' → {team_id}")
                return team_id
        
        logger.warning(f"⚠️  Unknown team: '{team_name}'")
        return None
    
    def get_team_name(self, participant_id: str) -> Optional[str]:
        """Get official team name from participant ID."""
        self._load_cache()
        return self.id_to_name.get(participant_id)


# Global singleton instance
_registry = None


def get_team_registry() -> TeamRegistry:
    """Get singleton team registry instance."""
    global _registry
    if _registry is None:
        _registry = TeamRegistry()
    return _registry
