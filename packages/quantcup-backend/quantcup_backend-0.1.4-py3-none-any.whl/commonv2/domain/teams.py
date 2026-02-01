"""
Team domain module for CommonV2.

Clean, testable team operations following Phase 1 patterns:
- Simple dependency injection via parameters
- Thin adapters for external dependencies  
- Pure business logic separated from infrastructure
- Facade pattern for clean public API
"""

import pandas as pd
import os
from typing import Optional, List
from ..core.logging import get_logger
from .models import TeamDataFrame

# Module-level logger for simple utilities (following database.py pattern)
_logger = get_logger('commonv2.domain.teams')


def get_all_teams(engine, logger=None, team_repo=None) -> TeamDataFrame:
    """
    Get all NFL teams with complete metadata from database.
    
    Clean facade function with explicit engine requirement.

    Args:
        engine: Database engine (required - caller must provide explicit engine)
        logger: Logger instance (optional, for dependency injection)
        team_repo: Team repository adapter (optional, for dependency injection)

    Returns:
        pd.DataFrame: All 32 NFL teams with metadata
        
    Raises:
        ValueError: If engine is None
    """
    # Validate required parameters
    if engine is None:
        raise ValueError("Engine parameter is required. Use create_db_engine_from_env(prefix) to create one.")
    
    # Create dependencies directly
    logger = logger or _logger
    
    if team_repo is None:
        from .adapters import DatabaseTeamRepository
        team_repo = DatabaseTeamRepository(engine, logger)
    
    # Use adapter to handle database operations
    return team_repo.get_all_teams()


def validate_team_data(df: TeamDataFrame, logger=None) -> bool:
    """
    Validate that team DataFrame has required columns and data.
    
    Uses centralized UnifiedDataValidator to reduce duplication.

    Args:
        df: Team DataFrame to validate
        logger: Logger instance (optional)

    Returns:
        bool: True if valid, False otherwise
    """
    from ..utils.validation.core import UnifiedDataValidator
    
    validator = UnifiedDataValidator(logger)
    return validator.validate_team_dataframe(df)


def standardize_team_name(team_name: str, output_format: str = 'abbr', 
                         standardizer=None) -> str:
    """
    Standardize a team name to either abbreviation or full name format.
    
    Clean facade with direct dependency creation (simplified from DependencyFactory).
    
    Args:
        team_name: The team name to standardize
        output_format: Either 'abbr' for abbreviation or 'full' for full name
        standardizer: Team name standardizer (optional, for dependency injection)
        
    Returns:
        str: Standardized team name, or original if not found
    """
    # Create standardizer directly
    if standardizer is None:
        from .adapters import TeamNameStandardizer
        standardizer = TeamNameStandardizer()
    
    return standardizer.standardize_team_name(team_name, output_format)


def standardize_team_column(df: pd.DataFrame, column_name: str, 
                          output_format: str = 'abbr', inplace: bool = False,
                          standardizer=None) -> pd.DataFrame:
    """
    Standardize a team column in a DataFrame.
    
    Clean facade with direct dependency creation (simplified from DependencyFactory).
    
    Args:
        df: The DataFrame containing the team column
        column_name: Name of the column to standardize
        output_format: Either 'abbr' for abbreviation or 'full' for full name
        inplace: Whether to modify the DataFrame in place
        standardizer: Team name standardizer (optional, for dependency injection)
        
    Returns:
        pd.DataFrame: DataFrame with standardized team names
    """
    # Create standardizer directly
    if standardizer is None:
        from .adapters import TeamNameStandardizer
        standardizer = TeamNameStandardizer()
    
    return standardizer.standardize_dataframe_column(df, column_name, output_format, inplace)


def get_team_abbreviation(team_name: str) -> str:
    """Get the standard abbreviation for a team name."""
    return standardize_team_name(team_name, output_format='abbr')


def get_team_full_name(team_name: str) -> str:
    """Get the full name for a team abbreviation or name."""
    return standardize_team_name(team_name, output_format='full')


def validate_team_names(df: pd.DataFrame, team_columns: List[str], logger=None,
                       standardizer=None) -> dict:
    """
    Validate that all team names in specified columns are recognized.
    
    Note: This function may need to be updated or removed as validate_team_names_in_columns
    was not found in UnifiedDataValidator. Consider implementing team name validation
    directly or removing this function if not used.
    
    Args:
        df: DataFrame to validate
        team_columns: List of column names containing team data
        logger: Logger instance (optional, for dependency injection)
        standardizer: Team name standardizer (optional, for dependency injection)
        
    Returns:
        dict: Dictionary with validation results
    """
    # TODO: This function needs review - validate_team_names_in_columns method
    # was not found in UnifiedDataValidator. Consider implementing or removing.
    logger = logger or _logger
    logger.warning("validate_team_names function needs review - method not available in UnifiedDataValidator")
    return {'valid': True, 'warnings': ['Team name validation not implemented']}


def get_all_team_abbreviations(standardizer=None) -> List[str]:
    """
    Get a list of all valid team abbreviations.
    
    Clean facade with direct dependency creation (simplified from DependencyFactory).
    """
    # Create standardizer directly
    if standardizer is None:
        from .adapters import TeamNameStandardizer
        standardizer = TeamNameStandardizer()
    
    return standardizer.get_all_abbreviations()


def get_all_team_names(standardizer=None) -> List[str]:
    """
    Get a list of all valid team full names.
    
    Clean facade with direct dependency creation (simplified from DependencyFactory).
    """
    # Create standardizer directly
    if standardizer is None:
        from .adapters import TeamNameStandardizer
        standardizer = TeamNameStandardizer()
    
    return standardizer.get_all_full_names()
