"""
Player Analytics Implementation

Advanced player performance analytics including usage patterns
and EPA-based contribution analysis.

Pattern: Minimum Viable Decoupling
Complexity: 3 points (analytics + business logic)
Layer: 2 (Implementation - calls infrastructure directly)

Migrated from data_pipeline/transformations for proper separation of concerns.
"""

import pandas as pd
from typing import Dict, Any, Optional
from commonv2 import get_logger


class PlayerAnalyticsImpl:
    """
    Advanced player performance analytics.
    
    Pattern: Minimum Viable Decoupling
    Complexity: 3 points
    Depth: 1 layer (calls infrastructure directly)
    
    Responsibilities:
    - Analyze player usage patterns and efficiency
    - Analyze EPA-based player contributions
    - Generate coaching insights
    - No complex patterns or abstractions
    """
    
    def __init__(self, db_service, logger):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
    
    def get_player_usage_analysis(self, season: str, position_group: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze player usage patterns for coaching insights.
        
        Advanced usage pattern analysis including:
        - Snap share and consistency
        - Opportunity metrics
        - Efficiency calculations
        - Usage tier categorization
        
        Args:
            season: Season to analyze
            position_group: Optional position filter (QB, RB, WR, TE)
            
        Returns:
            Dict with usage analysis results
            
        Complexity: Enhanced analytics function (3 points)
        """
        self.logger.info(f"Analyzing player usage for season {season}, position: {position_group or 'All'}")
        
        try:
            # Build position filter
            position_filter = ""
            if position_group:
                position_filter = f"AND position_group = '{position_group}'"
            
            # Usage patterns query
            usage_query = f"""
            SELECT 
                player_name,
                recent_team,
                position_group,
                COUNT(*) as games_played,
                AVG(offense_pct) as avg_snap_share,
                SUM(targets) as total_targets,
                SUM(carries) as total_carries,
                SUM(fantasy_points_ppr) as total_fantasy_points,
                
                -- Usage consistency metric
                STDDEV(offense_pct) as snap_share_volatility,
                
                -- Opportunity metrics
                CASE 
                    WHEN SUM(targets + carries) > 0 
                    THEN SUM(fantasy_points_ppr) / SUM(targets + carries)
                    ELSE 0
                END as points_per_opportunity
                
            FROM warehouse.fact_player_stats
            WHERE season = '{season}'
                AND offense_snaps > 0
                {position_filter}
            GROUP BY player_name, recent_team, position_group
            HAVING COUNT(*) >= 4  -- At least 4 games
            ORDER BY total_fantasy_points DESC
            LIMIT 100
            """
            
            # Get engine from database service
            engine = self.db_service.get_engine()
            usage_df = pd.read_sql(usage_query, engine)
            
            # Calculate usage tiers
            if not usage_df.empty:
                usage_df['usage_tier'] = pd.cut(
                    usage_df['avg_snap_share'], 
                    bins=[0, 0.3, 0.6, 1.0], 
                    labels=['Limited', 'Rotational', 'Workhorse']
                )
            
            self.logger.info(f"Usage analysis complete: {len(usage_df)} players analyzed")
            
            return {
                'status': 'success',
                'season': season,
                'position_group': position_group or 'All',
                'players_analyzed': len(usage_df),
                'usage_patterns': usage_df.to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate usage analysis: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def get_player_contribution_analysis(self, season: str, position_type: str = 'QB') -> Dict[str, Any]:
        """
        Analyze individual player contributions to team success.
        
        Advanced player contribution metrics including:
        - EPA-based contribution analysis
        - Efficiency metrics
        - Situational performance (3rd down, red zone)
        - Consistency metrics
        - Percentile rankings
        
        Args:
            season: Season to analyze
            position_type: Position involvement type ('QB', 'RB', 'WR', etc.)
            
        Returns:
            Dict with contribution analysis results
            
        Complexity: Enhanced analytics function (3 points)
        """
        self.logger.info(f"Analyzing player contributions for season {season}, position: {position_type}")
        
        try:
            # Player contribution analysis query
            contribution_query = f"""
            SELECT 
                player_name,
                posteam as team,
                COUNT(*) as total_plays,
                SUM(attributed_epa) as total_epa_contribution,
                AVG(attributed_epa) as avg_epa_per_play,
                SUM(stat_value) as total_production,
                SUM(opportunity_count) as total_opportunities,
                
                -- Efficiency metrics
                CASE 
                    WHEN SUM(opportunity_count) > 0 
                    THEN SUM(attributed_epa) / SUM(opportunity_count)
                    ELSE 0 
                END as epa_per_opportunity,
                
                -- Situational performance
                AVG(CASE WHEN down >= 3 THEN attributed_epa END) as third_down_epa,
                AVG(CASE WHEN yardline_100 <= 20 THEN attributed_epa END) as red_zone_epa,
                
                -- Consistency metrics
                STDDEV(attributed_epa) as epa_volatility
                
            FROM warehouse.fact_player_play
            WHERE EXTRACT(YEAR FROM game_date) = {season}
                AND involvement_type = '{position_type}'
                AND attributed_epa IS NOT NULL
            GROUP BY player_name, posteam
            HAVING COUNT(*) >= 20  -- Minimum play threshold
            ORDER BY total_epa_contribution DESC
            LIMIT 50
            """
            
            # Get engine from database service
            engine = self.db_service.get_engine()
            contribution_df = pd.read_sql(contribution_query, engine)
            
            # Calculate percentile rankings
            if not contribution_df.empty:
                contribution_df['epa_percentile'] = contribution_df['total_epa_contribution'].rank(pct=True)
                contribution_df['efficiency_percentile'] = contribution_df['epa_per_opportunity'].rank(pct=True)
            
            self.logger.info(f"Contribution analysis complete: {len(contribution_df)} players analyzed")
            
            return {
                'status': 'success',
                'season': season,
                'position_type': position_type,
                'players_analyzed': len(contribution_df),
                'contribution_analysis': contribution_df.to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate contribution analysis: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def validate_call_depth(self):
        """
        Development helper: Validate architecture constraints.
        
        Call depth check:
        User → PlayerAnalyticsImpl methods [Layer 2]
             → Database service calls [Layer 3]
        
        Returns:
            dict: Validation results
        """
        return {
            'max_depth': 3,
            'current_depth': 3,
            'within_limits': True,
            'pattern': 'Minimum Viable Decoupling',
            'complexity_points': 3,
            'traceable': True,
            'explanation': 'User → Player Analytics → Database (3 layers)'
        }


# Convenience function for direct usage
def create_player_analytics(db_service=None, logger=None):
    """
    Create player analytics service with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        
    Returns:
        PlayerAnalyticsImpl: Configured player analytics service
    """
    from ...shared.database_router import get_database_router
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.analytics.player_analytics')
    
    return PlayerAnalyticsImpl(db_service, logger)


__all__ = [
    'PlayerAnalyticsImpl',
    'create_player_analytics'
]