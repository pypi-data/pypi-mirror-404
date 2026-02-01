"""
NFL Stadium Registry

Provides stadium information including coordinates and roof types for weather analysis.
"""

from typing import Dict, Optional


# Enhanced NFL Stadium registry with roof types
NFL_STADIUMS = {
    # AFC East
    'BUF': {'name': 'Highmark Stadium', 'lat': 42.7738, 'lon': -78.7870, 'roof_type': 'open'},
    'MIA': {'name': 'Hard Rock Stadium', 'lat': 25.9580, 'lon': -80.2389, 'roof_type': 'open'},
    'NE': {'name': 'Gillette Stadium', 'lat': 42.0909, 'lon': -71.2643, 'roof_type': 'open'},
    'NYJ': {'name': 'MetLife Stadium', 'lat': 40.8135, 'lon': -74.0745, 'roof_type': 'open'},
    
    # AFC North
    'BAL': {'name': 'M&T Bank Stadium', 'lat': 39.2780, 'lon': -76.6227, 'roof_type': 'open'},
    'CIN': {'name': 'Paycor Stadium', 'lat': 39.0955, 'lon': -84.5160, 'roof_type': 'open'},
    'CLE': {'name': 'FirstEnergy Stadium', 'lat': 41.5061, 'lon': -81.6995, 'roof_type': 'open'},
    'PIT': {'name': 'Acrisure Stadium', 'lat': 40.4468, 'lon': -80.0158, 'roof_type': 'open'},
    
    # AFC South
    'HOU': {'name': 'NRG Stadium', 'lat': 29.6847, 'lon': -95.4107, 'roof_type': 'retractable'},
    'IND': {'name': 'Lucas Oil Stadium', 'lat': 39.7601, 'lon': -86.1639, 'roof_type': 'retractable'},
    'JAX': {'name': 'TIAA Bank Field', 'lat': 30.3240, 'lon': -81.6374, 'roof_type': 'open'},
    'TEN': {'name': 'Nissan Stadium', 'lat': 36.1665, 'lon': -86.7713, 'roof_type': 'open'},
    
    # AFC West
    'DEN': {'name': 'Empower Field at Mile High', 'lat': 39.7439, 'lon': -105.0201, 'roof_type': 'open'},
    'KC': {'name': 'Arrowhead Stadium', 'lat': 39.0489, 'lon': -94.4839, 'roof_type': 'open'},
    'LV': {'name': 'Allegiant Stadium', 'lat': 36.0909, 'lon': -115.1833, 'roof_type': 'fixed_dome'},
    'LAC': {'name': 'SoFi Stadium', 'lat': 33.9535, 'lon': -118.3392, 'roof_type': 'fixed_dome'},
    
    # NFC East
    'DAL': {'name': 'AT&T Stadium', 'lat': 32.7473, 'lon': -97.0945, 'roof_type': 'retractable'},
    'NYG': {'name': 'MetLife Stadium', 'lat': 40.8135, 'lon': -74.0745, 'roof_type': 'open'},
    'PHI': {'name': 'Lincoln Financial Field', 'lat': 39.9008, 'lon': -75.1675, 'roof_type': 'open'},
    'WAS': {'name': 'FedExField', 'lat': 38.9076, 'lon': -76.8645, 'roof_type': 'open'},
    
    # NFC North
    'CHI': {'name': 'Soldier Field', 'lat': 41.8623, 'lon': -87.6167, 'roof_type': 'open'},
    'DET': {'name': 'Ford Field', 'lat': 42.3400, 'lon': -83.0456, 'roof_type': 'fixed_dome'},
    'GB': {'name': 'Lambeau Field', 'lat': 42.3601, 'lon': -88.0620, 'roof_type': 'open'},
    'MIN': {'name': 'U.S. Bank Stadium', 'lat': 44.9738, 'lon': -93.2581, 'roof_type': 'fixed_dome'},
    
    # NFC South
    'ATL': {'name': 'Mercedes-Benz Stadium', 'lat': 33.7553, 'lon': -84.4006, 'roof_type': 'retractable'},
    'CAR': {'name': 'Bank of America Stadium', 'lat': 35.2258, 'lon': -80.8528, 'roof_type': 'open'},
    'NO': {'name': 'Caesars Superdome', 'lat': 29.9511, 'lon': -90.0812, 'roof_type': 'fixed_dome'},
    'TB': {'name': 'Raymond James Stadium', 'lat': 27.9759, 'lon': -82.5033, 'roof_type': 'open'},
    
    # NFC West
    'ARI': {'name': 'State Farm Stadium', 'lat': 33.5276, 'lon': -112.2626, 'roof_type': 'retractable'},
    'LAR': {'name': 'SoFi Stadium', 'lat': 33.9535, 'lon': -118.3392, 'roof_type': 'fixed_dome'},
    'SF': {'name': "Levi's Stadium", 'lat': 37.4032, 'lon': -121.9698, 'roof_type': 'open'},
    'SEA': {'name': 'Lumen Field', 'lat': 47.5952, 'lon': -122.3316, 'roof_type': 'open'}
}


class StadiumRegistry:
    """
    Stadium registry for weather exposure logic
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.stadiums = NFL_STADIUMS
        
    def get_stadium_info(self, team: str) -> Optional[Dict]:
        """
        Get stadium information for a team
        
        Args:
            team: Team abbreviation (e.g., 'KC', 'BUF')
            
        Returns:
            Dict with stadium info or None if team not found
        """
        return self.stadiums.get(team.upper())
    
    def is_weather_exposed(self, team: str, game_id: Optional[str] = None) -> Dict:
        """
        Determine if a team's game is exposed to weather conditions
        
        Args:
            team: Team abbreviation
            game_id: Optional game ID to check for roof overrides
            
        Returns:
            Dict with exposure status and reasoning
        """
        stadium_info = self.get_stadium_info(team)
        if not stadium_info:
            return {'exposed': True, 'reason': 'Unknown stadium - assuming outdoor'}
        
        roof_type = stadium_info['roof_type']
        
        if roof_type == 'open':
            return {'exposed': True, 'reason': 'Open stadium'}
        
        elif roof_type == 'fixed_dome':
            return {'exposed': False, 'reason': 'Fixed dome - climate controlled'}
        
        elif roof_type == 'retractable':
            # Default assumption for retractable roofs (no database override checking for simplicity)
            return {
                'exposed': True,  # Conservative assumption - fetch weather data
                'reason': 'Retractable roof - status unknown, assuming open',
                'override_applied': False
            }
        
        return {'exposed': True, 'reason': 'Unknown roof type - assuming outdoor'}
    
    def validate_team(self, team: str) -> bool:
        """
        Validate if team abbreviation exists in registry
        
        Args:
            team: Team abbreviation
            
        Returns:
            True if team exists, False otherwise
        """
        return team.upper() in self.stadiums
