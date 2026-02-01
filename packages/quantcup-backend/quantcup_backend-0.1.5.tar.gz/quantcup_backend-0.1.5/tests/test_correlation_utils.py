"""
Unit tests for safe correlation utilities.

Tests that the utility functions properly handle:
- Constant series (zero variance)
- Insufficient data pairs
- Normal correlation calculations
"""

import pandas as pd
import numpy as np
import pytest

from nflfastRv3.features.ml_pipeline.reporting.common.correlation_utils import (
    safe_correlation,
    safe_corrwith,
    safe_corr_matrix
)


class TestSafeCorrelation:
    """Test safe_correlation function."""
    
    def test_normal_correlation(self):
        """Test correlation with normal data."""
        s1 = pd.Series([1, 2, 3, 4, 5])
        s2 = pd.Series([2, 4, 6, 8, 10])
        
        result = safe_correlation(s1, s2)
        assert result == pytest.approx(1.0, abs=0.001)
    
    def test_constant_series1(self):
        """Test with constant first series."""
        s1 = pd.Series([5, 5, 5, 5, 5])  # Constant
        s2 = pd.Series([1, 2, 3, 4, 5])
        
        result = safe_correlation(s1, s2)
        assert pd.isna(result)
    
    def test_constant_series2(self):
        """Test with constant second series."""
        s1 = pd.Series([1, 2, 3, 4, 5])
        s2 = pd.Series([10, 10, 10, 10, 10])  # Constant
        
        result = safe_correlation(s1, s2)
        assert pd.isna(result)
    
    def test_insufficient_data(self):
        """Test with insufficient data pairs."""
        s1 = pd.Series([1])
        s2 = pd.Series([2])
        
        result = safe_correlation(s1, s2)
        assert pd.isna(result)
    
    def test_with_nulls(self):
        """Test correlation with null values."""
        s1 = pd.Series([1, 2, np.nan, 4, 5])
        s2 = pd.Series([2, 4, 6, np.nan, 10])
        
        result = safe_correlation(s1, s2)
        # Should calculate on [1,2,5] vs [2,4,10]
        assert not pd.isna(result)


class TestSafeCorrwith:
    """Test safe_corrwith function."""
    
    def test_normal_corrwith(self):
        """Test corrwith with normal data."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [2, 4, 6, 8, 10],
            'c': [5, 4, 3, 2, 1]
        })
        target = pd.Series([1, 2, 3, 4, 5])
        
        result = safe_corrwith(df, target)
        assert len(result) == 3
        assert result['a'] == pytest.approx(1.0, abs=0.001)
        assert result['b'] == pytest.approx(1.0, abs=0.001)
        assert result['c'] == pytest.approx(-1.0, abs=0.001)
    
    def test_with_constant_column(self):
        """Test corrwith with constant column."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [10, 10, 10, 10, 10],  # Constant
            'c': [5, 4, 3, 2, 1]
        })
        target = pd.Series([1, 2, 3, 4, 5])
        
        result = safe_corrwith(df, target)
        assert len(result) == 3
        assert not pd.isna(result['a'])
        assert pd.isna(result['b'])  # Constant column should return nan
        assert not pd.isna(result['c'])
    
    def test_empty_dataframe(self):
        """Test corrwith with empty DataFrame."""
        df = pd.DataFrame()
        target = pd.Series([1, 2, 3])
        
        result = safe_corrwith(df, target)
        assert result.empty


class TestSafeCorrMatrix:
    """Test safe_corr_matrix function."""
    
    def test_normal_corr_matrix(self):
        """Test correlation matrix with normal data."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [2, 4, 6, 8, 10],
            'c': [5, 4, 3, 2, 1]
        })
        
        result = safe_corr_matrix(df)
        assert result.shape == (3, 3)
        assert result.loc['a', 'b'] == pytest.approx(1.0, abs=0.001)
        assert result.loc['a', 'c'] == pytest.approx(-1.0, abs=0.001)
    
    def test_with_constant_column(self):
        """Test correlation matrix with constant column."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [10, 10, 10, 10, 10],  # Constant
            'c': [5, 4, 3, 2, 1]
        })
        
        result = safe_corr_matrix(df)
        # Constant column should be filtered out
        assert result.shape == (2, 2)
        assert 'b' not in result.columns
        assert 'a' in result.columns
        assert 'c' in result.columns
    
    def test_all_constant_columns(self):
        """Test correlation matrix with all constant columns."""
        df = pd.DataFrame({
            'a': [5, 5, 5, 5, 5],
            'b': [10, 10, 10, 10, 10]
        })
        
        result = safe_corr_matrix(df)
        assert result.empty
    
    def test_insufficient_columns(self):
        """Test correlation matrix with only one non-constant column."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [10, 10, 10, 10, 10]
        })
        
        result = safe_corr_matrix(df)
        assert result.empty  # Need at least 2 non-constant columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
