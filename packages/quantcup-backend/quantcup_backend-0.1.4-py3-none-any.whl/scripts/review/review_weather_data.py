#!/usr/bin/env python3
"""
Weather Data Review Script

Audits weather data availability in dim_game warehouse table for games across
seasons, weeks, and venues. Analyzes historical weather data already stored
in the bucket.

Note: This script only reviews existing dim_game data. It includes parsing of
weather description strings to recover embedded temp/wind values. For historical
backfill from NOAA NCEI, see weather/historical/. For forecast integration,
see weather/forecasts/.

Usage:
    python scripts/review_weather_data.py --seasons 2023 2024 2025
    python scripts/review_weather_data.py --season 2024 --week 15
    python scripts/review_weather_data.py --all

Reports saved to: C:/Users/acief/Documents/cdrive_projects/quantcup_backend/reports
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from nflfastRv3.shared.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger

# Import shared weather enrichment functions
from weather.transforms.weather_enrichment import enrich_weather

# Initialize logger and bucket
logger = get_logger('weather_data_review')
bucket = get_bucket_adapter()

# Reports directory - use absolute path resolution with domain-based subfolder
REPORTS_BASE_DIR = project_root / "reports"
DOMAIN_FOLDER = "weather_review"
REPORTS_DIR = REPORTS_BASE_DIR / DOMAIN_FOLDER

# TODO: If this script generates multiple artifact types (e.g., CSV + MD + JSON),
# consider using timestamped subfolders: REPORTS_BASE_DIR / f"{DOMAIN_FOLDER}_{timestamp}"
# This groups related artifacts together (see scripts/analyze_pbp_odds_data_v4.py)


# ============================================================================
# Main Reviewer Class
# ============================================================================

class WeatherDataReviewer:
    """
    Comprehensive weather data availability reviewer
    
    Analyzes:
    1. Historical weather in dim_game (temp, wind, weather)
    2. Stadium roof types and weather exposure
    3. Coverage by season, week, and venue
    4. Data quality metrics
    """
    
    def __init__(self):
        self.bucket = get_bucket_adapter()
        self.logger = get_logger('WeatherDataReviewer')
        self.dim_game = None
        self.stadium_registry = None
        self.analysis_results = {}
        
    def load_data(self, seasons: Optional[List[int]] = None, week: Optional[int] = None) -> None:
        """Load dim_game data from bucket and backfill weather from strings"""
        self.logger.info("Loading dim_game from bucket...")
        
        try:
            self.dim_game = self.bucket.read_data('dim_game', 'warehouse')
            
            # Filter by seasons if specified
            if seasons:
                self.dim_game = self.dim_game[self.dim_game['season'].isin(seasons)]
            
            # Filter by week if specified
            if week is not None:
                self.dim_game = self.dim_game[self.dim_game['week'] == week]
            
            self.logger.info(f"Loaded {len(self.dim_game):,} games")
            
            # Load stadium registry first (needed for modeling filter)
            from weather.utils.stadium_registry import NFL_STADIUMS
            self.stadium_registry = NFL_STADIUMS
            
            # Backfill temp/wind from weather strings (using shared module)
            self.logger.info("Backfilling temp/wind from weather description strings...")
            self.dim_game = enrich_weather(self.dim_game)
            
            # Add model-eligible weather columns (exclude indoor/closed games)
            self.logger.info("Creating model-eligible weather columns...")
            self.dim_game = self._filter_weather_for_modeling(self.dim_game)
            
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            raise
    
    def _filter_weather_for_modeling(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create model-eligible weather columns (exclude indoor/closed roof games)
        
        Rules:
        - Fixed domes: NaN (outside weather ≠ gameplay conditions)
        - Retractable closed: NaN
        - Retractable open / outdoor: keep weather
        
        Creates:
        - temp_model: temperature safe for modeling
        - wind_model: wind safe for modeling
        """
        df = df.copy()
        
        df["temp_model"] = df["temp_filled"]
        df["wind_model"] = df["wind_filled"]
        
        for idx, row in df.iterrows():
            stadium_info = self.stadium_registry.get(row['home_team'], {})
            roof_type = stadium_info.get('roof_type', 'unknown')
            dim_game_roof = row.get('roof')
            
            # Fixed domes: always exclude (outside weather doesn't affect indoor play)
            if roof_type == 'fixed_dome':
                df.at[idx, "temp_model"] = np.nan
                df.at[idx, "wind_model"] = np.nan
            
            # Retractables: only include if explicitly open
            elif roof_type == 'retractable' and dim_game_roof != 'open':
                df.at[idx, "temp_model"] = np.nan
                df.at[idx, "wind_model"] = np.nan
        
        model_eligible = df[['temp_model']].notna().sum().sum()
        self.logger.info(f"Model-eligible weather: {model_eligible} games (excludes fixed domes and closed retractables)")
        
        return df
    
    def analyze_weather_coverage(self) -> Dict:
        """
        Analyze weather data coverage across all games
        
        Uses temp_filled/wind_filled which includes parsed values from weather strings.
        
        Returns:
            Dict with coverage statistics
        """
        self.logger.info("Analyzing weather data coverage...")
        
        df = self.dim_game.copy()
        
        # Total games
        total_games = len(df)
        
        # Weather field availability (using filled columns)
        temp_available = df['temp_filled'].notna().sum()
        wind_available = df['wind_filled'].notna().sum()
        weather_available = df['weather'].notna().sum()
        
        # Provenance tracking (3 buckets + metrics)
        structured_both = (df['weather_provenance'] == 'structured_both').sum()
        mixed_count = (df['weather_provenance'] == 'mixed_structured+parsed').sum()
        parsed_both = (df['weather_provenance'] == 'parsed_both').sum()
        
        parsing_used = df['parsing_used'].sum()
        parsing_attempted = df['parsing_attempted'].sum()
        malformed_count = df['is_malformed_weather_string'].sum()
        
        # Games with ANY weather data
        any_weather = df[
            df['temp_filled'].notna() | df['wind_filled'].notna() | df['weather'].notna()
        ].shape[0]
        
        # Games with COMPLETE weather data
        complete_weather = df[
            df['temp_filled'].notna() & df['wind_filled'].notna()
        ].shape[0]
        
        # Outdoor vs indoor games (using dim_game.roof)
        outdoor_games = df[df['roof'].isin(['outdoors', 'open'])].shape[0]
        dome_games = df[df['roof'] == 'dome'].shape[0]
        retractable_games = df[df['roof'] == 'retractable'].shape[0]
        missing_roof_info = df[df['roof'].isna()].shape[0]
        
        results = {
            'total_games': total_games,
            'temp_available': temp_available,
            'temp_coverage_pct': (temp_available / total_games * 100) if total_games > 0 else 0,
            'wind_available': wind_available,
            'wind_coverage_pct': (wind_available / total_games * 100) if total_games > 0 else 0,
            'weather_desc_available': weather_available,
            'weather_desc_coverage_pct': (weather_available / total_games * 100) if total_games > 0 else 0,
            'any_weather_data': any_weather,
            'any_weather_pct': (any_weather / total_games * 100) if total_games > 0 else 0,
            'complete_weather_data': complete_weather,
            'complete_weather_pct': (complete_weather / total_games * 100) if total_games > 0 else 0,
            # New granular provenance (3 buckets)
            'structured_both': structured_both,
            'mixed_count': mixed_count,
            'parsed_both': parsed_both,
            'parsing_used': parsing_used,
            'parsing_attempted': parsing_attempted,
            'parsing_used_pct': (parsing_used / total_games * 100) if total_games > 0 else 0,
            'malformed_strings': malformed_count,
            'malformed_pct': (malformed_count / total_games * 100) if total_games > 0 else 0,
            'outdoor_games': outdoor_games,
            'dome_games': dome_games,
            'retractable_games': retractable_games,
            'missing_roof_info': missing_roof_info,
        }
        
        self.analysis_results['coverage'] = results
        return results
    
    def analyze_by_season(self) -> pd.DataFrame:
        """Analyze weather data availability by season (using filled values)"""
        self.logger.info("Analyzing weather coverage by season...")
        
        df = self.dim_game.copy()
        
        season_stats = []
        for season in sorted(df['season'].unique()):
            season_df = df[df['season'] == season]
            total = len(season_df)
            
            stats = {
                'season': season,
                'total_games': total,
                'temp_available': season_df['temp_filled'].notna().sum(),
                'temp_pct': (season_df['temp_filled'].notna().sum() / total * 100) if total > 0 else 0,
                'wind_available': season_df['wind_filled'].notna().sum(),
                'wind_pct': (season_df['wind_filled'].notna().sum() / total * 100) if total > 0 else 0,
                'weather_available': season_df['weather'].notna().sum(),
                'weather_pct': (season_df['weather'].notna().sum() / total * 100) if total > 0 else 0,
                'outdoor_games': season_df[season_df['roof'].isin(['outdoors', 'open'])].shape[0],
                'avg_temp': season_df['temp_filled'].mean() if season_df['temp_filled'].notna().any() else None,
                'avg_wind': season_df['wind_filled'].mean() if season_df['wind_filled'].notna().any() else None,
            }
            season_stats.append(stats)
        
        season_df = pd.DataFrame(season_stats)
        self.analysis_results['by_season'] = season_df
        return season_df
    
    def analyze_by_week(self, season: Optional[int] = None) -> pd.DataFrame:
        """Analyze weather data availability by week (using filled values)"""
        self.logger.info(f"Analyzing weather coverage by week (season={season or 'all'})...")
        
        df = self.dim_game.copy()
        
        if season:
            df = df[df['season'] == season]
        
        week_stats = []
        for week in sorted(df['week'].unique()):
            week_df = df[df['week'] == week]
            total = len(week_df)
            
            stats = {
                'week': week,
                'total_games': total,
                'temp_available': week_df['temp_filled'].notna().sum(),
                'temp_pct': (week_df['temp_filled'].notna().sum() / total * 100) if total > 0 else 0,
                'wind_available': week_df['wind_filled'].notna().sum(),
                'wind_pct': (week_df['wind_filled'].notna().sum() / total * 100) if total > 0 else 0,
                'complete_weather': week_df[week_df['temp_filled'].notna() & week_df['wind_filled'].notna()].shape[0],
                'complete_pct': (week_df[week_df['temp_filled'].notna() & week_df['wind_filled'].notna()].shape[0] / total * 100) if total > 0 else 0,
            }
            week_stats.append(stats)
        
        week_df = pd.DataFrame(week_stats)
        self.analysis_results['by_week'] = week_df
        return week_df
    
    def analyze_by_venue(self) -> pd.DataFrame:
        """Analyze weather data by venue (stadium/team) using filled values"""
        self.logger.info("Analyzing weather coverage by venue...")
        
        df = self.dim_game.copy()
        
        venue_stats = []
        for team in sorted(df['home_team'].unique()):
            team_df = df[df['home_team'] == team]
            total = len(team_df)
            
            # Get stadium info from registry
            stadium_info = self.stadium_registry.get(team, {})
            roof_type = stadium_info.get('roof_type', 'unknown')
            stadium_name = stadium_info.get('name', 'Unknown')
            
            stats = {
                'team': team,
                'stadium': stadium_name,
                'roof_type': roof_type,
                'total_games': total,
                'temp_available': team_df['temp_filled'].notna().sum(),
                'temp_pct': (team_df['temp_filled'].notna().sum() / total * 100) if total > 0 else 0,
                'wind_available': team_df['wind_filled'].notna().sum(),
                'wind_pct': (team_df['wind_filled'].notna().sum() / total * 100) if total > 0 else 0,
                'avg_temp': team_df['temp_filled'].mean() if team_df['temp_filled'].notna().any() else None,
                'avg_wind': team_df['wind_filled'].mean() if team_df['wind_filled'].notna().any() else None,
                'weather_exposed': roof_type in ['open', 'retractable'],
            }
            venue_stats.append(stats)
        
        venue_df = pd.DataFrame(venue_stats)
        self.analysis_results['by_venue'] = venue_df
        return venue_df
    
    def analyze_data_quality(self) -> Dict:
        """Analyze weather data quality issues (using filled values and NFL-impact thresholds)"""
        self.logger.info("Analyzing data quality...")
        
        df = self.dim_game.copy()
        
        # Outdoor games without weather data (potential issue) - using filled values
        outdoor_games = df[df['roof'].isin(['outdoors', 'open'])]
        outdoor_missing_weather = outdoor_games[
            outdoor_games['temp_filled'].isna() & outdoor_games['wind_filled'].isna()
        ]
        
        # NFL Impact Thresholds (not meteorological extremes)
        # Temperature
        freezing_games = df[df['temp_filled'] <= 32].shape[0]
        impactful_cold = df[df['temp_filled'] < 20].shape[0]  # Ball handling, gameplans
        meteorological_extreme_cold = df[df['temp_filled'] < 0].shape[0]
        extreme_hot = df[df['temp_filled'] > 100].shape[0]
        
        # Wind
        impactful_wind = df[df['wind_filled'] > 15].shape[0]  # Passing accuracy
        high_wind = df[df['wind_filled'] > 20].shape[0]  # Game plan changes  
        extreme_wind = df[df['wind_filled'] > 30].shape[0]  # Rare
        
        # Recent games (2023+) missing weather
        recent_df = df[df['season'] >= 2023]
        recent_outdoor = recent_df[recent_df['roof'].isin(['outdoors', 'open'])]
        recent_missing = recent_outdoor[
            recent_outdoor['temp_filled'].isna() & recent_outdoor['wind_filled'].isna()
        ]
        
        quality = {
            'outdoor_games_total': len(outdoor_games),
            'outdoor_missing_weather': len(outdoor_missing_weather),
            'outdoor_missing_pct': (len(outdoor_missing_weather) / len(outdoor_games) * 100) if len(outdoor_games) > 0 else 0,
            # NFL Impact Temperature
            'freezing_games': freezing_games,
            'impactful_cold_games': impactful_cold,
            'meteorological_extreme_cold': meteorological_extreme_cold,
            'extreme_hot_games': extreme_hot,
            # NFL Impact Wind
            'impactful_wind_games': impactful_wind,
            'high_wind_games': high_wind,
            'extreme_wind_games': extreme_wind,
            # Recent games
            'recent_outdoor_games': len(recent_outdoor),
            'recent_missing_weather': len(recent_missing),
            'recent_missing_pct': (len(recent_missing) / len(recent_outdoor) * 100) if len(recent_outdoor) > 0 else 0,
        }
        
        self.analysis_results['quality'] = quality
        return quality
    
    def get_sample_games(self, criteria: str = 'missing', limit: int = 10) -> pd.DataFrame:
        """Get sample games matching criteria (using filled values)"""
        df = self.dim_game.copy()
        
        if criteria == 'missing':
            # Outdoor games missing weather (even after parsing)
            sample = df[
                df['roof'].isin(['outdoors', 'open']) &
                df['temp_filled'].isna() &
                df['wind_filled'].isna()
            ].head(limit)
        elif criteria == 'extreme_cold':
            sample = df[df['temp_filled'] < 20].head(limit)
        elif criteria == 'extreme_wind':
            sample = df[df['wind_filled'] > 20].head(limit)
        elif criteria == 'complete':
            sample = df[
                df['temp_filled'].notna() &
                df['wind_filled'].notna() &
                df['weather'].notna()
            ].head(limit)
        else:
            sample = df.head(limit)
        
        return sample[['game_id', 'season', 'week', 'home_team', 'away_team', 
                      'roof', 'temp_filled', 'wind_filled', 'weather', 'weather_provenance']]
    
    def analyze_roof_vocabulary(self) -> Dict:
        """Audit roof type vocabulary mismatches between dim_game and stadium registry"""
        self.logger.info("Auditing roof vocabulary...")
        
        df = self.dim_game.copy()
        
        # dim_game.roof values
        dim_game_roof_counts = df['roof'].value_counts().to_dict()
        
        # Stadium registry roof_type distribution
        registry_roof_counts = defaultdict(int)
        for team in df['home_team'].unique():
            stadium_info = self.stadium_registry.get(team, {})
            roof_type = stadium_info.get('roof_type', 'unknown')
            registry_roof_counts[roof_type] += 1
        
        # Check for retractables/domes with weather data
        retractable_teams = [
            team for team, info in self.stadium_registry.items()
            if info.get('roof_type') == 'retractable'
        ]
        dome_teams = [
            team for team, info in self.stadium_registry.items()
            if info.get('roof_type') == 'fixed_dome'
        ]
        
        retractable_with_weather = df[
            df['home_team'].isin(retractable_teams) &
            (df['temp_filled'].notna() | df['wind_filled'].notna())
        ]
        
        dome_with_weather = df[
            df['home_team'].isin(dome_teams) &
            (df['temp_filled'].notna() | df['wind_filled'].notna())
        ]
        
        result = {
            'dim_game_roof_values': dim_game_roof_counts,
            'registry_roof_types': dict(registry_roof_counts),
            'retractable_teams': retractable_teams,
            'dome_teams': dome_teams,
            'retractable_with_weather_count': len(retractable_with_weather),
            'dome_with_weather_count': len(dome_with_weather),
            'retractable_with_weather_sample': retractable_with_weather[
                ['game_id', 'home_team', 'roof', 'temp_filled', 'wind_filled', 'weather_provenance']
            ].head(5).to_dict('records') if not retractable_with_weather.empty else [],
            'dome_with_weather_sample': dome_with_weather[
                ['game_id', 'home_team', 'roof', 'temp_filled', 'wind_filled', 'weather_provenance']
            ].head(5).to_dict('records') if not dome_with_weather.empty else [],
        }
        
        self.analysis_results['roof_vocabulary'] = result
        return result
    
    def run_full_analysis(self, seasons: Optional[List[int]] = None,
                         specific_week: Optional[int] = None) -> None:
        """Run complete weather data analysis"""
        self.logger.info("Starting full weather data analysis...")
        
        # Load data (filter by week if specified)
        self.load_data(seasons=seasons, week=specific_week)
        
        # Run all analyses
        self.analyze_weather_coverage()
        self.analyze_by_season()
        
        # Only analyze week breakdown if NOT filtering to a specific week
        if specific_week is None:
            season = seasons[0] if seasons and len(seasons) == 1 else None
            self.analyze_by_week(season=season)
        
        self.analyze_by_venue()
        self.analyze_data_quality()
        self.analyze_roof_vocabulary()
        
        self.logger.info("Analysis complete!")
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """Generate comprehensive markdown report"""
        if not self.analysis_results:
            raise ValueError("No analysis results available. Run analysis first.")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_path is None:
            output_path = REPORTS_DIR / f"weather_data_review_{timestamp}.md"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build report
        report_lines = []
        report_lines.append("# Weather Data Review Report")
        report_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"\n**Source:** `dim_game` warehouse table (bucket)")
        report_lines.append("\n---\n")
        
        # Overall Coverage
        report_lines.append("## Overall Coverage\n")
        coverage = self.analysis_results['coverage']
        report_lines.append(f"- **Total Games:** {coverage['total_games']:,}")
        report_lines.append(f"- **Temperature Available:** {coverage['temp_available']:,} ({coverage['temp_coverage_pct']:.1f}%)")
        report_lines.append(f"- **Wind Available:** {coverage['wind_available']:,} ({coverage['wind_coverage_pct']:.1f}%)")
        report_lines.append(f"- **Weather Description:** {coverage['weather_desc_available']:,} ({coverage['weather_desc_coverage_pct']:.1f}%)")
        report_lines.append(f"- **Any Weather Data:** {coverage['any_weather_data']:,} ({coverage['any_weather_pct']:.1f}%)")
        report_lines.append(f"- **Complete Weather Data:** {coverage['complete_weather_data']:,} ({coverage['complete_weather_pct']:.1f}%)")
        report_lines.append("\n### Data Provenance\n")
        report_lines.append(f"- **Structured (both fields):** {coverage['structured_both']:,}")
        report_lines.append(f"- **Mixed (structured + parsed):** {coverage['mixed_count']:,}")
        report_lines.append(f"- **Parsed (both fields):** {coverage['parsed_both']:,}")
        report_lines.append(f"- **Parsing attempted:** {coverage['parsing_attempted']:,} games")
        report_lines.append(f"- **Parsing used:** {coverage['parsing_used']:,} games ({coverage['parsing_used_pct']:.1f}%)")
        if coverage['malformed_strings'] > 0:
            report_lines.append(f"- ⚠️ **Malformed weather strings:** {coverage['malformed_strings']:,} ({coverage['malformed_pct']:.1f}%)")
        report_lines.append("\n### Venue Types (dim_game.roof)\n")
        report_lines.append(f"- **Outdoor Games:** {coverage['outdoor_games']:,}")
        report_lines.append(f"- **Dome Games:** {coverage['dome_games']:,}")
        report_lines.append(f"- **Retractable Roof:** {coverage['retractable_games']:,}")
        report_lines.append(f"- **Missing Roof Info:** {coverage['missing_roof_info']:,}")
        report_lines.append("\n---\n")
        
        # By Season
        if 'by_season' in self.analysis_results:
            report_lines.append("## Coverage by Season\n")
            season_df = self.analysis_results['by_season']
            report_lines.append("| Season | Games | Temp % | Wind % | Weather % | Outdoor | Avg Temp | Avg Wind |")
            report_lines.append("|--------|-------|--------|--------|-----------|---------|----------|----------|")
            for _, row in season_df.iterrows():
                avg_temp = f"{row['avg_temp']:.1f}°F" if pd.notna(row['avg_temp']) else "N/A"
                avg_wind = f"{row['avg_wind']:.1f} mph" if pd.notna(row['avg_wind']) else "N/A"
                report_lines.append(
                    f"| {row['season']} | {row['total_games']} | "
                    f"{row['temp_pct']:.1f}% | {row['wind_pct']:.1f}% | {row['weather_pct']:.1f}% | "
                    f"{row['outdoor_games']} | {avg_temp} | {avg_wind} |"
                )
            report_lines.append("\n---\n")
        
        # By Week
        if 'by_week' in self.analysis_results:
            report_lines.append("## Coverage by Week\n")
            week_df = self.analysis_results['by_week']
            report_lines.append("| Week | Games | Temp % | Wind % | Complete % |")
            report_lines.append("|------|-------|--------|--------|------------|")
            for _, row in week_df.iterrows():
                report_lines.append(
                    f"| {row['week']} | {row['total_games']} | "
                    f"{row['temp_pct']:.1f}% | {row['wind_pct']:.1f}% | {row['complete_pct']:.1f}% |"
                )
            report_lines.append("\n---\n")
        
        # By Venue
        if 'by_venue' in self.analysis_results:
            report_lines.append("## Coverage by Venue\n")
            venue_df = self.analysis_results['by_venue'].sort_values('temp_pct', ascending=False)
            report_lines.append("| Team | Stadium | Roof Type | Games | Temp % | Wind % | Avg Temp | Avg Wind |")
            report_lines.append("|------|---------|-----------|-------|--------|--------|----------|----------|")
            for _, row in venue_df.iterrows():
                avg_temp = f"{row['avg_temp']:.1f}°F" if pd.notna(row['avg_temp']) else "N/A"
                avg_wind = f"{row['avg_wind']:.1f} mph" if pd.notna(row['avg_wind']) else "N/A"
                report_lines.append(
                    f"| {row['team']} | {row['stadium'][:30]} | {row['roof_type']} | "
                    f"{row['total_games']} | {row['temp_pct']:.1f}% | {row['wind_pct']:.1f}% | "
                    f"{avg_temp} | {avg_wind} |"
                )
            report_lines.append("\n---\n")
        
        # Data Quality
        if 'quality' in self.analysis_results:
            report_lines.append("## Data Quality Analysis\n")
            quality = self.analysis_results['quality']
            report_lines.append("### Missing Data Issues\n")
            report_lines.append(f"- **Outdoor games missing weather:** {quality['outdoor_missing_weather']:,} / {quality['outdoor_games_total']:,} ({quality['outdoor_missing_pct']:.1f}%)")
            report_lines.append(f"- **Recent (2023+) outdoor games missing:** {quality['recent_missing_weather']:,} / {quality['recent_outdoor_games']:,} ({quality['recent_missing_pct']:.1f}%)")
            report_lines.append("\n### NFL Impact - Temperature\n")
            report_lines.append(f"- **Freezing (≤32°F):** {quality['freezing_games']:,} games")
            report_lines.append(f"- **Impactful cold (<20°F):** {quality['impactful_cold_games']:,} games")
            report_lines.append(f"- **Meteorological extreme (<0°F):** {quality['meteorological_extreme_cold']:,} games")
            report_lines.append(f"- **Extreme heat (>100°F):** {quality['extreme_hot_games']:,} games")
            report_lines.append("\n### NFL Impact - Wind\n")
            report_lines.append(f"- **Impactful wind (>15 mph):** {quality['impactful_wind_games']:,} games")
            report_lines.append(f"- **High wind (>20 mph):** {quality['high_wind_games']:,} games")
            report_lines.append(f"- **Extreme wind (>30 mph):** {quality['extreme_wind_games']:,} games")
            report_lines.append("\n---\n")
        
        # Roof Vocabulary Audit
        if 'roof_vocabulary' in self.analysis_results:
            report_lines.append("## Roof Type Vocabulary Audit\n")
            roof_vocab = self.analysis_results['roof_vocabulary']
            
            report_lines.append("### dim_game.roof Distribution\n")
            for roof_val, count in roof_vocab['dim_game_roof_values'].items():
                report_lines.append(f"- **{roof_val}:** {count} teams")
            
            report_lines.append("\n### Stadium Registry roof_type Distribution\n")
            for roof_type, count in roof_vocab['registry_roof_types'].items():
                report_lines.append(f"- **{roof_type}:** {count} teams")
            
            report_lines.append(f"\n### Questionable Weather Data\n")
            report_lines.append(f"- **Retractable stadiums with weather:** {roof_vocab['retractable_with_weather_count']} games")
            report_lines.append(f"- **Fixed domes with weather:** {roof_vocab['dome_with_weather_count']} games")
            
            if roof_vocab['retractable_with_weather_sample']:
                report_lines.append("\n*Retractable roof games with weather (roof possibly open):*")
                for game in roof_vocab['retractable_with_weather_sample']:
                    report_lines.append(f"- {game['game_id']}: {game['home_team']} (temp={game['temp_filled']}, wind={game['wind_filled']}, source={game['weather_provenance']})")
            
            if roof_vocab['dome_with_weather_sample']:
                report_lines.append("\n*Fixed dome games with weather (unexpected):*")
                for game in roof_vocab['dome_with_weather_sample']:
                    report_lines.append(f"- {game['game_id']}: {game['home_team']} (temp={game['temp_filled']}, wind={game['wind_filled']}, source={game['weather_provenance']})")
            
            report_lines.append("\n---\n")
        
        # Sample Games
        report_lines.append("## Sample Games\n")
        report_lines.append("### Games Missing Weather Data (Outdoor, after parsing)\n")
        missing_sample = self.get_sample_games('missing', limit=10)
        if not missing_sample.empty:
            report_lines.append(missing_sample.to_markdown(index=False))
        else:
            report_lines.append("*No outdoor games missing weather data found*")
        
        report_lines.append("\n### Impactful Cold Games (<20°F)\n")
        cold_sample = self.get_sample_games('extreme_cold', limit=10)
        if not cold_sample.empty:
            report_lines.append(cold_sample.to_markdown(index=False))
        else:
            report_lines.append("*No impactful cold games found*")
        
        report_lines.append("\n### High Wind Games (>20 mph)\n")
        wind_sample = self.get_sample_games('extreme_wind', limit=10)
        if not wind_sample.empty:
            report_lines.append(wind_sample.to_markdown(index=False))
        else:
            report_lines.append("*No high wind games found*")
        
        # Add malformed string samples if present
        coverage = self.analysis_results['coverage']
        if coverage.get('malformed_strings', 0) > 0:
            report_lines.append("\n### Malformed Weather Strings\n")
            malformed_sample = self.dim_game[
                self.dim_game['is_malformed_weather_string'] == True
            ][['game_id', 'season', 'week', 'home_team', 'away_team',
               'roof', 'temp_filled', 'wind_filled', 'weather']].head(10)
            if not malformed_sample.empty:
                report_lines.append(malformed_sample.to_markdown(index=False))
        
        report_lines.append("\n---\n")
        report_lines.append("## Recommendations\n")
        report_lines.append("1. **String Parsing Success:** Recovered weather data from embedded strings (see Data Provenance section)")
        report_lines.append("2. **⚠️ CRITICAL FOR MODELING:** Use `temp_model`/`wind_model` columns for training (excludes fixed domes and closed retractables)")
        report_lines.append("   - `temp_filled`/`wind_filled` include outside weather for all games (raw availability)")
        report_lines.append("   - `temp_model`/`wind_model` only include weather when it affected gameplay")
        report_lines.append("   - Fixed dome weather reflects outside conditions, NOT gameplay environment")
        report_lines.append("3. **Roof Validation:** Review retractable/dome games with weather data (see Roof Vocabulary Audit)")
        report_lines.append("4. **NFL Impact Thresholds:** Focus on <20°F and >15mph wind for game analysis, not just meteorological extremes")
        report_lines.append("5. **Historical Backfill:** For remaining gaps, use weather/historical/ncei_client.py")
        report_lines.append("6. **Future Forecasts:** For upcoming games, use weather/forecasts/noaa_client.py")
        
        # Write report
        report_content = "\n".join(report_lines)
        output_path.write_text(report_content, encoding='utf-8')
        
        self.logger.info(f"Report saved to: {output_path}")
        return str(output_path)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Review weather data availability in the bucket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Review all seasons
  python scripts/review_weather_data.py --all
  
  # Review specific seasons
  python scripts/review_weather_data.py --seasons 2023 2024 2025
  
  # Review specific season and week
  python scripts/review_weather_data.py --season 2024 --week 15
  
  # Custom output path
  python scripts/review_weather_data.py --all --output reports/my_weather_review.md
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Review all seasons')
    parser.add_argument('--seasons', type=int, nargs='+',
                       help='Specific seasons to review')
    parser.add_argument('--season', type=int,
                       help='Single season (for week-specific analysis)')
    parser.add_argument('--week', type=int,
                       help='Specific week to analyze')
    parser.add_argument('--output', type=str,
                       help='Output path for report (default: reports/weather_data_review_TIMESTAMP.md)')
    
    args = parser.parse_args()
    
    # Determine seasons to analyze
    seasons = None
    if args.seasons:
        seasons = args.seasons
    elif args.season:
        seasons = [args.season]
    elif not args.all:
        # Default to recent 3 seasons
        current_year = datetime.now().year
        seasons = [current_year - 2, current_year - 1, current_year]
        print(f"No seasons specified. Defaulting to: {seasons}")
    
    # Create reviewer and run analysis
    reviewer = WeatherDataReviewer()
    
    try:
        print(f"\n{'='*60}")
        print("Weather Data Review Script")
        print(f"{'='*60}\n")
        
        reviewer.run_full_analysis(seasons=seasons, specific_week=args.week)
        
        # Generate report
        output_path = Path(args.output) if args.output else None
        report_path = reviewer.generate_report(output_path)
        
        print(f"\n{'='*60}")
        print(f"✓ Analysis Complete!")
        print(f"{'='*60}")
        print(f"\nReport saved to: {report_path}")
        print(f"\nSummary:")
        coverage = reviewer.analysis_results['coverage']
        print(f"  - Total Games: {coverage['total_games']:,}")
        print(f"  - Temperature Coverage: {coverage['temp_coverage_pct']:.1f}%")
        print(f"  - Wind Coverage: {coverage['wind_coverage_pct']:.1f}%")
        print(f"  - Complete Weather: {coverage['complete_weather_pct']:.1f}%")
        
        quality = reviewer.analysis_results.get('quality', {})
        if quality:
            print(f"\nData Quality:")
            print(f"  - Outdoor games missing weather: {quality.get('outdoor_missing_pct', 0):.1f}%")
            print(f"  - Recent games missing weather: {quality.get('recent_missing_pct', 0):.1f}%")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
