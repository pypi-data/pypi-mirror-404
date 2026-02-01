"""
Nickel Package Validation Module

Handles nickel (5 DBs) package analysis and depth chart validation
for defensive backs in nickel-heavy games.

Pattern: Domain-specific validation logic.
Extracted from lines 1391-1659 of original injury_features.py.

See docs/injury_analysis/algorithm_details.md for full algorithm documentation.
"""

import pandas as pd
import numpy as np
import re
from typing import Optional


class NickelValidator:
    """Validates nickel package usage and DB depth charts."""
    
    # Configuration constants
    LOW_USAGE_THRESHOLD = 0.20  # <20% nickel usage means NB is not a real starter
    NICKEL_DB_COUNT_THRESHOLD = 5  # 5+ DBs = nickel/dime package
    
    def __init__(self, logger=None, debug=False):
        """
        Initialize nickel validator.
        
        Args:
            logger: Optional logger instance
            debug: Enable diagnostic logging (default: False)
        """
        self.logger = logger
        self.debug = debug
    
    def calculate_nickel_usage(self, participation_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate nickel package usage % per team-week (Phase 4).
        
        Nickel definition: 5+ defensive backs on field
        Based on confirmed schema: defense_personnel = "# DL, # LB, # DB"
        
        Examples from actual data:
        - "4 DL, 2 LB, 5 DB" → 5 DBs (nickel)
        - "4 DL, 3 LB, 4 DB" → 4 DBs (base)
        - "3 DL, 3 LB, 5 DB" → 5 DBs (nickel variant)
        - "2 DL, 4 LB, 5 DB" → 5 DBs (nickel variant)
        
        Args:
            participation_df: Play-level participation data
            
        Returns:
            DataFrame with columns:
            - team: Defensive team code
            - season: Season year
            - week: Week number
            - nickel_usage_pct: % of snaps with 5+ DBs (0.0-1.0)
            - total_snaps: Total defensive snaps (for validation)
            - avg_db_count: Average DBs per snap (for analysis)
        """
        if self.logger:
            self.logger.info("   Calculating nickel usage rates from play-level data...")
        
        if participation_df.empty:
            return pd.DataFrame()
        
        # Extract DB count from "# DL, # LB, # DB" format
        def extract_db_count(personnel_str):
            """
            Parse defense_personnel string to extract DB count.
            
            Examples:
            - "4 DL, 2 LB, 5 DB" → 5 (nickel)
            - "4 DL, 3 LB, 4 DB" → 4 (base)
            - "3 DL, 3 LB, 5 DB" → 5 (nickel variant)
            - "2 DL, 4 LB, 5 DB" → 5 (nickel variant)
            """
            if pd.isna(personnel_str) or personnel_str == '':
                return np.nan
            
            try:
                # Use regex to extract "#DB" pattern
                # Pattern: "(\d+)\s*DB" captures digit(s) before "DB"
                match = re.search(r'(\d+)\s*DB', str(personnel_str))
                if match:
                    return int(match.group(1))
            except Exception:
                pass
            
            return np.nan
        
        # Apply extraction to all rows
        participation_df['db_count'] = participation_df['defense_personnel'].apply(extract_db_count)
        
        # Log extraction success
        valid_counts = participation_df['db_count'].notna().sum()
        total_rows = len(participation_df)
        valid_pct = (valid_counts / total_rows) * 100 if total_rows > 0 else 0
        if self.logger:
            self.logger.info(f"      ✓ Extracted DB counts for {valid_counts:,}/{total_rows:,} plays ({valid_pct:.1f}%)")
        
        # Log sample extractions for validation
        sample_extracts = participation_df[['defense_personnel', 'db_count']].dropna().head(5)
        if len(sample_extracts) > 0 and self.logger:
            self.logger.info("      Sample extractions:")
            for _, row in sample_extracts.iterrows():
                self.logger.info(f"         '{row['defense_personnel']}' → {row['db_count']} DBs")
        
        # Filter to plays with valid DB counts
        participation_clean = participation_df[participation_df['db_count'].notna()].copy()
        
        # Identify nickel/dime packages (5+ DBs)
        participation_clean['is_nickel_or_dime'] = (participation_clean['db_count'] >= self.NICKEL_DB_COUNT_THRESHOLD).astype(int)
        
        # Extract teams from game_id: "2016_01_CAR_DEN" → CAR (away), DEN (home)
        participation_clean[['season_parsed', 'week_parsed', 'away_team', 'home_team']] = (
            participation_clean['nflverse_game_id'].str.split('_', n=3, expand=True)
        )
        
        # Determine defensive team: If possession_team == home_team, defense = away_team (and vice versa)
        participation_clean['defense_team'] = np.where(
            participation_clean['possession_team'] == participation_clean['home_team'],
            participation_clean['away_team'],
            np.where(
                participation_clean['possession_team'] == participation_clean['away_team'],
                participation_clean['home_team'],
                np.nan  # Can't determine (shouldn't happen)
            )
        )
        
        # Filter out plays where we can't determine defensive team
        pre_filter = len(participation_clean)
        participation_clean = participation_clean[participation_clean['defense_team'].notna()]
        post_filter = len(participation_clean)
        
        if pre_filter != post_filter and self.logger:
            dropped = pre_filter - post_filter
            self.logger.warning(f"      ⚠️ Dropped {dropped:,} plays where defense_team couldn't be determined")
        
        # Aggregate to team-week level
        # Calculate: % of defensive snaps with 5+ DBs
        team_package_usage = (
            participation_clean
            .groupby(['defense_team', 'season', 'week'])
            .agg({
                'is_nickel_or_dime': 'mean',  # % of snaps with 5+ DBs
                'play_id': 'count',  # Total defensive snaps
                'db_count': 'mean'  # Average DBs per snap
            })
            .reset_index()
            .rename(columns={
                'defense_team': 'team',
                'is_nickel_or_dime': 'nickel_usage_pct',
                'play_id': 'total_snaps',
                'db_count': 'avg_db_count'
            })
        )
        
        if self.logger:
            self.logger.info(f"      ✓ Calculated nickel usage for {len(team_package_usage):,} team-weeks")
        
        # Log validation samples
        if self.logger:
            self.logger.info("      Sample nickel usage rates:")
        
        # Show highest usage teams (nickel-heavy defenses)
        high_usage = team_package_usage.nlargest(3, 'nickel_usage_pct')
        if self.logger:
            for _, row in high_usage.iterrows():
                self.logger.info(f"         HIGH: {row['team']} Week {row['week']}: {row['nickel_usage_pct']:.1%} nickel ({row['total_snaps']:.0f} snaps, avg {row['avg_db_count']:.1f} DBs)")
        
        # Show lowest usage teams (base-heavy defenses)
        low_usage = team_package_usage.nsmallest(3, 'nickel_usage_pct')
        if self.logger:
            for _, row in low_usage.iterrows():
                self.logger.info(f"         LOW:  {row['team']} Week {row['week']}: {row['nickel_usage_pct']:.1%} nickel ({row['total_snaps']:.0f} snaps, avg {row['avg_db_count']:.1f} DBs)")
        
        # Log overall stats
        avg_nickel_usage = team_package_usage['nickel_usage_pct'].mean()
        if self.logger:
            self.logger.info(f"      League average nickel usage: {avg_nickel_usage:.1%}")
        
        return team_package_usage
    
    def validate_nickel_starters(self,
                                  depth_chart_df: pd.DataFrame,
                                  participation_df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate nickel starter designations against actual package usage (Phase 4).
        
        Logic:
        1. Calculate team-week nickel usage % from participation data
        2. Merge with depth chart
        3. Override is_depth_starter_nickel=0 if team plays <20% nickel
        4. Log all overrides for transparency
        
        Rationale: If a team rarely plays nickel (e.g., <20% of snaps), then their listed
        "nickel back" is not truly a starter and shouldn't count as an injured starter.
        
        Args:
            depth_chart_df: Depth chart with is_depth_starter_nickel flags
            participation_df: Play-level participation data
            
        Returns:
            Depth chart with validated nickel designations
        """
        if self.logger:
            self.logger.info("📊 Validating nickel starter designations against actual usage...")
        
        if depth_chart_df.empty or participation_df.empty:
            if self.logger:
                self.logger.warning("⚠️ Cannot validate - missing depth chart or participation data")
            return depth_chart_df
        
        # Calculate package usage rates
        team_package_usage = self.calculate_nickel_usage(participation_df)
        
        if team_package_usage.empty:
            if self.logger:
                self.logger.warning("⚠️ No package usage calculated - skipping validation")
            return depth_chart_df
        
        # Determine team column name in depth chart
        team_col = 'club_code' if 'club_code' in depth_chart_df.columns else 'team'
        
        # Merge depth chart with usage rates
        pre_merge_count = len(depth_chart_df)
        
        depth_chart = depth_chart_df.merge(
            team_package_usage[['team', 'season', 'week', 'nickel_usage_pct', 'total_snaps', 'avg_db_count']],
            left_on=[team_col, 'season', 'week'],
            right_on=['team', 'season', 'week'],
            how='left'
        )
        
        # Clean up duplicate team column if merge created one
        if 'team' in depth_chart.columns and team_col == 'club_code':
            depth_chart = depth_chart.drop('team', axis=1)
        
        post_merge_count = len(depth_chart)
        
        # Validate merge didn't change row count
        if post_merge_count != pre_merge_count:
            if self.logger:
                self.logger.error(f"❌ Merge changed row count: {pre_merge_count} → {post_merge_count}")
            return depth_chart_df  # Return original if merge failed
        
        # Log merge coverage
        merged_count = depth_chart['nickel_usage_pct'].notna().sum()
        merge_pct = (merged_count / len(depth_chart)) * 100 if len(depth_chart) > 0 else 0
        if self.logger:
            self.logger.info(f"   ✓ Merged nickel usage data: {merged_count:,}/{len(depth_chart):,} rows ({merge_pct:.1f}%)")
        
        # Fill missing usage rates with team's season average
        depth_chart['nickel_usage_pct'] = depth_chart.groupby([team_col, 'season'])['nickel_usage_pct'].transform(
            lambda x: x.fillna(x.mean())
        )
        
        # If still missing, use league average
        league_avg_nickel = depth_chart['nickel_usage_pct'].mean()
        depth_chart['nickel_usage_pct'] = depth_chart['nickel_usage_pct'].fillna(league_avg_nickel)
        
        if self.logger:
            self.logger.info(f"   League average nickel usage: {league_avg_nickel:.1%}")
        
        # Identify and override low-usage nickel designations
        # Threshold: <20% nickel usage means NB is not a real starter
        
        # Count nickel starters before override
        nickel_starters_pre = depth_chart.get('is_depth_starter_nickel', pd.Series([0]*len(depth_chart))).sum()
        
        # Identify rows to override
        override_mask = (
            (depth_chart.get('is_depth_starter_nickel', 0) == 1) &
            (depth_chart['nickel_usage_pct'] < self.LOW_USAGE_THRESHOLD)
        )
        
        override_count = override_mask.sum()
        
        if override_count > 0:
            if self.logger:
                self.logger.info(f"   ⚠️ Overriding {override_count:,} nickel starters (team usage <{self.LOW_USAGE_THRESHOLD:.0%})")
            
            # Log sample overrides for transparency
            overrides = depth_chart[override_mask].head(10)
            if self.logger:
                self.logger.info("      Sample overrides:")
                for _, row in overrides.iterrows():
                    team_name = row.get(team_col, 'UNK')
                    usage = row.get('nickel_usage_pct', 0)
                    snaps = row.get('total_snaps', 0)
                    self.logger.info(f"         {team_name} Week {row['week']}: Listed NB but only {usage:.1%} nickel usage ({snaps:.0f} snaps)")
            
            # Apply override
            if 'is_depth_starter_nickel' in depth_chart.columns:
                depth_chart.loc[override_mask, 'is_depth_starter_nickel'] = 0
            
            # Count after override
            nickel_starters_post = depth_chart.get('is_depth_starter_nickel', pd.Series([0]*len(depth_chart))).sum()
            
            if self.logger:
                self.logger.info(f"   ✓ Nickel starters: {nickel_starters_pre} → {nickel_starters_post} (removed {override_count})")
            
            # Update combined flag if it exists
            if 'is_depth_starter' in depth_chart.columns and 'is_depth_starter_base11' in depth_chart.columns:
                # Fill NaN values before conversion to int (prevents "cannot convert NA to integer" error)
                depth_chart['is_depth_starter'] = (
                    depth_chart['is_depth_starter_base11'].fillna(0) | depth_chart['is_depth_starter_nickel'].fillna(0)
                ).astype(int)
        else:
            if self.logger:
                self.logger.info(f"   ✓ All {nickel_starters_pre} nickel designations validated (no overrides needed)")
        
        # Clean up intermediate columns
        depth_chart = depth_chart.drop(['total_snaps', 'avg_db_count'], axis=1, errors='ignore')
        
        return depth_chart


__all__ = ['NickelValidator']
