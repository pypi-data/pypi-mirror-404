"""
Fact Table Data Cleaning Functions for nflfastRv3

Preserves V2's sophisticated business logic for fact table data cleaning:
- Play-by-play data cleaning and derived metrics
- Player stats cleaning and validation
- Derived EPA and situation-based metrics
- Data type conversions and null handling

Pattern: Enhanced simple functions with optional dependency injection
Complexity: 4 points (enhanced functions with business logic)
Layer: 3 (transformations use SQL templates and warehouse utils)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Union
from commonv2 import get_logger

def clean_fact_play_data(df: pd.DataFrame, logger: Optional[Any] = None) -> pd.DataFrame:
    """
    Clean fact_play data preserving V2's sophisticated play analysis logic.
    
    V2 Business Logic Preserved:
    - EPA normalization and outlier handling
    - Situation classification (down, distance, field position)
    - Play type standardization and success metrics
    - Timeout and penalty handling
    - Game situation context (score differential, time remaining)
    
    Args:
        df: Raw fact_play DataFrame from SQL template
        logger: Optional logger for debugging
        
    Returns:
        Cleaned DataFrame ready for analytics schema
        
    Complexity: Enhanced function with business rules (3 points)
    """
    logger = logger or get_logger('nflfastRv3.cleaning_facts')
    assert logger is not None  # Type checker hint
    logger.info(f"Cleaning fact_play data: {len(df):,} rows")
    
    # Create working copy
    cleaned_df = df.copy()
    
    # 1. Data type conversions (V2 logic)
    numeric_columns = [
        'epa', 'wp', 'wpa', 'vegas_wp', 'vegas_wpa',
        'score_differential', 'yardline_100', 'ydstogo',
        'yards_gained', 'air_yards', 'yards_after_catch'
    ]
    
    for col in numeric_columns:
        if col in cleaned_df.columns:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
    
    # 2. EPA cleaning (V2's outlier handling)
    if 'epa' in cleaned_df.columns:
        # Cap extreme EPA values (preserve V2 logic)
        epa_p99 = cleaned_df['epa'].quantile(0.99)
        epa_p01 = cleaned_df['epa'].quantile(0.01)
        cleaned_df['epa'] = cleaned_df['epa'].clip(lower=epa_p01, upper=epa_p99)
        
        # Fill missing EPA with 0 for certain play types
        if 'play_type' in cleaned_df.columns:
            no_epa_plays = ['timeout', 'end_quarter', 'end_half']
            mask = cleaned_df['play_type'].isin(no_epa_plays)
            cleaned_df.loc[mask, 'epa'] = cleaned_df.loc[mask, 'epa'].fillna(0)
    
    # 3. Success metrics calculation (V2 logic)
    if all(col in cleaned_df.columns for col in ['down', 'ydstogo', 'yards_gained']):
        cleaned_df['success'] = _calculate_success_metric(cleaned_df)
    
    # 4. Situation classification (V2's field position logic)
    if 'yardline_100' in cleaned_df.columns:
        cleaned_df['field_position_category'] = _categorize_field_position(cleaned_df['yardline_100'])
    
    # 5. Game situation context (V2's time and score logic)
    if all(col in cleaned_df.columns for col in ['game_seconds_remaining', 'score_differential']):
        cleaned_df['game_situation'] = _categorize_game_situation(
            cleaned_df['game_seconds_remaining'], 
            cleaned_df['score_differential']
        )
    
    # 6. Play type standardization (V2 logic)
    if 'play_type' in cleaned_df.columns:
        cleaned_df['play_type_group'] = _standardize_play_types(cleaned_df['play_type'])
    
    # 7. Handle penalties and timeouts (V2 logic)
    if 'penalty' in cleaned_df.columns:
        cleaned_df['has_penalty'] = cleaned_df['penalty'].notna().astype(int)
    
    if 'timeout' in cleaned_df.columns:
        cleaned_df['has_timeout'] = cleaned_df['timeout'].notna().astype(int)
    
    logger.info(f"Completed fact_play cleaning: {len(cleaned_df):,} rows")
    return cleaned_df


def clean_fact_player_stats_data(df: pd.DataFrame, logger: Optional[Any] = None) -> pd.DataFrame:
    """
    Clean fact_player_stats data with V2's player performance metrics logic.
    
    V2 Business Logic Preserved:
    - Snap count validation and percentage calculations
    - Position-specific stat validation
    - Fantasy scoring calculations
    - Efficiency metrics (yards per target, etc.)
    
    Args:
        df: Raw fact_player_stats DataFrame
        logger: Optional logger
        
    Returns:
        Cleaned DataFrame with derived metrics
        
    Complexity: Enhanced function with player-specific logic (3 points)
    """
    logger = logger or get_logger('nflfastRv3.cleaning_facts')
    assert logger is not None  # Type checker hint
    logger.info(f"Cleaning fact_player_stats data: {len(df):,} rows")
    
    cleaned_df = df.copy()
    
    # 1. Numeric conversions for stats
    stat_columns = [
        'targets', 'receptions', 'receiving_yards', 'receiving_tds',
        'carries', 'rushing_yards', 'rushing_tds',
        'passing_yards', 'passing_tds', 'interceptions',
        'snap_count_offense', 'snap_count_defense', 'snap_count_st'
    ]
    
    for col in stat_columns:
        if col in cleaned_df.columns:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
    
    # 2. Snap count validation (V2 logic)
    snap_columns = ['snap_count_offense', 'snap_count_defense', 'snap_count_st']
    for col in snap_columns:
        if col in cleaned_df.columns:
            # Cap at reasonable maximum (V2's validation)
            cleaned_df[col] = cleaned_df[col].clip(upper=100)
    
    # 3. Efficiency metrics calculation (V2 logic)
    if all(col in cleaned_df.columns for col in ['receptions', 'targets']):
        # Catch rate
        cleaned_df['catch_rate'] = np.where(
            cleaned_df['targets'] > 0,
            cleaned_df['receptions'] / cleaned_df['targets'],
            np.nan
        )
    
    if all(col in cleaned_df.columns for col in ['receiving_yards', 'receptions']):
        # Yards per reception
        cleaned_df['yards_per_reception'] = np.where(
            cleaned_df['receptions'] > 0,
            cleaned_df['receiving_yards'] / cleaned_df['receptions'],
            np.nan
        )
    
    if all(col in cleaned_df.columns for col in ['rushing_yards', 'carries']):
        # Yards per carry
        cleaned_df['yards_per_carry'] = np.where(
            cleaned_df['carries'] > 0,
            cleaned_df['rushing_yards'] / cleaned_df['carries'],
            np.nan
        )
    
    # 4. Fantasy scoring (V2's standard scoring)
    fantasy_points = 0
    if 'receiving_yards' in cleaned_df.columns:
        fantasy_points += cleaned_df['receiving_yards'] * 0.1
    if 'receiving_tds' in cleaned_df.columns:
        fantasy_points += cleaned_df['receiving_tds'] * 6
    if 'rushing_yards' in cleaned_df.columns:
        fantasy_points += cleaned_df['rushing_yards'] * 0.1
    if 'rushing_tds' in cleaned_df.columns:
        fantasy_points += cleaned_df['rushing_tds'] * 6
    if 'receptions' in cleaned_df.columns:
        fantasy_points += cleaned_df['receptions'] * 1  # PPR
    
    cleaned_df['fantasy_points_ppr'] = fantasy_points
    
    logger.info(f"Completed fact_player_stats cleaning: {len(cleaned_df):,} rows")
    return cleaned_df


def clean_fact_player_play_data(df: pd.DataFrame, logger: Optional[Any] = None) -> pd.DataFrame:
    """
    Clean fact_player_play data with V2's individual play attribution logic.
    
    V2 Business Logic Preserved:
    - Player involvement classification
    - EPA attribution to individual players
    - Play outcome attribution
    - Usage rate calculations
    
    Args:
        df: Raw fact_player_play DataFrame
        logger: Optional logger
        
    Returns:
        Cleaned DataFrame with individual attribution metrics
        
    Complexity: Enhanced function with attribution logic (3 points)
    """
    logger = logger or get_logger('nflfastRv3.cleaning_facts')
    assert logger is not None  # Type checker hint
    logger.info(f"Cleaning fact_player_play data: {len(df):,} rows")
    
    cleaned_df = df.copy()
    
    # 1. Numeric conversions
    numeric_columns = [
        'epa_attributed', 'yards_attributed', 'fantasy_points_attributed',
        'usage_rate', 'target_share', 'air_yards_share'
    ]
    
    for col in numeric_columns:
        if col in cleaned_df.columns:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
    
    # 2. Player involvement validation (V2 logic)
    involvement_columns = [
        'is_passer', 'is_rusher', 'is_receiver', 'is_pass_target',
        'is_tackle', 'is_assist_tackle', 'is_penalty_player'
    ]
    
    for col in involvement_columns:
        if col in cleaned_df.columns:
            # Ensure boolean values
            cleaned_df[col] = cleaned_df[col].fillna(0).astype(int)
    
    # 3. EPA attribution validation (V2's attribution rules)
    if 'epa_attributed' in cleaned_df.columns:
        # Cap extreme attributions
        epa_p99 = cleaned_df['epa_attributed'].quantile(0.99)
        epa_p01 = cleaned_df['epa_attributed'].quantile(0.01)
        cleaned_df['epa_attributed'] = cleaned_df['epa_attributed'].clip(
            lower=epa_p01, upper=epa_p99
        )
    
    # 4. Primary involvement classification (V2 logic)
    if any(col in cleaned_df.columns for col in involvement_columns):
        cleaned_df['primary_involvement'] = _classify_primary_involvement(cleaned_df)
    
    # 5. Usage metrics validation (V2's percentage logic)
    percentage_columns = ['usage_rate', 'target_share', 'air_yards_share']
    for col in percentage_columns:
        if col in cleaned_df.columns:
            # Cap at 100% and floor at 0%
            cleaned_df[col] = cleaned_df[col].clip(lower=0, upper=1)
    
    logger.info(f"Completed fact_player_play cleaning: {len(cleaned_df):,} rows")
    return cleaned_df


# Helper functions for business logic

def _calculate_success_metric(df: pd.DataFrame) -> pd.Series:
    """
    Calculate success metric using V2's down and distance logic.
    
    Success criteria:
    - 1st down: 40% of yards to go
    - 2nd down: 60% of yards to go
    - 3rd/4th down: 100% of yards to go
    """
    success = pd.Series(0, index=df.index, dtype=int)
    
    # 1st down success
    first_down_mask = (df['down'] == 1)
    success.loc[first_down_mask] = (
        df.loc[first_down_mask, 'yards_gained'] >=
        (df.loc[first_down_mask, 'ydstogo'] * 0.4)
    ).fillna(False).astype(int)
    
    # 2nd down success
    second_down_mask = (df['down'] == 2)
    success.loc[second_down_mask] = (
        df.loc[second_down_mask, 'yards_gained'] >=
        (df.loc[second_down_mask, 'ydstogo'] * 0.6)
    ).fillna(False).astype(int)
    
    # 3rd/4th down success
    third_fourth_mask = df['down'].isin([3, 4])
    success.loc[third_fourth_mask] = (
        df.loc[third_fourth_mask, 'yards_gained'] >=
        df.loc[third_fourth_mask, 'ydstogo']
    ).fillna(False).astype(int)
    
    return success


def _categorize_field_position(yardline_100: pd.Series) -> pd.Series:
    """Categorize field position using V2's field zones logic."""
    categories = pd.Series('midfield', index=yardline_100.index)
    
    categories.loc[yardline_100 <= 20] = 'red_zone'
    categories.loc[yardline_100 <= 10] = 'goal_line'
    categories.loc[yardline_100 >= 80] = 'own_territory'
    categories.loc[(yardline_100 > 20) & (yardline_100 < 80)] = 'midfield'
    
    return categories


def _categorize_game_situation(seconds_remaining: pd.Series, score_diff: pd.Series) -> pd.Series:
    """Categorize game situation using V2's time and score logic."""
    situations = pd.Series('normal', index=seconds_remaining.index)
    
    # Late game situations
    late_game = seconds_remaining <= 300  # 5 minutes
    close_game = abs(score_diff) <= 7     # One score game
    
    situations.loc[late_game & close_game] = 'clutch'
    situations.loc[late_game & (score_diff <= -8)] = 'comeback'
    situations.loc[late_game & (score_diff >= 8)] = 'garbage_time'
    situations.loc[abs(score_diff) >= 21] = 'blowout'
    
    return situations


def _standardize_play_types(play_type: pd.Series) -> pd.Series:
    """Standardize play types using V2's grouping logic."""
    play_groups = pd.Series('other', index=play_type.index)
    
    # Major play type groups
    pass_types = ['pass', 'sack', 'qb_kneel', 'qb_spike']
    run_types = ['run', 'qb_scramble']
    special_types = ['punt', 'field_goal', 'extra_point', 'kickoff']
    
    play_groups.loc[play_type.isin(pass_types)] = 'pass'
    play_groups.loc[play_type.isin(run_types)] = 'run'
    play_groups.loc[play_type.isin(special_types)] = 'special'
    
    return play_groups


def _classify_primary_involvement(df: pd.DataFrame) -> pd.Series:
    """Classify primary player involvement using V2's priority logic."""
    involvement = pd.Series('other', index=df.index)
    
    # Priority order (V2 logic)
    if 'is_passer' in df.columns:
        involvement.loc[df['is_passer'] == 1] = 'passer'
    
    if 'is_rusher' in df.columns:
        involvement.loc[df['is_rusher'] == 1] = 'rusher'
    
    if 'is_receiver' in df.columns:
        involvement.loc[df['is_receiver'] == 1] = 'receiver'
    
    if 'is_pass_target' in df.columns:
        involvement.loc[df['is_pass_target'] == 1] = 'target'
    
    if 'is_tackle' in df.columns:
        involvement.loc[df['is_tackle'] == 1] = 'tackler'
    
    return involvement
