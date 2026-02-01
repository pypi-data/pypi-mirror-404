"""
Rolling Metrics Features - V3 Implementation

⚠️  MERGE PATTERN WARNING ⚠️
This feature set produces a TEAM-GAME table (2 rows per game_id).

✅ Correct merge pattern:
    # Home team
    df.merge(rolling_metrics,
             left_on=['game_id','season','week','home_team'],
             right_on=['game_id','season','week','team'],
             validate='one_to_one')
    
    # Away team
    df.merge(rolling_metrics,
             left_on=['game_id','season','week','away_team'],
             right_on=['game_id','season','week','team'],
             validate='one_to_one')

❌ INCORRECT (will create duplicates):
    df.merge(rolling_metrics,
             on=['game_id','season','week'])  # Missing team!

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + business logic)
Layer: 2 (Implementation - calls infrastructure directly)

V2 Business Logic Preserved:
- Rolling EPA averages (4, 8, 16 game windows)
- Recent form analysis (last 4 games)
- Momentum indicators (win/loss streaks)
- Performance trending (improving/declining)
- Game-by-game variance metrics
"""

import pandas as pd
from typing import Dict, Any, List, Optional


class RollingMetricsFeatures:
    """
    Rolling metrics feature engineering service.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + time-series calculations)
    Depth: 1 layer (calls database directly)
    
    V2 Capabilities Preserved:
    - Rolling EPA metrics (multiple windows)
    - Recent performance indicators
    - Win/loss streak tracking
    - Variance and consistency metrics
    - Game-by-game momentum analysis
    """
    
    def __init__(self, db_service, logger, bucket_adapter=None):
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
        
        # Rolling window configurations (V2 settings preserved)
        self.rolling_windows = [4, 8, 16]  # 4, 8, 16 game rolling averages
        self.recent_games_window = 4  # Recent form analysis
    
    def build_features(self, seasons=None) -> Dict[str, Any]:
        """
        Build comprehensive rolling metrics features.
        
        Pure computation - orchestrator handles saving (matches model_trainer pattern).
        
        Simple feature engineering flow:
        1. Extract game-by-game team performance (Layer 3 call)
        2. Calculate rolling averages and windows (Layer 3 call)
        3. Add momentum and streak indicators (Layer 3 call)
        4. Calculate variance and consistency metrics (Layer 3 call)
        5. Return DataFrame for orchestrator to save
        
        Args:
            seasons: List of seasons to process (default: all available)
            
        Returns:
            Dictionary with feature build results including DataFrame
        """
        self.logger.info(f"Building rolling metrics features for seasons: {seasons or 'all'}")
        
        try:
            # Step 1: Build game-by-game performance dataset
            df = self._build_game_by_game_dataset(seasons)
            
            if df.empty:
                self.logger.warning("No game-by-game data found")
                return {
                    'status': 'warning',
                    'message': 'No data available',
                    'features_built': 0,
                    'seasons_processed': 0
                }
            
            # Step 2: Calculate rolling metrics (V2 sophistication preserved)
            df = self._add_rolling_metrics(df)
            
            # Step 3: Add momentum and streak indicators
            df = self._add_momentum_indicators(df)
            
            # Step 4: Calculate consistency metrics
            df = self._add_consistency_metrics(df)
            
            # Step 5: Feature quality analysis
            self._log_feature_quality_metrics(df)
            
            # Step 6: Capture metadata and final summary
            seasons_processed = df['season'].nunique() if 'season' in df.columns else 0
            teams_processed = df['team'].nunique() if 'team' in df.columns else 0
            games_processed = len(df)
            feature_columns = len(df.columns)
            
            # FINAL DATA INSPECTION: Show complete transformation summary
            self.logger.info("=" * 80)
            self.logger.info("📊 FINAL TRANSFORMATION SUMMARY")
            self.logger.info("=" * 80)
            self.logger.info(f"✓ Built rolling metrics features: {games_processed:,} team-games across {seasons_processed} seasons and {teams_processed} teams")
            self.logger.info(f"✓ Total feature columns: {feature_columns}")
            
            # Show final data sample (one team, first 10 games)
            sample_team = df['team'].iloc[0]
            final_sample = df[df['team'] == sample_team].head(10)
            self.logger.info(f"\n📊 FINAL DATA SAMPLE - Complete feature set (first 10 rows for {sample_team}):")
            display_cols = ['team', 'season', 'week', 'win', 'epa_per_play_offense',
                          'rolling_4g_epa_offense', 'rolling_8g_epa_offense',
                          'win_loss_streak', 'recent_4g_win_rate',
                          'rolling_4g_epa_offense_std', 'rolling_8g_venue_point_diff']
            self.logger.info(f"\n{final_sample[display_cols].to_string()}")
            
            # Data quality summary
            self.logger.info(f"\n📊 DATA QUALITY SUMMARY:")
            self.logger.info(f"   Total rows: {len(df):,}")
            self.logger.info(f"   Total columns: {len(df.columns)}")
            self.logger.info(f"   Seasons: {sorted(df['season'].unique().tolist())}")
            self.logger.info(f"   Teams: {df['team'].nunique()}")
            self.logger.info(f"   Date range: {df['game_date'].min()} to {df['game_date'].max()}")
            
            # Check for nulls in key feature columns
            key_features = ['rolling_4g_epa_offense', 'rolling_8g_epa_offense', 'rolling_16g_epa_offense',
                          'win_loss_streak', 'recent_4g_win_rate', 'rolling_4g_epa_offense_std']
            null_counts = df[key_features].isnull().sum()
            self.logger.info(f"\n📊 NULL COUNTS in key features:")
            for col, count in null_counts.items():
                pct = (count / len(df)) * 100
                self.logger.info(f"   {col}: {count:,} ({pct:.2f}%)")
            
            # Statistical summary of key metrics
            self.logger.info(f"\n📊 KEY METRICS STATISTICS:")
            self.logger.info(f"   Win rate overall: {df['win'].mean():.3f}")
            self.logger.info(f"   Avg EPA/play offense: {df['epa_per_play_offense'].mean():.4f}")
            self.logger.info(f"   Avg rolling_4g EPA offense: {df['rolling_4g_epa_offense'].mean():.4f}")
            self.logger.info(f"   Avg rolling_8g EPA offense: {df['rolling_8g_epa_offense'].mean():.4f}")
            self.logger.info(f"   Avg win streak magnitude: {df['win_loss_streak'].abs().mean():.2f}")
            
            self.logger.info("=" * 80)
            
            # Return DataFrame for orchestrator to handle saving
            return {
                'status': 'success',
                'dataframe': df,  # ✅ Orchestrator will save this
                'features_built': games_processed,
                'seasons_processed': seasons_processed,
                'teams_processed': teams_processed,
                'feature_columns': feature_columns
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build rolling metrics features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }
    
    def _build_game_by_game_dataset(self, seasons=None) -> pd.DataFrame:
        """
        Build game-by-game performance dataset from bucket warehouse tables.
        
        MEMORY OBSERVABILITY: Tracks memory usage during data loading and processing.
        
        Bucket-first approach - reads from warehouse/fact_play and warehouse/dim_game
        Preserves V2 business logic using pandas operations
        
        Args:
            seasons: List of seasons to process
            
        Returns:
            DataFrame with game-by-game team performance
        """
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        from commonv2.utils.memory.manager import create_memory_manager
        import gc
        
        # Define minimal column sets needed for rolling metrics calculations
        FACT_PLAY_COLUMNS = [
            # Identifiers
            'game_id', 'season', 'posteam', 'defteam',
            
            # Play characteristics
            'play_type', 'play_id',
            
            # Performance metrics
            'epa', 'yards_gained',
            
            # Situational
            'down', 'ydstogo', 'yardline_100', 'score_differential',
            
            # Outcomes
            'touchdown', 'interception', 'fumble_lost',
            
            # Play types
            'rush_attempt', 'pass_attempt', 'third_down_converted'
        ]
        
        DIM_GAME_COLUMNS = [
            'game_id', 'season', 'week', 'game_date',
            'home_team', 'away_team', 'home_score', 'away_score',
            'roof', 'surface'
        ]
        
        try:
            # Initialize memory manager for observability
            memory_mgr = create_memory_manager(logger=self.logger)
            self.logger.info("🔍 Starting rolling metrics calculation...")
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
            
            #Log count before transformation
            self.logger.info(f"Rows in dim_game before drop_duplicates: {len(dim_game)}")

            # dim_game is play by play data (need game level data before merge)
            dim_game_unique = dim_game.drop_duplicates(subset=['game_id'], keep='first')
            
            #Log count after transformation
            self.logger.info(f"Rows in dim_game_unique after drop_duplicates: {len(dim_game_unique)}")

            # Log loaded data sizes
            fact_play_mb = fact_play.memory_usage(deep=True).sum() / (1024 * 1024)
            dim_game_mb = dim_game_unique.memory_usage(deep=True).sum() / (1024 * 1024)
            self.logger.info(f"✓ Loaded fact_play: {len(fact_play):,} rows, {len(fact_play.columns)} cols, {fact_play_mb:.1f}MB")
            self.logger.info(f"✓ Loaded dim_game: {len(dim_game_unique):,} rows, {len(dim_game_unique.columns)} cols, {dim_game_mb:.1f}MB")
            
            # DATA SUMMARY: Loaded data statistics
            self.logger.info(f"📊 fact_play: {len(fact_play):,} rows × {len(fact_play.columns)} cols")
            self.logger.info(f"📊 EPA Statistics: min={fact_play['epa'].min():.4f}, max={fact_play['epa'].max():.4f}, mean={fact_play['epa'].mean():.4f}, median={fact_play['epa'].median():.4f}")
            self.logger.info(f"📊 Null counts in fact_play: {fact_play[['epa', 'posteam', 'defteam', 'play_type']].isnull().sum().to_dict()}")
            
            self.logger.info(f"📊 dim_game: {len(dim_game_unique):,} rows × {len(dim_game_unique.columns)} cols")
            self.logger.info(f"📊 Score Statistics: home_score mean={dim_game_unique['home_score'].mean():.1f}, away_score mean={dim_game_unique['away_score'].mean():.1f}")
            self.logger.info("   See feature report for detailed data samples")
            
            memory_mgr.log_status()
            
            if fact_play.empty or dim_game_unique.empty:
                self.logger.warning("No warehouse data found in bucket")
                return pd.DataFrame()
            
            # Filter for valid plays
            self.logger.info(f"📊 Filtering for valid plays... (before: {len(fact_play):,} rows)")
            fact_play_valid = fact_play[
                (fact_play['play_type'].isin(['pass', 'run'])) &
                (fact_play['epa'].notna())
            ].copy()
            
            # Delete unfiltered fact_play
            del fact_play
            gc.collect()
            
            fact_play = fact_play_valid
            del fact_play_valid
            
            self.logger.info(f"✓ Filtered to valid plays (after: {len(fact_play):,} rows)")
            memory_mgr.log_status()
            
            # Calculate play-by-play stats per game per team (simpler approach)
            self.logger.info(f"📊 Creating game performance records from dim_game ({len(dim_game_unique):,} rows)...")
            memory_mgr.log_status()
            
            # Create home team game performance
            home_games = dim_game_unique[['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team',
                                   'home_score', 'away_score', 'roof', 'surface']].copy()
            self.logger.info(f"   Created home_games: {len(home_games):,} rows")
            home_games['team'] = home_games['home_team']
            home_games['venue'] = 'home'
            home_games['points_for'] = home_games['home_score']
            home_games['points_against'] = home_games['away_score']
            home_games['win'] = (home_games['home_score'] > home_games['away_score']).astype(int)
            home_games['point_differential'] = home_games['home_score'] - home_games['away_score']
            home_games['outdoor_game'] = (home_games['roof'] == 'outdoors').astype(int)
            home_games['grass_surface'] = (home_games['surface'] == 'grass').astype(int)
            
            # Add simple venue indicator flags (deterministic, no temporal leakage)
            home_games['is_home'] = 1
            home_games['is_neutral_site'] = 0
            home_games['venue_flag'] = 1  # +1 for home
            
            # Create away team game performance
            away_games = dim_game_unique[['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team',
                                   'home_score', 'away_score', 'roof', 'surface']].copy()
            self.logger.info(f"   Created away_games: {len(away_games):,} rows")
            away_games['team'] = away_games['away_team']
            away_games['venue'] = 'away'
            away_games['points_for'] = away_games['away_score']
            away_games['points_against'] = away_games['home_score']
            away_games['win'] = (away_games['away_score'] > away_games['home_score']).astype(int)
            away_games['point_differential'] = away_games['away_score'] - away_games['home_score']
            away_games['outdoor_game'] = (away_games['roof'] == 'outdoors').astype(int)
            away_games['grass_surface'] = (away_games['surface'] == 'grass').astype(int)
            
            # Add simple venue indicator flags (deterministic, no temporal leakage)
            away_games['is_home'] = 0
            away_games['is_neutral_site'] = 0
            away_games['venue_flag'] = -1  # -1 for away
            
            # Combine home and away games
            self.logger.info(f"   Combining home ({len(home_games):,}) + away ({len(away_games):,}) games...")
            all_games = pd.concat([home_games, away_games], ignore_index=True)
            
            # Clear intermediate DataFrames
            del home_games, away_games
            gc.collect()
            
            self.logger.info(f"✓ Created all_games: {len(all_games):,} game records (unique game_ids: {all_games['game_id'].nunique():,})")
            memory_mgr.log_status()
            
            # FAST: Vectorized groupby operations (~10 seconds)
            self.logger.info(f"📊 Calculating play-by-play statistics using vectorized operations...")
            
            # Validate required columns exist
            required_cols = ['epa', 'interception', 'fumble_lost', 'touchdown', 'third_down_converted', 'yardline_100', 'down']
            missing = [c for c in required_cols if c not in fact_play.columns]
            if missing:
                self.logger.warning(f"Missing columns for vectorized aggregation: {missing}")
            
            # Offensive stats (grouped by game_id + posteam)
            offense_stats = fact_play.groupby(['game_id', 'posteam'], observed=True).agg({
                'epa': ['sum', 'count'],
                'play_id': 'count',
                'interception': lambda x: (x.fillna(0) == 1).sum(),
                'fumble_lost': lambda x: (x.fillna(0) == 1).sum(),
            }).reset_index()
            
            offense_stats.columns = ['game_id', 'team', 'offensive_epa', 'epa_count',
                                     'total_plays_offense', 'interceptions', 'fumbles_lost']
            offense_stats['turnovers_lost'] = offense_stats['interceptions'] + offense_stats['fumbles_lost']
            
            # Red zone stats
            red_zone_stats = fact_play[fact_play['yardline_100'] <= 20].groupby(
                ['game_id', 'posteam'], observed=True
            ).agg({
                'play_id': 'count',
                'touchdown': lambda x: (x.fillna(0) == 1).sum()
            }).reset_index()
            red_zone_stats.columns = ['game_id', 'team', 'red_zone_attempts', 'red_zone_scores']
            
            # Third down stats
            third_down_stats = fact_play[fact_play['down'] == 3].groupby(
                ['game_id', 'posteam'], observed=True
            ).agg({
                'play_id': 'count',
                'third_down_converted': lambda x: (x.fillna(0) == 1).sum()
            }).reset_index()
            third_down_stats.columns = ['game_id', 'team', 'third_down_attempts', 'third_down_conversions']
            
            # Defensive stats (grouped by game_id + defteam)
            defense_stats = fact_play.groupby(['game_id', 'defteam'], observed=True).agg({
                'epa': 'sum',
                'play_id': 'count',
                'interception': lambda x: (x.fillna(0) == 1).sum(),
                'fumble_lost': lambda x: (x.fillna(0) == 1).sum(),
            }).reset_index()
            defense_stats.columns = ['game_id', 'team', 'defensive_epa', 'total_plays_defense',
                                     'interceptions_forced', 'fumbles_forced']
            defense_stats['turnovers_forced'] = defense_stats['interceptions_forced'] + defense_stats['fumbles_forced']
            
            # Merge all stats
            play_stats_df = offense_stats.merge(
                red_zone_stats, on=['game_id', 'team'], how='left'
            ).merge(
                third_down_stats, on=['game_id', 'team'], how='left'
            ).merge(
                defense_stats[['game_id', 'team', 'defensive_epa', 'total_plays_defense', 'turnovers_forced']],
                on=['game_id', 'team'], how='left'
            )
            
            # Fill NaN values
            play_stats_df = play_stats_df.fillna(0)
            
            # Drop intermediate columns
            play_stats_df = play_stats_df.drop(['interceptions', 'fumbles_lost', 'epa_count'], axis=1, errors='ignore')
            
            # ========================================================================
            # CRITICAL: Detect row count mismatch BEFORE merge (diagnose data quality)
            # ========================================================================
            expected_rows = all_games['game_id'].nunique() * 2  # 2 teams per game
            actual_rows = len(play_stats_df)
            play_stats_counts = play_stats_df.groupby(['game_id', 'team']).size()
            unique_pairs = len(play_stats_counts)
            
            if actual_rows != expected_rows:
                self.logger.warning("=" * 80)
                self.logger.warning("⚠️  ROW COUNT MISMATCH: play_stats_df")
                self.logger.warning("=" * 80)
                self.logger.warning(f"   Expected: {expected_rows:,} rows (2 teams × {all_games['game_id'].nunique()} games)")
                self.logger.warning(f"   Got: {actual_rows:,} rows")
                self.logger.warning(f"   Unique (game_id, team) pairs: {unique_pairs:,}")
                self.logger.warning(f"   EXTRA ROWS: {actual_rows - expected_rows:,}")
                
                # Analyze duplicate (game_id, team) pairs
                duplicates = play_stats_counts[play_stats_counts > 1]
                if len(duplicates) > 0:
                    self.logger.warning(f"\n   🔍 DUPLICATES FOUND: {len(duplicates)} (game_id, team) pairs appear multiple times")
                    self.logger.warning(f"   Sample duplicate counts: {dict(list(duplicates.head(10).items()))}")
                    
                    # Show detailed example of first duplicate
                    sample_dup = duplicates.index[0]
                    sample_rows = play_stats_df[
                        (play_stats_df['game_id'] == sample_dup[0]) &
                        (play_stats_df['team'] == sample_dup[1])
                    ]
                    self.logger.warning(f"\n   EXAMPLE DUPLICATE: {sample_dup}")
                    self.logger.warning(f"   {len(sample_rows)} rows for this (game_id, team):")
                    self.logger.warning(f"\n{sample_rows.to_string()}")
                    
                    # Identify which columns differ between duplicates
                    diff_cols = []
                    for col in sample_rows.columns:
                        if sample_rows[col].nunique() > 1:
                            diff_cols.append(col)
                    if diff_cols:
                        self.logger.warning(f"\n   Columns with different values: {diff_cols}")
                    else:
                        self.logger.warning(f"\n   All columns identical (pure duplicates)")
                else:
                    # No duplicates - extra rows must be from game_ids not in all_games
                    play_game_ids = set(play_stats_df['game_id'].unique())
                    all_game_ids = set(all_games['game_id'].unique())
                    extra_games = play_game_ids - all_game_ids
                    if extra_games:
                        self.logger.warning(f"\n   Found {len(extra_games)} game_ids in play_stats_df but NOT in all_games:")
                        self.logger.warning(f"   Sample: {list(extra_games)[:5]}")
                
                self.logger.warning(f"\n   ⚠️  DATA LOSS WARNING:")
                self.logger.warning(f"   Upcoming merge (all_games LEFT JOIN play_stats_df) will:")
                self.logger.warning(f"   - Keep only {expected_rows:,} rows from all_games")
                self.logger.warning(f"   - Discard {actual_rows - unique_pairs:,} duplicate rows")
                self.logger.warning(f"   - May lose valid stats if duplicates contain different data")
                self.logger.warning(f"\n   ROOT CAUSE: Likely fact_play aggregation issue")
                self.logger.warning(f"   - Check for data quality issues in fact_play table")
                self.logger.warning(f"   - Investigate why groupby(['game_id', 'posteam/defteam']) creates duplicates")
                self.logger.warning("=" * 80)
            
            # CRITICAL: Check for and remove duplicates in play_stats_df
            # (This may not trigger if merge does the filtering, but kept for defensive programming)
            before_dedup = len(play_stats_df)
            play_stats_dupes = play_stats_df.groupby(['game_id', 'team']).size()
            play_stats_dupes = play_stats_dupes[play_stats_dupes > 1]
            
            if len(play_stats_dupes) > 0:
                self.logger.warning("=" * 80)
                self.logger.warning("⚠️  DUPLICATE DETECTION: play_stats_df")
                self.logger.warning("=" * 80)
                self.logger.warning(f"   Found {len(play_stats_dupes)} (game_id, team) pairs with multiple rows")
                self.logger.warning(f"   Before deduplication: {before_dedup:,} rows")
                self.logger.warning(f"   Sample duplicates (showing counts): {dict(list(play_stats_dupes.head().items()))}")
                
                # Show detailed sample of one duplicate to understand structure
                sample_dup = play_stats_dupes.index[0]
                sample_rows = play_stats_df[(play_stats_df['game_id'] == sample_dup[0]) & (play_stats_df['team'] == sample_dup[1])]
                self.logger.warning(f"\n   EXAMPLE DUPLICATE ROWS for {sample_dup}:")
                self.logger.warning(f"\n{sample_rows.to_string()}")
                
                # Analyze which columns differ between duplicates
                if len(sample_rows) > 1:
                    diff_cols = []
                    for col in sample_rows.columns:
                        if sample_rows[col].nunique() > 1:
                            diff_cols.append(col)
                    self.logger.warning(f"\n   Columns with differing values: {diff_cols}")
                
                # ⚠️ POTENTIAL DATA LOSS: Keeping first occurrence may discard valid data
                # TODO: Investigate root cause - likely issue in fact_play aggregation
                # Better solution: Aggregate duplicates (sum offensive_epa, mean epa_per_play, etc.)
                self.logger.warning("\n   ⚠️  ACTION: Dropping duplicates (keeping first) - may lose data!")
                self.logger.warning("   RECOMMENDATION: Investigate fact_play for data quality issues")
                
                # Deduplicate by keeping first occurrence
                play_stats_df = play_stats_df.drop_duplicates(subset=['game_id', 'team'], keep='first')
                self.logger.warning(f"   ✓ After deduplication: {len(play_stats_df):,} rows (removed {before_dedup - len(play_stats_df):,} duplicates)")
                self.logger.warning("=" * 80)
            
            # Validate result row count
            unique_games = all_games['game_id'].nunique()
            expected_rows = unique_games * 2  # 2 teams per game
            if len(play_stats_df) != expected_rows:
                self.logger.warning(f"Expected {expected_rows} rows (2 teams × {unique_games} games), got {len(play_stats_df)}")
            
            self.logger.info(f"   Created play_stats_df: {len(play_stats_df):,} rows (vectorized)")
            
            # DATA SUMMARY: Aggregated play stats
            self.logger.info(f"📊 Offensive EPA: min={play_stats_df['offensive_epa'].min():.4f}, max={play_stats_df['offensive_epa'].max():.4f}, mean={play_stats_df['offensive_epa'].mean():.4f}")
            self.logger.info(f"📊 Defensive EPA: min={play_stats_df['defensive_epa'].min():.4f}, max={play_stats_df['defensive_epa'].max():.4f}, mean={play_stats_df['defensive_epa'].mean():.4f}")
            self.logger.info(f"📊 Null counts: {play_stats_df[['offensive_epa', 'defensive_epa', 'turnovers_lost', 'turnovers_forced']].isnull().sum().to_dict()}")
            
            # Clear fact_play, dim_game from memory (no longer needed)
            del fact_play, dim_game, dim_game_unique
            gc.collect()
            
            self.logger.info(f"✓ Calculated stats for {len(play_stats_df):,} team-games")
            self.logger.info("✓ Freed fact_play and dim_game from memory")
            memory_mgr.log_status()
            
            # Merge game info with play stats
            self.logger.info(f"📊 Merging all_games ({len(all_games):,}) with play_stats_df ({len(play_stats_df):,})...")
            df = all_games.merge(play_stats_df, on=['game_id', 'team'], how='left')
            self.logger.info(f"   After merge: {len(df):,} rows (unique game_id+team: {df.groupby(['game_id', 'team']).size().shape[0]:,})")
            
            # CRITICAL: Check for duplicates after merge and remove them
            before_dedup = len(df)
            merge_dupes = df.groupby(['game_id', 'team']).size()
            merge_dupes = merge_dupes[merge_dupes > 1]
            
            if len(merge_dupes) > 0:
                self.logger.warning("=" * 80)
                self.logger.warning("⚠️  DUPLICATE DETECTION: Final merged dataset")
                self.logger.warning("=" * 80)
                self.logger.warning(f"   Found {len(merge_dupes)} (game_id, team) pairs with multiple rows after merge")
                self.logger.warning(f"   Before deduplication: {before_dedup:,} rows")
                self.logger.warning(f"   Sample duplicates (showing counts): {dict(list(merge_dupes.head().items()))}")
                
                # Show detailed sample
                sample_dup = merge_dupes.index[0]
                sample_rows = df[(df['game_id'] == sample_dup[0]) & (df['team'] == sample_dup[1])]
                self.logger.warning(f"\n   EXAMPLE DUPLICATE ROWS for {sample_dup}:")
                self.logger.warning(f"\n{sample_rows[['game_id', 'team', 'week', 'points_for', 'offensive_epa', 'total_plays_offense']].to_string()}")
                
                # ⚠️ POTENTIAL DATA LOSS
                self.logger.warning("\n   ⚠️  ACTION: Dropping duplicates (keeping first) - may lose data!")
                self.logger.warning("   CAUSE: Likely cartesian product from all_games + play_stats_df merge")
                
                # Deduplicate by keeping first occurrence
                df = df.drop_duplicates(subset=['game_id', 'team'], keep='first')
                self.logger.warning(f"   ✓ After deduplication: {len(df):,} rows (removed {before_dedup - len(df):,} duplicates)")
                self.logger.warning("=" * 80)
            
            # Clear intermediate DataFrames
            del all_games, play_stats_df
            gc.collect()
            
            self.logger.info(f"✓ Merged game data: {len(df):,} team-games")
            memory_mgr.log_status()
            
            # Fill NaN values with 0 for stats
            stat_cols = ['offensive_epa', 'defensive_epa', 'total_plays_offense', 'total_plays_defense',
                        'turnovers_lost', 'turnovers_forced', 'red_zone_attempts', 'red_zone_scores',
                        'third_down_attempts', 'third_down_conversions']
            df[stat_cols] = df[stat_cols].fillna(0)
            
            # Calculate efficiency metrics (V2 logic preserved)
            # NOTE: These are per-game efficiency metrics calculated from completed games.
            # They are STORED in rolling_metrics_v1 as historical values.
            # Valid for backtesting/research (using completed game data).
            # For real-time predictions, models should use rolling averages instead
            # (e.g., rolling_4g_epa_offense) since you don't know these values before the game.
            df['epa_per_play_offense'] = (df['offensive_epa'] / df['total_plays_offense'].replace(0, 1)).round(4)
            df['epa_per_play_defense'] = (df['defensive_epa'] / df['total_plays_defense'].replace(0, 1)).round(4)
            df['red_zone_efficiency'] = (df['red_zone_scores'] / df['red_zone_attempts'].replace(0, 1)).round(4)
            df['third_down_efficiency'] = (df['third_down_conversions'] / df['third_down_attempts'].replace(0, 1)).round(4)
            df['turnover_differential'] = df['turnovers_forced'] - df['turnovers_lost']
            
            # Round numeric columns
            df['offensive_epa'] = df['offensive_epa'].round(4)
            df['defensive_epa'] = df['defensive_epa'].round(4)
            
            # Convert game_date to datetime for proper sorting
            df['game_date'] = pd.to_datetime(df['game_date'])
            
            # Sort by team and chronological order for rolling calculations
            self.logger.info(f"   Sorting data: {len(df):,} rows")
            df = df.sort_values(['team', 'season', 'week']).reset_index(drop=True)
            
            # DATA SUMMARY: Base metrics statistics
            self.logger.info(f"📊 Base metrics statistics:")
            self.logger.info(f"   EPA/play offense: min={df['epa_per_play_offense'].min():.4f}, max={df['epa_per_play_offense'].max():.4f}, mean={df['epa_per_play_offense'].mean():.4f}")
            self.logger.info(f"   EPA/play defense: min={df['epa_per_play_defense'].min():.4f}, max={df['epa_per_play_defense'].max():.4f}, mean={df['epa_per_play_defense'].mean():.4f}")
            self.logger.info(f"   Points for: min={df['points_for'].min():.1f}, max={df['points_for'].max():.1f}, mean={df['points_for'].mean():.1f}")
            self.logger.info(f"   Win rate: {df['win'].mean():.3f}")
            
            # Validate the feature data (V2 validation preserved)
            required_columns = ['team', 'season', 'week', 'game_date', 'win', 'epa_per_play_offense']
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                self.logger.error(f"Missing required columns in game performance data: {missing_cols}")
                return pd.DataFrame()
            
            # Final memory status
            final_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            final_status = memory_mgr.get_status()
            self.logger.info(
                f"✓ Rolling metrics calculation complete: {len(df):,} team-games, "
                f"{len(df.columns)} columns, {final_mb:.1f}MB"
            )
            self.logger.info(
                f"✓ Final memory: {final_status['current_usage_mb']:.1f}MB / {final_status['max_memory_mb']}MB "
                f"({final_status['usage_percent']:.1f}% used)"
            )
            
            # CRITICAL VALIDATION: Ensure uniqueness (team-game table contract)
            # After all deduplication logic, each (game_id, team) pair must be unique
            duplicate_check = df.groupby(['game_id', 'team']).size()
            max_count = duplicate_check.max()
            
            if max_count > 1:
                duplicate_pairs = duplicate_check[duplicate_check > 1]
                raise ValueError(
                    f"FATAL: Team-game table contains {len(duplicate_pairs)} duplicate (game_id, team) pairs after deduplication. "
                    f"This violates the data contract and will cause incorrect predictions. "
                    f"Sample duplicates: {dict(list(duplicate_pairs.head().items()))}. "
                    f"This indicates a data quality issue in fact_play or dim_game that must be resolved."
                )
            
            self.logger.info(f"✓ Validated uniqueness: {df['game_id'].nunique():,} games × 2 teams = {len(df):,} rows")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to extract game-by-game data from bucket: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _add_rolling_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add rolling metrics across multiple time windows (V2 logic preserved).
        
        Args:
            df: DataFrame with game-by-game performance
            
        Returns:
            DataFrame with rolling metrics added
        """
        if df.empty:
            return df
        
        self.logger.info(f"📊 Adding rolling metrics (input: {len(df):,} rows, {len(df.columns)} cols)")
        
        # Group by team AND season to prevent cross-season contamination
        # Use .transform() with .shift(1) to exclude current game from rolling window (prevent temporal leakage)
        # .transform() automatically maintains proper index alignment
        # Import shrinkage utility
        from nflfastRv3.features.ml_pipeline.utils.features.shrinkage import apply_shrinkage, get_league_prior
        
        # Calculate games played so far (for shrinkage)
        # shift(1) because we only know games played BEFORE the current game
        df['games_played_prior'] = df.groupby(['team', 'season']).cumcount()
        
        for window in self.rolling_windows:
            self.logger.info(f"🔄 Calculating {window}-game rolling window with proper index alignment...")
            
            # Use transform() to maintain index alignment - this is the key fix
            # Apply shrinkage to stabilize early-season metrics
            
            # Helper to apply rolling + shift + shrinkage
            def _rolling_shrunk(series, metric_name):
                # 1. Calculate rolling mean (shifted)
                rolling_val = series.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
                
                # 2. Get prior for this metric
                prior = get_league_prior(f'rolling_{window}g_{metric_name}')
                if prior == 0.0:
                    # Fallback to base metric prior if window-specific not found
                    prior = get_league_prior(metric_name)
                
                # 3. Apply shrinkage based on sample size (games played)
                # Note: We use 'games_played_prior' which is already available in the outer scope
                # But inside transform we need to align it.
                # Simpler approach: Calculate rolling first, then apply shrinkage column-wise after
                return rolling_val

            # 1. Calculate raw rolling metrics first
            df[f'rolling_{window}g_epa_offense'] = df.groupby(['team', 'season'])['epa_per_play_offense'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
            )
            df[f'rolling_{window}g_epa_defense'] = df.groupby(['team', 'season'])['epa_per_play_defense'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
            )
            df[f'rolling_{window}g_points_for'] = df.groupby(['team', 'season'])['points_for'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
            )
            df[f'rolling_{window}g_points_against'] = df.groupby(['team', 'season'])['points_against'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
            )
            df[f'rolling_{window}g_point_diff'] = df.groupby(['team', 'season'])['point_differential'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
            )
            df[f'rolling_{window}g_win_rate'] = df.groupby(['team', 'season'])['win'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
            )
            df[f'rolling_{window}g_turnover_diff'] = df.groupby(['team', 'season'])['turnover_differential'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
            )
            df[f'rolling_{window}g_red_zone_eff'] = df.groupby(['team', 'season'])['red_zone_efficiency'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
            )
            df[f'rolling_{window}g_third_down_eff'] = df.groupby(['team', 'season'])['third_down_efficiency'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
            )
            
            # 2. Apply shrinkage to key metrics
            # Only apply to EPA and Win Rate for now as they are most sensitive
            metrics_to_shrink = [
                f'rolling_{window}g_epa_offense',
                f'rolling_{window}g_epa_defense',
                f'rolling_{window}g_win_rate',
                f'rolling_{window}g_point_diff'
            ]
            
            for col in metrics_to_shrink:
                prior = get_league_prior(col)
                # Use effective sample size (min of window size and actual games played)
                n_samples = df['games_played_prior'].clip(upper=window)
                
                df[col] = apply_shrinkage(
                    value=df[col],
                    prior=prior,
                    n_samples=n_samples,
                    confidence=0.15  # Reduced from 0.3 to prevent over-smoothing in Week 1
                )
        
        # Validate temporal leakage prevention (first game should have 0 for rolling metrics)
        first_game_rolling = df.groupby(['team', 'season']).first()[['rolling_4g_epa_offense', 'rolling_8g_epa_offense']]
        self.logger.info(f"📊 VALIDATION - First game of each team-season (should be 0.0 to prevent leakage):")
        self.logger.info(f"   rolling_4g_epa_offense: min={first_game_rolling['rolling_4g_epa_offense'].min():.4f}, max={first_game_rolling['rolling_4g_epa_offense'].max():.4f}")
        self.logger.info(f"   rolling_8g_epa_offense: min={first_game_rolling['rolling_8g_epa_offense'].min():.4f}, max={first_game_rolling['rolling_8g_epa_offense'].max():.4f}")
        
        # Show statistics for new rolling columns
        self.logger.info(f"📊 Rolling metrics statistics:")
        for window in self.rolling_windows:
            col = f'rolling_{window}g_epa_offense'
            self.logger.info(f"   {col}: min={df[col].min():.4f}, max={df[col].max():.4f}, mean={df[col].mean():.4f}, nulls={df[col].isnull().sum()}")
        
        self.logger.info(f"✓ Added rolling metrics (output: {len(df):,} rows, {len(df.columns)} cols)")
        return df
    
    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add momentum and streak indicators (V2 logic preserved).
        
        Args:
            df: DataFrame with rolling metrics
            
        Returns:
            DataFrame with momentum indicators added
        """
        if df.empty:
            return df
        
        self.logger.info(f"📊 Adding momentum indicators (input: {len(df):,} rows, {len(df.columns)} cols)")
        
        # Recent form analysis (last N games) - exclude current game with .shift(1)
        # Use .transform() for proper index alignment
        recent_window = self.recent_games_window
        df[f'recent_{recent_window}g_win_rate'] = df.groupby(['team', 'season'])['win'].transform(
            lambda x: x.rolling(window=recent_window, min_periods=1).mean().shift(1).fillna(0)
        )
        df[f'recent_{recent_window}g_avg_margin'] = df.groupby(['team', 'season'])['point_differential'].transform(
            lambda x: x.rolling(window=recent_window, min_periods=1).mean().shift(1).fillna(0)
        )
        df[f'recent_{recent_window}g_epa_trend'] = df.groupby(['team', 'season'])['epa_per_play_offense'].transform(
            lambda x: x.rolling(window=recent_window, min_periods=1).mean().shift(1).fillna(0)
        )
        
        # Win/loss streaks - LEAK-PROOF VERSION
        # Uses shift(1) to ensure streak is based only on PRIOR games, not current game
        def _streak_from_prior_games(s: pd.Series) -> pd.Series:
            """
            Calculate win/loss streak from prior games only (no temporal leakage).
            
            Args:
                s: Series of win/loss values (1/0)
                
            Returns:
                Series of streak values where positive = win streak, negative = loss streak
            """
            # shift(1) ensures no current-game info is used
            prior = s.shift(1).fillna(0).astype(int)
            cur = 0
            out = []
            for w in prior:
                if w == 1:
                    cur = cur + 1 if cur > 0 else 1
                else:
                    cur = cur - 1 if cur < 0 else -1
                out.append(cur)
            return pd.Series(out, index=s.index)
        
        df['win_loss_streak'] = df.groupby(['team', 'season'], group_keys=False)['win'].apply(_streak_from_prior_games)
        
        # Performance trending (improving vs declining) - exclude current game
        # Use .transform() for proper index alignment
        for metric in ['epa_per_play_offense', 'epa_per_play_defense', 'point_differential']:
            # Compare recent performance to longer-term average
            recent_avg = df.groupby(['team', 'season'])[metric].transform(
                lambda x: x.rolling(window=4, min_periods=1).mean().shift(1).fillna(0)
            )
            longer_avg = df.groupby(['team', 'season'])[metric].transform(
                lambda x: x.rolling(window=8, min_periods=1).mean().shift(1).fillna(0)
            )
            df[f'{metric}_trending'] = recent_avg - longer_avg
        
        # Show statistics for momentum indicators
        self.logger.info(f"📊 Momentum indicators statistics:")
        self.logger.info(f"   win_loss_streak: min={df['win_loss_streak'].min()}, max={df['win_loss_streak'].max()}, mean={df['win_loss_streak'].mean():.2f}")
        self.logger.info(f"   recent_4g_win_rate: min={df['recent_4g_win_rate'].min():.4f}, max={df['recent_4g_win_rate'].max():.4f}, mean={df['recent_4g_win_rate'].mean():.4f}")
        self.logger.info(f"   epa_per_play_offense_trending: min={df['epa_per_play_offense_trending'].min():.4f}, max={df['epa_per_play_offense_trending'].max():.4f}, mean={df['epa_per_play_offense_trending'].mean():.4f}")
        
        self.logger.info(f"✓ Added momentum indicators (output: {len(df):,} rows, {len(df.columns)} cols)")
        return df
    
    def _add_consistency_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add consistency and variance metrics (V2 logic preserved).
        
        Args:
            df: DataFrame with momentum indicators
            
        Returns:
            DataFrame with consistency metrics added
        """
        if df.empty:
            return df
        
        self.logger.info(f"📊 Adding consistency metrics (input: {len(df):,} rows, {len(df.columns)} cols)")
        
        # Rolling standard deviations (consistency indicators) - exclude current game
        # Use .transform() for proper index alignment
        for window in [4, 8]:
            df[f'rolling_{window}g_epa_offense_std'] = df.groupby(['team', 'season'])['epa_per_play_offense'].transform(
                lambda x: x.rolling(window=window, min_periods=2).std().shift(1)
            )
            df[f'rolling_{window}g_epa_defense_std'] = df.groupby(['team', 'season'])['epa_per_play_defense'].transform(
                lambda x: x.rolling(window=window, min_periods=2).std().shift(1)
            )
            df[f'rolling_{window}g_point_diff_std'] = df.groupby(['team', 'season'])['point_differential'].transform(
                lambda x: x.rolling(window=window, min_periods=2).std().shift(1)
            )
            df[f'rolling_{window}g_points_for_std'] = df.groupby(['team', 'season'])['points_for'].transform(
                lambda x: x.rolling(window=window, min_periods=2).std().shift(1)
            )
        
        # Venue-specific performance (rolling 8-game average point differential at this venue)
        # Renamed from 'home_field_advantage' for clarity - this is measured in points, not a binary flag
        df['rolling_8g_venue_point_diff'] = df.groupby(['team', 'season', 'venue'])['point_differential'].transform(lambda x: x.rolling(window=8, min_periods=1).mean().shift(1).fillna(0))
        
        # Performance by game context - exclude current game
        df['outdoor_performance'] = df.groupby(['team', 'season', 'outdoor_game'])['epa_per_play_offense'].transform(lambda x: x.rolling(window=8, min_periods=1).mean().shift(1).fillna(0))
        df['grass_performance'] = df.groupby(['team', 'season', 'grass_surface'])['epa_per_play_offense'].transform(lambda x: x.rolling(window=8, min_periods=1).mean().shift(1).fillna(0))
        
        # Show statistics for consistency metrics
        self.logger.info(f"📊 Consistency metrics statistics:")
        self.logger.info(f"   rolling_4g_epa_offense_std: min={df['rolling_4g_epa_offense_std'].min():.4f}, max={df['rolling_4g_epa_offense_std'].max():.4f}, mean={df['rolling_4g_epa_offense_std'].mean():.4f}, nulls={df['rolling_4g_epa_offense_std'].isnull().sum()}")
        self.logger.info(f"   rolling_4g_epa_defense_std: min={df['rolling_4g_epa_defense_std'].min():.4f}, max={df['rolling_4g_epa_defense_std'].max():.4f}, mean={df['rolling_4g_epa_defense_std'].mean():.4f}, nulls={df['rolling_4g_epa_defense_std'].isnull().sum()}")
        self.logger.info(f"   rolling_8g_point_diff_std: min={df['rolling_8g_point_diff_std'].min():.4f}, max={df['rolling_8g_point_diff_std'].max():.4f}, mean={df['rolling_8g_point_diff_std'].mean():.4f}, nulls={df['rolling_8g_point_diff_std'].isnull().sum()}")
        self.logger.info(f"   rolling_8g_venue_point_diff: min={df['rolling_8g_venue_point_diff'].min():.4f}, max={df['rolling_8g_venue_point_diff'].max():.4f}, mean={df['rolling_8g_venue_point_diff'].mean():.4f}")
        
        # Log venue indicator flags
        self.logger.info(f"📊 Venue indicator flags:")
        self.logger.info(f"   is_home: {df['is_home'].value_counts().to_dict()}")
        self.logger.info(f"   is_neutral_site: {df['is_neutral_site'].value_counts().to_dict()}")
        self.logger.info(f"   venue_flag: {df['venue_flag'].value_counts().to_dict()}")
        
        # Validate venue split
        venue_counts = df['venue'].value_counts()
        self.logger.info(f"📊 Venue distribution: {venue_counts.to_dict()}")
        
        self.logger.info(f"✓ Added consistency metrics (output: {len(df):,} rows, {len(df.columns)} cols)")
        
        return df
    
    def _log_feature_quality_metrics(self, df: pd.DataFrame) -> None:
        """
        Analyze and log feature quality metrics to assess predictive power.
        
        This provides insights into which features are likely to be useful for modeling
        BEFORE training, helping identify weak features early.
        
        Args:
            df: DataFrame with all features calculated
        """
        if df.empty or 'win' not in df.columns:
            return
        
        self.logger.info("=" * 80)
        self.logger.info("📊 FEATURE QUALITY ANALYSIS")
        self.logger.info("=" * 80)
        
        # Define key feature groups to analyze
        rolling_features = [
            'rolling_4g_epa_offense', 'rolling_8g_epa_offense', 'rolling_16g_epa_offense',
            'rolling_4g_epa_defense', 'rolling_8g_epa_defense', 'rolling_16g_epa_defense',
            'rolling_4g_point_diff', 'rolling_8g_point_diff', 'rolling_16g_point_diff',
            'rolling_4g_win_rate', 'rolling_8g_win_rate', 'rolling_16g_win_rate'
        ]
        
        momentum_features = [
            'win_loss_streak', 'recent_4g_win_rate', 'recent_4g_avg_margin', 'recent_4g_epa_trend',
            'epa_per_play_offense_trending', 'epa_per_play_defense_trending', 'point_differential_trending'
        ]
        
        consistency_features = [
            'rolling_4g_epa_offense_std', 'rolling_8g_epa_offense_std',
            'rolling_4g_point_diff_std', 'rolling_8g_point_diff_std',
            'rolling_8g_venue_point_diff', 'outdoor_performance', 'grass_performance'
        ]
        
        all_features = rolling_features + momentum_features + consistency_features
        available_features = [f for f in all_features if f in df.columns]
        
        # 1. CORRELATION ANALYSIS
        self.logger.info("\n📊 1. CORRELATION WITH WINS (Higher = More Predictive)")
        self.logger.info("-" * 80)
        
        correlations = df[available_features].corrwith(df['win']).sort_values(ascending=False)
        
        self.logger.info("Top 10 Positive Correlations (features associated with winning):")
        for feat, corr in correlations.head(10).items():
            strength = "STRONG" if abs(corr) > 0.15 else "MODERATE" if abs(corr) > 0.08 else "WEAK"
            self.logger.info(f"   {feat:40s}: {corr:+.4f} ({strength})")
        
        self.logger.info("\nTop 10 Negative Correlations (features associated with losing):")
        for feat, corr in correlations.tail(10).items():
            strength = "STRONG" if abs(corr) > 0.15 else "MODERATE" if abs(corr) > 0.08 else "WEAK"
            self.logger.info(f"   {feat:40s}: {corr:+.4f} ({strength})")
        
        # Identify weak features
        weak_features = correlations[abs(correlations) < 0.05]
        if len(weak_features) > 0:
            self.logger.info(f"\n⚠️  {len(weak_features)} features with VERY WEAK correlation (<0.05):")
            for feat, corr in weak_features.items():
                self.logger.info(f"   {feat:40s}: {corr:+.4f} (may not be predictive)")
        
        # 2. WIN/LOSS STRATIFICATION
        self.logger.info("\n📊 2. WIN/LOSS STRATIFICATION (Larger Difference = More Predictive)")
        self.logger.info("-" * 80)
        
        wins_df = df[df['win'] == 1]
        losses_df = df[df['win'] == 0]
        
        stratification = []
        for feat in available_features:
            win_mean = wins_df[feat].mean()
            loss_mean = losses_df[feat].mean()
            diff = win_mean - loss_mean
            diff_pct = (diff / (abs(loss_mean) + 1e-10)) * 100  # Avoid division by zero
            stratification.append((feat, win_mean, loss_mean, diff, abs(diff)))
        
        # Sort by absolute difference
        stratification.sort(key=lambda x: x[4], reverse=True)
        
        self.logger.info("Top 10 Features by Win/Loss Separation:")
        for feat, win_mean, loss_mean, diff, abs_diff in stratification[:10]:
            self.logger.info(f"   {feat:40s}: wins={win_mean:+.4f}, losses={loss_mean:+.4f}, diff={diff:+.4f}")
        
        # 3. FEATURE VARIANCE ANALYSIS
        self.logger.info("\n📊 3. FEATURE VARIANCE (Low Variance = Not Useful)")
        self.logger.info("-" * 80)
        
        variances = df[available_features].var().sort_values(ascending=True)
        
        self.logger.info("Features with LOWEST variance (may not be predictive):")
        for feat, var in variances.head(10).items():
            std = var ** 0.5
            self.logger.info(f"   {feat:40s}: variance={var:.6f}, std={std:.4f}")
        
        self.logger.info("\nFeatures with HIGHEST variance (more information):")
        for feat, var in variances.tail(10).items():
            std = var ** 0.5
            self.logger.info(f"   {feat:40s}: variance={var:.6f}, std={std:.4f}")
        
        # 4. TEMPORAL STABILITY ANALYSIS
        self.logger.info("\n📊 4. TEMPORAL STABILITY (Consistency Across Seasons)")
        self.logger.info("-" * 80)
        
        # Analyze last 5 seasons for stability
        recent_seasons = sorted(df['season'].unique())[-5:]
        self.logger.info(f"Analyzing stability across seasons: {recent_seasons}")
        
        # Check key features for temporal stability
        key_features_for_stability = ['rolling_8g_epa_offense', 'rolling_8g_point_diff', 'win_loss_streak', 'recent_4g_win_rate']
        
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
            self.logger.info(f"   {feat:40s}: CV={cv:.1f}% ({stability})")
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
        total_features = len(available_features)
        useful_features = strong_corr + moderate_corr
        useful_pct = (useful_features / total_features) * 100
        
        self.logger.info(f"\nOverall Feature Quality:")
        self.logger.info(f"   Total features analyzed: {total_features}")
        self.logger.info(f"   Useful features (>0.08 correlation): {useful_features} ({useful_pct:.1f}%)")
        
        if useful_pct < 30:
            self.logger.warning(f"⚠️  Only {useful_pct:.1f}% of features show moderate-to-strong correlation with wins")
            self.logger.warning("   Consider feature engineering improvements or additional data sources")
        elif useful_pct > 60:
            self.logger.info(f"✓ {useful_pct:.1f}% of features show good predictive potential")
        else:
            self.logger.info(f"✓ {useful_pct:.1f}% of features show moderate predictive potential")
        
        self.logger.info("=" * 80)


# Convenience function for direct usage
def create_rolling_metrics_features(db_service=None, logger=None, bucket_adapter=None):
    """
    Create rolling metrics features service with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        RollingMetricsFeatures: Configured rolling metrics features service
    """

    from ....shared.database_router import get_database_router
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.ml_pipeline.rolling_metrics')
    
    return RollingMetricsFeatures(db_service, logger, bucket_adapter)


__all__ = ['RollingMetricsFeatures', 'create_rolling_metrics_features']
