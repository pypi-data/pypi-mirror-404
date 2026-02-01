"""
Calendar dimension builders for nflfastRv3.

Pattern: Enhanced simple functions (3 complexity points)
- Date dimension builder: 1 point
- Drive dimension builder: 1 point
- NFL calendar logic: +1 point

Preserves V2 sophistication:
- NFL season calendar logic
- Drive situation analysis
- Temporal pattern support

================================================================================
USAGE GUIDE: dim_date vs schedules (as of 11/1/25)
================================================================================

CURRENT STATUS:
- dim_date: Built by warehouse but NOT consumed by ML pipeline
- ML Pipeline: Uses dim_game.game_date for temporal features instead
- See docs/dim_date_vs_schedules_analysis.md for detailed comparison

DATA MODEL:
- 10,227 rows: Every single day from 1998-03-01 to 2026-02-28
- Includes offseason dates (March-July marked as season_type='OFF')
- Continuous time series with no gaps

FEATURES PROVIDED:
1. Calendar Features:
   - day_of_week, is_weekend, is_weekday, is_thursday, is_monday
   - day_of_year, week_of_year, quarter
   
2. NFL-Specific Features:
   - nfl_season: NFL season year (Sept-Feb boundary logic)
   - season_type: PRE (Aug) / REG (Sep-Dec) / POST (Jan-Feb) / OFF (Mar-Jul)
   - is_holiday: Thanksgiving, Christmas, New Year's flags

3. Temporal Components:
   - date, year, month, day

WHEN TO USE dim_date:
✅ Time series analysis requiring continuous dates (filling gaps)
✅ Calendar-based features (holidays, day-of-week patterns)
✅ Offseason analysis (draft timing, free agency periods)
✅ Season boundary logic (NFL season runs Sept-Feb)

WHEN NOT TO USE dim_date:
❌ Game-specific analysis (use schedules or dim_game instead)
❌ Team matchup data (use schedules or dim_game)
❌ Venue/weather context (use schedules)
❌ ML feature engineering (use dim_game - currently active approach)

COMPARISON WITH schedules:
- dim_date: 10,227 continuous dates with calendar features
- schedules: ~7,263 game dates with venue/weather metadata
- They serve DIFFERENT purposes and are NOT interchangeable
- schedules CANNOT replace dim_date (missing 2,964 offseason dates + no calendar features)

See docs/dim_date_vs_schedules_analysis.md for complete comparison and examples.
================================================================================
"""

import pandas as pd
from datetime import datetime, timedelta
from commonv2 import get_logger
from .dataframe_engine import DataFrameEngine
from .warehouse_utils import validate_table_data


def build_dim_date(engine, logger=None) -> pd.DataFrame:
    """
    Build date dimension with NFL season calendar logic.
    
    Preserves V2 features:
    - NFL season boundaries (September - February)
    - Week type classification (preseason/regular/playoffs)
    - Holiday and scheduling context
    
    UPDATED: Supports bucket-first architecture via DataFrameEngine
    
    Args:
        engine: SQLAlchemy database engine OR DataFrameEngine (bucket data) - used to determine date range
        logger: Optional logger override
        
    Returns:
        pd.DataFrame: Complete date dimension
    """
    logger = logger or get_logger('nflfastRv3.transformations.calendar')
    
    # Determine date range from engine data
    if isinstance(engine, DataFrameEngine):
        # Bucket mode: Get min/max seasons from play_by_play data
        df_pbp = engine.df
        if 'season' in df_pbp.columns:
            start_year = int(df_pbp['season'].min())
            end_year = int(df_pbp['season'].max())
        else:
            # Fallback to default range
            start_year = 1999
            end_year = datetime.now().year + 1
    else:
        # Database mode: Query for min/max seasons
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT MIN(season) as min_season, MAX(season) as max_season
                    FROM raw_nflfastr.play_by_play
                    WHERE season IS NOT NULL
                """))
                row = result.fetchone()
                if row and row[0] and row[1]:
                    start_year = int(row[0])
                    end_year = int(row[1])
                else:
                    # Fallback to default range
                    start_year = 1999
                    end_year = datetime.now().year + 1
        except Exception as e:
            logger.warning(f"Failed to query season range: {e}, using defaults")
            start_year = 1999
            end_year = datetime.now().year + 1
    
    # Add buffer for future scheduling
    end_year = end_year + 1
    
    logger.info(f"Building dim_date for NFL seasons {start_year}-{end_year}...")
    
    # Generate date range covering all NFL seasons
    start_date = datetime(start_year - 1, 3, 1)  # Start before season for offseason
    end_date = datetime(end_year + 1, 2, 28)     # End after season for playoffs
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    df = pd.DataFrame({'date': date_range})
    
    # Basic date components
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['day_of_week'] = df['date'].dt.day_name()
    df['day_of_year'] = df['date'].dt.dayofyear
    df['week_of_year'] = df['date'].dt.isocalendar().week
    df['quarter'] = df['date'].dt.quarter
    
    # NFL season logic (key V2 feature)
    df['nfl_season'] = df.apply(_calculate_nfl_season, axis=1)
    df['season_type'] = df.apply(_classify_season_type, axis=1)
    
    # Game scheduling context
    df['is_weekend'] = df['date'].dt.dayofweek.isin([5, 6])  # Saturday, Sunday
    df['is_weekday'] = ~df['is_weekend']
    df['is_thursday'] = df['date'].dt.dayofweek == 3
    df['is_monday'] = df['date'].dt.dayofweek == 0
    
    # Holiday detection (affects scheduling)
    df['is_holiday'] = df['date'].apply(_is_nfl_relevant_holiday)
    
    # Validation
    validation_result = validate_table_data(
        df, 
        'dim_date',
        required_columns=['date', 'nfl_season', 'season_type'],
        logger=logger
    )
    
    logger.info(f"✓ Built dim_date: {len(df):,} dates for {end_year - start_year + 1} NFL seasons")
    return df


def build_dim_drive(engine, logger=None) -> pd.DataFrame:
    """
    Build drive dimension with situational context.
    
    Preserves V2 features:
    - Drive outcome classification
    - Field position analysis
    - Scoring context
    
    UPDATED: Supports bucket-first architecture via DataFrameEngine
    
    Args:
        engine: SQLAlchemy database engine OR DataFrameEngine (bucket data)
        logger: Optional logger override
        
    Returns:
        pd.DataFrame: Complete drive dimension
    """
    logger = logger or get_logger('nflfastRv3.transformations.calendar')
    logger.info("Building dim_drive with situational analysis...")
    
    try:
        logger.info("dim_drive: Extracting drive data")
        
        # NEW: Support DataFrameEngine (bucket data)
        if isinstance(engine, DataFrameEngine):
            # Bucket mode: Aggregate from play_by_play DataFrame
            df_pbp = engine.df
            
            # Filter valid drives
            df_pbp = df_pbp[
                (df_pbp['game_id'].notna()) &
                (df_pbp['drive'].notna()) &
                (df_pbp['posteam'].notna())
            ].copy()
            
            # Group by drive
            df = df_pbp.groupby(['game_id', 'drive', 'posteam', 'defteam']).agg({
                'play_id': ['min', 'max', 'count'],
                'yardline_100': ['max', 'min'],
                'touchdown': lambda x: (x == True).any() if 'touchdown' in df_pbp.columns else False,
                'field_goal_attempt': lambda x: ((x == True) & (df_pbp.loc[x.index, 'field_goal_result'] == 'made')).any() if 'field_goal_attempt' in df_pbp.columns else False,
                'punt_attempt': lambda x: (x == True).any() if 'punt_attempt' in df_pbp.columns else False,
                'epa': lambda x: x.fillna(0).sum() if 'epa' in df_pbp.columns else 0,
                'yards_gained': 'sum'
            }).reset_index()
            
            # Flatten column names
            df.columns = [
                'game_id', 'drive', 'drive_team', 'defense_team',
                'first_play_id', 'last_play_id', 'drive_plays',
                'drive_start_yardline', 'drive_end_yardline',
                'drive_touchdown', 'drive_field_goal', 'drive_punt',
                'drive_total_epa', 'drive_total_yards'
            ]
            
            # Create drive key
            df['drive_key'] = df['game_id'] + '-' + df['drive'].astype(str)
            
            logger.info(f"Aggregated drive data from bucket: {len(df):,} drives")
            
        else:
            # FALLBACK: Database mode (local dev only)
            drive_sql = """
            SELECT DISTINCT
                CONCAT(game_id, '-', COALESCE(drive, 0)) as drive_key,
                game_id,
                drive,
                posteam as drive_team,
                defteam as defense_team,
                
                -- Drive boundaries
                MIN(play_id) as first_play_id,
                MAX(play_id) as last_play_id,
                COUNT(*) as drive_plays,
                
                -- Field position
                MAX(yardline_100) as drive_start_yardline,
                MIN(yardline_100) as drive_end_yardline,
                
                -- Drive outcome
                MAX(CASE WHEN touchdown = true THEN 1 ELSE 0 END) as drive_touchdown,
                MAX(CASE WHEN field_goal_attempt = true AND field_goal_result = 'made' THEN 1 ELSE 0 END) as drive_field_goal,
                MAX(CASE WHEN punt_attempt = true THEN 1 ELSE 0 END) as drive_punt,
                
                -- Drive efficiency
                SUM(COALESCE(epa, 0)) as drive_total_epa,
                SUM(yards_gained) as drive_total_yards
                
            FROM raw_nflfastr.play_by_play
            WHERE game_id IS NOT NULL
                AND drive IS NOT NULL
                AND posteam IS NOT NULL
            GROUP BY game_id, drive, posteam, defteam
            """
            
            df = pd.read_sql(drive_sql, engine)
            logger.info(f"Extracted drive data from database: {len(df):,} drives")
        
        logger.info(f"dim_drive: Extracted drive data ({len(df):,} rows)")
        
        if df.empty:
            logger.warning("No drive data found")
            return pd.DataFrame()
        
        # Calculate derived drive metrics
        logger.info("dim_drive: Calculating derived drive metrics")
        df['drive_net_yards'] = df['drive_start_yardline'] - df['drive_end_yardline']
        df['drive_avg_epa'] = df['drive_total_epa'] / df['drive_plays']
        
        # Classify drive outcomes
        df['drive_outcome'] = df.apply(_classify_drive_outcome, axis=1)
        df['drive_success'] = df['drive_outcome'].isin(['Touchdown', 'Field Goal'])
        
        # Field position categories
        df['drive_start_field_position'] = pd.cut(
            df['drive_start_yardline'], 
            bins=[0, 20, 50, 80, 100], 
            labels=['Red Zone', 'Short Field', 'Mid Field', 'Long Field']
        )
        
        # Validation
        validation_result = validate_table_data(
            df, 
            'dim_drive',
            required_columns=['drive_key', 'game_id', 'drive_team'],
            logger=logger
        )
        
        logger.info(f"✓ Built dim_drive: {len(df):,} drives with outcome analysis")
        return df
        
    except Exception as e:
        logger.error(f"Failed to build dim_drive: {e}", exc_info=True)
        return pd.DataFrame()


# Helper functions (simple, 1 complexity point each)
def _calculate_nfl_season(row):
    """Calculate NFL season from date (V2 logic)."""
    date = row['date']
    if date.month >= 3:  # March onwards = same year season
        return date.year
    else:  # Jan-Feb = previous year season  
        return date.year - 1


def _classify_season_type(row):
    """Classify date into season type (V2 logic)."""
    month = row['date'].month
    if month in [8]:  # August
        return 'PRE'
    elif month in [9, 10, 11, 12]:  # Sep-Dec
        return 'REG'  
    elif month in [1, 2]:  # Jan-Feb
        return 'POST'
    else:
        return 'OFF'  # Offseason


def _is_nfl_relevant_holiday(date):
    """Check if date is a relevant holiday for NFL scheduling."""
    # Thanksgiving (affects Thursday games)
    thanksgiving = datetime(date.year, 11, 1)
    while thanksgiving.weekday() != 3:  # Find 4th Thursday
        thanksgiving += timedelta(days=1)
    if thanksgiving.day > 21:
        thanksgiving += timedelta(days=7)
    
    if date.date() == thanksgiving.date():
        return True
    
    # Christmas, New Year's (affect scheduling)
    holidays = [
        datetime(date.year, 12, 25).date(),  # Christmas
        datetime(date.year, 1, 1).date(),    # New Year's
    ]
    
    return date.date() in holidays


def _classify_drive_outcome(row):
    """Classify drive outcome based on result flags."""
    if row['drive_touchdown']:
        return 'Touchdown'
    elif row['drive_field_goal']:
        return 'Field Goal'
    elif row['drive_punt']:
        return 'Punt'
    else:
        return 'Other'
