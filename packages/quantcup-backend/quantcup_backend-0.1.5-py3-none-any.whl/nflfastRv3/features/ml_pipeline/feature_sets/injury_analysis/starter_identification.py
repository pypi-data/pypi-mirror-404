"""
Starter Identification Module

Identifies true starters using depth chart + snap count validation.
Classifies replacement reasons (injury/performance/unknown).

Pattern: Complex algorithmic logic with clear inputs/outputs.
Extracted from lines 721-1399 of original injury_features.py.

See docs/injury_analysis/algorithm_details.md for full algorithm documentation.
"""

import pandas as pd
import numpy as np
from typing import Optional


class StarterIdentifier:
    """Identifies starters and analyzes replacements."""
    
    # Configuration constants
    SNAP_SHARE_STARTER_THRESHOLD = 0.50   # >50% snaps = effective starter
    SNAP_SHARE_INJURY_REPLACEMENT_THRESHOLD = 0.30  # <30% = injury replacement
    DEFAULT_SNAP_SHARE = 0.15  # Unknown player default assumption
    
    def __init__(self, logger=None, debug=False):
        """
        Initialize starter identifier.
        
        Args:
            logger: Optional logger instance
            debug: Enable diagnostic logging (default: False)
        """
        self.logger = logger
        self.debug = debug
    
    def identify_true_starters(self,
                                depth_chart_df: pd.DataFrame,
                                snap_counts_df: pd.DataFrame,
                                id_mapping: pd.DataFrame) -> pd.DataFrame:
        """
        Identify TRUE starters using hybrid snap counts + depth chart approach.
        
        Two-Source Strategy:
        1. **Historical Games**: Use rolling 3-game snap share
           - >50% snap share = effective starter (ACTUAL playing time)
        2. **Future Games**: Use depth chart
           - depth_team=1 = depth starter (EXPECTED playing time)
        
        This solves the "backup starting due to injury" problem:
        - Week 5: Patrick Mahomes listed QB1, plays 98% snaps → effective_starter=True
        - Week 6: Mahomes injured, Chad Henne moves to QB1 on depth chart
        - Week 7: Henne is depth_starter=True BUT rolling_3g_snap_share=0%
                 → is_injury_replacement=True (don't count as "starter injured")
        
        Data Sources:
        - snap_counts (uses pfr_player_id)
        - depth_chart/injuries (use gsis_id)
        - player_id_mapping (crosswalk pfr_player_id ↔ gsis_id)
        
        Args:
            depth_chart_df: Depth chart data (prospective/expected)
            snap_counts_df: Actual snap participation (historical reality)
            id_mapping: Player ID crosswalk (pfr_player_id ↔ gsis_id)
            
        Returns:
            DataFrame with columns:
            - gsis_id, pfr_player_id (player identifiers)
            - season, week, team
            - is_true_starter: Boolean (1 = true starter, 0 = backup)
            - rolling_3g_snap_share: Float (0-1) - 3-game average snap %
            - is_injury_replacement: Boolean (listed starter but low snap history)
            - snap_share: Float (0-1) - current week snap % (for analysis)
        
        Football Logic:
        - Snap share > depth chart for TRUE starter identification
        - Nickel backs (high snap % but not in base 11) = true starters (modern NFL)
        - Backups promoted due to injury: depth_starter=True BUT snap_share<30%
        
        Temporal Safety: Uses .shift(1) on snap shares (don't peek at current week)
        """
        if self.logger:
            self.logger.info("🎯 Identifying true starters (hybrid snap + depth chart approach)...")
        
        starters_list = []
        
        # ═══════════════════════════════════════════════════════════════════════════
        # PART 1: Snap-Based Starters (Historical Reality - "Who Actually Played")
        # ═══════════════════════════════════════════════════════════════════════════
        if not snap_counts_df.empty:
            if self.logger:
                self.logger.info("   Analyzing snap count data (historical reality)...")
            
            snap_sorted = snap_counts_df.copy().sort_values(['pfr_player_id', 'season', 'week'])
            
            # Use offense_pct or defense_pct (whichever is higher for each player)
            if 'offense_pct' in snap_sorted.columns and 'defense_pct' in snap_sorted.columns:
                # Auto-detect if data is percentage (0-100) or decimal (0-1)
                max_val = snap_sorted[['offense_pct', 'defense_pct']].max().max()
                divisor = 100.0 if max_val > 1.0 else 1.0  # Only divide by 100 if values > 1.0
                snap_sorted['snap_share'] = snap_sorted[['offense_pct', 'defense_pct']].max(axis=1) / divisor
                
                # Log detected format for debugging
                snap_min = snap_sorted['snap_share'].min()
                snap_max = snap_sorted['snap_share'].max()
                format_type = "percentage (0-100)" if divisor == 100.0 else "decimal (0-1)"
                if self.logger:
                    self.logger.info(f"   Snap data format detected: {format_type} | Range: {snap_min:.3f} - {snap_max:.3f}")
            elif 'offense_pct' in snap_sorted.columns:
                # Single column available - apply same logic
                max_val = snap_sorted['offense_pct'].max()
                divisor = 100.0 if max_val > 1.0 else 1.0
                snap_sorted['snap_share'] = snap_sorted['offense_pct'] / divisor
                if self.logger:
                    self.logger.info(f"   Using offense_pct only | Range: {snap_sorted['snap_share'].min():.3f} - {snap_sorted['snap_share'].max():.3f}")
            elif 'defense_pct' in snap_sorted.columns:
                # Single column available - apply same logic
                max_val = snap_sorted['defense_pct'].max()
                divisor = 100.0 if max_val > 1.0 else 1.0
                snap_sorted['snap_share'] = snap_sorted['defense_pct'] / divisor
                if self.logger:
                    self.logger.info(f"   Using defense_pct only | Range: {snap_sorted['snap_share'].min():.3f} - {snap_sorted['snap_share'].max():.3f}")
            else:
                if self.logger:
                    self.logger.warning("   ⚠️ No snap percentage columns found - cannot calculate snap share")
                snap_sorted['snap_share'] = 0
            
            # Validate consecutive weeks (bye week handling)
            snap_sorted['prev_week'] = snap_sorted.groupby(['pfr_player_id', 'season'])['week'].shift(1)
            snap_sorted['is_consecutive'] = (snap_sorted['week'] - snap_sorted['prev_week'] == 1) | snap_sorted['prev_week'].isna()
            
            # Rolling 3-game average (shifted by 1 to avoid current week leakage)
            snap_sorted['rolling_3g_snap_share'] = snap_sorted.groupby(['pfr_player_id', 'season'])['snap_share']\
                .transform(lambda x: x.rolling(3, min_periods=1).mean().shift(1).fillna(0))
            
            # Only use shifted snap share if consecutive weeks (null out bye week issues)
            snap_sorted.loc[~snap_sorted['is_consecutive'], 'rolling_3g_snap_share'] = np.nan
            snap_sorted['rolling_3g_snap_share'] = snap_sorted['rolling_3g_snap_share'].fillna(0)
            
            # Log non-consecutive weeks
            non_consecutive = (~snap_sorted['is_consecutive']).sum()
            if non_consecutive > 0 and self.logger:
                non_consec_pct = (non_consecutive / len(snap_sorted)) * 100
                self.logger.info(f"   Detected {non_consecutive:,} non-consecutive week transitions ({non_consec_pct:.1f}% - bye weeks)")
            
            # ✅ Phase 3: Early-season guardrail (Week 1-2)
            snap_sorted['is_early_season'] = (snap_sorted['week'] <= 2)
            
            # Use relaxed threshold for Week 1-2
            # Week 1-2: 30% threshold (lower bar due to thin history)
            # Week 3+: 50% threshold (normal bar)
            snap_sorted['effective_starter_threshold'] = np.where(
                snap_sorted['is_early_season'],
                0.30,  # Relaxed threshold for early season
                self.SNAP_SHARE_STARTER_THRESHOLD  # 0.50 for normal weeks
            )
            
            # Effective starter = played >THRESHOLD% of snaps in recent games
            # BUT: Week 1-2 with 0% snap history → NOT effective starter (fall back to depth chart)
            snap_sorted['is_effective_starter'] = np.where(
                snap_sorted['is_early_season'] & (snap_sorted['rolling_3g_snap_share'] == 0),
                0,  # Week 1-2 with no history → not effective starter
                (snap_sorted['rolling_3g_snap_share'] > snap_sorted['effective_starter_threshold']).astype(int)
            )
            
            # Log early-season handling
            early_season_count = snap_sorted['is_early_season'].sum()
            early_season_zero_history = (snap_sorted['is_early_season'] & (snap_sorted['rolling_3g_snap_share'] == 0)).sum()
            if self.logger:
                self.logger.info(f"   ✓ Phase 3 early-season guardrail applied:")
                self.logger.info(f"      Week 1-2 records: {early_season_count:,}")
                self.logger.info(f"      Week 1-2 with 0% snap history: {early_season_zero_history:,} (will trust depth chart)")
            
            # Keep only relevant columns + add team if available
            cols_to_keep = ['pfr_player_id', 'season', 'week', 'is_effective_starter', 
                           'rolling_3g_snap_share', 'snap_share']
            if 'team' in snap_sorted.columns:
                cols_to_keep.append('team')
            
            snap_starters = snap_sorted[cols_to_keep].copy()
            
            # Add gsis_id via mapping if available
            if not id_mapping.empty and 'pfr_player_id' in snap_starters.columns:
                snap_starters = snap_starters.merge(
                    id_mapping[['pfr_player_id', 'gsis_id']],
                    on='pfr_player_id',
                    how='left'
                )
                
                # Log unmapped players
                unmapped = snap_starters[snap_starters['gsis_id'].isna()]
                if len(unmapped) > 0 and self.logger:
                    unmapped_pct = (len(unmapped) / len(snap_starters)) * 100
                    self.logger.warning(f"   ⚠️ {len(unmapped):,} snap count records missing gsis_id ({unmapped_pct:.1f}%)")
                    self.logger.warning(f"      Expected ~5-10% unmapped (historical players with incomplete data)")
            
            starters_list.append(snap_starters)
            
            effective_count = snap_starters['is_effective_starter'].sum()
            if self.logger:
                self.logger.info(f"   ✓ Identified {effective_count:,} effective starters from snap counts (>{self.SNAP_SHARE_STARTER_THRESHOLD:.0%} snap share)")
            
            # Log sample distribution
            if effective_count > 0 and self.logger:
                avg_snap = snap_starters[snap_starters['is_effective_starter']==1]['rolling_3g_snap_share'].mean()
                self.logger.info(f"      Average snap share (effective starters): {avg_snap:.1%}")
        else:
            if self.logger:
                self.logger.info("   ⚠️ No snap count data - will rely on depth chart only")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # PART 2: Depth Chart Starters (Prospective - "Who Is Expected to Play")
        # ═══════════════════════════════════════════════════════════════════════════
        if not depth_chart_df.empty:
            if self.logger:
                self.logger.info("   Analyzing depth chart data (prospective/expected)...")
            
            depth_chart = depth_chart_df.copy()
            
            # Determine structure: ESPN (pos_slot, pos_rank) or simple (depth_team)
            has_espn_structure = all(col in depth_chart.columns for col in ['pos_slot', 'pos_rank'])
            
            if has_espn_structure:
                if self.logger:
                    self.logger.info("   ✓ Using ESPN depth chart structure (pos_slot, pos_rank)")
                
                # Convert to numeric
                depth_chart['pos_slot'] = pd.to_numeric(depth_chart['pos_slot'], errors='coerce').fillna(99).astype(int)
                depth_chart['pos_rank'] = pd.to_numeric(depth_chart['pos_rank'], errors='coerce').fillna(99).astype(int)
                
                # Base 11 starters: pos_rank=1 AND pos_slot<=11
                depth_chart['is_depth_starter_base11'] = (
                    (depth_chart['pos_rank'] == 1) &
                    (depth_chart['pos_slot'] <= 11)
                ).astype(int)
                
                # Nickel/Dime backs: pos_rank=1 AND pos_slot=12 OR pos_abb in special packages
                if 'pos_abb' in depth_chart.columns:
                    depth_chart['is_depth_starter_nickel'] = (
                        (depth_chart['pos_rank'] == 1) &
                        ((depth_chart['pos_slot'] == 12) | depth_chart['pos_abb'].isin(['NB', 'DB', 'SLOT', 'CB']))
                    ).astype(int)
                else:
                    # No pos_abb column - assume no nickel starters identifiable
                    depth_chart['is_depth_starter_nickel'] = 0
                
                # ✅ KEEP COMBINED FLAG for backward compatibility
                # Fill NaN values before conversion to int (prevents "cannot convert NA to integer" error)
                depth_chart['is_depth_starter'] = (
                    depth_chart['is_depth_starter_base11'].fillna(0) | depth_chart['is_depth_starter_nickel'].fillna(0)
                ).astype(int)
                
                base11_count = depth_chart['is_depth_starter_base11'].sum()
                nickel_count = depth_chart['is_depth_starter_nickel'].sum()
                combined_count = depth_chart['is_depth_starter'].sum()
                if self.logger:
                    self.logger.info(f"      Base 11 starters: {base11_count:,}")
                    self.logger.info(f"      Nickel/Dime starters: {nickel_count:,}")
                    self.logger.info(f"      Combined (base+nickel): {combined_count:,}")
                
            else:
                # ✅ FIX: No fallback needed - ESPN structure (pos_slot + pos_rank) is the only structure
                # The depth_team column does not exist in any actual data
                if self.logger:
                    self.logger.error("   ❌ ESPN structure (pos_slot, pos_rank) not detected in depth chart")
                    self.logger.error("   Available columns: " + str(list(depth_chart.columns)))
                    self.logger.error("   Cannot identify starters without pos_rank column")
                
                # Set all starter flags to 0 since we can't identify without proper structure
                depth_chart['is_depth_starter'] = 0
                depth_chart['is_depth_starter_base11'] = 0
                depth_chart['is_depth_starter_nickel'] = 0
            
            # Keep base11/nickel columns in addition to combined flag
            cols_to_keep = ['gsis_id', 'season', 'week', 'is_depth_starter',
                            'is_depth_starter_base11', 'is_depth_starter_nickel']
            if 'club_code' in depth_chart.columns:
                cols_to_keep.append('club_code')
                depth_chart = depth_chart.rename(columns={'club_code': 'team'})
                cols_to_keep[cols_to_keep.index('club_code')] = 'team'
            elif 'team' in depth_chart.columns:
                cols_to_keep.append('team')
            
            # Filter to columns that actually exist
            depth_starters = depth_chart[[c for c in cols_to_keep if c in depth_chart.columns]].copy()
            
            # Ensure base11/nickel columns exist even if not in source data
            if 'is_depth_starter_base11' not in depth_starters.columns:
                depth_starters['is_depth_starter_base11'] = 0
            if 'is_depth_starter_nickel' not in depth_starters.columns:
                depth_starters['is_depth_starter_nickel'] = 0
            
            starters_list.append(depth_starters)
            
            depth_count = depth_chart['is_depth_starter'].sum()
            if self.logger:
                self.logger.info(f"   ✓ Identified {depth_count:,} depth chart starters")
        else:
            if self.logger:
                self.logger.info("   ⚠️ No depth chart data - will rely on snap counts only")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # PART 3: Merge Snap-Based + Depth Chart
        # ═══════════════════════════════════════════════════════════════════════════
        if len(starters_list) == 0:
            if self.logger:
                self.logger.warning("⚠️ No starter data available (no snap counts or depth chart) - returning empty")
            return pd.DataFrame()
        
        if len(starters_list) == 2:
            # Have both snap counts AND depth chart - MERGE
            if self.logger:
                self.logger.info("   Merging snap counts + depth chart for hybrid identification...")
            
            snap_df = starters_list[0]  # From snap counts
            depth_df = starters_list[1]  # From depth chart
            
            # Merge on gsis_id (if available) OR pfr_player_id + season + week
            # Prefer gsis_id since both should have it now
            if 'gsis_id' in snap_df.columns and 'gsis_id' in depth_df.columns:
                merge_keys = ['gsis_id', 'season', 'week']
                if self.logger:
                    self.logger.info(f"      Merging on: {merge_keys}")
            else:
                # Fallback to team-level if player IDs not available
                merge_keys = ['team', 'season', 'week'] if 'team' in snap_df.columns and 'team' in depth_df.columns else ['season', 'week']
                if self.logger:
                    self.logger.warning(f"   ⚠️ gsis_id not available in both datasets - merging on {merge_keys} (less precise)")
            
            starters_df = snap_df.merge(
                depth_df,
                on=merge_keys,
                how='outer',
                suffixes=('_snap', '_depth')
            )
            
            # Fill NaN values
            starting_cols = len(starters_df)
            starters_df['is_effective_starter'] = starters_df.get('is_effective_starter', pd.Series([0]*starting_cols)).fillna(0).astype(int)
            starters_df['is_depth_starter'] = starters_df.get('is_depth_starter', pd.Series([0]*starting_cols)).fillna(0).astype(int)
            starters_df['rolling_3g_snap_share'] = starters_df.get('rolling_3g_snap_share', pd.Series([0.0]*starting_cols)).fillna(0.0)
            
            # TRUE STARTER = Effective (snap-based) OR Depth Chart (prospective)
            starters_df['is_true_starter'] = (
                (starters_df['is_effective_starter'] == 1) |
                (starters_df['is_depth_starter'] == 1)
            ).astype(int)
            
            # ✅ Phase 3: Apply early-season logic to injury replacement detection
            # Week 1-2 with 0% snap history = normal (not injury replacement)
            # Week 3+ with <30% snap history = injury replacement
            is_early_season_flag = starters_df.get('is_early_season', False)
            if 'is_early_season' not in starters_df.columns and 'week' in starters_df.columns:
                is_early_season_flag = (starters_df['week'] <= 2).fillna(False)
            
            # Flag injury replacements: Listed as depth starter but LOW snap history
            # BUT: Don't flag Week 1-2 starters with 0% history (no prior season data expected)
            starters_df['is_injury_replacement'] = (
                (starters_df['is_depth_starter'] == 1) &
                (starters_df['rolling_3g_snap_share'] < self.SNAP_SHARE_INJURY_REPLACEMENT_THRESHOLD) &
                (starters_df['is_effective_starter'] == 0) &
                ~(is_early_season_flag & (starters_df['rolling_3g_snap_share'] == 0))  # Exclude Week 1-2 with 0% history
            ).fillna(0).astype(int)
            
            injury_replacement_count = starters_df['is_injury_replacement'].sum()
            if injury_replacement_count > 0 and self.logger:
                self.logger.info(f"   ⚠️ Flagged {injury_replacement_count:,} injury replacements")
                self.logger.info(f"      (listed as starters but <{self.SNAP_SHARE_INJURY_REPLACEMENT_THRESHOLD:.0%} snap share - likely filling in for injured players)")
                self.logger.info(f"      Note: Week 1-2 starters with 0% history excluded (not counted as replacements)")
            
            # Handle team column merging
            if 'team_snap' in starters_df.columns and 'team_depth' in starters_df.columns:
                starters_df['team'] = starters_df['team_snap'].fillna(starters_df['team_depth'])
                starters_df = starters_df.drop(['team_snap', 'team_depth'], axis=1, errors='ignore')
            
        else:
            # Only have ONE source (either snap counts OR depth chart)
            starters_df = starters_list[0]
            
            if 'is_effective_starter' in starters_df.columns:
                # Only snap counts available
                starters_df['is_true_starter'] = starters_df['is_effective_starter']
                starters_df['is_depth_starter'] = 0  # Unknown
                starters_df['is_injury_replacement'] = 0  # Can't detect without depth chart
                if self.logger:
                    self.logger.info("   Using snap counts only (no depth chart)")
            else:
                # Only depth chart available
                starters_df['is_true_starter'] = starters_df['is_depth_starter']
                starters_df['is_effective_starter'] = 0  # Unknown
                starters_df['is_injury_replacement'] = 0  # Can't detect without snap counts
                starters_df['rolling_3g_snap_share'] = self.DEFAULT_SNAP_SHARE  # Default assumption
                if self.logger:
                    self.logger.info("   Using depth chart only (no snap counts)")
        
        # Final summary
        true_starter_count = starters_df['is_true_starter'].sum()
        if self.logger:
            self.logger.info(f"✓ Total true starters identified: {true_starter_count:,}")
        
        # Log distribution by snap share (if available)
        if 'rolling_3g_snap_share' in starters_df.columns and self.logger:
            starters_only = starters_df[starters_df['is_true_starter'] == 1]
            if len(starters_only) > 0:
                snap_dist = starters_only['rolling_3g_snap_share'].describe()
                self.logger.info(f"   Snap share distribution (true starters):")
                self.logger.info(f"      Mean: {snap_dist['mean']:.1%}, Median: {snap_dist['50%']:.1%}")
                self.logger.info(f"      Min: {snap_dist['min']:.1%}, Max: {snap_dist['max']:.1%}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # DIAGNOSTIC: QB Starter Samples & Position Breakdown
        # ═══════════════════════════════════════════════════════════════════════════
        if self.logger and not snap_counts_df.empty and 'position' in snap_counts_df.columns:
            # Merge position for analysis
            starters_with_pos = starters_df.merge(
                snap_counts_df[['pfr_player_id', 'position', 'team']].drop_duplicates(),
                on='pfr_player_id',
                how='left'
            )
            
            # Filter to true starters
            true_starters = starters_with_pos[starters_with_pos['is_true_starter'] == 1].copy()
            
            if len(true_starters) > 0:
                self.logger.info("=" * 80)
                self.logger.info("📊 STARTER IDENTIFICATION SUMMARY")
                self.logger.info("=" * 80)
                
                # QB starters sample
                qb_starters = true_starters[
                    true_starters['position'].str.upper().str.contains('QB', na=False)
                ]
                
                if len(qb_starters) > 0:
                    self.logger.info(f"\n🏈 QB STARTERS (Sample - First 10):")
                    display_cols = ['team', 'season', 'week', 'rolling_3g_snap_share', 'is_injury_replacement']
                    sample = qb_starters[display_cols].head(10)
                    self.logger.info(f"\n{sample.to_string(index=False)}")
                    self.logger.info(f"\n   Total QB starters: {len(qb_starters):,}")
                
                # Starters per team
                if 'team' in true_starters.columns:
                    team_counts = true_starters.groupby('team').size().sort_values(ascending=False)
                    self.logger.info(f"\n📍 STARTERS PER TEAM (Top 10):")
                    for team, count in team_counts.head(10).items():
                        self.logger.info(f"   {team}: {count:,} starters")
                
                # Position distribution
                if 'position' in true_starters.columns:
                    pos_dist = true_starters['position'].value_counts().head(10)
                    self.logger.info(f"\n📋 TOP POSITIONS:")
                    for pos, count in pos_dist.items():
                        self.logger.info(f"   {pos}: {count:,} starters")
                
                self.logger.info("=" * 80)
        
        return starters_df
    
    def classify_replacement_reason(self,
                                      starters_df: pd.DataFrame,
                                      injuries_df: pd.DataFrame,
                                      snap_counts_df: pd.DataFrame) -> pd.DataFrame:
        """
        Classify whether starter replacements are injury-driven, performance-driven, or unknown.
        
        Logic:
        1. Identify incumbent (player with highest snap share at each position in prior games)
        2. Compare to current depth chart starter
        3. If different, check if incumbent is on injury report
        4. Classify based on severity:
           - 'injury': Incumbent Out/Doubtful/IR/PUP (definitive absences)
           - 'unknown': Incumbent Questionable/Probable (mixed evidence)
           - 'performance': Incumbent healthy but not starting (benched/role change)
           - None: No replacement (same starter continues)
        
        Args:
            starters_df: DataFrame from identify_true_starters() with snap/depth data
            injuries_df: DataFrame with injury reports
            snap_counts_df: DataFrame with snap counts for position mapping
            
        Returns:
            DataFrame with columns: gsis_id, team, season, week, replacement_reason
        """
        if self.logger:
            self.logger.info("📊 Classifying replacement reasons (injury vs performance vs unknown)...")
        
        # Validate required data exists
        if starters_df.empty:
            if self.logger:
                self.logger.warning("⚠️ No starters data - cannot classify replacements")
            return pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
        
        if injuries_df.empty:
            if self.logger:
                self.logger.warning("⚠️ No injuries data - cannot classify replacements")
            return pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
        
        # Check required columns in starters_df
        required_starter_cols = ['team', 'gsis_id', 'season', 'week', 'is_depth_starter', 'rolling_3g_snap_share']
        missing_starter = [c for c in required_starter_cols if c not in starters_df.columns]
        if missing_starter:
            if self.logger:
                self.logger.error(f"❌ Cannot classify replacements - starters_df missing columns: {missing_starter}")
            return pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
        
        # Check required columns in injuries_df
        required_injury_cols = ['gsis_id', 'season', 'week', 'injury_status']
        # Handle report_status vs injury_status
        if 'report_status' in injuries_df.columns and 'injury_status' not in injuries_df.columns:
            injuries_df = injuries_df.rename(columns={'report_status': 'injury_status'})
        
        missing_injury = [c for c in required_injury_cols if c not in injuries_df.columns]
        if missing_injury:
            if self.logger:
                self.logger.error(f"❌ Cannot classify replacements - injuries_df missing columns: {missing_injury}")
            return pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
        
        # Merge position data from snap counts if not already in starters_df
        if 'position' not in starters_df.columns and not snap_counts_df.empty:
            if self.logger:
                self.logger.info("   Merging position data from snap counts...")
            if 'position' in snap_counts_df.columns and 'pfr_player_id' in starters_df.columns:
                # Get position for each player (use most common position)
                player_positions = (
                    snap_counts_df[['pfr_player_id', 'position']]
                    .dropna()
                    .drop_duplicates()
                    .groupby('pfr_player_id')['position']
                    .first()  # Take first position if player has multiple
                    .reset_index()
                )
                
                starters_df = starters_df.merge(
                    player_positions,
                    on='pfr_player_id',
                    how='left'
                )
                
                if 'position' in starters_df.columns and self.logger:
                    self.logger.info(f"      ✓ Merged positions for {starters_df['position'].notna().sum():,} players")
                else:
                    if self.logger:
                        self.logger.warning("      ⚠️ Position merge failed")
        
        # Determine position column to use
        position_col = None
        if 'position' in starters_df.columns:
            position_col = 'position'
        elif 'position_slot' in starters_df.columns:
            position_col = 'position_slot'
            if self.logger:
                self.logger.info("   Using position_slot as fallback position identifier")
        else:
            if self.logger:
                self.logger.error("❌ No position column available - cannot track position-specific replacements")
            return pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
        
        # Filter out Week 1-2 players with no snap history to avoid false positives
        pre_filter_count = len(starters_df)
        early_season_no_history = (
            (starters_df['week'] <= 2) &
            (starters_df['rolling_3g_snap_share'] == 0)
        )
        
        if early_season_no_history.sum() > 0 and self.logger:
            self.logger.info(f"   ⚠️ Filtering {early_season_no_history.sum():,} Week 1-2 players with no snap history (avoid false replacements)")
            starters_analysis = starters_df[~early_season_no_history].copy()
        else:
            starters_analysis = starters_df.copy()
        
        if len(starters_analysis) == 0:
            if self.logger:
                self.logger.warning("⚠️ No players remaining after filtering - cannot classify replacements")
            return pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
        
        # ═══════════════════════════════════════════════════════════════════════════
        # STEP 1: Identify Incumbents (highest snap share per position in prior games)
        # ═══════════════════════════════════════════════════════════════════════════
        if self.logger:
            self.logger.info("   Identifying incumbents (prior snap leaders by position)...")
        
        # Only consider players with snap history
        players_with_history = starters_analysis[starters_analysis['rolling_3g_snap_share'] > 0].copy()
        
        if len(players_with_history) == 0:
            if self.logger:
                self.logger.warning("⚠️ No players with snap history - cannot identify incumbents")
            return pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
        
        # Get player with highest snap share for each team-position-week
        # Use idxmax() to reliably get the index of max value
        incumbent_indices = (
            players_with_history
            .groupby(['team', position_col, 'season', 'week'])['rolling_3g_snap_share']
            .idxmax()
        )
        
        incumbents = players_with_history.loc[incumbent_indices][
            ['team', position_col, 'season', 'week', 'gsis_id', 'rolling_3g_snap_share']
        ].copy()
        
        incumbents = incumbents.rename(columns={
            'gsis_id': 'incumbent_gsis_id',
            'rolling_3g_snap_share': 'incumbent_snap_share'
        })
        
        if self.logger:
            self.logger.info(f"      ✓ Identified {len(incumbents):,} incumbents across {incumbents['team'].nunique()} teams")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # STEP 2: Get Current Depth Chart Starters
        # ═══════════════════════════════════════════════════════════════════════════
        depth_starters = starters_analysis[starters_analysis['is_depth_starter'] == 1][
            ['team', position_col, 'season', 'week', 'gsis_id']
        ].copy()
        
        if len(depth_starters) == 0:
            if self.logger:
                self.logger.warning("⚠️ No depth chart starters found - cannot identify replacements")
            return pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
        
        if self.logger:
            self.logger.info(f"      ✓ Found {len(depth_starters):,} current depth chart starters")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # STEP 3: Merge to Find Replacements (current starter != incumbent)
        # ═══════════════════════════════════════════════════════════════════════════
        replacements = depth_starters.merge(
            incumbents,
            on=['team', position_col, 'season', 'week'],
            how='left'
        )
        
        # Flag replacements (current starter is different from incumbent)
        replacements['is_replacement'] = (
            (replacements['gsis_id'] != replacements['incumbent_gsis_id']) &
            replacements['incumbent_gsis_id'].notna()
        )
        
        replacement_count = replacements['is_replacement'].sum()
        if self.logger:
            self.logger.info(f"      ✓ Detected {replacement_count:,} position replacements")
        
        if replacement_count == 0:
            if self.logger:
                self.logger.info("   No replacements detected - all depth starters match incumbents")
            return pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
        
        # ═══════════════════════════════════════════════════════════════════════════
        # STEP 4: Check Injury Status of Incumbents (3-bucket classification)
        # ═══════════════════════════════════════════════════════════════════════════
        if self.logger:
            self.logger.info("   Checking injury status of incumbents...")
        
        # ✅ DIAGNOSTIC: Check injuries_df coverage before filtering
        if self.debug and self.logger:
            self.logger.info("🔍 DIAGNOSTIC - Injury data before filtering:")
            self.logger.info(f"   Total injury records: {len(injuries_df):,}")
            self.logger.info(f"   Unique players in injuries: {injuries_df['gsis_id'].nunique():,}")
            self.logger.info(f"   Injury status distribution: {injuries_df['injury_status'].value_counts().to_dict()}")
        
        # Bucket 1: Serious injuries (Out/Doubtful/IR/PUP) → 'injury'
        serious_injuries = injuries_df[
            injuries_df['injury_status'].isin(['Out', 'Doubtful', 'IR', 'PUP'])
        ][['gsis_id', 'season', 'week']].drop_duplicates()
        serious_injuries['injury_bucket'] = 'serious'
        
        # Bucket 2: Questionable injuries (Questionable/Probable) → 'unknown'
        questionable_injuries = injuries_df[
            injuries_df['injury_status'].isin(['Questionable', 'Probable'])
        ][['gsis_id', 'season', 'week']].drop_duplicates()
        questionable_injuries['injury_bucket'] = 'questionable'
        
        # ✅ DIAGNOSTIC: Check injury bucket sizes
        if self.debug and self.logger:
            self.logger.info("🔍 DIAGNOSTIC - Injury buckets created:")
            self.logger.info(f"   Serious injuries (Out/Doubtful/IR/PUP): {len(serious_injuries):,} player-weeks")
            self.logger.info(f"   Questionable injuries: {len(questionable_injuries):,} player-weeks")
        
        # Combine injury buckets
        injury_buckets = pd.concat([serious_injuries, questionable_injuries], ignore_index=True)
        
        # ✅ FIX: Create prior-week injury lookup
        # Problem: Incumbent injured in Week N, replacement detected in Week N+1
        # Solution: Shift injury weeks forward by 1 (injury in Week N shows up as Week N+1)
        injury_buckets_shifted = injury_buckets.copy()
        injury_buckets_shifted['week'] = injury_buckets_shifted['week'] + 1
        injury_buckets_shifted = injury_buckets_shifted.rename(columns={'gsis_id': 'incumbent_gsis_id'})
        
        if self.logger:
            self.logger.info(f"🔧 Created prior-week injury lookup: {len(injury_buckets_shifted):,} player-weeks")
            self.logger.info("   Matching Week N+1 replacements to Week N injuries (temporal alignment fix)")
        
        # ✅ DIAGNOSTIC: Check incumbent coverage in injuries
        if self.debug and self.logger:
            unique_incumbents = replacements['incumbent_gsis_id'].dropna().nunique()
            incumbents_in_injuries = replacements['incumbent_gsis_id'].isin(injury_buckets_shifted['incumbent_gsis_id']).sum()
            self.logger.info("🔍 DIAGNOSTIC - Incumbent injury coverage (prior-week lookup):")
            self.logger.info(f"   Unique incumbents being replaced: {unique_incumbents:,}")
            self.logger.info(f"   Incumbents found in injury data: {incumbents_in_injuries:,}")
            self.logger.info(f"   Coverage: {(incumbents_in_injuries/unique_incumbents)*100:.1f}%")
        
        # Merge with replacements using PRIOR week's injury status
        replacements = replacements.merge(
            injury_buckets_shifted[['incumbent_gsis_id', 'season', 'week', 'injury_bucket']],
            on=['incumbent_gsis_id', 'season', 'week'],  # ← Now matches Week N+1 replacement to Week N injury
            how='left'
        )
        
        # ✅ DIAGNOSTIC: Check merge results
        if self.debug and self.logger:
            matched_serious = (replacements['injury_bucket'] == 'serious').sum()
            matched_questionable = (replacements['injury_bucket'] == 'questionable').sum()
            matched_none = replacements['injury_bucket'].isna().sum()
            self.logger.info("🔍 DIAGNOSTIC - Prior-week injury merge results:")
            self.logger.info(f"   Matched to serious injuries (prior week): {matched_serious:,}")
            self.logger.info(f"   Matched to questionable (prior week): {matched_questionable:,}")
            self.logger.info(f"   No match (healthy/not reported): {matched_none:,}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # STEP 5: Classify Replacement Reason
        # ═══════════════════════════════════════════════════════════════════════════
        # Use None instead of np.nan to avoid dtype promotion errors
        replacements['replacement_reason'] = np.where(
            ~replacements['is_replacement'],
            None,  # Not a replacement (use None for compatibility with strings)
            np.where(
                replacements['injury_bucket'] == 'serious',
                'injury',  # Incumbent has serious injury
                np.where(
                    replacements['injury_bucket'] == 'questionable',
                    'unknown',  # Incumbent questionable/probable (mixed evidence)
                    'performance'  # Incumbent healthy but not starting
                )
            )
        )
        
        # ═══════════════════════════════════════════════════════════════════════════
        # STEP 6: Log Summary and Validation Samples
        # ═══════════════════════════════════════════════════════════════════════════
        total_replacements = replacements['is_replacement'].sum()
        injury_driven = (replacements['replacement_reason'] == 'injury').sum()
        performance_driven = (replacements['replacement_reason'] == 'performance').sum()
        unknown_driven = (replacements['replacement_reason'] == 'unknown').sum()
        
        # ✅ DIAGNOSTIC: Check injury bucket distribution
        if self.debug and self.logger:
            self.logger.info("🔍 DIAGNOSTIC - Replacement reason classification:")
            self.logger.info(f"   Total replacements detected: {total_replacements:,}")
            if 'injury_bucket' in replacements.columns:
                bucket_dist = replacements['injury_bucket'].value_counts()
                self.logger.info(f"   Injury bucket distribution: {bucket_dist.to_dict()}")
                self.logger.info(f"   Serious injuries: {(replacements['injury_bucket'] == 'serious').sum():,}")
                self.logger.info(f"   Questionable injuries: {(replacements['injury_bucket'] == 'questionable').sum():,}")
                self.logger.info(f"   No injury data: {replacements['injury_bucket'].isna().sum():,}")
            else:
                self.logger.error("   ❌ injury_bucket column missing")
        
        if self.logger:
            self.logger.info(f"   ✓ Classified {total_replacements:,} replacements:")
            self.logger.info(f"      Injury-driven:      {injury_driven:,} ({(injury_driven/total_replacements)*100:.1f}%)")
            self.logger.info(f"      Performance-driven: {performance_driven:,} ({(performance_driven/total_replacements)*100:.1f}%)")
            self.logger.info(f"      Unknown (mixed):    {unknown_driven:,} ({(unknown_driven/total_replacements)*100:.1f}%)")
        
        # ✅ VALIDATION: Sanity check on distribution (expected: 40-70% injury-driven)
        if total_replacements > 0 and self.logger:
            injury_pct = (injury_driven / total_replacements) * 100
            performance_pct = (performance_driven / total_replacements) * 100
            
            if injury_pct < 20:
                self.logger.warning(f"⚠️ Suspiciously low injury-driven replacements ({injury_pct:.1f}%)")
                self.logger.warning("   Expected: 40-70% of replacements due to injuries")
                self.logger.warning("   Check: Week alignment, injury data coverage, or merge logic")
            elif performance_pct > 70:
                self.logger.warning(f"⚠️ Suspiciously high performance-driven replacements ({performance_pct:.1f}%)")
                self.logger.warning("   Expected: 20-40% of replacements due to benching/role changes")
                self.logger.warning("   Check: Are injuries being missed in the merge?")
            else:
                self.logger.info(f"   ✓ Distribution within expected range (injury-driven: {injury_pct:.1f}%)")
        
        # Log sample injury-driven replacements for validation
        if injury_driven > 0 and self.logger:
            injury_samples = replacements[replacements['replacement_reason'] == 'injury'].head(3)
            self.logger.info("   Sample injury-driven replacements:")
            for _, row in injury_samples.iterrows():
                self.logger.info(f"      {row['team']} {row[position_col]} Week {row['week']}: New starter (incumbent injured)")
        
        # Return classification results
        return replacements[['gsis_id', 'team', 'season', 'week', 'replacement_reason']].copy()


__all__ = ['StarterIdentifier']
