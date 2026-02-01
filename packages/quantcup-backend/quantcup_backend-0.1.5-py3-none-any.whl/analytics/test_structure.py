"""
Test script to verify the Solo Developer pattern implementation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from commonv2 import create_db_engine_from_env, get_logger

# Test imports
try:
    from analyticsv2.points_per_drive import generate_points_per_drive_analysis
    from analyticsv2.success_rate import generate_success_rate_analysis
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Setup logging
logger = get_logger(__name__)

def test_points_per_drive():
    """Test points per drive analysis."""
    print("\n=== Testing Points Per Drive Analysis ===")
    
    try:
        from analyticsv2.points_per_drive.models import ChartConfig, AnalysisConfig, CalculationMethod
        
        engine = create_db_engine_from_env('NFLFASTR_DB')
        
        chart_config = ChartConfig(
            title="Test Points Per Drive Chart",
            x_axis_label="Opponent-Adjusted Scoring Efficiency",
            y_axis_label="Opponent-Adjusted Stopping Efficiency", 
            save_path="analyticsv2/test_ppd_chart.png",
            use_dynamic_ranges=True
        )
        
        config = AnalysisConfig(
            season=2025,
            max_week=3,
            calculation_method=CalculationMethod.EPA_BASED,
            chart_config=chart_config,
            include_chart=True
        )
        
        result = generate_points_per_drive_analysis(engine, logger, config)
        
        print(f"✓ Points per drive analysis completed")
        print(f"  - Teams analyzed: {len(result.team_efficiency_metrics)}")
        print(f"  - Execution time: {result.execution_time_seconds:.2f}s")
        print(f"  - Chart saved: {result.chart_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Points per drive analysis failed: {e}")
        return False

def test_success_rate():
    """Test success rate analysis."""
    print("\n=== Testing Success Rate Analysis ===")
    
    try:
        from analyticsv2.success_rate.models import ChartConfig, AnalysisConfig, CalculationMethod
        
        engine = create_db_engine_from_env('NFLFASTR_DB')
        
        chart_config = ChartConfig(
            title="Test Success Rate Chart",
            x_axis_label="Rush Success Rate",
            y_axis_label="Pass Success Rate",
            save_path="analyticsv2/test_sr_chart.png"
        )
        
        config = AnalysisConfig(
            season=2025,
            max_week=3,
            calculation_method=CalculationMethod.EPA_BASED,
            chart_config=chart_config,
            include_chart=True
        )
        
        result = generate_success_rate_analysis(engine, logger, config)
        
        print(f"✓ Success rate analysis completed")
        print(f"  - Teams analyzed: {len(result.team_success_rates)}")
        print(f"  - Execution time: {result.execution_time_seconds:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ Success rate analysis failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing AnalyticsV2 Solo Developer Pattern Implementation")
    print("=" * 60)
    
    tests = [
        test_points_per_drive,
        test_success_rate
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Solo Developer pattern implementation successful.")
        return True
    else:
        print("✗ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
