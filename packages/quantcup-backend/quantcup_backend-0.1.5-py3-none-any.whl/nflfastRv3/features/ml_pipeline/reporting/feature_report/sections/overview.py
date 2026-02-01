"""
Feature Report - Overview and Details Section

Generates feature set overview table and detailed breakdowns.
"""

from typing import Dict, Any

from ....feature_sets import FEATURE_REGISTRY, get_feature_info


class OverviewSectionGenerator:
    """
    Generates feature set overview and details sections.
    
    Provides registry-based overview table and per-feature detailed status.
    """
    
    def __init__(self, logger=None):
        """
        Initialize overview generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_overview(self) -> str:
        """
        Generate feature set overview table.
        
        Returns:
            str: Formatted overview section with registry table
        """
        sections = ["""## Feature Set Overview

The ML pipeline supports 6 feature sets, each capturing different aspects of NFL games:

| Feature Set | Description | Granularity | Phase |
|-------------|-------------|-------------|-------|"""]
        
        # Add all feature sets from registry
        for feature_name, info in FEATURE_REGISTRY.items():
            description = info.get('description', 'No description')
            phase = info.get('phase', 'unknown')
            table = info.get('table', '')
            
            # Determine granularity from table name
            if 'v1' in table and feature_name in ['team_efficiency', 'opponent_adjusted']:
                granularity = "Season-level"
            else:
                granularity = "Game-level"
            
            sections.append(
                f"| **{feature_name}** | {description} | {granularity} | {phase} |"
            )
        
        return '\n'.join(sections)
    
    def generate_details(self, results: Dict[str, Any]) -> str:
        """
        Generate detailed breakdown for each feature set.
        
        Args:
            results: Feature engineering results dict
        
        Returns:
            str: Formatted details section
        """
        feature_results = results.get('results', {})
        
        if not feature_results:
            return """## Feature Set Details

No feature sets were processed."""
        
        sections = ["## Feature Set Details\n"]
        
        # Process in order from registry to maintain consistency
        for feature_name in FEATURE_REGISTRY.keys():
            if feature_name not in feature_results:
                continue
            
            result = feature_results[feature_name]
            info = get_feature_info(feature_name)
            
            status = result.get('status', 'unknown')
            rows = result.get('rows_built', 0)
            error = result.get('error', '')
            
            # Status icon
            status_icon = "✅" if status == 'success' else "❌"
            
            # Handle case where feature info is not found
            if info is None:
                info = {'description': 'Unknown feature set', 'table': 'unknown', 'phase': 'unknown'}
            
            section_parts = [f"""### {status_icon} {feature_name.replace('_', ' ').title()}

**Description:** {info.get('description', 'No description')}
**Database Table:** `features.{info.get('table', 'unknown')}`
**Development Phase:** {info.get('phase', 'unknown')}
**Build Status:** {status}
**Rows Generated:** {rows:,}"""]
            
            if error:
                section_parts.append(f"\n**Error Details:**\n```\n{error}\n```")
            
            # Add feature set specific notes
            feature_notes = self._get_feature_notes(feature_name, status)
            if feature_notes:
                section_parts.append(feature_notes)
            
            sections.append('\n'.join(section_parts))
        
        return '\n\n'.join(sections)
    
    def _get_feature_notes(self, feature_name: str, status: str) -> str:
        """
        Get feature-specific notes for successful builds.
        
        Args:
            feature_name: Name of the feature set
            status: Build status
        
        Returns:
            str: Feature-specific notes or empty string
        """
        if status != 'success':
            return ""
        
        notes_map = {
            'team_efficiency': """
**Key Features:**
- EPA calculations (offense & defense)
- Red zone efficiency metrics
- Third down conversion rates
- Turnover differentials
- Overall efficiency rankings""",
            
            'rolling_metrics': """
**Key Features:**
- 4/8/16-game rolling averages
- Momentum indicators (win streaks, trends)
- Consistency metrics (standard deviations)
- Venue-specific performance tracking""",
            
            'opponent_adjusted': """
**Key Features:**
- Strength of schedule calculations
- Quality wins/losses tracking
- Performance vs strong/average/weak opponents
- Schedule difficulty percentiles""",
            
            'nextgen': """
**Key Features:**
- QB NextGen Stats differentials
- Passer rating, completion %, aggressiveness
- Time to throw, air yards metrics
- Available for seasons 2016-2025""",
            
            'contextual': """
**Key Features:**
- Rest days differential (short/long rest indicators)
- Division and conference game flags
- Stadium-specific home advantage
- Weather impact (temperature, wind, precipitation)
- Playoff implications (late season, playoff week flags)""",
            
            'injury': """
**Key Features:**
- Position-weighted injury impact scores
- QB availability indicators
- Starter injury counts (depth chart based)
- Injury impact differentials"""
        }
        
        return notes_map.get(feature_name, "")


__all__ = ['OverviewSectionGenerator']
