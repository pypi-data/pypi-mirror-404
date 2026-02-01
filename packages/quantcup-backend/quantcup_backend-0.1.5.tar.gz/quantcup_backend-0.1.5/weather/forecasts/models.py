"""
Data Models for NOAA Weather API Integration

Defines data structures for game weather following the established QuantCup data model patterns.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import json


@dataclass
class GameWeather:
    """
    Processed game weather data with impact assessment
    """
    id: Optional[int] = None
    
    # Game Context
    game_id: Optional[str] = None
    season: int = 0
    week: int = 0
    home_team: str = ""
    away_team: str = ""
    game_time: Optional[datetime] = None
    
    # Stadium Info
    stadium_name: str = ""
    is_dome: bool = False
    roof_type: str = "open"
    roof_status: Optional[str] = None  # 'open', 'closed', 'n/a'
    roof_override_applied: bool = False
    
    # Weather Conditions
    temperature: Optional[int] = None
    temperature_category: str = "mild"  # 'very_cold', 'cold', 'cool', 'mild', 'warm', 'hot'
    wind_speed_mph: Optional[int] = None
    wind_category: str = "calm"  # 'calm', 'light', 'moderate', 'strong', 'very_strong'
    wind_direction: Optional[str] = None
    precipitation_type: str = "none"  # 'none', 'rain', 'snow', 'sleet', 'mixed'
    precipitation_intensity: str = "none"  # 'none', 'light', 'moderate', 'heavy'
    
    # Enhanced Precipitation Analysis
    precipitation_analysis: Optional[Dict] = None
    special_conditions: Optional[List[str]] = None
    has_thunder: bool = False
    intensity_weight: Optional[float] = None
    
    # Processed Weather Impact
    weather_description: str = ""
    weather_emoji: str = "🌤️"
    
    # Betting Impact Assessment
    impact_level: str = "none"  # 'none', 'low', 'medium', 'high'
    impact_score: float = 0.0  # 0.0-10.0 scale
    favors_under: bool = False
    favors_rushing: bool = False
    
    # Factor Generation
    weather_factors: Optional[List[str]] = None
    
    # Metadata
    forecast_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.precipitation_analysis is None:
            self.precipitation_analysis = {}
        if self.special_conditions is None:
            self.special_conditions = []
        if self.weather_factors is None:
            self.weather_factors = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return {
            'game_id': self.game_id,
            'season': self.season,
            'week': self.week,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'game_time': self.game_time,
            'stadium_name': self.stadium_name,
            'is_dome': self.is_dome,
            'roof_type': self.roof_type,
            'roof_status': self.roof_status,
            'roof_override_applied': self.roof_override_applied,
            'temperature': self.temperature,
            'temperature_category': self.temperature_category,
            'wind_speed_mph': self.wind_speed_mph,
            'wind_category': self.wind_category,
            'wind_direction': self.wind_direction,
            'precipitation_type': self.precipitation_type,
            'precipitation_intensity': self.precipitation_intensity,
            'precipitation_analysis': json.dumps(self.precipitation_analysis) if self.precipitation_analysis else None,
            'special_conditions': json.dumps(self.special_conditions) if self.special_conditions else None,
            'has_thunder': self.has_thunder,
            'intensity_weight': self.intensity_weight,
            'weather_description': self.weather_description,
            'weather_emoji': self.weather_emoji,
            'impact_level': self.impact_level,
            'impact_score': self.impact_score,
            'favors_under': self.favors_under,
            'favors_rushing': self.favors_rushing,
            'weather_factors': json.dumps(self.weather_factors) if self.weather_factors else None,
            'forecast_updated_at': self.forecast_updated_at,
            'created_at': self.created_at
        }
    
    def get_impact_summary(self) -> Dict:
        """Get summary of weather impact for display"""
        return {
            'level': self.impact_level,
            'score': self.impact_score,
            'description': self.weather_description,
            'emoji': self.weather_emoji,
            'favors_under': self.favors_under,
            'favors_rushing': self.favors_rushing,
            'factors': self.weather_factors[:3] if self.weather_factors else []  # Top 3 factors
        }
    
    def is_significant_weather(self) -> bool:
        """Check if weather conditions are significant for betting"""
        return (
            self.impact_level in ['medium', 'high'] or
            self.impact_score >= 3.0 or
            self.has_thunder or
            self.precipitation_type in ['snow', 'sleet', 'mixed'] or
            (self.temperature is not None and (self.temperature < 32 or self.temperature > 85)) or
            (self.wind_speed_mph is not None and self.wind_speed_mph >= 15)
        )




# Weather category mappings
TEMPERATURE_CATEGORIES = {
    'very_cold': (-100, 20),
    'cold': (20, 33),
    'cool': (33, 46),
    'mild': (46, 61),
    'warm': (61, 76),
    'hot': (76, 100)
}

WIND_CATEGORIES = {
    'calm': (0, 5),
    'light': (5, 10),
    'moderate': (10, 20),
    'strong': (20, 30),
    'very_strong': (30, 100)
}



def categorize_temperature(temp: int) -> str:
    """Categorize temperature into betting-relevant ranges"""
    for category, (min_temp, max_temp) in TEMPERATURE_CATEGORIES.items():
        if min_temp <= temp < max_temp:
            return category
    return 'mild'


def categorize_wind(wind_speed: int) -> str:
    """Categorize wind speed into betting-relevant ranges"""
    for category, (min_wind, max_wind) in WIND_CATEGORIES.items():
        if min_wind <= wind_speed < max_wind:
            return category
    return 'moderate'
