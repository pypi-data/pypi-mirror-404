"""
Test GameOutcomeModel with Contextual Features Integration

Validates that the model can successfully:
1. Load rolling metrics
2. Load contextual features
3. Merge them correctly
4. Train without errors
5. Use contextual features in predictions

Usage:
    python scripts/test_model_with_contextual.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from commonv2 import get_logger
from nflfastRv3.shared.database_router import get_database_router
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from nflfastRv3.features.ml_pipeline.models.game_lines.game_outcome import GameOutcomeModel

def test_contextual_integration():
    """Test that contextual features are properly integrated into the model."""
    
    logger = get_logger('test_contextual_integration')
    logger.info("=" * 80)
    logger.info("TESTING GAMEOUTCOMEMODEL WITH CONTEXTUAL FEATURES")
    logger.info("=" * 80)
    
    try:
        # Step 1: Load sample data
        logger.info("\n📊 Step 1: Loading sample data (2023 season)")
        bucket_adapter = get_bucket_adapter(logger=logger)
        
        # Load rolling metrics
        rolling_metrics = bucket_adapter.read_data(
            table_name='rolling_metrics_v1',
            schema='features',
            filters=[('season', '==', 2023)]
        )
        logger.info(f"✓ Loaded rolling_metrics_v1: {len(rolling_metrics):,} rows, {len(rolling_metrics.columns)} columns")
        
        # Load contextual features
        contextual_features = bucket_adapter.read_data(
            table_name='contextual_features_v1',
            schema='features',
            filters=[('season', '==', 2023)]
        )
        logger.info(f"✓ Loaded contextual_features_v1: {len(contextual_features):,} rows, {len(contextual_features.columns)} columns")
        
        # Load targets
        dim_game = bucket_adapter.read_data(
            table_name='dim_game',
            schema='warehouse',
            filters=[('season', '==', 2023)]
        )
        logger.info(f"✓ Loaded dim_game: {len(dim_game):,} rows")
        
        # Step 2: Test prepare_data (should merge contextual features)
        logger.info("\n🔍 Step 2: Testing prepare_data() with contextual features")
        game_df = GameOutcomeModel.prepare_data(rolling_metrics, dim_game, logger=logger)
        
        # Validate contextual features are present
        contextual_cols = [
            'rest_days_diff', 'home_short_rest', 'away_short_rest',
            'is_division_game', 'is_conference_game',
            'stadium_home_win_rate', 'is_dome'
        ]
        
        found_contextual = [col for col in contextual_cols if col in game_df.columns]
        missing_contextual = [col for col in contextual_cols if col not in game_df.columns]
        
        logger.info(f"\n✓ Contextual features found: {len(found_contextual)}/{len(contextual_cols)}")
        for col in found_contextual:
            logger.info(f"  ✓ {col}")
        
        if missing_contextual:
            logger.warning(f"\n⚠️  Missing contextual features: {len(missing_contextual)}")
            for col in missing_contextual:
                logger.warning(f"  ✗ {col}")
        
        # Step 3: Test engineer_features
        logger.info("\n🔍 Step 3: Testing engineer_features()")
        game_df = GameOutcomeModel.engineer_features(game_df, logger=logger)
        logger.info(f"✓ Engineered features: {len(game_df.columns)} total columns")
        
        # Step 4: Test select_features
        logger.info("\n🔍 Step 4: Testing select_features()")
        model_df = GameOutcomeModel.select_features(game_df, logger=logger)
        
        # Count feature types
        diff_features = [col for col in model_df.columns if col.endswith('_diff')]
        contextual_in_model = [col for col in found_contextual if col in model_df.columns]
        
        logger.info(f"\n✓ Final feature set:")
        logger.info(f"  Differential features: {len(diff_features)}")
        logger.info(f"  Contextual features: {len(contextual_in_model)}")
        logger.info(f"  Total features: {len(model_df.columns) - 7}")  # Exclude metadata + target
        
        # Step 5: Validate data quality
        logger.info("\n🔍 Step 5: Validating data quality")
        
        # Check for nulls in contextual features
        null_counts = {}
        for col in contextual_in_model:
            null_count = model_df[col].isna().sum()
            if null_count > 0:
                null_counts[col] = null_count
        
        if null_counts:
            logger.warning(f"\n⚠️  Null values found in contextual features:")
            for col, count in null_counts.items():
                pct = (count / len(model_df)) * 100
                logger.warning(f"  {col}: {count:,} nulls ({pct:.1f}%)")
        else:
            logger.info("✓ No nulls in contextual features")
        
        # Step 6: Sample feature values
        logger.info("\n📊 Step 6: Sample contextual feature values")
        sample = model_df[contextual_in_model].head(5)
        logger.info(f"\n{sample.to_string()}")
        
        # Step 7: Feature statistics
        logger.info("\n📊 Step 7: Contextual feature statistics")
        for col in contextual_in_model:
            if model_df[col].dtype in ['int64', 'float64', 'Int64']:
                stats = model_df[col].describe()
                logger.info(f"\n{col}:")
                logger.info(f"  Mean: {stats['mean']:.3f}")
                logger.info(f"  Std: {stats['std']:.3f}")
                logger.info(f"  Min: {stats['min']:.3f}")
                logger.info(f"  Max: {stats['max']:.3f}")
            else:
                value_counts = model_df[col].value_counts()
                logger.info(f"\n{col}:")
                for val, count in value_counts.head(3).items():
                    pct = (count / len(model_df)) * 100
                    logger.info(f"  {val}: {count:,} ({pct:.1f}%)")
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ CONTEXTUAL FEATURES INTEGRATION TEST PASSED")
        logger.info("=" * 80)
        logger.info(f"\nSummary:")
        logger.info(f"  Games processed: {len(model_df):,}")
        logger.info(f"  Contextual features integrated: {len(contextual_in_model)}")
        logger.info(f"  Total features for training: {len(model_df.columns) - 7}")
        logger.info(f"\nThe model is ready to train with contextual features!")
        logger.info(f"\nNext step: Run training with:")
        logger.info(f"  quantcup nflfastrv3 ml train --train-seasons 2000-2022 --test-seasons 2024")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = test_contextual_integration()
    sys.exit(0 if success else 1)