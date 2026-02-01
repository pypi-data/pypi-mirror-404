"""
Opponent Adjusted Features - V3 Implementation

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + business logic)
Layer: 2 (Implementation - calls infrastructure directly)

V2 Business Logic Preserved:
- Strength-of-schedule calculations
- Opponent quality adjustments
- Context-weighted performance metrics
- Division/conference strength analysis
- Quality of wins/losses tracking
"""

import pandas as pd
from typing import Dict, Any, List, Optional

from commonv2 import get_logger
from nflfastRv3.shared.schedule_provider import ScheduleDataProvider
from nflfastRv3.shared.models import ValidationResult


class OpponentAdjustedFeatures:
    """
    Opponent-adjusted feature engineering service.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + strength-of-schedule calculations)
    Depth: 1 layer (calls database directly)
    
    V2 Capabilities Preserved:
    - Strength of schedule metrics
    - Opponent quality adjustments
    - Context-weighted team performance
    - Division and conference strength
    - Quality of wins and losses
    """
    
    def __init__(self, db_service, logger, schedule_provider=None, bucket_adapter=None):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
            schedule_provider: Optional CommonV2 schedule provider
            bucket_adapter: Optional bucket adapter for dual-write (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        self.schedule_provider = schedule_provider or ScheduleDataProvider()
        self.bucket_adapter = bucket_adapter
    
    def build_features(self, seasons=None) -> Dict[str, Any]:
        """
        Build comprehensive opponent-adjusted features with CommonV2 integration.
        
        Pure computation - orchestrator handles saving (matches model_trainer pattern).
        
        Enhanced feature engineering flow:
        1. Validate seasons using CommonV2 schedule data
        2. Calculate base team strength metrics (Layer 3 call)
        3. Calculate opponent quality for each game (Layer 3 call)
        4. Adjust team performance by opponent strength (Layer 3 call)
        5. Calculate strength-of-schedule metrics (Layer 3 call)
        6. Integrate with CommonV2 schedule context
        7. Return DataFrame for orchestrator to save
        
        Args:
            seasons: List of seasons to process (default: all available)
            
        Returns:
            Dictionary with feature build results including DataFrame
        """
        self.logger.info(f"Building opponent-adjusted features for seasons: {seasons or 'all'}")
        
        try:
            # Step 0: Validate seasons with CommonV2 schedule data
            # ✅ PERFORMANCE FIX: Get schedule data once and reuse it
            validated_seasons, schedule_data = self._validate_seasons_with_schedule_data(seasons)
            if not validated_seasons:
                self.logger.warning("No valid seasons found in schedule data")
                return {
                    'status': 'warning',
                    'message': 'No valid seasons with schedule data',
                    'features_built': 0,
                    'seasons_processed': 0
                }
            
            # Step 1: Calculate base team strength metrics
            team_strength_df = self._calculate_team_strength(validated_seasons)
            
            if team_strength_df.empty:
                self.logger.warning("No team strength data found")
                return {
                    'status': 'warning',
                    'message': 'No data available',
                    'features_built': 0,
                    'seasons_processed': 0
                }
            
            # Step 2: Calculate game-level opponent adjustments
            game_adjustments_df = self._calculate_game_adjustments(validated_seasons, team_strength_df)
            
            # Step 3: Aggregate to team-season level with opponent adjustments
            df = self._aggregate_opponent_adjusted_metrics(game_adjustments_df)
            
            # Step 4: Add strength-of-schedule calculations
            df = self._add_strength_of_schedule_metrics(df, team_strength_df)
            
            # Step 5: Enhance with CommonV2 schedule context
            # ✅ PERFORMANCE FIX: Pass already-loaded schedule data
            df = self._add_schedule_context_features(df, validated_seasons, schedule_data)
            
            # Step 6: Validate feature quality
            validation = self._validate_opponent_features(df)
            if not validation.is_valid:
                self.logger.warning(f"Feature validation issues: {validation.errors}")
            
            # Step 7: Capture metadata
            features_built = len(df)
            seasons_processed = df['season'].nunique() if 'season' in df.columns else 0
            teams_processed = df['team'].nunique() if 'team' in df.columns else 0
            feature_columns = len(df.columns)
            
            self.logger.info(f"✓ Built opponent-adjusted features: {features_built} team-seasons")
            
            # Return DataFrame for orchestrator to handle saving
            return {
                'status': 'success',
                'dataframe': df,  # ✅ Orchestrator will save this
                'features_built': features_built,
                'seasons_processed': seasons_processed,
                'teams_processed': teams_processed,
                'feature_columns': feature_columns,
                'validation': validation,
                'seasons_validated': validated_seasons
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build opponent-adjusted features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }
    
    def _calculate_team_strength(self, seasons=None) -> pd.DataFrame:
        """
        Calculate base team strength metrics from bucket warehouse tables.
        
        MEMORY OBSERVABILITY: Tracks memory usage during data loading and processing.
        MEMORY OPTIMIZED: Follows team_efficiency.py pattern - aggregate first, no play-level merges
        
        Bucket-first approach - reads from warehouse/fact_play and warehouse/dim_game
        Preserves V2 business logic using pandas operations
        
        Args:
            seasons: List of seasons to process
            
        Returns:
            DataFrame with team strength metrics by season
        """
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        from commonv2.utils.memory.manager import create_memory_manager
        import gc
        
        # Define minimal column sets needed for team strength calculations
        FACT_PLAY_COLUMNS = [
            # Identifiers
            'game_id', 'season', 'posteam', 'defteam', 'play_id',
            
            # Play characteristics
            'play_type',
            
            # Performance metrics
            'epa', 'yards_gained',
            
            # Situational
            'down', 'yardline_100', 'score_differential',
            
            # Outcomes
            'touchdown', 'interception', 'fumble_lost',
            
            # Play types
            'rush_attempt', 'pass_attempt'
        ]
        
        DIM_GAME_COLUMNS = [
            'game_id', 'season', 'home_team', 'away_team',
            'home_score', 'away_score'
        ]
        
        try:
            # Initialize memory manager for observability
            memory_mgr = create_memory_manager(logger=self.logger)
            self.logger.info("🔍 Starting team strength calculation...")
            memory_mgr.log_status()
            
            # Read warehouse tables from bucket with optional season filtering
            # MEMORY OPTIMIZATION: Filter during read to avoid loading unnecessary data
            bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
            
            # Prepare filters if seasons specified
            filters = None
            if seasons:
                season_list = seasons if isinstance(seasons, (list, tuple)) else [seasons]
                if len(season_list) == 1:
                    filters = [('season', '==', season_list[0])]
                else:
                    filters = [('season', 'in', season_list)]
                self.logger.info(f"📊 Loading warehouse tables from bucket (filtered to season(s) {season_list})...")
            else:
                self.logger.info("📊 Loading warehouse tables from bucket (all seasons)...")
            
            memory_mgr.log_status()
            
            # OPTIMIZATION: Load only needed columns (predicate + projection pushdown)
            fact_play = bucket_adapter.read_data('fact_play', 'warehouse', filters=filters, columns=FACT_PLAY_COLUMNS)
            dim_game = bucket_adapter.read_data('dim_game', 'warehouse', filters=filters, columns=DIM_GAME_COLUMNS)
            
            # Log loaded data sizes
            fact_play_mb = fact_play.memory_usage(deep=True).sum() / (1024 * 1024)
            dim_game_mb = dim_game.memory_usage(deep=True).sum() / (1024 * 1024)
            self.logger.info(f"✓ Loaded fact_play: {len(fact_play):,} rows, {len(fact_play.columns)} cols, {fact_play_mb:.1f}MB")
            self.logger.info(f"✓ Loaded dim_game: {len(dim_game):,} rows, {len(dim_game.columns)} cols, {dim_game_mb:.1f}MB")
            memory_mgr.log_status()
            
            if fact_play.empty or dim_game.empty:
                self.logger.warning("No warehouse data found in bucket")
                return pd.DataFrame()
            
            # Filter for valid plays
            self.logger.info("📊 Filtering for valid plays...")
            fact_play_valid = fact_play[
                (fact_play['posteam'].notna()) &
                (fact_play['play_type'].isin(['pass', 'run'])) &
                (fact_play['epa'].notna())
            ].copy()
            
            # Delete unfiltered fact_play
            del fact_play
            gc.collect()
            
            fact_play = fact_play_valid
            del fact_play_valid
            
            self.logger.info(f"✓ Filtered to valid plays: {len(fact_play):,} rows")
            memory_mgr.log_status()
            
            # MEMORY OPTIMIZATION: Aggregate fact_play to team-season level FIRST
            # This follows team_efficiency.py pattern - NO play-level merges
            self.logger.info("📊 Calculating team statistics...")
            memory_mgr.log_status()
            
            # Calculate team season stats (aggregated from plays)
            team_stats = fact_play.groupby(['posteam', 'season']).agg({
                'play_id': 'count',
                'epa': 'mean',
                'game_id': 'nunique'
            }).reset_index()
            team_stats.columns = ['team', 'season', 'total_plays', 'avg_epa_offense', 'games_played']
            
            # Calculate defensive EPA
            def_epa = fact_play[fact_play['defteam'].notna()].groupby(['defteam', 'season'])['epa'].mean().reset_index()
            def_epa.columns = ['team', 'season', 'avg_epa_defense_allowed']
            team_stats = team_stats.merge(def_epa, on=['team', 'season'], how='left')
            del def_epa
            gc.collect()
            
            # Situational performance
            early_down = fact_play[fact_play['down'] <= 2].groupby(['posteam', 'season'])['epa'].mean().reset_index()
            early_down.columns = ['team', 'season', 'early_down_epa']
            team_stats = team_stats.merge(early_down, on=['team', 'season'], how='left')
            del early_down
            gc.collect()
            
            late_down = fact_play[fact_play['down'] >= 3].groupby(['posteam', 'season'])['epa'].mean().reset_index()
            late_down.columns = ['team', 'season', 'late_down_epa']
            team_stats = team_stats.merge(late_down, on=['team', 'season'], how='left')
            del late_down
            gc.collect()
            
            red_zone = fact_play[fact_play['yardline_100'] <= 20].groupby(['posteam', 'season'])['epa'].mean().reset_index()
            red_zone.columns = ['team', 'season', 'red_zone_epa']
            team_stats = team_stats.merge(red_zone, on=['team', 'season'], how='left')
            del red_zone
            gc.collect()
            
            close_game = fact_play[fact_play['score_differential'].between(-7, 7)].groupby(['posteam', 'season'])['epa'].mean().reset_index()
            close_game.columns = ['team', 'season', 'close_game_epa']
            team_stats = team_stats.merge(close_game, on=['team', 'season'], how='left')
            del close_game
            gc.collect()
            
            # Advanced metrics
            touchdowns = fact_play[fact_play['touchdown'] == 1].groupby(['posteam', 'season']).size().reset_index(name='touchdowns')
            team_stats = team_stats.merge(touchdowns, left_on=['team', 'season'], right_on=['posteam', 'season'], how='left')
            team_stats = team_stats.drop('posteam', axis=1, errors='ignore')
            del touchdowns
            gc.collect()
            
            turnovers = fact_play[(fact_play['interception'] == 1) | (fact_play['fumble_lost'] == 1)].groupby(['posteam', 'season']).size().reset_index(name='turnovers')
            team_stats = team_stats.merge(turnovers, left_on=['team', 'season'], right_on=['posteam', 'season'], how='left')
            team_stats = team_stats.drop('posteam', axis=1, errors='ignore')
            del turnovers
            gc.collect()
            
            pass_epa = fact_play[fact_play['pass_attempt'] == 1].groupby(['posteam', 'season'])['epa'].mean().reset_index()
            pass_epa.columns = ['team', 'season', 'pass_epa']
            team_stats = team_stats.merge(pass_epa, on=['team', 'season'], how='left')
            del pass_epa
            gc.collect()
            
            rush_epa = fact_play[fact_play['rush_attempt'] == 1].groupby(['posteam', 'season'])['epa'].mean().reset_index()
            rush_epa.columns = ['team', 'season', 'rush_epa']
            team_stats = team_stats.merge(rush_epa, on=['team', 'season'], how='left')
            del rush_epa
            gc.collect()
            
            # Delete fact_play now that we've aggregated everything
            del fact_play
            gc.collect()
            
            self.logger.info(f"✓ Calculated stats for {len(team_stats):,} team-seasons")
            self.logger.info("✓ Freed fact_play from memory")
            memory_mgr.log_status()
            
            # Calculate team records from games (deduplicate dim_game first)
            self.logger.info("📊 Calculating team records...")
            memory_mgr.log_status()
            
            # Deduplicate dim_game to get unique games only
            dim_game_unique = dim_game.drop_duplicates(subset=['game_id']).copy()
            del dim_game
            gc.collect()
            
            self.logger.info(f"✓ Deduplicated to {len(dim_game_unique):,} unique games")
            
            home_games = dim_game_unique[['season', 'home_team', 'home_score', 'away_score']].copy()
            home_games['wins'] = (home_games['home_score'] > home_games['away_score']).astype(int)
            home_games['losses'] = (home_games['home_score'] < home_games['away_score']).astype(int)
            home_records = home_games.groupby(['home_team', 'season']).agg({'wins': 'sum', 'losses': 'sum'}).reset_index()
            home_records.columns = ['team', 'season', 'home_wins', 'home_losses']
            
            away_games = dim_game_unique[['season', 'away_team', 'home_score', 'away_score']].copy()
            away_games['wins'] = (away_games['away_score'] > away_games['home_score']).astype(int)
            away_games['losses'] = (away_games['away_score'] < away_games['home_score']).astype(int)
            away_records = away_games.groupby(['away_team', 'season']).agg({'wins': 'sum', 'losses': 'sum'}).reset_index()
            away_records.columns = ['team', 'season', 'away_wins', 'away_losses']
            
            # Combine records
            records = home_records.merge(away_records, on=['team', 'season'], how='outer').fillna(0)
            records['wins'] = records['home_wins'] + records['away_wins']
            records['losses'] = records['home_losses'] + records['away_losses']
            records['win_percentage'] = records['wins'] / (records['wins'] + records['losses']).replace(0, 1)
            records = records[['team', 'season', 'wins', 'losses', 'win_percentage']]
            
            # Clear intermediate DataFrames
            del home_games, away_games, home_records, away_records, dim_game_unique
            gc.collect()
            self.logger.info("✓ Freed dim_game and record calculation intermediates from memory")
            memory_mgr.log_status()
            
            # Merge stats with records
            self.logger.info("📊 Merging stats with records...")
            df = team_stats.merge(records, on=['team', 'season'], how='outer')
            
            # Clear intermediate DataFrames
            del team_stats, records
            gc.collect()
            
            self.logger.info("✓ Freed intermediate DataFrames from memory")
            memory_mgr.log_status()
            
            self.logger.info(f"✓ Created team strength DataFrame: {len(df):,} team-seasons")
            memory_mgr.log_status()
            
            # Fill NaN values
            df = df.fillna(0)
            
            # Calculate strength metrics (V2 sophistication preserved)
            df['team_strength_offense'] = df['avg_epa_offense'].round(4)
            df['team_strength_defense'] = df['avg_epa_defense_allowed'].round(4)
            df['team_strength_overall'] = (df['avg_epa_offense'] - df['avg_epa_defense_allowed']).round(4)
            
            # Situational strength
            df['early_down_strength'] = df['early_down_epa'].round(4)
            df['late_down_strength'] = df['late_down_epa'].round(4)
            df['red_zone_strength'] = df['red_zone_epa'].round(4)
            df['close_game_strength'] = df['close_game_epa'].round(4)
            
            # Component strengths
            df['pass_strength'] = df['pass_epa'].round(4)
            df['rush_strength'] = df['rush_epa'].round(4)
            
            # Efficiency metrics
            df['touchdowns_per_game'] = (df['touchdowns'] / df['games_played'].replace(0, 1)).round(2)
            df['turnovers_per_game'] = (df['turnovers'] / df['games_played'].replace(0, 1)).round(2)
            
            # Round win percentage
            df['win_percentage'] = df['win_percentage'].round(4)
            
            # Sort by season and strength
            df = df.sort_values(['season', 'team_strength_overall'], ascending=[False, False]).reset_index(drop=True)
            
            # Validate the team strength data
            required_columns = ['team', 'season', 'team_strength_offense', 'team_strength_defense']
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                self.logger.error(f"Missing required columns in team strength data: {missing_cols}")
                return pd.DataFrame()
            
            # Final memory status
            final_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            final_status = memory_mgr.get_status()
            self.logger.info(
                f"✓ Team strength calculation complete: {len(df):,} team-seasons, "
                f"{len(df.columns)} columns, {final_mb:.1f}MB"
            )
            self.logger.info(
                f"✓ Final memory: {final_status['current_usage_mb']:.1f}MB / {final_status['max_memory_mb']}MB "
                f"({final_status['usage_percent']:.1f}% used)"
            )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to calculate team strength from bucket: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _calculate_game_adjustments(self, seasons, team_strength_df) -> pd.DataFrame:
        """
        Calculate game-level opponent adjustments from bucket warehouse tables.
        
        MEMORY OPTIMIZED: Uses single-pass merges and explicit garbage collection
        to prevent memory exhaustion during large dataset processing.
        
        MEMORY OBSERVABILITY: Tracks memory usage at each step to identify bottlenecks.
        
        Bucket-first approach - reads from warehouse/fact_play and warehouse/dim_game
        Preserves V2 business logic using pandas operations
        
        Args:
            seasons: List of seasons to process
            team_strength_df: DataFrame with team strength metrics
            
        Returns:
            DataFrame with game-level opponent adjustments
        """
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        from commonv2.utils.memory.manager import create_memory_manager
        import gc
        
        # Define minimal column sets needed for game adjustments
        FACT_PLAY_COLUMNS = [
            'game_id', 'season', 'posteam', 'defteam', 'play_type', 'epa'
        ]
        
        DIM_GAME_COLUMNS = [
            'game_id', 'season', 'week', 'home_team', 'away_team',
            'home_score', 'away_score'
        ]
        
        try:
            # Initialize memory manager for observability
            memory_mgr = create_memory_manager(logger=self.logger)
            memory_mgr.log_status()
            
            # Read warehouse tables from bucket with optional season filtering
            # MEMORY OPTIMIZATION: Filter during read to avoid loading unnecessary data
            bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
            
            # Prepare filters if seasons specified
            filters = None
            if seasons:
                season_list = seasons if isinstance(seasons, (list, tuple)) else [seasons]
                if len(season_list) == 1:
                    filters = [('season', '==', season_list[0])]
                else:
                    filters = [('season', 'in', season_list)]
                self.logger.info(f"📊 Step 1: Reading warehouse tables from bucket (filtered to season(s) {season_list})...")
            else:
                self.logger.info("📊 Step 1: Reading warehouse tables from bucket (all seasons)...")
            
            memory_mgr.log_status()
            
            # OPTIMIZATION: Load only needed columns (predicate + projection pushdown)
            fact_play = bucket_adapter.read_data('fact_play', 'warehouse', filters=filters, columns=FACT_PLAY_COLUMNS)
            dim_game = bucket_adapter.read_data('dim_game', 'warehouse', filters=filters, columns=DIM_GAME_COLUMNS)
            
            self.logger.info(f"✓ Loaded fact_play: {len(fact_play):,} rows, {len(fact_play.columns)} columns")
            self.logger.info(f"✓ Loaded dim_game: {len(dim_game):,} rows, {len(dim_game.columns)} columns")
            memory_mgr.log_status()
            
            if fact_play.empty or dim_game.empty:
                self.logger.warning("No warehouse data found in bucket")
                return pd.DataFrame()
            
            # Deduplicate dim_game to get unique games
            dim_game_unique = dim_game.drop_duplicates(subset=['game_id']).copy()
            del dim_game
            gc.collect()
            self.logger.info(f"✓ Deduplicated to {len(dim_game_unique):,} unique games")
            
            # Filter for valid plays
            fact_play_valid = fact_play[
                (fact_play['play_type'].isin(['pass', 'run'])) &
                (fact_play['epa'].notna())
            ].copy()
            
            # Delete unfiltered fact_play
            del fact_play
            gc.collect()
            
            fact_play = fact_play_valid
            del fact_play_valid
            
            # MEMORY OPTIMIZATION: Calculate stats and merge BEFORE creating game records
            # This reduces intermediate DataFrame creation
            
            self.logger.info("📊 Step 2: Aggregating team-game statistics...")
            memory_mgr.log_status()
            
            # Calculate offensive stats per game per team using groupby
            offense_stats = fact_play.groupby(['game_id', 'posteam']).agg({
                'epa': ['sum', 'mean', 'count']
            }).reset_index()
            offense_stats.columns = ['game_id', 'team', 'offensive_epa', 'epa_per_play', 'total_plays']
            
            # Calculate defensive stats per game per team using groupby
            defense_stats = fact_play.groupby(['game_id', 'defteam']).agg({
                'epa': 'sum'
            }).reset_index()
            defense_stats.columns = ['game_id', 'team', 'defensive_epa']
            
            # OPTIMIZATION: Merge stats together first, then clear fact_play
            team_game_stats = offense_stats.merge(defense_stats, on=['game_id', 'team'], how='outer')
            team_game_stats = team_game_stats.fillna(0)
            
            # Clear large intermediate DataFrames
            del offense_stats, defense_stats, fact_play
            gc.collect()
            
            self.logger.info(f"✓ Aggregated stats for {len(team_game_stats):,} team-games")
            self.logger.info(f"✓ Cleared fact_play from memory ({len(team_game_stats.columns)} columns)")
            memory_mgr.log_status()
            
            # OPTIMIZATION: Build game records efficiently using list comprehension
            # More memory-efficient than creating two large DataFrames and concatenating
            self.logger.info("📊 Step 3: Building game records...")
            memory_mgr.log_status()
            
            game_records = []
            for _, game in dim_game_unique.iterrows():
                # Home team record
                game_records.append({
                    'game_id': game['game_id'],
                    'season': game['season'],
                    'week': game['week'],
                    'team': game['home_team'],
                    'opponent_team': game['away_team'],
                    'venue': 'home',
                    'win': int(game['home_score'] > game['away_score']),
                    'points_for': game['home_score'],
                    'points_against': game['away_score'],
                    'point_differential': game['home_score'] - game['away_score']
                })
                # Away team record
                game_records.append({
                    'game_id': game['game_id'],
                    'season': game['season'],
                    'week': game['week'],
                    'team': game['away_team'],
                    'opponent_team': game['home_team'],
                    'venue': 'away',
                    'win': int(game['away_score'] > game['home_score']),
                    'points_for': game['away_score'],
                    'points_against': game['home_score'],
                    'point_differential': game['away_score'] - game['home_score']
                })
            
            game_df = pd.DataFrame(game_records)
            del dim_game_unique, game_records
            gc.collect()
            
            self.logger.info(f"✓ Created {len(game_df):,} game records")
            self.logger.info(f"✓ Cleared dim_game from memory")
            memory_mgr.log_status()
            
            # OPTIMIZATION: Single efficient merge instead of cascading merges
            self.logger.info("📊 Step 4: Merging game records with team stats...")
            memory_mgr.log_status()
            
            df = game_df.merge(team_game_stats, on=['game_id', 'team'], how='left')
            
            # Log DataFrame memory footprint
            df_memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            self.logger.info(f"✓ Merged DataFrame size: {df_memory_mb:.1f}MB ({len(df):,} rows × {len(df.columns)} columns)")
            
            del game_df, team_game_stats
            gc.collect()
            
            memory_mgr.log_status()
            
            # Fill NaN values for games with no plays (shouldn't happen but defensive)
            df['offensive_epa'] = df['offensive_epa'].fillna(0).round(4)
            df['defensive_epa'] = df['defensive_epa'].fillna(0).round(4)
            df['total_plays'] = df['total_plays'].fillna(0)
            df['epa_per_play'] = df['epa_per_play'].fillna(0).round(4)
            
            # Merge with opponent strength data (V2 logic preserved)
            self.logger.info("📊 Step 5: Merging opponent strength data...")
            memory_mgr.log_status()
            
            opponent_strength = team_strength_df[['team', 'season', 'team_strength_overall', 'team_strength_defense']].copy()
            opponent_strength.columns = ['opponent_team', 'season', 'opponent_strength', 'opponent_defense_strength']
            
            # Log opponent strength DataFrame size
            opp_memory_mb = opponent_strength.memory_usage(deep=True).sum() / (1024 * 1024)
            self.logger.info(f"Opponent strength DataFrame: {opp_memory_mb:.1f}MB ({len(opponent_strength):,} rows)")
            
            # Join game performance with opponent strength
            df = df.merge(
                opponent_strength,
                on=['opponent_team', 'season'],
                how='left'
            )
            
            # Log final DataFrame memory footprint
            final_memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            self.logger.info(f"✓ Final merged DataFrame: {final_memory_mb:.1f}MB ({len(df):,} rows × {len(df.columns)} columns)")
            
            del opponent_strength
            gc.collect()
            
            memory_mgr.log_status()
            
            # Fill NaN values for opponent strength
            df['opponent_strength'] = df['opponent_strength'].fillna(0)
            df['opponent_defense_strength'] = df['opponent_defense_strength'].fillna(0)
            
            # Calculate opponent adjustments (V2 sophistication preserved)
            df['strength_adjusted_epa'] = df['epa_per_play'] - df['opponent_defense_strength']
            df['strength_adjusted_points'] = df['point_differential'] / (1 + abs(df['opponent_strength']))
            
            # Quality of opponent indicators
            df['opponent_quality_tier'] = pd.cut(
                df['opponent_strength'],
                bins=[-float('inf'), -0.1, 0.1, float('inf')],
                labels=['weak', 'average', 'strong']
            )
            
            # Sort by team, season, week
            df = df.sort_values(['team', 'season', 'week']).reset_index(drop=True)
            
            self.logger.info("📊 Step 6: Completed game adjustments calculation")
            final_status = memory_mgr.get_status()
            self.logger.info(
                f"✓ Final memory: {final_status['current_usage_mb']:.1f}MB / {final_status['max_memory_mb']}MB "
                f"({final_status['usage_percent']:.1f}% used)"
            )
            self.logger.info(f"✓ Calculated {len(df):,} game adjustments with {len(df.columns)} features")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to calculate game adjustments from bucket: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _aggregate_opponent_adjusted_metrics(self, game_adjustments_df) -> pd.DataFrame:
        """
        Aggregate game-level adjustments to team-season metrics.
        
        Args:
            game_adjustments_df: DataFrame with game-level adjustments
            
        Returns:
            DataFrame with team-season opponent-adjusted metrics
        """
        if game_adjustments_df.empty:
            return pd.DataFrame()
        
        self.logger.debug("Aggregating opponent-adjusted metrics")
        
        # Aggregate by team and season (V2 logic preserved)
        agg_functions = {
            'win': ['sum', 'count', 'mean'],
            'points_for': 'mean',
            'points_against': 'mean',
            'point_differential': 'mean',
            'epa_per_play': 'mean',
            'strength_adjusted_epa': 'mean',
            'strength_adjusted_points': 'mean',
            'opponent_strength': 'mean',
            'opponent_defense_strength': 'mean'
        }
        
        df = game_adjustments_df.groupby(['team', 'season']).agg(agg_functions).reset_index()
        
        # Flatten column names
        df.columns = [f"{col[0]}_{col[1]}" if col[1] else col[0] for col in df.columns]
        df.columns = ['team', 'season'] + [col for col in df.columns if col not in ['team', 'season']]
        
        # Rename and clean columns
        df = df.rename(columns={
            'win_sum': 'wins',
            'win_count': 'games_played', 
            'win_mean': 'win_percentage',
            'points_for_mean': 'avg_points_for',
            'points_against_mean': 'avg_points_against',
            'point_differential_mean': 'avg_point_differential',
            'epa_per_play_mean': 'avg_epa_per_play',
            'strength_adjusted_epa_mean': 'strength_adjusted_epa_avg',
            'strength_adjusted_points_mean': 'strength_adjusted_points_avg',
            'opponent_strength_mean': 'avg_opponent_strength',
            'opponent_defense_strength_mean': 'avg_opponent_defense_strength'
        })
        
        # Calculate quality of wins/losses (V2 sophistication preserved)
        quality_wins = game_adjustments_df[game_adjustments_df['win'] == 1].groupby(['team', 'season']).agg({
            'opponent_strength': ['mean', 'count']
        }).reset_index()
        quality_wins.columns = ['team', 'season', 'quality_wins_avg_opponent', 'total_wins']
        
        quality_losses = game_adjustments_df[game_adjustments_df['win'] == 0].groupby(['team', 'season']).agg({
            'opponent_strength': ['mean', 'count']
        }).reset_index()
        quality_losses.columns = ['team', 'season', 'quality_losses_avg_opponent', 'total_losses']
        
        # Merge quality metrics
        df = df.merge(quality_wins, on=['team', 'season'], how='left')
        df = df.merge(quality_losses, on=['team', 'season'], how='left')
        
        # Performance vs opponent quality tiers
        tier_performance = game_adjustments_df.groupby(['team', 'season', 'opponent_quality_tier']).agg({
            'win': 'mean',
            'epa_per_play': 'mean',
            'point_differential': 'mean'
        }).reset_index()
        
        # Pivot to get performance vs each tier
        for tier in ['weak', 'average', 'strong']:
            tier_data = tier_performance[tier_performance['opponent_quality_tier'] == tier]
            tier_data = tier_data.drop('opponent_quality_tier', axis=1)
            tier_data.columns = ['team', 'season'] + [f'{col}_vs_{tier}' for col in tier_data.columns if col not in ['team', 'season']]
            df = df.merge(tier_data, on=['team', 'season'], how='left')
        
        self.logger.debug(f"Aggregated opponent-adjusted metrics: {len(df)} team-seasons")
        return df
    
    def _add_strength_of_schedule_metrics(self, df, team_strength_df) -> pd.DataFrame:
        """
        Add comprehensive strength-of-schedule metrics (V2 logic preserved).
        
        Args:
            df: DataFrame with opponent-adjusted metrics
            team_strength_df: DataFrame with team strength data
            
        Returns:
            DataFrame with strength-of-schedule metrics added
        """
        if df.empty:
            return df
        
        self.logger.debug("Adding strength-of-schedule metrics")
        
        # Calculate league averages by season for normalization
        league_averages = team_strength_df.groupby('season').agg({
            'team_strength_overall': 'mean',
            'team_strength_offense': 'mean', 
            'team_strength_defense': 'mean'
        }).reset_index()
        
        league_averages.columns = ['season', 'league_avg_strength', 'league_avg_offense', 'league_avg_defense']
        
        # Merge league averages
        df = df.merge(league_averages, on='season', how='left')
        
        # Strength of schedule calculations (V2 sophistication preserved)
        df['strength_of_schedule'] = df['avg_opponent_strength'] - df['league_avg_strength']
        df['strength_of_schedule_defense'] = df['avg_opponent_defense_strength'] - df['league_avg_defense']
        
        # Performance relative to schedule difficulty
        df['performance_vs_schedule'] = df['strength_adjusted_epa_avg'] / (1 + abs(df['strength_of_schedule']))
        df['wins_vs_schedule_difficulty'] = df['win_percentage'] - (0.5 + df['strength_of_schedule'])
        
        # Schedule-adjusted efficiency rankings would require comparing across all teams
        # For now, add relative schedule strength metrics
        df['schedule_difficulty_percentile'] = df.groupby('season')['strength_of_schedule'].rank(pct=True)
        df['opponent_defense_difficulty_percentile'] = df.groupby('season')['strength_of_schedule_defense'].rank(pct=True)
        
        # Clean up temporary columns
        df = df.drop(['league_avg_strength', 'league_avg_offense', 'league_avg_defense'], axis=1)
        
        self.logger.debug(f"Added strength-of-schedule metrics: {len(df.columns)} total columns")
        return df

    def _validate_seasons_with_schedule_data(self, seasons=None) -> tuple[List[int], List]:
        """
        Validate seasons against available CommonV2 schedule data.
        
        MEMORY OBSERVABILITY: Tracks memory during schedule data loading.
        ✅ PERFORMANCE FIX: Returns schedule data to avoid re-loading
        
        Args:
            seasons: List of seasons to validate
            
        Returns:
            Tuple of (validated_seasons, all_schedule_games)
        """
        from commonv2.utils.memory.manager import create_memory_manager
        
        try:
            # Initialize memory manager
            memory_mgr = create_memory_manager(logger=self.logger)
            self.logger.info("🔍 Validating seasons with schedule data...")
            memory_mgr.log_status()
            
            if not seasons:
                # If no seasons specified, get available seasons from schedule provider
                # For now, default to current season
                from datetime import datetime
                current_year = datetime.now().year
                seasons = [current_year if datetime.now().month >= 9 else current_year - 1]
            
            if not isinstance(seasons, (list, tuple)):
                seasons = [seasons]
            
            validated_seasons = []
            all_games = []
            
            # ✅ PERFORMANCE FIX: Load full schedule data once during validation
            # This eliminates duplicate loading in _add_schedule_context_features
            for season in seasons:
                try:
                    # Load complete schedule data for the season (not just week 1)
                    self.logger.info(f"📊 Loading schedule data for season {season}...")
                    season_games = self.schedule_provider.load_schedule([season])
                    
                    if season_games:  # If we get games, season has data
                        validated_seasons.append(season)
                        all_games.extend(season_games)
                        self.logger.info(f"✓ Season {season} validated: {len(season_games)} total games")
                    else:
                        self.logger.warning(f"No schedule data available for season {season}")
                except Exception as e:
                    self.logger.warning(f"Failed to validate season {season}: {e}")
            
            self.logger.info(f"✓ Validated {len(validated_seasons)} seasons: {validated_seasons}")
            self.logger.info(f"✓ Loaded {len(all_games)} total games (reusing for context features)")
            memory_mgr.log_status()
            
            return validated_seasons, all_games
            
        except Exception as e:
            self.logger.error(f"Failed to validate seasons: {e}")
            return [], []
    
    def _add_schedule_context_features(self, df: pd.DataFrame, seasons: List[int],
                                       all_games: Optional[List] = None) -> pd.DataFrame:
        """
        Add schedule context features using CommonV2 integration.
        
        ✅ PERFORMANCE FIX: Accepts pre-loaded schedule data to avoid re-fetching
        
        Args:
            df: DataFrame with opponent-adjusted features
            seasons: List of validated seasons
            all_games: Optional pre-loaded schedule games (from validation step)
            
        Returns:
            DataFrame with enhanced schedule context features
        """
        if df.empty:
            return df
        
        try:
            self.logger.debug("Adding schedule context features")
            
            # ✅ PERFORMANCE FIX: Use pre-loaded schedule data if available
            if all_games is None:
                # Fallback: Load schedule data if not provided (backward compatibility)
                self.logger.debug("Schedule data not pre-loaded, loading now...")
                all_games = []
                for season in seasons:
                    try:
                        season_games = self.schedule_provider.load_schedule([season])
                        all_games.extend(season_games)
                    except Exception as e:
                        self.logger.warning(f"Failed to load schedule for season {season}: {e}")
            else:
                self.logger.debug(f"✓ Reusing pre-loaded schedule data ({len(all_games)} games)")
            
            if not all_games:
                self.logger.warning("No schedule data available for context features")
                return df
            
            # Convert schedule games to DataFrame for analysis
            schedule_data = []
            for game in all_games:
                schedule_data.append({
                    'game_id': game.game_id,
                    'season': game.season,
                    'week': game.week,
                    'home_team': game.home_team,
                    'away_team': game.away_team,
                    'stadium': game.stadium
                })
            
            schedule_df = pd.DataFrame(schedule_data)
            
            if schedule_df.empty:
                return df
            
            # Calculate schedule context metrics
            for season in seasons:
                season_schedule = schedule_df[schedule_df['season'] == season]
                
                if season_schedule.empty:
                    continue
                
                # Calculate division game frequency
                division_game_counts = self._calculate_division_game_frequency(season_schedule)
                
                # Calculate venue diversity
                venue_diversity = self._calculate_venue_diversity(season_schedule)
                
                # Merge schedule context back to main DataFrame
                season_mask = df['season'] == season
                
                for team in df[season_mask]['team'].unique():
                    team_mask = season_mask & (df['team'] == team)
                    
                    # Add division game frequency
                    if team in division_game_counts:
                        df.loc[team_mask, 'division_game_frequency'] = division_game_counts[team]
                    
                    # Add venue diversity
                    if team in venue_diversity:
                        df.loc[team_mask, 'venue_diversity'] = venue_diversity[team]
            
            # Fill missing values with defaults
            df['division_game_frequency'] = df['division_game_frequency'].fillna(0.0)
            df['venue_diversity'] = df['venue_diversity'].fillna(0.5)
            
            self.logger.debug(f"Added schedule context features: {len(df.columns)} total columns")
            return df
            
        except Exception as e:
            self.logger.warning("=" * 80)
            self.logger.warning("⚠️  SCHEDULE CONTEXT FEATURES FAILED")
            self.logger.warning("=" * 80)
            self.logger.warning(f"Error: {e}")
            self.logger.warning("\nAFFECTED FEATURES:")
            self.logger.warning("  - division_game_frequency (likely cause)")
            self.logger.warning("  - venue_diversity")
            self.logger.warning("\nIMPACT:")
            self.logger.warning("  These columns will be MISSING from opponent_adjusted features")
            self.logger.warning("  Models may fail if expecting these features")
            self.logger.warning("\nROOT CAUSE:")
            self.logger.warning("  _calculate_division_game_frequency() returns empty dict")
            self.logger.warning("  See function docstring for implementation requirements")
            self.logger.warning("=" * 80)
            return df
    
    def _calculate_division_game_frequency(self, schedule_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate division game frequency for each team.
        
        ❌ NOT IMPLEMENTED - Returns empty dict (all teams get 0.0)
        
        REASON FOR FAILURE:
        - Requires team→division mapping (AFC East, NFC West, etc.)
        - Division data not available in current schedule data
        - Feature column populated with default value (0.0) via fillna()
        
        IMPACT:
        - All teams show 0.0 division_game_frequency
        - Model cannot learn division rivalry effects
        - Feature provides NO predictive value
        
        TODO - Implementation Requirements:
        1. Add division/conference mapping to commonv2.domain.teams:
           ```python
           TEAM_DIVISIONS = {
               'BUF': 'AFC East', 'MIA': 'AFC East', 'NE': 'AFC East', 'NYJ': 'AFC East',
               'BAL': 'AFC North', 'CIN': 'AFC North', 'CLE': 'AFC North', 'PIT': 'AFC North',
               # ... etc
           }
           ```
        2. Implement division game detection:
           ```python
           for team in schedule_df['home_team'].unique():
               team_games = schedule_df[(schedule_df['home_team'] == team) |
                                       (schedule_df['away_team'] == team)]
               division_games = 0
               for _, game in team_games.iterrows():
                   opponent = (game['away_team'] if game['home_team'] == team
                             else game['home_team'])
                   if TEAM_DIVISIONS[team] == TEAM_DIVISIONS[opponent]:
                       division_games += 1
               results[team] = division_games / len(team_games)
           ```
        3. Add validation test ensuring non-zero values for known matchups
        
        ALTERNATIVE: Remove feature entirely to avoid misleading zeros
        
        Args:
            schedule_df: Schedule data with game_id, home_team, away_team
            
        Returns:
            Empty dict - feature will be filled with 0.0 defaults
        """
        self.logger.warning("⚠️  division_game_frequency NOT IMPLEMENTED - returning empty dict")
        self.logger.warning("   All teams will have division_game_frequency = 0.0 (no predictive value)")
        self.logger.warning("   See _calculate_division_game_frequency() docstring for implementation plan")
        return {}
    
    def _calculate_venue_diversity(self, schedule_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate venue diversity for each team."""
        venue_counts = {}
        
        for team in pd.concat([schedule_df['home_team'], schedule_df['away_team']]).unique():
            team_games = schedule_df[
                (schedule_df['home_team'] == team) | (schedule_df['away_team'] == team)
            ]
            
            unique_venues = team_games['stadium'].nunique()
            total_games = len(team_games)
            
            venue_counts[team] = unique_venues / max(total_games, 1)
        
        return venue_counts
    
    def _validate_opponent_features(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate the quality of opponent-adjusted features.
        
        Args:
            df: DataFrame with opponent-adjusted features
            
        Returns:
            ValidationResult with validation status
        """
        # ValidationResult fields: is_valid, errors, warnings, record_count, validation_date
        validation = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            record_count=len(df)
        )
        
        if df.empty:
            validation.add_error("No opponent-adjusted features generated")
            return validation
        
        # Check required columns
        required_columns = ['team', 'season', 'strength_adjusted_epa_avg', 'avg_opponent_strength']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation.add_error(f"Missing required columns: {missing_columns}")
        
        # Check for reasonable value ranges
        if 'win_percentage' in df.columns:
            invalid_win_pct = df[(df['win_percentage'] < 0) | (df['win_percentage'] > 1)]
            if not invalid_win_pct.empty:
                validation.add_error(f"Invalid win percentage values: {len(invalid_win_pct)} rows")
        
        # Check for null values in key metrics
        key_metrics = ['strength_adjusted_epa_avg', 'avg_opponent_strength', 'strength_of_schedule']
        for metric in key_metrics:
            if metric in df.columns:
                null_count = df[metric].isnull().sum()
                if null_count > 0:
                    validation.add_warning(f"Null values in {metric}: {null_count} rows")
        
        # Check team count per season
        teams_per_season = df.groupby('season')['team'].nunique()
        for season, team_count in teams_per_season.items():
            if team_count < 30:  # NFL should have 32 teams
                validation.add_warning(f"Season {season} has only {team_count} teams")
        
        return validation

    def build_opponent_adjusted_features(self, game_id: str, historical_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Build opponent-adjusted features for a specific game.
        
        This method integrates with the real feature builder to provide
        opponent-adjusted metrics for individual game prediction.
        
        Args:
            game_id: Specific game identifier
            historical_data: Historical data context
            
        Returns:
            Dictionary of opponent-adjusted features for the game
        """
        try:
            # Extract game information
            if 'schedules' not in historical_data:
                self.logger.warning("No schedule data available for opponent adjustment")
                return self._get_default_opponent_features()
            
            schedules = historical_data['schedules']
            game_row = schedules[schedules['game_id'] == game_id]
            
            if game_row.empty:
                self.logger.warning(f"Game {game_id} not found in schedule data")
                return self._get_default_opponent_features()
            
            game = game_row.iloc[0]
            home_team = game.get('home_team')
            away_team = game.get('away_team')
            season = game.get('season')
            
            # Get team strength data for the season
            team_strength_df = self._calculate_team_strength([season])
            
            # Calculate opponent-adjusted features for both teams
            features = {}
            
            # Home team opponent adjustments
            home_strength = team_strength_df[team_strength_df['team'] == home_team]
            away_strength = team_strength_df[team_strength_df['team'] == away_team]
            
            if not home_strength.empty and not away_strength.empty:
                home_stats = home_strength.iloc[0]
                away_stats = away_strength.iloc[0]
                
                # Opponent-adjusted metrics
                features['home_strength_vs_away_defense'] = home_stats.get('team_strength_offense', 0.0) - away_stats.get('team_strength_defense', 0.0)
                features['away_strength_vs_home_defense'] = away_stats.get('team_strength_offense', 0.0) - home_stats.get('team_strength_defense', 0.0)
                features['overall_strength_differential'] = home_stats.get('team_strength_overall', 0.0) - away_stats.get('team_strength_overall', 0.0)
                
                # Strength-of-schedule adjustments
                features['home_sos_adjusted_strength'] = home_stats.get('team_strength_overall', 0.0)
                features['away_sos_adjusted_strength'] = away_stats.get('team_strength_overall', 0.0)
            else:
                # Default values if team strength data not available
                features.update(self._get_default_opponent_features())
            
            return features
            
        except Exception as e:
            self.logger.error(f"Failed to build opponent-adjusted features for game {game_id}: {e}")
            return self._get_default_opponent_features()
    
    def _get_default_opponent_features(self) -> Dict[str, float]:
        """Get default opponent-adjusted feature values."""
        return {
            'home_strength_vs_away_defense': 0.0,
            'away_strength_vs_home_defense': 0.0,
            'overall_strength_differential': 0.0,
            'home_sos_adjusted_strength': 0.0,
            'away_sos_adjusted_strength': 0.0
        }


# Convenience function for direct usage
def create_opponent_adjusted_features(db_service=None, logger=None, schedule_provider=None, bucket_adapter=None):
    """
    Create opponent-adjusted features service with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        schedule_provider: Optional CommonV2 schedule provider override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        OpponentAdjustedFeatures: Configured opponent-adjusted features service
    """
    from nflfastRv3.shared.database_router import get_database_router
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.ml_pipeline.opponent_adjusted')
    
    return OpponentAdjustedFeatures(db_service, logger, schedule_provider, bucket_adapter)


__all__ = ['OpponentAdjustedFeatures', 'create_opponent_adjusted_features']
