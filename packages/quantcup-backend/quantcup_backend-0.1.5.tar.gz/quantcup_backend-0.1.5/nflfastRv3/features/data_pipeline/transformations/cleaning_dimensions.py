"""
Data cleaning functions for dimensional transformations.

Pattern: Specialized cleaning functions (4 complexity points)
- Game data cleaning: 2 points
- Team data cleaning: 1 point  
- Player data cleaning: 1 point

Following REFACTORING_SPECS.md: Stay within complexity budget while preserving V2 business logic.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any


def clean_play_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize play dimension data (V2 business logic preserved).
    
    Pattern: Simple cleaning function (2 complexity points)
    - Data type conversions: 1 point
    - Business logic categorization: +1 point
    
    Args:
        df: Raw play data DataFrame
        
    Returns:
        pd.DataFrame: Cleaned play dimension data
    """
    # Convert data types
    df['game_date'] = pd.to_datetime(df['game_date'])
    df['season'] = df['season'].astype('Int64')
    df['week'] = df['week'].astype('Int64')
    
    # Handle missing values for categorical data
    df['weather'] = df['weather'].fillna('Unknown')
    df['roof'] = df['roof'].fillna('Unknown')
    df['surface'] = df['surface'].fillna('Unknown')
    df['stadium'] = df['stadium'].fillna('Unknown')
    
    # Convert numeric columns
    df['temp'] = pd.to_numeric(df['temp'], errors='coerce')
    df['wind'] = pd.to_numeric(df['wind'], errors='coerce')
    df['div_game'] = df['div_game'].astype('boolean')
    
    # Handle betting lines
    df['spread_line'] = pd.to_numeric(df['spread_line'], errors='coerce')
    df['total_line'] = pd.to_numeric(df['total_line'], errors='coerce')
    df['result'] = pd.to_numeric(df['result'], errors='coerce')
    df['total'] = pd.to_numeric(df['total'], errors='coerce')
    
    # Extract and rename game scores (required for ML feature engineering)
    # Source columns: total_home_score, total_away_score from play_by_play
    # Target columns: home_score, away_score for dim_play
    if 'total_home_score' in df.columns:
        df['home_score'] = pd.to_numeric(df['total_home_score'], errors='coerce').astype('Int64')
    else:
        df['home_score'] = pd.NA
    
    if 'total_away_score' in df.columns:
        df['away_score'] = pd.to_numeric(df['total_away_score'], errors='coerce').astype('Int64')
    else:
        df['away_score'] = pd.NA
    
    return df


def categorize_weather(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add sophisticated weather categorization (V2 business logic preserved).
    
    Pattern: Simple categorization function (1 complexity point)
    
    Args:
        df: Game data with weather column
        
    Returns:
        pd.DataFrame: Game data with weather categories
    """
    def _categorize_condition(weather):
        if pd.isna(weather) or weather == 'Unknown':
            return 'Unknown'
        
        weather_lower = str(weather).lower()
        
        if any(word in weather_lower for word in ['dome', 'indoor', 'controlled']):
            return 'Dome'
        elif any(word in weather_lower for word in ['rain', 'shower', 'drizzle']):
            return 'Rain'
        elif any(word in weather_lower for word in ['snow', 'flurr']):
            return 'Snow'
        elif any(word in weather_lower for word in ['wind', 'gust']):
            return 'Windy'
        elif any(word in weather_lower for word in ['cloud', 'overcast']):
            return 'Cloudy'
        elif any(word in weather_lower for word in ['clear', 'sunny', 'fair']):
            return 'Clear'
        else:
            return 'Other'
    
    df['weather_category'] = df['weather'].apply(_categorize_condition)
    
    # Standardize venue information
    df['venue_type'] = df['roof'].map({
        'dome': 'Dome',
        'outdoors': 'Outdoor',
        'closed': 'Dome',
        'open': 'Outdoor',
        'retractable': 'Retractable'
    }).fillna('Unknown')
    
    # Create game type indicators
    df['is_playoff'] = df['season_type'] == 'POST'
    df['is_regular_season'] = df['season_type'] == 'REG'
    df['is_preseason'] = df['season_type'] == 'PRE'
    
    return df


def clean_team_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize team data (V2 business logic preserved).
    
    Pattern: Simple cleaning function (1 complexity point)
    
    Args:
        df: Raw team data DataFrame
        
    Returns:
        pd.DataFrame: Cleaned team dimension data
    """
    # Standardize team identifiers
    df['team_id'] = df['team_abbr']
    df['team_name_primary'] = df['team_name'] if 'team_name' in df.columns else df['team_abbr']
    df['team_mascot'] = df['team_nick'] if 'team_nick' in df.columns else df['team_abbr']
    
    # Conference/Division standardization (defensive for bucket mode)
    df['conference'] = df['team_conf'] if 'team_conf' in df.columns else 'Unknown'
    df['division'] = df['team_division'] if 'team_division' in df.columns else 'Unknown'
    
    # Create full division names (V2 logic preserved)
    division_mapping = {
        'AFC East': 'AFC East', 'AFC North': 'AFC North',
        'AFC South': 'AFC South', 'AFC West': 'AFC West',
        'NFC East': 'NFC East', 'NFC North': 'NFC North',
        'NFC South': 'NFC South', 'NFC West': 'NFC West'
    }
    
    df['division_full'] = (df['conference'].astype(str) + ' ' + 
                          df['division'].astype(str))
    df['division_full'] = df['division_full'].map(division_mapping).fillna(df['division_full'])
    
    # Create full team name
    df['team_full_name'] = df['team_name_primary']
    
    return df


def standardize_stadium_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add sophisticated stadium categorization (V2 feature preserved).
    
    Pattern: Simple categorization function (1 complexity point)
    
    Args:
        df: Team data with stadium columns
        
    Returns:
        pd.DataFrame: Team data with stadium categorizations
    """
    # Dome detection (V2 logic preserved)
    if 'roof' in df.columns:
        df['is_dome'] = df['roof'].isin(['dome', 'closed', 'retractable'])
        
        # Venue type mapping
        df['venue_type'] = df['roof'].map({
            'dome': 'Dome',
            'outdoors': 'Outdoor',
            'closed': 'Dome', 
            'open': 'Outdoor',
            'retractable': 'Retractable'
        }).fillna('Unknown')
    else:
        df['is_dome'] = False
        df['venue_type'] = 'Unknown'
    
    # Surface type standardization (V2 logic preserved)
    if 'surface' in df.columns:
        surface_mapping = {
            'grass': 'Natural Grass',
            'turf': 'Artificial Turf',
            'fieldturf': 'Artificial Turf',
            'astroturf': 'Artificial Turf'
        }
        df['surface_type'] = df['surface'].str.lower().map(surface_mapping).fillna(df['surface'])
    else:
        df['surface_type'] = 'Unknown'
    
    # Stadium name cleaning
    if 'stadium' in df.columns:
        df['stadium_name'] = df['stadium'].fillna('Unknown')
    else:
        df['stadium_name'] = 'Unknown'
    
    return df


def clean_player_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize player data (V2 business logic preserved).
    
    Pattern: Simple cleaning function (1 complexity point)
    
    Args:
        df: Raw player data DataFrame
        
    Returns:
        pd.DataFrame: Cleaned player dimension data
    """
    # Handle birth dates (defensive for bucket mode)
    if 'birth_date' in df.columns:
        df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
    else:
        df['birth_date'] = pd.NaT
    
    # Convert numeric columns (only if they exist)
    numeric_columns = ['jersey_number', 'height', 'weight', 'years_of_experience',
                      'rookie_year', 'draft_number', 'current_season', 'current_week']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    
    # Standardize player names (V2 logic preserved, defensive for bucket mode)
    if 'display_name' in df.columns:
        df['player_name'] = df['display_name'].fillna(
            df.get('first_name', pd.Series()).fillna('') + ' ' + df.get('last_name', pd.Series()).fillna('')
        ).str.strip()
    elif 'player_name' not in df.columns:
        # Bucket mode may already have player_name from extraction
        if 'first_name' in df.columns and 'last_name' in df.columns:
            df['player_name'] = (df['first_name'].fillna('') + ' ' + df['last_name'].fillna('')).str.strip()
        else:
            df['player_name'] = 'Unknown'
    
    # Handle missing current team (defensive)
    if 'current_team' in df.columns:
        df['most_recent_team'] = df['current_team'].fillna('FA')  # Free Agent
    else:
        df['most_recent_team'] = 'FA'
    
    return df


def calculate_player_age(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate player age from birth date (V2 feature preserved).
    
    Pattern: Simple calculation function (1 complexity point)
    
    Args:
        df: Player data with birth_date column
        
    Returns:
        pd.DataFrame: Player data with age column
    """
    current_date = pd.Timestamp.now()
    df['age'] = df['birth_date'].apply(
        lambda x: round((current_date - x).days / 365.25, 1) if pd.notna(x) else None
    )
    return df


def standardize_positions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize position groups (V2 logic preserved).
    
    Pattern: Simple mapping function (1 complexity point)
    
    Args:
        df: Player data with position column
        
    Returns:
        pd.DataFrame: Player data with standardized position groups
    """
    position_mapping = {
        'QB': 'QB', 'RB': 'RB', 'FB': 'RB',
        'WR': 'WR', 'TE': 'TE',
        'T': 'OL', 'G': 'OL', 'C': 'OL', 'OT': 'OL', 'OG': 'OL',
        'DE': 'DL', 'DT': 'DL', 'NT': 'DL',
        'LB': 'LB', 'ILB': 'LB', 'OLB': 'LB',
        'CB': 'DB', 'S': 'DB', 'FS': 'DB', 'SS': 'DB',
        'K': 'ST', 'P': 'ST', 'LS': 'ST'
    }
    
    # Defensive for bucket mode - position_group may not exist
    if 'position' in df.columns:
        if 'position_group' in df.columns:
            df['position_group_clean'] = df['position'].map(position_mapping).fillna(df['position_group'])
        else:
            df['position_group_clean'] = df['position'].map(position_mapping).fillna('Unknown')
    else:
        df['position_group_clean'] = 'Unknown'
    
    return df
