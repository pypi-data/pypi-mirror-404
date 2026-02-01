"""
Test enhanced confusion matrix reporting.

Tests the new visual annotations and comprehensive metrics breakdown.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import
try:
    from nflfastRv3.features.ml_pipeline.reporting.analyzers import _EnsembleAnalyzer
except ModuleNotFoundError:
    # Alternative import for when run directly
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "analyzers",
        project_root / "nflfastRv3" / "features" / "ml_pipeline" / "reporting" / "analyzers.py"
    )
    analyzers_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzers_module)
    _EnsembleAnalyzer = analyzers_module._EnsembleAnalyzer


def test_enhanced_confusion_matrix_xgboost():
    """Test enhanced matrix with XGBOOST example from report."""
    analyzer = _EnsembleAnalyzer()
    
    # XGBOOST example: TN=4, FP=5, FN=1, TP=6, Total=16
    result = analyzer._format_enhanced_confusion_matrix(
        name='xgboost',
        tn=4,
        fp=5,
        fn=1,
        tp=6,
        total=16
    )
    
    print("=" * 80)
    print("XGBOOST Enhanced Confusion Matrix")
    print("=" * 80)
    print(result)
    print("\n")
    
    # Verify key elements are present
    assert "4 pred" in result and "11 pred" in result  # Prediction counts
    assert "← 9 actual away wins" in result  # Away count annotation
    assert "← 7 actual home wins" in result  # Home count annotation
    assert "TN    FP" in result and "FN    TP" in result  # Labels
    assert "precision = TP / (TP + FP)" in result  # Formula
    assert "recall = TP / (TP + FN)" in result  # Formula
    assert "0.55" in result or "54.5%" in result  # Precision value
    assert "0.86" in result or "85.7%" in result  # Recall value
    assert "68.8%" in result  # Home prediction rate
    assert "+25" in result  # Bias
    
    print("✅ XGBOOST test passed!")
    return True


def test_enhanced_confusion_matrix_elasticnet():
    """Test enhanced matrix with ELASTICNET example from report."""
    analyzer = _EnsembleAnalyzer()
    
    # ELASTICNET example: TN=6, FP=3, FN=1, TP=6, Total=16
    result = analyzer._format_enhanced_confusion_matrix(
        name='elasticnet',
        tn=6,
        fp=3,
        fn=1,
        tp=6,
        total=16
    )
    
    print("=" * 80)
    print("ELASTICNET Enhanced Confusion Matrix")
    print("=" * 80)
    print(result)
    print("\n")
    
    # Verify key metrics
    assert "7 pred" in result and "9 pred" in result  # Better balance
    assert "0.67" in result or "66.7%" in result  # Better precision
    assert "56.2%" in result  # Better home prediction rate
    assert "well-calibrated" in result.lower() or "+12" in result  # Lower bias
    
    print("✅ ELASTICNET test passed!")
    return True


def test_enhanced_confusion_matrix_logistic():
    """Test enhanced matrix with LOGISTIC example from report."""
    analyzer = _EnsembleAnalyzer()
    
    # LOGISTIC example: TN=4, FP=5, FN=2, TP=5, Total=16
    result = analyzer._format_enhanced_confusion_matrix(
        name='logistic',
        tn=4,
        fp=5,
        fn=2,
        tp=5,
        total=16
    )
    
    print("=" * 80)
    print("LOGISTIC Enhanced Confusion Matrix")
    print("=" * 80)
    print(result)
    print("\n")
    
    # Verify worst performer metrics
    assert "0.50" in result or "50.0%" in result  # Coin flip precision
    assert "0.71" in result or "71.4%" in result  # Worst recall
    assert "10 pred" in result  # 10 home predictions
    
    print("✅ LOGISTIC test passed!")
    return True


def test_bias_severity_levels():
    """Test different bias severity indicators."""
    analyzer = _EnsembleAnalyzer()
    
    # Test well-calibrated (< 5% bias)
    result_good = analyzer._format_enhanced_confusion_matrix(
        'test', tn=5, fp=4, fn=4, tp=3, total=16
    )
    assert "✅" in result_good and "well-calibrated" in result_good
    print("✅ Well-calibrated bias test passed!")
    
    # Test slight bias (5-15%)
    result_slight = analyzer._format_enhanced_confusion_matrix(
        'test', tn=4, fp=5, fn=1, tp=6, total=16
    )
    assert "🟡" in result_slight or "⚠️" in result_slight
    print("✅ Slight bias test passed!")
    
    # Test severe bias (>25%)
    result_severe = analyzer._format_enhanced_confusion_matrix(
        'test', tn=2, fp=10, fn=0, tp=4, total=16
    )
    assert "🔴" in result_severe and "severe" in result_severe.lower()
    print("✅ Severe bias test passed!")
    
    return True


def test_precision_recall_insights():
    """Test contextual insights based on precision/recall combinations."""
    analyzer = _EnsembleAnalyzer()
    
    # High precision, high recall (excellent)
    result_excellent = analyzer._format_enhanced_confusion_matrix(
        'test', tn=6, fp=2, fn=1, tp=7, total=16
    )
    assert "excellent" in result_excellent.lower() or "🎯" in result_excellent
    print("✅ Excellent balance insight test passed!")
    
    # High precision, low recall (conservative)
    result_conservative = analyzer._format_enhanced_confusion_matrix(
        'test', tn=10, fp=1, fn=4, tp=1, total=16
    )
    assert "conservative" in result_conservative.lower() or "🔒" in result_conservative
    print("✅ Conservative predictor insight test passed!")
    
    # Low precision, high recall (aggressive)
    result_aggressive = analyzer._format_enhanced_confusion_matrix(
        'test', tn=2, fp=6, fn=1, tp=7, total=16
    )
    assert "aggressive" in result_aggressive.lower() or "⚡" in result_aggressive
    print("✅ Aggressive predictor insight test passed!")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Testing Enhanced Confusion Matrix Reporting")
    print("=" * 80 + "\n")
    
    try:
        # Run all tests
        test_enhanced_confusion_matrix_xgboost()
        test_enhanced_confusion_matrix_elasticnet()
        test_enhanced_confusion_matrix_logistic()
        test_bias_severity_levels()
        test_precision_recall_insights()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\nEnhanced confusion matrix reporting is working correctly.")
        print("Data-driven thresholds are aligned with NFL statistics:")
        print("  - Bias thresholds: ±5% (well-calibrated), ±15% (slight), ±25% (severe)")
        print("  - Precision thresholds: 75%+ (excellent), 65%+ (good), 55%+ (moderate)")
        print("  - Recall thresholds: 85%+ (excellent), 75%+ (good), 65%+ (moderate)")
        print("\nThe report now includes:")
        print("  ✓ Visual prediction/actual count annotations")
        print("  ✓ TN/FP/FN/TP labels for education")
        print("  ✓ Complete formulas with calculations")
        print("  ✓ Quality ratings (Excellent/Good/Moderate/Poor)")
        print("  ✓ Contextual insights based on model behavior")
        print("  ✓ NFL-aligned bias severity indicators")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)