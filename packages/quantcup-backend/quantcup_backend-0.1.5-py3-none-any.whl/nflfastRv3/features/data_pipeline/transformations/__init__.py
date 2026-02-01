"""
Warehouse transformation modules for nflfastRv3.

Clean architecture implementation following REFACTORING_SPECS.md:
- Maximum 5 complexity points per module
- Maximum 3 layers call depth
- Minimum Viable Decoupling pattern

Imports all transformation builders for warehouse construction.
"""

# Bucket-first infrastructure
from .dataframe_engine import DataFrameEngine, create_dataframe_engine

# Dimensional table builders
from .dimension_game import build_dim_game
from .dimensions_player import build_dim_player
from .dimensions_calendar import build_dim_date, build_dim_drive

# Warehouse table builders
from .warehouse_injuries import build_warehouse_injuries
from .warehouse_player_id_mapping import build_player_id_mapping
from .warehouse_player_availability import build_warehouse_player_availability
from .warehouse_weather import build_dim_game_weather

# Fact table builders
from .facts import build_fact_play, build_fact_player_stats, build_fact_player_play

# Utility functions
from .warehouse_utils import save_table_to_db, validate_table_data

__all__ = [
    # Bucket-first infrastructure
    'DataFrameEngine',
    'create_dataframe_engine',
    
    # Dimension builders
    'build_dim_game',
    'build_dim_player',
    'build_dim_date',
    'build_dim_drive',
    
    # Warehouse builders
    'build_warehouse_injuries',
    'build_player_id_mapping',
    'build_warehouse_player_availability',
    'build_dim_game_weather',
    
    # Fact builders
    'build_fact_play',
    'build_fact_player_stats',
    'build_fact_player_play',
    
    # Utilities
    'save_table_to_db',
    'validate_table_data'
]
