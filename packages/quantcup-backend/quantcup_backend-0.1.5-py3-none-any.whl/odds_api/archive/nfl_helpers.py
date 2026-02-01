
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Dict, Any




def calculate_nfl_week(kickoff_utc: datetime, season: int) -> int:
    """
    Calculate NFL week number for a given game kickoff time.
    
    Args:
        kickoff_utc: Game kickoff time in UTC
        season: NFL season year
    
    Returns:
        Week number (1-22, where 1-18 are regular season, 19-22 are playoffs)
        
    Implementation:
        - Week 1 starts first Thursday of September (typically Sept 5-11)
        - Each week is 7 days
        - Weeks 19-22 are playoffs (Wild Card, Divisional, Conference, Super Bowl)
    """
    # NFL season starts first Thursday of September
    # Use Sept 5 as baseline (confirmed for 2025)
    season_start = datetime(season, 9, 5, 0, 0, 0, tzinfo=timezone.utc)
    
    # Calculate days since season start
    days_since_start = (kickoff_utc - season_start).days
    
    # Calculate week number (1-indexed)
    week_num = (days_since_start // 7) + 1
    
    # Clamp to valid range (1-22)
    return max(1, min(22, week_num))

def classify_game_window(kickoff_utc: datetime) -> Dict[str, Any]:
    """
    Classify game into betting window (TNF, SNF, MNF, etc.).
    
    Args:
        kickoff_utc: Game kickoff time in UTC
    
    Returns:
        Dict with 'window_label' and 'kickoff_et' keys
        
    Window Labels:
        - TNF: Thursday Night Football
        - MNF: Monday Night Football
        - SNF: Sunday Night Football
        - SAT: Saturday games (late season)
        - SUN_EARLY: Sunday 1pm ET slot
        - SUN_LATE: Sunday 4pm ET slot
        - THANKSGIVING: Thanksgiving Day games
        - OTHER: All other games
    """
    et = kickoff_utc.astimezone(ZoneInfo('America/New_York'))
    
    weekday = et.weekday()  # 0=Monday, 6=Sunday
    hour = et.hour
    month = et.month
    day = et.day
    
    # Thanksgiving (4th Thursday in November - around Nov 22-28)
    if weekday == 3 and month == 11 and 22 <= day <= 28:
        return {'window_label': 'THANKSGIVING', 'kickoff_et': et}
    
    # Thursday Night Football
    if weekday == 3:
        return {'window_label': 'TNF', 'kickoff_et': et}
    
    # Monday Night Football
    elif weekday == 0:
        return {'window_label': 'MNF', 'kickoff_et': et}
    
    # Saturday games (late season)
    elif weekday == 5:
        return {'window_label': 'SAT', 'kickoff_et': et}
    
    # Sunday games
    elif weekday == 6:
        if hour < 16:
            return {'window_label': 'SUN_EARLY', 'kickoff_et': et}  # 9:30am London or 1pm ET
        elif 16 <= hour < 20:
            return {'window_label': 'SUN_LATE', 'kickoff_et': et}  # 4pm ET slot
        else:
            return {'window_label': 'SNF', 'kickoff_et': et}  # Sunday Night Football
    
    # Catch-all for other times (Christmas, etc.)
    else:
        return {'window_label': 'OTHER', 'kickoff_et': et}
