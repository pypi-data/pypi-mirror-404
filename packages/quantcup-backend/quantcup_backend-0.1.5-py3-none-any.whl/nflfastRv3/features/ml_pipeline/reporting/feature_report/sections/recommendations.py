"""
Feature Report - Recommendations Section

Generates actionable recommendations based on build status.
"""

from typing import Dict, Any


class RecommendationsSectionGenerator:
    """
    Generates recommendations section.
    
    Provides actionable next steps based on feature engineering success rate.
    """
    
    def __init__(self, logger=None):
        """
        Initialize recommendations generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate(self, results: Dict[str, Any]) -> str:
        """
        Generate actionable recommendations.
        
        Args:
            results: Feature engineering results dict
        
        Returns:
            str: Formatted recommendations section
        """
        feature_results = results.get('results', {})
        successful = sum(1 for r in feature_results.values() if r.get('status') == 'success')
        total = len(feature_results)
        
        recommendations = ["## Recommendations\n"]
        
        # Success-based recommendations
        if successful == total:
            recommendations.append("""### ✅ All Features Built Successfully

**Next Steps:**
1. **Start Model Training** - Features are ready for ML pipeline
2. **Review Feature Logs** - Check individual feature set logs for detailed statistics
3. **Validate Data Quality** - Verify features loaded correctly in training pipeline
4. **Monitor Performance** - Track how features impact model accuracy

**Usage in ML Pipeline:**
```bash
# Train model with all features
quantcup nflfastrv3 ml train game_outcome --train-years 5 --test-year 2024

# Or backtest across multiple years
quantcup nflfastrv3 ml backtest game_outcome --train-years 5 --start-year 2020 --end-year 2024
```""")
        
        elif successful > 0:
            failed_features = [name for name, r in feature_results.items() if r.get('status') != 'success']
            recommendations.append(f"""### ⚠️ Partial Success - Some Features Failed

**Failed Features:** {', '.join(failed_features)}

**Troubleshooting:**
1. **Review Error Logs** - Check individual feature set logs for error details
2. **Data Availability** - Ensure required warehouse tables are populated
3. **Retry Failed Features** - Use CLI to rebuild specific feature sets:
   ```bash
   quantcup nflfastrv3 ml features --sets {' '.join(failed_features)}
   ```
4. **Check Dependencies** - Some features depend on others being built first

**Impact:**
- Models can still train with partial features, but accuracy may be reduced
- Consider addressing failures before production deployment""")
        
        else:
            recommendations.append("""### ❌ Feature Engineering Failed

**Immediate Actions:**
1. **Check Warehouse Data** - Verify warehouse tables are populated
2. **Review Error Logs** - Examine detailed error messages in feature logs
3. **Database Connectivity** - Ensure database and bucket connections are working
4. **Contact Support** - If issue persists, review documentation or seek assistance

**Common Issues:**
- Missing warehouse data (run `quantcup nflfastrv3 data warehouse` first)
- Database connection problems
- Insufficient memory (check memory manager logs)
- Invalid season specifications""")
        
        # General best practices
        recommendations.append("""
### General Best Practices

1. **Regular Rebuilds** - Rebuild features when new seasons become available
2. **Version Control** - Feature sets are versioned (v1, v2) for backwards compatibility
3. **Log Review** - Individual feature logs contain detailed statistics and quality metrics
4. **Documentation** - Refer to feature set source code for implementation details
5. **Temporal Safety** - Features use temporal shifting to prevent data leakage

### Feature Set Documentation

For detailed implementation information:
- **Source Code**: `nflfastRv3/features/ml_pipeline/feature_sets/`
- **Logs Directory**: `logs/quantcup_nflfastrv3_ml_features_<timestamp>/`
- **Database Tables**: `features` schema in QuantCup database
- **Bucket Storage**: `features/` directory in object storage""")
        
        return '\n'.join(recommendations)


__all__ = ['RecommendationsSectionGenerator']
