"""
Quality Logging Module

Logs feature quality metrics, coverage, and diagnostics.

Pattern: Pure logging logic, no business rules.
Extracted from lines 2228-2402 of original injury_features.py.

See docs/injury_analysis/algorithm_details.md for methodology.
"""

import pandas as pd
from typing import Optional


class QualityLogger:
    """Logs feature quality and coverage metrics."""
    
    def __init__(self, logger=None):
        """
        Initialize quality logger.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def log_feature_quality(self, df: pd.DataFrame, bucket_adapter=None) -> None:
        """
        Analyze and log feature quality metrics to assess predictive power.
        
        Enhanced analysis following rolling_metrics.py pattern (lines 737-899):
        1. Correlation analysis with home wins
        2. Win/loss stratification
        3. Feature variance analysis
        4. Temporal stability across seasons
        5. Overall quality summary
        
        This provides insights into which features are likely to be useful for modeling
        BEFORE training, helping identify weak features early.
        
        Args:
            df: DataFrame with all injury features calculated
            bucket_adapter: Optional bucket adapter for loading score data
        """
        if df.empty:
            return
        
        if not self.logger:
            return
        
        # Create home_won indicator if not present
        if 'home_won' not in df.columns and 'home_score' in df.columns and 'away_score' in df.columns:
            # Try to load scores from dim_game
            try:
                from commonv2.persistence.bucket_adapter import get_bucket_adapter
                bucket_adapter = bucket_adapter or get_bucket_adapter(logger=self.logger)
                
                dim_game = bucket_adapter.read_data('dim_game', 'warehouse', 
                                                    columns=['game_id', 'home_score', 'away_score'])
                df = df.merge(dim_game[['game_id', 'home_score', 'away_score']], 
                             on='game_id', how='left')
                df['home_won'] = (df['home_score'] > df['away_score']).astype(int)
            except Exception as e:
                self.logger.warning(f"⚠️  Could not load scores for correlation analysis: {e}")
                return
        
        if 'home_won' not in df.columns:
            self.logger.warning("⚠️  Cannot perform correlation analysis - home_won not available")
            return
        
        self.logger.info("=" * 80)
        self.logger.info("📊 INJURY FEATURE QUALITY ANALYSIS")
        self.logger.info("=" * 80)
        
        # Define injury feature groups (include Phase 1 base11/nickel + Phase 2 replacement reason features)
        injury_features = [
            'home_injury_impact', 'away_injury_impact', 'injury_impact_diff',
            'home_qb_available', 'away_qb_available',
            'home_starter_injuries', 'away_starter_injuries',  # Legacy combined
            'home_starter_injuries_base11', 'away_starter_injuries_base11',  # Phase 1
            'home_starter_injuries_nickel', 'away_starter_injuries_nickel',  # Phase 1
            'home_injury_driven_replacements', 'away_injury_driven_replacements',  # Phase 2
            'home_performance_replacements', 'away_performance_replacements',  # Phase 2
            'home_unknown_replacements', 'away_unknown_replacements'  # Phase 2
        ]
        
        available = [f for f in injury_features if f in df.columns]
        
        # 1. CORRELATION ANALYSIS
        self.logger.info("\n📊 1. CORRELATION WITH HOME WINS (Higher = More Predictive)")
        self.logger.info("-" * 80)
        
        correlations = df[available].corrwith(df['home_won']).sort_values(ascending=False)
        
        self.logger.info("Injury Feature Correlations:")
        for feat, corr in correlations.items():
            strength = "STRONG" if abs(corr) > 0.15 else "MODERATE" if abs(corr) > 0.08 else "WEAK"
            self.logger.info(f"   {feat:30s}: {corr:+.4f} ({strength})")
        
        # Identify weak features
        weak_features = correlations[abs(correlations) < 0.05]
        if len(weak_features) > 0:
            self.logger.info(f"\n⚠️  {len(weak_features)} features with VERY WEAK correlation (<0.05):")
            for feat, corr in weak_features.items():
                self.logger.info(f"   {feat:30s}: {corr:+.4f} (may not be predictive)")
        
        # 2. WIN/LOSS STRATIFICATION
        self.logger.info("\n📊 2. WIN/LOSS STRATIFICATION (Larger Difference = More Predictive)")
        self.logger.info("-" * 80)
        
        wins_df = df[df['home_won'] == 1]
        losses_df = df[df['home_won'] == 0]
        
        self.logger.info("Injury Features by Win/Loss:")
        for feat in available:
            win_mean = wins_df[feat].mean()
            loss_mean = losses_df[feat].mean()
            diff = win_mean - loss_mean
            self.logger.info(f"   {feat:30s}: wins={win_mean:+.4f}, losses={loss_mean:+.4f}, diff={diff:+.4f}")
        
        # 3. FEATURE VARIANCE ANALYSIS
        self.logger.info("\n📊 3. FEATURE VARIANCE (Low Variance = Not Useful)")
        self.logger.info("-" * 80)
        
        for feat in available:
            # Calculate variance and std - type: ignore for pandas scalar types
            var_value = df[feat].var()  # type: ignore
            std_value = var_value ** 0.5  # type: ignore
            self.logger.info(f"   {feat:30s}: variance={var_value:.6f}, std={std_value:.4f}")
        
        # 4. TEMPORAL STABILITY ANALYSIS (if multiple seasons)
        if 'season' in df.columns and df['season'].nunique() > 1:
            self.logger.info("\n📊 4. TEMPORAL STABILITY (Consistency Across Seasons)")
            self.logger.info("-" * 80)
            
            # Analyze last 5 seasons for stability
            recent_seasons = sorted(df['season'].unique())[-5:]
            self.logger.info(f"Analyzing stability across seasons: {recent_seasons}")
            
            for feat in ['injury_impact_diff', 'home_qb_available']:
                if feat not in df.columns:
                    continue
                
                season_means = []
                for season in recent_seasons:
                    season_mean = df[df['season'] == season][feat].mean()
                    season_means.append(season_mean)
                
                # Calculate coefficient of variation
                mean_of_means = sum(season_means) / len(season_means)
                std_of_means = (sum((x - mean_of_means) ** 2 for x in season_means) / len(season_means)) ** 0.5
                cv = (std_of_means / (abs(mean_of_means) + 1e-10)) * 100
                
                stability = "STABLE" if cv < 20 else "MODERATE" if cv < 50 else "UNSTABLE"
                self.logger.info(f"   {feat:30s}: CV={cv:.1f}% ({stability})")
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
        total_features = len(available)
        useful_features = strong_corr + moderate_corr
        useful_pct = (useful_features / total_features) * 100 if total_features > 0 else 0
        
        self.logger.info(f"\nOverall Feature Quality:")
        self.logger.info(f"   Total features analyzed: {total_features}")
        self.logger.info(f"   Useful features (>0.08 correlation): {useful_features} ({useful_pct:.1f}%)")
        
        if useful_pct < 30:
            self.logger.warning(f"⚠️  Only {useful_pct:.1f}% of injury features show moderate-to-strong correlation")
            self.logger.warning("   NOTE: Injury features may work through interaction effects with team performance")
            self.logger.warning("   Multi-season training will reveal true predictive power")
        elif useful_pct > 60:
            self.logger.info(f"✓ {useful_pct:.1f}% of injury features show good predictive potential")
        else:
            self.logger.info(f"✓ {useful_pct:.1f}% of injury features show moderate predictive potential")
        
        # Feature statistics
        self.logger.info("\n📊 6. FEATURE STATISTICS")
        self.logger.info("-" * 80)
        for feat in available:
            nulls = df[feat].isnull().sum()
            null_pct = (nulls / len(df)) * 100
            unique = df[feat].nunique()
            feat_min = df[feat].min()
            feat_max = df[feat].max()
            feat_mean = df[feat].mean()
            self.logger.info(f"   {feat:30s}: nulls={nulls:,} ({null_pct:.1f}%), unique={unique:,}, range=[{feat_min:.3f}, {feat_max:.3f}], mean={feat_mean:.3f}")
        
        self.logger.info("=" * 80)


__all__ = ['QualityLogger']
