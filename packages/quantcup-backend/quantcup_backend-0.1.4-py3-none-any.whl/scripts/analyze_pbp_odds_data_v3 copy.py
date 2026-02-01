#!/usr/bin/env python3
"""
Comprehensive analysis of play-by-play odds data from nflfastR dataset.

Analyzes odds-related columns including Vegas win probability metrics and betting lines.
Generates markdown report, JSON output, and CSV data export with quality assessments.

Output locations:
- Reports: C:\\Users\\acief\\Documents\\cdrive_projects\\quantcup_backend\\reports
- Data: C:\\Users\\acief\\Documents\\cdrive_projects\\quantcup_backend\\data

Usage:
    python scripts/analyze_pbp_odds_data.py

Architecture:
    2 complexity points (DI + business logic)
    - Dependency Injection: bucket_adapter, logger
    - Business Logic: analysis engine
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

from commonv2 import get_logger
from commonv2.persistence.bucket_adapter import get_bucket_adapter

# ============================================================================
# CONFIGURATION
# ============================================================================

SEASON = 2025  # Configurable season for analysis

# Output directories (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"

# Data source
BUCKET_SCHEMA = 'raw_nflfastr'
TABLE_NAME = 'play_by_play'

# Quality thresholds
QUALITY_THRESHOLDS = {
    'null_warning_pct': 5.0,      # Warn if >5% null
    'null_critical_pct': 20.0,    # Critical if >20% null
    'outlier_warning_count': 10,  # Warn if >10 outliers
}

# Column-type-specific analysis behavior. This prevents generic outlier logic
# (IQR / 3σ) from flagging heavy-tailed metrics like WPA as "bad data".
COLUMN_TYPE_CONFIGS = {
    'wp': {
        'use_iqr': True,
        'use_3sigma': True,
        'iqr_multiplier': 1.5,
        'sigma_multiplier': 3.0,
    },
    'wpa': {
        # WPA is heavy-tailed; treat large deltas as "high-leverage" instead of outliers.
        'use_iqr': False,
        'use_3sigma': False,
        # "High leverage" thresholds are informational (not quality downgrades)
        'high_leverage_threshold': 0.15,
        'extreme_threshold': 0.30,
        # Only treat as quality issue if we exceed theoretical bounds
        'theoretical_range': (-1.0, 1.0),
    },
    'line': {
        'use_iqr': True,
        'use_3sigma': True,
        'iqr_multiplier': 1.5,
        'sigma_multiplier': 3.0,
    }
}

# Odds columns specification (from PBP_COLUMN_INFO.md)
ODDS_COLUMNS = {
    'vegas_wp': {
        'section': 'Vegas-Adjusted Win Probability',
        'col_type': 'wp',
        'data_type': 'float',
        'expected_range': (0.0, 1.0),
        'description': 'Vegas baseline WP pre-play (0-1)'
    },
    'vegas_home_wp': {
        'section': 'Vegas-Adjusted Win Probability',
        'col_type': 'wp',
        'data_type': 'float',
        'expected_range': (0.0, 1.0),
        'description': 'Vegas baseline home WP (0-1)'
    },
    'vegas_wpa': {
        'section': 'Vegas-Adjusted Win Probability',
        'col_type': 'wpa',
        'data_type': 'float',
        # WPA is a delta of WP, so it is theoretically bounded to [-1.0, 1.0]
        'expected_range': (-1.0, 1.0),
        'description': 'Vegas baseline WPA (offense perspective)'
    },
    'vegas_home_wpa': {
        'section': 'Vegas-Adjusted Win Probability',
        'col_type': 'wpa',
        'data_type': 'float',
        # WPA is a delta of WP, so it is theoretically bounded to [-1.0, 1.0]
        'expected_range': (-1.0, 1.0),
        'description': 'Vegas baseline home WPA'
    },
    'spread_line': {
        'section': 'Game-Level Metadata',
        'col_type': 'line',
        'data_type': 'float',
        'expected_range': (-20.0, 20.0),
        'description': 'Closing spread (home team perspective)'
    },
    'total_line': {
        'section': 'Game-Level Metadata',
        'col_type': 'line',
        'data_type': 'float',
        # Totals can drift below 35 in low-scoring/weather spots; keep this a bit wider.
        'expected_range': (32.0, 65.0),
        'description': 'Closing over/under line'
    }
}


# ============================================================================
# ANALYSIS ENGINE
# ============================================================================

class OddsDataAnalyzer:
    """
    Analyze odds-related columns in play-by-play data.
    
    Follows DI pattern (2 complexity points):
    - Injectable: bucket_adapter, logger
    - Business logic: statistical analysis and reporting
    """
    
    def __init__(self, bucket_adapter, logger):
        """
        Initialize analyzer with dependencies.
        
        Args:
            bucket_adapter: Bucket data access adapter
            logger: Logging instance
        """
        self.bucket = bucket_adapter
        self.logger = logger
        self.df = None
        self.analysis_results = {}
        self.start_time = None
        self.game_summary = None
        self.week_summary = None
        
    def load_data(self, season: int) -> bool:
        """
        Load play-by-play data from bucket for specified season.
        
        Args:
            season: NFL season year
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Loading play_by_play data for {season} season...")
            
            self.df = self.bucket.read_data(
                table_name=TABLE_NAME,
                schema=BUCKET_SCHEMA,
                filters=[('season', '==', season)]
            )
            
            if self.df.empty:
                self.logger.error(f"No data found for {season} season")
                return False
                
            self.logger.info(f"✓ Loaded {len(self.df):,} plays from {season} season")
            self.logger.info(f"  Columns available: {len(self.df.columns)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load data from bucket: {e}", exc_info=True)
            return False
    
    def analyze_population(self, col: str) -> Dict[str, Any]:
        """
        Analyze population metrics for a column.
        
        Args:
            col: Column name
            
        Returns:
            dict: Population statistics
        """
        total = len(self.df)
        non_null = self.df[col].notna().sum()
        null_count = self.df[col].isna().sum()
        
        return {
            'total_rows': total,
            'non_null_count': int(non_null),
            'null_count': int(null_count),
            'population_pct': round((non_null / total) * 100, 2) if total > 0 else 0
        }
    
    def compute_statistics(self, series: pd.Series) -> Dict[str, float]:
        """
        Compute statistical summary for numerical series.
        
        Args:
            series: Pandas series to analyze
            
        Returns:
            dict: Statistical measures
        """
        series_clean = series.dropna()
        
        if len(series_clean) == 0:
            return {'error': 'No non-null values'}
        
        return {
            'mean': round(float(series_clean.mean()), 4),
            'median': round(float(series_clean.median()), 4),
            'std': round(float(series_clean.std()), 4),
            'min': round(float(series_clean.min()), 4),
            'max': round(float(series_clean.max()), 4),
            'q1': round(float(series_clean.quantile(0.25)), 4),
            'q3': round(float(series_clean.quantile(0.75)), 4),
            'skewness': round(float(series_clean.skew()), 4),
            'kurtosis': round(float(series_clean.kurtosis()), 4)
        }
    
    
    def detect_anomalies(
        self,
        series: pd.Series,
        expected_range: Tuple[float, float],
        col_type: str
    ) -> Tuple[List[str], List[str]]:
        """
        Detect data-quality anomalies and return (anomalies, notes).

        - anomalies: likely data problems (range violations, inf, etc.)
        - notes: informational flags that should NOT degrade the quality score
        """
        anomalies: List[str] = []
        notes: List[str] = []
        series_clean = series.dropna()

        if len(series_clean) == 0:
            return anomalies, notes

        cfg = COLUMN_TYPE_CONFIGS.get(col_type, COLUMN_TYPE_CONFIGS['wp'])

        # ------------------------------------------------------------------
        # Hard range violations (true data-quality issues)
        # ------------------------------------------------------------------
        below_min = int((series_clean < expected_range[0]).sum())
        above_max = int((series_clean > expected_range[1]).sum())

        if below_min > 0:
            anomalies.append(f"{below_min} values below expected min {expected_range[0]}")
        if above_max > 0:
            anomalies.append(f"{above_max} values above expected max {expected_range[1]}")

        # ------------------------------------------------------------------
        # WPA: treat heavy tails as "high-leverage" notes (not outliers)
        # ------------------------------------------------------------------
        if col_type == 'wpa':
            hl = cfg.get('high_leverage_threshold', 0.15)
            extreme = cfg.get('extreme_threshold', 0.30)

            high_leverage = int((series_clean.abs() > hl).sum())
            extreme_leverage = int((series_clean.abs() > extreme).sum())

            if high_leverage > 0:
                notes.append(f"{high_leverage} high-leverage plays (|WPA| > {hl})")
            if extreme_leverage > 0:
                notes.append(f"{extreme_leverage} extreme plays (|WPA| > {extreme})")

            # Skip generic IQR / 3σ detection for WPA by default
            inf_count = int(np.isinf(series_clean).sum())
            if inf_count > 0:
                anomalies.append(f"{inf_count} infinite values")

            return anomalies, notes

        # ------------------------------------------------------------------
        # Generic outlier detection (lines / WP): IQR and 3σ
        # ------------------------------------------------------------------
        if cfg.get('use_iqr', True):
            q1 = float(series_clean.quantile(0.25))
            q3 = float(series_clean.quantile(0.75))
            iqr = q3 - q1
            mult = cfg.get('iqr_multiplier', 1.5)

            if iqr > 0:
                outliers = int(((series_clean < (q1 - mult * iqr)) | (series_clean > (q3 + mult * iqr))).sum())
                if outliers > QUALITY_THRESHOLDS['outlier_warning_count']:
                    anomalies.append(f"{outliers} IQR outliers detected")

        if cfg.get('use_3sigma', True) and series_clean.std() > 0:
            mean = float(series_clean.mean())
            std = float(series_clean.std())
            k = cfg.get('sigma_multiplier', 3.0)
            stat_outliers = int(((series_clean < (mean - k*std)) | (series_clean > (mean + k*std))).sum())
            if stat_outliers > 0:
                anomalies.append(f"{stat_outliers} values beyond {k}σ")

        inf_count = int(np.isinf(series_clean).sum())
        if inf_count > 0:
            anomalies.append(f"{inf_count} infinite values")

        return anomalies, notes
    
    def analyze_distribution(self, series: pd.Series) -> Dict[str, Any]:
        """
        Analyze value distribution for series.
        
        Args:
            series: Pandas series to analyze
            
        Returns:
            dict: Distribution metrics
        """
        series_clean = series.dropna()
        
        if len(series_clean) == 0:
            return {'error': 'No non-null values'}
        
        # Value counts (top 10)
        value_counts = series_clean.value_counts().head(10)
        top_10 = {str(k): int(v) for k, v in value_counts.items()}
        
        # Histogram (10 bins)
        try:
            hist, bin_edges = np.histogram(series_clean, bins=10)
            histogram = {
                'counts': hist.tolist(),
                'edges': np.round(bin_edges, 4).tolist()
            }
        except Exception as e:
            self.logger.warning(f"Histogram generation failed: {e}")
            histogram = {'error': str(e)}
        
        return {
            'unique_values': int(series_clean.nunique()),
            'mode': float(series_clean.mode().iloc[0]) if len(series_clean.mode()) > 0 else None,
            'top_10_values': top_10,
            'histogram': histogram
        }
    
    
    def assess_quality(self, population_pct: float, anomalies: List[str], col_type: str) -> str:
        """
        Assess overall quality status for a column.

        Rules of thumb:
        - Null rate is handled explicitly via QUALITY_THRESHOLDS.
        - Range violations / inf are treated as CRITICAL.
        - Generic outlier flags (IQR / σ) are WARN-level signals for non-WPA columns.
        """
        null_pct = 100.0 - population_pct

        # Null-driven quality
        if null_pct > QUALITY_THRESHOLDS['null_critical_pct']:
            return 'CRITICAL'
        if null_pct > QUALITY_THRESHOLDS['null_warning_pct']:
            return 'WARN'

        # Hard anomalies (range / inf) => critical
        hard_markers = ('values below expected min', 'values above expected max', 'infinite values')
        if any(any(marker in a for marker in hard_markers) for a in anomalies):
            return 'CRITICAL'

        # Remaining anomalies are usually distributional
        if len(anomalies) > 0:
            return 'WARN'

        return 'GOOD'
    
    def analyze_column(self, col_name: str, col_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on a single column.
        
        Args:
            col_name: Column name
            col_spec: Column specification dict
            
        Returns:
            dict: Complete analysis results
        """
        self.logger.info(f"Analyzing column: {col_name}")
        
        # Check if column exists
        if col_name not in self.df.columns:
            self.logger.warning(f"  Column '{col_name}' not found in dataset - SKIPPED")
            return {
                'name': col_name,
                'status': 'MISSING',
                'section': col_spec['section'],
                'description': col_spec['description']
            }
        
        try:
            # Population analysis
            population = self.analyze_population(col_name)
            self.logger.debug(f"  Population: {population['population_pct']:.2f}%")
            
            # Statistical analysis
            series = self.df[col_name]
            statistics = self.compute_statistics(series)
            
            # Anomaly detection
            col_type = col_spec.get('col_type', 'wp')
            anomalies, notes = self.detect_anomalies(series, col_spec['expected_range'], col_type)
            
            # Distribution analysis
            distribution = self.analyze_distribution(series)
            
            # Quality assessment
            quality_status = self.assess_quality(population['population_pct'], anomalies, col_type)
            self.logger.debug(f"  Quality: {quality_status}")
            
            if quality_status == 'WARN':
                self.logger.warning(f"  {col_name}: Quality issues detected")
            elif quality_status == 'CRITICAL':
                self.logger.error(f"  {col_name}: Critical quality issues")
            
            return {
                'name': col_name,
                'section': col_spec['section'],
                'description': col_spec['description'],
                'data_type': col_spec['data_type'],
                'expected_range': col_spec['expected_range'],
                'population': population,
                'statistics': statistics,
                'distribution': distribution,
                'quality': {
                    'status': quality_status,
                    'anomalies': anomalies,
                    'notes': notes
                }
            }
            
        except Exception as e:
            self.logger.error(f"  Analysis failed for {col_name}: {e}", exc_info=True)
            return {
                'name': col_name,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def analyze_all(self) -> None:
        """Analyze all odds columns and store results."""
        self.logger.info(f"=== Starting analysis of {len(ODDS_COLUMNS)} odds columns ===")
        self.start_time = datetime.now()
        
        for col_name, col_spec in ODDS_COLUMNS.items():
            result = self.analyze_column(col_name, col_spec)
            self.analysis_results[col_name] = result
        
        runtime = (datetime.now() - self.start_time).total_seconds()
        self.logger.info(f"=== Analysis complete in {runtime:.1f} seconds ===")
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics across all analyzed columns.
        
        Returns:
            dict: Summary metrics
        """
        total_columns = len(self.analysis_results)
        columns_with_issues = sum(
            1 for r in self.analysis_results.values()
            if r.get('quality', {}).get('status') in ['WARN', 'CRITICAL']
        )
        
        total_nulls = sum(
            r.get('population', {}).get('null_count', 0)
            for r in self.analysis_results.values()
        )
        
        # Overall quality (worst status found)
        statuses = [r.get('quality', {}).get('status', 'UNKNOWN') for r in self.analysis_results.values()]
        if 'CRITICAL' in statuses:
            overall_quality = 'CRITICAL'
        elif 'WARN' in statuses:
            overall_quality = 'WARN'
        else:
            overall_quality = 'GOOD'
        
        return {
            'columns_analyzed': total_columns,
            'overall_quality': overall_quality,
            'columns_with_issues': columns_with_issues,
            'total_null_values': total_nulls
        }
    
    def generate_markdown_report(self) -> str:
        """
        Generate comprehensive markdown report.
        
        Returns:
            str: Markdown formatted report
        """
        summary = self.generate_summary()
        runtime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        lines = []
        lines.append("# Play-by-Play Odds Data Analysis Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Script**: {Path(__file__).name}")
        lines.append(f"**Season**: {SEASON}")
        lines.append(f"**Total Plays Analyzed**: {len(self.df):,}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Odds Columns Analyzed | {summary['columns_analyzed']} |")
        lines.append(f"| Overall Quality Score | {summary['overall_quality']} |")
        lines.append(f"| Columns with Quality Issues | {summary['columns_with_issues']} |")
        lines.append(f"| Total Null Values | {summary['total_null_values']:,} |")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Column Analysis
        lines.append("## Column Analysis")
        lines.append("")
        
        for idx, (col_name, result) in enumerate(self.analysis_results.items(), 1):
            lines.append(f"### {idx}. {col_name} ({result.get('section', 'Unknown')})")
            lines.append("")
            
            if result.get('status') == 'MISSING':
                lines.append("**Status**: ❌ Column not found in dataset")
                lines.append("")
                continue
            
            if result.get('status') == 'ERROR':
                lines.append(f"**Status**: ❌ Analysis error: {result.get('error')}")
                lines.append("")
                continue
            
            lines.append(f"**Description**: {result['description']}")
            lines.append("")
            
            # Population
            pop = result['population']
            lines.append("**Population Metrics**:")
            lines.append(f"- Total Plays: {pop['total_rows']:,}")
            lines.append(f"- Non-Null: {pop['non_null_count']:,} ({pop['population_pct']:.2f}%)")
            lines.append(f"- Null: {pop['null_count']:,} ({100-pop['population_pct']:.2f}%)")
            lines.append("")
            
            # Statistics
            stats = result['statistics']
            if 'error' not in stats:
                lines.append("**Statistical Summary**:")
                lines.append("```")
                lines.append(f"Mean:     {stats['mean']:>8.4f}    Median:   {stats['median']:>8.4f}")
                lines.append(f"Std Dev:  {stats['std']:>8.4f}    Min:      {stats['min']:>8.4f}")
                lines.append(f"Max:      {stats['max']:>8.4f}    Q1:       {stats['q1']:>8.4f}")
                lines.append(f"Q3:       {stats['q3']:>8.4f}")
                lines.append("```")
                lines.append("")
            
            # Distribution
            dist = result['distribution']
            if 'error' not in dist:
                lines.append("**Distribution**:")
                lines.append(f"- Unique Values: {dist['unique_values']}")
                if dist['mode'] is not None:
                    lines.append(f"- Mode: {dist['mode']}")
                
                if dist['top_10_values']:
                    lines.append("- Most Common:")
                    for rank, (val, count) in enumerate(list(dist['top_10_values'].items())[:3], 1):
                        lines.append(f"  {rank}. {val}: {count:,} plays")
                lines.append("")
            
            # Quality Assessment
            quality = result['quality']
            status_icon = {'GOOD': '✓', 'WARN': '⚠', 'CRITICAL': '❌'}.get(quality['status'], '?')
            lines.append(f"**Quality Assessment**: {status_icon} {quality['status']}")
            
            if quality.get('anomalies'):
                lines.append("- Anomalies detected:")
                for anomaly in quality['anomalies']:
                    lines.append(f"  - {anomaly}")
            else:
                lines.append("- No anomalies detected")

            # Informational notes (e.g., high-leverage WPA plays)
            if quality.get('notes'):
                lines.append("- Notes:")
                for note in quality['notes']:
                    lines.append(f"  - {note}")

            lines.append(f"- Values within expected range {result['expected_range']}")
          
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Recommendations
        
        # Game / Week Level Diagnostics
        self._ensure_game_week_summaries()
        if self.game_summary is not None and not self.game_summary.empty:
            lines.append("## Game-Level Diagnostics")
            lines.append("")
            lines.append("These rollups help localize issues (nulls, extreme leverage, reconciliation drift) to specific games.")
            lines.append("")

            # Top reconciliation errors (home)
            if 'abs_recon_error_home' in self.game_summary.columns:
                top_recon = self.game_summary.dropna(subset=['abs_recon_error_home']).sort_values('abs_recon_error_home', ascending=False)
                lines.append("### Top games by |recon_error_home|")
                lines.append("")
                lines.extend(self._df_to_markdown_table(
                    top_recon,
                    columns=['game_id','week','home_team','away_team','n_plays','abs_recon_error_home','recon_error_home','sum_vegas_home_wpa','delta_vegas_home_wp'],
                    max_rows=10
                ))
                lines.append("")

            # Null WPA concentration
            if 'null_vegas_wpa' in self.game_summary.columns:
                top_null = self.game_summary.sort_values('null_vegas_wpa', ascending=False)
                lines.append("### Top games by null vegas_wpa")
                lines.append("")
                lines.extend(self._df_to_markdown_table(
                    top_null,
                    columns=['game_id','week','home_team','away_team','n_plays','null_vegas_wpa','pop_vegas_wpa_pct','null_vegas_wp','pop_vegas_wp_pct'],
                    max_rows=10
                ))
                lines.append("")

            # Extreme WPA plays
            if 'extreme_vegas_home_wpa' in self.game_summary.columns:
                top_ext = self.game_summary.sort_values('extreme_vegas_home_wpa', ascending=False)
                lines.append("### Top games by extreme home WPA plays (|WPA| > 0.30)")
                lines.append("")
                lines.extend(self._df_to_markdown_table(
                    top_ext,
                    columns=['game_id','week','home_team','away_team','n_plays','extreme_vegas_home_wpa','high_leverage_vegas_home_wpa','max_abs_vegas_home_wpa'],
                    max_rows=10
                ))
                lines.append("")

        if self.week_summary is not None and not self.week_summary.empty:
            lines.append("## Week-to-Week Diagnostics")
            lines.append("")
            lines.append("Week-level aggregates highlight clustering (e.g., null spikes or reconciliation drift in a specific week).")
            lines.append("")
            week_view = self.week_summary.copy()
            # Prefer numeric sorting of week if possible
            if 'week' in week_view.columns:
                try:
                    week_view = week_view.sort_values('week')
                except Exception:
                    pass
            lines.extend(self._df_to_markdown_table(
                week_view,
                columns=[
                    'week','n_games','n_plays',
                    'null_vegas_wpa','null_vegas_wp',
                    'high_leverage_vegas_home_wpa','extreme_vegas_home_wpa',
                    'abs_recon_error_home_p95','abs_recon_error_home_max','abs_recon_error_home_gt_0p05'
                ],
                max_rows=25
            ))
            lines.append("")
        lines.append("## Recommendations")
        lines.append("")
        
        warn_cols = [name for name, r in self.analysis_results.items() 
                     if r.get('quality', {}).get('status') == 'WARN']
        critical_cols = [name for name, r in self.analysis_results.items() 
                        if r.get('quality', {}).get('status') == 'CRITICAL']
        
        if critical_cols or warn_cols:
            lines.append("### Data Quality Priorities")
            for col in critical_cols:
                result = self.analysis_results[col]
                pop_pct = result.get('population', {}).get('population_pct', 0)
                lines.append(f"1. **{col}**: CRITICAL - {100-pop_pct:.2f}% missing")
            for col in warn_cols:
                result = self.analysis_results[col]
                anomalies = result.get('quality', {}).get('anomalies', [])
                if anomalies:
                    lines.append(f"2. **{col}**: Review {len(anomalies)} anomaly types")
            lines.append("")
        else:
            lines.append("### Data Quality Status")
            lines.append("✓ All odds columns show good data quality")
            lines.append("")
        
        # Appendix
        lines.append("---")
        lines.append("")
        lines.append("## Appendix: Methodology")
        lines.append("")
        lines.append(f"**Analysis performed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total runtime**: {runtime:.1f} seconds")
        lines.append(f"**Bucket source**: `{BUCKET_SCHEMA}.{TABLE_NAME}` (season={SEASON})")
        lines.append("")
        lines.append("**Quality Thresholds**:")
        lines.append("- GOOD: >95% populated, no critical anomalies")
        lines.append("- WARN: 80-95% populated OR minor anomalies")
        lines.append("- CRITICAL: <80% populated OR multiple severe anomalies")
        
        return "\n".join(lines)
    
    def generate_json_output(self) -> Dict[str, Any]:
        """
        Generate JSON-serializable output.
        
        Returns:
            dict: Complete analysis results
        """
        summary = self.generate_summary()
        runtime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        # Attach optional game/week rollups (small, debuggable slices)
        self._ensure_game_week_summaries()

        game_rollup = {}
        if self.game_summary is not None and not self.game_summary.empty:
            if 'abs_recon_error_home' in self.game_summary.columns:
                top_recon = (self.game_summary.dropna(subset=['abs_recon_error_home'])
                             .sort_values('abs_recon_error_home', ascending=False)
                             .head(20))
                game_rollup['top_abs_recon_error_home'] = top_recon.to_dict(orient='records')
            if 'null_vegas_wpa' in self.game_summary.columns:
                top_null = (self.game_summary.sort_values('null_vegas_wpa', ascending=False)
                            .head(20))
                game_rollup['top_null_vegas_wpa'] = top_null.to_dict(orient='records')

        week_rollup = {}
        if self.week_summary is not None and not self.week_summary.empty:
            week_rollup['rows'] = self.week_summary.to_dict(orient='records')

        
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'script': Path(__file__).name,
                'season': SEASON,
                'total_plays': len(self.df),
                'runtime_seconds': round(runtime, 2)
            },
            'summary': summary,
            'columns': list(self.analysis_results.values()),
            'game_rollup': game_rollup,
            'week_rollup': week_rollup
        }
    
    def export_csv(self) -> str:
        """
        Export odds columns to CSV with context columns.
        
        Returns:
            str: Path to exported CSV file
        """
        # Context columns for reference
        context_cols = [
            'game_id','play_id','season','week',
            'game_date','qtr','down','ydstogo','yardline_100',
            'posteam','defteam','score_differential','total_home_score','total_away_score',
            'play_type','desc'
        ]
        
        # Available odds columns
        odds_cols = [col for col in ODDS_COLUMNS.keys() if col in self.df.columns]
        
        # Combine
        export_cols = [col for col in context_cols if col in self.df.columns] + odds_cols
        
        # Export
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pbp_odds_columns_{SEASON}_{timestamp}.csv"
        filepath = DATA_DIR / filename
        
        self.logger.info(f"Exporting {len(export_cols)} columns to CSV...")
        
        self.df[export_cols].to_csv(filepath, index=False)
        
        self.logger.info(f"✓ Exported {len(self.df):,} rows to: {filepath}")
        
        return str(filepath)


    def export_anomaly_csv(self) -> str:
        """
        Export a compact CSV of potentially interesting rows for investigation.

        Focus:
        - WPA rows with large absolute values (high leverage)
        - Any theoretical range violations
        - Rows where WPA is null (to study missingness patterns)

        Returns:
            str: Path to exported CSV file
        """
        # Only proceed if we have the relevant cols
        if self.df is None or self.df.empty:
            return ""

        cols_needed = [
            'game_id','play_id','season','week','game_date','qtr','down','ydstogo','yardline_100',
            'posteam','defteam','score_differential','total_home_score','total_away_score',
            'play_type','desc',
            'vegas_wp','vegas_home_wp','vegas_wpa','vegas_home_wpa',
            'spread_line','total_line'
        ]
        cols_available = [c for c in cols_needed if c in self.df.columns]

        df = self.df[cols_available].copy()

        # Build masks safely (only if columns exist)
        masks = []

        if 'vegas_wpa' in df.columns:
            cfg = COLUMN_TYPE_CONFIGS['wpa']
            hl = cfg.get('high_leverage_threshold', 0.15)
            masks.append(df['vegas_wpa'].abs() > hl)
            masks.append(df['vegas_wpa'].isna())

        if 'vegas_home_wpa' in df.columns:
            cfg = COLUMN_TYPE_CONFIGS['wpa']
            hl = cfg.get('high_leverage_threshold', 0.15)
            masks.append(df['vegas_home_wpa'].abs() > hl)
            masks.append(df['vegas_home_wpa'].isna())

        if not masks:
            return ""

        interesting = masks[0]
        for mm in masks[1:]:
            interesting = interesting | mm

        out = df.loc[interesting].copy()

        # Export
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pbp_odds_anomalies_{SEASON}_{timestamp}.csv"
        filepath = DATA_DIR / filename

        self.logger.info(f"Exporting anomaly sample ({len(out):,} rows) to CSV...")
        out.to_csv(filepath, index=False)
        self.logger.info(f"✓ Exported anomaly CSV: {filepath}")

        return str(filepath)
    
    
    # ------------------------------------------------------------------------
    # GAME / WEEK LEVEL SUMMARIES
    # ------------------------------------------------------------------------

    def _ensure_game_week_summaries(self) -> None:
        """Compute game/week summaries if not already computed."""
        if self.game_summary is None:
            self.game_summary = self.compute_game_summary()
        if self.week_summary is None:
            self.week_summary = self.compute_week_summary(self.game_summary)

    def compute_game_summary(self) -> pd.DataFrame:
        """Compute game-level aggregates for debugging and validation."""
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        df = self.df.copy()

        # Ensure we have required identifiers
        if 'game_id' not in df.columns:
            return pd.DataFrame()

        # Ordering: prefer game_seconds_remaining (higher earlier), then play_id
        sort_cols = []
        if 'game_seconds_remaining' in df.columns:
            sort_cols.append('game_seconds_remaining')
        elif 'half_seconds_remaining' in df.columns:
            sort_cols.append('half_seconds_remaining')
        elif 'quarter_seconds_remaining' in df.columns:
            sort_cols.append('quarter_seconds_remaining')

        # Add qtr if present as a stable tiebreaker
        if 'qtr' in df.columns:
            sort_cols.append('qtr')

        if 'play_id' in df.columns:
            sort_cols.append('play_id')

        # Build sort directions: seconds remaining desc (earlier in game), qtr asc, play_id asc
        ascending = []
        for c in sort_cols:
            if c in ('game_seconds_remaining','half_seconds_remaining','quarter_seconds_remaining'):
                ascending.append(False)
            elif c == 'qtr':
                ascending.append(True)
            else:
                ascending.append(True)

        if sort_cols:
            df = df.sort_values(sort_cols, ascending=ascending, kind='mergesort')

        # Thresholds (domain)
        wpa_cfg = COLUMN_TYPE_CONFIGS.get('wpa', {})
        hl = float(wpa_cfg.get('high_leverage_threshold', 0.15))
        ex = float(wpa_cfg.get('extreme_threshold', 0.30))

        # Helper to safely compute first/last non-null
        def first_nonnull(s: pd.Series):
            s2 = s.dropna()
            return s2.iloc[0] if len(s2) else np.nan

        def last_nonnull(s: pd.Series):
            s2 = s.dropna()
            return s2.iloc[-1] if len(s2) else np.nan

        # Build base metadata columns (only if present)
        meta_cols = [c for c in ['season','week','season_type','game_date','home_team','away_team'] if c in df.columns]

        # Group aggregates
        g = df.groupby('game_id', dropna=False)

        out = pd.DataFrame(index=g.size().index)
        out['n_plays'] = g.size().astype(int)

        # Meta: take first value per game for metadata cols
        for c in meta_cols:
            out[c] = g[c].agg(first_nonnull)

        # Null counts
        for c in ['vegas_wp','vegas_wpa','vegas_home_wp','vegas_home_wpa','spread_line','total_line']:
            if c in df.columns:
                out[f'null_{c}'] = g[c].apply(lambda x: int(x.isna().sum()))
                out[f'pop_{c}_pct'] = (1.0 - (out[f'null_{c}'] / out['n_plays'])) * 100.0

        # High leverage counts + extrema
        if 'vegas_wpa' in df.columns:
            out['high_leverage_vegas_wpa'] = g['vegas_wpa'].apply(lambda x: int((x.abs() > hl).sum(skipna=True)))
            out['extreme_vegas_wpa'] = g['vegas_wpa'].apply(lambda x: int((x.abs() > ex).sum(skipna=True)))
            out['max_abs_vegas_wpa'] = g['vegas_wpa'].apply(lambda x: float(x.abs().max(skipna=True)) if x.notna().any() else np.nan)

        if 'vegas_home_wpa' in df.columns:
            out['high_leverage_vegas_home_wpa'] = g['vegas_home_wpa'].apply(lambda x: int((x.abs() > hl).sum(skipna=True)))
            out['extreme_vegas_home_wpa'] = g['vegas_home_wpa'].apply(lambda x: int((x.abs() > ex).sum(skipna=True)))
            out['max_abs_vegas_home_wpa'] = g['vegas_home_wpa'].apply(lambda x: float(x.abs().max(skipna=True)) if x.notna().any() else np.nan)

        # WPA reconciliation check (home model)
        if 'vegas_home_wp' in df.columns and 'vegas_home_wpa' in df.columns:
            out['first_vegas_home_wp'] = g['vegas_home_wp'].agg(first_nonnull)
            out['last_vegas_home_wp'] = g['vegas_home_wp'].agg(last_nonnull)
            out['delta_vegas_home_wp'] = out['last_vegas_home_wp'] - out['first_vegas_home_wp']
            out['sum_vegas_home_wpa'] = g['vegas_home_wpa'].sum(min_count=1)
            out['recon_error_home'] = out['sum_vegas_home_wpa'] - out['delta_vegas_home_wp']
            out['abs_recon_error_home'] = out['recon_error_home'].abs()

        # WPA reconciliation check (overall)
        if 'vegas_wp' in df.columns and 'vegas_wpa' in df.columns:
            out['first_vegas_wp'] = g['vegas_wp'].agg(first_nonnull)
            out['last_vegas_wp'] = g['vegas_wp'].agg(last_nonnull)
            out['delta_vegas_wp'] = out['last_vegas_wp'] - out['first_vegas_wp']
            out['sum_vegas_wpa'] = g['vegas_wpa'].sum(min_count=1)
            out['recon_error'] = out['sum_vegas_wpa'] - out['delta_vegas_wp']
            out['abs_recon_error'] = out['recon_error'].abs()

        # Clean up types
        out = out.reset_index()

        return out

    def compute_week_summary(self, game_summary: pd.DataFrame) -> pd.DataFrame:
        """Compute week-level aggregates from the game summary."""
        if game_summary is None or game_summary.empty:
            return pd.DataFrame()

        # If week is missing, fallback to a single bucket
        if 'week' not in game_summary.columns:
            tmp = game_summary.copy()
            tmp['week'] = np.nan
            game_summary = tmp

        g = game_summary.groupby('week', dropna=False)

        out = pd.DataFrame(index=g.size().index)
        out['n_games'] = g.size().astype(int)
        out['n_plays'] = g['n_plays'].sum(min_count=1)

        # Sum nulls and leverage counts if present
        for c in [col for col in game_summary.columns if col.startswith('null_')]:
            out[c] = g[c].sum(min_count=1)

        for c in ['high_leverage_vegas_wpa','extreme_vegas_wpa','high_leverage_vegas_home_wpa','extreme_vegas_home_wpa']:
            if c in game_summary.columns:
                out[c] = g[c].sum(min_count=1)

        # Recon check summaries
        for c in ['abs_recon_error','abs_recon_error_home']:
            if c in game_summary.columns:
                out[f'{c}_mean'] = g[c].mean()
                out[f'{c}_p95'] = g[c].quantile(0.95)
                out[f'{c}_max'] = g[c].max()
                # count games over small threshold
                out[f'{c}_gt_0p05'] = g[c].apply(lambda x: int((x > 0.05).sum(skipna=True)))

        out = out.reset_index()
        return out

    def export_game_summary_csv(self) -> str:
        """Export game-level summary CSV."""
        self._ensure_game_week_summaries()
        if self.game_summary is None or self.game_summary.empty:
            return ""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pbp_odds_game_summary_{SEASON}_{timestamp}.csv"
        filepath = DATA_DIR / filename
        self.logger.info(f"Exporting game summary ({len(self.game_summary):,} games) to CSV...")
        self.game_summary.to_csv(filepath, index=False)
        self.logger.info(f"✓ Exported game summary CSV: {filepath}")
        return str(filepath)

    def export_week_summary_csv(self) -> str:
        """Export week-level summary CSV."""
        self._ensure_game_week_summaries()
        if self.week_summary is None or self.week_summary.empty:
            return ""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pbp_odds_week_summary_{SEASON}_{timestamp}.csv"
        filepath = DATA_DIR / filename
        self.logger.info(f"Exporting week summary ({len(self.week_summary):,} rows) to CSV...")
        self.week_summary.to_csv(filepath, index=False)
        self.logger.info(f"✓ Exported week summary CSV: {filepath}")
        return str(filepath)

    def _df_to_markdown_table(self, df: pd.DataFrame, columns: List[str], max_rows: int = 10) -> List[str]:
        """Convert a small DataFrame slice to markdown table lines."""
        if df is None or df.empty:
            return ["_No rows._"]
        use_cols = [c for c in columns if c in df.columns]
        if not use_cols:
            return ["_No matching columns._"]
        view = df[use_cols].head(max_rows).copy()
        # string formatting
        for c in use_cols:
            if pd.api.types.is_float_dtype(view[c]):
                view[c] = view[c].map(lambda x: f"{x:.4f}" if pd.notna(x) else "")
        lines = []
        lines.append("| " + " | ".join(use_cols) + " |")
        lines.append("|" + "|".join(["---"] * len(use_cols)) + "|")
        for _, row in view.iterrows():
            vals = [str(row[c]) if pd.notna(row[c]) else "" for c in use_cols]
            lines.append("| " + " | ".join(vals) + " |")
        return lines

    def save_reports(self) -> Dict[str, str]:
        """
        Save all reports to designated directories.
        
        Returns:
            dict: Paths to generated files
        """
        # Ensure directories exist
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Markdown report
        self.logger.info("Generating markdown report...")
        markdown_report = self.generate_markdown_report()
        md_filename = f"pbp_odds_analysis_{timestamp}.md"
        md_path = REPORTS_DIR / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        self.logger.info(f"✓ Markdown report: {md_path}")
        
        # JSON output
        self.logger.info("Generating JSON output...")
        json_output = self.generate_json_output()
        json_filename = f"pbp_odds_analysis_{timestamp}.json"
        json_path = REPORTS_DIR / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=2)
        
        self.logger.info(f"✓ JSON output: {json_path}")
        
        # CSV export
        csv_path = self.export_csv()
        anomaly_csv_path = self.export_anomaly_csv()
        game_summary_csv_path = self.export_game_summary_csv()
        week_summary_csv_path = self.export_week_summary_csv()

        return {
            'markdown': str(md_path),
            'json': str(json_path),
            'csv': csv_path,
            'anomaly_csv': anomaly_csv_path,
            'game_summary_csv': game_summary_csv_path,
            'week_summary_csv': week_summary_csv_path
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    # Setup logging
    logger = get_logger('scripts.analyze_pbp_odds_data')
    
    logger.info("="*60)
    logger.info("PBP Odds Data Analysis Starting")
    logger.info("="*60)
    logger.info(f"Season: {SEASON}")
    logger.info(f"Data source: {BUCKET_SCHEMA}.{TABLE_NAME}")
    logger.info(f"Odds columns to analyze: {len(ODDS_COLUMNS)}")
    
    try:
        # Initialize analyzer with dependencies
        bucket = get_bucket_adapter()
        analyzer = OddsDataAnalyzer(bucket_adapter=bucket, logger=logger)
        
        # Load data
        if not analyzer.load_data(SEASON):
            logger.error("Failed to load data - aborting analysis")
            sys.exit(1)
        
        # Perform analysis
        analyzer.analyze_all()
        
        # Generate and save reports
        logger.info("")
        logger.info("="*60)
        logger.info("Generating Output Files")
        logger.info("="*60)
        
        output_paths = analyzer.save_reports()
        
        # Summary
        summary = analyzer.generate_summary()
        
        logger.info("")
        logger.info("="*60)
        logger.info("Analysis Complete")
        logger.info("="*60)
        logger.info(f"Overall Quality: {summary['overall_quality']}")
        logger.info(f"Columns Analyzed: {summary['columns_analyzed']}")
        logger.info(f"Columns with Issues: {summary['columns_with_issues']}")
        logger.info("")
        logger.info("Output Files:")
        logger.info(f"  Markdown: {output_paths['markdown']}")
        logger.info(f"  JSON: {output_paths['json']}")
        logger.info(f"  CSV: {output_paths['csv']}")
        logger.info(f"  Anomaly CSV: {output_paths.get('anomaly_csv','')}")
        logger.info("="*60)
        
    except KeyboardInterrupt:
        logger.warning("Analysis interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
