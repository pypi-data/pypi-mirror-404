"""
NOAA Weather API Client

Provides integration with NOAA Weather API for real-time weather data retrieval
with proper rate limiting, error handling, and dome stadium support.
"""

import requests
import time
import re
import pytz
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from commonv2.core.logging import setup_logger
from ..utils.stadium_registry import StadiumRegistry


class NOAAWeatherClient:
    """
    NOAA Weather API client with enhanced roof handling and rate limiting
    """
    
    def __init__(self, db_connection=None, logger=None):
        self.base_url = "https://api.weather.gov"
        self.session = requests.Session()
        self.db = db_connection
        
        # Use injected logger or create default
        self.logger = logger or setup_logger('weather.forecasts.noaa_client', project_name='WEATHER')
        
        # Set required user agent for NOAA API compliance
        self.session.headers.update({
            "User-Agent": "QuantCup-NFL-Weather/1.0 (contact@quantcup.com)"
        })
        
        # Rate limiting configuration
        self.requests_made = 0
        self.last_request_time = None
        self.min_request_interval = 1.0  # 1 second between requests (conservative)
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Stadium registry for coordinates and roof types
        self.stadium_registry = StadiumRegistry(db_connection)
        
        # Cache for grid information (reduces API calls)
        self._grid_cache = {}
        
    
    def get_weather_for_team(self, team: str, game_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get weather forecast for a specific team's stadium
        
        Args:
            team: Team abbreviation
            game_id: Optional game ID for roof override checking
            
        Returns:
            Dict containing weather forecast data or None if unavailable
        """
        try:
            # Get stadium information
            stadium_info = self.stadium_registry.get_stadium_info(team)
            if not stadium_info:
                self.logger.error(f"Stadium information not found for team: {team}")
                return None
            
            # Check if weather exposure is needed
            exposure_info = self.stadium_registry.is_weather_exposed(team, game_id)
            
            if not exposure_info['exposed']:
                # Return dome conditions for non-exposed stadiums
                return self._get_dome_conditions(team, stadium_info, exposure_info['reason'])
            
            # Get live weather data for exposed stadiums
            return self._get_live_weather_data(team, stadium_info)
            
        except Exception as e:
            self.logger.error(f"Error getting weather for team {team}: {e}")
            return None
    
    def _get_live_weather_data(self, team: str, stadium_info: Dict) -> Optional[Dict]:
        """Get live weather data from NOAA API"""
        try:
            # Step 1: Get forecast grid information
            grid_info = self._get_forecast_grid(
                stadium_info['lat'], 
                stadium_info['lon'],
                team
            )
            if not grid_info:
                self.logger.warning(f"Could not get grid info for {team}")
                return None
            
            # Step 2: Get detailed forecast
            forecast_data = self._get_detailed_forecast(grid_info)
            if not forecast_data:
                self.logger.warning(f"Could not get forecast data for {team}")
                return None
            
            return {
                'team': team,
                'stadium': stadium_info,
                'grid_info': grid_info,
                'forecast': forecast_data,
                'exposure_info': {'exposed': True, 'reason': 'Live weather data'}
            }
            
        except Exception as e:
            self.logger.error(f"Error getting live weather data for {team}: {e}")
            return None
    
    def _get_forecast_grid(self, lat: float, lon: float, team: Optional[str] = None) -> Optional[Dict]:
        """
        Get forecast grid information for coordinates with caching
        
        Args:
            lat: Latitude
            lon: Longitude
            team: Team abbreviation for caching
            
        Returns:
            Dict with grid information or None if failed
        """
        # Check cache first
        cache_key = f"{lat},{lon}"
        if cache_key in self._grid_cache:
            cached_data = self._grid_cache[cache_key]
            # Use cached data if less than 24 hours old
            if (datetime.now() - cached_data['timestamp']).total_seconds() < 86400:
                return cached_data['data']
        
        endpoint = f"{self.base_url}/points/{lat},{lon}"
        
        for attempt in range(self.max_retries):
            try:
                self._enforce_rate_limit()
                
                response = self.session.get(endpoint, timeout=30)
                response.raise_for_status()
                
                self.requests_made += 1
                self.last_request_time = datetime.now(timezone.utc)
                
                data = response.json()
                properties = data.get('properties', {})
                
                grid_info = {
                    'office': properties.get('gridId'),
                    'grid_x': properties.get('gridX'),
                    'grid_y': properties.get('gridY'),
                    'forecast_url': properties.get('forecast'),
                    'forecast_hourly_url': properties.get('forecastHourly')
                }
                
                # Cache the result
                self._grid_cache[cache_key] = {
                    'data': grid_info,
                    'timestamp': datetime.now()
                }
                
                office = grid_info.get('office', 'unknown')
                grid_x = grid_info.get('grid_x', 'unknown')
                grid_y = grid_info.get('grid_y', 'unknown')
                self.logger.info(f"Retrieved grid info for {team or 'coordinates'}: {office}/{grid_x},{grid_y}")
                return grid_info
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    self.logger.error(f"Grid point not found for coordinates {lat},{lon}")
                    return None
                elif e.response.status_code == 429:
                    # Rate limited - wait and retry
                    self.logger.warning(f"Rate limited on grid request, attempt {attempt + 1}")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    self.logger.error(f"HTTP error getting grid info: {e}")
                    if attempt == self.max_retries - 1:
                        return None
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error getting grid info: {e}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(self.retry_delay)
        
        return None
    
    def _get_detailed_forecast(self, grid_info: Dict) -> Optional[Dict]:
        """
        Get detailed forecast from grid information
        
        Args:
            grid_info: Grid information from points endpoint
            
        Returns:
            Forecast data or None if failed
        """
        forecast_url = grid_info.get('forecast_url')
        if not forecast_url:
            self.logger.error("No forecast URL in grid info")
            return None
        
        for attempt in range(self.max_retries):
            try:
                self._enforce_rate_limit()
                
                response = self.session.get(forecast_url, timeout=30)
                response.raise_for_status()
                
                self.requests_made += 1
                self.last_request_time = datetime.now(timezone.utc)
                
                forecast_data = response.json()
                self.logger.info(f"Retrieved forecast data with {len(forecast_data.get('properties', {}).get('periods', []))} periods")
                return forecast_data
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    self.logger.error(f"Forecast not found for URL: {forecast_url}")
                    return None
                elif e.response.status_code == 429:
                    # Rate limited - wait and retry
                    self.logger.warning(f"Rate limited on forecast request, attempt {attempt + 1}")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    self.logger.error(f"HTTP error getting forecast: {e}")
                    if attempt == self.max_retries - 1:
                        return None
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error getting forecast: {e}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(self.retry_delay)
        
        return None
    
    def _get_dome_conditions(self, team: str, stadium_info: Dict, reason: str) -> Dict:
        """
        Return standard dome conditions for indoor/closed roof stadiums
        
        Args:
            team: Team abbreviation
            stadium_info: Stadium information
            reason: Reason for dome conditions
            
        Returns:
            Dict with dome weather conditions
        """
        return {
            'team': team,
            'stadium': stadium_info,
            'grid_info': None,
            'forecast': {
                'properties': {
                    'periods': [{
                        'number': 1,
                        'name': 'Game Time',
                        'startTime': datetime.now().isoformat(),
                        'endTime': (datetime.now()).isoformat(),
                        'isDaytime': True,
                        'temperature': 72,
                        'temperatureUnit': 'F',
                        'windSpeed': '0 mph',
                        'windDirection': 'N',
                        'shortForecast': 'Indoor Dome',
                        'detailedForecast': 'Climate controlled indoor stadium conditions'
                    }]
                }
            },
            'exposure_info': {'exposed': False, 'reason': reason}
        }
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        if self.last_request_time:
            time_since_last = (datetime.now(timezone.utc) - self.last_request_time).total_seconds()
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                time.sleep(sleep_time)
    
    
    def extract_wind_speed(self, wind_speed_str: str) -> int:
        """
        Extract numeric wind speed from NOAA wind speed string
        
        Args:
            wind_speed_str: Wind speed string like "15 mph" or "10 to 20 mph"
            
        Returns:
            Wind speed in mph as integer
        """
        if not wind_speed_str:
            return 0
        
        # Handle range patterns like "10 to 20 mph"
        range_match = re.search(r'(\d+)\s*to\s*(\d+)', wind_speed_str)
        if range_match:
            # Use the higher value for conservative impact assessment
            return int(range_match.group(2))
        
        # Handle single value patterns like "15 mph"
        single_match = re.search(r'(\d+)', wind_speed_str)
        if single_match:
            return int(single_match.group(1))
        
        return 0
    
    def find_game_period(self, forecast_data: Dict, game_time: Optional[datetime]) -> Optional[Dict]:
        """
        Find the forecast period that best matches game time
        
        Args:
            forecast_data: NOAA forecast response
            game_time: Game start time
            
        Returns:
            Best matching forecast period or None if game too far in future
        """
        # Maximum hours from game time for valid forecast (7 days)
        MAX_HOURS = 168
        
        periods = forecast_data.get('properties', {}).get('periods', [])
        
        if not periods:
            return None
        
        if game_time is None:
            self.logger.info("No game time provided, using first available period")
            return periods[0]
        
        # Normalize game time to UTC for comparison
        if game_time.tzinfo is None:
            game_time = pytz.utc.localize(game_time)
        else:
            game_time = game_time.astimezone(pytz.utc)
        
        best_period = None
        min_distance = float('inf')
        
        for period in periods:
            try:
                start_time = datetime.fromisoformat(period['startTime'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(period['endTime'].replace('Z', '+00:00'))
                
                # Check if game time falls within period
                if start_time <= game_time <= end_time:
                    self.logger.info(f"Found exact period match for game time")
                    return period
                
                # Calculate distance to period (prefer periods that start before game time)
                if game_time < start_time:
                    distance = (start_time - game_time).total_seconds()
                else:
                    distance = (game_time - end_time).total_seconds()
                
                if distance < min_distance:
                    min_distance = distance
                    best_period = period
                    
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Error parsing period time: {e}")
                continue
        
        if best_period:
            hours_diff = min_distance / 3600
            
            # Check if the closest period is too far from game time
            if min_distance > MAX_HOURS * 3600:
                self.logger.warning(f"Game time is {hours_diff:.1f} hours from closest forecast period (max: {MAX_HOURS}h). Forecast not reliable.")
                return None
            
            self.logger.info(f"Using closest period (±{hours_diff:.1f} hours from game time)")
            return best_period
        
        # Fallback to first period only if it's within reasonable range
        if periods:
            first_period = periods[0]
            try:
                start_time = datetime.fromisoformat(first_period['startTime'].replace('Z', '+00:00'))
                distance = abs((game_time - start_time).total_seconds())
                hours_diff = distance / 3600
                
                if distance <= MAX_HOURS * 3600:
                    self.logger.info(f"Using first available period ({hours_diff:.1f} hours from game time)")
                    return first_period
                else:
                    self.logger.warning(f"First period is {hours_diff:.1f} hours from game time (max: {MAX_HOURS}h). No suitable forecast available.")
                    return None
            except (KeyError, ValueError):
                pass
        
        self.logger.warning("No suitable forecast period found within time window")
        return None
