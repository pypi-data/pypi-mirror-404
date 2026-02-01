"""
Points Per Drive Data Loader

Simple functions for loading play data and team data.
Extracted from analytics/adapters/ following Solo Developer pattern.
"""

import pandas as pd
import requests
from pathlib import Path
from typing import List

from commonv2 import get_logger
from .models import TeamInfo


def load_play_data(engine, season: int, max_week: int) -> pd.DataFrame:
    """
    Load play-by-play data for points per drive analysis.
    
    Args:
        engine: Database engine
        season: NFL season year
        max_week: Maximum week number to include
        
    Returns:
        DataFrame with play data including drive and scoring information
    """
    logger = get_logger(__name__)
    
    try:
        # Read SQL file
        sql_path = Path("analytics/sql/points_per_drive_data.sql")
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_path}")
        
        with open(sql_path, 'r') as f:
            sql_query = f.read()
        
        # Replace parameters in SQL
        sql_query = sql_query.replace("season = 2025", f"season = {season}")
        sql_query = sql_query.replace("week <= 3", f"week <= {max_week}")
        
        # Execute query
        df = pd.read_sql(sql_query, engine)
        
        logger.info(f"Loaded {len(df)} plays for points per drive analysis (season {season}, weeks 1-{max_week})")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load play data: {e}")
        raise


def load_team_data(api_url: str = "https://quantcupapi-ra8sf.sevalla.app/api/teams") -> List[TeamInfo]:
    """
    Load team information from API.
    
    Args:
        api_url: Base URL for team data API
        
    Returns:
        List of TeamInfo objects
    """
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Fetching team data from {api_url}")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        team_data = response.json()
        teams = []
        
        for team_dict in team_data:
            team = TeamInfo(
                team_abbr=team_dict['team_abbr'],
                team_name=team_dict['team_name'],
                team_nick=team_dict['team_nick'],
                team_id=team_dict['team_id'],
                team_conf=team_dict['team_conf'],
                team_division=team_dict['team_division'],
                team_color=team_dict['team_color'],
                team_logo_squared=team_dict['team_logo_squared'],
                team_logo_espn=team_dict.get('team_logo_espn')
            )
            teams.append(team)
        
        logger.info(f"Successfully loaded {len(teams)} teams from API")
        return teams
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch team data from API: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to process team data: {e}")
        raise


def get_team_by_abbreviation(teams: List[TeamInfo], team_abbr: str) -> TeamInfo:
    """
    Get specific team by abbreviation.
    
    Args:
        teams: List of TeamInfo objects
        team_abbr: Team abbreviation
        
    Returns:
        TeamInfo object
    """
    team_abbr = team_abbr.upper()
    
    for team in teams:
        if team.team_abbr == team_abbr:
            return team
    
    raise ValueError(f"Team not found: {team_abbr}")


def validate_database_connection(engine) -> bool:
    """
    Validate that database connection is working.
    
    Args:
        engine: Database engine
        
    Returns:
        True if connection is valid, False otherwise
    """
    logger = get_logger(__name__)
    
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database connection validation failed: {e}")
        return False
