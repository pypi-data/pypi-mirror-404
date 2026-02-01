"""
Weather Processor for NOAA Weather Integration

Consolidated weather processing with all functionality in one place for simplicity.
"""

from typing import Dict, List, Optional
from datetime import datetime
import typer

from .noaa_client import NOAAWeatherClient
from .nlp_parser import WeatherNLPParser
from ..utils.stadium_registry import StadiumRegistry
from .models import GameWeather, categorize_temperature, categorize_wind


class WeatherProcessor:
    """
    Complete weather processor that handles all weather analysis and display
    """
    
    def __init__(self, db_connection=None, logger=None):
        self.db = db_connection
        self.logger = logger
        
        # Core components
        self.noaa_client = NOAAWeatherClient(db_connection, logger)
        self.nlp_parser = WeatherNLPParser()
        self.stadium_registry = StadiumRegistry(db_connection)
        
        # Weather emojis for display
        self.weather_emojis = {
            'clear': '☀️',
            'sunny': '☀️',
            'partly_cloudy': '⛅',
            'cloudy': '☁️',
            'rain': '🌧️',
            'heavy_rain': '⛈️',
            'snow': '❄️',
            'heavy_snow': '🌨️',
            'sleet': '🌨️',
            'thunderstorm': '⛈️',
            'fog': '🌫️',
            'wind': '💨',
            'dome': '🏟️',
            'cold': '🥶',
            'hot': '🔥'
        }
        
        # Weather impact scoring weights
        self.impact_weights = {
            'temperature': {
                'very_cold': 3.0,  # Below 20°F
                'cold': 2.0,       # 20-32°F
                'cool': 1.0,       # 33-45°F
                'mild': 0.0,       # 46-60°F
                'warm': 0.5,       # 61-75°F
                'hot': 1.5         # Above 75°F
            },
            'wind': {
                'calm': 0.0,       # 0-5 mph
                'light': 0.5,      # 5-10 mph
                'moderate': 1.5,   # 10-20 mph
                'strong': 3.0,     # 20-30 mph
                'very_strong': 4.0 # 30+ mph
            },
            'precipitation': {
                'none': 0.0,
                'trace': 0.5,
                'light': 1.0,
                'moderate': 2.5,
                'heavy': 4.0
            },
            'special_conditions': {
                'thunder': 2.0,
                'freezing': 1.5,
                'wind': 1.0,
                'visibility': 1.0,
                'severe': 3.0
            }
        }
    
    def process_game_weather(self, home_team: str, away_team: str, game_id: Optional[str] = None, 
                           game_time: Optional[datetime] = None, season: Optional[int] = None, week: Optional[int] = None) -> Optional[GameWeather]:
        """
        Process complete weather analysis for a game
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            game_id: Optional game ID
            game_time: Optional game start time
            season: Optional season year
            week: Optional week number
            
        Returns:
            GameWeather instance with complete analysis
        """
        try:
            # Get raw weather data (use home team's stadium)
            weather_data = self.noaa_client.get_weather_for_team(home_team, game_id)
            if not weather_data:
                if self.logger:
                    self.logger.warning(f"No weather data available for {home_team} vs {away_team}")
                return None
            
            # Extract forecast period for game time
            forecast_period = self._get_game_forecast_period(weather_data, game_time)
            if not forecast_period:
                if self.logger:
                    self.logger.warning(f"No forecast period found for game time")
                return None
            
            # Parse precipitation with NLP
            precipitation_analysis = self.nlp_parser.get_dominant_condition(
                forecast_period.get('shortForecast', '')
            )
            
            # Extract basic weather metrics
            temperature = forecast_period.get('temperature')
            wind_speed_str = forecast_period.get('windSpeed', '0 mph')
            wind_speed_mph = self.noaa_client.extract_wind_speed(wind_speed_str)
            
            # Get stadium and roof information
            stadium_info = weather_data['stadium']
            exposure_info = weather_data['exposure_info']
            
            # Create GameWeather instance
            game_weather = GameWeather(
                game_id=game_id,
                season=season or datetime.now().year,
                week=week or 1,
                home_team=home_team,
                away_team=away_team,
                game_time=game_time,
                stadium_name=stadium_info['name'],
                is_dome=stadium_info['roof_type'] == 'fixed_dome',
                roof_type=stadium_info['roof_type'],
                roof_override_applied=exposure_info.get('override_applied', False),
                temperature=temperature,
                wind_speed_mph=wind_speed_mph,
                wind_direction=forecast_period.get('windDirection'),
                precipitation_analysis=precipitation_analysis,
                forecast_updated_at=datetime.now(),
                created_at=datetime.now()
            )
            
            # Process all weather analysis
            self._process_weather_categories(game_weather)
            self._calculate_weather_impact(game_weather)
            self._analyze_betting_tendencies(game_weather)
            self._generate_weather_description(game_weather)
            self._generate_weather_factors(game_weather)
            
            return game_weather
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error processing game weather for {home_team} vs {away_team}: {e}")
            return None
    
    def _get_game_forecast_period(self, weather_data: Dict, game_time: Optional[datetime] = None) -> Optional[Dict]:
        """Get the forecast period that matches the game time"""
        forecast_data = weather_data.get('forecast', {})
        
        if game_time:
            # Try to find exact period match (returns None if too far in future)
            period = self.noaa_client.find_game_period(forecast_data, game_time)
            return period  # Could be None if game is too far in future
        
        # Default to first available period only if no game time provided
        periods = forecast_data.get('properties', {}).get('periods', [])
        return periods[0] if periods else None
    
    def _process_weather_categories(self, game_weather: GameWeather):
        """Process weather data into categorical formats"""
        # Temperature categorization
        if game_weather.temperature is not None:
            game_weather.temperature_category = categorize_temperature(game_weather.temperature)
        
        # Wind categorization
        if game_weather.wind_speed_mph is not None:
            game_weather.wind_category = categorize_wind(game_weather.wind_speed_mph)
        
        # Precipitation categorization
        if game_weather.precipitation_analysis:
            game_weather.precipitation_type = game_weather.precipitation_analysis['precipitation_type']
            game_weather.precipitation_intensity = game_weather.precipitation_analysis['intensity_categorical']
            game_weather.has_thunder = game_weather.precipitation_analysis['has_thunder']
            game_weather.intensity_weight = game_weather.precipitation_analysis['intensity_weight']
            game_weather.special_conditions = game_weather.precipitation_analysis['special_conditions']
        
        # Roof status determination
        if game_weather.roof_type == 'fixed_dome':
            game_weather.roof_status = 'n/a'
        elif game_weather.roof_type == 'open':
            game_weather.roof_status = 'n/a'
        else:  # retractable
            game_weather.roof_status = 'open'  # Default assumption
    
    def _calculate_weather_impact(self, game_weather: GameWeather):
        """Calculate comprehensive weather impact scoring"""
        impact_score = 0.0
        
        # Temperature impact
        temp_impact = self.impact_weights['temperature'].get(game_weather.temperature_category, 0.0)
        impact_score += temp_impact
        
        # Wind impact
        wind_impact = self.impact_weights['wind'].get(game_weather.wind_category, 0.0)
        impact_score += wind_impact
        
        # Precipitation impact
        precip_impact = self.impact_weights['precipitation'].get(game_weather.precipitation_intensity, 0.0)
        impact_score += precip_impact
        
        # Special conditions impact
        if game_weather.special_conditions:
            for condition in game_weather.special_conditions:
                condition_impact = self.impact_weights['special_conditions'].get(condition, 0.0)
                impact_score += condition_impact
        
        # Dome adjustment - no weather impact for domed stadiums
        if game_weather.is_dome or game_weather.roof_status == 'closed':
            impact_score = 0.0
        
        # Set impact level and score
        game_weather.impact_score = round(impact_score, 1)
        
        if impact_score >= 4.0:
            game_weather.impact_level = 'high'
        elif impact_score >= 2.0:
            game_weather.impact_level = 'medium'
        elif impact_score >= 1.0:
            game_weather.impact_level = 'low'
        else:
            game_weather.impact_level = 'none'
    
    def _analyze_betting_tendencies(self, game_weather: GameWeather):
        """Analyze how weather conditions affect betting tendencies"""
        # Factors that favor UNDER
        under_factors = []
        
        # Cold weather tends to favor under
        if game_weather.temperature_category in ['very_cold', 'cold']:
            under_factors.append('cold_weather')
        
        # High winds favor under (especially passing games)
        if game_weather.wind_category in ['strong', 'very_strong']:
            under_factors.append('high_winds')
        
        # Precipitation favors under
        if game_weather.precipitation_intensity in ['moderate', 'heavy']:
            under_factors.append('precipitation')
        
        # Snow especially favors under
        if game_weather.precipitation_type == 'snow':
            under_factors.append('snow')
        
        # Thunderstorms favor under
        if game_weather.has_thunder:
            under_factors.append('thunderstorm')
        
        game_weather.favors_under = len(under_factors) >= 2 or game_weather.impact_score >= 3.0
        
        # Factors that favor RUSHING
        rushing_factors = []
        
        # Bad weather favors ground game
        if game_weather.precipitation_intensity in ['moderate', 'heavy']:
            rushing_factors.append('precipitation')
        
        if game_weather.wind_category in ['strong', 'very_strong']:
            rushing_factors.append('wind')
        
        if game_weather.precipitation_type in ['snow', 'sleet']:
            rushing_factors.append('winter_weather')
        
        game_weather.favors_rushing = len(rushing_factors) >= 1 or game_weather.impact_score >= 2.5
    
    def _generate_weather_description(self, game_weather: GameWeather):
        """Generate human-readable weather description"""
        if game_weather.is_dome or game_weather.roof_status == 'closed':
            game_weather.weather_description = "Indoor dome conditions"
            game_weather.weather_emoji = self.weather_emojis['dome']
            return
        
        description_parts = []
        emoji = self.weather_emojis['partly_cloudy']  # default
        
        # Temperature description
        if game_weather.temperature is not None:
            temp_desc = f"{game_weather.temperature}°F"
            if game_weather.temperature_category == 'very_cold':
                temp_desc += " (very cold)"
                emoji = self.weather_emojis['cold']
            elif game_weather.temperature_category == 'cold':
                temp_desc += " (cold)"
            elif game_weather.temperature_category == 'hot':
                temp_desc += " (hot)"
                emoji = self.weather_emojis['hot']
            
            description_parts.append(temp_desc)
        
        # Wind description
        if game_weather.wind_speed_mph and game_weather.wind_speed_mph > 10:
            wind_desc = f"{game_weather.wind_speed_mph} mph winds"
            if game_weather.wind_speed_mph >= 20:
                wind_desc = f"Strong {wind_desc}"
                emoji = self.weather_emojis['wind']
            description_parts.append(wind_desc)
        
        # Precipitation description
        if game_weather.precipitation_type != 'none':
            precip_desc = game_weather.precipitation_type
            if game_weather.precipitation_intensity != 'none':
                precip_desc = f"{game_weather.precipitation_intensity} {precip_desc}"
            
            # Set appropriate emoji
            if game_weather.precipitation_type == 'snow':
                emoji = self.weather_emojis['heavy_snow'] if game_weather.precipitation_intensity == 'heavy' else self.weather_emojis['snow']
            elif game_weather.precipitation_type == 'rain':
                emoji = self.weather_emojis['heavy_rain'] if game_weather.precipitation_intensity == 'heavy' else self.weather_emojis['rain']
            elif game_weather.precipitation_type == 'thunderstorm':
                emoji = self.weather_emojis['thunderstorm']
            elif game_weather.precipitation_type == 'fog':
                emoji = self.weather_emojis['fog']
            
            description_parts.append(precip_desc)
        
        # Combine description
        if description_parts:
            game_weather.weather_description = ", ".join(description_parts)
        else:
            game_weather.weather_description = "Fair conditions"
            emoji = self.weather_emojis['sunny']
        
        game_weather.weather_emoji = emoji
    
    def _generate_weather_factors(self, game_weather: GameWeather):
        """Generate weather factors for edge calculation"""
        factors = []
        
        # Temperature factors
        if game_weather.temperature_category == 'very_cold':
            factors.append('extreme_cold_weather')
        elif game_weather.temperature_category == 'cold':
            factors.append('cold_weather')
        elif game_weather.temperature_category == 'hot':
            factors.append('hot_weather')
        
        # Wind factors
        if game_weather.wind_category == 'very_strong':
            factors.append('extreme_wind_conditions')
        elif game_weather.wind_category == 'strong':
            factors.append('high_wind_conditions')
        elif game_weather.wind_category == 'moderate':
            factors.append('moderate_wind_conditions')
        
        # Precipitation factors
        if game_weather.precipitation_type == 'snow':
            factors.append('snow_conditions')
        elif game_weather.precipitation_type == 'rain' and game_weather.precipitation_intensity in ['moderate', 'heavy']:
            factors.append('heavy_rain_conditions')
        elif game_weather.precipitation_type == 'thunderstorm':
            factors.append('thunderstorm_conditions')
        elif game_weather.precipitation_type == 'sleet':
            factors.append('icy_conditions')
        
        # Combined factors
        if game_weather.favors_under:
            factors.append('weather_favors_under')
        
        if game_weather.favors_rushing:
            factors.append('weather_favors_rushing')
        
        # Dome factor
        if game_weather.is_dome:
            factors.append('dome_stadium')
        
        game_weather.weather_factors = factors
    
    def get_weather_summary(self, game_weather: GameWeather) -> Dict:
        """
        Get concise weather summary for display
        
        Args:
            game_weather: GameWeather instance
            
        Returns:
            Dict with summary information
        """
        return {
            'description': game_weather.weather_description,
            'emoji': game_weather.weather_emoji,
            'impact_level': game_weather.impact_level,
            'impact_score': game_weather.impact_score,
            'temperature': game_weather.temperature,
            'wind_speed': game_weather.wind_speed_mph,
            'precipitation': game_weather.precipitation_type,
            'favors_under': game_weather.favors_under,
            'favors_rushing': game_weather.favors_rushing,
            'is_dome': game_weather.is_dome,
            'significant': game_weather.is_significant_weather()
        }
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """
        Smart text truncation that preserves readability
        
        Args:
            text: Text to truncate
            max_length: Maximum length allowed
            
        Returns:
            Truncated text with smart word boundaries
        """
        if not text or len(text) <= max_length:
            return text
        
        # Common abbreviations for stadium names
        abbreviations = {
            'Stadium': 'Stad',
            'Field': 'Fld',
            'Center': 'Ctr',
            'Memorial': 'Mem',
            'University': 'Univ',
            'International': 'Intl',
            'Financial': 'Fin',
            'National': 'Natl',
            'American': 'Am',
            'Corporate': 'Corp'
        }
        
        # Apply abbreviations first
        abbreviated_text = text
        for full, abbrev in abbreviations.items():
            abbreviated_text = abbreviated_text.replace(full, abbrev)
        
        # If still too long, truncate at word boundary
        if len(abbreviated_text) <= max_length:
            return abbreviated_text
        
        # Find last space before max_length
        truncate_pos = max_length - 3  # Leave room for "..."
        last_space = abbreviated_text.rfind(' ', 0, truncate_pos)
        
        if last_space > max_length // 2:  # Only use word boundary if it's not too short
            return abbreviated_text[:last_space] + "..."
        else:
            return abbreviated_text[:max_length - 3] + "..."
    
    def _smart_truncate_weather(self, text: str, max_length: int) -> str:
        """
        Smart truncation specifically for weather conditions
        
        Args:
            text: Weather description to truncate
            max_length: Maximum length allowed
            
        Returns:
            Truncated weather description with proper ellipsis
        """
        if not text or len(text) <= max_length:
            return text
        
        # Weather-specific abbreviations
        weather_abbreviations = {
            'thunderstorm': 'tstorm',
            'moderate': 'mod',
            'temperature': 'temp',
            'conditions': 'cond'
        }
        
        # Apply weather abbreviations first
        abbreviated_text = text
        for full, abbrev in weather_abbreviations.items():
            abbreviated_text = abbreviated_text.replace(full, abbrev)
        
        # If still too long, truncate at word boundary
        if len(abbreviated_text) <= max_length:
            return abbreviated_text
        
        # Find last space before max_length
        truncate_pos = max_length - 3  # Leave room for "..."
        last_space = abbreviated_text.rfind(' ', 0, truncate_pos)
        
        # Don't break single important weather words
        important_words = ['thunderstorm', 'tstorm', 'snow', 'rain', 'wind', 'cold', 'hot']
        
        if last_space > max_length // 2:  # Only use word boundary if it's not too short
            truncated = abbreviated_text[:last_space]
            # Check if we're cutting an important word
            next_word = abbreviated_text[last_space:].split()[0] if last_space < len(abbreviated_text) else ""
            if any(word in next_word.lower() for word in important_words):
                # Try to include the important word if possible
                full_word_end = last_space + len(next_word)
                if full_word_end <= max_length:
                    return abbreviated_text[:full_word_end]
            return truncated + "..."
        else:
            return abbreviated_text[:max_length - 3] + "..."
    
    # CLI Display Functions
    

    def display_week_summary(self, games_weather: List[Dict], week_number: int, season: int):
        """Display week summary"""
        typer.echo(f"🏈 Week {week_number}, {season} Weather Summary ({len(games_weather)} games)")
        typer.echo("=" * 70)
        
        for game in games_weather:
            weather = game.get('weather', {})
            impact_emoji = {
                'none': '🟢',
                'low': '🟡', 
                'medium': '🟠',
                'high': '🔴'
            }.get(weather.get('impact_level', 'none'), '⚪')
            
            # Null-safe game time formatting
            game_time = game.get('game_time', 'TBD')
            if isinstance(game_time, datetime):
                game_time_str = game_time.strftime('%a %I:%M %p')
            else:
                game_time_str = str(game_time) if game_time is not None else 'TBD'
            
            # Null-safe team name formatting
            home_team = str(game.get('home_team') or 'UNK')
            away_team = str(game.get('away_team') or 'UNK')
            
            # Null-safe weather description formatting
            weather_desc = weather.get('description', 'No data')
            if weather_desc is None:
                weather_desc = 'No data'
            weather_desc_str = str(weather_desc)[:30]
            
            typer.echo(f"{impact_emoji} {home_team} vs {away_team:3} | {game_time_str:12} | {weather_desc_str:<30}")

    def display_week_full(self, games_weather: List[Dict], week_number: int, season: int):
        """Display full week information"""
        typer.echo(f"🏈 Week {week_number}, {season} Detailed Weather Analysis")
        typer.echo("=" * 70)
        
        for i, game in enumerate(games_weather, 1):
            weather = game.get('weather', {})
            
            # Null-safe team name formatting
            home_team = game.get('home_team') or 'UNK'
            away_team = game.get('away_team') or 'UNK'
            
            typer.echo(f"\n{i}. {home_team} vs {away_team}")
            
            game_time = game.get('game_time', 'TBD')
            if isinstance(game_time, datetime):
                typer.echo(f"   Time: {game_time.strftime('%A, %B %d at %I:%M %p')}")
            
            if weather:
                typer.echo(f"   Weather: {weather.get('emoji', '')} {weather.get('description', 'No data')}")
                typer.echo(f"   Impact: {weather.get('impact_level', 'unknown').upper()} (Score: {weather.get('impact_score', 0)})")
                
                if weather.get('favors_under') or weather.get('favors_rushing'):
                    tendencies = []
                    if weather.get('favors_under'):
                        tendencies.append("UNDER")
                    if weather.get('favors_rushing'):
                        tendencies.append("RUSHING")
                    typer.echo(f"   Betting Impact: Favors {' & '.join(tendencies)}")

    def display_week_dataframe(self, games_weather: List[Dict], week_number: int, season: int):
        """Display week data in structured dataframe format"""
        typer.echo(f"🏈 Week {week_number}, {season} Weather Data ({len(games_weather)} games)")
        typer.echo("=" * 150)
        
        # Header with improved column widths
        header = f"{'Matchup':<18} | {'Stadium':<30} | {'Roof':<12} | {'Location':<16} | {'Temp':<6} | {'Wind':<6} | {'Conditions':<45} | {'Impact':<8}"
        typer.echo(header)
        typer.echo("-" * 150)
        
        for game in games_weather:
            # Extract game data
            home_team = str(game.get('home_team') or 'UNK')
            away_team = str(game.get('away_team') or 'UNK')
            matchup = f"{away_team} @ {home_team}"
            
            # Extract stadium data from game_weather object
            game_weather_obj = game.get('game_weather')
            if game_weather_obj:
                # Smart stadium name truncation
                stadium_name = self._smart_truncate(game_weather_obj.stadium_name, 28) if game_weather_obj.stadium_name else 'Unknown'
                roof_type = game_weather_obj.roof_type
                
                # Get stadium coordinates from registry
                stadium_info = self.stadium_registry.get_stadium_info(home_team)
                if stadium_info:
                    location = f"{stadium_info['lat']:.2f},{stadium_info['lon']:.2f}"
                else:
                    location = "Unknown"
                
                # Weather data
                temp = f"{game_weather_obj.temperature}°F" if game_weather_obj.temperature else "N/A"
                wind = f"{game_weather_obj.wind_speed_mph}mph" if game_weather_obj.wind_speed_mph else "N/A"
                
                # Smart conditions truncation with better handling
                if game_weather_obj.weather_description:
                    conditions = self._smart_truncate_weather(game_weather_obj.weather_description, 43)
                else:
                    conditions = "N/A"
                impact = f"{game_weather_obj.impact_level.upper()}"
            else:
                # Handle case where no weather data is available (e.g., too far in future)
                stadium_info = game.get('stadium_info')
                if stadium_info:
                    stadium_name = self._smart_truncate(stadium_info['name'], 28)
                    roof_type = stadium_info.get('roof_type', 'unknown')
                    location = f"{stadium_info['lat']:.2f},{stadium_info['lon']:.2f}"
                else:
                    stadium_name = "Unknown"
                    roof_type = "unknown"
                    location = "Unknown"
                
                temp = "—"
                wind = "—"
                impact = "—"
                
                # Use forecast_status flag for clearer messaging
                status = game.get('forecast_status')
                if status == 'unavailable-too-far':
                    conditions = "Forecast not available (game is >7 days out)"
                else:
                    conditions = "Forecast not available"
            
            # Format row
            row = f"{matchup:<18} | {stadium_name:<30} | {roof_type:<12} | {location:<16} | {temp:<6} | {wind:<6} | {conditions:<45} | {impact:<8}"
            typer.echo(row)

    def display_today_dataframe(self, games_weather: List[Dict], today_date: datetime):
        """Display today's games in structured dataframe format"""
        typer.echo(f"🏈 Today's Games - {today_date.strftime('%A, %B %d, %Y')} ({len(games_weather)} games)")
        typer.echo("=" * 120)
        
        # Header
        header = f"{'Matchup':<20} | {'Stadium':<25} | {'Roof':<12} | {'Location':<18} | {'Temp':<6} | {'Wind':<6} | {'Conditions':<25} | {'Impact':<8}"
        typer.echo(header)
        typer.echo("-" * 120)
        
        for game in games_weather:
            # Extract game data
            home_team = str(game.get('home_team') or 'UNK')
            away_team = str(game.get('away_team') or 'UNK')
            matchup = f"{away_team} @ {home_team}"
            
            # Extract stadium data from game_weather object
            game_weather_obj = game.get('game_weather')
            if game_weather_obj:
                stadium_name = game_weather_obj.stadium_name[:23] if game_weather_obj.stadium_name else 'Unknown'
                roof_type = game_weather_obj.roof_type
                
                # Get stadium coordinates from registry
                stadium_info = self.stadium_registry.get_stadium_info(home_team)
                if stadium_info:
                    location = f"{stadium_info['lat']:.2f},{stadium_info['lon']:.2f}"
                else:
                    location = "Unknown"
                
                # Weather data
                temp = f"{game_weather_obj.temperature}°F" if game_weather_obj.temperature else "N/A"
                wind = f"{game_weather_obj.wind_speed_mph}mph" if game_weather_obj.wind_speed_mph else "N/A"
                conditions = game_weather_obj.weather_description[:23] if game_weather_obj.weather_description else "N/A"
                impact = f"{game_weather_obj.impact_level.upper()}"
            else:
                stadium_name = "Unknown"
                roof_type = "unknown"
                location = "Unknown"
                temp = "N/A"
                wind = "N/A"
                conditions = "No data"
                impact = "UNKNOWN"
            
            # Format row
            row = f"{matchup:<20} | {stadium_name:<25} | {roof_type:<12} | {location:<18} | {temp:<6} | {wind:<6} | {conditions:<25} | {impact:<8}"
            typer.echo(row)

    def display_today_summary(self, games_weather: List[Dict], today_date: datetime):
        """Display today's games summary"""
        typer.echo(f"🏈 Today's Games - {today_date.strftime('%A, %B %d, %Y')} ({len(games_weather)} games)")
        typer.echo("=" * 70)
        
        for game in games_weather:
            weather = game.get('weather', {})
            impact_emoji = {
                'none': '🟢',
                'low': '🟡', 
                'medium': '🟠',
                'high': '🔴'
            }.get(weather.get('impact_level', 'none'), '⚪')
            
            # Null-safe game time formatting
            game_time = game.get('gametime', 'TBD')
            game_time_str = str(game_time) if game_time is not None else 'TBD'
            
            # Null-safe team name formatting
            home_team = str(game.get('home_team') or 'UNK')
            away_team = str(game.get('away_team') or 'UNK')
            
            # Null-safe weather description formatting
            weather_desc = weather.get('description', 'No data')
            if weather_desc is None:
                weather_desc = 'No data'
            weather_desc_str = str(weather_desc)[:35]
            
            typer.echo(f"{impact_emoji} {home_team} vs {away_team:3} | {game_time_str:8} | {weather_desc_str:<35}")

    def display_today_full(self, games_weather: List[Dict], today_date: datetime):
        """Display full today's games information"""
        typer.echo(f"🏈 Today's Games - {today_date.strftime('%A, %B %d, %Y')} Detailed Analysis")
        typer.echo("=" * 70)
        
        for i, game in enumerate(games_weather, 1):
            weather = game.get('weather', {})
            
            # Null-safe team name formatting
            home_team = game.get('home_team') or 'UNK'
            away_team = game.get('away_team') or 'UNK'
            
            typer.echo(f"\n{i}. {home_team} vs {away_team}")
            
            game_time = game.get('game_time', 'TBD')
            if isinstance(game_time, datetime):
                typer.echo(f"   Time: {game_time.strftime('%A, %B %d at %I:%M %p')}")
            
            if weather:
                typer.echo(f"   Weather: {weather.get('emoji', '')} {weather.get('description', 'No data')}")
                typer.echo(f"   Impact: {weather.get('impact_level', 'unknown').upper()} (Score: {weather.get('impact_score', 0)})")
                
                if weather.get('favors_under') or weather.get('favors_rushing'):
                    tendencies = []
                    if weather.get('favors_under'):
                        tendencies.append("UNDER")
                    if weather.get('favors_rushing'):
                        tendencies.append("RUSHING")
                    typer.echo(f"   Betting Impact: Favors {' & '.join(tendencies)}")
