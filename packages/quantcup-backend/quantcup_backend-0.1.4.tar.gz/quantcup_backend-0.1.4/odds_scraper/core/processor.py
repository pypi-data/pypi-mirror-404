"""Data processing for Sportsbook odds."""
import re
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pytz

from commonv2 import get_logger

logger = get_logger(__name__)


class OddsDataProcessor:
    """
    Transform raw Sportsbook scrape data into structured DataFrame.
    
    Handles:
    - Date/time parsing and timezone conversion
    - Team data extraction
    - Odds normalization
    - Data validation
    """
    
    def process(self, raw_data: Dict, data_pull_id: str) -> pd.DataFrame:
        """
        Transform raw AgentQL response to DataFrame.
        
        Args:
            raw_data: Dict with 'games' key from AgentQL query
            data_pull_id: Unique identifier for this scrape
            
        Returns:
            Processed DataFrame with standardized columns
        """
        games = raw_data.get("games", [])
        if not games:
            logger.warning("No games found in raw data")
            return pd.DataFrame()
        
        logger.info(f"Processing {len(games)} games")
        
        start_time = datetime.now().isoformat()
        rows = []
        
        for game in games:
            game_rows = self._process_game(game, data_pull_id, start_time)
            rows.extend(game_rows)
        
        end_time = datetime.now().isoformat()
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        if df.empty:
            logger.warning("No valid team data found in games")
            return df
        
        # Add metadata
        df['data_pull_start_time'] = start_time
        df['data_pull_end_time'] = end_time
        df['bookmaker'] = 'Sportsbook'
        df['odds_format'] = 'American'
        
        # Convert numeric columns
        self._convert_numeric_columns(df)
        
        logger.info(f"Processed {len(df)} team records")
        return df
    
    def _process_game(self, game: Dict, data_pull_id: str, start_time: str) -> List[Dict]:
        """Process single game into team-level records."""
        header = game.get('header', '')
        date_str = game.get('date', '')
        time_str = game.get('time', '')
        event_url = game.get('event_url', '')
        
        # Parse date/time
        standardized_date = self._parse_date_string(date_str)
        if standardized_date:
            converted = self._convert_time_to_eastern(standardized_date, time_str)
            if converted:
                date_converted, time_converted = converted
            else:
                date_converted, time_converted = date_str, time_str
        else:
            date_converted, time_converted = date_str, time_str
        
        # Extract team data
        teams = game.get('teams', [])
        rows = []
        
        for team in teams:
            team_name = team.get('name', '')
            if not team_name:
                continue
            
            row = {
                'event_id': self._extract_event_id(event_url),
                'header': header,
                'date': date_converted,
                'time': time_converted,
                'team': team_name,
                'spread': team.get('spread', ''),
                'spread_odds': team.get('spread_odds', ''),
                'moneyline': team.get('moneyline', ''),
                'total_over': game.get('total_over', ''),
                'total_over_odds': game.get('total_over_odds', ''),
                'total_under': game.get('total_under', ''),
                'total_under_odds': game.get('total_under_odds', ''),
                'event_url': event_url,
                'data_pull_id': data_pull_id
            }
            rows.append(row)
        
        return rows
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse various date formats to YYYY-MM-DD."""
        if not date_str:
            return None
        
        date_str_clean = date_str.strip()
        
        # Handle relative dates
        relative_days = {'TODAY': 0, 'TOMORROW': 1, 'YESTERDAY': -1}
        if date_str_clean.upper() in relative_days:
            target_date = datetime.now() + timedelta(days=relative_days[date_str_clean.upper()])
            return target_date.strftime('%Y-%m-%d')
        
        # Remove ordinal suffixes (1st, 2nd, 3rd, 4th...)
        clean_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str_clean, flags=re.IGNORECASE)
        
        # Remove time if present (e.g., "Mon Dec 29 8:15 PM" -> "Mon Dec 29")
        clean_str = re.sub(r'\s+\d{1,2}:\d{2}\s*(?:AM|PM).*$', '', clean_str, flags=re.IGNORECASE)
        
        # Try common formats
        formats = [
            '%Y-%m-%d',       # 2025-12-27
            '%a %b %d',       # FRI NOV 15
            '%b %d, %Y',      # December 27, 2025
            '%m/%d/%Y',       # 12/27/2025
            '%d/%m/%Y',       # 27/12/2025
            '%Y/%m/%d',       # 2025/12/27
            '%b %d'           # NOV 15
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_str, fmt)
                if dt.year == 1900:  # If year was not in format
                    current_date = datetime.now()
                    dt = dt.replace(year=current_date.year)
                    # If the parsed date is more than 6 months in the past, it's likely next year
                    if (current_date - dt).days > 180:
                        dt = dt.replace(year=current_date.year + 1)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Fallback to pandas for more complex formats
        try:
            dt = pd.to_datetime(clean_str)
            if dt.year == 1900:
                current_date = datetime.now()
                dt = dt.replace(year=current_date.year)
                if (current_date - dt).days > 180:
                    dt = dt.replace(year=current_date.year + 1)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
            
        logger.warning(f"Failed to parse date: '{date_str}'")
        return None
    
    def _convert_time_to_eastern(self, date_str: str, time_str: str) -> Optional[tuple]:
        """Convert time to Eastern timezone."""
        if not date_str or not time_str:
            return None
        
        try:
            # Clean time string: remove spaces and ensure uppercase AM/PM
            time_str_clean = time_str.strip().upper().replace(" ", "")
            
            # Handle cases where minutes might be missing (e.g., "4 PM" -> "4:00PM")
            if ":" not in time_str_clean:
                time_str_clean = re.sub(r'(\d+)(AM|PM)', r'\1:00\2', time_str_clean)
                
            # Ensure 2-digit hour for %I (e.g., "4:30PM" -> "04:30PM")
            if re.match(r'^\d:', time_str_clean):
                time_str_clean = "0" + time_str_clean
                
            datetime_str = f"{date_str} {time_str_clean}"
            
            # Try to parse the cleaned datetime string
            try:
                naive_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M%p")
            except ValueError:
                # Fallback to pandas if strptime fails
                naive_datetime = pd.to_datetime(datetime_str).to_pydatetime()
            
            # Assume GMT and convert to Eastern
            gmt_timezone = pytz.timezone('GMT')
            gmt_datetime = gmt_timezone.localize(naive_datetime)
            eastern_timezone = pytz.timezone('America/New_York')
            eastern_datetime = gmt_datetime.astimezone(eastern_timezone)
            
            converted_date = eastern_datetime.strftime("%m/%d/%Y")
            converted_time = eastern_datetime.strftime("%I:%M%p")
            
            return converted_date, converted_time
        except Exception as e:
            logger.error(f"Time conversion failed: {e} (date: {date_str}, time: {time_str})")
            return None
    
    def _extract_event_id(self, event_url: str) -> Optional[int]:
        """Extract numeric event ID from Sportsbook URL."""
        if not event_url:
            return None
        
        match = re.search(r'/([^/]+)$', event_url)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                logger.warning(f"Non-numeric event ID in URL: {event_url}")
        return None
    
    def _convert_numeric_columns(self, df: pd.DataFrame):
        """Convert odds columns to numeric with validation."""
        numeric_cols = [
            'spread', 'spread_odds', 'moneyline',
            'total_over', 'total_over_odds', 'total_under', 'total_under_odds'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                before_nulls = df[col].isnull().sum()
                df[col] = pd.to_numeric(df[col], errors='coerce')
                after_nulls = df[col].isnull().sum()
                
                if after_nulls > before_nulls:
                    failed = after_nulls - before_nulls
                    logger.warning(f"Column '{col}': {failed} values failed numeric conversion")
