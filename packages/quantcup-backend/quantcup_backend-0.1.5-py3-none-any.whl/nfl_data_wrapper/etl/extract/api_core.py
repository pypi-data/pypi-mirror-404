"""
Core utilities for NFL Data Python extraction.

Handles session management, retry logic, data validation, and caching
for robust interaction with the nfl_data_py library.
"""

# pylint: disable=no-member  # External library members not recognized by linter

import pandas as pd
import nfl_data_py as nfl
from datetime import datetime
from typing import List, Optional, Union, Any
from functools import wraps
import time

# Import logging from common module
from commonv2 import get_logger

# Use centralized logging (updated from stdlib logging)
logger = get_logger('nfl_data_py.api_core')

__all__ = [
    'get_nfl_session',
    'close_nfl_session', 
    'validate_years',
    'validate_stat_type',
    'handle_data_cleaning',
    'add_metadata_columns',
    '_nfl_import_with_retry',
    # NFL Data Python wrapper functions
    '_import_pbp_data',
    '_import_weekly_data',
    '_import_seasonal_data',
    '_import_seasonal_rosters',
    '_import_weekly_rosters',
    '_import_team_desc',
    '_import_win_totals',
    '_import_sc_lines',
    '_import_schedules',
    '_import_officials',
    '_import_draft_picks',
    '_import_draft_values',
    '_import_combine_data',
    '_import_ids',
    '_import_ngs_data',
    '_import_depth_charts',
    '_import_injuries',
    '_import_qbr',
    '_import_snap_counts',
    '_import_seasonal_pfr',
    '_import_weekly_pfr',
    '_import_ftn_data',
    '_see_pbp_cols',
    '_see_weekly_cols',
    '_cache_pbp'
]

# Global session state for caching and configuration
_nfl_session = {
    'cache_enabled': False,
    'cache_path': None,
    'default_downcast': True,
    'session_active': False
}

def get_nfl_session(cache_enabled=False, cache_path=None, default_downcast=True):
    """
    Initialize or get the NFL data session with configuration.
    
    Args:
        cache_enabled: Whether to enable local caching
        cache_path: Custom cache path (optional)
        default_downcast: Default downcast setting for memory optimization
        
    Returns:
        dict: Session configuration
    """
    global _nfl_session
    
    if not _nfl_session['session_active']:
        _nfl_session.update({
            'cache_enabled': cache_enabled,
            'cache_path': cache_path,
            'default_downcast': default_downcast,
            'session_active': True
        })
        logger.info(f"NFL data session initialized - cache: {cache_enabled}, downcast: {default_downcast}")
    
    return _nfl_session.copy()

def close_nfl_session():
    """Close the NFL data session and cleanup."""
    global _nfl_session
    _nfl_session = {
        'cache_enabled': False,
        'cache_path': None,
        'default_downcast': True,
        'session_active': False
    }
    logger.info("NFL data session closed")

def validate_years(years: Union[int, List[int], None]) -> List[int]:
    """
    Validate and normalize years parameter.
    
    Args:
        years: Year or list of years to validate
        
    Returns:
        List[int]: Validated list of years
        
    Raises:
        ValueError: If years are invalid
    """
    if years is None:
        return []
    
    if isinstance(years, int):
        years = [years]
    
    if not isinstance(years, list):
        raise ValueError(f"Years must be int, list of ints, or None. Got: {type(years)}")
    
    current_year = datetime.now().year
    valid_years = []
    
    for year in years:
        if not isinstance(year, int):
            raise ValueError(f"Year must be integer. Got: {type(year)} ({year})")
        
        if year < 1999:
            logger.warning(f"Year {year} is before 1999 (earliest available data)")
        elif year > current_year + 1:
            logger.warning(f"Year {year} is in the future")
        
        valid_years.append(year)
    
    return valid_years

def validate_stat_type(stat_type: str, valid_types: List[str]) -> str:
    """
    Validate stat_type parameter.
    
    Args:
        stat_type: The stat type to validate
        valid_types: List of valid stat types
        
    Returns:
        str: Validated stat type
        
    Raises:
        ValueError: If stat_type is invalid
    """
    if not isinstance(stat_type, str):
        raise ValueError(f"stat_type must be string. Got: {type(stat_type)}")
    
    if stat_type not in valid_types:
        raise ValueError(f"stat_type must be one of {valid_types}. Got: {stat_type}")
    
    return stat_type

def handle_data_cleaning(df: pd.DataFrame, clean_data: bool = True) -> pd.DataFrame:
    """
    Apply data cleaning if requested.
    
    Args:
        df: DataFrame to clean
        clean_data: Whether to apply cleaning
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    if df.empty or not clean_data:
        return df
    
    try:
        # Note: clean_nfl_data function may not be available in all versions
        if hasattr(nfl, 'clean_nfl_data'):
            cleaned_df = nfl.clean_nfl_data(df)  # type: ignore
            logger.debug("Applied nfl_data_py data cleaning")
            return cleaned_df
        
        logger.debug("clean_nfl_data not available, returning original data")
        return df
    except Exception as e:
        logger.warning(f"Data cleaning failed: {e}. Returning original data.")
        return df

def _nfl_import_with_retry(func, *args, max_retries=3, delay=1, **kwargs):
    """
    Execute nfl_data_py import function with retry logic.
    
    Args:
        func: The nfl_data_py function to call
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        **kwargs: Keyword arguments for the function
        
    Returns:
        pd.DataFrame: Result from the function or empty DataFrame on failure
    """
    func_name = getattr(func, '__name__', str(func))
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Calling {func_name} (attempt {attempt + 1}/{max_retries})")
            
            # Apply session defaults if not specified
            session = get_nfl_session()
            if 'downcast' in kwargs and kwargs['downcast'] is None:
                kwargs['downcast'] = session['default_downcast']
            
            result = func(*args, **kwargs)
            
            if result is not None and not result.empty:
                logger.info(f"{func_name} succeeded: {len(result)} records")
                return result
            else:
                logger.warning(f"{func_name} returned empty data")
                return pd.DataFrame()
                
        except Exception as e:
            logger.warning(f"{func_name} attempt {attempt + 1} failed: {e}")
            
            if attempt == max_retries - 1:
                logger.error(f"{func_name} failed after {max_retries} attempts")
                return pd.DataFrame()
            
            if delay > 0:
                time.sleep(delay)
    
    return pd.DataFrame()

def add_metadata_columns(df: pd.DataFrame, source_function: Optional[str] = None) -> pd.DataFrame:
    """
    Add metadata columns to track data source and extraction time.
    
    Args:
        df: DataFrame to add metadata to
        source_function: Name of the source function
        
    Returns:
        pd.DataFrame: DataFrame with metadata columns
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Add extraction timestamp
    df['_extracted_at'] = datetime.now()
    
    # Add source function if provided
    if source_function:
        df['_source_function'] = source_function
    
    return df

# ============================================================================
# NFL Data Python Wrapper Functions
# ============================================================================

# Play-by-Play & Weekly Data
def _import_pbp_data(years, **kwargs):
    """Internal wrapper for nfl_data_py.import_pbp_data"""
    return _nfl_import_with_retry(nfl.import_pbp_data, years, **kwargs)  # type: ignore

def _import_weekly_data(years, **kwargs):
    """Internal wrapper for nfl_data_py.import_weekly_data"""
    return _nfl_import_with_retry(nfl.import_weekly_data, years, **kwargs)  # type: ignore

def _import_seasonal_data(years, **kwargs):
    """Internal wrapper for nfl_data_py.import_seasonal_data"""
    return _nfl_import_with_retry(nfl.import_seasonal_data, years, **kwargs)  # type: ignore

# Roster & Team Data
def _import_seasonal_rosters(years, **kwargs):
    """Internal wrapper for nfl_data_py.import_seasonal_rosters"""
    return _nfl_import_with_retry(nfl.import_seasonal_rosters, years, **kwargs)  # type: ignore

def _import_weekly_rosters(years, **kwargs):
    """Internal wrapper for nfl_data_py.import_weekly_rosters"""
    return _nfl_import_with_retry(nfl.import_weekly_rosters, years, **kwargs)  # type: ignore

def _import_team_desc(**kwargs):
    """Internal wrapper for nfl_data_py.import_team_desc"""
    return _nfl_import_with_retry(nfl.import_team_desc, **kwargs)  # type: ignore

# Betting & Lines
def _import_win_totals(*args, **kwargs):
    """Internal wrapper for nfl_data_py.import_win_totals"""
    return _nfl_import_with_retry(nfl.import_win_totals, *args, **kwargs)  # type: ignore

def _import_sc_lines(*args, **kwargs):
    """Internal wrapper for nfl_data_py.import_sc_lines"""
    return _nfl_import_with_retry(nfl.import_sc_lines, *args, **kwargs)  # type: ignore

# Schedule & Games
def _import_schedules(years, **kwargs):
    """Internal wrapper for nfl_data_py.import_schedules"""
    return _nfl_import_with_retry(nfl.import_schedules, years, **kwargs)  # type: ignore

def _import_officials(*args, **kwargs):
    """Internal wrapper for nfl_data_py.import_officials"""
    return _nfl_import_with_retry(nfl.import_officials, *args, **kwargs)  # type: ignore

# Draft Data
def _import_draft_picks(*args, **kwargs):
    """Internal wrapper for nfl_data_py.import_draft_picks"""
    return _nfl_import_with_retry(nfl.import_draft_picks, *args, **kwargs)  # type: ignore

def _import_draft_values(**kwargs):
    """Internal wrapper for nfl_data_py.import_draft_values"""
    return _nfl_import_with_retry(nfl.import_draft_values, **kwargs)  # type: ignore

def _import_combine_data(*args, **kwargs):
    """Internal wrapper for nfl_data_py.import_combine_data"""
    return _nfl_import_with_retry(nfl.import_combine_data, *args, **kwargs)  # type: ignore

# Advanced Stats
def _import_ids(**kwargs):
    """Internal wrapper for nfl_data_py.import_ids"""
    return _nfl_import_with_retry(nfl.import_ids, **kwargs)  # type: ignore

def _import_ngs_data(stat_type, *args, **kwargs):
    """Internal wrapper for nfl_data_py.import_ngs_data"""
    return _nfl_import_with_retry(nfl.import_ngs_data, stat_type, *args, **kwargs)  # type: ignore

def _import_depth_charts(*args, **kwargs):
    """Internal wrapper for nfl_data_py.import_depth_charts"""
    return _nfl_import_with_retry(nfl.import_depth_charts, *args, **kwargs)  # type: ignore

def _import_injuries(*args, **kwargs):
    """Internal wrapper for nfl_data_py.import_injuries"""
    return _nfl_import_with_retry(nfl.import_injuries, *args, **kwargs)  # type: ignore

def _import_qbr(*args, **kwargs):
    """Internal wrapper for nfl_data_py.import_qbr"""
    return _nfl_import_with_retry(nfl.import_qbr, *args, **kwargs)  # type: ignore

def _import_snap_counts(*args, **kwargs):
    """Internal wrapper for nfl_data_py.import_snap_counts"""
    return _nfl_import_with_retry(nfl.import_snap_counts, *args, **kwargs)  # type: ignore

# Pro Football Reference
def _import_seasonal_pfr(s_type, *args, **kwargs):
    """Internal wrapper for nfl_data_py.import_seasonal_pfr"""
    return _nfl_import_with_retry(nfl.import_seasonal_pfr, s_type, *args, **kwargs)  # type: ignore

def _import_weekly_pfr(s_type, *args, **kwargs):
    """Internal wrapper for nfl_data_py.import_weekly_pfr"""
    return _nfl_import_with_retry(nfl.import_weekly_pfr, s_type, *args, **kwargs)  # type: ignore

# Third Party
def _import_ftn_data(years, **kwargs):
    """Internal wrapper for nfl_data_py.import_ftn_data"""
    return _nfl_import_with_retry(nfl.import_ftn_data, years, **kwargs)  # type: ignore

# Utilities
def _see_pbp_cols():
    """Internal wrapper for nfl_data_py.see_pbp_cols"""
    try:
        return nfl.see_pbp_cols()  # type: ignore
    except Exception as e:
        logger.error(f"Failed to get PBP columns: {e}")
        return []

def _see_weekly_cols():
    """Internal wrapper for nfl_data_py.see_weekly_cols"""
    try:
        return nfl.see_weekly_cols()  # type: ignore
    except Exception as e:
        logger.error(f"Failed to get weekly columns: {e}")
        return []

def _cache_pbp(years, **kwargs):
    """Internal wrapper for nfl_data_py.cache_pbp"""
    try:
        nfl.cache_pbp(years, **kwargs)  # type: ignore
        logger.info(f"Successfully cached PBP data for years: {years}")
    except Exception as e:
        logger.error(f"Failed to cache PBP data: {e}")
