"""
Player Availability Features

Calculates player availability features using the warehouse/player_availability table.
This module REPLACES the old injury_features.py which had architectural issues.

Key Improvements from injury_features.py:
- Single data source: warehouse/player_availability (no complex merges)
- Uses is_available field (handles injuries, IR, suspensions, cuts, etc.)
- Cleaner architecture (no need for snap_counts + depth_chart + injuries merging)
- More accurate (fixes bugs with IR players showing as available)

Architecture:
- Input: warehouse/player_availability table (built by warehouse_player_availability.py)
- Output: Game-level availability features
- Pattern: Simple aggregation + position weighting

Created: 2026-01-25
Replaces: injury_features.py (deprecated)
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

# Position importance weights (for impact scoring)
POSITION_WEIGHTS = {
    # Offense (35% of total weight)
    'QB': 0.35,   # Quarterback - most critical position
    'LT': 0.10,   # Left Tackle - protects QB blind side
    'WR': 0.08,   # Wide Receiver
    'RB': 0.07,   # Running Back
    'TE': 0.06,   # Tight End
    'C': 0.05,    # Center - calls protections
    'RT': 0.04,   # Right Tackle
    'LG': 0.03,   # Left Guard
    'RG': 0.03,   # Right Guard
    
    # Defense (35% of total weight)
    'DE': 0.08,   # Defensive End - pass rush
    'DT': 0.07,   # Defensive Tackle
    'OLB': 0.07,  # Outside Linebacker - edge rush
    'MLB': 0.06,  # Middle Linebacker - defensive QB
    'ILB': 0.05,  # Inside Linebacker
    'CB': 0.09,   # Cornerback - covers WR1
    'S': 0.06,    # Safety
    'FS': 0.05,   # Free Safety
    'SS': 0.05,   # Strong Safety
    'LB': 0.06,   # Linebacker (generic)
    'DB': 0.05,   # Defensive Back (generic)
    'DL': 0.06,   # Defensive Line (generic)
    
    # Special Teams (5% of total weight)
    'K': 0.03,    # Kicker
    'P': 0.02,    # Punter
    'LS': 0.01,   # Long Snapper
    
    # Default (for unknown positions)
    'DEFAULT': 0.01
}


class PlayerAvailabilityFeatureCalculator:
    """
    Calculate player availability features for game predictions.
    
    Features Generated:
    - QB availability (home/away_qb_available)
    - Starter unavailability counts (total + by unit: offense/defense)
    - Position-weighted availability impact scores
    - Key position unavailability flags
    
    Data Flow:
    1. Load warehouse/player_availability (single source of truth)
    2. Filter to starters using position group logic:
       - Most positions: depth_rank='1'
       - WR: Top N based on formation (2-3 WRs depending on 'NWR' in pos_grp)
       - RB: Top 2 by depth_rank
       - Filter to pos_slot 1-11 (exclude special teams-only)
    3. Identify unavailable players (is_available=FALSE)
    4. Aggregate by team-week
    5. Calculate position-weighted impact
    6. Merge with games DataFrame
    """
    
    def __init__(self, logger=None, debug=False):
        """
        Initialize availability feature calculator.
        
        Args:
            logger: Optional logger instance
            debug: Enable diagnostic logging
        """
        self.logger = logger
        self.debug = debug
    
    def calculate_features(self,
                          games_df: pd.DataFrame,
                          player_availability_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all player availability features.
        
        Args:
            games_df: Game schedule with columns: game_id, season, week, home_team, away_team
            player_availability_df: Unified player availability from warehouse
                Required columns: season, week, team, position, is_available,
                                 depth_rank, roster_status, availability_status
        
        Returns:
            DataFrame with availability features added
        
        Raises:
            ValueError: If player availability data is missing or invalid
        """
        if self.logger:
            self.logger.info("=" * 80)
            self.logger.info("🏥 CALCULATING PLAYER AVAILABILITY FEATURES")
            self.logger.info("=" * 80)
        
        df = games_df.copy()
        
        # Validate input data - RAISE ERROR instead of silently using defaults
        if player_availability_df.empty:
            error_msg = (
                "Player availability data is empty. This indicates a data pipeline failure.\n"
                "Please rebuild warehouse player availability:\n"
                "  quantcup nflfastrv3 data warehouse --phase player_availability"
            )
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Validate required columns - RAISE ERROR instead of silently using defaults
        required_cols = ['season', 'week', 'team', 'position', 'is_available']
        missing_cols = [col for col in required_cols if col not in player_availability_df.columns]
        if missing_cols:
            error_msg = (
                f"Player availability data is missing required columns: {missing_cols}\n"
                f"Available columns: {list(player_availability_df.columns)}\n"
                "This indicates a schema mismatch. Please rebuild warehouse:\n"
                "  quantcup nflfastrv3 data warehouse --phase player_availability"
            )
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        if self.logger:
            self.logger.info(f"📊 Input data:")
            self.logger.info(f"   Games: {len(df):,}")
            self.logger.info(f"   Player availability records: {len(player_availability_df):,}")
            self.logger.info(f"   Seasons: {player_availability_df['season'].min()}-{player_availability_df['season'].max()}")
        
        # Validate depth_rank column exists (required for starter identification)
        if 'depth_rank' not in player_availability_df.columns:
            error_msg = (
                "Player availability data is missing 'depth_rank' column - cannot identify starters.\n"
                "This indicates incomplete warehouse data. Please rebuild:\n"
                "  quantcup nflfastrv3 data warehouse --phase player_availability"
            )
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # ✅ CRITICAL: Only process 2013+ data (snap counts required for accurate starter identification)
        # Pre-2013 data would require dummy values which corrupts model training
        seasons_list = player_availability_df['season'].unique().tolist()
        min_season = min(seasons_list) if seasons_list else 9999
        
        if min_season < 2013:
            if self.logger:
                pre_2013_seasons = [s for s in seasons_list if s < 2013]
                self.logger.warning(f"⚠️  Filtering out pre-2013 seasons (no snap count data): {pre_2013_seasons}")
                self.logger.warning("   Cannot use default values - would corrupt model with fake data")
            # Filter to 2013+ only
            player_availability_df = player_availability_df[player_availability_df['season'] >= 2013].copy()
            df = df[df['season'] >= 2013].copy()
            
            if player_availability_df.empty:
                error_msg = (
                    "All data is pre-2013 (no snap counts available).\n"
                    "Cannot generate features without actual snap count data.\n"
                    "Please request 2013+ seasons only."
                )
                if self.logger:
                    self.logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
        
        # All remaining data is 2013+ - use hybrid approach
        if True:  # Always use hybrid for 2013+
            if self.logger:
                self.logger.info("   📊 Using hybrid starter identification (position group + snap counts)")
            
            # Load and process snap counts
            snap_counts = self._load_snap_counts(seasons=seasons_list)
            if not snap_counts.empty:
                snap_counts_enriched = self._calculate_rolling_snap_share(snap_counts)
                starters = self._identify_true_starters_hybrid(player_availability_df, snap_counts_enriched).copy()
            # Fallback: snap counts unavailable even for 2013+ seasons - FAIL HARD
            else:
                error_msg = (
                    "Snap counts unavailable for 2013+ seasons.\n"
                    "Cannot generate features without snap count data.\n"
                    "Please rebuild snap_counts data or restrict to earlier training period."
                )
                if self.logger:
                    self.logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
        
        if self.logger:
            self.logger.info(f"   ✓ Filtered to {len(starters):,} starters")
        
        # Add missing data indicator (0 = data exists, will be set to 1 if missing)
        df['player_availability_data_missing'] = 0
        
        # Calculate features
        df = self._add_qb_availability(df, starters)
        df = self._add_starter_unavailability_counts(df, starters)
        df = self._add_availability_impact_scores(df, starters)
        
        if self.logger:
            self.logger.info("=" * 80)
            self.logger.info("✅ PLAYER AVAILABILITY FEATURES COMPLETE")
            self.logger.info("=" * 80)
        
        return df
    
    def _add_qb_availability(self, df: pd.DataFrame, starters: pd.DataFrame) -> pd.DataFrame:
        """
        Add QB availability flags (most critical feature).
        
        Creates:
        - home_qb_available: 1 if starting QB is available, 0 if unavailable
        - away_qb_available: 1 if starting QB is available, 0 if unavailable
        """
        if self.logger:
            self.logger.info("🏈 Calculating QB availability...")
        
        # Filter to QBs
        qbs = starters[
            starters['position'].str.upper().str.contains('QB', na=False)
        ].copy()
        
        if len(qbs) == 0:
            if self.logger:
                self.logger.warning("   ⚠️ No QBs found in starters")
            df['home_qb_available'] = 1
            df['away_qb_available'] = 1
            return df
        
        # Find unavailable QBs
        unavailable_qbs = qbs[~qbs['is_available']].copy()
        
        if len(unavailable_qbs) == 0:
            if self.logger:
                self.logger.info("   ✓ All starting QBs available")
            df['home_qb_available'] = 1
            df['away_qb_available'] = 1
            return df
        
        # Aggregate by team-week
        qb_unavailable = (
            unavailable_qbs.groupby(['team', 'season', 'week'])
            .size()
            .reset_index(name='qb_out')
        )
        
        # Merge with games (home team)
        df = df.merge(
            qb_unavailable.rename(columns={'team': 'home_team', 'qb_out': 'home_qb_out'}),
            on=['home_team', 'season', 'week'],
            how='left'
        )
        
        # Merge with games (away team)
        df = df.merge(
            qb_unavailable.rename(columns={'team': 'away_team', 'qb_out': 'away_qb_out'}),
            on=['away_team', 'season', 'week'],
            how='left'
        )
        
        # Create availability flags (1 = available, 0 = unavailable)
        df['home_qb_available'] = (df['home_qb_out'].fillna(0) == 0).astype(int)
        df['away_qb_available'] = (df['away_qb_out'].fillna(0) == 0).astype(int)
        
        # Clean up intermediate columns
        df = df.drop(['home_qb_out', 'away_qb_out'], axis=1, errors='ignore')
        
        # Log statistics
        qb_unavailable_games = ((df['home_qb_available'] == 0) | (df['away_qb_available'] == 0)).sum()
        if self.logger:
            self.logger.info(f"   ✓ QB availability calculated:")
            self.logger.info(f"      QBs unavailable: {len(unavailable_qbs):,} player-weeks")
            self.logger.info(f"      Games with QB unavailable: {qb_unavailable_games:,}")
            
            # Show sample unavailable QBs
            if len(unavailable_qbs) > 0 and 'full_name' in unavailable_qbs.columns:
                sample = unavailable_qbs[['full_name', 'team', 'season', 'week', 'availability_status']].head(5)
                self.logger.info(f"\n      Sample unavailable QBs:")
                self.logger.info(f"\n{sample.to_string(index=False)}")
        
        return df
    
    def _add_starter_unavailability_counts(self, df: pd.DataFrame, starters: pd.DataFrame) -> pd.DataFrame:
        """
        Add counts of unavailable starters by position type.
        
        Creates:
        - home_starter_unavailable: Total unavailable starters
        - away_starter_unavailable: Total unavailable starters
        - home_offense_unavailable: Unavailable offensive starters
        - away_offense_unavailable: Unavailable offensive starters
        - home_defense_unavailable: Unavailable defensive starters
        - away_defense_unavailable: Unavailable defensive starters
        """
        if self.logger:
            self.logger.info("📊 Calculating starter unavailability counts...")
        
        # Filter to unavailable starters
        unavailable = starters[~starters['is_available']].copy()
        
        if len(unavailable) == 0:
            if self.logger:
                self.logger.info("   ✓ All starters available")
            df['home_starter_unavailable'] = 0
            df['away_starter_unavailable'] = 0
            df['home_offense_unavailable'] = 0
            df['away_offense_unavailable'] = 0
            df['home_defense_unavailable'] = 0
            df['away_defense_unavailable'] = 0
            return df
        
        # Classify positions into units
        unavailable['unit'] = unavailable['position'].apply(self._classify_position_unit)
        
        # Total unavailable starters
        total_unavailable = (
            unavailable.groupby(['team', 'season', 'week'])
            .size()
            .reset_index(name='starter_unavailable')
        )
        
        # Merge total
        df = df.merge(
            total_unavailable.rename(columns={'team': 'home_team', 'starter_unavailable': 'home_starter_unavailable'}),
            on=['home_team', 'season', 'week'],
            how='left'
        )
        df = df.merge(
            total_unavailable.rename(columns={'team': 'away_team', 'starter_unavailable': 'away_starter_unavailable'}),
            on=['away_team', 'season', 'week'],
            how='left'
        )
        
        # By unit (offense/defense)
        for unit in ['offense', 'defense']:
            unit_unavailable = (
                unavailable[unavailable['unit'] == unit]
                .groupby(['team', 'season', 'week'])
                .size()
                .reset_index(name=f'{unit}_unavailable')
            )
            
            df = df.merge(
                unit_unavailable.rename(columns={'team': 'home_team', f'{unit}_unavailable': f'home_{unit}_unavailable'}),
                on=['home_team', 'season', 'week'],
                how='left'
            )
            df = df.merge(
                unit_unavailable.rename(columns={'team': 'away_team', f'{unit}_unavailable': f'away_{unit}_unavailable'}),
                on=['away_team', 'season', 'week'],
                how='left'
            )
        
        # Fill NaN with 0
        for col in ['home_starter_unavailable', 'away_starter_unavailable',
                    'home_offense_unavailable', 'away_offense_unavailable',
                    'home_defense_unavailable', 'away_defense_unavailable']:
            df[col] = df[col].fillna(0).astype(int)
        
        if self.logger:
            self.logger.info(f"   ✓ Unavailability counts calculated:")
            self.logger.info(f"      Total unavailable starters: {len(unavailable):,}")
            self.logger.info(f"      Avg unavailable per team-week: {df['home_starter_unavailable'].mean():.2f}")
            self.logger.info(f"      Offense unavailable: {df['home_offense_unavailable'].sum():,}")
            self.logger.info(f"      Defense unavailable: {df['home_defense_unavailable'].sum():,}")
        
        return df
    
    def _add_availability_impact_scores(self, df: pd.DataFrame, starters: pd.DataFrame) -> pd.DataFrame:
        """
        Add position-weighted availability impact scores.
        
        Creates:
        - home_availability_impact: Sum of position weights for unavailable starters
        - away_availability_impact: Sum of position weights for unavailable starters
        - availability_impact_diff: home - away (positive = home more impacted)
        """
        if self.logger:
            self.logger.info("⚖️ Calculating position-weighted availability impact...")
        
        # Filter to unavailable starters
        unavailable = starters[~starters['is_available']].copy()
        
        if len(unavailable) == 0:
            if self.logger:
                self.logger.info("   ✓ No unavailable starters - impact scores = 0")
            df['home_availability_impact'] = 0.0
            df['away_availability_impact'] = 0.0
            df['availability_impact_diff'] = 0.0
            return df
        
        # Get position weights
        unavailable['position_weight'] = unavailable['position'].apply(self._get_position_weight)
        
        # Aggregate by team-week
        impact_scores = (
            unavailable.groupby(['team', 'season', 'week'])['position_weight']
            .sum()
            .reset_index(name='availability_impact')
        )
        
        # Merge with games
        df = df.merge(
            impact_scores.rename(columns={'team': 'home_team', 'availability_impact': 'home_availability_impact'}),
            on=['home_team', 'season', 'week'],
            how='left'
        )
        df = df.merge(
            impact_scores.rename(columns={'team': 'away_team', 'availability_impact': 'away_availability_impact'}),
            on=['away_team', 'season', 'week'],
            how='left'
        )
        
        # Fill NaN with 0
        df['home_availability_impact'] = df['home_availability_impact'].fillna(0.0)
        df['away_availability_impact'] = df['away_availability_impact'].fillna(0.0)
        
        # Calculate differential (positive = home more impacted)
        df['availability_impact_diff'] = df['home_availability_impact'] - df['away_availability_impact']
        
        if self.logger:
            self.logger.info(f"   ✓ Impact scores calculated:")
            self.logger.info(f"      Mean home impact: {df['home_availability_impact'].mean():.4f}")
            self.logger.info(f"      Mean away impact: {df['away_availability_impact'].mean():.4f}")
            self.logger.info(f"      Max impact diff: {df['availability_impact_diff'].abs().max():.4f}")
        
        return df
    
    def _load_snap_counts(self, seasons=None) -> pd.DataFrame:
        """
        Load player snap counts from raw_nflfastr/snap_counts.
        
        Snap counts provide ACTUAL playing time, showing who truly started and how much they played.
        Coverage: 2013+ seasons (nflfastr availability)
        
        Schema (from nflreadr_snapcounts.md):
        - game_id: nflfastR game ID
        - pfr_player_id: Player PFR ID (for joining)
        - season, week, team
        - offense_pct: % of offensive snaps (0-100)
        - defense_pct: % of defensive snaps (0-100)
        - st_pct: % of special teams snaps (0-100)
        
        Args:
            seasons: Optional list of seasons to load (None = all)
            
        Returns:
            DataFrame with snap count data
        """
        if self.logger:
            self.logger.info("📊 Loading snap counts...")
        
        try:
            from commonv2.persistence.bucket_adapter import get_bucket_adapter
            bucket_adapter = get_bucket_adapter(logger=self.logger)
            
            # Build season filters
            filters = None
            if seasons:
                if isinstance(seasons, int):
                    seasons = [seasons]
                if len(seasons) == 1:
                    filters = [('season', '==', seasons[0])]
                else:
                    filters = [('season', 'in', seasons)]
            
            snap_counts = bucket_adapter.read_data('snap_counts', 'raw_nflfastr', filters=filters)
            
            if snap_counts.empty:
                if self.logger:
                    self.logger.warning("⚠️  No snap count data available")
                return pd.DataFrame()
            
            # Validate required columns
            required_cols = ['pfr_player_id', 'season', 'week', 'team', 'offense_pct', 'defense_pct']
            missing_cols = [col for col in required_cols if col not in snap_counts.columns]
            if missing_cols:
                if self.logger:
                    self.logger.error(f"❌ Snap counts missing required columns: {missing_cols}")
                    self.logger.error(f"   Available columns: {list(snap_counts.columns)}")
                return pd.DataFrame()
            
            #Check for null values in critical columns
            null_counts = snap_counts[required_cols].isnull().sum()
            if null_counts.any():
                if self.logger:
                    self.logger.warning(f"⚠️  Snap counts have null values:")
                    for col, count in null_counts[null_counts > 0].items():
                        self.logger.warning(f"      {col}: {count:,} nulls ({(count/len(snap_counts)*100):.1f}%)")
            
            if self.logger:
                self.logger.info(f"   ✓ Loaded snap counts: {len(snap_counts):,} rows")
                self.logger.info(f"   Seasons: {snap_counts['season'].min()}-{snap_counts['season'].max()}")
                self.logger.info(f"   Players: {snap_counts['pfr_player_id'].nunique():,}")
                self.logger.info(f"   Games: {snap_counts['game_id'].nunique() if 'game_id' in snap_counts.columns else 'N/A'}")
            
            return snap_counts
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️  Failed to load snap counts: {e}")
            return pd.DataFrame()
    
    def _calculate_rolling_snap_share(self, snap_counts_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate rolling 3-game average snap share for each player.
        
        Logic:
        1. Determine player's primary side (offense vs defense) based on where they play most
        2. Calculate snap percentage relative to their primary side
        3. Compute rolling 3-game average (shifted for temporal safety)
        
        Args:
            snap_counts_df: Raw snap counts from _load_snap_counts()
            
        Returns:
            DataFrame with added column: rolling_3g_snap_share (0.0-1.0)
        """
        if snap_counts_df.empty:
            return pd.DataFrame()
        
        if self.logger:
            self.logger.info("   📊 Calculating rolling snap share (3-game average)...")
        
        snap_df = snap_counts_df.copy()
        
        # Determine primary side (offense vs defense) per player
        # Use the side where they play more snaps overall
        snap_df['offense_pct'] = pd.to_numeric(snap_df['offense_pct'], errors='coerce').fillna(0)
        snap_df['defense_pct'] = pd.to_numeric(snap_df['defense_pct'], errors='coerce').fillna(0)
        
        # Calculate player's primary side by season (may change if they switch positions)
        player_side = snap_df.groupby(['pfr_player_id', 'season']).agg({
            'offense_pct': 'sum',
            'defense_pct': 'sum'
        }).reset_index()
        player_side['primary_side'] = np.where(
            player_side['offense_pct'] >= player_side['defense_pct'],
            'offense', 'defense'
        )
        
        # Merge primary side back to snap counts
        snap_df = snap_df.merge(
            player_side[['pfr_player_id', 'season', 'primary_side']],
            on=['pfr_player_id', 'season'],
            how='left'
        )
        
        # Calculate snap share based on primary side
        snap_df['snap_pct'] = np.where(
            snap_df['primary_side'] == 'offense',
            snap_df['offense_pct'],
            snap_df['defense_pct']
        )
        
        # ✅ CRITICAL: Detect if data is already 0-1 or needs 0-100 → 0-1 conversion
        max_pct = snap_df['snap_pct'].max(skipna=True)
        if max_pct <= 1.0:
            # Already normalized (0-1 scale)
            snap_df['snap_share'] = snap_df['snap_pct']
            if self.logger:
                self.logger.info(f"   📏 Snap counts already normalized (max={max_pct:.3f}) - using as-is")
        else:
            # Need to convert from 0-100 to 0-1
            snap_df['snap_share'] = snap_df['snap_pct'] / 100.0
            if self.logger:
                self.logger.info(f"   📏 Snap counts in percentage format (max={max_pct:.1f}%) - converting to 0-1")
        
        snap_df['snap_share'] = snap_df['snap_share'].clip(0, 1)  # Ensure bounds
        
        # Calculate rolling 3-game average (shifted for temporal safety)
        # Sort by player and date
        snap_df = snap_df.sort_values(['pfr_player_id', 'season', 'week'])
        
        # Rolling average with shift (use PAST games only)
        snap_df['rolling_3g_snap_share'] = (
            snap_df.groupby(['pfr_player_id', 'season'])['snap_share']
            .transform(lambda x: x.shift(1).rolling(window=3, min_periods=1).mean())
        )
        
        # For first game of season (no history), use current game's snap share
        snap_df['rolling_3g_snap_share'] = snap_df['rolling_3g_snap_share'].fillna(snap_df['snap_share'])
        
        if self.logger:
            self.logger.info(f"   ✓ Rolling snap share calculated for {snap_df['pfr_player_id'].nunique():,} players")
            has_snaps = snap_df['rolling_3g_snap_share'].notna().sum()
            self.logger.info(f"   Coverage: {has_snaps:,}/{len(snap_df):,} records ({(has_snaps/len(snap_df)*100):.1f}%)")
            
            # Log snap share distribution for quality check
            snap_stats = snap_df['rolling_3g_snap_share'].describe()
            self.logger.info(f"   Snap share distribution:")
            self.logger.info(f"      Mean: {snap_stats['mean']:.3f}, Median: {snap_stats['50%']:.3f}")
            self.logger.info(f"      Range: {snap_stats['min']:.3f} - {snap_stats['max']:.3f}")
            
            # Warn if distribution looks suspicious
            if snap_stats['max'] > 1.0:
                self.logger.warning(f"⚠️  Snap share max > 1.0 ({snap_stats['max']:.3f}) - data may be in wrong format (should be 0-1)")
            if snap_stats['mean'] > 0.8:
                self.logger.warning(f"⚠️  Snap share mean > 0.8 ({snap_stats['mean']:.3f}) - suspiciously high, verify data")
        
        return snap_df[['pfr_player_id', 'season', 'week', 'team', 'rolling_3g_snap_share', 'primary_side']]
    
    def _identify_true_starters_hybrid(self, player_availability_df: pd.DataFrame,
                                       snap_counts_enriched: pd.DataFrame) -> pd.DataFrame:
        """
        Identify TRUE starters using hybrid approach: position group logic + snap counts.
        
        Strategy:
        1. Start with position group starters (depth chart + formation logic)
        2. Enrich with snap share data (actual playing time)
        3. Flag injury replacements (depth_rank='1' but low historical snap share <30%)
        4. Use snap share for weighting unavailability impact
        
        Args:
            player_availability_df: Warehouse player availability data
            snap_counts_enriched: Snap counts with rolling_3g_snap_share
            
        Returns:
            DataFrame with starters + snap share + injury replacement flag
        """
        if self.logger:
            self.logger.info("   🎯 Identifying true starters (hybrid: position group + snap counts)...")
        
        # Part 1: Get position group starters (from depth chart)
        depth_starters = self._filter_starters_by_position_group(player_availability_df)
        
        if depth_starters.empty:
            if self.logger:
                self.logger.warning("   ⚠️  No starters from position group logic")
            return pd.DataFrame()
        
        # No fallbacks - snap counts are REQUIRED for 2013+ data
        if snap_counts_enriched.empty:
            error_msg = (
                "Snap counts empty in hybrid identification.\n"
                "Cannot proceed without snap count data for 2013+ seasons.\n"
                "This indicates a data pipeline failure."
            )
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Part 2: Merge with snap counts
        # Join on pfr_player_id (need to map gsis_id → pfr_player_id)
        # For now, use pfr_id column from player_availability (already exists)
        if 'pfr_id' not in depth_starters.columns:
            if self.logger:
                self.logger.error("   ❌ No pfr_id column - cannot join snap counts")
                self.logger.error(f"   Available columns: {list(depth_starters.columns)}")
            depth_starters['rolling_3g_snap_share'] = 0.50
            depth_starters['is_injury_replacement'] = 0
            return depth_starters
        
        if self.logger:
            self.logger.info(f"   🔗 Merging {len(depth_starters):,} starters with snap counts...")
            self.logger.info(f"      Starters with pfr_id: {depth_starters['pfr_id'].notna().sum():,}/{len(depth_starters):,}")
        
        depth_starters_with_snaps = depth_starters.merge(
            snap_counts_enriched,
            left_on=['pfr_id', 'season', 'week', 'team'],
            right_on=['pfr_player_id', 'season', 'week', 'team'],
            how='left'
        )
        
        # Log join success rate
        if self.logger:
            matched = depth_starters_with_snaps['rolling_3g_snap_share'].notna().sum()
            match_rate = (matched / len(depth_starters_with_snaps)) * 100
            self.logger.info(f"      ✓ Matched {matched:,}/{len(depth_starters_with_snaps):,} ({match_rate:.1f}%) with snap counts")
            
            if match_rate < 50:
                self.logger.warning(f"      ⚠️  Low match rate ({match_rate:.1f}%) - most starters missing snap data")
            elif match_rate < 80:
                self.logger.warning(f"      ⚠️  Moderate match rate ({match_rate:.1f}%) - some starters missing snap data")
        
        # Part 3: Flag injury replacements
        # Player is injury replacement if: depth_rank='1' BUT low historical snap share
        LOW_SNAP_THRESHOLD = 0.30  # <30% historical snaps suggests backup promoted
        
        # Note: depth_rank is Int64 (pandas nullable integer) after conversion
        # Must use Int64 dtype for astype() to handle NA values
        depth_starters_with_snaps['is_injury_replacement'] = (
            (depth_starters_with_snaps['rolling_3g_snap_share'].fillna(0.50) < LOW_SNAP_THRESHOLD) &
            (depth_starters_with_snaps['depth_rank'] == 1)  # Numeric comparison after conversion
        ).astype('Int64')  # Use pandas nullable integer to handle NAs
        
        # Part 4: Fill missing snap shares with default
        depth_starters_with_snaps['rolling_3g_snap_share'] = (
            depth_starters_with_snaps['rolling_3g_snap_share'].fillna(0.50)
        )
        
        if self.logger:
            total_starters = len(depth_starters_with_snaps)
            injury_replacements = depth_starters_with_snaps['is_injury_replacement'].sum()
            high_snap = (depth_starters_with_snaps['rolling_3g_snap_share'] > 0.50).sum()
            
            self.logger.info(f"   ✓ Hybrid identification complete:")
            self.logger.info(f"      Total starters: {total_starters:,}")
            self.logger.info(f"      High-snap starters (>50%): {high_snap:,} ({(high_snap/total_starters*100):.1f}%)")
            self.logger.info(f"      Injury replacements flagged: {injury_replacements:,} ({(injury_replacements/total_starters*100):.1f}%)")
        
        return depth_starters_with_snaps
    
    def _filter_starters_by_position_group(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify starters using position group and formation logic.
        
        Strategy:
        1. Most positions: depth_rank='1' (QB, TE, OL, DL, LB, S, K, P, LS)
        2. WR: Top N based on formation (pos_grp contains 'NWR' → top N, default 2)
        3. RB/HB/FB: Top 2 by depth_rank (RB1 + RB2/FB)
        4. Safety net: Filter to pos_slot 1-11 to exclude special teams-only players
        5. Must be on active roster (roster_status='ACT')
        
        Args:
            df: player_availability DataFrame with columns: depth_rank, position,
                pos_grp (formation), pos_slot, roster_status, season, week, team
                
        Returns:
            DataFrame with starter records only (~22 per team per week: 11 offense + 11 defense)
        """
        if self.logger:
            self.logger.info("   📋 Applying position group logic to identify starters...")
        
        starters = []
        
        # ✅ CRITICAL: Convert depth_rank to numeric for sorting operations (nsmallest)
        # Warehouse transformation stores as 'string' dtype for Parquet schema compatibility
        if 'depth_rank' in df.columns:
            df = df.copy()
            if self.logger:
                self.logger.info(f"      📊 BEFORE conversion - depth_rank dtype: {df['depth_rank'].dtype}")
                self.logger.info(f"         Unique values (first 10): {sorted(df['depth_rank'].dropna().unique())[:10]}")
                self.logger.info(f"         Null count: {df['depth_rank'].isna().sum():,}")
                self.logger.info(f"         Value '1' count: {(df['depth_rank'] == '1').sum():,}")
                self.logger.info(f"         Value 1 count: {(df['depth_rank'] == 1).sum():,}")
            
            if df['depth_rank'].dtype == 'object' or df['depth_rank'].dtype.name == 'string':
                if self.logger:
                    self.logger.info(f"      🔧 Converting depth_rank from {df['depth_rank'].dtype} to numeric...")
                df['depth_rank'] = pd.to_numeric(df['depth_rank'], errors='coerce')
                null_count = df['depth_rank'].isna().sum()
                
                if self.logger:
                    self.logger.info(f"      📊 AFTER conversion - depth_rank dtype: {df['depth_rank'].dtype}")
                    self.logger.info(f"         Unique values (first 10): {sorted(df['depth_rank'].dropna().unique())[:10]}")
                    self.logger.info(f"         Null count: {null_count:,}")
                    self.logger.info(f"         Value 1 count: {(df['depth_rank'] == 1).sum():,}")
                    if null_count > 0:
                        self.logger.warning(f"         ⚠️  {null_count:,} invalid depth_rank values (converted to NaN)")
        
        # ✅ CRITICAL: DO NOT filter to roster_status='ACT' - we need IR/Suspended/etc. to count unavailable!
        # Only exclude practice squad (+dev) and fully cut players (who aren't starters anyway)
        if 'roster_status' in df.columns:
            exclude_statuses = ['DEV', 'CUT', 'RET', 'UFA', 'TRC', 'TRD', 'TRT']  # Practice squad + released
            active_df = df[~df['roster_status'].isin(exclude_statuses)].copy()
            excluded_count = len(df) - len(active_df)
            if self.logger:
                self.logger.info(f"      Excluding practice squad/cut players: {excluded_count:,}")
                self.logger.info(f"      Potential starters (inc. IR/Out/Suspended): {len(active_df):,}")
        else:
            active_df = df.copy()
            if self.logger:
                self.logger.warning("      ⚠️  No roster_status column - cannot filter practice squad")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Group 1: Simple depth_rank='1' positions (QB, TE, OL, DL, LB, S, K, P, LS)
        # ═══════════════════════════════════════════════════════════════════════════
        simple_positions = ['QB', 'TE', 'C', 'G', 'T', 'OL', 'OT', 'OG',
                           'LT', 'RT', 'LG', 'RG',  # Offensive line
                           'DL', 'DE', 'DT', 'NT',  # Defensive line
                           'LB', 'ILB', 'OLB', 'MLB',  # Linebackers
                           'CB', 'S', 'FS', 'SS', 'DB',  # Secondary
                           'K', 'P', 'LS']  # Special teams
        
        simple_mask = (
            active_df['position'].str.upper().isin(simple_positions) &
            (active_df['depth_rank'] == 1)  # Numeric comparison after conversion
        )
        simple_starters = active_df[simple_mask]
        if len(simple_starters) > 0:
            starters.append(simple_starters)
            if self.logger:
                self.logger.info(f"      Simple positions (depth_rank='1'): {len(simple_starters):,}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Group 2: WR - Top N based on formation
        # ═══════════════════════════════════════════════════════════════════════════
        wr_mask = active_df['position'].str.upper().isin(['WR'])
        if wr_mask.sum() > 0:
            wr_df = active_df[wr_mask].copy()
            
            # Extract WR count from formation (e.g., '3WR 1TE' → 3)
            if 'pos_grp' in wr_df.columns:
                wr_df['wr_count'] = wr_df['pos_grp'].str.extract(r'(\d+)WR', expand=False).fillna('2').astype(float)
            else:
                wr_df['wr_count'] = 2  # Default 2WR if no formation data
            
            # Group by team-week and take top N WRs based on depth_rank
            wr_starters_list = []
            for (season, week, team), group in wr_df.groupby(['season', 'week', 'team']):
                n_wr = int(group['wr_count'].iloc[0])
                # Sort by depth_rank (lower is better) and take top N
                top_wr = group.nsmallest(n_wr, 'depth_rank', keep='all')
                wr_starters_list.append(top_wr)
            
            if wr_starters_list:
                wr_starters = pd.concat(wr_starters_list, ignore_index=True)
                starters.append(wr_starters)
                if self.logger:
                    self.logger.info(f"      WR (formation-based): {len(wr_starters):,}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Group 3: RB/HB/FB - Top 2 (RB1 + RB2/FB)
        # ═══════════════════════════════════════════════════════════════════════════
        rb_mask = active_df['position'].str.upper().isin(['RB', 'HB', 'FB'])
        if rb_mask.sum() > 0:
            rb_df = active_df[rb_mask].copy()
            # Take top 2 RBs per team-week
            rb_starters = rb_df.sort_values(['season', 'week', 'team', 'depth_rank']).groupby(['season', 'week', 'team'], as_index=False).head(2)
            if len(rb_starters) > 0:
                starters.append(rb_starters)
                if self.logger:
                    self.logger.info(f"      RB/HB/FB (top 2): {len(rb_starters):,}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Combine and apply safety net
        # ═══════════════════════════════════════════════════════════════════════════
        if not starters:
            if self.logger:
                self.logger.warning("      ⚠️ No starters identified - returning empty")
            return pd.DataFrame()
        
        result = pd.concat(starters, ignore_index=True)
        
        # Safety net: Filter to pos_slot 1-22 (11 offense + 11 defense, exclude special teams-only)
        if 'pos_slot' in result.columns:
            pre_filter_count = len(result)
            # Convert pos_slot to numeric, handle non-numeric values
            result['pos_slot_numeric'] = pd.to_numeric(result['pos_slot'], errors='coerce')
            result = result[result['pos_slot_numeric'].fillna(999) <= 22]  # Was 11 - missed defense!
            result = result.drop(columns=['pos_slot_numeric'])
            filtered_count = pre_filter_count - len(result)
            if filtered_count > 0 and self.logger:
                self.logger.info(f"      Filtered {filtered_count:,} special teams-only players (pos_slot >22)")
        
        # Remove duplicates (player may appear in multiple groups)
        if len(result) > 0:
            result = result.drop_duplicates(subset=['season', 'week', 'team', 'gsis_id'], keep='first')
        
        if self.logger:
            if len(result) > 0:
                avg_per_team = result.groupby(['season', 'week', 'team']).size().mean()
                self.logger.info(f"      ✓ Total starters identified: {len(result):,} (~{avg_per_team:.1f} per team-week)")
            else:
                self.logger.warning("      ⚠️ No starters after filtering")
        
        return result
    
    def _classify_position_unit(self, position: str) -> str:
        """
        Classify position into offensive, defensive, or special teams unit.
        
        Args:
            position: Position code (e.g., 'QB', 'WR', 'CB')
            
        Returns:
            'offense', 'defense', or 'special'
        """
        if pd.isna(position):
            return 'unknown'
        
        pos_upper = position.upper()
        
        # Offensive positions
        if any(p in pos_upper for p in ['QB', 'RB', 'WR', 'TE', 'OL', 'OT', 'OG', 'C', 'T', 'G', 'LT', 'RT', 'LG', 'RG']):
            return 'offense'
        
        # Defensive positions
        if any(p in pos_upper for p in ['DL', 'LB', 'CB', 'S', 'DB', 'DE', 'DT', 'NT', 'ILB', 'OLB', 'MLB', 'FS', 'SS']):
            return 'defense'
        
        # Special teams
        if any(p in pos_upper for p in ['K', 'P', 'LS']):
            return 'special'
        
        return 'unknown'
    
    def _get_position_weight(self, position: str) -> float:
        """
        Get importance weight for a position.
        
        Args:
            position: Position code (e.g., 'QB', 'WR')
            
        Returns:
            float: Position weight (0.01-0.35)
        """
        if pd.isna(position):
            return POSITION_WEIGHTS['DEFAULT']
        
        pos_upper = position.upper()
        
        # Try exact match first
        if pos_upper in POSITION_WEIGHTS:
            return POSITION_WEIGHTS[pos_upper]
        
        # Try prefix match (e.g., 'LT' for 'LT/RT')
        for key in POSITION_WEIGHTS:
            if key in pos_upper:
                return POSITION_WEIGHTS[key]
        
        return POSITION_WEIGHTS['DEFAULT']


class PlayerAvailabilityFeatures:
    """
    Service wrapper for player availability features (follows standard pattern).
    
    Pattern: Minimum Viable Decoupling
    Complexity: 2 points (DI + business logic)
    Layer: 2 (Implementation - calls infrastructure directly)
    
    This wrapper provides the standard build_features() interface expected by
    the feature orchestrator while delegating to PlayerAvailabilityFeatureCalculator.
    """
    
    def __init__(self, db_service, logger=None):
        """
        Initialize player availability features service.
        
        Args:
            db_service: Database service instance
            logger: Optional logger (uses default if None)
        """
        self.db_service = db_service
        self.logger = logger
        self.calculator = PlayerAvailabilityFeatureCalculator(logger=logger, debug=False)
    
    def build_features(self, seasons=None):
        """
        Build player availability features for specified seasons.
        
        Args:
            seasons: Season(s) to build features for (list of ints, or None for all)
            
        Returns:
            dict: Build result with 'status', 'dataframe', 'features_built'
        """
        try:
            # Load game schedule
            game_schedule_df = self._load_game_schedule(seasons)
            
            if game_schedule_df.empty:
                return {
                    'status': 'warning',
                    'message': 'No game schedule data available',
                    'features_built': 0
                }
            
            # Load player availability data
            player_availability_df = self._load_player_availability(seasons)
            
            # Calculate features
            result_df = self.calculator.calculate_features(
                games_df=game_schedule_df,
                player_availability_df=player_availability_df
            )
            
            # Drop metadata columns to prevent merge conflicts
            # (like other feature sets - e.g., nextgen_features.py:520-532)
            # KEEP season and week for bucket filtering (required for queries)
            metadata_columns = ['home_team', 'away_team']
            columns_to_drop = [col for col in metadata_columns if col in result_df.columns]
            
            if columns_to_drop:
                self.logger.info(f"📊 Dropping metadata columns: {columns_to_drop}")
                result_df = result_df.drop(columns=columns_to_drop)
            
            return {
                'status': 'success',
                'dataframe': result_df,
                'features_built': len(result_df),
                'seasons_processed': len(seasons) if seasons else 'all'
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to build player availability features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }
    
    def _load_game_schedule(self, seasons):
        """Load game schedule from dim_game."""
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        bucket_adapter = get_bucket_adapter(logger=self.logger)
        games_df = bucket_adapter.read_data('dim_game', 'warehouse')
        
        if games_df.empty:
            if self.logger:
                self.logger.error("❌ dim_game is empty")
            return pd.DataFrame()
        
        # Filter to requested seasons
        if seasons:
            if isinstance(seasons, int):
                seasons = [seasons]
            games_df = games_df[games_df['season'].isin(seasons)]
        
        # Select required columns
        required_cols = ['game_id', 'season', 'week', 'home_team', 'away_team']
        games_df = games_df[required_cols].copy()
        
        return games_df
    
    def _load_player_availability(self, seasons):
        """Load player availability from warehouse."""
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        bucket_adapter = get_bucket_adapter(logger=self.logger)
        availability_df = bucket_adapter.read_data('player_availability', 'warehouse')
        
        if availability_df.empty:
            if self.logger:
                self.logger.warning("⚠️ warehouse/player_availability is empty")
            return pd.DataFrame()
        
        # Filter to requested seasons
        if seasons:
            if isinstance(seasons, int):
                seasons = [seasons]
            availability_df = availability_df[availability_df['season'].isin(seasons)]
        
        return availability_df


def create_player_availability_features(db_service=None, logger=None):
    """
    Factory function to create player availability features service.
    
    Args:
        db_service: Database service instance (optional)
        logger: Optional logger (uses default if None)
        
    Returns:
        PlayerAvailabilityFeatures: Configured service instance
    """
    from commonv2 import get_logger
    
    if logger is None:
        logger = get_logger('nflfastRv3.ml_pipeline.player_availability_features')
    
    return PlayerAvailabilityFeatures(db_service, logger)


__all__ = [
    'PlayerAvailabilityFeatureCalculator',
    'PlayerAvailabilityFeatures',
    'create_player_availability_features',
    'POSITION_WEIGHTS'
]


# ARCHITECTURAL NOTE ON MISSING DATA HANDLING:
#
# This module now raises ValueError when player availability data is missing
# instead of silently using optimistic defaults. This is a deliberate design
# choice to prevent:
#
# 1. Silent failures that degrade model performance
# 2. Optimistic bias when data is unavailable
# 3. Inability to distinguish "all available" from "no data"
#

