"""
Contextual Features - Game Context and Situational Factors

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + business logic)
Layer: 2 (Implementation - calls infrastructure directly)

Features:
- Rest days differential (home vs away)
- Division game indicator
- Stadium-specific home advantage
- Weather conditions (Phase 2)
- Playoff implications (Phase 2)

Based on FEATURE_ENHANCEMENT_PLAN.md Phase 1 implementation.
"""

import pandas as pd
from typing import Dict, Any, Optional


class ContextualFeatures:
    """
    Contextual feature engineering service.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + contextual calculations)
    Depth: 1 layer (calls database directly)
    
    Follows same pattern as RollingMetricsFeatures.
    """
    
    # Division mapping (from FEATURE_ENHANCEMENT_PLAN.md lines 305-314)
    # Used because dim_team has 'Unknown' divisions
    DIVISIONS = {
        'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
        'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
        'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
        'AFC West': ['DEN', 'KC', 'LV', 'LAC'],
        'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
        'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
        'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
        'NFC West': ['ARI', 'LA', 'SF', 'SEA']
    }
    
    def __init__(self, db_service, logger, bucket_adapter=None):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
            bucket_adapter: Optional bucket adapter (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        self.bucket_adapter = bucket_adapter
    
    def build_features(self, seasons=None) -> Dict[str, Any]:
        """
        Build contextual features for game prediction.
        
        Phase 1 Features (Week 1):
        - Rest days differential
        - Division game indicator
        - Stadium-specific home advantage
        
        Phase 2 Features (Week 2):
        - Weather conditions
        - Playoff implications
        
        Args:
            seasons: List of seasons to process
            
        Returns:
            Dictionary with feature build results including DataFrame
        """
        self.logger.info(f"Building contextual features for seasons: {seasons or 'all'}")
        
        try:
            # Step 1: Load base game data
            df = self._load_game_data(seasons)
            
            if df.empty:
                return {
                    'status': 'warning',
                    'message': 'No data available',
                    'features_built': 0
                }
            
            # Step 2: Phase 1 features (easy wins)
            df = self._add_rest_days_differential(df)
            df = self._add_division_game_indicator(df)
            df = self._add_stadium_home_advantage(df)
            
            # Step 3: Phase 2 features (weather + playoff)
            df = self._add_weather_conditions(df)
            df = self._add_playoff_implications(df)
            
            # Step 4: Feature quality analysis
            self._log_feature_quality(df)
            
            # Step 5: Drop identity columns before returning
            # Contract: Contextual features should only persist computed features
            # Identity columns (home_team, away_team, scores) are owned by game_outcome.py
            identity_cols = ['home_team', 'away_team', 'home_score', 'away_score', 'home_won', 'total_points']
            drop_cols = [col for col in identity_cols if col in df.columns]
            if drop_cols:
                self.logger.info(f"✓ Dropping identity columns before persistence: {drop_cols}")
                df = df.drop(columns=drop_cols)
            
            return {
                'status': 'success',
                'dataframe': df,
                'features_built': len(df),
                'seasons_processed': df['season'].nunique()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build contextual features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }
    
    def _load_game_data(self, seasons=None) -> pd.DataFrame:
        """Load game-level data from bucket warehouse."""
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        # Prepare filters
        filters = None
        if seasons:
            season_list = seasons if isinstance(seasons, (list, tuple)) else [seasons]
            filters = [('season', 'in', season_list)] if len(season_list) > 1 else [('season', '==', season_list[0])]
        
        # Load dim_game with needed columns (Phase 1 + Phase 2)
        # Note: We load home_team/away_team/scores for internal calculations
        # but will drop them before persisting (game_outcome.py owns identity columns)
        columns = [
            'game_id', 'season', 'week', 'game_date',
            'home_team', 'away_team', 'home_score', 'away_score',  # Needed for calculations
            'stadium', 'roof', 'surface',
            'temp', 'wind', 'weather'  # Phase 2: Weather conditions
        ]
        
        dim_game = bucket_adapter.read_data('dim_game', 'warehouse', filters=filters, columns=columns)
        dim_game = dim_game.drop_duplicates(subset=['game_id'], keep='first')
        
        # Convert game_date to datetime
        dim_game['game_date'] = pd.to_datetime(dim_game['game_date'])
        
        self.logger.info(f"✓ Loaded {len(dim_game):,} games")
        
        return dim_game
    
    def _add_rest_days_differential(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate rest days differential (home - away).
        
        Expected Impact: 2-3 point variance reduction
        Rationale: Teams with more rest have measurable advantage
        
        Temporal Safety: Uses game_date which is known before game
        """
        self.logger.info("📊 Adding rest days differential...")
        
        # DATA INSPECTION: Show BEFORE
        self.logger.info("📊 DATA SAMPLE - BEFORE rest days calculation (first 5 games):")
        sample_before = df[['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team']].head(5)
        self.logger.info(f"\n{sample_before.to_string()}")
        
        # Sort by team, season, and date for home team
        # CRITICAL: Group by ['home_team', 'season'] to prevent cross-season contamination
        # (LESSONS_LEARNED.md lines 1581-1589)
        df = df.sort_values(['home_team', 'season', 'game_date'])
        
        # Calculate days since last game for home team (within same season)
        df['home_last_game'] = df.groupby(['home_team', 'season'])['game_date'].shift(1)
        df['home_rest_days'] = (df['game_date'] - df['home_last_game']).dt.days
        
        # Sort by team, season, and date for away team
        df = df.sort_values(['away_team', 'season', 'game_date'])
        df['away_last_game'] = df.groupby(['away_team', 'season'])['game_date'].shift(1)
        df['away_rest_days'] = (df['game_date'] - df['away_last_game']).dt.days
        
        # Calculate differential
        df['rest_days_diff'] = df['home_rest_days'] - df['away_rest_days']
        
        # Fill NaN (first game of season) with 0
        df['rest_days_diff'] = df['rest_days_diff'].fillna(0)
        df['home_rest_days'] = df['home_rest_days'].fillna(7)  # Assume 7 days for first game
        df['away_rest_days'] = df['away_rest_days'].fillna(7)
        
        # Add categorical indicators
        df['home_short_rest'] = (df['home_rest_days'] <= 5).astype(int)  # Thursday game
        df['away_short_rest'] = (df['away_rest_days'] <= 5).astype(int)
        df['home_long_rest'] = (df['home_rest_days'] >= 10).astype(int)  # Bye week
        df['away_long_rest'] = (df['away_rest_days'] >= 10).astype(int)
        
        # DATA INSPECTION: Show AFTER
        self.logger.info("📊 DATA SAMPLE - AFTER rest days calculation (first 5 games):")
        sample_after = df[['game_id', 'home_team', 'away_team', 'home_rest_days', 'away_rest_days', 'rest_days_diff']].head(5)
        self.logger.info(f"\n{sample_after.to_string()}")
        
        # STATISTICS
        self.logger.info(f"📊 Rest days statistics:")
        self.logger.info(f"   rest_days_diff: mean={df['rest_days_diff'].mean():.1f}, range=[{df['rest_days_diff'].min():.0f}, {df['rest_days_diff'].max():.0f}]")
        self.logger.info(f"   home_short_rest: {df['home_short_rest'].sum():,} games ({df['home_short_rest'].mean()*100:.1f}%)")
        self.logger.info(f"   away_short_rest: {df['away_short_rest'].sum():,} games ({df['away_short_rest'].mean()*100:.1f}%)")
        
        # Sort back to original order
        df = df.sort_values(['season', 'week', 'game_id'])
        
        self.logger.info(f"✓ Rest days differential added")
        
        return df
    
    def _add_division_game_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add division game indicator.
        
        Expected Impact: 1-2 point variance reduction
        Rationale: Division games have different dynamics (familiarity, rivalry)
        
        Temporal Safety: Team divisions are static for a season
        """
        self.logger.info("📊 Adding division game indicator...")
        
        # Create reverse mapping
        team_to_division = {}
        for division, teams in self.DIVISIONS.items():
            for team in teams:
                team_to_division[team] = division
        
        # Map teams to divisions
        df['home_division'] = df['home_team'].map(team_to_division)
        df['away_division'] = df['away_team'].map(team_to_division)
        
        # Create division game indicator
        df['is_division_game'] = (df['home_division'] == df['away_division']).astype(int)
        
        # Add conference game indicator
        df['home_conference'] = df['home_division'].str.split().str[0]  # AFC or NFC
        df['away_conference'] = df['away_division'].str.split().str[0]
        df['is_conference_game'] = (df['home_conference'] == df['away_conference']).astype(int)
        
        division_game_pct = df['is_division_game'].mean() * 100
        conference_game_pct = df['is_conference_game'].mean() * 100
        
        self.logger.info(f"✓ Division games: {division_game_pct:.1f}% of total games")
        self.logger.info(f"✓ Conference games: {conference_game_pct:.1f}% of total games")
        
        return df
    
    def _add_stadium_home_advantage(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate stadium-specific home advantage.
        
        Expected Impact: 3-5 point variance reduction
        Rationale: Some stadiums have stronger home-field advantage (weather, altitude, crowd)
        
        Temporal Safety: Uses .shift(1) to exclude current game
        """
        self.logger.info("📊 Adding stadium-specific home advantage...")
        
        # DATA INSPECTION: Show BEFORE
        self.logger.info("📊 DATA SAMPLE - BEFORE stadium advantage (first 5 games):")
        sample_before = df[['game_id', 'stadium', 'home_score', 'away_score']].head(5)
        self.logger.info(f"\n{sample_before.to_string()}")
        
        # Calculate home win indicator
        df['home_won'] = (df['home_score'] > df['away_score']).astype(int)
        
        # Calculate rolling home win rate by stadium (32-game window = ~2 years)
        # Group by stadium and season to prevent cross-season contamination
        # Use .shift(1) to exclude current game
        df = df.sort_values(['stadium', 'season', 'week'])
        df['stadium_home_win_rate'] = df.groupby(['stadium', 'season'])['home_won'].transform(
            lambda x: x.rolling(window=32, min_periods=8).mean().shift(1).fillna(0.565)
        )
        
        # Calculate stadium scoring environment (total points)
        df['total_points'] = df['home_score'] + df['away_score']
        df['stadium_scoring_rate'] = df.groupby(['stadium', 'season'])['total_points'].transform(
            lambda x: x.rolling(window=32, min_periods=8).mean().shift(1).fillna(45.0)
        )
        
        # Stadium altitude/weather advantage (for specific stadiums)
        HIGH_ALTITUDE_STADIUMS = ['Empower Field at Mile High', 'Sports Authority Field at Mile High']  # Denver
        DOME_STADIUMS = ['Mercedes-Benz Superdome', 'AT&T Stadium', 'U.S. Bank Stadium', 
                        'State Farm Stadium', 'Allegiant Stadium', 'SoFi Stadium',
                        'Lucas Oil Stadium', 'Ford Field', 'NRG Stadium']
        
        df['is_high_altitude'] = df['stadium'].isin(HIGH_ALTITUDE_STADIUMS).astype(int)
        df['is_dome'] = df['stadium'].isin(DOME_STADIUMS).astype(int)
        
        # Also check roof column for dome games
        if 'roof' in df.columns:
            df['is_dome'] = ((df['is_dome'] == 1) | (df['roof'] == 'dome')).astype(int)
        
        # DATA INSPECTION: Show AFTER
        self.logger.info("📊 DATA SAMPLE - AFTER stadium advantage (first 5 games):")
        sample_after = df[['game_id', 'stadium', 'stadium_home_win_rate', 'stadium_scoring_rate', 'is_dome']].head(5)
        self.logger.info(f"\n{sample_after.to_string()}")
        
        # VALIDATION: First observations should be default values
        first_obs = df.groupby(['stadium', 'season']).first()
        self.logger.info(f"📊 VALIDATION - First observation per stadium-season:")
        self.logger.info(f"   stadium_home_win_rate: min={first_obs['stadium_home_win_rate'].min():.3f}, max={first_obs['stadium_home_win_rate'].max():.3f}")
        self.logger.info(f"   Expected: 0.565 (NFL average) for stadiums with <8 games")
        
        # STATISTICS
        self.logger.info(f"📊 Stadium advantage statistics:")
        self.logger.info(f"   stadium_home_win_rate: mean={df['stadium_home_win_rate'].mean():.3f}, range=[{df['stadium_home_win_rate'].min():.3f}, {df['stadium_home_win_rate'].max():.3f}]")
        self.logger.info(f"   stadium_scoring_rate: mean={df['stadium_scoring_rate'].mean():.1f}, range=[{df['stadium_scoring_rate'].min():.1f}, {df['stadium_scoring_rate'].max():.1f}]")
        self.logger.info(f"   is_high_altitude: {df['is_high_altitude'].sum():,} games ({df['is_high_altitude'].mean()*100:.1f}%)")
        self.logger.info(f"   is_dome: {df['is_dome'].sum():,} games ({df['is_dome'].mean()*100:.1f}%)")
        
        # Sort back to original order
        df = df.sort_values(['season', 'week', 'game_id'])
        
        self.logger.info(f"✓ Stadium home advantage added")
        
        return df
    
    def _add_weather_conditions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add weather conditions from dim_game.
        
        Expected Impact: 5-8 point variance reduction
        Rationale: Weather affects passing efficiency (wind >15mph, precipitation)
        
        Temporal Safety: Weather is known before game (forecasts available)
        Data Source: dim_game.temp, dim_game.wind, dim_game.weather (71.7% coverage)
        
        Following LESSONS_LEARNED.md Case Study #4 (lines 549-735):
        - Log data samples before/after transformation
        - Include statistical summaries
        - Validate temporal leakage prevention
        """
        self.logger.info("📊 Adding weather conditions...")
        
        # DATA INSPECTION: Show BEFORE (LESSONS_LEARNED.md lines 673-710)
        self.logger.info("📊 DATA SAMPLE - BEFORE weather features (first 5 games):")
        sample_before = df[['game_id', 'stadium', 'temp', 'wind', 'weather']].head(5)
        self.logger.info(f"\n{sample_before.to_string()}")
        
        # Calculate seasonal normal temperature by stadium and month
        # Uses .shift(1) to prevent temporal leakage (LESSONS_LEARNED.md lines 27-29)
        df['month'] = df['game_date'].dt.month
        df = df.sort_values(['stadium', 'season', 'week'])
        
        df['seasonal_normal_temp'] = df.groupby(['stadium', 'month'])['temp'].transform(
            lambda x: x.rolling(window=52, min_periods=10).mean().shift(1).fillna(58.1)
        )
        
        # Temperature differential from seasonal normal
        df['temp_diff_from_normal'] = df['temp'] - df['seasonal_normal_temp']
        
        # Precipitation indicator (from weather text field)
        # Data shows 8.6% of games have precipitation
        precipitation_keywords = ['rain', 'snow', 'sleet', 'showers', 'drizzle']
        df['is_precipitation'] = df['weather'].str.lower().str.contains(
            '|'.join(precipitation_keywords), na=False
        ).astype(int)
        
        # High wind indicator (>15 mph affects passing)
        # Data shows 9.2% of games have high wind
        df['high_wind'] = (df['wind'] > 15).fillna(False).astype(int)
        
        # Weather passing impact composite score
        # Negative values indicate worse passing conditions
        df['weather_passing_impact'] = (
            df['is_precipitation'] * -0.05 +  # Rain reduces passing efficiency
            df['high_wind'] * -0.08 +          # Wind reduces passing efficiency
            (df['temp_diff_from_normal'] / 100) * -0.001  # Extreme temps reduce efficiency
        )
        
        # Fill nulls for games without weather data (28.3% of games)
        df['temp_diff_from_normal'] = df['temp_diff_from_normal'].fillna(0)
        df['is_precipitation'] = df['is_precipitation'].fillna(0)
        df['high_wind'] = df['high_wind'].fillna(0)
        df['weather_passing_impact'] = df['weather_passing_impact'].fillna(0)
        
        # DATA INSPECTION: Show AFTER (LESSONS_LEARNED.md lines 673-710)
        self.logger.info("📊 DATA SAMPLE - AFTER weather features (first 5 games):")
        sample_after = df[['game_id', 'temp_diff_from_normal', 'is_precipitation', 'high_wind', 'weather_passing_impact']].head(5)
        self.logger.info(f"\n{sample_after.to_string()}")
        
        # VALIDATION: First observations for seasonal normal (LESSONS_LEARNED.md lines 31-34)
        first_obs = df.groupby(['stadium', 'season']).first()
        self.logger.info(f"📊 VALIDATION - First observation seasonal normal (should be 58.1°F):")
        self.logger.info(f"   min={first_obs['seasonal_normal_temp'].min():.1f}°F, max={first_obs['seasonal_normal_temp'].max():.1f}°F")
        
        # STATISTICS: Summary (CODING_GUIDE.md lines 1690-1693)
        self.logger.info(f"📊 Weather Statistics:")
        self.logger.info(f"   Coverage: {(~df['temp'].isna()).sum():,} / {len(df):,} games ({(~df['temp'].isna()).mean()*100:.1f}%)")
        self.logger.info(f"   High wind games (>15 mph): {df['high_wind'].sum():,} ({df['high_wind'].mean()*100:.1f}%)")
        self.logger.info(f"   Precipitation games: {df['is_precipitation'].sum():,} ({df['is_precipitation'].mean()*100:.1f}%)")
        self.logger.info(f"   Temp diff range: [{df['temp_diff_from_normal'].min():.1f}°F, {df['temp_diff_from_normal'].max():.1f}°F]")
        self.logger.info(f"   Weather passing impact: mean={df['weather_passing_impact'].mean():.4f}, range=[{df['weather_passing_impact'].min():.4f}, {df['weather_passing_impact'].max():.4f}]")
        
        # Sort back to original order
        df = df.sort_values(['season', 'week', 'game_id'])
        
        self.logger.info(f"✓ Weather conditions added")
        
        return df
    
    def _add_playoff_implications(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add playoff race context.
        
        Expected Impact: 3-5 point variance reduction
        Rationale: Teams play differently when playoff spots are on the line
        
        Temporal Safety: Week number is known before game
        Data Source: dim_game.week (100% coverage)
        
        Following LESSONS_LEARNED.md Case Study #4 (lines 549-735):
        - Log data samples before/after transformation
        - Include statistical summaries
        """
        self.logger.info("📊 Adding playoff implications...")
        
        # DATA INSPECTION: Show BEFORE (LESSONS_LEARNED.md lines 673-710)
        self.logger.info("📊 DATA SAMPLE - BEFORE playoff features (first 5 games):")
        sample_before = df[['game_id', 'season', 'week']].head(5)
        self.logger.info(f"\n{sample_before.to_string()}")
        
        # Calculate games remaining in season (18-game regular season)
        df['games_remaining'] = 18 - df['week']
        
        # Late season indicator (weeks 14-18)
        # These games often have playoff implications
        df['is_late_season'] = (df['week'] >= 14).astype(int)
        
        # Playoff week indicator (weeks 19+)
        df['is_playoff_week'] = (df['week'] > 18).astype(int)
        
        # DATA INSPECTION: Show AFTER (LESSONS_LEARNED.md lines 673-710)
        self.logger.info("📊 DATA SAMPLE - AFTER playoff features (first 5 games):")
        sample_after = df[['game_id', 'week', 'games_remaining', 'is_late_season', 'is_playoff_week']].head(5)
        self.logger.info(f"\n{sample_after.to_string()}")
        
        # STATISTICS: Summary (CODING_GUIDE.md lines 1690-1693)
        self.logger.info(f"📊 Playoff Statistics:")
        self.logger.info(f"   Late season games (weeks 14-18): {df['is_late_season'].sum():,} ({df['is_late_season'].mean()*100:.1f}%)")
        self.logger.info(f"   Playoff games (weeks 19+): {df['is_playoff_week'].sum():,} ({df['is_playoff_week'].mean()*100:.1f}%)")
        self.logger.info(f"   Games remaining range: [{df['games_remaining'].min()}, {df['games_remaining'].max()}]")
        
        self.logger.info(f"✓ Playoff implications added")
        
        return df
    
    def _log_feature_quality(self, df: pd.DataFrame) -> None:
        """
        Analyze and log feature quality metrics to assess predictive power.
        
        Enhanced analysis following rolling_metrics.py pattern (lines 737-899):
        1. Correlation analysis with home wins
        2. Win/loss stratification
        3. Feature variance analysis
        4. Temporal stability across seasons
        5. Overall quality summary
        
        This provides insights into which features are likely to be useful for modeling
        BEFORE training, helping identify weak features early.
        
        Args:
            df: DataFrame with all contextual features calculated
        """
        if df.empty or 'home_won' not in df.columns:
            return
        
        self.logger.info("=" * 80)
        self.logger.info("📊 CONTEXTUAL FEATURE QUALITY ANALYSIS")
        self.logger.info("=" * 80)
        
        # Define contextual feature groups (Phase 1 + Phase 2)
        contextual_features = [
            # Phase 1: Rest days
            'rest_days_diff', 'home_short_rest', 'away_short_rest',
            'home_long_rest', 'away_long_rest',
            # Phase 1: Division/Conference
            'is_division_game', 'is_conference_game',
            # Phase 1: Stadium
            'stadium_home_win_rate', 'stadium_scoring_rate',
            'is_high_altitude', 'is_dome',
            # Phase 2: Weather
            'temp_diff_from_normal', 'is_precipitation', 'high_wind',
            'weather_passing_impact',
            # Phase 2: Playoff
            'games_remaining', 'is_late_season'
        ]
        
        available = [f for f in contextual_features if f in df.columns]
        
        # 1. CORRELATION ANALYSIS
        self.logger.info("\n📊 1. CORRELATION WITH HOME WINS (Higher = More Predictive)")
        self.logger.info("-" * 80)
        
        correlations = df[available].corrwith(df['home_won']).sort_values(ascending=False)
        
        self.logger.info("Top Positive Correlations (features associated with home winning):")
        for feat, corr in correlations.head(5).items():
            strength = "STRONG" if abs(corr) > 0.15 else "MODERATE" if abs(corr) > 0.08 else "WEAK"
            self.logger.info(f"   {feat:30s}: {corr:+.4f} ({strength})")
        
        self.logger.info("\nTop Negative Correlations (features associated with home losing):")
        for feat, corr in correlations.tail(5).items():
            strength = "STRONG" if abs(corr) > 0.15 else "MODERATE" if abs(corr) > 0.08 else "WEAK"
            self.logger.info(f"   {feat:30s}: {corr:+.4f} ({strength})")
        
        # Identify weak features
        weak_features = correlations[abs(correlations) < 0.05]
        if len(weak_features) > 0:
            self.logger.info(f"\n⚠️  {len(weak_features)} features with VERY WEAK correlation (<0.05):")
            for feat, corr in weak_features.items():
                self.logger.info(f"   {feat:30s}: {corr:+.4f} (may not be predictive)")
        
        # 2. WIN/LOSS STRATIFICATION
        self.logger.info("\n📊 2. WIN/LOSS STRATIFICATION (Larger Difference = More Predictive)")
        self.logger.info("-" * 80)
        
        wins_df = df[df['home_won'] == 1]
        losses_df = df[df['home_won'] == 0]
        
        stratification = []
        for feat in available:
            win_mean = wins_df[feat].mean()
            loss_mean = losses_df[feat].mean()
            diff = win_mean - loss_mean
            stratification.append((feat, win_mean, loss_mean, diff, abs(diff)))
        
        # Sort by absolute difference
        stratification.sort(key=lambda x: x[4], reverse=True)
        
        self.logger.info("Top Features by Win/Loss Separation:")
        for feat, win_mean, loss_mean, diff, abs_diff in stratification[:10]:
            self.logger.info(f"   {feat:30s}: wins={win_mean:+.4f}, losses={loss_mean:+.4f}, diff={diff:+.4f}")
        
        # 3. FEATURE VARIANCE ANALYSIS
        self.logger.info("\n📊 3. FEATURE VARIANCE (Low Variance = Not Useful)")
        self.logger.info("-" * 80)
        
        variances = df[available].var().sort_values(ascending=True)
        
        self.logger.info("Features with LOWEST variance (may not be predictive):")
        for feat, var in variances.head(5).items():
            std = var ** 0.5
            self.logger.info(f"   {feat:30s}: variance={var:.6f}, std={std:.4f}")
        
        self.logger.info("\nFeatures with HIGHEST variance (more information):")
        for feat, var in variances.tail(5).items():
            std = var ** 0.5
            self.logger.info(f"   {feat:30s}: variance={var:.6f}, std={std:.4f}")
        
        # 4. TEMPORAL STABILITY ANALYSIS (if multiple seasons)
        if 'season' in df.columns and df['season'].nunique() > 1:
            self.logger.info("\n📊 4. TEMPORAL STABILITY (Consistency Across Seasons)")
            self.logger.info("-" * 80)
            
            # Analyze last 5 seasons for stability
            recent_seasons = sorted(df['season'].unique())[-5:]
            self.logger.info(f"Analyzing stability across seasons: {recent_seasons}")
            
            # Check key features for temporal stability
            key_features_for_stability = ['rest_days_diff', 'is_division_game', 'stadium_home_win_rate']
            
            for feat in key_features_for_stability:
                if feat not in df.columns:
                    continue
                
                season_means = []
                for season in recent_seasons:
                    season_mean = df[df['season'] == season][feat].mean()
                    season_means.append(season_mean)
                
                # Calculate coefficient of variation (std/mean) as stability metric
                mean_of_means = sum(season_means) / len(season_means)
                std_of_means = (sum((x - mean_of_means) ** 2 for x in season_means) / len(season_means)) ** 0.5
                cv = (std_of_means / (abs(mean_of_means) + 1e-10)) * 100
                
                stability = "STABLE" if cv < 20 else "MODERATE" if cv < 50 else "UNSTABLE"
                self.logger.info(f"   {feat:30s}: CV={cv:.1f}% ({stability})")
                self.logger.info(f"      Season means: {[f'{m:.4f}' for m in season_means]}")
        
        # 5. FEATURE QUALITY SUMMARY
        self.logger.info("\n📊 5. FEATURE QUALITY SUMMARY")
        self.logger.info("-" * 80)
        
        # Count features by quality tier
        strong_corr = sum(abs(correlations) > 0.15)
        moderate_corr = sum((abs(correlations) > 0.08) & (abs(correlations) <= 0.15))
        weak_corr = sum((abs(correlations) > 0.05) & (abs(correlations) <= 0.08))
        very_weak_corr = sum(abs(correlations) <= 0.05)
        
        self.logger.info(f"Feature Correlation Tiers:")
        self.logger.info(f"   STRONG (>0.15):     {strong_corr:2d} features - Highly predictive")
        self.logger.info(f"   MODERATE (0.08-0.15): {moderate_corr:2d} features - Moderately predictive")
        self.logger.info(f"   WEAK (0.05-0.08):   {weak_corr:2d} features - Weakly predictive")
        self.logger.info(f"   VERY WEAK (<0.05):  {very_weak_corr:2d} features - May not be useful")
        
        # Overall assessment
        total_features = len(available)
        useful_features = strong_corr + moderate_corr
        useful_pct = (useful_features / total_features) * 100 if total_features > 0 else 0
        
        self.logger.info(f"\nOverall Feature Quality:")
        self.logger.info(f"   Total features analyzed: {total_features}")
        self.logger.info(f"   Useful features (>0.08 correlation): {useful_features} ({useful_pct:.1f}%)")
        
        if useful_pct < 30:
            self.logger.warning(f"⚠️  Only {useful_pct:.1f}% of features show moderate-to-strong correlation with home wins")
            self.logger.warning("   NOTE: Single-season correlations may be weak. Multi-season training will reveal true predictive power.")
            self.logger.warning("   These features capture game context that may interact with other features in the model.")
        elif useful_pct > 60:
            self.logger.info(f"✓ {useful_pct:.1f}% of features show good predictive potential")
        else:
            self.logger.info(f"✓ {useful_pct:.1f}% of features show moderate predictive potential")
        
        # Feature statistics
        self.logger.info("\n📊 6. FEATURE STATISTICS")
        self.logger.info("-" * 80)
        for feat in available:
            nulls = df[feat].isnull().sum()
            null_pct = (nulls / len(df)) * 100
            unique = df[feat].nunique()
            feat_min = df[feat].min()
            feat_max = df[feat].max()
            feat_mean = df[feat].mean()
            self.logger.info(f"   {feat:30s}: nulls={nulls:,} ({null_pct:.1f}%), unique={unique:,}, range=[{feat_min:.3f}, {feat_max:.3f}], mean={feat_mean:.3f}")
        
        self.logger.info("=" * 80)


def create_contextual_features(db_service=None, logger=None, bucket_adapter=None):
    """
    Create contextual features service with default dependencies.
    
    Follows factory pattern from create_rolling_metrics_features().
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        ContextualFeatures: Configured contextual features service
    """
    from ....shared.database_router import get_database_router
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.ml_pipeline.contextual_features')
    
    return ContextualFeatures(db_service, logger, bucket_adapter)


__all__ = ['ContextualFeatures', 'create_contextual_features']