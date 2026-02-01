"""
Thin adapters for external dependencies.

Following Phase 1 patterns: simple wrappers that isolate external APIs
and provide clean interfaces for the domain layer.
"""

import pandas as pd
import sqlalchemy as sa
from typing import List, Optional
from ..core.logging import get_logger
from .._data.sql_queries import GET_TEAMS_BY_ABBREVIATIONS
from .models import Team, Game, TeamDataFrame, GameDataFrame


class DatabaseTeamRepository:
    """
    Thin adapter for database team operations.
    
    Wraps database access and provides clean interface.
    Simple parameter injection for testability.
    """
    
    def __init__(self, engine, logger=None):
        """Simple dependency injection via constructor."""
        self._engine = engine
        self._logger = logger or get_logger('commonv2.domain.adapters')
    
    def get_all_teams(self) -> TeamDataFrame:
        """Get all teams from database."""
        try:
            # Get canonical abbreviations directly from TeamNameStandardizer
            standardizer = TeamNameStandardizer()
            canonical_abbrs = standardizer.get_all_abbreviations()
            
            with self._engine.connect() as conn:
                stmt = sa.text(GET_TEAMS_BY_ABBREVIATIONS).bindparams(
                    sa.bindparam("canonical_abbrs", expanding=True)
                )
                teams_df = pd.read_sql(
                    stmt,
                    conn,
                    params={'canonical_abbrs': tuple(canonical_abbrs)}
                )
            
            if teams_df.empty:
                self._logger.warning("No team data found in database")
                return pd.DataFrame()
            
            self._logger.info(f"Retrieved {len(teams_df)} teams from database")
            return teams_df
            
        except Exception as e:
            self._logger.error(f"Failed to get team data from database: {e}")
            return pd.DataFrame()
    
    def get_team_by_abbreviation(self, abbr: str) -> Optional[Team]:
        """Get a single team by abbreviation."""
        teams_df = self.get_all_teams()
        if teams_df.empty:
            return None
        
        team_row = teams_df[teams_df['team_abbr'] == abbr]
        if team_row.empty:
            return None
        
        row = team_row.iloc[0]
        return Team(
            abbreviation=row['team_abbr'],
            full_name=row['team_name'],
            nickname=row.get('team_nick'),
            conference=row.get('team_conf'),
            division=row.get('team_division'),
            team_id=row.get('team_id'),
            primary_color=row.get('team_color'),
            secondary_color=row.get('team_color2'),
            logo_espn=row.get('team_logo_espn'),
            logo_wikipedia=row.get('team_logo_wikipedia')
        )


class NFLDataScheduleProvider:
    """
    Thin adapter for nfl_data_py schedule operations.
    
    Anti-corruption layer that wraps external API and handles errors.
    """
    
    def __init__(self, logger=None):
        """Simple dependency injection via constructor."""
        self._logger = logger or get_logger('commonv2.domain.adapters')
    
    def get_schedule_data(self, seasons: List[int]) -> GameDataFrame:
        """
        Get schedule data from nfl_data_py with error handling.
        
        Returns clean DataFrame or empty DataFrame on failure.
        """
        try:
            # Import inside method to avoid circular imports and handle missing dependency
            import nfl_data_py as nfl
            
            self._logger.info(f"Fetching schedule data for seasons: {seasons}")
            schedule_df = nfl.import_schedules(seasons)
            
            if schedule_df.empty:
                self._logger.warning(f"No schedule data found for seasons: {seasons}")
                return pd.DataFrame()
            
            self._logger.info(f"Retrieved {len(schedule_df)} games from nfl_data_py")
            return schedule_df
            
        except RecursionError as e:
            self._logger.error(f"RecursionError from nfl_data_py.import_schedules({seasons}): {e}")
            return pd.DataFrame()
        except ImportError as e:
            self._logger.error(f"nfl_data_py not available: {e}")
            return pd.DataFrame()
        except Exception as e:
            self._logger.error(f"Failed to get schedule data: {e}")
            return pd.DataFrame()


class TeamNameStandardizer:
    """
    Domain service for team name standardization.
    
    Pure business logic with no external dependencies.
    """
    
    # Team mappings as class constants
    NFL_TEAM_MAPPINGS = {
        'ARI': 'Arizona Cardinals',
        'ATL': 'Atlanta Falcons', 
        'BAL': 'Baltimore Ravens',
        'BUF': 'Buffalo Bills',
        'CAR': 'Carolina Panthers',
        'CHI': 'Chicago Bears',
        'CIN': 'Cincinnati Bengals',
        'CLE': 'Cleveland Browns',
        'DAL': 'Dallas Cowboys',
        'DEN': 'Denver Broncos',
        'DET': 'Detroit Lions',
        'GB': 'Green Bay Packers',
        'HOU': 'Houston Texans',
        'IND': 'Indianapolis Colts',
        'JAX': 'Jacksonville Jaguars',
        'KC': 'Kansas City Chiefs',
        'LV': 'Las Vegas Raiders',
        'LAC': 'Los Angeles Chargers',
        'LAR': 'Los Angeles Rams',
        'MIA': 'Miami Dolphins',
        'MIN': 'Minnesota Vikings',
        'NE': 'New England Patriots',
        'NO': 'New Orleans Saints',
        'NYG': 'New York Giants',
        'NYJ': 'New York Jets',
        'PHI': 'Philadelphia Eagles',
        'PIT': 'Pittsburgh Steelers',
        'SF': 'San Francisco 49ers',
        'SEA': 'Seattle Seahawks',
        'TB': 'Tampa Bay Buccaneers',
        'TEN': 'Tennessee Titans',
        'WAS': 'Washington Commanders'
    }
    
    # Build aliases mapping
    TEAM_NAME_ALIASES = {}
    
    def __init__(self):
        """Initialize the standardizer with all mappings."""
        # Build comprehensive aliases mapping
        self.TEAM_NAME_ALIASES = {}
        
        # Add full names -> abbreviations
        for abbr, full_name in self.NFL_TEAM_MAPPINGS.items():
            self.TEAM_NAME_ALIASES[full_name] = abbr
        
        # Add abbreviations -> abbreviations (identity mapping)
        for abbr in self.NFL_TEAM_MAPPINGS.keys():
            self.TEAM_NAME_ALIASES[abbr] = abbr
        
        # Add common alternatives (abbreviation variants)
        abbreviation_aliases = {
            'GNB': 'GB', 'JAC': 'JAX', 'KAN': 'KC', 'LVR': 'LV', 'OAK': 'LV',
            'LA': 'LAR', 'NEP': 'NE', 'NOR': 'NO', 'SFO': 'SF', 'TAM': 'TB',
            'WSH': 'WAS'
        }
        self.TEAM_NAME_ALIASES.update(abbreviation_aliases)
        
        # Add team nicknames (e.g., "Cardinals" -> "ARI")
        nickname_mappings = {
            'Cardinals': 'ARI', 'Falcons': 'ATL', 'Ravens': 'BAL',
            'Bills': 'BUF', 'Panthers': 'CAR', 'Bears': 'CHI',
            'Bengals': 'CIN', 'Browns': 'CLE', 'Cowboys': 'DAL',
            'Broncos': 'DEN', 'Lions': 'DET', 'Packers': 'GB',
            'Texans': 'HOU', 'Colts': 'IND', 'Jaguars': 'JAX',
            'Chiefs': 'KC', 'Raiders': 'LV', 'Chargers': 'LAC',
            'Rams': 'LAR', 'Dolphins': 'MIA', 'Vikings': 'MIN',
            'Patriots': 'NE', 'Saints': 'NO', 'Giants': 'NYG',
            'Jets': 'NYJ', 'Eagles': 'PHI', 'Steelers': 'PIT',
            'Seahawks': 'SEA', '49ers': 'SF', 'Buccaneers': 'TB',
            'Titans': 'TEN', 'Commanders': 'WAS'
        }
        self.TEAM_NAME_ALIASES.update(nickname_mappings)
        
        # Add historical team names
        historical_names = {
            'Washington Redskins': 'WAS',
            'Washington Football Team': 'WAS',
            'Football Team': 'WAS',  # 2020-2021
            'San Diego Chargers': 'LAC',
            'St. Louis Rams': 'LAR',
            'Oakland Raiders': 'LV'
        }
        self.TEAM_NAME_ALIASES.update(historical_names)
    
    def standardize_team_name(self, team_name: str, output_format: str = 'abbr') -> str:
        """
        Standardize a team name to abbreviation or full name.
        
        Pure business logic with no side effects.
        """
        if pd.isna(team_name) or team_name is None:
            return team_name
        
        team_name = str(team_name).strip()
        
        if team_name in self.TEAM_NAME_ALIASES:
            abbr = self.TEAM_NAME_ALIASES[team_name]
            if output_format == 'abbr':
                return abbr
            elif output_format == 'full':
                return self.NFL_TEAM_MAPPINGS.get(abbr, team_name)
        
        # Return original if not found (no logging here - pure function)
        return team_name
    
    def standardize_dataframe_column(self, df: pd.DataFrame, column_name: str, 
                                   output_format: str = 'abbr', inplace: bool = False) -> pd.DataFrame:
        """Standardize a team column in a DataFrame."""
        if not inplace:
            df = df.copy()
        
        if column_name in df.columns:
            df[column_name] = df[column_name].apply(
                lambda x: self.standardize_team_name(x, output_format)
            )
        
        return df
    
    def get_all_abbreviations(self) -> List[str]:
        """Get all valid team abbreviations."""
        return list(self.NFL_TEAM_MAPPINGS.keys())
    
    def get_all_full_names(self) -> List[str]:
        """Get all valid team full names."""
        return list(self.NFL_TEAM_MAPPINGS.values())
