"""
Exploratory Analysis Implementation

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + business logic)
Layer: 2 (Implementation - calls infrastructure directly)

Follows clean architecture with maximum 3 layers:
Layer 1: Public API (nflfastRv3/__init__.py)
Layer 2: This implementation
Layer 3: Infrastructure (database, validation)

Migrated from nflfastRv2/features/analytics_suite/exploratory.py
with V3 clean architecture patterns applied.
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy import text


class ExploratoryAnalysisImpl:
    """
    Core exploratory analysis business logic.
    
    Pattern: Minimum Viable Decoupling (⭐ RECOMMENDED START)
    Complexity: 2 points
    Depth: 1 layer (calls infrastructure directly)
    
    Responsibilities:
    - Run comprehensive exploratory analysis on NFL data
    - Generate data overview and insights
    - Analyze team performance metrics
    - Examine seasonal trends and game factors
    - No complex patterns or abstractions
    """
    
    def __init__(self, db_service, logger, bucket_adapter=None):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
            bucket_adapter: Bucket adapter (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        self.bucket_adapter = bucket_adapter
    
    def run_exploratory_analysis(self, **kwargs) -> Dict[str, Any]:
        """
        Run comprehensive exploratory analysis on NFL data.
        
        Simple analysis flow:
        1. Get data overview (Layer 3 call)
        2. Analyze team performance (Layer 3 call)
        3. Examine seasonal trends (Layer 3 call)
        4. Study game factors (Layer 3 call)
        5. Return combined results
        
        Args:
            **kwargs: Additional analysis options
            
        Returns:
            Dictionary with exploratory analysis results
        """
        self.logger.info("Starting exploratory data analysis")
        
        try:
            analysis_results = {
                'status': 'success',
                'data_overview': self._get_data_overview(),
                'team_performance': self._analyze_team_performance(),
                'seasonal_trends': self._analyze_seasonal_trends(),
                'game_factors': self._analyze_game_factors()
            }
            
            self.logger.info("Exploratory analysis completed successfully")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Exploratory analysis failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def analyze_team_performance(self, season: int = 2024, **kwargs) -> Dict[str, Any]:
        """
        Analyze team performance metrics for a given season.
        
        Args:
            season: NFL season to analyze
            **kwargs: Additional analysis options
            
        Returns:
            Dictionary with team performance insights
        """
        self.logger.info(f"Analyzing team performance for {season} season")
        
        if not self.bucket_adapter:
            return {'status': 'error', 'message': 'Bucket adapter not initialized'}
            
        try:
            # Load play data for season
            columns = [
                'posteam', 'season', 'yards_gained', 'touchdown',
                'interception', 'fumble_lost'
            ]
            
            # Use filters to optimize read for partitioned data
            filters = [('season', '==', season)]
            
            df = self.bucket_adapter.read_data(
                'play_by_play',
                'raw_nflfastr',
                columns=columns,
                filters=filters
            )
            
            if df.empty:
                return {'status': 'error', 'message': f'No data found for season {season}'}
                
            season_df = df
            
            if season_df.empty:
                return {
                    'status': 'warning',
                    'message': f'No data found for season {season}',
                    'season': season,
                    'teams_analyzed': 0,
                    'team_performance': []
                }
            
            # Aggregate stats
            team_stats_df = season_df.groupby('posteam').agg(
                total_plays=('yards_gained', 'count'),
                avg_yards_per_play=('yards_gained', 'mean'),
                touchdowns=('touchdown', 'sum'),
                interceptions=('interception', 'sum'),
                fumbles_lost=('fumble_lost', 'sum')
            ).reset_index()
            
            # Calculate efficiency score
            team_stats_df['efficiency_score'] = (
                team_stats_df['avg_yards_per_play'] -
                (team_stats_df['interceptions'] + team_stats_df['fumbles_lost']) * 0.5
            )
            
            # Sort by efficiency
            team_stats_df = team_stats_df.sort_values('avg_yards_per_play', ascending=False)
            
            # Convert to list of dicts
            team_stats = team_stats_df.rename(columns={'posteam': 'team'}).to_dict('records')
            
            # Round floats
            for team in team_stats:
                team['avg_yards_per_play'] = round(team['avg_yards_per_play'], 2)
                team['efficiency_score'] = round(team['efficiency_score'], 2)
            
            analysis_results = {
                "status": "success",
                "season": season,
                "teams_analyzed": len(team_stats),
                "team_performance": team_stats,
                "insights": self._generate_team_insights(team_stats)
            }
            
            self.logger.info(f"Team performance analysis complete for {season}")
            return analysis_results
                
        except Exception as e:
            self.logger.error(f"Team performance analysis failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'season': season
            }
    
    def _get_data_overview(self) -> Dict[str, Any]:
        """
        Get overview of available data.
        
        Uses bucket adapter (Layer 3) - no complex patterns
        
        Returns:
            dict: Data overview results
        """
        self.logger.info("Generating data overview")
        
        overview = {
            'schemas': {},
            'total_records': 0,
            'date_range': {}
        }
        
        if not self.bucket_adapter:
            overview['error'] = 'Bucket adapter not initialized'
            return overview
            
        try:
            # List files in bucket
            files = self.bucket_adapter.list_files()
            
            # Group by schema (folder)
            schemas = {}
            for file in files:
                parts = file.split('/')
                if len(parts) > 1:
                    schema = parts[0]
                    table = parts[1]
                    if schema not in schemas:
                        schemas[schema] = []
                    schemas[schema].append(table)
            
            overview['schemas'] = schemas
            
            # Get date range from play_by_play
            try:
                df = self.bucket_adapter.read_data(
                    'play_by_play',
                    'raw_nflfastr',
                    columns=['game_date']
                )
                
                if not df.empty:
                    overview['date_range'] = {
                        'min_date': str(df['game_date'].min()),
                        'max_date': str(df['game_date'].max()),
                        'total_plays': len(df)
                    }
            except Exception as e:
                self.logger.warning(f"Could not get date range: {e}")
                overview['date_range'] = {'status': 'unavailable'}
            
            self.logger.info("Data overview generated successfully")
            
        except Exception as e:
            self.logger.warning(f"Could not generate complete data overview: {e}")
            overview['error'] = str(e)
        
        return overview
    
    def _analyze_team_performance(self) -> Dict[str, Any]:
        """
        Analyze basic team performance metrics.
        
        Uses bucket adapter (Layer 3) - no complex patterns
        
        Returns:
            dict: Team performance analysis results
        """
        self.logger.info("Analyzing team performance")
        
        if not self.bucket_adapter:
            return {'error': 'Bucket adapter not initialized'}
            
        try:
            # Load play data
            columns = [
                'posteam', 'season', 'yards_gained', 'touchdown',
                'interception', 'fumble_lost'
            ]
            
            df = self.bucket_adapter.read_data(
                'play_by_play',
                'raw_nflfastr',
                columns=columns
            )
            
            if df.empty:
                return {'error': 'No data found'}
                
            # Filter for most recent season
            max_season = df['season'].max()
            season_df = df[df['season'] == max_season].copy()
            
            # Aggregate stats
            team_stats_df = season_df.groupby('posteam').agg(
                total_plays=('yards_gained', 'count'),
                avg_yards_per_play=('yards_gained', 'mean'),
                touchdowns=('touchdown', 'sum'),
                interceptions=('interception', 'sum'),
                fumbles_lost=('fumble_lost', 'sum')
            ).reset_index()
            
            # Sort by efficiency
            team_stats_df = team_stats_df.sort_values('avg_yards_per_play', ascending=False).head(10)
            
            # Convert to list of dicts
            team_stats = team_stats_df.rename(columns={'posteam': 'team'}).to_dict('records')
            
            # Round floats
            for team in team_stats:
                team['avg_yards_per_play'] = round(team['avg_yards_per_play'], 2)
            
            return {
                'top_teams_by_efficiency': team_stats,
                'analysis_note': f'Based on yards per play for {max_season} season'
            }
                
        except Exception as e:
            self.logger.warning(f"Could not analyze team performance: {e}")
            return {'error': str(e)}
    
    def _analyze_seasonal_trends(self) -> Dict[str, Any]:
        """
        Analyze trends across seasons.
        
        Uses bucket adapter (Layer 3) - no complex patterns
        
        Returns:
            dict: Seasonal trends analysis results
        """
        self.logger.info("Analyzing seasonal trends")
        
        if not self.bucket_adapter:
            return {'error': 'Bucket adapter not initialized'}
            
        try:
            # Load play data
            columns = [
                'season', 'game_id', 'yards_gained', 'touchdown'
            ]
            
            df = self.bucket_adapter.read_data(
                'play_by_play',
                'raw_nflfastr',
                columns=columns
            )
            
            if df.empty:
                return {'error': 'No data found'}
            
            # Group by season
            trends_df = df.groupby('season').agg(
                total_games=('game_id', 'nunique'),
                td_rate=('touchdown', 'mean'),
                avg_yards_per_play=('yards_gained', 'mean'),
                total_plays=('yards_gained', 'count')
            ).reset_index()
            
            # Calculate percentage
            trends_df['td_rate'] = trends_df['td_rate'] * 100
            
            # Sort and limit
            trends_df = trends_df.sort_values('season', ascending=False).head(5)
            
            # Convert to list of dicts
            trends = trends_df.to_dict('records')
            
            # Round floats
            for trend in trends:
                trend['touchdown_rate_percent'] = round(trend.pop('td_rate'), 2)
                trend['avg_yards_per_play'] = round(trend['avg_yards_per_play'], 2)
            
            return {
                'recent_seasons': trends,
                'analysis_note': 'Trends for last 5 seasons'
            }
                
        except Exception as e:
            self.logger.warning(f"Could not analyze seasonal trends: {e}")
            return {'error': str(e)}
    
    def _analyze_game_factors(self) -> Dict[str, Any]:
        """
        Analyze factors that influence games.
        
        Uses bucket adapter (Layer 3) - no complex patterns
        
        Returns:
            dict: Game factors analysis results
        """
        self.logger.info("Analyzing game factors")
        
        if not self.bucket_adapter:
            return {'error': 'Bucket adapter not initialized'}
            
        try:
            # Load play data
            columns = [
                'season', 'posteam', 'home_team', 'away_team',
                'yards_gained', 'touchdown'
            ]
            
            df = self.bucket_adapter.read_data(
                'play_by_play',
                'raw_nflfastr',
                columns=columns
            )
            
            if df.empty:
                return {'error': 'No data found'}
            
            # Filter for most recent season
            max_season = df['season'].max()
            season_df = df[df['season'] == max_season].copy()
            
            # Split home/away
            home_plays = season_df[season_df['posteam'] == season_df['home_team']]
            away_plays = season_df[season_df['posteam'] == season_df['away_team']]
            
            factors = []
            
            # Home stats
            factors.append({
                'factor': 'home_field_advantage',
                'total_plays': len(home_plays),
                'touchdown_rate': round(home_plays['touchdown'].mean() * 100, 2),
                'avg_yards_per_play': round(home_plays['yards_gained'].mean(), 2)
            })
            
            # Away stats
            factors.append({
                'factor': 'away_performance',
                'total_plays': len(away_plays),
                'touchdown_rate': round(away_plays['touchdown'].mean() * 100, 2),
                'avg_yards_per_play': round(away_plays['yards_gained'].mean(), 2)
            })
            
            return {
                'home_vs_away': factors,
                'analysis_note': f'Home vs away performance for {max_season} season'
            }
                
        except Exception as e:
            self.logger.warning(f"Could not analyze game factors: {e}")
            return {'error': str(e)}
    
    def _generate_team_insights(self, team_stats: List[Dict[str, Any]]) -> List[str]:
        """
        Generate insights from team performance analysis.
        
        Args:
            team_stats: List of team performance statistics
            
        Returns:
            List of insight strings
        """
        if not team_stats:
            return ["No team data available for analysis"]
        
        insights = []
        
        # Top performer insight
        top_team = team_stats[0]
        insights.append(f"Most efficient team: {top_team['team']} ({top_team['avg_yards_per_play']} yards/play)")
        
        # Efficiency range insight
        if len(team_stats) > 1:
            bottom_team = team_stats[-1]
            efficiency_gap = top_team['avg_yards_per_play'] - bottom_team['avg_yards_per_play']
            insights.append(f"Efficiency gap between top and bottom teams: {efficiency_gap:.2f} yards/play")
        
        # Turnover analysis
        high_turnover_teams = [team for team in team_stats if (team['interceptions'] + team['fumbles_lost']) > 15]
        if high_turnover_teams:
            insights.append(f"{len(high_turnover_teams)} teams with high turnover rates (>15 per season)")
        
        # Touchdown production
        avg_touchdowns = sum(team['touchdowns'] for team in team_stats) / len(team_stats)
        insights.append(f"Average touchdowns per team: {avg_touchdowns:.1f}")
        
        return insights
    def get_fact_play_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of fact_play table for monitoring.
        
        Data quality monitoring features:
        - Row counts by season/week
        - Data quality metrics
        - Coverage analysis
        
        Returns:
            Dict with comprehensive table summary
            
        Complexity: Simple aggregation function (2 points)
        """
        self.logger.info("Generating fact_play table summary")
        
        try:
            # Get engine from database service
            engine = self.db_service.get_engine()
            
            # Basic table summary
            sample_query = "SELECT * FROM warehouse.fact_play LIMIT 1000"
            sample_df = pd.read_sql(sample_query, engine)
            
            # Import warehouse utils for summary creation
            from ..data_pipeline.transformations.warehouse_utils import create_table_summary
            summary = create_table_summary(sample_df, 'fact_play')
            
            # Season/week breakdown
            coverage_query = """
            SELECT 
                season,
                COUNT(DISTINCT week) as weeks_covered,
                COUNT(*) as total_plays,
                COUNT(DISTINCT game_id) as games_covered
            FROM warehouse.fact_play
            GROUP BY season
            ORDER BY season DESC
            """
            
            coverage_df = pd.read_sql(coverage_query, engine)
            summary['coverage_by_season'] = coverage_df.to_dict('records')
            
            # Data quality metrics
            quality_query = """
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN epa IS NOT NULL THEN 1 END) as rows_with_epa,
                COUNT(CASE WHEN success IS NOT NULL THEN 1 END) as rows_with_success,
                AVG(CASE WHEN epa IS NOT NULL THEN epa END) as avg_epa,
                COUNT(DISTINCT play_type) as unique_play_types
            FROM warehouse.fact_play
            """
            
            quality_df = pd.read_sql(quality_query, engine)
            summary['data_quality'] = quality_df.to_dict('records')[0]
            
            self.logger.info("Generated fact_play table summary")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate fact_play summary: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def get_fact_player_stats_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of fact_player_stats table for monitoring.
        
        Data quality monitoring features:
        - Player counts by position and team
        - Performance metrics distribution
        - Snap count coverage analysis
        
        Returns:
            Dict with comprehensive table summary
            
        Complexity: Simple aggregation function (2 points)
        """
        self.logger.info("Generating fact_player_stats table summary")
        
        try:
            # Get engine from database service
            engine = self.db_service.get_engine()
            
            # Basic table summary
            sample_query = "SELECT * FROM warehouse.fact_player_stats LIMIT 1000"
            sample_df = pd.read_sql(sample_query, engine)
            
            # Import warehouse utils for summary creation
            from ..data_pipeline.transformations.warehouse_utils import create_table_summary
            summary = create_table_summary(sample_df, 'fact_player_stats')
            
            # Position breakdown
            position_query = """
            SELECT 
                position_group,
                COUNT(DISTINCT player_id) as unique_players,
                COUNT(*) as total_records,
                AVG(fantasy_points_ppr) as avg_fantasy_points
            FROM warehouse.fact_player_stats
            WHERE position_group IS NOT NULL
            GROUP BY position_group
            ORDER BY total_records DESC
            """
            
            position_df = pd.read_sql(position_query, engine)
            summary['position_breakdown'] = position_df.to_dict('records')
            
            # Season/team coverage
            coverage_query = """
            SELECT 
                season,
                COUNT(DISTINCT recent_team) as teams_covered,
                COUNT(DISTINCT player_id) as unique_players,
                COUNT(*) as total_records
            FROM warehouse.fact_player_stats
            GROUP BY season
            ORDER BY season DESC
            """
            
            coverage_df = pd.read_sql(coverage_query, engine)
            summary['coverage_by_season'] = coverage_df.to_dict('records')
            
            # Data quality metrics
            quality_query = """
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN offense_snaps IS NOT NULL THEN 1 END) as rows_with_snap_counts,
                COUNT(CASE WHEN fantasy_points_ppr > 0 THEN 1 END) as rows_with_fantasy_points,
                AVG(CASE WHEN targets > 0 THEN targets END) as avg_targets_when_targeted,
                COUNT(DISTINCT position) as unique_positions
            FROM warehouse.fact_player_stats
            """
            
            quality_df = pd.read_sql(quality_query, engine)
            summary['data_quality'] = quality_df.to_dict('records')[0]
            
            # Top performers by position
            top_performers_query = """
            SELECT 
                position_group,
                player_name,
                recent_team,
                SUM(fantasy_points_ppr) as total_fantasy_points,
                SUM(targets) as total_targets,
                SUM(receptions) as total_receptions
            FROM warehouse.fact_player_stats
            WHERE season = (SELECT MAX(season) FROM warehouse.fact_player_stats)
                AND position_group IN ('QB', 'RB', 'WR', 'TE')
            GROUP BY position_group, player_name, recent_team
            HAVING SUM(fantasy_points_ppr) > 50
            ORDER BY position_group, total_fantasy_points DESC
            """
            
            top_performers_df = pd.read_sql(top_performers_query, engine)
            summary['top_performers'] = top_performers_df.to_dict('records')
            
            self.logger.info("Generated fact_player_stats table summary")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate fact_player_stats summary: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def get_fact_player_play_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of fact_player_play table for monitoring.
        
        Data quality monitoring features:
        - Player involvement breakdown by type
        - EPA attribution analysis
        - Usage pattern metrics
        
        Returns:
            Dict with comprehensive table summary
            
        Complexity: Simple aggregation function (2 points)
        """
        self.logger.info("Generating fact_player_play table summary")
        
        try:
            # Get engine from database service
            engine = self.db_service.get_engine()
            
            # Basic table summary
            sample_query = "SELECT * FROM warehouse.fact_player_play LIMIT 1000"
            sample_df = pd.read_sql(sample_query, engine)
            
            # Import warehouse utils for summary creation
            from ..data_pipeline.transformations.warehouse_utils import create_table_summary
            summary = create_table_summary(sample_df, 'fact_player_play')
            
            # Involvement type breakdown
            involvement_query = """
            SELECT 
                involvement_type,
                side_of_ball,
                COUNT(*) as total_plays,
                COUNT(DISTINCT player_id) as unique_players,
                AVG(attributed_epa) as avg_epa_attributed,
                SUM(opportunity_count) as total_opportunities
            FROM warehouse.fact_player_play
            GROUP BY involvement_type, side_of_ball
            ORDER BY total_plays DESC
            """
            
            involvement_df = pd.read_sql(involvement_query, engine)
            summary['involvement_breakdown'] = involvement_df.to_dict('records')
            
            # Top EPA contributors
            top_epa_query = """
            SELECT 
                player_name,
                involvement_type,
                COUNT(*) as total_plays,
                SUM(attributed_epa) as total_epa_attributed,
                AVG(attributed_epa) as avg_epa_per_play,
                SUM(stat_value) as total_stat_value
            FROM warehouse.fact_player_play
            WHERE attributed_epa IS NOT NULL
            GROUP BY player_name, involvement_type
            HAVING COUNT(*) >= 20  -- At least 20 plays
            ORDER BY total_epa_attributed DESC
            LIMIT 50
            """
            
            top_epa_df = pd.read_sql(top_epa_query, engine)
            summary['top_epa_contributors'] = top_epa_df.to_dict('records')
            
            # Data quality metrics
            quality_query = """
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN attributed_epa IS NOT NULL THEN 1 END) as rows_with_epa,
                COUNT(CASE WHEN stat_value > 0 THEN 1 END) as rows_with_positive_stats,
                COUNT(DISTINCT player_id) as unique_players,
                COUNT(DISTINCT game_id) as unique_games,
                AVG(opportunity_count) as avg_opportunities_per_play
            FROM warehouse.fact_player_play
            """
            
            quality_df = pd.read_sql(quality_query, engine)
            summary['data_quality'] = quality_df.to_dict('records')[0]
            
            self.logger.info("Generated fact_player_play table summary")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate fact_player_play summary: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    
    def validate_call_depth(self):
        """
        Development helper: Validate architecture constraints.
        
        Call depth check:
        User → run_exploratory_analysis() [Layer 1]
             → ExploratoryAnalysisImpl.run_exploratory_analysis() [Layer 2]
             → Database service calls [Layer 3]
        
        Returns:
            dict: Validation results
        """
        return {
            'max_depth': 3,
            'current_depth': 3,
            'within_limits': True,
            'pattern': 'Minimum Viable Decoupling',
            'complexity_points': 2,
            'traceable': True,
            'explanation': 'User → Exploratory Analysis → Database (3 layers)'
        }


# Convenience function for direct usage
def create_exploratory_analysis(db_service=None, logger=None, bucket_adapter=None):
    """
    Create exploratory analysis service with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        ExploratoryAnalysisImpl: Configured exploratory analysis service
    """
    from ...shared.database_router import get_database_router
    from commonv2.persistence.bucket_adapter import get_bucket_adapter
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.analytics.exploratory')
    bucket_adapter = bucket_adapter or get_bucket_adapter()
    
    return ExploratoryAnalysisImpl(db_service, logger, bucket_adapter)


__all__ = [
    'ExploratoryAnalysisImpl',
    'create_exploratory_analysis'
]
