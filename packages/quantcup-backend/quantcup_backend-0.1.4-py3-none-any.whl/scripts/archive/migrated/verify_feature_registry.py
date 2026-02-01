import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Testing FeatureRegistry...")
    from nflfastRv3.features.ml_pipeline.utils.feature_registry import FeatureRegistry
    active = FeatureRegistry.get_active_features()
    print(f"✓ FeatureRegistry loaded. Active features: {len(active)}")
    
    print("\nTesting GameOutcomeModel integration...")
    from nflfastRv3.features.ml_pipeline.models.game_lines.game_outcome import GameOutcomeModel
    print("✓ GameOutcomeModel imported successfully")
    
    print("\nTesting Predictor integration...")
    from nflfastRv3.features.ml_pipeline.orchestrators.predictor import PredictorImplementation
    print("✓ PredictorImplementation imported successfully")
    
    print("\nAll checks passed!")
    
except Exception as e:
    print(f"\n❌ Verification failed: {e}")
    sys.exit(1)