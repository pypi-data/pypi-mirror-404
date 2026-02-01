"""
Injury Impact Calculation Module

Calculates injury impact scores and starter availability features.
Includes internal SeverityClassifier for injury scoring.

Pattern: Feature calculation with internal helpers.
Extracted from lines 1670-2226 of original injury_features.py.

See docs/injury_analysis/algorithm_details.md for full algorithm documentation.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple
from .constants import (
    POSITION_WEIGHTS,
    INJURY_STATUS_WEIGHTS,
    INJURY_SEVERITY,
    INJURY_SEVERITY_PATTERNS
)


class SeverityClassifier:
    """
    Internal helper for injury severity classification.
    
    NOT exported - only used within impact_calculation.
    If 3+ feature sets need this, THEN extract to utils/.
    """
    
    def __init__(self, logger=None):
        """
        Initialize severity classifier.
        
        Args:
            logger: Optional logger instance for unmapped injury warnings
        """
        self.logger = logger
        self._logged_unmapped = set()
    
    def classify_injury_severity(self, injury_text: str) -> float:
        """
        Fuzzy match injury types to severity scores.
        
        Handles typos, variations, and multi-word descriptions.
        Example: "Torn ACL" → matches 'ACL' pattern → 1.0 severity
        
        Args:
            injury_text: Raw injury description from data
            
        Returns:
            float: Severity score (0.0-1.0)
        """
        if pd.isna(injury_text) or injury_text == '':
            return 0.5  # Unknown default
        
        injury_lower = str(injury_text).lower().strip()
        
        # Try exact match first (fastest)
        if injury_lower.title() in INJURY_SEVERITY:
            return INJURY_SEVERITY[injury_lower.title()]
        
        # Fuzzy match using patterns
        for injury_type, patterns in INJURY_SEVERITY_PATTERNS.items():
            if any(pattern in injury_lower for pattern in patterns):
                return INJURY_SEVERITY[injury_type]
        
        # No match found - log for future improvement (limit spam)
        if injury_lower not in self._logged_unmapped:
            self._logged_unmapped.add(injury_lower)
            if self.logger and len(self._logged_unmapped) <= 10:  # Only log first 10
                self.logger.warning(f"⚠️  Unmapped injury type: '{injury_text}' - using default 0.5")
        
        return 0.5  # Unknown default
    
    def get_position_weight(self, position: str) -> float:
        """
        Get position importance weight.
        
        Args:
            position: Position code (e.g., 'QB', 'WR', 'RB')
            
        Returns:
            float: Position weight (0.01-0.35)
        """
        normalized = position.upper()[:2]
        return POSITION_WEIGHTS.get(normalized, 0.01)
    
    def get_status_impact(self, status: str) -> float:
        """
        Get injury status impact score.
        
        Args:
            status: Injury status (e.g., 'Out', 'Questionable', 'Doubtful')
            
        Returns:
            float: Status impact (0.0-1.0)
        """
        return INJURY_STATUS_WEIGHTS.get(status, 0.0)


class InjuryImpactCalculator:
    """Calculates injury impact and starter availability features."""
    
    def __init__(self, logger=None, debug=False):
        """
        Initialize injury impact calculator.
        
        Args:
            logger: Optional logger instance
            debug: Enable diagnostic logging (default: False)
        """
        self.logger = logger
        self.debug = debug
        self.severity = SeverityClassifier(logger)
    
    def calculate_injury_impact(self, games_df: pd.DataFrame,
                                 depth_chart_df: pd.DataFrame,
                                 injuries_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate position-weighted injury impact scores for each game.
        
        Expected Impact: 8-12 point variance reduction
        Rationale: Injuries to key positions (especially QB) significantly affect outcomes
        
        Temporal Safety: Uses injury reports from BEFORE game (week-based)
        
        Following LESSONS_LEARNED.md Case Study #4 (lines 549-735):
        - Log data samples before/after transformation
        - Include statistical summaries
        - Validate temporal leakage prevention
        
        Args:
            games_df: Game-level DataFrame with schedule data
            depth_chart_df: Depth chart data
            injuries_df: Injury report data
            
        Returns:
            DataFrame with injury impact features added
        """
        if self.logger:
            self.logger.info("📊 Calculating position-weighted injury impact...")
        
        df = games_df.copy()
        
        # DATA INSPECTION: Show BEFORE (LESSONS_LEARNED.md lines 673-710)
        if self.logger:
            self.logger.info("📊 DATA SAMPLE - BEFORE injury impact (first 5 games):")
            sample_before = df[['game_id', 'season', 'week', 'home_team', 'away_team']].head(5)
            self.logger.info(f"\n{sample_before.to_string()}")
        
        if depth_chart_df.empty or injuries_df.empty:
            if self.logger:
                self.logger.warning("⚠️  Insufficient data for injury impact calculation")
            df['home_injury_impact'] = 0.0
            df['away_injury_impact'] = 0.0
            df['injury_impact_diff'] = 0.0
            return df
        
        # Use columns as-is from bucket data (no renaming needed)
        # depth_chart columns: season, club_code, week, game_type, pos_rank, pos_slot, position, etc.
        # injuries columns: season, game_type, team, week, position, report_status, date_modified, etc.
        
        depth_chart = depth_chart_df.copy()
        injuries = injuries_df.copy()
        
        # ⚠️ CRITICAL: Temporal Leakage Prevention (Feature-Level Filtering)
        # Filter injury reports to only include those published BEFORE game start time
        # This prevents using mid-game or post-game injury updates in predictions
        # Complements TemporalValidator's week-level filtering
        if 'date_modified' in injuries.columns and not games_df.empty:
            if self.logger:
                self.logger.info("🔒 Applying temporal leakage filtering (date_modified < game_datetime)...")
            
            # Merge injuries with game dates to filter by game start time
            injuries_with_dates = injuries.merge(
                games_df[['season', 'week', 'game_date']].drop_duplicates(),
                on=['season', 'week'],
                how='left'
            )
            
            # Ensure both timestamps are timezone-naive for comparison
            injuries_with_dates['date_modified'] = pd.to_datetime(injuries_with_dates['date_modified']).dt.tz_localize(None)
            injuries_with_dates['game_date'] = pd.to_datetime(injuries_with_dates['game_date']).dt.tz_localize(None)
            
            # Filter: Only use injury reports from BEFORE game start
            pre_count = len(injuries_with_dates)
            injuries = injuries_with_dates[injuries_with_dates['date_modified'] < injuries_with_dates['game_date']].copy()
            post_count = len(injuries)
            
            filtered_count = pre_count - post_count
            if filtered_count > 0 and self.logger:
                self.logger.info(f"   ✓ Filtered {filtered_count:,} injury reports with date_modified >= game_date ({(filtered_count/pre_count)*100:.1f}%)")
                self.logger.info(f"   ✓ Using {post_count:,} pre-game injury reports for feature calculation")
            elif self.logger:
                self.logger.info(f"   ✓ All {post_count:,} injury reports are pre-game (no temporal leakage detected)")
            
            # Drop game_date column (no longer needed)
            injuries = injuries.drop(columns=['game_date'])
        else:
            if 'date_modified' not in injuries.columns and self.logger:
                self.logger.warning("⚠️  'date_modified' column not found in injuries data - cannot apply temporal leakage filtering!")
                self.logger.warning("   This may result in data leakage if injury reports were updated during/after games")
        
        # Map injury status column if needed
        if 'report_status' in injuries.columns:
            injuries = injuries.rename(columns={'report_status': 'injury_status'})
        
        # Filter for regular season only
        if 'game_type' in depth_chart.columns:
            depth_chart = depth_chart[depth_chart['game_type'] == 'REG']
        if 'game_type' in injuries.columns:
            injuries = injuries[injuries['game_type'] == 'REG']
        
        if self.logger:
            self.logger.info(f"   Depth chart: {len(depth_chart):,} rows after filtering")
            self.logger.info(f"   Injuries: {len(injuries):,} rows after filtering")
        
        # Calculate injury impact for each team-week
        # Use 'team' column from injuries (already present)
        if not injuries.empty and all(c in injuries.columns for c in ['team', 'season', 'week', 'position', 'injury_status']):
            
            # Map injury status to impact score
            injuries['impact_score'] = injuries['injury_status'].map(INJURY_STATUS_WEIGHTS).fillna(0)
            
            # Map position to importance weight
            # Normalize position names (QB, WR, RB, etc.)
            injuries['position_normalized'] = injuries['position'].str.upper().str[:2]
            injuries['position_weight'] = injuries['position_normalized'].map(POSITION_WEIGHTS).fillna(0.01)
            
            # Calculate weighted injury impact per player
            injuries['player_injury_impact'] = injuries['impact_score'] * injuries['position_weight']
            
            # Aggregate by team-season-week
            team_injury_impact = injuries.groupby(['team', 'season', 'week']).agg({
                'player_injury_impact': 'sum',  # Total injury impact
                'impact_score': 'count'  # Number of injured players
            }).reset_index()
            
            team_injury_impact.columns = ['team', 'season', 'week', 'injury_impact', 'injured_count']
            
            if self.logger:
                self.logger.info(f"✓ Calculated injury impact for {len(team_injury_impact):,} team-weeks")
            
            # Merge with games for home team
            df = df.merge(
                team_injury_impact.rename(columns={
                    'team': 'home_team',
                    'injury_impact': 'home_injury_impact',
                    'injured_count': 'home_injured_count'
                }),
                on=['home_team', 'season', 'week'],
                how='left'
            )
            
            # Merge with games for away team
            df = df.merge(
                team_injury_impact.rename(columns={
                    'team': 'away_team',
                    'injury_impact': 'away_injury_impact',
                    'injured_count': 'away_injured_count'
                }),
                on=['away_team', 'season', 'week'],
                how='left'
            )
            
            # Fill NaN (no injuries reported) with 0
            df['home_injury_impact'] = df['home_injury_impact'].fillna(0)
            df['away_injury_impact'] = df['away_injury_impact'].fillna(0)
            df['home_injured_count'] = df['home_injured_count'].fillna(0)
            df['away_injured_count'] = df['away_injured_count'].fillna(0)
            
            # Calculate differential (home - away)
            # Positive = home team more injured, negative = away team more injured
            df['injury_impact_diff'] = df['home_injury_impact'] - df['away_injury_impact']
            
        else:
            if self.logger:
                self.logger.warning("⚠️  Injury data missing required columns - using zeros")
            df['home_injury_impact'] = 0.0
            df['away_injury_impact'] = 0.0
            df['home_injured_count'] = 0
            df['away_injured_count'] = 0
            df['injury_impact_diff'] = 0.0
        
        # DATA INSPECTION: Show AFTER (LESSONS_LEARNED.md lines 673-710)
        if self.logger:
            self.logger.info("📊 DATA SAMPLE - AFTER injury impact (first 5 games):")
            sample_after = df[['game_id', 'home_team', 'away_team', 'home_injury_impact', 
                              'away_injury_impact', 'injury_impact_diff']].head(5)
            self.logger.info(f"\n{sample_after.to_string()}")
        
        # STATISTICS: Summary (CODING_GUIDE.md lines 1690-1693)
        if self.logger:
            self.logger.info(f"📊 Injury Impact Statistics:")
            self.logger.info(f"   home_injury_impact: mean={df['home_injury_impact'].mean():.4f}, range=[{df['home_injury_impact'].min():.4f}, {df['home_injury_impact'].max():.4f}]")
            self.logger.info(f"   away_injury_impact: mean={df['away_injury_impact'].mean():.4f}, range=[{df['away_injury_impact'].min():.4f}, {df['away_injury_impact'].max():.4f}]")
            self.logger.info(f"   injury_impact_diff: mean={df['injury_impact_diff'].mean():.4f}, range=[{df['injury_impact_diff'].min():.4f}, {df['injury_impact_diff'].max():.4f}]")
            self.logger.info(f"   Games with injuries: {(df['home_injury_impact'] > 0).sum() + (df['away_injury_impact'] > 0).sum():,}")
        
        if self.logger:
            self.logger.info(f"✓ Injury impact calculation complete")
        
        return df
    
    def add_starter_availability(self, df: pd.DataFrame,
                                  depth_chart_df: pd.DataFrame,
                                  injuries_df: pd.DataFrame,
                                  replacement_reasons: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Add starter availability indicators and replacement reason features (Phase 2).
        
        Expected Impact: 3-4 point variance reduction (QB alone)
        Rationale: Starting QB availability is the single most important injury factor
        
        Phase 2 Enhancement: Adds replacement reason classification features
        - home/away_injury_driven_replacements: Count of injury-forced changes
        - home/away_performance_replacements: Count of benching/role changes
        - home/away_unknown_replacements: Count of questionable status changes
        
        Temporal Safety: Uses injury reports from BEFORE game (week-based)
        
        Following LESSONS_LEARNED.md Case Study #4 (lines 549-735):
        - Log data samples before/after transformation
       - Include statistical summaries
        
        Args:
            df: Game-level DataFrame
            depth_chart_df: Depth chart data
            injuries_df: Injury report data
            replacement_reasons: Optional DataFrame with replacement classifications from _classify_replacement_reason()
            
        Returns:
            DataFrame with starter availability features added
        """
        if self.logger:
            self.logger.info("📊 Adding starter availability indicators...")
        
        # DATA INSPECTION: Show BEFORE
        if self.logger:
            self.logger.info("📊 DATA SAMPLE - BEFORE starter availability (first 5 games):")
            sample_before = df[['game_id', 'home_team', 'away_team', 'week']].head(5)
            self.logger.info(f"\n{sample_before.to_string()}")
        
        if depth_chart_df.empty or injuries_df.empty:
            if self.logger:
                self.logger.warning("⚠️  Insufficient data for starter availability - using defaults")
            df['home_qb_available'] = 1
            df['away_qb_available'] = 1
            df['home_starter_injuries'] = 0
            df['away_starter_injuries'] = 0
            return df
        
        # Use columns as-is from bucket data
        depth_chart = depth_chart_df.copy()
        injuries = injuries_df.copy()
        
        # Map injury status column if needed
        if 'report_status' in injuries.columns:
            injuries = injuries.rename(columns={'report_status': 'injury_status'})
        
        # Determine team column name (club_code or team)
        team_col = 'club_code' if 'club_code' in depth_chart.columns else 'team'
        
        # ✅ FIX: Filter for starters using pos_rank (1 = starter, 2-15 = backups)
        if 'pos_rank' in depth_chart.columns:
            # Normalize pos_rank to int for consistent comparison
            # (handles float, string, or int from bucket data)
            depth_chart['pos_rank'] = pd.to_numeric(depth_chart['pos_rank'], errors='coerce').fillna(99).astype(int)
            
            # ✅ DIAGNOSTIC: Check depth_chart before filter
            if self.debug and self.logger:
                self.logger.info("🔍 DIAGNOSTIC - depth_chart before filtering:")
                self.logger.info(f"   Total rows: {len(depth_chart):,}")
                self.logger.info(f"   pos_rank distribution: {depth_chart['pos_rank'].value_counts().head().to_dict()}")
                if 'is_depth_starter_base11' in depth_chart.columns:
                    base11_pre = depth_chart['is_depth_starter_base11'].sum()
                    self.logger.info(f"   is_depth_starter_base11 (before filter): {base11_pre:,}")
                else:
                    self.logger.error("   ❌ is_depth_starter_base11 NOT in depth_chart before filter")
                
                if 'is_depth_starter_nickel' in depth_chart.columns:
                    nickel_pre = depth_chart['is_depth_starter_nickel'].sum()
                    self.logger.info(f"   is_depth_starter_nickel (before filter): {nickel_pre:,}")
                else:
                    self.logger.error("   ❌ is_depth_starter_nickel NOT in depth_chart before filter")
            
            # Filter for starters (pos_rank == 1)
            starters = depth_chart[depth_chart['pos_rank'] == 1].copy()
            
            # ✅ DIAGNOSTIC: Check starters after filter
            if self.debug and self.logger:
                self.logger.info("🔍 DIAGNOSTIC - starters after pos_rank==1 filter:")
                self.logger.info(f"   Rows after filter: {len(starters):,}")
                self.logger.info(f"   Columns in starters: {starters.columns.tolist()}")
                if 'is_depth_starter_base11' in starters.columns:
                    base11_post = (starters['is_depth_starter_base11'] == 1).sum()
                    self.logger.info(f"   is_depth_starter_base11 (after filter): {base11_post:,} starters")
                else:
                    self.logger.error("   ❌ is_depth_starter_base11 LOST after filter")
                
                if 'is_depth_starter_nickel' in starters.columns:
                    nickel_post = (starters['is_depth_starter_nickel'] == 1).sum()
                    self.logger.info(f"   is_depth_starter_nickel (after filter): {nickel_post:,} starters")
                else:
                    self.logger.error("   ❌ is_depth_starter_nickel LOST after filter")
            
            if self.logger:
                self.logger.info(f"   Identified {len(starters):,} starter records total")
            
            # DATA INSPECTION: Log pos_rank distribution
            if len(starters) == 0 and self.logger:
                self.logger.warning(f"⚠️  No starters found - pos_rank distribution:")
                rank_dist = depth_chart['pos_rank'].value_counts().head(10)
                self.logger.info(f"   {rank_dist.to_dict()}")
            
            # Merge starters with injuries to find injured starters
            if all(c in starters.columns for c in [team_col, 'season', 'week', 'position']):
                if all(c in injuries.columns for c in ['team', 'season', 'week', 'position']):
                    
                    # ✅ DIAGNOSTIC: Check starters DataFrame before merge
                    if self.debug and self.logger:
                        self.logger.info("🔍 DIAGNOSTIC - starters before injury merge:")
                        self.logger.info(f"   Columns: {starters.columns.tolist()}")
                        self.logger.info(f"   Rows: {len(starters):,}")
                        if 'is_depth_starter_base11' in starters.columns:
                            base11 = (starters['is_depth_starter_base11'] == 1).sum()
                            self.logger.info(f"   Base11 starters: {base11:,}")
                        else:
                            self.logger.error("   ❌ is_depth_starter_base11 NOT in starters before merge")
                        
                        if 'is_depth_starter_nickel' in starters.columns:
                            nickel = (starters['is_depth_starter_nickel'] == 1).sum()
                            self.logger.info(f"   Nickel starters: {nickel:,}")
                        else:
                            self.logger.error("   ❌ is_depth_starter_nickel NOT in starters before merge")
                    
                    # Merge on team, season, week, position
                    # Use left_on/right_on to avoid duplicate column issues
                    # (depth chart has 'club_code', injuries has 'team')
                    injured_starters = starters.merge(
                        injuries[['team', 'season', 'week', 'position', 'injury_status']],
                        left_on=[team_col, 'season', 'week', 'position'],
                        right_on=['team', 'season', 'week', 'position'],
                        how='inner'
                    )
                    
                    # ✅ DIAGNOSTIC: Check injured_starters after merge
                    if self.debug and self.logger:
                        self.logger.info("🔍 DIAGNOSTIC - injured_starters after merge:")
                        self.logger.info(f"   Columns: {injured_starters.columns.tolist()}")
                        self.logger.info(f"   Rows: {len(injured_starters):,}")
                        if 'is_depth_starter_base11' in injured_starters.columns:
                            base11_inj = (injured_starters['is_depth_starter_base11'] == 1).sum()
                            self.logger.info(f"   Base11 injured: {base11_inj:,}")
                        else:
                            self.logger.error("   ❌ is_depth_starter_base11 LOST in merge")
                        
                        if 'is_depth_starter_nickel' in injured_starters.columns:
                            nickel_inj = (injured_starters['is_depth_starter_nickel'] == 1).sum()
                            self.logger.info(f"   Nickel injured: {nickel_inj:,}")
                        else:
                            self.logger.error("   ❌ is_depth_starter_nickel LOST in merge")
                    
                    if self.logger:
                        self.logger.info(f"   Found {len(injured_starters):,} injured starter records total")
                    
                    # QB availability (most critical)
                    qb_injuries = injured_starters[
                        injured_starters['position'].str.upper().str.contains('QB', na=False)
                    ].copy()
                    
                    # Map injury status to availability (Out/Doubtful = unavailable)
                    qb_injuries['unavailable'] = qb_injuries['injury_status'].isin(['Out', 'Doubtful', 'IR', 'PUP']).astype(int)
                    
                    # Aggregate QB availability by team-week
                    qb_unavailable_grouped = qb_injuries[qb_injuries['unavailable'] == 1].groupby(
                        ['team', 'season', 'week']
                    ).size()
                    qb_unavailable = qb_unavailable_grouped.reset_index(name='qb_out')
                    
                    # Merge with games for home team
                    df = df.merge(
                        qb_unavailable.rename(columns={'team': 'home_team', 'qb_out': 'home_qb_out'}),
                        on=['home_team', 'season', 'week'],
                        how='left'
                    )
                    
                    # Merge with games for away team
                    df = df.merge(
                        qb_unavailable.rename(columns={'team': 'away_team', 'qb_out': 'away_qb_out'}),
                        on=['away_team', 'season', 'week'],
                        how='left'
                    )
                    
                    # Create availability flags (1 = available, 0 = unavailable)
                    df['home_qb_available'] = (df['home_qb_out'].fillna(0) == 0).astype(int)
                    df['away_qb_available'] = (df['away_qb_out'].fillna(0) == 0).astype(int)
                    
                    # ✅ NEW: Separate base11 and nickel injury counts
                    # Count base 11 starter injuries
                    if 'is_depth_starter_base11' in injured_starters.columns:
                        base11_injuries = injured_starters[injured_starters['is_depth_starter_base11'] == 1]
                        base11_injury_counts = (
                            base11_injuries.groupby(['team', 'season', 'week'])
                            .size()
                            .reset_index(name='starter_injuries_base11')
                        )
                        
                        # Merge with games
                        df = df.merge(
                            base11_injury_counts.rename(columns={'team': 'home_team', 'starter_injuries_base11': 'home_starter_injuries_base11'}),
                            on=['home_team', 'season', 'week'],
                            how='left'
                        )
                        df = df.merge(
                            base11_injury_counts.rename(columns={'team': 'away_team', 'starter_injuries_base11': 'away_starter_injuries_base11'}),
                            on=['away_team', 'season', 'week'],
                            how='left'
                        )
                        
                        df['home_starter_injuries_base11'] = df['home_starter_injuries_base11'].fillna(0)
                        df['away_starter_injuries_base11'] = df['away_starter_injuries_base11'].fillna(0)
                    else:
                        if self.logger:
                            self.logger.warning("⚠️ is_depth_starter_base11 column not found - base11 injuries will be 0")
                        df['home_starter_injuries_base11'] = 0
                        df['away_starter_injuries_base11'] = 0
                    
                    # Count nickel/dime starter injuries
                    if 'is_depth_starter_nickel' in injured_starters.columns:
                        nickel_injuries = injured_starters[injured_starters['is_depth_starter_nickel'] == 1]
                        nickel_injury_counts = (
                            nickel_injuries.groupby(['team', 'season', 'week'])
                            .size()
                            .reset_index(name='starter_injuries_nickel')
                        )
                        
                        # Merge with games
                        df = df.merge(
                            nickel_injury_counts.rename(columns={'team': 'home_team', 'starter_injuries_nickel': 'home_starter_injuries_nickel'}),
                            on=['home_team', 'season', 'week'],
                            how='left'
                        )
                        df = df.merge(
                            nickel_injury_counts.rename(columns={'team': 'away_team', 'starter_injuries_nickel': 'away_starter_injuries_nickel'}),
                            on=['away_team', 'season', 'week'],
                            how='left'
                        )
                        
                        df['home_starter_injuries_nickel'] = df['home_starter_injuries_nickel'].fillna(0)
                        df['away_starter_injuries_nickel'] = df['away_starter_injuries_nickel'].fillna(0)
                    else:
                        if self.logger:
                            self.logger.warning("⚠️ is_depth_starter_nickel column not found - nickel injuries will be 0")
                        df['home_starter_injuries_nickel'] = 0
                        df['away_starter_injuries_nickel'] = 0
                    
                    # ✅ KEEP combined count for backward compatibility
                    df['home_starter_injuries'] = df['home_starter_injuries_base11'] + df['home_starter_injuries_nickel']
                    df['away_starter_injuries'] = df['away_starter_injuries_base11'] + df['away_starter_injuries_nickel']
                    
                    # ═══════════════════════════════════════════════════════════════════════════
                    # Phase 2: Add Replacement Reason Features (NEW)
                    # ═══════════════════════════════════════════════════════════════════════════
                    if replacement_reasons is not None and not replacement_reasons.empty and 'replacement_reason' in replacement_reasons.columns:
                        if self.logger:
                            self.logger.info("📊 Adding replacement reason features (injury vs performance vs unknown)...")
                        
                        # Count injury-driven replacements
                        injury_replacements = replacement_reasons[replacement_reasons['replacement_reason'] == 'injury']
                        if len(injury_replacements) > 0:
                            injury_replacement_counts = (
                                injury_replacements.groupby(['team', 'season', 'week'])
                                .size()
                                .reset_index(name='injury_driven_replacements')
                            )
                            
                            # Merge with games
                            df = df.merge(
                                injury_replacement_counts.rename(columns={'team': 'home_team', 'injury_driven_replacements': 'home_injury_driven_replacements'}),
                                on=['home_team', 'season', 'week'],
                                how='left'
                            )
                            df = df.merge(
                                injury_replacement_counts.rename(columns={'team': 'away_team', 'injury_driven_replacements': 'away_injury_driven_replacements'}),
                                on=['away_team', 'season', 'week'],
                                how='left'
                            )
                            
                            df['home_injury_driven_replacements'] = df['home_injury_driven_replacements'].fillna(0)
                            df['away_injury_driven_replacements'] = df['away_injury_driven_replacements'].fillna(0)
                        else:
                            df['home_injury_driven_replacements'] = 0
                            df['away_injury_driven_replacements'] = 0
                        
                        # Count performance-driven replacements
                        performance_replacements = replacement_reasons[replacement_reasons['replacement_reason'] == 'performance']
                        if len(performance_replacements) > 0:
                            performance_replacement_counts = (
                                performance_replacements.groupby(['team', 'season', 'week'])
                                .size()
                                .reset_index(name='performance_replacements')
                            )
                            
                            # Merge with games
                            df = df.merge(
                                performance_replacement_counts.rename(columns={'team': 'home_team', 'performance_replacements': 'home_performance_replacements'}),
                                on=['home_team', 'season', 'week'],
                                how='left'
                            )
                            df = df.merge(
                                performance_replacement_counts.rename(columns={'team': 'away_team', 'performance_replacements': 'away_performance_replacements'}),
                                on=['away_team', 'season', 'week'],
                                how='left'
                            )
                            
                            df['home_performance_replacements'] = df['home_performance_replacements'].fillna(0)
                            df['away_performance_replacements'] = df['away_performance_replacements'].fillna(0)
                        else:
                            df['home_performance_replacements'] = 0
                            df['away_performance_replacements'] = 0
                        
                        # Count unknown replacements (Questionable/Probable status)
                        unknown_replacements = replacement_reasons[replacement_reasons['replacement_reason'] == 'unknown']
                        if len(unknown_replacements) > 0:
                            unknown_replacement_counts = (
                                unknown_replacements.groupby(['team', 'season', 'week'])
                                .size()
                                .reset_index(name='unknown_replacements')
                            )
                            
                            # Merge with games
                            df = df.merge(
                                unknown_replacement_counts.rename(columns={'team': 'home_team', 'unknown_replacements': 'home_unknown_replacements'}),
                                on=['home_team', 'season', 'week'],
                                how='left'
                            )
                            df = df.merge(
                                unknown_replacement_counts.rename(columns={'team': 'away_team', 'unknown_replacements': 'away_unknown_replacements'}),
                                on=['away_team', 'season', 'week'],
                                how='left'
                            )
                            
                            df['home_unknown_replacements'] = df['home_unknown_replacements'].fillna(0)
                            df['away_unknown_replacements'] = df['away_unknown_replacements'].fillna(0)
                        else:
                            df['home_unknown_replacements'] = 0
                            df['away_unknown_replacements'] = 0
                        
                        if self.logger:
                            self.logger.info(f"   ✓ Added replacement reason features")
                    else:
                        if self.logger:
                            self.logger.warning("⚠️ No replacement reasons provided - using zeros for replacement features")
                        df['home_injury_driven_replacements'] = 0
                        df['away_injury_driven_replacements'] = 0
                        df['home_performance_replacements'] = 0
                        df['away_performance_replacements'] = 0
                        df['home_unknown_replacements'] = 0
                        df['away_unknown_replacements'] = 0
                    
                    # Clean up intermediate columns
                    df = df.drop(['home_qb_out', 'away_qb_out'], axis=1, errors='ignore')
                    
                else:
                    if self.logger:
                        self.logger.warning("⚠️  Injuries missing required columns for starter merge")
                    df['home_qb_available'] = 1
                    df['away_qb_available'] = 1
                    df['home_starter_injuries'] = 0
                    df['away_starter_injuries'] = 0
            else:
                if self.logger:
                    self.logger.warning(f"⚠️  Depth chart missing required columns for starter merge (need: {team_col}, season, week, position)")
                df['home_qb_available'] = 1
                df['away_qb_available'] = 1
                df['home_starter_injuries'] = 0
                df['away_starter_injuries'] = 0
        else:
            if self.logger:
                self.logger.warning("⚠️  Depth chart missing pos_rank column")
            df['home_qb_available'] = 1
            df['away_qb_available'] = 1
            df['home_starter_injuries'] = 0
            df['away_starter_injuries'] = 0
        
        # DATA INSPECTION: Show AFTER (LESSONS_LEARNED.md lines 673-710)
        if self.logger:
            self.logger.info("📊 DATA SAMPLE - AFTER starter availability (first 5 games):")
            sample_after = df[['game_id', 'home_team', 'away_team', 'home_qb_available', 
                              'away_qb_available', 'home_starter_injuries', 'away_starter_injuries']].head(5)
            self.logger.info(f"\n{sample_after.to_string()}")
        
        # STATISTICS: Summary (CODING_GUIDE.md lines 1690-1693)
        if self.logger:
            self.logger.info(f"📊 Starter Availability Statistics:")
            self.logger.info(f"   home_qb_available: {df['home_qb_available'].sum():,} / {len(df):,} games ({df['home_qb_available'].mean()*100:.1f}%)")
            self.logger.info(f"   away_qb_available: {df['away_qb_available'].sum():,} / {len(df):,} games ({df['away_qb_available'].mean()*100:.1f}%)")
            self.logger.info(f"   home_starter_injuries: mean={df['home_starter_injuries'].mean():.2f}, max={df['home_starter_injuries'].max():.0f}")
            self.logger.info(f"   away_starter_injuries: mean={df['away_starter_injuries'].mean():.2f}, max={df['away_starter_injuries'].max():.0f}")
        
        # Games with QB injuries
        qb_injury_games = ((df['home_qb_available'] == 0) | (df['away_qb_available'] == 0)).sum()
        if self.logger:
            self.logger.info(f"   Games with QB injuries: {qb_injury_games:,} ({(qb_injury_games/len(df))*100:.1f}%)")
        
        if self.logger:
            self.logger.info(f"✓ Starter availability indicators added")
        
        return df


__all__ = ['InjuryImpactCalculator', 'SeverityClassifier']
