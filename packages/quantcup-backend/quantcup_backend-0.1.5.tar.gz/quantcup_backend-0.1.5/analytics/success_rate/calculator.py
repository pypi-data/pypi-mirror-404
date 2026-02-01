"""
Success Rate Calculator

Pure functions for calculating team success rates using EPA methodology.
Extracted from analytics/strategies/epa_calculator.py following Solo Developer pattern.
"""

import pandas as pd
from typing import List

from commonv2 import get_logger
from .models import TeamSuccessRate, LeagueAverages, TeamInfo


def calculate_success_rates(play_data_df: pd.DataFrame, team_data: List[TeamInfo]) -> List[TeamSuccessRate]:
    """
    Calculate success rates for all teams from play data.
    
    Args:
        play_data_df: DataFrame with play data
        team_data: List of TeamInfo objects for enrichment
        
    Returns:
        List of TeamSuccessRate objects
    """
    logger = get_logger(__name__)
    logger.info("Calculating EPA-based success rates by team")
    
    # Validate data
    if not _validate_play_data(play_data_df):
        raise ValueError("Invalid play data")
    
    # Separate rushing and passing plays
    rush_plays = play_data_df[play_data_df['rush_attempt'] == True].copy()
    pass_plays = play_data_df[play_data_df['pass_attempt'] == True].copy()
    
    logger.info(f"Processing {len(rush_plays)} rushing plays and {len(pass_plays)} passing plays")
    
    # Calculate rushing success rates
    rush_stats = rush_plays.groupby('team').agg({
        'is_success': ['sum', 'count']
    }).round(4)
    rush_stats.columns = ['rush_successes', 'rush_attempts']
    rush_stats['rush_success_rate'] = (rush_stats['rush_successes'] / rush_stats['rush_attempts']).round(4)
    
    # Calculate passing success rates
    pass_stats = pass_plays.groupby('team').agg({
        'is_success': ['sum', 'count']
    }).round(4)
    pass_stats.columns = ['pass_successes', 'pass_attempts']
    pass_stats['pass_success_rate'] = (pass_stats['pass_successes'] / pass_stats['pass_attempts']).round(4)
    
    # Combine results
    combined_stats = pd.merge(
        rush_stats, 
        pass_stats, 
        left_index=True, 
        right_index=True, 
        how='outer'
    ).fillna(0)
    
    # Convert to domain objects with team enrichment
    team_success_rates = _create_team_success_rate_objects(combined_stats, team_data)
    
    logger.info(f"Calculated success rates for {len(team_success_rates)} teams")
    return team_success_rates


def calculate_league_averages(team_success_rates: List[TeamSuccessRate]) -> LeagueAverages:
    """
    Calculate league-wide average success rates.
    
    Args:
        team_success_rates: List of team success rates
        
    Returns:
        LeagueAverages object with weighted averages
    """
    logger = get_logger(__name__)
    logger.info("Calculating league averages")
    
    if not team_success_rates:
        raise ValueError("Cannot calculate league averages with empty team success rates")
    
    total_rush_successes = sum(team.rush_successes for team in team_success_rates)
    total_rush_attempts = sum(team.rush_attempts for team in team_success_rates)
    total_pass_successes = sum(team.pass_successes for team in team_success_rates)
    total_pass_attempts = sum(team.pass_attempts for team in team_success_rates)
    
    avg_rush_success_rate = total_rush_successes / total_rush_attempts if total_rush_attempts > 0 else 0.0
    avg_pass_success_rate = total_pass_successes / total_pass_attempts if total_pass_attempts > 0 else 0.0
    
    league_averages = LeagueAverages(
        avg_rush_success_rate=avg_rush_success_rate,
        avg_pass_success_rate=avg_pass_success_rate,
        total_rush_attempts=total_rush_attempts,
        total_pass_attempts=total_pass_attempts,
        teams_included=len(team_success_rates)
    )
    
    logger.info(f"League averages - Rush: {avg_rush_success_rate:.3f}, Pass: {avg_pass_success_rate:.3f}")
    return league_averages


def _validate_play_data(play_data_df: pd.DataFrame) -> bool:
    """
    Validate that play data contains required fields.
    
    Args:
        play_data_df: DataFrame to validate
        
    Returns:
        True if data is valid for this calculator
    """
    logger = get_logger(__name__)
    
    required_columns = ['team', 'rush_attempt', 'pass_attempt', 'is_success']
    
    for col in required_columns:
        if col not in play_data_df.columns:
            logger.error(f"Missing required column: {col}")
            return False
    
    if len(play_data_df) == 0:
        logger.error("Play data is empty")
        return False
    
    logger.info(f"Play data validation passed: {len(play_data_df)} plays")
    return True


def _create_team_success_rate_objects(combined_stats: pd.DataFrame, team_data: List[TeamInfo]) -> List[TeamSuccessRate]:
    """
    Convert pandas DataFrame to domain objects with team enrichment.
    
    Args:
        combined_stats: DataFrame with calculated success rate statistics
        team_data: List of TeamInfo objects for enrichment
        
    Returns:
        List of TeamSuccessRate objects
    """
    # Create team lookup dictionary
    team_lookup = {team.team_abbr: team for team in team_data}
    
    team_success_rates = []
    
    for team, row in combined_stats.iterrows():
        team_abbr = str(team)
        team_info = team_lookup.get(team_abbr)
        
        team_success_rate = TeamSuccessRate(
            team=team_abbr,
            team_name=team_info.team_name if team_info else team_abbr,
            team_nick=team_info.team_nick if team_info else team_abbr,
            rush_success_rate=float(row['rush_success_rate']),
            pass_success_rate=float(row['pass_success_rate']),
            rush_attempts=int(row['rush_attempts']),
            pass_attempts=int(row['pass_attempts']),
            rush_successes=int(row['rush_successes']),
            pass_successes=int(row['pass_successes']),
            team_logo_squared=team_info.team_logo_squared if team_info else None,
            team_logo_espn=team_info.team_logo_espn if team_info else None,
            team_color=team_info.team_color if team_info else None
        )
        team_success_rates.append(team_success_rate)
    
    return team_success_rates
