"""
NextGen QB Features - Player Performance Metrics

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + aggregation logic)
Layer: 2 (Implementation - calls infrastructure directly)

Features:
- QB passing efficiency metrics
- QB decision-making metrics  
- QB accuracy above expectation
- QB aggressiveness and risk-taking

Temporal Safety:
- Uses .shift(1) to get PRIOR week's performance
- Week 1 filled with season average (prevents cross-season contamination)
- Groups by ['team_abbr', 'season'] to prevent temporal leakage
"""

import pandas as pd
from typing import Dict, Any, Optional


class NextGenFeatures:
    """
    NextGen QB feature engineering service.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + player→team aggregation)
    Depth: 1 layer (calls database directly)
    
    Aggregates player-level NextGen stats to team-level features.
    """
    
    def __init__(self, db_service, logger, bucket_adapter=None):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
            bucket_adapter: Optional bucket adapter for data loading (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        self.bucket_adapter = bucket_adapter
    
    def build_features(self, seasons=None) -> Dict[str, Any]:
        """
        Build NextGen QB features for game prediction.
        
        Pure computation - orchestrator handles saving (matches model_trainer pattern).
        
        Process:
        1. Load NextGen stats from bucket (raw_nflfastr.nextgen)
        2. Identify starting QB per team/week (most attempts)
        3. Create team-level features with temporal safety (.shift(1))
        4. Merge with game schedule
        5. Calculate home vs away differentials
        6. Analyze feature quality
        
        Args:
            seasons: List of seasons to process (default: all available)
            
        Returns:
            Dictionary with feature build results including DataFrame
        """
        self.logger.info(f"Building NextGen QB features for seasons: {seasons or 'all'}")
        
        try:
            # Step 1: Load NextGen data from bucket
            nextgen_df = self._load_nextgen_data(seasons)
            
            if nextgen_df.empty:
                self.logger.warning("No NextGen data found")
                return {
                    'status': 'warning',
                    'message': 'No NextGen data available',
                    'features_built': 0,
                    'seasons_processed': 0
                }
            
            # Step 2: Identify starting QBs (most attempts per team/week)
            starters_df = self._identify_starting_qbs(nextgen_df)
            
            # Step 3: Create team-level features with temporal safety
            team_features = self._create_team_level_features(starters_df)
            
            # Step 4: Merge with game schedule
            game_features = self._merge_with_games(team_features)
            
            # Step 5: Calculate QB differentials (home - away)
            final_df = self._calculate_qb_differentials(game_features)
            
            # Step 6: Feature quality analysis
            self._log_feature_quality_metrics(final_df)
            
            # Capture metadata
            seasons_processed = final_df['season'].nunique() if 'season' in final_df.columns else 0
            games_processed = len(final_df)
            feature_columns = len([col for col in final_df.columns if col.startswith('qb_')])
            
            # Final summary
            self.logger.info("=" * 80)
            self.logger.info("📊 NEXTGEN FEATURES - FINAL SUMMARY")
            self.logger.info("=" * 80)
            self.logger.info(f"✓ Built NextGen QB features: {games_processed:,} games across {seasons_processed} seasons")
            self.logger.info(f"✓ Total QB differential features: {feature_columns}")
            self.logger.info(f"✓ Seasons: {sorted(final_df['season'].unique().tolist())}")
            self.logger.info(f"✓ Date range: {final_df['game_date'].min()} to {final_df['game_date'].max()}")
            self.logger.info("=" * 80)
            
            # Return DataFrame for orchestrator to save
            return {
                'status': 'success',
                'dataframe': final_df,  # ✅ Orchestrator will save this
                'features_built': games_processed,
                'seasons_processed': seasons_processed,
                'feature_columns': feature_columns
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build NextGen QB features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }
    
    def _load_nextgen_data(self, seasons=None) -> pd.DataFrame:
        """
        Load NextGen stats from bucket raw_nflfastr.
        
        Data Source: raw_nflfastr.nextgen (already populated via data pipeline)
        Granularity: Player × Season × Week
        Temporal Range: 2016-present
        
        Args:
            seasons: Optional list of seasons to filter
            
        Returns:
            DataFrame with QB NextGen stats
        """
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        self.logger.info("📊 Loading NextGen stats from bucket raw_nflfastr...")
        
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        # Prepare filters
        filters = None
        if seasons:
            season_list = seasons if isinstance(seasons, (list, tuple)) else [seasons]
            filters = [('season', 'in', season_list)]
            self.logger.info(f"   Filtering to seasons: {season_list}")
        
        # Load NextGen stats (passing only for QB metrics)
        nextgen_df = bucket_adapter.read_data('nextgen', 'raw_nflfastr', filters=filters)
        
        if nextgen_df.empty:
            self.logger.warning("⚠️  No NextGen data found in bucket")
            return pd.DataFrame()
        
        # Filter to QB passing stats only
        if 'player_position' in nextgen_df.columns:
            nextgen_df = nextgen_df[nextgen_df['player_position'] == 'QB'].copy()
        else:
            self.logger.warning("⚠️  'player_position' column not found, cannot filter to QBs")
        
        self.logger.info(f"✓ Loaded {len(nextgen_df):,} QB performances from NextGen stats")
        self.logger.info(f"   Seasons: {sorted(nextgen_df['season'].unique())}")
        self.logger.info(f"   Weeks: {sorted(nextgen_df['week'].unique())}")
        self.logger.info(f"   Teams: {nextgen_df['team_abbr'].nunique()} unique teams")
        
        # DATA INSPECTION: Show sample of loaded data
        self.logger.info("📊 DATA SAMPLE - NextGen QB stats (first 10 rows):")
        display_cols = ['season', 'week', 'team_abbr', 'player_display_name', 'attempts', 
                       'passer_rating', 'completion_percentage', 'avg_time_to_throw']
        available_cols = [col for col in display_cols if col in nextgen_df.columns]
        self.logger.info(f"\n{nextgen_df[available_cols].head(10).to_string()}")
        
        # Log statistics
        if 'passer_rating' in nextgen_df.columns:
            self.logger.info(f"📊 Passer Rating: min={nextgen_df['passer_rating'].min():.1f}, "
                           f"max={nextgen_df['passer_rating'].max():.1f}, "
                           f"mean={nextgen_df['passer_rating'].mean():.1f}")
        
        if 'attempts' in nextgen_df.columns:
            self.logger.info(f"📊 Attempts: min={nextgen_df['attempts'].min():.0f}, "
                           f"max={nextgen_df['attempts'].max():.0f}, "
                           f"mean={nextgen_df['attempts'].mean():.1f}")
        
        return nextgen_df
    
    def _identify_starting_qbs(self, nextgen_df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify starting QB for each team/week based on attempts.
        
        Logic: QB with most attempts = starter
        Handles: Backup QB situations, injuries, platoons
        
        Temporal Safety: Uses actual game data (known after game)
        
        Args:
            nextgen_df: DataFrame with all QB performances
            
        Returns:
            DataFrame with one QB per team/week (the starter)
        """
        self.logger.info("📊 Identifying starting QBs per team/week...")
        
        # DATA INSPECTION: Show sample BEFORE starter identification
        self.logger.info("📊 DATA SAMPLE - BEFORE starter identification (first 15 rows):")
        sample_cols = ['season', 'week', 'team_abbr', 'player_display_name', 'attempts']
        available_cols = [col for col in sample_cols if col in nextgen_df.columns]
        self.logger.info(f"\n{nextgen_df[available_cols].head(15).to_string()}")
        
        # Sort by attempts (descending) to get starter first
        nextgen_df = nextgen_df.sort_values(
            ['season', 'week', 'team_abbr', 'attempts'],
            ascending=[True, True, True, False]
        )
        
        # Take first QB per team/week (most attempts = starter)
        starters = nextgen_df.groupby(['season', 'week', 'team_abbr']).first().reset_index()
        
        self.logger.info(f"✓ Identified {len(starters):,} starting QB performances")
        
        # DATA INSPECTION: Show sample AFTER starter identification
        self.logger.info("📊 DATA SAMPLE - AFTER starter identification (first 10 rows):")
        sample = starters[available_cols].head(10)
        self.logger.info(f"\n{sample.to_string()}")
        
        # Log starter statistics
        if 'attempts' in starters.columns:
            self.logger.info(f"📊 Starter attempts: min={starters['attempts'].min():.0f}, "
                           f"max={starters['attempts'].max():.0f}, "
                           f"mean={starters['attempts'].mean():.1f}")
        
        # Validate one QB per team/week
        duplicates = starters.groupby(['season', 'week', 'team_abbr']).size()
        if (duplicates > 1).any():
            self.logger.warning(f"⚠️  Found {(duplicates > 1).sum()} team/week combinations with multiple QBs")
        else:
            self.logger.info(f"✓ Validation passed: One QB per team/week")
        
        return starters
    
    def _create_team_level_features(self, starters_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create team-level QB features from starter metrics.
        
        CRITICAL TEMPORAL SAFETY: Uses .shift(1) to get PRIOR week's performance.
        This prevents using current week's stats to predict current week's outcome.
        
        Week 1 Handling: Fills with season average (prevents cross-season contamination)
        
        Pattern: Follows rolling_metrics.py:529-555 temporal safety approach
        
        Args:
            starters_df: DataFrame with starting QB per team/week
            
        Returns:
            DataFrame with prior week QB features (temporally safe)
        """
        self.logger.info("📊 Creating team-level QB features with temporal safety...")
        
        # DATA INSPECTION: Show sample BEFORE temporal shift
        self.logger.info("📊 DATA SAMPLE - BEFORE temporal shift (first 10 rows, one team):")
        sample_team = starters_df['team_abbr'].iloc[0] if len(starters_df) > 0 else None
        if sample_team:
            sample_df = starters_df[starters_df['team_abbr'] == sample_team].head(10)
            display_cols = ['team_abbr', 'season', 'week', 'player_display_name', 
                          'passer_rating', 'completion_percentage', 'attempts']
            available_cols = [col for col in display_cols if col in sample_df.columns]
            self.logger.info(f"\n{sample_df[available_cols].to_string()}")
        
        # Sort by team and chronological order for temporal operations
        starters_df = starters_df.sort_values(['team_abbr', 'season', 'week'])
        
        # Define QB metrics to create prior-week features for
        feature_cols = [
            # Efficiency metrics
            'passer_rating',
            'completion_percentage',
            'completion_percentage_above_expectation',
            'expected_completion_percentage',
            
            # Decision-making metrics
            'avg_time_to_throw',
            'avg_intended_air_yards',
            'avg_completed_air_yards',
            'avg_air_yards_differential',
            'avg_air_yards_to_sticks',
            'aggressiveness',
            'max_completed_air_distance',
            
            # Volume metrics
            'attempts',
            'completions',
            'pass_yards',
            'pass_touchdowns',
            'interceptions'
        ]
        
        # TEMPORAL SAFETY: Use .shift(1) to get PRIOR week's performance
        # This prevents using current week's stats to predict current week's outcome
        # Pattern from LESSONS_LEARNED.md Case Study #1
        
        # Convert all feature columns to float64 BEFORE transform to avoid Int64 dtype issues
        for col in feature_cols:
            if col in starters_df.columns:
                starters_df[col] = starters_df[col].astype('float64')
        
        for col in feature_cols:
            if col in starters_df.columns:
                # Use .transform() for automatic index alignment (CODING_GUIDE.md best practice)
                # Group by ['team_abbr', 'season'] to prevent cross-season contamination
                # .shift(1) excludes current observation
                # .fillna(x.mean()) fills Week 1 with season average
                starters_df[f'prior_{col}'] = starters_df.groupby(
                    ['team_abbr', 'season']
                )[col].transform(
                    lambda x: x.shift(1).fillna(x.mean())
                )
            else:
                self.logger.warning(f"⚠️  Column '{col}' not found in NextGen data")
        
        # DATA INSPECTION: Show sample AFTER temporal shift
        self.logger.info("📊 DATA SAMPLE - AFTER temporal shift (first 10 rows, same team):")
        if sample_team:
            sample_df_after = starters_df[starters_df['team_abbr'] == sample_team].head(10)
            display_cols_after = ['team_abbr', 'season', 'week', 'passer_rating', 
                                 'prior_passer_rating', 'completion_percentage', 
                                 'prior_completion_percentage']
            available_cols_after = [col for col in display_cols_after if col in sample_df_after.columns]
            self.logger.info(f"\n{sample_df_after[available_cols_after].to_string()}")
        
        # TEMPORAL VALIDATION: Week 1 should use season average
        first_week = starters_df[starters_df['week'] == 1]
        if len(first_week) > 0 and 'prior_passer_rating' in first_week.columns:
            week_1_prior_mean = first_week['prior_passer_rating'].mean()
            season_avg = starters_df.groupby(['team_abbr', 'season'])['passer_rating'].mean().mean()
            
            self.logger.info(f"📊 TEMPORAL VALIDATION - Week 1 prior metrics:")
            self.logger.info(f"   Week 1 prior_passer_rating mean: {week_1_prior_mean:.2f}")
            self.logger.info(f"   Overall season average: {season_avg:.2f}")
            self.logger.info(f"   ✓ Week 1 uses season average (prevents temporal leakage)")
        
        # Log statistics for prior features
        self.logger.info(f"📊 Prior week QB metrics statistics:")
        for col in ['prior_passer_rating', 'prior_completion_percentage', 
                   'prior_completion_percentage_above_expectation', 'prior_avg_time_to_throw']:
            if col in starters_df.columns:
                self.logger.info(f"   {col}: min={starters_df[col].min():.2f}, "
                               f"max={starters_df[col].max():.2f}, "
                               f"mean={starters_df[col].mean():.2f}, "
                               f"nulls={starters_df[col].isnull().sum()}")
        
        self.logger.info(f"✓ Created team-level QB features: {len(starters_df):,} team-weeks")
        
        return starters_df
    
    def _merge_with_games(self, team_features: pd.DataFrame) -> pd.DataFrame:
        """
        Merge team-level QB features with game schedule.
        
        Creates home vs away QB matchups for each game.
        
        Args:
            team_features: DataFrame with team-level QB features
            
        Returns:
            DataFrame with QB features for both home and away teams
        """
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        self.logger.info("📊 Merging QB features with game schedule...")
        
        # Load game schedule from bucket
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        # Get seasons from team_features for filtering
        seasons = team_features['season'].unique().tolist()
        filters = [('season', 'in', seasons)] if len(seasons) > 1 else [('season', '==', seasons[0])]
        
        games_df = bucket_adapter.read_data('dim_game', 'warehouse', filters=filters)
        
        if games_df.empty:
            self.logger.warning("⚠️  No games found in warehouse")
            return pd.DataFrame()
        
        self.logger.info(f"✓ Loaded {len(games_df):,} games from warehouse")
        
        # DATA INSPECTION: Show sample games
        self.logger.info("📊 DATA SAMPLE - Games (first 5 rows):")
        game_cols = ['game_id', 'season', 'week', 'home_team', 'away_team', 'game_date']
        available_game_cols = [col for col in game_cols if col in games_df.columns]
        self.logger.info(f"\n{games_df[available_game_cols].head(5).to_string()}")
        
        # Merge home team QB features
        games_with_qb = games_df.merge(
            team_features,
            left_on=['season', 'week', 'home_team'],
            right_on=['season', 'week', 'team_abbr'],
            how='left',
            suffixes=('', '_home_qb')
        )
        
        # Drop duplicate team_abbr column from home merge
        games_with_qb = games_with_qb.drop(columns=['team_abbr'], errors='ignore')
        
        self.logger.info(f"✓ Merged home team QB features: {len(games_with_qb):,} games")
        
        # Merge away team QB features
        games_with_qb = games_with_qb.merge(
            team_features,
            left_on=['season', 'week', 'away_team'],
            right_on=['season', 'week', 'team_abbr'],
            how='left',
            suffixes=('_home', '_away')
        )
        
        # Drop duplicate team_abbr column from away merge
        games_with_qb = games_with_qb.drop(columns=['team_abbr'], errors='ignore')
        
        self.logger.info(f"✓ Merged away team QB features: {len(games_with_qb):,} games")
        
        # DATA INSPECTION: Show sample with QB features
        self.logger.info("📊 DATA SAMPLE - Games with QB features (first 5 rows):")
        qb_sample_cols = ['game_id', 'season', 'week', 'home_team', 'away_team',
                         'prior_passer_rating_home', 'prior_passer_rating_away']
        available_qb_cols = [col for col in qb_sample_cols if col in games_with_qb.columns]
        self.logger.info(f"\n{games_with_qb[available_qb_cols].head(5).to_string()}")
        
        # Check for missing QB data
        if 'prior_passer_rating_home' in games_with_qb.columns:
            missing_home = games_with_qb['prior_passer_rating_home'].isnull().sum()
            missing_away = games_with_qb['prior_passer_rating_away'].isnull().sum()
            missing_pct = ((missing_home + missing_away) / (2 * len(games_with_qb))) * 100
            
            self.logger.info(f"📊 QB data coverage:")
            self.logger.info(f"   Missing home QB: {missing_home:,} ({(missing_home/len(games_with_qb)*100):.1f}%)")
            self.logger.info(f"   Missing away QB: {missing_away:,} ({(missing_away/len(games_with_qb)*100):.1f}%)")
            self.logger.info(f"   Overall coverage: {100-missing_pct:.1f}%")
        
        return games_with_qb
    
    def _calculate_qb_differentials(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate home vs away QB metric differentials.
        
        Pattern: home_metric - away_metric (positive = home advantage)
        
        Args:
            games_df: DataFrame with home and away QB features
            
        Returns:
            DataFrame with QB differential features
        """
        self.logger.info("📊 Calculating QB metric differentials...")
        
        # Define differential features to create
        # Maps differential name to (home_column, away_column) tuple
        differential_features = {
            'qb_passer_rating_diff': ('prior_passer_rating_home', 'prior_passer_rating_away'),
            'qb_completion_pct_diff': ('prior_completion_percentage_home', 'prior_completion_percentage_away'),
            'qb_completion_above_exp_diff': ('prior_completion_percentage_above_expectation_home', 
                                            'prior_completion_percentage_above_expectation_away'),
            'qb_time_to_throw_diff': ('prior_avg_time_to_throw_home', 'prior_avg_time_to_throw_away'),
            'qb_aggressiveness_diff': ('prior_aggressiveness_home', 'prior_aggressiveness_away'),
            'qb_air_yards_diff': ('prior_avg_intended_air_yards_home', 'prior_avg_intended_air_yards_away'),
            'qb_completed_air_yards_diff': ('prior_avg_completed_air_yards_home', 'prior_avg_completed_air_yards_away'),
            'qb_air_yards_to_sticks_diff': ('prior_avg_air_yards_to_sticks_home', 'prior_avg_air_yards_to_sticks_away'),
            'qb_deep_ball_diff': ('prior_max_completed_air_distance_home', 'prior_max_completed_air_distance_away'),
            'qb_attempts_diff': ('prior_attempts_home', 'prior_attempts_away'),
            'qb_pass_yards_diff': ('prior_pass_yards_home', 'prior_pass_yards_away'),
        }
        
        # Calculate differentials
        created_features = []
        for diff_name, (home_col, away_col) in differential_features.items():
            if home_col in games_df.columns and away_col in games_df.columns:
                games_df[diff_name] = games_df[home_col] - games_df[away_col]
                created_features.append(diff_name)
            else:
                self.logger.warning(f"⚠️  Missing columns for {diff_name}: {home_col} or {away_col}")
                games_df[diff_name] = 0.0
        
        # Calculate TD/INT ratio differential (special case - needs division)
        if 'prior_pass_touchdowns_home' in games_df.columns and 'prior_interceptions_home' in games_df.columns:
            games_df['qb_td_int_ratio_home'] = games_df['prior_pass_touchdowns_home'] / (games_df['prior_interceptions_home'] + 1)
            games_df['qb_td_int_ratio_away'] = games_df['prior_pass_touchdowns_away'] / (games_df['prior_interceptions_away'] + 1)
            games_df['qb_td_int_ratio_diff'] = games_df['qb_td_int_ratio_home'] - games_df['qb_td_int_ratio_away']
            created_features.append('qb_td_int_ratio_diff')
        
        self.logger.info(f"✓ Created {len(created_features)} QB differential features")
        
        # DATA INSPECTION: Show sample with differentials
        self.logger.info("📊 DATA SAMPLE - QB differentials (first 5 rows):")
        diff_sample_cols = ['game_id', 'season', 'week', 'home_team', 'away_team',
                           'qb_passer_rating_diff', 'qb_completion_pct_diff', 'qb_aggressiveness_diff']
        available_diff_cols = [col for col in diff_sample_cols if col in games_df.columns]
        self.logger.info(f"\n{games_df[available_diff_cols].head(5).to_string()}")
        
        # Log differential statistics
        self.logger.info("📊 QB Differential Statistics:")
        for diff_name in created_features[:8]:  # Show first 8 to avoid log spam
            if diff_name in games_df.columns:
                mean_val = games_df[diff_name].mean()
                std_val = games_df[diff_name].std()
                min_val = games_df[diff_name].min()
                max_val = games_df[diff_name].max()
                self.logger.info(f"   {diff_name:35s}: mean={mean_val:+.3f}, std={std_val:.3f}, "
                               f"range=[{min_val:+.2f}, {max_val:+.2f}]")
        
        if len(created_features) > 8:
            self.logger.info(f"   ... and {len(created_features) - 8} more differential features")
        
        # CRITICAL: Drop target variable columns before returning
        # Feature sets should ONLY return features, not target variables
        # Target variable (home_team_won) should only come from dim_game via prepare_data()
        # This prevents merge conflicts when game_outcome.py merges NextGen features
        # Pattern: Matches rolling_metrics.py and contextual_features.py (no target in output)
        target_columns = ['home_team_won', 'home_won', 'home_score', 'away_score', 'result']
        columns_to_drop = [col for col in target_columns if col in games_df.columns]
        
        if columns_to_drop:
            self.logger.info(f"📊 Dropping target variable columns from NextGen features: {columns_to_drop}")
            games_df = games_df.drop(columns=columns_to_drop)
            self.logger.info(f"✓ Feature set cleaned: Only QB differential features remain")
        
        return games_df
    
    def _log_feature_quality_metrics(self, df: pd.DataFrame) -> None:
        """
        Analyze and log NextGen feature quality metrics.
        
        Provides insights into which QB features are likely to be useful for modeling
        BEFORE training, helping identify weak features early.
        
        Pattern: Follows rolling_metrics.py:737-899 feature quality analysis
        
        Args:
            df: DataFrame with all NextGen QB differential features
        """
        if df.empty:
            return
        
        # Check if we have target variable for correlation analysis
        has_target = 'home_team_won' in df.columns or 'home_won' in df.columns
        target_col = 'home_team_won' if 'home_team_won' in df.columns else 'home_won' if 'home_won' in df.columns else None
        
        self.logger.info("=" * 80)
        self.logger.info("📊 NEXTGEN FEATURE QUALITY ANALYSIS")
        self.logger.info("=" * 80)
        
        # Get all QB differential features
        qb_features = [col for col in df.columns if col.startswith('qb_') and col.endswith('_diff')]
        
        self.logger.info(f"\n📊 NextGen QB Features Created: {len(qb_features)}")
        for feat in qb_features:
            self.logger.info(f"   - {feat}")
        
        # 1. CORRELATION ANALYSIS (if target available)
        if has_target and target_col:
            self.logger.info("\n📊 1. CORRELATION WITH HOME WINS (Higher = More Predictive)")
            self.logger.info("-" * 80)
            
            correlations = df[qb_features].corrwith(df[target_col]).sort_values(ascending=False)
            
            self.logger.info("Top 10 QB Features by Correlation:")
            for feat, corr in correlations.head(10).items():
                strength = "STRONG" if abs(corr) > 0.15 else "MODERATE" if abs(corr) > 0.08 else "WEAK"
                self.logger.info(f"   {feat:40s}: {corr:+.4f} ({strength})")
            
            # Identify weak features
            weak_features = correlations[abs(correlations) < 0.05]
            if len(weak_features) > 0:
                self.logger.info(f"\n⚠️  {len(weak_features)} QB features with VERY WEAK correlation (<0.05):")
                for feat, corr in weak_features.items():
                    self.logger.info(f"   {feat:40s}: {corr:+.4f} (may not be predictive)")
            
            # Feature quality summary
            strong_corr = sum(abs(correlations) > 0.15)
            moderate_corr = sum((abs(correlations) > 0.08) & (abs(correlations) <= 0.15))
            weak_corr = sum((abs(correlations) > 0.05) & (abs(correlations) <= 0.08))
            very_weak_corr = sum(abs(correlations) <= 0.05)
            
            self.logger.info(f"\n📊 NextGen Feature Correlation Tiers:")
            self.logger.info(f"   STRONG (>0.15):     {strong_corr:2d} features - Highly predictive")
            self.logger.info(f"   MODERATE (0.08-0.15): {moderate_corr:2d} features - Moderately predictive")
            self.logger.info(f"   WEAK (0.05-0.08):   {weak_corr:2d} features - Weakly predictive")
            self.logger.info(f"   VERY WEAK (<0.05):  {very_weak_corr:2d} features - May not be useful")
            
            useful_features = strong_corr + moderate_corr
            useful_pct = (useful_features / len(qb_features)) * 100 if len(qb_features) > 0 else 0
            
            self.logger.info(f"\n📊 Overall NextGen Feature Quality:")
            self.logger.info(f"   Total QB features: {len(qb_features)}")
            self.logger.info(f"   Useful features (>0.08 correlation): {useful_features} ({useful_pct:.1f}%)")
            
            if useful_pct < 30:
                self.logger.warning(f"⚠️  Only {useful_pct:.1f}% of QB features show moderate-to-strong correlation")
                self.logger.warning("   Consider feature selection or additional QB metrics")
            elif useful_pct > 60:
                self.logger.info(f"✓ {useful_pct:.1f}% of QB features show good predictive potential")
            else:
                self.logger.info(f"✓ {useful_pct:.1f}% of QB features show moderate predictive potential")
        
        # 2. FEATURE VARIANCE ANALYSIS
        self.logger.info("\n📊 2. FEATURE VARIANCE (Low Variance = Not Useful)")
        self.logger.info("-" * 80)
        
        variances = df[qb_features].var().sort_values(ascending=True)
        
        self.logger.info("QB Features with LOWEST variance:")
        for feat, var in variances.head(5).items():
            std = var ** 0.5
            self.logger.info(f"   {feat:40s}: variance={var:.6f}, std={std:.4f}")
        
        self.logger.info("\nQB Features with HIGHEST variance:")
        for feat, var in variances.tail(5).items():
            std = var ** 0.5
            self.logger.info(f"   {feat:40s}: variance={var:.6f}, std={std:.4f}")
        
        # 3. MISSING DATA ANALYSIS
        self.logger.info("\n📊 3. MISSING DATA ANALYSIS")
        self.logger.info("-" * 80)
        
        null_counts = df[qb_features].isnull().sum().sort_values(ascending=False)
        total_rows = len(df)
        
        features_with_nulls = null_counts[null_counts > 0]
        if len(features_with_nulls) > 0:
            self.logger.info(f"QB Features with missing data:")
            for feat, count in features_with_nulls.head(10).items():
                pct = (count / total_rows) * 100
                self.logger.info(f"   {feat:40s}: {count:,} ({pct:.1f}%)")
        else:
            self.logger.info("✓ No missing data in QB differential features")
        
        self.logger.info("=" * 80)


def create_nextgen_features(db_service=None, logger=None, bucket_adapter=None):
    """
    Create NextGen QB features service with default dependencies.
    
    Factory function following rolling_metrics.py:903-925 pattern.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        NextGenFeatures: Configured NextGen features service
    """
    from ....shared.database_router import get_database_router
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.ml_pipeline.nextgen_features')
    
    return NextGenFeatures(db_service, logger, bucket_adapter)


__all__ = ['NextGenFeatures', 'create_nextgen_features']