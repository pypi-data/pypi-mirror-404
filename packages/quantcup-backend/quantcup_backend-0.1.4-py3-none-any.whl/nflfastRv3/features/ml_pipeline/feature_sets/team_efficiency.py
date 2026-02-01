"""
Team Efficiency Features - V3 Implementation

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + business logic)
Layer: 2 (Implementation - calls infrastructure directly)

V2 Business Logic Preserved:
- Comprehensive team offensive/defensive efficiency metrics
- EPA per play calculations
- Red zone touchdown rates
- Third down conversion rates  
- Turnover rates and differentials
- Efficiency rankings within season
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Union


class TeamEfficiencyFeatures:
    """
    Team efficiency feature engineering service.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + sophisticated calculations)
    Depth: 1 layer (calls database directly)
    
    V2 Capabilities Preserved:
    - Offensive EPA per play
    - Defensive EPA per play allowed
    - Red zone efficiency (offense and defense)
    - Third down conversion rates
    - Turnover rates and differentials
    - Time of possession efficiency
    - Efficiency rankings
    """
    
    def __init__(self, db_service: Any, logger: Any, bucket_adapter: Optional[Any] = None) -> None:
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
            bucket_adapter: Optional bucket adapter for dual-write (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        self.bucket_adapter = bucket_adapter
    
    def build_features(self, seasons: Optional[Union[int, List[int]]] = None) -> Dict[str, Any]:
        """
        Build comprehensive team efficiency features.
        
        Pure computation - orchestrator handles saving (matches model_trainer pattern).
        
        Simple feature engineering flow:
        1. Extract team offensive metrics (Layer 3 call)
        2. Extract team defensive metrics (Layer 3 call)
        3. Calculate efficiency differentials (Layer 3 call)
        4. Add derived features and rankings (Layer 3 call)
        5. Return DataFrame for orchestrator to save
        
        Args:
            seasons: List of seasons to process (default: all available)
            
        Returns:
            Dictionary with feature build results including DataFrame
        """
        self.logger.info(f"Building team efficiency features for seasons: {seasons or 'all'}")
        
        try:
            # Step 1: Build the feature dataset using V2's sophisticated logic
            df = self._build_team_efficiency_dataset(seasons)
            
            if df.empty:
                self.logger.warning("No team efficiency data found")
                return {
                    'status': 'warning',
                    'message': 'No data available',
                    'features_built': 0,
                    'seasons_processed': 0
                }
            
            # Step 2: Add derived features (V2 sophistication preserved)
            df = self._add_derived_efficiency_features(df)
            
            # Step 3: Capture metadata
            features_built = len(df)
            seasons_processed = df['season'].nunique() if 'season' in df.columns else 0
            teams_processed = df['team'].nunique() if 'team' in df.columns else 0
            feature_columns = len(df.columns)
            
            self.logger.info(f"✓ Built team efficiency features: {features_built} team-seasons")
            
            # Return DataFrame for orchestrator to handle saving
            return {
                'status': 'success',
                'dataframe': df,  # ✅ Orchestrator will save this
                'features_built': features_built,
                'seasons_processed': seasons_processed,
                'teams_processed': teams_processed,
                'feature_columns': feature_columns
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build team efficiency features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }
    
    def _build_team_efficiency_dataset(self, seasons: Optional[Union[int, List[int]]] = None) -> pd.DataFrame:
        """
        Build team efficiency dataset from bucket warehouse tables.
        
        MEMORY OPTIMIZED: Uses column selection, categorical types, and efficient data handling.
        
        Bucket-first approach - reads from warehouse/fact_play and warehouse/dim_game
        Preserves V2 business logic using pandas operations
        
        Args:
            seasons: List of seasons to process
            
        Returns:
            DataFrame with team efficiency features
        """
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        from commonv2.utils.memory.manager import create_memory_manager
        import gc
        
        # Define minimal column sets needed for team efficiency calculations
        FACT_PLAY_COLUMNS = [
            # Identifiers
            'game_id', 'season', 'posteam', 'defteam',
            
            # Play characteristics
            'play_type', 'play_id',
            
            # Performance metrics
            'epa', 'yards_gained',
            
            # Situational
            'down', 'ydstogo', 'yardline_100',
            
            # Outcomes
            'touchdown', 'interception', 'fumble_lost',
            
            # Play types
            'rush_attempt', 'pass_attempt', 'third_down_converted'
        ]
        
        DIM_GAME_COLUMNS = [
            'game_id', 'season', 'week', 'game_date',
            'home_team', 'away_team', 'home_score', 'away_score'
        ]
        
        try:
            # Initialize memory manager for observability
            memory_mgr = create_memory_manager(logger=self.logger)
            self.logger.info("🔍 Starting team efficiency calculation...")
            memory_mgr.log_status()
            
            # Read warehouse tables from bucket with optional season filtering
            # MEMORY OPTIMIZATION: Filter during read to avoid loading unnecessary data
            bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
            
            # Prepare filters if seasons specified
            filters = None
            if seasons:
                season_list = seasons if isinstance(seasons, (list, tuple)) else [seasons]
                # Parquet filter format: [('column', 'operator', value)]
                # For multiple seasons, use 'in' operator
                if len(season_list) == 1:
                    filters = [('season', '==', season_list[0])]
                else:
                    filters = [('season', 'in', season_list)]
                self.logger.info(f"📊 Loading warehouse tables from bucket (filtered to season(s) {season_list})...")
            else:
                self.logger.info("📊 Loading warehouse tables from bucket (all seasons)...")
            
            memory_mgr.log_status()
            
            # OPTIMIZATION 1: Load only needed columns (predicate + projection pushdown)
            # Using columns parameter eliminates memory spike from loading all 66 columns
            fact_play = bucket_adapter.read_data('fact_play', 'warehouse', filters=filters, columns=FACT_PLAY_COLUMNS)
            dim_game = bucket_adapter.read_data('dim_game', 'warehouse', filters=filters, columns=DIM_GAME_COLUMNS)
            
            self.logger.info(f"✓ Loaded fact_play with {len(FACT_PLAY_COLUMNS)} columns (projection pushdown)")
            self.logger.info(f"✓ Loaded dim_game with {len(DIM_GAME_COLUMNS)} columns (projection pushdown)")
            
            # OPTIMIZATION 2: Convert to categorical types
            CATEGORICAL_COLUMNS = ['posteam', 'defteam', 'play_type']
            for col in CATEGORICAL_COLUMNS:
                if col in fact_play.columns:
                    fact_play[col] = fact_play[col].astype('category')
            
            for col in ['home_team', 'away_team']:
                if col in dim_game.columns:
                    dim_game[col] = dim_game[col].astype('category')
            
            # Log loaded data sizes
            self._log_dataframe_memory(fact_play, "fact_play")
            self._log_dataframe_memory(dim_game, "dim_game")
            memory_mgr.log_status()
            
            if fact_play.empty or dim_game.empty:
                self.logger.warning("No warehouse data found in bucket")
                return pd.DataFrame()
            
            # OPTIMIZATION 3: Streamlined filtering (no intermediate variable)
            self.logger.info("📊 Filtering for valid plays...")
            fact_play = fact_play[
                (fact_play['play_type'].isin(['pass', 'run'])) &
                (fact_play['epa'].notna())
            ].copy()
            
            # Immediate garbage collection
            self._aggressive_gc()
            
            self.logger.info(f"✓ Filtered to valid plays: {len(fact_play):,} rows")
            memory_mgr.log_status()
            
            # Helper columns for calculations
            # Use third_down_converted if available, otherwise calculate
            if 'third_down_converted' in fact_play.columns:
                fact_play['third_down_conv'] = fact_play['third_down_converted'].fillna(0).astype(float)
            else:
                fact_play['third_down_conv'] = ((fact_play['down'] == 3) &
                                                (fact_play['ydstogo'] <= fact_play['yards_gained'])).astype(float)
            
            # OPTIMIZATION 4: Efficient boolean operations
            fact_play['red_zone'] = (fact_play['yardline_100'] <= 20)
            fact_play['red_zone_td'] = (
                fact_play['red_zone'] &
                (fact_play['touchdown'].fillna(0) == 1)
            ).astype(float)
            
            # Turnover calculation - use fumble_lost and interception columns
            fact_play['is_turnover'] = (
                (fact_play['interception'].fillna(0) == 1) |
                (fact_play['fumble_lost'].fillna(0) == 1)
            ).astype(int)
            
            # Calculate team offensive metrics (optimized for speed)
            self.logger.info("📊 Calculating team offensive metrics...")
            memory_mgr.log_status()
            
            offense_df = fact_play[fact_play['posteam'].notna()].copy()
            team_offense = offense_df.groupby(['posteam', 'season'], observed=True).agg({
                'play_id': 'count',
                'epa': 'mean',
                'third_down_conv': 'mean',
                'red_zone_td': 'sum',
                'red_zone': 'sum',
                'is_turnover': 'sum',
                'touchdown': 'sum'
            }).reset_index()
            
            # Additional metrics requiring filtering
            rush_yards = offense_df[offense_df['rush_attempt'] == 1].groupby(['posteam', 'season'], observed=True)['yards_gained'].mean()
            pass_yards = offense_df[offense_df['pass_attempt'] == 1].groupby(['posteam', 'season'], observed=True)['yards_gained'].mean()
            pass_epa = offense_df[offense_df['play_type'] == 'pass'].groupby(['posteam', 'season'], observed=True)['epa'].mean()
            rush_epa = offense_df[offense_df['play_type'] == 'run'].groupby(['posteam', 'season'], observed=True)['epa'].mean()
            
            team_offense = team_offense.merge(rush_yards.rename('avg_rush_yards'), left_on=['posteam', 'season'], right_index=True, how='left')
            team_offense = team_offense.merge(pass_yards.rename('avg_pass_yards'), left_on=['posteam', 'season'], right_index=True, how='left')
            team_offense = team_offense.merge(pass_epa.rename('pass_epa'), left_on=['posteam', 'season'], right_index=True, how='left')
            team_offense = team_offense.merge(rush_epa.rename('rush_epa'), left_on=['posteam', 'season'], right_index=True, how='left')
            
            # Clear intermediate Series objects
            del rush_yards, pass_yards, pass_epa, rush_epa
            
            # Calculate red zone TD rate
            team_offense['red_zone_td_rate'] = team_offense['red_zone_td'] / team_offense['red_zone'].replace(0, 1)
            
            # Rename columns
            team_offense = team_offense.rename(columns={
                'posteam': 'team',
                'play_id': 'offensive_plays',
                'epa': 'avg_offensive_epa',
                'third_down_conv': 'third_down_conversion_rate',
                'is_turnover': 'turnovers_lost',
                'touchdown': 'touchdowns_scored'
            })
            
            # Clear offense_df to free memory
            del offense_df
            self._aggressive_gc()
            
            self.logger.info(f"✓ Calculated offensive metrics for {len(team_offense):,} team-seasons")
            memory_mgr.log_status()
            
            # Calculate team defensive metrics (optimized for speed)
            self.logger.info("📊 Calculating team defensive metrics...")
            defense_df = fact_play[fact_play['defteam'].notna()].copy()
            team_defense = defense_df.groupby(['defteam', 'season'], observed=True).agg({
                'play_id': 'count',
                'epa': 'mean',
                'third_down_conv': 'mean',
                'red_zone_td': 'sum',
                'red_zone': 'sum',
                'is_turnover': 'sum',
                'touchdown': 'sum'
            }).reset_index()
            
            # Additional defensive metrics
            rush_yards_allowed = defense_df[defense_df['rush_attempt'] == 1].groupby(['defteam', 'season'], observed=True)['yards_gained'].mean()
            pass_yards_allowed = defense_df[defense_df['pass_attempt'] == 1].groupby(['defteam', 'season'], observed=True)['yards_gained'].mean()
            pass_epa_allowed = defense_df[defense_df['play_type'] == 'pass'].groupby(['defteam', 'season'], observed=True)['epa'].mean()
            rush_epa_allowed = defense_df[defense_df['play_type'] == 'run'].groupby(['defteam', 'season'], observed=True)['epa'].mean()
            
            team_defense = team_defense.merge(rush_yards_allowed.rename('avg_rush_yards_allowed'), left_on=['defteam', 'season'], right_index=True, how='left')
            team_defense = team_defense.merge(pass_yards_allowed.rename('avg_pass_yards_allowed'), left_on=['defteam', 'season'], right_index=True, how='left')
            team_defense = team_defense.merge(pass_epa_allowed.rename('pass_epa_allowed'), left_on=['defteam', 'season'], right_index=True, how='left')
            team_defense = team_defense.merge(rush_epa_allowed.rename('rush_epa_allowed'), left_on=['defteam', 'season'], right_index=True, how='left')
            
            # Clear intermediate Series objects
            del rush_yards_allowed, pass_yards_allowed, pass_epa_allowed, rush_epa_allowed
            
            # Calculate red zone TD rate allowed
            team_defense['red_zone_td_rate_allowed'] = team_defense['red_zone_td'] / team_defense['red_zone'].replace(0, 1)
            
            # Rename columns
            team_defense = team_defense.rename(columns={
                'defteam': 'team',
                'play_id': 'defensive_plays',
                'epa': 'avg_defensive_epa_allowed',
                'third_down_conv': 'third_down_conversion_rate_allowed',
                'is_turnover': 'turnovers_forced',
                'touchdown': 'touchdowns_allowed'
            })
            
            # Clear defense_df and fact_play to free memory
            del defense_df, fact_play
            self._aggressive_gc()
            
            self.logger.info(f"✓ Calculated defensive metrics for {len(team_defense):,} team-seasons")
            self.logger.info("✓ Freed fact_play from memory")
            memory_mgr.log_status()
            
            # Calculate games played per team
            self.logger.info("📊 Calculating team records...")
            home_games = dim_game.groupby(['home_team', 'season'], observed=True).size().reset_index(name='games')
            home_games.columns = ['team', 'season', 'games']
            away_games = dim_game.groupby(['away_team', 'season'], observed=True).size().reset_index(name='games')
            away_games.columns = ['team', 'season', 'games']
            team_games = pd.concat([home_games, away_games]).groupby(['team', 'season'], observed=True)['games'].sum().reset_index(name='games_played')
            
            # Clear intermediate DataFrames
            del home_games, away_games, dim_game
            self._aggressive_gc()
            
            self.logger.info("✓ Freed dim_game from memory")
            memory_mgr.log_status()
            
            # Merge all metrics
            self.logger.info("📊 Merging offensive, defensive, and game metrics...")
            df = team_offense.merge(team_defense, on=['team', 'season'], how='outer', suffixes=('', '_def'))
            df = df.merge(team_games, on=['team', 'season'], how='left')
            
            # Clear intermediate DataFrames
            del team_offense, team_defense, team_games
            self._aggressive_gc()
            
            self.logger.info(f"✓ Merged metrics: {len(df):,} team-seasons")
            memory_mgr.log_status()
            
            # Round numeric columns (V2 precision preserved)
            numeric_cols = {
                'avg_offensive_epa': 4, 'third_down_conversion_rate': 4, 'red_zone_td_rate': 4,
                'avg_rush_yards': 2, 'avg_pass_yards': 2, 'pass_epa': 4, 'rush_epa': 4,
                'avg_defensive_epa_allowed': 4, 'third_down_conversion_rate_allowed': 4,
                'red_zone_td_rate_allowed': 4, 'avg_rush_yards_allowed': 2, 'avg_pass_yards_allowed': 2,
                'pass_epa_allowed': 4, 'rush_epa_allowed': 4
            }
            
            for col, decimals in numeric_cols.items():
                if col in df.columns:
                    df[col] = df[col].round(decimals)
            
            # OPTIMIZATION 6: Downcast numeric types before final operations
            df = self._optimize_dtypes(df)
            
            # Rename columns to match schema
            df = df.rename(columns={
                'avg_offensive_epa': 'offensive_epa_per_play',
                'third_down_conversion_rate': 'offensive_third_down_rate',
                'red_zone_td_rate': 'offensive_red_zone_td_rate',
                'turnovers_lost': 'offensive_turnovers',
                'avg_rush_yards': 'avg_rushing_yards',
                'avg_pass_yards': 'avg_passing_yards',
                'touchdowns_scored': 'offensive_touchdowns',
                'pass_epa': 'offensive_pass_epa',
                'rush_epa': 'offensive_rush_epa',
                'avg_defensive_epa_allowed': 'defensive_epa_per_play_allowed',
                'third_down_conversion_rate_allowed': 'defensive_third_down_rate_allowed',
                'red_zone_td_rate_allowed': 'defensive_red_zone_td_rate_allowed',
                'turnovers_forced': 'defensive_turnovers_forced',
                'avg_rush_yards_allowed': 'avg_rushing_yards_allowed',
                'avg_pass_yards_allowed': 'avg_passing_yards_allowed',
                'touchdowns_allowed': 'defensive_touchdowns_allowed',
                'pass_epa_allowed': 'defensive_pass_epa_allowed',
                'rush_epa_allowed': 'defensive_rush_epa_allowed'
            })
            
            # Calculate efficiency ratios 
            df['turnover_rate_offense'] = (df['offensive_turnovers'] / df['offensive_plays'].replace(0, 1)).round(6)
            df['turnover_rate_defense'] = (df['defensive_turnovers_forced'] / df['defensive_plays'].replace(0, 1)).round(6)
            df['touchdowns_per_game'] = (df['offensive_touchdowns'] / df['games_played'].replace(0, 1)).round(2)
            df['touchdowns_allowed_per_game'] = (df['defensive_touchdowns_allowed'] / df['games_played'].replace(0, 1)).round(2)
            
            # Sort by season and team
            df = df.sort_values(['season', 'team'], ascending=[False, True]).reset_index(drop=True)
            
            # Validate the feature data
            required_columns = ['team', 'season', 'offensive_epa_per_play', 'defensive_epa_per_play_allowed']
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                self.logger.error(f"Missing required columns in team efficiency features: {missing_cols}")
                return pd.DataFrame()
            
            # Final memory status
            final_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            final_status = memory_mgr.get_status()
            self.logger.info(
                f"✓ Team efficiency calculation complete: {len(df):,} team-seasons, "
                f"{len(df.columns)} columns, {final_mb:.1f}MB"
            )
            self.logger.info(
                f"✓ Final memory: {final_status['current_usage_mb']:.1f}MB / {final_status['max_memory_mb']}MB "
                f"({final_status['usage_percent']:.1f}% used)"
            )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to extract team efficiency data from bucket: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _add_derived_efficiency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived efficiency features.
        
        Args:
            df: DataFrame with base team efficiency features
            
        Returns:
            DataFrame with additional derived features
        """
        if df.empty:
            return df
        
        self.logger.debug("Adding derived efficiency features")
        
        # Calculate efficiency differentials
        df['epa_differential'] = df['offensive_epa_per_play'] - df['defensive_epa_per_play_allowed']
        df['pass_epa_differential'] = df['offensive_pass_epa'] - df['defensive_pass_epa_allowed']
        df['rush_epa_differential'] = df['offensive_rush_epa'] - df['defensive_rush_epa_allowed']
        
        # Calculate turnover differential
        df['turnover_differential'] = df['defensive_turnovers_forced'] - df['offensive_turnovers']
        
        # Calculate scoring differential per game 
        df['scoring_differential_per_game'] = df['touchdowns_per_game'] - df['touchdowns_allowed_per_game']
        
        # Calculate yards differential 
        df['rushing_yards_differential'] = df['avg_rushing_yards'] - df['avg_rushing_yards_allowed']
        df['passing_yards_differential'] = df['avg_passing_yards'] - df['avg_passing_yards_allowed']
        
        # Calculate efficiency rankings within season
        for season in df['season'].unique():
            season_mask = df['season'] == season
            
            # Offensive rankings (higher is better)
            df.loc[season_mask, 'offensive_epa_rank'] = df.loc[season_mask, 'offensive_epa_per_play'].rank(ascending=False)  # type: ignore[attr-defined]
            df.loc[season_mask, 'offensive_third_down_rank'] = df.loc[season_mask, 'offensive_third_down_rate'].rank(ascending=False)  # type: ignore[attr-defined]
            df.loc[season_mask, 'offensive_red_zone_rank'] = df.loc[season_mask, 'offensive_red_zone_td_rate'].rank(ascending=False)  # type: ignore[attr-defined]
            
            # Defensive rankings (lower is better for EPA allowed)
            df.loc[season_mask, 'defensive_epa_rank'] = df.loc[season_mask, 'defensive_epa_per_play_allowed'].rank(ascending=True)  # type: ignore[attr-defined]
            df.loc[season_mask, 'defensive_third_down_rank'] = df.loc[season_mask, 'defensive_third_down_rate_allowed'].rank(ascending=True)  # type: ignore[attr-defined]
            df.loc[season_mask, 'defensive_red_zone_rank'] = df.loc[season_mask, 'defensive_red_zone_td_rate_allowed'].rank(ascending=True)  # type: ignore[attr-defined]
            
            # Overall efficiency rank
            df.loc[season_mask, 'overall_efficiency_rank'] = df.loc[season_mask, 'epa_differential'].rank(ascending=False)  # type: ignore[attr-defined]
            df.loc[season_mask, 'turnover_differential_rank'] = df.loc[season_mask, 'turnover_differential'].rank(ascending=False)  # type: ignore[attr-defined]
        
        self.logger.debug(f"Added derived features: {len(df.columns)} total columns")
        return df
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Downcast numeric types to reduce memory footprint (MEMORY OPTIMIZED).
        
        Args:
            df: DataFrame to optimize
            
        Returns:
            DataFrame with optimized dtypes
        """
        # Downcast floats (float64 -> float32 where precision allows)
        float_cols = df.select_dtypes(include=['float64']).columns
        for col in float_cols:
            # Skip columns requiring high precision (EPA calculations and ranks)
            if 'epa' in col.lower() or 'rank' in col.lower():
                continue
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Downcast integers (int64 -> int32/int16 where range allows)
        int_cols = df.select_dtypes(include=['int64']).columns
        for col in int_cols:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        return df
    
    def _aggressive_gc(self):
        """Force aggressive garbage collection with multiple passes (MEMORY OPTIMIZED)."""
        import gc
        collected = gc.collect()
        collected += gc.collect()  # Second pass for circular references
        self.logger.debug(f"Garbage collection freed {collected} objects")
        return collected
    
    def _log_dataframe_memory(self, df: pd.DataFrame, name: str):
        """
        Log detailed memory usage for a DataFrame (MEMORY OBSERVABILITY).
        
        Args:
            df: DataFrame to analyze
            name: Name for logging
        """
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        self.logger.info(
            f"📊 {name}: {len(df):,} rows × {len(df.columns)} cols = {memory_mb:.1f}MB"
        )
        
        # Log top memory-consuming columns
        col_memory = df.memory_usage(deep=True).sort_values(ascending=False).head(5)
        for col, mem in col_memory.items():
            if col != 'Index':
                self.logger.debug(f"   - {col}: {mem / (1024*1024):.1f}MB")

# Convenience function for direct usage
def create_team_efficiency_features(
    db_service: Optional[Any] = None,
    logger: Optional[Any] = None,
    bucket_adapter: Optional[Any] = None
) -> TeamEfficiencyFeatures:
    """
    Create team efficiency features service with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        TeamEfficiencyFeatures: Configured team efficiency features service
    """
    from nflfastRv3.shared.database_router import get_database_router
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.ml_pipeline.team_efficiency')
    
    return TeamEfficiencyFeatures(db_service, logger, bucket_adapter)


__all__ = ['TeamEfficiencyFeatures', 'create_team_efficiency_features']
