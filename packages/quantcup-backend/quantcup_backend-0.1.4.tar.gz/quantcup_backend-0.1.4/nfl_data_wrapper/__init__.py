"""
NFL Data Python API wrapper.

Provides a clean interface to nfl_data_py functionality with consistent
structure matching the odds_api module pattern.
"""

__version__ = "1.0.0"

# Import all functions from the API module
from .etl.extract.api import *

# Define __all__ to include all API functions
__all__ = [
    # Play-by-Play & Weekly Data
    'import_pbp_data',
    'import_weekly_data', 
    'import_seasonal_data',
    
    # Roster & Team Data
    'import_seasonal_rosters',
    'import_weekly_rosters',
    'import_team_desc',
    
    # Betting & Lines
    'import_win_totals',
    'import_sc_lines',
    
    # Schedule & Games
    'import_schedules',
    'import_officials',
    
    # Draft Data
    'import_draft_picks',
    'import_draft_values',
    'import_combine_data',
    
    # Advanced Stats
    'import_ids',
    'import_ngs_data',
    'import_depth_charts',
    'import_injuries',
    'import_qbr',
    'import_snap_counts',
    
    # Pro Football Reference
    'import_seasonal_pfr',
    'import_weekly_pfr',
    
    # Third Party
    'import_ftn_data',
    
    # Utilities
    'see_pbp_cols',
    'see_weekly_cols',
    'cache_pbp',
    'clean_nfl_data'
]
