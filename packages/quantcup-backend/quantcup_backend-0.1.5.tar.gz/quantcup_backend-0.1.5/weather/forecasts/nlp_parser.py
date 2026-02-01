"""
Natural Language Processing for NOAA Weather Forecast Text

Provides robust parsing of NOAA forecast strings to extract precipitation type,
intensity, and special conditions with enhanced accuracy.
"""

import re
from typing import Dict, List


class WeatherNLPParser:
    """
    Advanced NLP parser for NOAA weather forecast text analysis
    
    Handles varied forecast language patterns with intensity weighting
    and special condition detection (thunder, fog, etc.)
    """
    
    def __init__(self):
        # Precipitation type patterns (order matters - most specific first)
        self.precip_patterns = {
            'thunderstorm': r'thunder|storm|t-storm|tstorm|lightning',
            'snow': r'snow|blizzard|flurries|snowfall',
            'sleet': r'sleet|freezing rain|ice pellets|freezing drizzle',
            'mixed': r'mix|wintry mix|rain.*snow|snow.*rain|sleet.*rain',
            'drizzle': r'drizzle|mist|sprinkle|light rain',
            'rain': r'rain|showers|downpour|precipitation',
            'fog': r'fog|haze|mist(?!.*rain)',  # Mist without rain context
            'none': r'clear|sunny|fair|partly cloudy|mostly sunny|mostly clear'
        }
        
        # Intensity modifiers with weights (0.0 = none, 1.0 = maximum)
        self.intensity_patterns = {
            'heavy': {'patterns': r'heavy|severe|torrential|intense|major', 'weight': 1.0},
            'moderate': {'patterns': r'moderate|steady|continuous', 'weight': 0.7},
            'light': {'patterns': r'light|slight|brief|scattered|minor', 'weight': 0.4},
            'chance': {'patterns': r'chance|possible|likely', 'weight': 0.3},
            'slight_chance': {'patterns': r'slight chance|small chance|low chance', 'weight': 0.2},
            'patchy': {'patterns': r'patchy|isolated|occasional|intermittent', 'weight': 0.3}
        }
        
        # Special condition flags
        self.special_flags = {
            'thunder': r'thunder|lightning|t-storm|tstorm|thunderstorm',
            'wind': r'windy|gusty|breezy|wind',
            'visibility': r'fog|haze|mist',
            'freezing': r'freezing|ice|icy',
            'severe': r'severe|warning|watch|advisory'
        }
        
        # Timing indicators
        self.timing_patterns = {
            'early': r'early|morning|am',
            'late': r'late|evening|night|pm',
            'then': r'then|becoming|changing to|followed by',
            'continuing': r'continuing|persistent|ongoing'
        }
        
    def parse_forecast(self, forecast_text: str) -> Dict:
        """
        Parse forecast text into structured precipitation data
        
        Args:
            forecast_text: NOAA short forecast string
            
        Returns:
            Dict with comprehensive precipitation analysis
        """
        if not forecast_text:
            return self._get_default_analysis()
        
        text_lower = forecast_text.lower().strip()
        
        # Detect precipitation type
        precip_type = self._detect_precipitation_type(text_lower)
        
        # Detect intensity
        intensity_analysis = self._detect_intensity(text_lower, precip_type)
        
        # Detect special conditions
        special_conditions = self._detect_special_conditions(text_lower)
        
        # Analyze timing
        timing_info = self._analyze_timing(text_lower)
        
        # Generate confidence score
        confidence = self._calculate_confidence(text_lower, precip_type, intensity_analysis)
        
        return {
            'precipitation_type': precip_type,
            'intensity_categorical': intensity_analysis['categorical'],
            'intensity_weight': intensity_analysis['weight'],
            'intensity_name': intensity_analysis['name'],
            'special_conditions': special_conditions,
            'has_thunder': 'thunder' in special_conditions,
            'has_freezing': 'freezing' in special_conditions,
            'timing_info': timing_info,
            'confidence_score': confidence,
            'original_text': forecast_text
        }
    
    def _detect_precipitation_type(self, text_lower: str) -> str:
        """Detect primary precipitation type from forecast text"""
        for ptype, pattern in self.precip_patterns.items():
            if re.search(pattern, text_lower):
                return ptype
        return 'none'
    
    def _detect_intensity(self, text_lower: str, precip_type: str) -> Dict:
        """Detect precipitation intensity with contextual weighting"""
        intensity_weight = 0.5  # default moderate
        intensity_name = 'moderate'
        
        # Check for explicit intensity modifiers
        for intensity, config in self.intensity_patterns.items():
            if re.search(config['patterns'], text_lower):
                intensity_weight = config['weight']
                intensity_name = intensity
                break
        
        # Contextual adjustments based on precipitation type
        if precip_type == 'thunderstorm':
            # Thunderstorms are inherently more intense
            intensity_weight = max(intensity_weight, 0.7)
        elif precip_type == 'drizzle':
            # Drizzle is inherently light
            intensity_weight = min(intensity_weight, 0.4)
        elif precip_type == 'none':
            intensity_weight = 0.0
            intensity_name = 'none'
        
        # Convert weight to categorical intensity
        categorical_intensity = self._weight_to_categorical(intensity_weight)
        
        return {
            'weight': intensity_weight,
            'name': intensity_name,
            'categorical': categorical_intensity
        }
    
    def _weight_to_categorical(self, weight: float) -> str:
        """Convert intensity weight to categorical description"""
        if weight >= 0.8:
            return 'heavy'
        elif weight >= 0.5:
            return 'moderate'
        elif weight >= 0.3:
            return 'light'
        elif weight > 0.0:
            return 'trace'
        else:
            return 'none'
    
    def _detect_special_conditions(self, text_lower: str) -> List[str]:
        """Detect special weather conditions"""
        conditions = []
        for condition, pattern in self.special_flags.items():
            if re.search(pattern, text_lower):
                conditions.append(condition)
        return conditions
    
    def _analyze_timing(self, text_lower: str) -> Dict:
        """Analyze timing information in forecast"""
        timing_info = {
            'has_timing': False,
            'early_period': False,
            'late_period': False,
            'changing_conditions': False,
            'persistent': False
        }
        
        for timing_type, pattern in self.timing_patterns.items():
            if re.search(pattern, text_lower):
                timing_info['has_timing'] = True
                if timing_type == 'early':
                    timing_info['early_period'] = True
                elif timing_type == 'late':
                    timing_info['late_period'] = True
                elif timing_type == 'then':
                    timing_info['changing_conditions'] = True
                elif timing_type == 'continuing':
                    timing_info['persistent'] = True
        
        return timing_info
    
    def _calculate_confidence(self, text_lower: str, precip_type: str, intensity_analysis: Dict) -> float:
        """Calculate confidence score for the analysis (0.0-1.0)"""
        confidence = 0.5  # base confidence
        
        # Higher confidence for explicit precipitation types
        if precip_type in ['snow', 'rain', 'thunderstorm']:
            confidence += 0.3
        elif precip_type == 'none' and re.search(r'clear|sunny|fair', text_lower):
            confidence += 0.3
        
        # Higher confidence for explicit intensity modifiers
        if intensity_analysis['name'] in ['heavy', 'light', 'moderate']:
            confidence += 0.2
        
        # Lower confidence for chance-based forecasts
        if re.search(r'chance|possible|likely', text_lower):
            confidence -= 0.2
        
        # Higher confidence for specific conditions
        if re.search(r'thunder|blizzard|fog', text_lower):
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _get_default_analysis(self) -> Dict:
        """Return default analysis for empty/invalid input"""
        return {
            'precipitation_type': 'none',
            'intensity_categorical': 'none',
            'intensity_weight': 0.0,
            'intensity_name': 'none',
            'special_conditions': [],
            'has_thunder': False,
            'has_freezing': False,
            'timing_info': {
                'has_timing': False,
                'early_period': False,
                'late_period': False,
                'changing_conditions': False,
                'persistent': False
            },
            'confidence_score': 1.0,
            'original_text': ''
        }
    
    def parse_multiple_conditions(self, forecast_text: str) -> List[Dict]:
        """
        Parse forecast text that may contain multiple conditions
        
        Args:
            forecast_text: NOAA forecast text
            
        Returns:
            List of condition analyses
        """
        # Split on common separators
        separators = [' then ', ' becoming ', ' followed by ', ' and ', ' with ']
        conditions = [forecast_text]
        
        for separator in separators:
            new_conditions = []
            for condition in conditions:
                new_conditions.extend(condition.split(separator))
            conditions = new_conditions
        
        # Parse each condition separately
        analyses = []
        for condition in conditions:
            condition = condition.strip()
            if condition:
                analysis = self.parse_forecast(condition)
                analyses.append(analysis)
        
        return analyses if analyses else [self._get_default_analysis()]
    
    def get_dominant_condition(self, forecast_text: str) -> Dict:
        """
        Get the most significant weather condition from complex forecast
        
        Args:
            forecast_text: NOAA forecast text
            
        Returns:
            Analysis of the most impactful condition
        """
        analyses = self.parse_multiple_conditions(forecast_text)
        
        if not analyses:
            return self._get_default_analysis()
        
        # Score each condition by impact potential
        def impact_score(analysis):
            score = 0
            
            # Precipitation type scoring
            type_scores = {
                'thunderstorm': 10,
                'snow': 9,
                'sleet': 8,
                'mixed': 7,
                'rain': 5,
                'drizzle': 3,
                'fog': 4,
                'none': 0
            }
            score += type_scores.get(analysis['precipitation_type'], 0)
            
            # Intensity scoring
            score += analysis['intensity_weight'] * 5
            
            # Special conditions
            if analysis['has_thunder']:
                score += 3
            if analysis['has_freezing']:
                score += 2
            
            return score
        
        # Return the highest impact condition
        return max(analyses, key=impact_score)

