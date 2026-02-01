"""
Points Per Drive Calculator

Pure functions for calculating team efficiency metrics.
Extracted from analytics/strategies/points_per_drive_calculator.py following Solo Developer pattern.
"""

import pandas as pd
import numpy as np
from typing import List

from commonv2 import get_logger

from .models import TeamEfficiencyMetrics, LeagueEfficiencyAverages, TeamInfo


def calculate_efficiency_metrics(play_data_df: pd.DataFrame, team_data: List[TeamInfo]) -> List[TeamEfficiencyMetrics]:
    """
    Calculate team efficiency metrics from play-by-play data.
    
    Args:
        play_data_df: DataFrame with play-by-play data
        team_data: List of TeamInfo objects for enrichment
        
    Returns:
        List of TeamEfficiencyMetrics objects
    """
    logger = get_logger(__name__)
    logger.info("Starting points per drive calculations...")
    
    # Validate data
    if not _validate_play_data(play_data_df):
        raise ValueError("Invalid play data")
    
    # Step 1: Calculate drive-level metrics
    drive_stats = _calculate_drive_metrics(play_data_df)
    logger.info(f"Calculated stats for {len(drive_stats)} drives")
    
    # Step 2: Calculate team offensive efficiency (points per drive)
    offensive_metrics = _calculate_offensive_efficiency(drive_stats)
    logger.info(f"Calculated offensive metrics for {len(offensive_metrics)} teams")
    
    # Step 3: Calculate team defensive efficiency (opponent points allowed per drive)
    defensive_metrics = _calculate_defensive_efficiency(drive_stats)
    logger.info(f"Calculated defensive metrics for {len(defensive_metrics)} teams")
    
    # Step 4: Apply opponent adjustments
    adjusted_metrics = _apply_opponent_adjustments(
        offensive_metrics, defensive_metrics, drive_stats
    )
    logger.info("Applied opponent adjustments")
    
    # Step 5: Convert to domain objects with team enrichment
    team_metrics = _create_team_efficiency_objects(adjusted_metrics, team_data)
    
    logger.info(f"Successfully calculated efficiency metrics for {len(team_metrics)} teams")
    return team_metrics


def calculate_league_averages(team_metrics: List[TeamEfficiencyMetrics]) -> LeagueEfficiencyAverages:
    """
    Calculate league-wide average efficiency metrics.
    
    Args:
        team_metrics: List of team efficiency metrics
        
    Returns:
        LeagueEfficiencyAverages object
    """
    if not team_metrics:
        raise ValueError("Cannot calculate league averages with empty team metrics")
    
    # Calculate weighted averages based on number of drives
    total_drives_offense = sum(team.total_drives_offense for team in team_metrics)
    total_drives_defense = sum(team.total_drives_defense for team in team_metrics)
    total_points_scored = sum(team.total_points_scored for team in team_metrics)
    total_points_allowed = sum(team.total_points_allowed for team in team_metrics)
    
    avg_scoring_efficiency = total_points_scored / total_drives_offense if total_drives_offense > 0 else 0.0
    avg_stopping_efficiency = total_points_allowed / total_drives_defense if total_drives_defense > 0 else 0.0
    
    # Simple averages for opponent-adjusted metrics
    avg_opponent_adjusted_scoring = float(np.mean([team.opponent_adjusted_scoring for team in team_metrics]))
    avg_opponent_adjusted_stopping = float(np.mean([team.opponent_adjusted_stopping for team in team_metrics]))
    
    return LeagueEfficiencyAverages(
        avg_scoring_efficiency_ppd=avg_scoring_efficiency,
        avg_stopping_efficiency_ppd=avg_stopping_efficiency,
        avg_opponent_adjusted_scoring=avg_opponent_adjusted_scoring,
        avg_opponent_adjusted_stopping=avg_opponent_adjusted_stopping,
        total_drives=total_drives_offense,
        total_points=total_points_scored,
        teams_included=len(team_metrics)
    )


def _validate_play_data(play_data_df: pd.DataFrame) -> bool:
    """
    Validate that the play data contains required columns for PPD analysis.
    
    Args:
        play_data_df: DataFrame with play-by-play data
        
    Returns:
        True if data is valid, False otherwise
    """
    logger = get_logger(__name__)
    
    required_columns = [
        'team', 'opponent', 'game_id', 'drive', 
        'points_scored', 'season', 'week'
    ]
    
    missing_columns = [col for col in required_columns if col not in play_data_df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    
    if len(play_data_df) == 0:
        logger.error("Play data is empty")
        return False
    
    logger.info(f"Play data validation passed: {len(play_data_df)} plays")
    return True


def _calculate_drive_metrics(play_data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Group plays into drives and calculate drive-level outcomes.
    
    Args:
        play_data_df: Raw play-by-play data
        
    Returns:
        DataFrame with drive-level statistics
    """
    # Group by team, opponent, game, and drive
    drive_stats = play_data_df.groupby(['team', 'opponent', 'game_id', 'drive']).agg({
        'points_for_posteam': 'sum',  # Points scored by offense (posteam)
        'points_for_defteam': 'sum',  # Points scored by defense (defteam) - safeties
        'points_scored': 'sum',       # Total points scored on this drive (backward compatibility)
        'play_id': 'count',           # Number of plays in drive
        'epa': 'sum',                # Total EPA for drive
        'season': 'first',            # Metadata
        'week': 'first',
        'game_date': 'first'
    }).reset_index()
    
    # Rename play_id count to play_count for clarity
    drive_stats = drive_stats.rename(columns={'play_id': 'play_count'})
    
    # Calculate drive points correctly attributed to each team
    drive_stats['drive_points_offense'] = drive_stats['points_for_posteam']
    drive_stats['drive_points_defense'] = drive_stats['points_for_defteam']
    
    # Add drive outcome indicators
    drive_stats['scored_points'] = drive_stats['points_for_posteam'] > 0
    drive_stats['drive_points'] = drive_stats['points_for_posteam']  # Use offensive points for drive success
    
    return drive_stats


def _calculate_offensive_efficiency(drive_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate offensive efficiency metrics (points per drive) for each team.
    
    Args:
        drive_stats: Drive-level statistics
        
    Returns:
        DataFrame with offensive efficiency metrics
    """
    # Calculate offensive metrics including defensive points scored (safeties)
    offensive_metrics = drive_stats.groupby('team').agg({
        'drive_points': ['sum', 'count', 'mean'],  # Offensive points, drives, PPD
        'drive_points_defense': 'sum',             # Defensive points scored (safeties)
        'scored_points': 'sum',                    # Drives that scored
        'epa': 'sum'                              # Total offensive EPA
    }).reset_index()
    
    # Flatten column names
    offensive_metrics.columns = [
        'team', 'total_offensive_points', 'total_drives_offense', 
        'scoring_efficiency_ppd', 'total_defensive_points', 'scoring_drives', 'total_epa_offense'
    ]
    
    # Calculate total points scored by team (offensive + defensive)
    offensive_metrics['total_points_scored'] = (
        offensive_metrics['total_offensive_points'] + 
        offensive_metrics['total_defensive_points']
    )
    
    return offensive_metrics


def _calculate_defensive_efficiency(drive_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate defensive efficiency metrics (opponent points per drive allowed).
    
    Args:
        drive_stats: Drive-level statistics
        
    Returns:
        DataFrame with defensive efficiency metrics
    """
    # Flip perspective: team's defense = opponent's offense against them
    defensive_stats = drive_stats.copy()
    defensive_stats = defensive_stats.rename(columns={
        'team': 'offense_team',
        'opponent': 'defense_team'
    })
    
    # Calculate points allowed (offensive points by opponents) and points scored by defense (safeties)
    defensive_metrics = defensive_stats.groupby('defense_team').agg({
        'drive_points': ['sum', 'count', 'mean'],  # Offensive points allowed, drives faced, PPDA
        'scored_points': 'sum',                    # Drives that scored against
        'drive_points_defense': 'sum',             # Points scored by defense (safeties)
        'epa': 'sum'                              # Total EPA allowed
    }).reset_index()
    
    # Flatten column names
    defensive_metrics.columns = [
        'team', 'total_points_allowed', 'total_drives_defense',
        'stopping_efficiency_ppd', 'scoring_drives_allowed', 'defensive_points_scored', 'total_epa_defense'
    ]
    
    return defensive_metrics


def _apply_opponent_adjustments(
    offensive_metrics: pd.DataFrame, 
    defensive_metrics: pd.DataFrame,
    drive_stats: pd.DataFrame
) -> pd.DataFrame:
    """
    Apply opponent strength adjustments to efficiency metrics.
    
    Args:
        offensive_metrics: Team offensive efficiency metrics
        defensive_metrics: Team defensive efficiency metrics
        drive_stats: Drive-level statistics for opponent strength calculation
        
    Returns:
        DataFrame with opponent-adjusted metrics
    """
    # Calculate team strength baselines
    team_offensive_strength = drive_stats.groupby('team')['drive_points'].mean()
    
    # Defensive strength: points per drive allowed by each team (flip perspective)
    defensive_stats = drive_stats.copy()
    defensive_stats = defensive_stats.rename(columns={
        'team': 'offense_team',
        'opponent': 'defense_team'
    })
    team_defensive_strength = defensive_stats.groupby('defense_team')['drive_points'].mean()
    
    # League averages for normalization
    league_avg_ppd = drive_stats['drive_points'].mean()
    
    # Merge offensive and defensive metrics
    combined_metrics = pd.merge(
        offensive_metrics, 
        defensive_metrics, 
        on='team', 
        how='outer'
    ).fillna(0)
    
    # Calculate opponent strength adjustments
    team_opponent_def_strength = []
    for team in combined_metrics['team']:
        team_games = drive_stats[drive_stats['team'] == team]
        
        total_weighted_strength = 0.0
        total_drives = 0
        
        for opponent in team_games['opponent'].unique():
            opponent_games = team_games[team_games['opponent'] == opponent]
            drives_vs_opponent = len(opponent_games)
            
            if opponent in team_defensive_strength.index:
                opponent_def_strength = team_defensive_strength[opponent]
                total_weighted_strength += opponent_def_strength * drives_vs_opponent
                total_drives += drives_vs_opponent
        
        avg_opponent_def_strength = (total_weighted_strength / total_drives) if total_drives > 0 else league_avg_ppd
        
        team_opponent_def_strength.append({
            'team': team,
            'avg_opponent_def_strength': avg_opponent_def_strength
        })
    
    opponent_def_df = pd.DataFrame(team_opponent_def_strength)
    combined_metrics = pd.merge(combined_metrics, opponent_def_df, on='team', how='left')
    
    # Calculate opponent offensive strength for defensive adjustments
    team_opponent_off_strength = []
    for team in combined_metrics['team']:
        team_games = drive_stats[drive_stats['opponent'] == team]
        
        total_weighted_strength = 0.0
        total_drives = 0
        
        for opponent in team_games['team'].unique():
            opponent_games = team_games[team_games['team'] == opponent]
            drives_vs_opponent = len(opponent_games)
            
            if opponent in team_offensive_strength.index:
                opponent_off_strength = team_offensive_strength[opponent]
                total_weighted_strength += opponent_off_strength * drives_vs_opponent
                total_drives += drives_vs_opponent
        
        avg_opponent_off_strength = (total_weighted_strength / total_drives) if total_drives > 0 else league_avg_ppd
        
        team_opponent_off_strength.append({
            'team': team,
            'avg_opponent_off_strength': avg_opponent_off_strength
        })
    
    opponent_off_df = pd.DataFrame(team_opponent_off_strength)
    combined_metrics = pd.merge(combined_metrics, opponent_off_df, on='team', how='left')
    
    # Fill any missing values with league average
    combined_metrics['avg_opponent_def_strength'] = combined_metrics['avg_opponent_def_strength'].fillna(league_avg_ppd)
    combined_metrics['avg_opponent_off_strength'] = combined_metrics['avg_opponent_off_strength'].fillna(league_avg_ppd)
    
    # Apply opponent adjustments
    raw_adjusted_scoring = (
        combined_metrics['scoring_efficiency_ppd'] * 
        league_avg_ppd / combined_metrics['avg_opponent_def_strength']
    )
    
    normalized_ppda = (
        combined_metrics['stopping_efficiency_ppd'] * 
        league_avg_ppd / combined_metrics['avg_opponent_off_strength']
    )
    
    # Center around league average
    combined_metrics['opponent_adjusted_scoring'] = raw_adjusted_scoring - league_avg_ppd
    combined_metrics['opponent_adjusted_stopping'] = league_avg_ppd - normalized_ppda
    
    return combined_metrics


def _create_team_efficiency_objects(metrics_df: pd.DataFrame, team_data: List[TeamInfo]) -> List[TeamEfficiencyMetrics]:
    """
    Convert pandas DataFrame to domain objects with team enrichment.
    
    Args:
        metrics_df: DataFrame with calculated efficiency metrics
        team_data: List of TeamInfo objects for enrichment
        
    Returns:
        List of TeamEfficiencyMetrics objects
    """
    # Create team lookup dictionary
    team_lookup = {team.team_abbr: team for team in team_data}
    
    team_metrics = []
    
    for _, row in metrics_df.iterrows():
        team_abbr = row['team']
        team_info = team_lookup.get(team_abbr)
        
        team_metric = TeamEfficiencyMetrics(
            team=team_abbr,
            team_name=team_info.team_name if team_info else team_abbr,
            team_nick=team_info.team_nick if team_info else team_abbr,
            scoring_efficiency_ppd=float(row['scoring_efficiency_ppd']),
            stopping_efficiency_ppd=float(row['stopping_efficiency_ppd']),
            opponent_adjusted_scoring=float(row['opponent_adjusted_scoring']),
            opponent_adjusted_stopping=float(row['opponent_adjusted_stopping']),
            total_drives_offense=int(row['total_drives_offense']),
            total_drives_defense=int(row['total_drives_defense']),
            total_points_scored=int(row['total_points_scored']),
            total_points_allowed=int(row['total_points_allowed']),
            team_logo_squared=team_info.team_logo_squared if team_info else None,
            team_logo_espn=team_info.team_logo_espn if team_info else None,
            team_color=team_info.team_color if team_info else None
        )
        team_metrics.append(team_metric)
    
    return team_metrics
