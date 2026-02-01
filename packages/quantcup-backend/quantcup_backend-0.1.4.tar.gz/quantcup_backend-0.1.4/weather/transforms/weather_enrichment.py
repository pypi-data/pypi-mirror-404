"""
Shared weather data enrichment functions.

Single source of truth for weather parsing, backfill, and quality tracking.
Used by:
- nflfastRv3/features/data_pipeline/transformations/warehouse_weather.py (table builder)
- scripts/review/review_weather_data.py (audit script)

Pattern: Shared transformation logic (2 complexity points)
- String parsing: 1 point
- Data quality tracking: 1 point
"""

import re
from typing import Optional, Tuple
import pandas as pd
import numpy as np

# Regex patterns for parsing weather strings (single definition)
_TEMP_RE = re.compile(r"(?i)\btemp:\s*(-?\d+)\s*°?\s*f\b")
_WIND_RE = re.compile(r"(?i)\bwind:\s*(?:[a-z]+)?\s*(\d+)\s*mph\b")
_CALM_RE = re.compile(r"(?i)\bwind:\s*calm\b")


def parse_weather_string(weather: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract temp/wind from weather description string.
    
    Single source of truth — replaces identical functions in:
    - warehouse_weather.py (Lines 32-59)
    - review_weather_data.py (Lines 99-126)
    
    Args:
        weather: Weather description like "Temp: 76° F, Wind: S 2 mph"
    
    Returns:
        Tuple of (temp_fahrenheit, wind_mph) or (None, None) if not parseable
    
    Examples:
        >>> parse_weather_string("Temp: 76° F, Wind: S 2 mph")
        (76, 2)
        >>> parse_weather_string("Wind: Calm")
        (None, 0)
        >>> parse_weather_string("Indoor Climate Controlled")
        (None, None)
    """
    if not isinstance(weather, str) or not weather.strip():
        return None, None
    
    t = None
    w = None
    
    mt = _TEMP_RE.search(weather)
    if mt:
        t = int(mt.group(1))
    
    if _CALM_RE.search(weather):
        w = 0
    else:
        mw = _WIND_RE.search(weather)
        if mw:
            w = int(mw.group(1))
    
    return t, w


def enrich_weather(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply full weather enrichment pipeline.
    
    Consolidates logic from:
    - warehouse_weather.py (Lines 100-171)
    - review_weather_data.py backfill_from_weather_string() (Lines 129-214)
    
    Steps:
    1. Store raw columns (temp_filled, wind_filled initial values)
    2. Parse weather strings to backfill missing values
    3. Detect malformed strings (keywords present but parse failed)
    4. Compute provenance categories (structured vs parsed vs mixed)
    
    Args:
        df: DataFrame with 'temp', 'wind', 'weather' columns
    
    Returns:
        DataFrame with added columns:
        - temp_filled, wind_filled: Final values (original or parsed)
        - temp_source, wind_source: 'structured' | 'parsed' | None
        - parsing_attempted: Boolean (True if parsing was attempted)
        - parsing_used: Boolean (True if parsed value actually used)
        - is_malformed_weather_string: Boolean (keyword present but parse failed)
        - weather_provenance: 'structured_both' | 'parsed_both' | 'mixed_structured+parsed' | None
    
    Example:
        >>> df = pd.DataFrame({
        ...     'temp': [72.0, None, 45.0],
        ...     'wind': [10.0, None, None],
        ...     'weather': [None, "Temp: 55° F, Wind: 12 mph", "Temp: 45° F"]
        ... })
        >>> enriched = enrich_weather(df)
        >>> enriched[['temp_filled', 'wind_filled', 'weather_provenance']].values
        array([[72.0, 10.0, 'structured_both'],
               [55.0, 12.0, 'parsed_both'],
               [45.0, None, 'structured_both']])
    """
    df = df.copy()
    
    # Initialize filled columns with original structured values
    df['temp_filled'] = df['temp']
    df['wind_filled'] = df['wind']
    
    # Track source of each value
    df['temp_source'] = df['temp'].apply(lambda x: 'structured' if pd.notna(x) else None)
    df['wind_source'] = df['wind'].apply(lambda x: 'structured' if pd.notna(x) else None)
    
    # Only parse where at least one field is missing and weather string exists
    mask = (df['temp'].isna() | df['wind'].isna()) & df['weather'].notna()
    df['parsing_attempted'] = False
    df.loc[mask, 'parsing_attempted'] = True
    
    # Parse once, cache results (efficient single-pass)
    parsed_results = {}
    malformed_flags = {}
    parsed_used_count = 0
    
    for idx, row in df.loc[mask].iterrows():
        weather_str = row['weather']
        t, w = parse_weather_string(weather_str)
        parsed_results[idx] = (t, w)
        
        # Check malformed (keyword present but parsing failed)
        weather_lower = weather_str.lower()
        malformed_temp = ('temp:' in weather_lower) and (t is None)
        malformed_wind = ('wind:' in weather_lower) and (w is None) and ('calm' not in weather_lower)
        malformed_flags[idx] = malformed_temp or malformed_wind
        
        # Fill values
        used_parsed = False
        if pd.isna(row['temp']) and t is not None:
            df.at[idx, 'temp_filled'] = t
            df.at[idx, 'temp_source'] = 'parsed'
            used_parsed = True
        
        if pd.isna(row['wind']) and w is not None:
            df.at[idx, 'wind_filled'] = w
            df.at[idx, 'wind_source'] = 'parsed'
            used_parsed = True
        
        if used_parsed:
            parsed_used_count += 1
    
    df['parsing_used'] = (df['temp_source'].eq('parsed') | df['wind_source'].eq('parsed'))
    df['is_malformed_weather_string'] = df.index.map(malformed_flags).fillna(False)
    
    # Provenance categories (3 buckets)
    tsrc = df['temp_source']
    wsrc = df['wind_source']
    conditions = [
        (tsrc == 'structured') & (wsrc == 'structured'),
        (tsrc == 'parsed') & (wsrc == 'parsed'),
        (tsrc.notna()) & (wsrc.notna()) & (tsrc != wsrc),
    ]
    choices = ['structured_both', 'parsed_both', 'mixed_structured+parsed']
    df['weather_provenance'] = pd.Series(np.select(conditions, choices, default=''), index=df.index)
    df['weather_provenance'] = df['weather_provenance'].replace('', None)
    
    return df


def add_qa_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add convenience QA columns for analysts.
    
    Creates boolean flags that enable fast filtering without reconstructing complex logic:
    - is_outdoor_dim_game: Games that should have weather (open stadiums + retractables when open)
    - is_missing_weather_after_parse: Outdoor games still missing data after parsing
    
    Args:
        df: DataFrame with:
            - 'roof' column (from dim_game)
            - 'stadium_roof_type' column (from stadium registry) — optional
            - 'temp_filled', 'wind_filled' columns (from enrich_weather)
    
    Returns:
        DataFrame with added columns:
        - is_outdoor_dim_game: Boolean
        - is_missing_weather_after_parse: Boolean
    
    Example Usage:
        >>> # Instead of complex WHERE clause:
        >>> # SELECT * FROM dim_game_weather
        >>> # WHERE roof IN ('outdoors', 'open') AND temp_filled IS NULL
        >>> 
        >>> # Use simple flag:
        >>> # SELECT * FROM dim_game_weather WHERE is_missing_weather_after_parse
    """
    df = df.copy()
    
    # Determine outdoor games
    if 'stadium_roof_type' in df.columns:
        # Use registry roof_type if available (more accurate)
        df['is_outdoor_dim_game'] = (
            df['roof'].isin(['outdoors', 'open']) | 
            ((df['stadium_roof_type'] == 'retractable') & (df['roof'] == 'open'))
        )
    else:
        # Fallback to dim_game.roof only
        df['is_outdoor_dim_game'] = df['roof'].isin(['outdoors', 'open'])
    
    # Flag outdoor games still missing weather after parsing
    df['is_missing_weather_after_parse'] = (
        df['is_outdoor_dim_game'] & 
        df['temp_filled'].isna() & 
        df['wind_filled'].isna()
    )
    
    return df


__all__ = [
    'parse_weather_string',
    'enrich_weather',
    'add_qa_columns'
]
