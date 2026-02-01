"""
Weather Features - Game-Level Weather Impact

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + weather calculations)
Layer: 2 (Implementation - calls infrastructure directly)

V1 Features (Conservative Observables):
- Temperature: raw values, absolute thresholds, extreme scores
- Wind: raw values, absolute thresholds, categorical handicaps
- Precipitation: keyword flags (unvalidated heuristic)
- Stadium context: roof type, altitude, outdoor flags
- Composite impact scores: passing impact, rushing advantage

V2 Roadmap (Future):
- Temperature differentials from seasonal normals (requires baseline strategy)
- Historical weather averages (month-based vs season-week buckets)
- External precipitation validation (NOAA, Weather API)

Data Source: dim_game_weather (warehouse)
Output: weather_features_v1 (features schema)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List


class WeatherFeatures:
    """
    Weather feature engineering service - V1 Observables Only.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + weather calculations)
    Depth: 1 layer (calls bucket warehouse directly)
    
    Follows same pattern as ContextualFeatures and OddsGameFeatures.
    
    V1 Strategy: Use direct observable weather values without derived "normals"
    to avoid premature assumptions about baseline definitions.
    """
    
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
    
    def build_features(self, seasons: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Build weather features for game prediction.
        
        V1 Features:
        - Temperature: raw values, absolute thresholds, extreme scores
        - Wind: raw values, absolute thresholds, categorical handicaps
        - Precipitation: keyword flags (unvalidated heuristic)
        - Stadium context: roof type, altitude, outdoor flags
        - Composite impact scores
        
        Args:
            seasons: List of seasons to process (e.g., [2020, 2021, 2022])
            
        Returns:
            Dictionary with feature build results including DataFrame
        """
        self.logger.info(f"Building weather features for seasons: {seasons or 'all'}")
        
        try:
            # Step 1: Load dim_game_weather from warehouse
            df = self._load_weather_data(seasons)
            
            if df.empty:
                return {
                    'status': 'warning',
                    'message': 'No weather data available',
                    'features_built': 0
                }
            
            # Step 2: Temperature features
            df = self._add_temperature_features(df)
            
            # Step 3: Wind features
            df = self._add_wind_features(df)
            
            # Step 4: Precipitation features (keyword-based heuristic)
            df = self._add_precipitation_features(df)
            
            # Step 5: Stadium context features
            df = self._add_stadium_context_features(df)
            
            # Step 6: Composite impact scores
            df = self._add_composite_scores(df)
            
            # Step 7: Feature quality analysis
            self._log_feature_quality(df)
            
            # Step 8: Drop identity columns before returning
            # Contract: Weather features should only persist computed features
            # Identity columns (home_team, away_team) are owned by game_outcome.py
            identity_cols = ['home_team', 'away_team']
            drop_cols = [col for col in identity_cols if col in df.columns]
            if drop_cols:
                self.logger.info(f"✓ Dropping identity columns before persistence: {drop_cols}")
                df = df.drop(columns=drop_cols)
            
            return {
                'status': 'success',
                'dataframe': df,
                'features_built': len(df),
                'seasons_processed': df['season'].nunique() if 'season' in df.columns else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build weather features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }
    
    def _load_weather_data(self, seasons: Optional[List[int]] = None) -> pd.DataFrame:
        """Load weather data from warehouse bucket."""
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        # Prepare filters
        filters = None
        if seasons:
            season_list = seasons if isinstance(seasons, (list, tuple)) else [seasons]
            filters = [('season', 'in', season_list)] if len(season_list) > 1 else [('season', '==', season_list[0])]
        
        # Load dim_game_weather with needed columns
        # Note: We load home_team/away_team for validation/debugging
        # but will drop them before persisting (game_outcome.py owns identity columns)
        columns = [
            'game_id', 'season', 'week', 'game_date',
            'home_team', 'away_team',  # Will be dropped before persistence
            'temp_model', 'wind_model', 'weather',
            'is_weather_model_eligible', 'weather_provenance',
            'is_malformed_weather_string', 'is_missing_weather_after_parse',
            'is_outdoor_dim_game', 'stadium_roof_type', 'stadium_name'
        ]
        
        dim_game_weather = bucket_adapter.read_data('dim_game_weather', 'warehouse', filters=filters, columns=columns)
        dim_game_weather = dim_game_weather.drop_duplicates(subset=['game_id'], keep='first')
        
        self.logger.info(f"✓ Loaded {len(dim_game_weather):,} games from dim_game_weather")
        
        # Log model eligibility stats
        if 'is_weather_model_eligible' in dim_game_weather.columns:
            eligible = dim_game_weather['is_weather_model_eligible'].sum()
            total = len(dim_game_weather)
            self.logger.info(f"  Model-eligible games: {eligible:,}/{total:,} ({eligible/total*100:.1f}%)")
        
        return dim_game_weather
    
    def _add_temperature_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add temperature-based features.
        
        Features:
        - temp_raw: Pass-through from temp_model
        - is_cold_weather: Temp < 32°F (freezing)
        - is_hot_weather: Temp > 85°F
        - temp_extreme_score: |temp - 72| / 40 (normalized distance from ideal)
        - temp_bucket: Categorical temperature ranges
        """
        self.logger.info("📊 Adding temperature features...")
        
        # DATA INSPECTION: Show BEFORE
        self.logger.info("📊 DATA SAMPLE - BEFORE temperature features (first 5 games):")
        sample_before = df[['game_id', 'temp_model', 'is_weather_model_eligible']].head(5)
        self.logger.info(f"\n{sample_before.to_string()}")
        
        # Raw temperature (pass-through)
        df['temp_raw'] = df['temp_model']
        
        # Absolute threshold features
        df['is_cold_weather'] = (df['temp_model'] < 32).fillna(False).astype(int)
        df['is_hot_weather'] = (df['temp_model'] > 85).fillna(False).astype(int)
        
        # Extreme score (normalized distance from ideal 72°F)
        # Higher score = more extreme conditions
        df['temp_extreme_score'] = (df['temp_model'] - 72).abs() / 40
        df['temp_extreme_score'] = df['temp_extreme_score'].fillna(0)  # Indoor games = neutral
        
        # Temperature buckets for categorical analysis
        def categorize_temp(temp):
            if pd.isna(temp):
                return 'indoor'
            elif temp < 32:
                return 'freezing'
            elif temp < 45:
                return 'cold'
            elif temp < 75:
                return 'moderate'
            elif temp < 85:
                return 'warm'
            else:
                return 'hot'
        
        df['temp_bucket'] = df['temp_model'].apply(categorize_temp)
        
        # DATA INSPECTION: Show AFTER
        self.logger.info("📊 DATA SAMPLE - AFTER temperature features (first 5 games):")
        sample_after = df[['game_id', 'temp_raw', 'is_cold_weather', 'is_hot_weather', 'temp_extreme_score', 'temp_bucket']].head(5)
        self.logger.info(f"\n{sample_after.to_string()}")
        
        # STATISTICS
        self.logger.info(f"📊 Temperature statistics:")
        self.logger.info(f"   Coverage: {df['temp_raw'].notna().sum():,}/{len(df):,} ({df['temp_raw'].notna().mean()*100:.1f}%)")
        self.logger.info(f"   Cold weather (<32°F): {df['is_cold_weather'].sum():,} ({df['is_cold_weather'].mean()*100:.1f}%)")
        self.logger.info(f"   Hot weather (>85°F): {df['is_hot_weather'].sum():,} ({df['is_hot_weather'].mean()*100:.1f}%)")
        self.logger.info(f"   Extreme score: mean={df['temp_extreme_score'].mean():.3f}, max={df['temp_extreme_score'].max():.3f}")
        self.logger.info(f"   Temperature buckets:")
        for bucket, count in df['temp_bucket'].value_counts().items():
            self.logger.info(f"     {bucket}: {count:,} ({count/len(df)*100:.1f}%)")
        
        self.logger.info(f"✓ Temperature features added")
        
        return df
    
    def _add_wind_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add wind-based features.
        
        Features:
        - wind_raw: Pass-through from wind_model
        - high_wind: Wind > 15 mph (affects passing)
        - extreme_wind: Wind > 20 mph (severe impact)
        - wind_passing_handicap: Categorical 0-3 (none/moderate/high/extreme)
        """
        self.logger.info("📊 Adding wind features...")
        
        # DATA INSPECTION: Show BEFORE
        self.logger.info("📊 DATA SAMPLE - BEFORE wind features (first 5 games):")
        sample_before = df[['game_id', 'wind_model', 'is_weather_model_eligible']].head(5)
        self.logger.info(f"\n{sample_before.to_string()}")
        
        # Raw wind (pass-through)
        df['wind_raw'] = df['wind_model']
        
        # Absolute threshold features
        df['high_wind'] = (df['wind_model'] > 15).fillna(False).astype(int)
        df['extreme_wind'] = (df['wind_model'] > 20).fillna(False).astype(int)
        
        # Wind passing handicap (categorical)
        def categorize_wind_handicap(wind):
            if pd.isna(wind):
                return 0  # Indoor = no handicap
            elif wind < 10:
                return 0  # None
            elif wind < 15:
                return 1  # Moderate
            elif wind < 20:
                return 2  # High
            else:
                return 3  # Extreme
        
        df['wind_passing_handicap'] = df['wind_model'].apply(categorize_wind_handicap)
        
        # DATA INSPECTION: Show AFTER
        self.logger.info("📊 DATA SAMPLE - AFTER wind features (first 5 games):")
        sample_after = df[['game_id', 'wind_raw', 'high_wind', 'extreme_wind', 'wind_passing_handicap']].head(5)
        self.logger.info(f"\n{sample_after.to_string()}")
        
        # STATISTICS
        self.logger.info(f"📊 Wind statistics:")
        self.logger.info(f"   Coverage: {df['wind_raw'].notna().sum():,}/{len(df):,} ({df['wind_raw'].notna().mean()*100:.1f}%)")
        self.logger.info(f"   High wind (>15 mph): {df['high_wind'].sum():,} ({df['high_wind'].mean()*100:.1f}%)")
        self.logger.info(f"   Extreme wind (>20 mph): {df['extreme_wind'].sum():,} ({df['extreme_wind'].mean()*100:.1f}%)")
        self.logger.info(f"   Wind handicap distribution:")
        handicap_labels = {0: 'none', 1: 'moderate', 2: 'high', 3: 'extreme'}
        for handicap, count in df['wind_passing_handicap'].value_counts().sort_index().items():
            label = handicap_labels.get(int(handicap), 'unknown')
            self.logger.info(f"     {handicap} ({label}): {count:,} ({count/len(df)*100:.1f}%)")
        
        self.logger.info(f"✓ Wind features added")
        
        return df
    
    def _add_precipitation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add precipitation features (V1 keyword-based heuristic).
        
        ⚠️ IMPORTANT: These are UNVALIDATED string pattern matches.
        Use naming convention *_keyword_flag (NOT is_*) to indicate this.
        
        Features:
        - precip_keyword_flag: Weather string contains precipitation keywords
        - snow_keyword_flag: Weather string contains 'snow'
        - rain_keyword_flag: Weather string contains 'rain' or 'drizzle'
        - precip_keyword_source: Metadata tracking ('weather_string_heuristic')
        """
        self.logger.info("📊 Adding precipitation features (keyword-based heuristic)...")
        
        # DATA INSPECTION: Show BEFORE
        self.logger.info("📊 DATA SAMPLE - BEFORE precipitation features (first 5 games):")
        sample_before = df[['game_id', 'weather']].head(5)
        self.logger.info(f"\n{sample_before.to_string()}")
        
        # Keyword lists
        precip_keywords = ['rain', 'snow', 'sleet', 'showers', 'drizzle']
        
        # Precipitation keyword flag (general)
        df['precip_keyword_flag'] = df['weather'].str.lower().str.contains(
            '|'.join(precip_keywords), na=False
        ).astype(int)
        
        # Specific precipitation type flags
        df['snow_keyword_flag'] = df['weather'].str.lower().str.contains('snow', na=False).astype(int)
        df['rain_keyword_flag'] = df['weather'].str.lower().str.contains('rain|drizzle', na=False).astype(int)
        
        # Source metadata (track that this is a heuristic, not validated)
        df['precip_keyword_source'] = 'weather_string_heuristic'
        
        # DATA INSPECTION: Show AFTER
        self.logger.info("📊 DATA SAMPLE - AFTER precipitation features (first 5 games):")
        sample_after = df[['game_id', 'weather', 'precip_keyword_flag', 'snow_keyword_flag', 'rain_keyword_flag']].head(5)
        self.logger.info(f"\n{sample_after.to_string()}")
        
        # STATISTICS
        self.logger.info(f"📊 Precipitation statistics (KEYWORD-BASED - UNVALIDATED):")
        self.logger.info(f"   ⚠️ These are string pattern matches only, not validated against observed precipitation")
        self.logger.info(f"   precip_keyword_flag: {df['precip_keyword_flag'].sum():,} ({df['precip_keyword_flag'].mean()*100:.1f}%)")
        self.logger.info(f"   snow_keyword_flag: {df['snow_keyword_flag'].sum():,} ({df['snow_keyword_flag'].mean()*100:.1f}%)")
        self.logger.info(f"   rain_keyword_flag: {df['rain_keyword_flag'].sum():,} ({df['rain_keyword_flag'].mean()*100:.1f}%)")
        
        self.logger.info(f"✓ Precipitation keyword features added")
        
        return df
    
    def _add_stadium_context_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add stadium context features.
        
        Features:
        - is_outdoor_dim_game: From warehouse (outdoor games that should have weather)
        - stadium_roof_type: Fixed dome | retractable | open
        - is_dome: Climate-controlled environment
        - is_high_altitude: Denver stadiums (affects ball flight)
        """
        self.logger.info("📊 Adding stadium context features...")
        
        # DATA INSPECTION: Show BEFORE
        self.logger.info("📊 DATA SAMPLE - BEFORE stadium features (first 5 games):")
        sample_before = df[['game_id', 'stadium_roof_type', 'is_outdoor_dim_game']].head(5)
        self.logger.info(f"\n{sample_before.to_string()}")
        
        # is_outdoor_dim_game is already in dim_game_weather (pass-through)
        # stadium_roof_type is already in dim_game_weather (pass-through)
        
        # Dome indicator (fixed_dome or retractable when closed)
        df['is_dome'] = (df['stadium_roof_type'] == 'fixed_dome').astype(int)
        
        # High altitude stadiums (Denver)
        HIGH_ALTITUDE_STADIUMS = [
            'Empower Field at Mile High',
            'Sports Authority Field at Mile High',
            'Mile High Stadium',
            'Invesco Field at Mile High'
        ]
        
        df['is_high_altitude'] = df['stadium_name'].isin(HIGH_ALTITUDE_STADIUMS).astype(int)
        
        # DATA INSPECTION: Show AFTER
        self.logger.info("📊 DATA SAMPLE - AFTER stadium features (first 5 games):")
        sample_after = df[['game_id', 'is_outdoor_dim_game', 'stadium_roof_type', 'is_dome', 'is_high_altitude']].head(5)
        self.logger.info(f"\n{sample_after.to_string()}")
        
        # STATISTICS
        self.logger.info(f"📊 Stadium statistics:")
        self.logger.info(f"   Outdoor games: {df['is_outdoor_dim_game'].sum():,} ({df['is_outdoor_dim_game'].mean()*100:.1f}%)")
        self.logger.info(f"   Dome games: {df['is_dome'].sum():,} ({df['is_dome'].mean()*100:.1f}%)")
        self.logger.info(f"   High altitude games: {df['is_high_altitude'].sum():,} ({df['is_high_altitude'].mean()*100:.1f}%)")
        self.logger.info(f"   Roof type distribution:")
        for roof_type, count in df['stadium_roof_type'].value_counts().items():
            self.logger.info(f"     {roof_type}: {count:,} ({count/len(df)*100:.1f}%)")
        
        self.logger.info(f"✓ Stadium context features added")
        
        return df
    
    def _add_composite_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add composite impact scores.
        
        Features:
        - weather_passing_impact: Negative score for passing conditions
        - weather_rushing_advantage: Positive score for rushing conditions
        - weather_game_environment: Overall gameplay impact
        """
        self.logger.info("📊 Adding composite impact scores...")
        
        # DATA INSPECTION: Show BEFORE
        self.logger.info("📊 DATA SAMPLE - BEFORE composite scores (first 5 games):")
        sample_before = df[['game_id', 'precip_keyword_flag', 'high_wind', 'temp_extreme_score']].head(5)
        self.logger.info(f"\n{sample_before.to_string()}")
        
        # Weather passing impact (negative = worse for passing)
        # Formula: (precip * -0.05) + (high_wind * -0.08)
        # Note: Does NOT include temp differential (V2 feature)
        df['weather_passing_impact'] = (
            df['precip_keyword_flag'] * -0.05 +
            df['high_wind'] * -0.08
        )
        
        # Weather rushing advantage (positive = better for rushing)
        # Bad weather favors ground game
        df['weather_rushing_advantage'] = (
            df['precip_keyword_flag'] * 0.05 +
            df['high_wind'] * 0.03
        )
        
        # Overall game environment score
        # Combines passing/rushing advantages
        df['weather_game_environment'] = (
            df['weather_passing_impact'] + df['weather_rushing_advantage']
        )
        
        # DATA INSPECTION: Show AFTER
        self.logger.info("📊 DATA SAMPLE - AFTER composite scores (first 5 games):")
        sample_after = df[['game_id', 'weather_passing_impact', 'weather_rushing_advantage', 'weather_game_environment']].head(5)
        self.logger.info(f"\n{sample_after.to_string()}")
        
        # STATISTICS
        self.logger.info(f"📊 Composite score statistics:")
        self.logger.info(f"   weather_passing_impact: mean={df['weather_passing_impact'].mean():.4f}, range=[{df['weather_passing_impact'].min():.4f}, {df['weather_passing_impact'].max():.4f}]")
        self.logger.info(f"   weather_rushing_advantage: mean={df['weather_rushing_advantage'].mean():.4f}, range=[{df['weather_rushing_advantage'].min():.4f}, {df['weather_rushing_advantage'].max():.4f}]")
        self.logger.info(f"   weather_game_environment: mean={df['weather_game_environment'].mean():.4f}, range=[{df['weather_game_environment'].min():.4f}, {df['weather_game_environment'].max():.4f}]")
        
        self.logger.info(f"✓ Composite impact scores added")
        
        return df
    
    def _log_feature_quality(self, df: pd.DataFrame) -> None:
        """
        Analyze and log feature quality metrics.
        
        Enhanced analysis following rolling_metrics.py pattern:
        1. Feature statistics (coverage, uniqueness, range)
        2. Data quality issues
        3. Overall feature summary
        """
        if df.empty:
            return
        
        self.logger.info("=" * 80)
        self.logger.info("📊 WEATHER FEATURE QUALITY ANALYSIS")
        self.logger.info("=" * 80)
        
        # Define weather feature groups
        weather_features = [
            # Temperature
            'temp_raw', 'is_cold_weather', 'is_hot_weather', 'temp_extreme_score',
            # Wind
            'wind_raw', 'high_wind', 'extreme_wind', 'wind_passing_handicap',
            # Precipitation (keyword-based)
            'precip_keyword_flag', 'snow_keyword_flag', 'rain_keyword_flag',
            # Stadium context
            'is_outdoor_dim_game', 'is_dome', 'is_high_altitude',
            # Composite scores
            'weather_passing_impact', 'weather_rushing_advantage', 'weather_game_environment'
        ]
        
        available = [f for f in weather_features if f in df.columns]
        
        # 1. FEATURE STATISTICS
        self.logger.info("\n📊 1. FEATURE STATISTICS")
        self.logger.info("-" * 80)
        
        for feat in available:
            nulls = df[feat].isnull().sum()
            null_pct = (nulls / len(df)) * 100
            unique = df[feat].nunique()
            
            if df[feat].dtype in ['int64', 'float64']:
                feat_min = df[feat].min()
                feat_max = df[feat].max()
                feat_mean = df[feat].mean()
                self.logger.info(f"   {feat:30s}: nulls={nulls:,} ({null_pct:.1f}%), unique={unique:,}, range=[{feat_min:.3f}, {feat_max:.3f}], mean={feat_mean:.3f}")
            else:
                self.logger.info(f"   {feat:30s}: nulls={nulls:,} ({null_pct:.1f}%), unique={unique:,}")
        
        # 2. DATA QUALITY ISSUES
        self.logger.info("\n📊 2. DATA QUALITY ISSUES")
        self.logger.info("-" * 80)
        
        if 'is_missing_weather_after_parse' in df.columns:
            missing = df['is_missing_weather_after_parse'].sum()
            if missing > 0:
                self.logger.warning(f"   ⚠️ {missing:,} outdoor games missing weather data")
        
        if 'is_malformed_weather_string' in df.columns:
            malformed = df['is_malformed_weather_string'].sum()
            if malformed > 0:
                self.logger.warning(f"   ⚠️ {malformed:,} games with malformed weather strings")
        
        if 'weather_provenance' in df.columns:
            self.logger.info(f"   Weather provenance:")
            for prov, count in df['weather_provenance'].value_counts().items():
                self.logger.info(f"     {prov}: {count:,} ({count/len(df)*100:.1f}%)")
        
        # 3. OVERALL SUMMARY
        self.logger.info("\n📊 3. OVERALL SUMMARY")
        self.logger.info("-" * 80)
        
        total_features = len(available)
        self.logger.info(f"   Total features built: {total_features}")
        self.logger.info(f"   Total games: {len(df):,}")
        
        if 'is_weather_model_eligible' in df.columns:
            eligible = df['is_weather_model_eligible'].sum()
            self.logger.info(f"   Model-eligible games: {eligible:,} ({eligible/len(df)*100:.1f}%)")
        
        self.logger.info("\n   ⚠️ V1 FEATURE SET - CONSERVATIVE OBSERVABLES")
        self.logger.info("   - Temperature/wind: Raw values and absolute thresholds")
        self.logger.info("   - Precipitation: Keyword flags (UNVALIDATED heuristic)")
        self.logger.info("   - V2 roadmap: Temperature differentials, historical averages")
        
        self.logger.info("=" * 80)


def create_weather_features(db_service=None, logger=None, bucket_adapter=None):
    """
    Create weather features service with default dependencies.
    
    Follows factory pattern from create_contextual_features() and create_odds_game_features().
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        WeatherFeatures: Configured weather features service
    """
    from ....shared.database_router import get_database_router
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.ml_pipeline.weather_features')
    
    return WeatherFeatures(db_service, logger, bucket_adapter)


__all__ = ['WeatherFeatures', 'create_weather_features']
