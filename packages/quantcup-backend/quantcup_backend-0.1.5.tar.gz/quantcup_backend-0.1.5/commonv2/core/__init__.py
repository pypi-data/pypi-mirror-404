"""
Core infrastructure module for CommonV2.

Contains stable foundational utilities:
- Configuration validation
- Logging setup
- Error handling
- CLI utilities
"""

from .logging import setup_logger, get_logger, setup_nflfastr_logger, setup_odds_api_logger, setup_nfl_data_py_logger
from .errors import (
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
from .cli import (
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

__all__ = [
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
    'confirm_operation'
]
