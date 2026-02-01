"""
Data Loading Module for Injury Analysis

Handles loading of:
- Game schedules
- Injury reports  
- Snap counts
- Participation data
- Player ID mappings

Pattern: Simple data fetchers with unified season filtering.
Complexity: 1 point (DI only, no business logic)
Layer: 2 (Implementation - calls infrastructure directly)

Extracted from lines 350-719 of original injury_features.py
"""

import pandas as pd
from typing import Optional, List, Union


class InjuryDataLoader:
    """Handles all data loading for injury analysis."""
    
    def __init__(self, db_service=None, bucket_adapter=None, logger=None):
        """
        Initialize data loader with injected dependencies.
        
        Args:
            db_service: Database service instance (not currently used, kept for future)
            bucket_adapter: Bucket adapter for data loading
            logger: Logger instance
        """
        self.db_service = db_service
        self.bucket_adapter = bucket_adapter
        self.logger = logger
    
    def _get_season_filters(self, seasons: Optional[Union[int, List[int]]]) -> Optional[List]:
        """
        DRY helper: Convert seasons to bucket filter format.
        
        Args:
            seasons: Single season, list of seasons, or None
            
        Returns:
            Filter list in bucket adapter format, or None if no seasons
        """
        if not seasons:
            return None
        season_list = list(seasons) if isinstance(seasons, (list, tuple)) else [seasons]
        if len(season_list) == 0:
            return None
        return [('season', 'in', season_list)] if len(season_list) > 1 else [('season', '==', season_list[0])]
    
    def load_game_schedule(self, seasons: Optional[Union[int, List[int]]] = None) -> pd.DataFrame:
        """
        Load game schedule from bucket warehouse.
        
        Returns base game structure for injury feature mapping.
        From original lines 350-378.
        
        Args:
            seasons: Season(s) to load data for
            
        Returns:
            DataFrame with columns: game_id, season, week, game_date, home_team, away_team
        """
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        # Prepare filters
        filters = self._get_season_filters(seasons)
        
        # Load dim_game with needed columns
        columns = ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team']
        
        dim_game = bucket_adapter.read_data('dim_game', 'warehouse', filters=filters, columns=columns)
        dim_game = dim_game.drop_duplicates(subset=['game_id'], keep='first')
        
        # Convert game_date to datetime
        dim_game['game_date'] = pd.to_datetime(dim_game['game_date'])
        
        if self.logger:
            self.logger.info(f"✓ Loaded {len(dim_game):,} games for injury feature mapping")
        
        return dim_game
    
    def load_injury_data(self, seasons: Optional[Union[int, List[int]]] = None) -> tuple:
        """
        Load depth chart and injury report data from bucket.
        
        Data Sources:
        - raw_nfldatapy/depth_chart: Historical depth chart data from NFL Data Wrapper (2009+)
        - warehouse/injuries: Unified injury report data (multi-source)
        
        From original lines 380-471.
        
        Args:
            seasons: Season(s) to load data for
            
        Returns:
            Tuple of (depth_chart_df, injuries_df)
        """
        if self.logger:
            self.logger.info("📊 Loading depth chart and injury data...")
        
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        depth_chart_df = pd.DataFrame()
        injuries_df = pd.DataFrame()
        
        try:
            # Prepare season filters
            filters = self._get_season_filters(seasons)
            
            if filters and self.logger:
                season_list = list(seasons) if isinstance(seasons, (list, tuple)) else [seasons]
                self.logger.info(f"   Loading data for seasons: {season_list}")
            elif self.logger:
                self.logger.info(f"   Loading data for all available seasons")
            
            # Load depth charts from raw_nfldatapy bucket (historical data with season/week)
            try:
                depth_chart_df = bucket_adapter.read_data('depth_chart', 'raw_nfldatapy', filters=filters)
                
                if not depth_chart_df.empty and self.logger:
                    self.logger.info(f"✓ Loaded depth charts: {len(depth_chart_df):,} rows")
                    
                    # Show sample columns
                    self.logger.info(f"   Columns: {', '.join(depth_chart_df.columns[:10])}...")
                    
                    # Show data coverage
                    if 'season' in depth_chart_df.columns:
                        seasons_covered = sorted(depth_chart_df['season'].dropna().unique())
                        self.logger.info(f"   Seasons: {seasons_covered}")
                    if 'club_code' in depth_chart_df.columns or 'team' in depth_chart_df.columns:
                        team_col = 'club_code' if 'club_code' in depth_chart_df.columns else 'team'
                        teams_covered = depth_chart_df[team_col].nunique()
                        self.logger.info(f"   Teams: {teams_covered}")
                elif self.logger:
                    self.logger.warning("⚠️  Depth chart data is empty")
                    
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️  Could not load depth charts from bucket: {e}")
            
            # Load injuries from warehouse (unified multi-source data)
            try:
                injuries_df = bucket_adapter.read_data('injuries', 'warehouse', filters=filters)
                
                if not injuries_df.empty and self.logger:
                    self.logger.info(f"✓ Loaded injuries from warehouse: {len(injuries_df):,} rows")
                    
                    # Log source distribution for transparency
                    if 'source' in injuries_df.columns:
                        source_dist = injuries_df['source'].value_counts().to_dict()
                        self.logger.info(f"   Sources: {source_dist}")
                    
                    # Show sample columns
                    self.logger.info(f"   Columns: {', '.join(injuries_df.columns[:10])}...")
                    
                    # Show data coverage
                    if 'season' in injuries_df.columns:
                        seasons_covered = sorted(injuries_df['season'].dropna().unique())
                        self.logger.info(f"   Seasons: {seasons_covered}")
                    if 'team' in injuries_df.columns:
                        teams_covered = injuries_df['team'].nunique()
                        self.logger.info(f"   Teams: {teams_covered}")
                    if 'report_status' in injuries_df.columns:
                        status_counts = injuries_df['report_status'].value_counts()
                        self.logger.info(f"   Injury statuses: {', '.join(status_counts.head(5).index.tolist())}")
                elif self.logger:
                    self.logger.warning("⚠️  Injury data is empty")
                    
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️  Could not load injuries from bucket: {e}")
        
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️  Error loading injury data from bucket: {e}")
                self.logger.warning("   Injury features will use placeholder values")
        
        return depth_chart_df, injuries_df
    
    def load_player_availability(self, seasons: Optional[Union[int, List[int]]] = None) -> pd.DataFrame:
        """
        Load unified player availability from warehouse (NEW - replaces separate injury/depth loads).
        
        Data Source: warehouse/player_availability
        Coverage: 2002-present (wkly_rosters availability)
        Status: ✅ Implements AVAILABILITYTRACKING_ENHANCEMENTS.md solution
        
        This method replaces the need for separate load_injury_data() calls by providing
        a unified view of ALL player statuses (not just injured):
        - Active players (ACT)
        - Inactive players - healthy scratch (INA + no injury)
        - Inactive players - injured (INA + injury)
        - Injured Reserve (RES)
        - Suspended (SUS)
        - Practice Squad (DEV)
        
        Key Benefits:
        1. Single source of truth for player availability
        2. Identifies healthy scratches (strategic roster decisions)
        3. Tracks long-term unavailability (IR, suspensions)
        4. Comprehensive roster status tracking
        
        Schema (from warehouse_player_availability.py):
        - Identifiers: season, week, team, gsis_id, full_name
        - Player Info: position (primary), depth_chart_position (analysis), jersey_number
        - Roster Status: roster_status (ACT/INA/RES/etc), roster_status_description
        - Injury Status: injury_report_status (Out/Questionable/etc), report_primary_injury
        - Availability: availability_status (unified), is_available (boolean)
        - Depth: depth_rank (from depth_chart)
        - Alternative IDs: pfr_player_id, espn_id, sleeper_id (for joins)
        
        Args:
            seasons: Season(s) to load data for
            
        Returns:
            DataFrame with unified player availability data
            
        Temporal Safety: ✅  Data represents player status at WEEK START (pre-game)
        - wkly_rosters: Week-level snapshot (published pre-game)
        - injuries: Merged by (season, week) gives final injury report
        
        Example Usage:
            >>> # Instead of:
            >>> depth_chart_df, injuries_df = data_loader.load_injury_data(seasons=[2024])
            >>>
            >>> # Use:
            >>> availability_df = data_loader.load_player_availability(seasons=[2024])
            >>>
            >>> # Extract components:
            >>> starters = availability_df[availability_df['depth_rank'] <= 2]
            >>> injured = availability_df[availability_df['injury_report_status'].notna()]
            >>> healthy_scratches = availability_df[availability_df['availability_status'] == 'INACTIVE_HEALTHY']
        """
        if self.logger:
            self.logger.info("📊 Loading unified player availability...")
        
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        # Prepare season filters
        filters = self._get_season_filters(seasons)
        
        try:
            # Load unified availability data from warehouse
            availability_df = bucket_adapter.read_data('player_availability', 'warehouse', filters=filters)
            
            if availability_df.empty:
                if self.logger:
                    self.logger.warning("⚠️  Player availability data is empty")
                    self.logger.warning("   Ensure warehouse builder has been run: quantcup nflfastrv3 data warehouse --tables player_availability")
                return pd.DataFrame()
            
            if self.logger:
                self.logger.info(f"✓ Loaded {len(availability_df):,} player availability records")
                
                # Log coverage summary
                if 'season' in availability_df.columns:
                    seasons_covered = sorted(availability_df['season'].dropna().unique())
                    self.logger.info(f"   Seasons: {', '.join(map(str, seasons_covered))}")
                
                if 'team' in availability_df.columns:
                    teams_covered = availability_df['team'].nunique()
                    self.logger.info(f"   Teams: {teams_covered}")
                
                # Log availability status distribution
                if 'availability_status' in availability_df.columns:
                    status_dist = availability_df['availability_status'].value_counts()
                    self.logger.info(f"   Status distribution:")
                    for status, count in status_dist.head(5).items():
                        pct = (count / len(availability_df)) * 100
                        self.logger.info(f"      {status}: {count:,} ({pct:.1f}%)")
                
                # Log key feature: healthy scratches
                if 'availability_status' in availability_df.columns:
                    healthy_scratches = (availability_df['availability_status'] == 'INACTIVE_HEALTHY').sum()
                    if healthy_scratches > 0:
                        self.logger.info(f"   ⭐ Healthy scratches: {healthy_scratches:,} (strategic roster decisions)")
            
            return availability_df
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Could not load player availability: {e}")
                self.logger.error("   Possible causes:")
                self.logger.error("   1. Warehouse table not built yet (run: quantcup nflfastrv3 data warehouse --tables player_availability)")
                self.logger.error("   2. wkly_rosters not loaded (dependency)")
                self.logger.error("   3. Season filter too restrictive")
                self.logger.error("   Falling back to legacy load_injury_data() method")
            return pd.DataFrame()
    
    def load_snap_counts(self, seasons: Optional[Union[int, List[int]]] = None) -> pd.DataFrame:
        """
        Load player snap counts (actual participation per game).
        
        Data Source: raw_nflfastr/snap_counts
        Coverage: 2012+ (nflfastr availability)
        
        Snap counts show WHO ACTUALLY PLAYED, not just who was listed as starter.
        Critical for identifying:
        - True starters (98% snap share)
        - Rotational players (40-60% snap share)
        - Backups (5-20% snap share)
        
        From original lines 473-547.
        
        Args:
            seasons: Season(s) to load data for
            
        Returns:
            DataFrame with columns:
            - game_id, season, week
            - pfr_player_id (or gsis_id depending on nflfastr version)
            - player (full name)
            - position, team
            - offense_snaps, offense_pct
            - defense_snaps, defense_pct
            - st_snaps, st_pct (special teams)
        
        Temporal Safety: Snap counts are from COMPLETED games only (no future leakage)
        """
        if self.logger:
            self.logger.info("📊 Loading snap counts for true starter identification...")
        
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        # Prepare season filters (same pattern as injuries/depth chart loading)
        filters = self._get_season_filters(seasons)
        
        try:
            snap_counts_df = bucket_adapter.read_data('snap_counts', 'raw_nflfastr', filters=filters)
            
            if not snap_counts_df.empty and self.logger:
                self.logger.info(f"✓ Loaded snap counts: {len(snap_counts_df):,} rows")
                
                # Log coverage for transparency
                if 'season' in snap_counts_df.columns:
                    seasons_covered = sorted(snap_counts_df['season'].dropna().unique())
                    self.logger.info(f"   Seasons: {seasons_covered}")
                    
                    # Check for pre-2012 data (snap counts weren't tracked)
                    if any(s < 2012 for s in seasons_covered):
                        self.logger.warning(f"   ⚠️ Snap counts unavailable before 2012 - will fall back to depth chart")
                
                # Log key columns available
                snap_cols = [c for c in snap_counts_df.columns if 'pct' in c.lower()]
                self.logger.info(f"   Snap % columns: {', '.join(snap_cols)}")
                
                # Log sample data distribution
                if 'offense_pct' in snap_counts_df.columns:
                    avg_snap_pct = snap_counts_df['offense_pct'].mean()
                    self.logger.info(f"   Average offense snap %: {avg_snap_pct:.1f}%")
                
                return snap_counts_df
            else:
                if self.logger:
                    self.logger.warning("⚠️  Snap counts data is empty")
                    self.logger.warning("   Will fall back to depth chart only for starter identification")
                return pd.DataFrame()
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️  Could not load snap counts from bucket: {e}")
                self.logger.warning("   Expected if:")
                self.logger.warning("   1. Seasons before 2012 requested (snap counts not tracked)")
                self.logger.warning("   2. snap_counts table not yet in bucket")
                self.logger.warning("   Falling back to depth chart only for starter identification")
            return pd.DataFrame()
    
    def load_participation_data(self, seasons: Optional[Union[int, List[int]]] = None) -> pd.DataFrame:
        """
        Load play-by-play participation data for package usage validation (Phase 4).
        
        Data Source: bucket/raw_nflfastr/participation
        Coverage: 433,805 rows (2016-2025) confirmed
        Status: ✅ Data available and schema validated (2026-01-24)
        
        Schema (confirmed with actual data):
        - nflverse_game_id: Modern game ID format (e.g., "2016_01_CAR_DEN")
        - old_game_id: Legacy game ID (e.g., "2016090800")
        - play_id: Play-level identifier
        - possession_team: Offensive team code
        - defense_personnel: "# DL, # LB, # DB" format (e.g., "4 DL, 2 LB, 5 DB")
        - offense_personnel: "# RB, # TE, # WR" format
        
        From original lines 549-619.
        
        Args:
            seasons: Season(s) to load data for
            
        Returns:
            DataFrame with play-level participation data for nickel validation
        
        Temporal Safety: Participation data is historical (completed plays only)
        """
        if self.logger:
            self.logger.info("📊 Loading participation data for nickel validation...")
        
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        # Prepare season filters
        filters = self._get_season_filters(seasons)
        
        try:
            # Load participation data from bucket
            participation_df = bucket_adapter.read_data('participation', 'raw_nflfastr', filters=filters)
            
            if participation_df.empty:
                if self.logger:
                    self.logger.warning("⚠️ Participation data is empty")
                return pd.DataFrame()
            
            if self.logger:
                self.logger.info(f"✓ Loaded {len(participation_df):,} participation records (play-level)")
            
            # Validate schema (based on confirmed data structure)
            required_cols = ['nflverse_game_id', 'defense_personnel']
            missing = [c for c in required_cols if c not in participation_df.columns]
            if missing and self.logger:
                self.logger.error(f"❌ Missing required columns: {missing}")
                self.logger.error(f"   Available: {list(participation_df.columns)}")
                return pd.DataFrame()
            
            # Log sample defense_personnel values for verification
            if self.logger:
                sample_values = participation_df['defense_personnel'].dropna().head(10).tolist()
                self.logger.info(f"   Sample defense_personnel values: {sample_values[:3]}...")
            
            # Extract season and week from game_id (format: "YYYY_WW_AWAY_HOME")
            if 'season' not in participation_df.columns or 'week' not in participation_df.columns:
                if self.logger:
                    self.logger.info("   Extracting season/week from nflverse_game_id...")
                participation_df[['season', 'week']] = participation_df['nflverse_game_id'].str.split('_', n=2, expand=True)[[0, 1]]
                participation_df['season'] = pd.to_numeric(participation_df['season'], errors='coerce')
                participation_df['week'] = pd.to_numeric(participation_df['week'], errors='coerce')
                
                # Log extraction results
                if self.logger:
                    extracted_count = participation_df[['season', 'week']].notna().all(axis=1).sum()
                    self.logger.info(f"      ✓ Extracted {extracted_count:,} rows with valid season/week")
            
            return participation_df
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Could not load participation data: {e}")
            return pd.DataFrame()
    
    def load_player_id_mapping(self) -> pd.DataFrame:
        """
        Load player ID crosswalk (pfr_player_id ↔ gsis_id mapping).
        
        Enables merging snap counts (pfr_player_id) with injuries/depth chart (gsis_id).
        
        Data Sources (in order of preference):
        1. warehouse/player_id_mapping (dedicated crosswalk table)
        2. raw_nflfastr/players (fallback - build mapping on-the-fly)
        
        Coverage: 22,191 players (91.1% of all players as of 2026-01-24)
        From original lines 621-719.
        
        Returns:
            DataFrame with columns:
            - gsis_id: NFL Game Statistics & Information System ID
            - pfr_player_id: Pro Football Reference player ID
            - player_name: Display name for debugging
        
        Temporal Safety: Player IDs are static (don't change over time)
        """
        if self.logger:
            self.logger.info("📊 Loading player ID mapping (gsis_id ↔ pfr_player_id)...")
        
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        bucket_adapter = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
        
        try:
            # Primary: Load dedicated warehouse table (created 2026-01-24)
            id_mapping = bucket_adapter.read_data('player_id_mapping', 'warehouse')
            
            if not id_mapping.empty:
                if self.logger:
                    self.logger.info(f"✓ Loaded {len(id_mapping):,} player ID mappings from warehouse")
                
                # Verify required columns exist
                required_cols = ['gsis_id', 'pfr_player_id', 'player_name']
                missing = [c for c in required_cols if c not in id_mapping.columns]
                
                if missing:
                    if self.logger:
                        self.logger.error(f"❌ Missing columns in player_id_mapping: {missing}")
                        self.logger.warning(f"   Expected: {required_cols}")
                        self.logger.warning(f"   Found: {list(id_mapping.columns)}")
                    return pd.DataFrame()
                
                # Show coverage stats
                valid_mappings = id_mapping.dropna(subset=['gsis_id', 'pfr_player_id'])
                coverage_pct = (len(valid_mappings) / len(id_mapping)) * 100 if len(id_mapping) > 0 else 0
                if self.logger:
                    self.logger.info(f"   Coverage: {len(valid_mappings):,} valid mappings ({coverage_pct:.1f}%)")
                
                return id_mapping
            else:
                if self.logger:
                    self.logger.warning("⚠️  player_id_mapping table is empty - falling back to players table")
                
        except Exception as e:
            # Fallback: Build from players table directly
            if self.logger:
                self.logger.warning(f"⚠️  Could not load player_id_mapping warehouse table: {e}")
                self.logger.warning(f"   Falling back to building from players table...")
        
        # Fallback: Build mapping from raw_nflfastr/players table
        try:
            players = bucket_adapter.read_data('players', 'raw_nflfastr')
            
            if players.empty:
                if self.logger:
                    self.logger.error("❌ Players table is also empty - cannot build ID mapping")
                return pd.DataFrame()
            
            # Check which ID columns are available
            has_pfr_id = 'pfr_id' in players.columns
            has_gsis_id = 'gsis_id' in players.columns
            has_name = 'display_name' in players.columns or 'full_name' in players.columns
            
            if not (has_pfr_id and has_gsis_id):
                if self.logger:
                    self.logger.error(f"❌ Players table missing required columns")
                    self.logger.error(f"   Has pfr_id: {has_pfr_id}, Has gsis_id: {has_gsis_id}")
                return pd.DataFrame()
            
            # Extract crosswalk columns
            name_col = 'display_name' if 'display_name' in players.columns else 'full_name'
            id_mapping = players[['gsis_id', 'pfr_id', name_col]].copy()
            id_mapping = id_mapping.rename(columns={
                'pfr_id': 'pfr_player_id',
                name_col: 'player_name'
            })
            
            # Remove rows with missing IDs
            pre_clean = len(id_mapping)
            id_mapping = id_mapping.dropna(subset=['gsis_id', 'pfr_player_id'])
            post_clean = len(id_mapping)
            
            dropped = pre_clean - post_clean
            if dropped > 0 and self.logger:
                self.logger.warning(f"   Dropped {dropped:,} rows with missing IDs ({(dropped/pre_clean)*100:.1f}%)")
            
            if self.logger:
                self.logger.info(f"✓ Built {len(id_mapping):,} player ID mappings from players table (fallback)")
            
            return id_mapping
            
        except Exception as fallback_error:
            if self.logger:
                self.logger.error(f"❌ Could not load player ID mapping from any source: {fallback_error}")
                self.logger.error(f"   Phase 3 (hybrid starter identification) will not work properly")
            return pd.DataFrame()


__all__ = ['InjuryDataLoader']
