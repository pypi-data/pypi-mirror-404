"""
Core transformation utilities shared across all endpoints.
Contains odds calculations, datetime handling, and common data processing functions.
"""

import pandas as pd
import numpy as np
from typing import Union
import os
from commonv2 import get_logger

logger = get_logger(__name__)

# Output directory for CSV exports
from pathlib import Path
output_dir = Path.cwd() / "data"
output_dir.mkdir(exist_ok=True)

# Odds column mapping for vectorized processing
ODDS_COLUMNS = {
    'home_team_odds': 'home',
    'away_team_odds': 'away', 
    'home_team_spread_odds': 'home_spread',
    'away_team_spread_odds': 'away_spread',
    'over_odds': 'over',
    'under_odds': 'under'
}


def american_to_decimal(american_odds: Union[float, int]) -> float:
    """Convert American odds to decimal odds for proper payout calculations"""
    if pd.isna(american_odds):
        return np.nan
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

def enrich_odds_metrics(df: pd.DataFrame, stake: int = 100) -> pd.DataFrame:
    """Single-pass odds enrichment: decimal conversion + payouts + juice
    
    Replaces calculate_payouts() and calculate_juice() with a unified approach
    that eliminates duplicate American→decimal conversions and processes
    all metrics in a single pass for better performance.
    
    Args:
        df: DataFrame with American odds columns
        stake: Bet amount for payout calculations (default: 100)
    
    Returns:
        DataFrame with all odds metrics calculated
    """
    out = df.copy()
    
    # 1️⃣ Vectorized American → decimal conversion (once per column)
    decimal_cols = {}
    for odds_col, prefix in ODDS_COLUMNS.items():
        if odds_col in out.columns:
            decimal_col = f"{prefix}_decimal"
            decimal_cols[decimal_col] = out[odds_col].apply(american_to_decimal)
    
    out = out.assign(**decimal_cols)
    
    # 2️⃣ Payouts, profits & implied probabilities (single loop)
    for odds_col, prefix in ODDS_COLUMNS.items():
        decimal_col = f"{prefix}_decimal"
        if decimal_col in out.columns:
            dec_odds = out[decimal_col]
            
            # Payouts and profits
            out[f"{prefix}_payout"] = dec_odds * stake
            out[f"{prefix}_profit"] = out[f"{prefix}_payout"] - stake
            
            # Implied probabilities (as percentages)
            out[f"{prefix}_implied_prob_pct"] = (1 / dec_odds.fillna(float('inf'))) * 100
    
    # 3️⃣ Juice calculations (single pass per market type)
    # Moneyline juice
    if {'home_decimal', 'away_decimal'}.issubset(out.columns):
        home_prob = 1 / out['home_decimal'].fillna(float('inf'))
        away_prob = 1 / out['away_decimal'].fillna(float('inf'))
        out['moneyline_total_prob'] = home_prob + away_prob
        out['moneyline_juice_pct'] = (out['moneyline_total_prob'] - 1.0) * 100
    
    # Spread juice  
    if {'home_spread_decimal', 'away_spread_decimal'}.issubset(out.columns):
        home_spread_prob = 1 / out['home_spread_decimal'].fillna(float('inf'))
        away_spread_prob = 1 / out['away_spread_decimal'].fillna(float('inf'))
        out['spread_total_prob'] = home_spread_prob + away_spread_prob
        out['spread_juice_pct'] = (out['spread_total_prob'] - 1.0) * 100
    
    # Totals juice
    if {'over_decimal', 'under_decimal'}.issubset(out.columns):
        over_prob = 1 / out['over_decimal'].fillna(float('inf'))
        under_prob = 1 / out['under_decimal'].fillna(float('inf'))
        out['totals_total_prob'] = over_prob + under_prob
        out['totals_juice_pct'] = (out['totals_total_prob'] - 1.0) * 100
    
    # 4️⃣ Add legacy column names for backward compatibility
    # Map new implied prob columns to old names
    if 'home_implied_prob_pct' in out.columns:
        out['home_implied_prob'] = out['home_implied_prob_pct'] / 100
        out['away_implied_prob'] = out['away_implied_prob_pct'] / 100
    
    if 'home_spread_implied_prob_pct' in out.columns:
        out['home_spread_implied_prob'] = out['home_spread_implied_prob_pct'] / 100
        out['away_spread_implied_prob'] = out['away_spread_implied_prob_pct'] / 100
    
    if 'over_implied_prob_pct' in out.columns:
        out['over_implied_prob'] = out['over_implied_prob_pct'] / 100
        out['under_implied_prob'] = out['under_implied_prob_pct'] / 100
    
    return out

def fix_commence_time(df):
    """Convert commence_time to timezone-aware datetime in Eastern Time"""
    df = df.copy()
    df['commence_time'] = pd.to_datetime(df['commence_time'], utc=True).dt.tz_convert('America/New_York')
    return df

def write_to_csv(df: pd.DataFrame, table_name: str, split_by_market: bool = False):
    """Unified CSV export engine for all pipelines."""
    if split_by_market and 'market_key' in df.columns:
        # Specialized logic for the 'odds' pipeline
        for m in ["h2h", "spreads", "totals"]:
            m_df = df[df['market_key'] == m]
            if not m_df.empty:
                # Drop columns that are entirely null for this market to keep CSVs lean
                m_df = m_df.dropna(axis=1, how='all')
                m_df.to_csv(output_dir / f"odds_{m}.csv", index=False)
    else:
        # Standard logic for all other tables (results, teams, etc.)
        path = output_dir / f"{table_name}.csv"
        df.to_csv(path, index=False)
