import pandas as pd
import numpy as np
from typing import Union

from commonv2.core.logging import setup_logger
from odds_api.core.types import SelectionSide, SelectionType

# Setup logger
logger = setup_logger('odds_api.transform.analytics', project_name='ODDS_API')


def validate_odds_sanity(fact_odds: pd.DataFrame) -> pd.DataFrame:
    """
    Flag suspicious odds values.
    
    Returns DataFrame of anomalies.
    """
    anomalies = fact_odds[
        (fact_odds['odds_price'].abs() > 10000) |  # Extreme odds
        (fact_odds['implied_probability'] > 1) |  # Impossible probability (must be 0-1)
        (fact_odds['implied_probability'] < 0)
    ].copy()
    
    if not anomalies.empty:
        logger.warning(f"⚠️  {len(anomalies)} anomalous odds detected")
        # Add flag to main dataframe
        fact_odds['is_anomalous'] = fact_odds.index.isin(anomalies.index)
    else:
        fact_odds['is_anomalous'] = False
    
    return anomalies

def deduplicate_facts(fact_odds: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate odds records based on composite key with stable selection keys."""
    logger.info(f"Starting deduplication on {len(fact_odds)} records")
    
    # Fill NaN values for deduplication (H2H markets don't have points, some markets don't have participant_id)
    fact_odds['_odds_point_filled'] = fact_odds['odds_point'].fillna(-999999)
    fact_odds['_participant_id_filled'] = fact_odds['participant_id'].fillna('__none__')
    
    composite_key = [
        'event_id', 'snapshot_timestamp', 'bookmaker_key',
        'market_key', 'selection_type', '_participant_id_filled', 'side', '_odds_point_filled'
    ]
    
    before_count = len(fact_odds)
    fact_odds_deduped = fact_odds.drop_duplicates(subset=composite_key, keep='last')
    after_count = len(fact_odds_deduped)
    
    # Drop temporary columns
    fact_odds_deduped = fact_odds_deduped.drop(columns=['_odds_point_filled', '_participant_id_filled'])
    
    if before_count != after_count:
        logger.warning(f"⚠️  Removed {before_count - after_count} duplicate records ({(before_count - after_count) / before_count * 100:.2f}%)")
    else:
        logger.info("✅ No duplicates found")
    
    return fact_odds_deduped

def add_opening_closing_lines(fact_odds: pd.DataFrame, pregame_scheduled_minutes: int = 15) -> pd.DataFrame:
    """
    Add TRUE opening and closing line columns (per bookmaker).
    
    IMPORTANT DISTINCTION:
    
    TRUE OPENING LINE: First line when THIS BOOKMAKER opened this specific market
                       - Earliest snapshot for (event + bookmaker + market + selection)
                       - Could be weeks before kickoff
                       - Varies by bookmaker (some open earlier than others)
                       - NOT the same as your "OPEN_T6D" snapshot!
    
    WEEK-OPEN (T-6d): Scheduled snapshot 6 days before kickoff (stored in snapshot_role column)
                      - Consistent timing across all games
                      - May NOT be the true sportsbook opener if market opened earlier
                      - Use snapshot_role = 'OPEN_T6D' to filter these snapshots
    
    TRUE CLOSING LINE: Last bookmaker update BEFORE kickoff
                       - Uses bookmaker_last_update, NOT snapshot_timestamp
                       - Captures TRUE last pre-game line regardless of when you polled
                       - Used for CLV (Closing Line Value) calculation
                       - Critical for historical backfills captured post-game
    
    This function computes TRUE opening/closing per bookmaker, not snapshot roles!
    
    UPDATED (V2):
    - Uses bookmaker_last_update for closing line detection (not snapshot_timestamp)
    - Captures TRUE closing line even when backfill runs hours after game
    - Adds closing_bookmaker_update_time and closing_captured_at for tracking
    - Calculates closing_line_seconds_before_kickoff for accuracy metrics
    
    Args:
        fact_odds: DataFrame with odds data
        pregame_scheduled_minutes: Legacy parameter (kept for compatibility, not used)
    """
    logger.info(f"Computing opening/closing lines for {len(fact_odds)} records")
    
    # Ensure timestamps are datetime with UTC timezone
    fact_odds['snapshot_timestamp'] = pd.to_datetime(fact_odds['snapshot_timestamp'], utc=True)
    fact_odds['commence_time'] = pd.to_datetime(fact_odds['commence_time'], utc=True)
    fact_odds['bookmaker_last_update'] = pd.to_datetime(fact_odds['bookmaker_last_update'], utc=True)
    
    # Fill NaN values for grouping
    fact_odds['_odds_point_filled'] = fact_odds['odds_point'].fillna(-999999)
    fact_odds['_participant_id_filled'] = fact_odds['participant_id'].fillna('__none__')
    
    # UPDATED: Group by stable selection keys to track line history
    group_cols = ['event_id', 'bookmaker_key', 'market_key',
                  'selection_type', '_participant_id_filled', 'side', '_odds_point_filled']
    
    # Sort by timestamp
    fact_odds = fact_odds.sort_values(group_cols + ['snapshot_timestamp'])
    
    # Count unique outcomes being tracked
    n_unique_outcomes = fact_odds.groupby(group_cols).ngroups
    logger.info(f"Tracking {n_unique_outcomes} unique outcomes across {fact_odds['event_id'].nunique()} events")
    
    # OPENING LINE: Get FIRST line when bookmaker opened betting
    # This is per outcome (e.g., Chiefs -3 may open before Chiefs -2.5)
    opening_lines = fact_odds.groupby(group_cols).agg({
        'snapshot_timestamp': 'min',
        'odds_price': 'first'
    }).reset_index()
    opening_lines = opening_lines.rename(columns={
        'snapshot_timestamp': 'opening_timestamp',
        'odds_price': 'opening_line'
    })
    logger.info(f"✅ Computed opening lines for {len(opening_lines)} outcomes")
    
    # CLOSING LINE: Get LAST bookmaker update BEFORE kickoff (TRUE CLOSE for CLV)
    # Uses bookmaker_last_update to capture TRUE pre-game line regardless of when we polled
    closing_window_odds = fact_odds[
        fact_odds['bookmaker_last_update'] < fact_odds['commence_time']
    ].copy()
    
    pre_game_pct = (len(closing_window_odds) / len(fact_odds) * 100) if len(fact_odds) > 0 else 0
    logger.info(f"Found {len(closing_window_odds)} pre-game records ({pre_game_pct:.1f}%) using bookmaker_last_update")
    
    if not closing_window_odds.empty:
        closing_lines = closing_window_odds.groupby(group_cols).agg({
            'bookmaker_last_update': 'max',  # Last time bookmaker updated pre-game
            'odds_price': 'last',
            'snapshot_timestamp': 'last'  # When we happened to capture it
        }).reset_index()
        closing_lines = closing_lines.rename(columns={
            'bookmaker_last_update': 'closing_bookmaker_update_time',
            'odds_price': 'closing_line',
            'snapshot_timestamp': 'closing_captured_at'
        })
        
        # Calculate statistics about closing line timing
        # Ensure UTC timezone for grouped commence_time values
        commence_times = pd.to_datetime(
            closing_window_odds.groupby(group_cols)['commence_time'].first().values,
            utc=True
        )
        closing_lines['_seconds_before_kickoff'] = (
            commence_times - closing_lines['closing_bookmaker_update_time']
        ).dt.total_seconds()
        
        avg_seconds = closing_lines['_seconds_before_kickoff'].mean()
        min_seconds = closing_lines['_seconds_before_kickoff'].min()
        max_seconds = closing_lines['_seconds_before_kickoff'].max()
        
        logger.info(f"✅ Computed closing lines for {len(closing_lines)} outcomes")
        logger.info(f"   Closing line timing (before kickoff): avg={avg_seconds/60:.1f}min, min={min_seconds/60:.1f}min, max={max_seconds/60:.1f}min")
        
        closing_lines = closing_lines.drop(columns=['_seconds_before_kickoff'])
    else:
        # Fallback: No pre-game data at all (rare edge case)
        logger.warning("⚠️  No pre-game bookmaker updates found - cannot determine closing line")
        closing_lines = pd.DataFrame(
            columns=group_cols + ['closing_bookmaker_update_time', 'closing_line', 'closing_captured_at']
        )
    
    # Merge both
    fact_odds = fact_odds.merge(
        opening_lines[group_cols + ['opening_line', 'opening_timestamp']],
        on=group_cols,
        how='left'
    )
    fact_odds = fact_odds.merge(
        closing_lines[group_cols + ['closing_line', 'closing_bookmaker_update_time', 'closing_captured_at']],
        on=group_cols,
        how='left'
    )
    
    # Calculate how close to kickoff the TRUE closing line was
    fact_odds['closing_line_seconds_before_kickoff'] = (
        (fact_odds['commence_time'] - fact_odds['closing_bookmaker_update_time'])
        .dt.total_seconds()
    )
    
    # Drop the temporary filled columns
    fact_odds = fact_odds.drop(columns=['_odds_point_filled', '_participant_id_filled'])
    
    # Calculate movement metrics
    # Keep raw deltas for reference (American odds space - non-linear)
    fact_odds['line_moved_from_open_raw'] = fact_odds['odds_price'] - fact_odds['opening_line']
    fact_odds['opening_to_close_movement_raw'] = fact_odds['closing_line'] - fact_odds['opening_line']
    fact_odds['clv_vs_close_raw'] = fact_odds['odds_price'] - fact_odds['closing_line']
    
    # Add probability-space metrics (analytically meaningful - linear scale)
    def calc_implied_prob(price):
        """Convert American odds to implied probability (vectorized)."""
        return np.where(
            price > 0,
            100 / (price + 100),
            np.abs(price) / (np.abs(price) + 100)
        )
    
    # Convert opening/closing lines to probability space
    fact_odds['opening_line_prob'] = calc_implied_prob(fact_odds['opening_line'])
    fact_odds['closing_line_prob'] = calc_implied_prob(fact_odds['closing_line'])
    
    # Calculate probability-space movements (percentage point changes)
    fact_odds['prob_move_from_open'] = (
        fact_odds['implied_probability'] - fact_odds['opening_line_prob']
    )
    fact_odds['prob_move_open_to_close'] = (
        fact_odds['closing_line_prob'] - fact_odds['opening_line_prob']
    )
    fact_odds['clv_vs_close_prob'] = (
        fact_odds['implied_probability'] - fact_odds['closing_line_prob']
    )
    
    # Flag actual opening/closing snapshots
    fact_odds['is_true_opening'] = (
        fact_odds['snapshot_timestamp'] == fact_odds['opening_timestamp']
    )
    fact_odds['is_true_closing'] = (
        fact_odds['bookmaker_last_update'] == fact_odds['closing_bookmaker_update_time']
    )
    
    # Log summary stats
    n_true_opening = fact_odds['is_true_opening'].sum()
    n_true_closing = fact_odds['is_true_closing'].sum()
    logger.info(f"Flagged {n_true_opening} TRUE opening snapshots and {n_true_closing} TRUE closing snapshots")
    
    # Log line movement stats (both raw and probability-space)
    if 'opening_to_close_movement_raw' in fact_odds.columns:
        movements = fact_odds.dropna(subset=['opening_to_close_movement_raw'])
        if not movements.empty:
            avg_movement_raw = movements['opening_to_close_movement_raw'].abs().mean()
            max_movement_raw = movements['opening_to_close_movement_raw'].abs().max()
            logger.info(f"Line movement stats (raw odds): avg={avg_movement_raw:.1f} points, max={max_movement_raw:.1f} points")
    
    if 'prob_move_open_to_close' in fact_odds.columns:
        prob_movements = fact_odds.dropna(subset=['prob_move_open_to_close'])
        if not prob_movements.empty:
            avg_prob_movement = prob_movements['prob_move_open_to_close'].abs().mean()
            max_prob_movement = prob_movements['prob_move_open_to_close'].abs().max()
            logger.info(f"Line movement stats (probability): avg={avg_prob_movement:.4f} ({avg_prob_movement*100:.2f}pp), max={max_prob_movement:.4f} ({max_prob_movement*100:.2f}pp)")
    
    return fact_odds

def add_implied_probability(fact_odds: pd.DataFrame) -> pd.DataFrame:
    """Add implied probability column (0-1 scale)."""
    def american_to_implied_prob(american_odds: Union[float, int]) -> float:
        if pd.isna(american_odds):
            return np.nan
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)
    
    fact_odds['implied_probability'] = fact_odds['odds_price'].apply(american_to_implied_prob)
    return fact_odds

def add_snapshot_flags(fact_odds: pd.DataFrame) -> pd.DataFrame:
    """
    Add comprehensive snapshot flags for analysis.
    
    UPDATED (V2): Fixed is_last_snapshot bug that incorrectly marked all IN_GAME rows as last
    
    Flags Added:
    - is_first_overall: First snapshot captured for this outcome
    - is_last_overall: Last snapshot captured for this outcome (FIXED: was marking all in-game as last)
    - is_last_in_role: Last snapshot within specific role (e.g., last IN_GAME, last PREGAME_SCHEDULED)
    
    Note: This tracks snapshot capture timing, NOT bookmaker update timing (see is_true_opening/is_true_closing)
    """
    fact_odds['snapshot_timestamp'] = pd.to_datetime(fact_odds['snapshot_timestamp'])
    fact_odds['commence_time'] = pd.to_datetime(fact_odds['commence_time'])
    
    # Fill NaN values for grouping (needed for stable selection keys)
    fact_odds['_odds_point_filled'] = fact_odds['odds_point'].fillna(-999999)
    fact_odds['_participant_id_filled'] = fact_odds['participant_id'].fillna('__none__')
    
    # Group by stable selection keys (per outcome tracking)
    group_cols = ['event_id', 'bookmaker_key', 'market_key',
                  'selection_type', '_participant_id_filled', 'side', '_odds_point_filled']
    
    # FIXED: Only mark the actual last snapshot per outcome as last (not all in-game)
    fact_odds['is_first_overall'] = (
        fact_odds['snapshot_timestamp'] ==
        fact_odds.groupby(group_cols)['snapshot_timestamp'].transform('min')
    )
    
    fact_odds['is_last_overall'] = (
        fact_odds['snapshot_timestamp'] ==
        fact_odds.groupby(group_cols)['snapshot_timestamp'].transform('max')
    )
    
    # Add role-specific last snapshot flag (useful for IN_GAME analysis)
    if 'snapshot_role' in fact_odds.columns:
        fact_odds['is_last_in_role'] = (
            fact_odds['snapshot_timestamp'] ==
            fact_odds.groupby(group_cols + ['snapshot_role'])['snapshot_timestamp'].transform('max')
        )
    else:
        fact_odds['is_last_in_role'] = False
        logger.warning("⚠️  snapshot_role column not found - is_last_in_role will be False for all rows")
    
    # Clean up temporary columns
    fact_odds = fact_odds.drop(columns=['_odds_point_filled', '_participant_id_filled'])
    
    # Log summary
    n_first = fact_odds['is_first_overall'].sum()
    n_last = fact_odds['is_last_overall'].sum()
    n_last_in_role = fact_odds['is_last_in_role'].sum()
    logger.info(f"Flagged {n_first} first snapshots, {n_last} last snapshots, {n_last_in_role} last-in-role snapshots")
    
    return fact_odds

def add_best_odds_tracking(fact_odds: pd.DataFrame) -> pd.DataFrame:
    """
    Add best odds tracking across bookmakers using implied probability (linear scale).
    
    IMPORTANT: Ranks based on implied_probability, NOT raw American odds
    - American odds are non-linear (-110 vs +120 don't compare linearly)
    - Implied probability is linear and analytically meaningful
    - Lower implied probability = better value for bettors = rank 1
    
    Added Columns:
    - rank_by_odds_quality: Rank based on implied probability (1 = best odds)
    - is_best_odds: Boolean flag for rank 1 (best available odds across books)
    
    Note: Ranking is ACROSS bookmakers for same outcome at same snapshot
    """
    fact_odds['_odds_point_filled'] = fact_odds['odds_point'].fillna(-999999)
    fact_odds['_participant_id_filled'] = fact_odds['participant_id'].fillna('__none__')
    
    # Rank based on implied probability (linear scale)
    # ascending=True because LOWER implied prob = BETTER odds for bettor
    fact_odds['rank_by_odds_quality'] = fact_odds.groupby(
        ['snapshot_timestamp', 'event_id', 'market_key',
         'selection_type', '_participant_id_filled', 'side', '_odds_point_filled']
    )['implied_probability'].rank(method='dense', ascending=True).astype('Int64')
    
    # Flag best odds across bookmakers
    fact_odds['is_best_odds'] = (fact_odds['rank_by_odds_quality'] == 1)
    
    fact_odds = fact_odds.drop(columns=['_odds_point_filled', '_participant_id_filled'])
    
    # Log summary
    n_best_odds = fact_odds['is_best_odds'].sum()
    n_outcomes = fact_odds.groupby(['snapshot_timestamp', 'event_id', 'market_key', 'selection_type', 'side']).ngroups
    logger.info(f"Identified {n_best_odds} best odds instances across {n_outcomes} outcome groups")
    
    return fact_odds

def add_vig_metrics(fact_odds: pd.DataFrame) -> pd.DataFrame:
    """
    Add overround (vig) and no-vig probabilities per snapshot/bookmaker/market.
    
    Calculates:
    - overround: The bookmaker's margin (how much total implied probability exceeds 100%)
    - no_vig_probability: Fair probability after removing the vig (normalized to sum = 1.0)
    
    Example:
        Market with two outcomes:
        - Outcome A: -130 odds → 0.5652 implied prob
        - Outcome B: +110 odds → 0.4762 implied prob
        - Sum: 1.0414 → Overround: 4.14% vig
        
        No-vig probabilities:
        - Outcome A: 0.5652 / 1.0414 = 0.5427
        - Outcome B: 0.4762 / 1.0414 = 0.4573
        - Sum: 1.0000 ✅
    
    Returns:
        DataFrame with added columns: overround, no_vig_probability
    """
    logger.info(f"Computing vig metrics for {len(fact_odds)} records")
    
    # Group by market instance (all outcomes in same market at same snapshot)
    vig_groups = fact_odds.groupby([
        'event_id', 'snapshot_timestamp', 'bookmaker_key', 'market_key'
    ])
    
    # Sum of implied probabilities (should be > 1.0 due to vig)
    fact_odds['_market_prob_sum'] = vig_groups['implied_probability'].transform('sum')
    
    # Calculate overround (vig percentage)
    fact_odds['overround'] = fact_odds['_market_prob_sum'] - 1.0
    
    # No-vig probability (normalize to sum = 1.0)
    # Handle edge case where sum might be exactly 1.0 or less (rare)
    fact_odds['no_vig_probability'] = np.where(
        fact_odds['_market_prob_sum'] > 0,
        fact_odds['implied_probability'] / fact_odds['_market_prob_sum'],
        fact_odds['implied_probability']  # Fallback to raw probability
    )
    
    # Drop temporary column
    fact_odds = fact_odds.drop(columns=['_market_prob_sum'])
    
    # Log summary statistics
    if 'overround' in fact_odds.columns:
        avg_vig = fact_odds.groupby(['event_id', 'snapshot_timestamp', 'bookmaker_key', 'market_key'])['overround'].first().mean()
        min_vig = fact_odds.groupby(['event_id', 'snapshot_timestamp', 'bookmaker_key', 'market_key'])['overround'].first().min()
        max_vig = fact_odds.groupby(['event_id', 'snapshot_timestamp', 'bookmaker_key', 'market_key'])['overround'].first().max()
        
        logger.info(f"Vig statistics: avg={avg_vig*100:.2f}%, min={min_vig*100:.2f}%, max={max_vig*100:.2f}%")
    
    return fact_odds

def add_odds_movement_metrics(fact_odds: pd.DataFrame) -> pd.DataFrame:
    """
    Add odds movement metrics.
    
    UPDATED: Uses stable selection keys instead of outcome_name
    """
    fact_odds['_odds_point_filled'] = fact_odds['odds_point'].fillna(-999999)
    fact_odds['_participant_id_filled'] = fact_odds['participant_id'].fillna('__none__')
    
    fact_odds_sorted = fact_odds.sort_values([
        'event_id', 'bookmaker_key', 'market_key', 'selection_type', '_participant_id_filled', 'side', '_odds_point_filled', 'snapshot_timestamp'
    ])
    
    fact_odds_sorted['previous_odds_price'] = fact_odds_sorted.groupby(
        ['event_id', 'bookmaker_key', 'market_key', 'selection_type', '_participant_id_filled', 'side', '_odds_point_filled']
    )['odds_price'].shift(1)
    
    fact_odds_sorted['odds_change_from_previous'] = (
        fact_odds_sorted['odds_price'] - fact_odds_sorted['previous_odds_price']
    )
    
    def get_direction(change):
        if pd.isna(change):
            return 'first_snapshot'
        elif change > 0:
            return 'up'
        elif change < 0:
            return 'down'
        else:
            return 'unchanged'
    
    fact_odds_sorted['odds_change_direction'] = (
        fact_odds_sorted['odds_change_from_previous'].apply(get_direction)
    )
    
    fact_odds = fact_odds_sorted.drop(columns=['previous_odds_price', '_odds_point_filled', '_participant_id_filled'])
    return fact_odds

