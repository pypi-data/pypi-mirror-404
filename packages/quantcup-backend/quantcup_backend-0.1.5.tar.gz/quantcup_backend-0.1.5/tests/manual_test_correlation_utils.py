"""
Manual test for safe correlation utilities.

Run this script to verify the fixes work correctly without needing pytest.
"""

import pandas as pd
import numpy as np
import sys
import warnings

# Add parent directory to path
sys.path.insert(0, '..')

from nflfastRv3.features.ml_pipeline.reporting.common.correlation_utils import (
    safe_correlation,
    safe_corrwith,
    safe_corr_matrix
)


def test_safe_correlation():
    """Test safe_correlation function."""
    print("\n=== Testing safe_correlation ===")
    
    # Test 1: Normal correlation
    print("\n1. Normal correlation (should return 1.0)")
    s1 = pd.Series([1, 2, 3, 4, 5])
    s2 = pd.Series([2, 4, 6, 8, 10])
    result = safe_correlation(s1, s2)
    print(f"   Result: {result} ✓" if abs(result - 1.0) < 0.001 else f"   Result: {result} ✗")
    
    # Test 2: Constant series (should return nan with warning suppressed)
    print("\n2. Constant series (should return nan, no warnings)")
    s1 = pd.Series([5, 5, 5, 5, 5])
    s2 = pd.Series([1, 2, 3, 4, 5])
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = safe_correlation(s1, s2)
        
        # Check for NumPy division warnings
        numpy_warnings = [warning for warning in w if 'divide' in str(warning.message).lower()]
        if numpy_warnings:
            print(f"   Result: nan ✗ (NumPy warning not suppressed: {numpy_warnings[0].message})")
        else:
            print(f"   Result: {result} ✓" if pd.isna(result) else f"   Result: {result} ✗")
    
    # Test 3: Insufficient data
    print("\n3. Insufficient data (should return nan)")
    s1 = pd.Series([1])
    s2 = pd.Series([2])
    result = safe_correlation(s1, s2)
    print(f"   Result: {result} ✓" if pd.isna(result) else f"   Result: {result} ✗")


def test_safe_corrwith():
    """Test safe_corrwith function."""
    print("\n=== Testing safe_corrwith ===")
    
    # Test 1: Normal corrwith
    print("\n1. Normal corrwith")
    df = pd.DataFrame({
        'a': [1, 2, 3, 4, 5],
        'b': [2, 4, 6, 8, 10],
        'c': [5, 4, 3, 2, 1]
    })
    target = pd.Series([1, 2, 3, 4, 5])
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = safe_corrwith(df, target)
        
        numpy_warnings = [warning for warning in w if 'divide' in str(warning.message).lower()]
        if numpy_warnings:
            print(f"   ✗ NumPy warning: {numpy_warnings[0].message}")
        else:
            print(f"   ✓ No warnings")
            print(f"   a: {result['a']:.4f}, b: {result['b']:.4f}, c: {result['c']:.4f}")
    
    # Test 2: With constant column
    print("\n2. With constant column (column b should be nan)")
    df = pd.DataFrame({
        'a': [1, 2, 3, 4, 5],
        'b': [10, 10, 10, 10, 10],  # Constant
        'c': [5, 4, 3, 2, 1]
    })
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = safe_corrwith(df, target)
        
        numpy_warnings = [warning for warning in w if 'divide' in str(warning.message).lower()]
        if numpy_warnings:
            print(f"   ✗ NumPy warning: {numpy_warnings[0].message}")
        else:
            print(f"   ✓ No warnings")
            print(f"   a: {result['a']:.4f}, b: {result['b']}, c: {result['c']:.4f}")
            if pd.isna(result['b']):
                print(f"   ✓ Constant column correctly returned nan")


def test_safe_corr_matrix():
    """Test safe_corr_matrix function."""
    print("\n=== Testing safe_corr_matrix ===")
    
    # Test 1: Normal correlation matrix
    print("\n1. Normal correlation matrix")
    df = pd.DataFrame({
        'a': [1, 2, 3, 4, 5],
        'b': [2, 4, 6, 8, 10],
        'c': [5, 4, 3, 2, 1]
    })
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = safe_corr_matrix(df)
        
        numpy_warnings = [warning for warning in w if 'divide' in str(warning.message).lower()]
        if numpy_warnings:
            print(f"   ✗ NumPy warning: {numpy_warnings[0].message}")
        else:
            print(f"   ✓ No warnings")
            print(f"   Shape: {result.shape}")
            print(f"   a-b correlation: {result.loc['a', 'b']:.4f}")
    
    # Test 2: With constant column
    print("\n2. With constant column (should be filtered out)")
    df = pd.DataFrame({
        'a': [1, 2, 3, 4, 5],
        'b': [10, 10, 10, 10, 10],  # Constant
        'c': [5, 4, 3, 2, 1]
    })
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = safe_corr_matrix(df)
        
        numpy_warnings = [warning for warning in w if 'divide' in str(warning.message).lower()]
        if numpy_warnings:
            print(f"   ✗ NumPy warning: {numpy_warnings[0].message}")
        else:
            print(f"   ✓ No warnings")
            print(f"   Shape: {result.shape} (should be 2x2)")
            print(f"   Columns: {list(result.columns)}")
            if 'b' not in result.columns:
                print(f"   ✓ Constant column correctly filtered")


if __name__ == '__main__':
    print("Testing correlation utilities...")
    print("=" * 60)
    
    test_safe_correlation()
    test_safe_corrwith()
    test_safe_corr_matrix()
    
    print("\n" + "=" * 60)
    print("Tests complete! Check output above for any ✗ marks.")
