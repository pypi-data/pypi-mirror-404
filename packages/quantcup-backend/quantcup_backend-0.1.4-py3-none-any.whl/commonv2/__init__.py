"""
CommonV2 - Refactored shared utilities for quantcup ecosystem
Provides stable public API with improved organization and testability.

This is a refactored version of the original 'common' module with:
- Better organization using submodules (core/, data/, domain/)
- Stable facade API to prevent breaking changes
- Comprehensive test coverage
- Clear separation of concerns
"""

__version__ = "2.0.0"

# Core infrastructure
from .core.logging import setup_logger, get_logger, setup_nflfastr_logger, setup_odds_api_logger, setup_nfl_data_py_logger
from .core.errors import (
    NFLfastRError, 
    ConfigurationError, 
    DataValidationError, 
    NetworkError, 
    SeasonError,
    handle_cli_error,
    validate_required_config,
    validate_file_exists,
    validate_directory_exists,
    safe_int_conversion
)
from .core.cli import (
    opt_verbose, 
    opt_dry_run, 
    opt_config, 
    opt_workers, 
    opt_season, 
    parse_seasons_or_none,
    opt_force,
    opt_no_cache,
    opt_output_format,
    opt_limit,
    ExitCodes,
    echo_success,
    echo_warning,
    echo_error,
    echo_info,
    confirm_operation
)

# Enhanced data operations with loading strategies
from ._data.database import (
    create_db_engine_from_env,
    get_table_row_count,
    get_all_table_row_counts,
    table_exists,
    drop_table,
    db_session,
    DatabaseConfig,
    execute_incremental_load,        # NEW
    execute_full_refresh,            # NEW
)

from .utils.validation import (
    UnifiedDataValidator,
    DataQualityError,
    validate_dataframe,
    apply_cleaning,
    standardize_dtypes_for_postgres,
    TABLE_SPECIFIC_TYPE_RULES,
    QUALITY_THRESHOLDS,
    NFL_SCHEMAS
)

# Domain logic
from .domain.teams import (
    get_all_teams, 
    validate_team_data,
    standardize_team_name, 
    standardize_team_column,
    get_team_abbreviation,
    get_team_full_name,
    validate_team_names,
    get_all_team_abbreviations,
    get_all_team_names
)
from .domain.schedules import (
    get_upcoming_games,
    get_games_by_week,
    get_schedule_for_seasons,
    validate_schedule_data
)

# Public API definition - this is what consumers should import
__all__ = [
    # Core infrastructure
    'setup_logger', 
    'get_logger', 
    'setup_nflfastr_logger',
    'setup_odds_api_logger', 
    'setup_nfl_data_py_logger',
    'NFLfastRError', 
    'ConfigurationError',
    'DataValidationError',
    'NetworkError',
    'SeasonError',
    'handle_cli_error',
    'validate_required_config',
    'validate_file_exists',
    'validate_directory_exists',
    'safe_int_conversion',
    'opt_verbose', 
    'opt_dry_run',
    'opt_config',
    'opt_workers',
    'opt_season', 
    'parse_seasons_or_none',
    'opt_force',
    'opt_no_cache',
    'opt_output_format',
    'opt_limit',
    'ExitCodes',
    'echo_success',
    'echo_warning',
    'echo_error',
    'echo_info',
    'confirm_operation',
    
    # Enhanced data operations with loading strategies
    'create_db_engine_from_env',
    'get_table_row_count',
    'get_all_table_row_counts',
    'table_exists',
    'drop_table',
    'db_session',
    'DatabaseConfig',
    'execute_incremental_load',      # NEW
    'execute_full_refresh',          # NEW
    'UnifiedDataValidator',          # NEW
    'DataQualityError',              # NEW
    'validate_dataframe',            # NEW
    'apply_cleaning',                # NEW
    'standardize_dtypes_for_postgres', # NEW
    'TABLE_SPECIFIC_TYPE_RULES',     # NEW
    'QUALITY_THRESHOLDS',            # NEW
    'NFL_SCHEMAS',                   # NEW
    
    # Domain logic
    'get_all_teams',
    'validate_team_data',
    'standardize_team_name',
    'standardize_team_column',
    'get_team_abbreviation',
    'get_team_full_name',
    'validate_team_names',
    'get_all_team_abbreviations',
    'get_all_team_names',
    'get_upcoming_games',
    'get_games_by_week',
    'get_schedule_for_seasons',
    'validate_schedule_data'
]
