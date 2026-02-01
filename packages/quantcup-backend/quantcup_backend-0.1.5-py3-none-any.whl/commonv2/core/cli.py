"""
Shared CLI utilities for QuantCup commands.

Provides standardized Typer option factories and helpers to ensure consistent
behavior across all modules in the QuantCup ecosystem.
"""

from typing import Optional, List
import typer


def opt_verbose() -> bool:
    """Standard verbose option for all commands."""
    return typer.Option(False, "--verbose", "-v", help="Enable verbose logging output.")


def opt_dry_run() -> bool:
    """Standard dry-run option for all commands."""
    return typer.Option(False, "--dry-run", help="Show what would be done without making changes.")


def opt_config() -> Optional[str]:
    """Standard config file option for all commands."""
    return typer.Option(None, "--config", help="Path to config file (YAML/TOML). Overrides environment variables.")


def opt_workers() -> Optional[int]:
    """Standard workers option for parallel processing."""
    return typer.Option(None, "--workers", min=1, help="Maximum number of parallel workers.")


def opt_season(optional: bool = True) -> Optional[str]:
    """
    Standard season option for commands that support season filtering.
    
    Args:
        optional: If True, season is optional. If False, season is required.
        
    Returns:
        Typer option for season parameter
    """
    default_value = None if optional else ...
    help_text = "Season or range (e.g., 2024, 2020-2024, current)."
    
    return typer.Option(default_value, "--season", help=help_text)


def parse_seasons_or_none(season_expr: Optional[str]) -> Optional[List[int]]:
    """
    Parse season expression or return None if not provided.
    
    Args:
        season_expr: Season expression string or None
        
    Returns:
        List of season years or None if no expression provided
        
    Raises:
        typer.BadParameter: If season expression is invalid
    """
    if not season_expr:
        return None
    
    try:
        from ..domain.schedules import SeasonParser
        return SeasonParser.parse_season_expr(season_expr)
    except ValueError as e:
        raise typer.BadParameter(str(e))


def opt_force() -> bool:
    """Standard force option for operations that might overwrite data."""
    return typer.Option(False, "--force", help="Force operation even if data exists.")


def opt_no_cache() -> bool:
    """Standard no-cache option for operations that support caching."""
    return typer.Option(False, "--no-cache", help="Skip cache and fetch fresh data.")


def opt_output_format() -> str:
    """Standard output format option."""
    return typer.Option("table", "--format", help="Output format: table, json, csv.")


def opt_limit() -> Optional[int]:
    """Standard limit option for operations that return large datasets."""
    return typer.Option(None, "--limit", min=1, help="Limit number of results returned.")


# Standard exit codes
class ExitCodes:
    """Standard exit codes for CLI commands."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    CLI_ERROR = 2  # User input/argument errors
    DATA_ERROR = 3  # Data validation/processing errors
    CONFIG_ERROR = 4  # Configuration errors
    NETWORK_ERROR = 5  # Network/API errors


def echo_success(message: str) -> None:
    """Print success message in green."""
    typer.echo(typer.style(f"✓ {message}", fg=typer.colors.GREEN))


def echo_warning(message: str) -> None:
    """Print warning message in yellow."""
    typer.echo(typer.style(f"⚠ {message}", fg=typer.colors.YELLOW))


def echo_error(message: str) -> None:
    """Print error message in red."""
    typer.echo(typer.style(f"✗ {message}", fg=typer.colors.RED), err=True)


def echo_info(message: str) -> None:
    """Print info message in blue."""
    typer.echo(typer.style(f"ℹ {message}", fg=typer.colors.BLUE))


def confirm_operation(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation with a yes/no prompt.
    
    Args:
        message: Message to display
        default: Default value if user just presses enter
        
    Returns:
        True if user confirms, False otherwise
    """
    return typer.confirm(message, default=default)
