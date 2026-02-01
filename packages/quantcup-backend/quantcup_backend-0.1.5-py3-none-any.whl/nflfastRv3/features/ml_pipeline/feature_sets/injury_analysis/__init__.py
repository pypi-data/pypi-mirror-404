"""
Injury Analysis Module - Player Availability and Depth Chart Analysis

Self-contained module following the reporting refactor pattern.
All injury-related feature engineering logic is colocated here.

Pattern: Facade + Composition (no premature utils extraction)
Complexity: 2 points (DI + composition)
Layer: 2 (Implementation - calls infrastructure directly)

Architecture:
- Public API: InjuryFeatures (delegates to specialized classes)
- Data Loading: InjuryDataLoader
- Analysis: StarterIdentifier, NickelValidator, InjuryImpactCalculator
- Logging: QualityLogger

Usage:
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis import (
        create_injury_features
    )
    
    injury_features = create_injury_features(db_service, logger)
    result = injury_features.build_features([2023, 2024])
"""

import os
import pandas as pd
from typing import Dict, Any, Optional, Union, List

from commonv2.core.logging import get_logger
from .data_loaders import InjuryDataLoader
from .starter_identification import StarterIdentifier
from .nickel_validation import NickelValidator
from .impact_calculation import InjuryImpactCalculator
from .quality_logging import QualityLogger


class InjuryFeatures:
    """
    Facade for injury analysis (maintains backward compatibility).
    
    Delegates to specialized components:
    - data_loader: InjuryDataLoader
    - starter_id: StarterIdentifier
    - nickel: NickelValidator
    - impact: InjuryImpactCalculator
    - quality: QualityLogger
    """
    
    def __init__(self, db_service, logger=None, bucket_adapter=None, debug=False):
        """
        Initialize injury features facade.
        
        Args:
            db_service: Database service instance
            logger: Optional logger (uses unified logger if None)
            bucket_adapter: Optional bucket adapter for data loading
            debug: Enable diagnostic logging (default: False)
        """
        self.db_service = db_service
        self.logger = logger or get_logger('nflfastRv3.ml_pipeline.injury_features')
        self.bucket_adapter = bucket_adapter
        self.debug = debug or os.getenv('INJURY_DEBUG', '').lower() == 'true'
        
        # Initialize specialized components
        self.data_loader = InjuryDataLoader(db_service, bucket_adapter, self.logger)
        self.starter_id = StarterIdentifier(self.logger, debug)
        self.nickel = NickelValidator(self.logger, debug)
        self.impact = InjuryImpactCalculator(self.logger, debug)
        self.quality = QualityLogger(self.logger)
    
    def build_features(self, seasons: Optional[Union[int, List[int]]] = None) -> Dict[str, Any]:
        """
        Primary entry point - orchestrates all feature building.
        
        Expected Impact: 8-12 point variance reduction
        
        Features:
        - Position-weighted injury impact scores
        - Starter availability indicators (QB, key positions)
        - Depth chart quality metrics
        - Base11 vs nickel starter tracking
        - Replacement reason classification (injury/performance/unknown)
        
        Args:
            seasons: Season(s) to build features for
            
        Returns:
            Dict with 'status', 'dataframe', 'metadata'
        """
        self.logger.info(f"Building injury features for seasons: {seasons or 'all'}")
        
        try:
            # Step 1: Load all data sources
            games_df = self.data_loader.load_game_schedule(seasons)
            
            if games_df.empty:
                return {
                    'status': 'warning',
                    'message': 'No game schedule data available',
                    'features_built': 0
                }
            
            depth_chart_df, injuries_df = self.data_loader.load_injury_data(seasons)
            
            if depth_chart_df.empty and injuries_df.empty:
                self.logger.warning("No depth chart or injury data available - returning placeholder features")
            
            # Step 2: Load and validate participation data (Phase 4 - nickel validation)
            if not depth_chart_df.empty:
                self.logger.info("📊 Phase 4: Validating nickel designations with participation data...")
                participation_df = self.data_loader.load_participation_data(seasons)
                
                if not participation_df.empty:
                    # Validate nickel starters before using depth chart
                    depth_chart_df = self.nickel.validate_nickel_starters(depth_chart_df, participation_df)
                    self.logger.info("✓ Phase 4 nickel validation complete")
                else:
                    self.logger.warning("⚠️ No participation data available - skipping Phase 4 validation")
                    self.logger.warning("   Nickel starters will be used as-is from depth chart")
            else:
                self.logger.warning("⚠️ No depth chart data - skipping Phase 4 validation")
            
            # Step 3: Load snap counts for true starter identification (Phase 2/3)
            snap_counts_df = self.data_loader.load_snap_counts(seasons)
            
            # Step 4: Load player ID mapping for cross-referencing
            id_mapping = self.data_loader.load_player_id_mapping()
            
            # Step 5: Identify true starters using hybrid approach (Phase 3)
            if not depth_chart_df.empty or not snap_counts_df.empty:
                starters_df = self.starter_id.identify_true_starters(
                    depth_chart_df, 
                    snap_counts_df,
                    id_mapping
                )
                
                # ✅ DIAGNOSTIC: Check what columns exist in starters_df
                if self.debug:
                    self.logger.info("🔍 DIAGNOSTIC - starters_df after identify_true_starters():")
                    self.logger.info(f"   Columns: {starters_df.columns.tolist()}")
                    self.logger.info(f"   Rows: {len(starters_df):,}")
                    if 'is_depth_starter_base11' in starters_df.columns:
                        base11_count = starters_df['is_depth_starter_base11'].sum()
                        self.logger.info(f"   is_depth_starter_base11: {base11_count:,} starters")
                    else:
                        self.logger.error("   ❌ is_depth_starter_base11 column MISSING from starters_df")
                    
                    if 'is_depth_starter_nickel' in starters_df.columns:
                        nickel_count = starters_df['is_depth_starter_nickel'].sum()
                        self.logger.info(f"   is_depth_starter_nickel: {nickel_count:,} starters")
                    else:
                        self.logger.error("   ❌ is_depth_starter_nickel column MISSING from starters_df")
            else:
                self.logger.warning("⚠️ No depth chart or snap count data - cannot identify starters")
                starters_df = pd.DataFrame()
            
            # Step 6: Classify replacement reasons (Phase 2)
            if not starters_df.empty and not injuries_df.empty:
                replacement_reasons = self.starter_id.classify_replacement_reason(
                    starters_df, 
                    injuries_df, 
                    snap_counts_df
                )
            else:
                replacement_reasons = pd.DataFrame(columns=['gsis_id', 'team', 'season', 'week', 'replacement_reason'])
            
            # Step 7: Calculate position-weighted injury impact per game
            df = self.impact.calculate_injury_impact(games_df, depth_chart_df, injuries_df)
            
            # Step 8: ✅ FIX - Merge base11/nickel flags from starters_df into depth_chart_df
            # Root cause: add_starter_availability() needs base11/nickel columns but receives raw depth_chart_df
            # Those columns are created in identify_true_starters() but never merged back
            if not starters_df.empty and 'is_depth_starter_base11' in starters_df.columns:
                self.logger.info("🔧 Merging base11/nickel flags from starters_df into depth_chart_df...")
                
                merge_cols = ['gsis_id', 'season', 'week', 'is_depth_starter_base11', 'is_depth_starter_nickel']
                existing_cols = [c for c in merge_cols if c in starters_df.columns]
                
                # ✅ FIX: Remove duplicates before merge to prevent row explosion
                # starters_df has multiple rows per player (snap + depth), take max values
                starters_dedupe = starters_df[existing_cols].groupby(['gsis_id', 'season', 'week']).max().reset_index()
                
                self.logger.info(f"   starters_df rows before dedup: {len(starters_df):,}")
                self.logger.info(f"   starters_df rows after dedup: {len(starters_dedupe):,}")
                
                # Merge
                pre_merge_count = len(depth_chart_df)
                depth_chart_df = depth_chart_df.merge(
                    starters_dedupe,
                    on=['gsis_id', 'season', 'week'],
                    how='left'
                )
                post_merge_count = len(depth_chart_df)
                
                # Validate merge didn't change row count
                if post_merge_count != pre_merge_count:
                    self.logger.error(f"❌ Merge changed row count: {pre_merge_count:,} → {post_merge_count:,}")
                    self.logger.error(f"   Check for duplicate keys in starters_dedupe")
                    # Roll back to prevent data corruption
                    self.logger.warning("⚠️ Rolling back merge - using zeros for base11/nickel")
                    depth_chart_df = depth_chart_df.iloc[:pre_merge_count].copy()  # Truncate to original
                    depth_chart_df['is_depth_starter_base11'] = 0
                    depth_chart_df['is_depth_starter_nickel'] = 0
                else:
                    self.logger.info(f"   ✓ Merge preserved row count: {post_merge_count:,}")
                
                # Fill NaN for non-starters
                if 'is_depth_starter_base11' in depth_chart_df.columns:
                    null_count_pre = depth_chart_df['is_depth_starter_base11'].isna().sum()
                    depth_chart_df['is_depth_starter_base11'] = depth_chart_df['is_depth_starter_base11'].fillna(0).astype(int)
                    base11_count = (depth_chart_df['is_depth_starter_base11'] == 1).sum()
                    self.logger.info(f"   ✓ is_depth_starter_base11: {base11_count:,} starters ({null_count_pre:,} filled with 0)")
                
                if 'is_depth_starter_nickel' in depth_chart_df.columns:
                    null_count_pre = depth_chart_df['is_depth_starter_nickel'].isna().sum()
                    depth_chart_df['is_depth_starter_nickel'] = depth_chart_df['is_depth_starter_nickel'].fillna(0).astype(int)
                    nickel_count = (depth_chart_df['is_depth_starter_nickel'] == 1).sum()
                    self.logger.info(f"   ✓ is_depth_starter_nickel: {nickel_count:,} starters ({null_count_pre:,} filled with 0)")
            else:
                self.logger.warning("⚠️ Cannot merge base11/nickel flags - starters_df empty or columns missing")
            
            # Step 9: Add starter availability indicators (includes replacement reason features)
            df = self.impact.add_starter_availability(df, depth_chart_df, injuries_df, replacement_reasons)
            
            # Step 10: Feature quality analysis
            self.quality.log_feature_quality(df, self.bucket_adapter)
            
            # Step 11: Drop metadata columns to prevent merge conflicts
            # Pattern: Matches nextgen_features.py:520-532
            # These columns already exist in game_df from dim_game merge in game_outcome.py
            metadata_columns = ['home_team', 'away_team', 'game_date', 'home_score', 'away_score']
            columns_to_drop = [col for col in metadata_columns if col in df.columns]
            
            if columns_to_drop:
                self.logger.info(f"📊 Dropping metadata columns from injury features: {columns_to_drop}")
                df = df.drop(columns=columns_to_drop)
                self.logger.info(f"✓ Feature set cleaned: Only injury features + merge keys remain")
            
            return {
                'status': 'success',
                'dataframe': df,  # Now contains only: game_id, season, week + injury features
                'features_built': len(df),
                'seasons_processed': df['season'].nunique()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build injury features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }


def create_injury_features(db_service=None, logger=None, bucket_adapter=None, debug=False):
    """
    Factory function to create injury features analyzer.
    
    Maintains backward compatibility with original factory pattern.
    
    Args:
        db_service: Database service instance
        logger: Optional logger (uses unified logger if None)
        bucket_adapter: Optional bucket adapter for data loading
        debug: Enable diagnostic logging
        
    Returns:
        InjuryFeatures: Configured injury features analyzer
    """
    if logger is None:
        logger = get_logger('nflfastRv3.ml_pipeline.injury_features')
    return InjuryFeatures(db_service, logger, bucket_adapter, debug)


__all__ = ['InjuryFeatures', 'create_injury_features']
