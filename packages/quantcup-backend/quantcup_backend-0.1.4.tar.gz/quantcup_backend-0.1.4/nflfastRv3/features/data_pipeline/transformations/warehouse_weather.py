"""
Weather data enrichment for warehouse dimension table.

Creates dim_game_weather with:
- Raw weather fields (temp, wind, weather, roof)
- Enriched fields (parsed from weather strings)
- Model-ready fields (excludes indoor games)
- Data quality tracking
- Provenance metadata
- Audit columns (stadium metadata)

Pattern: Weather enrichment transformation (2 complexity points)
- Model filtering: 1 point
- Audit column tracking: 1 point
(String parsing moved to shared weather.transforms.weather_enrichment module)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from commonv2 import get_logger

# Import shared weather enrichment functions
from weather.transforms.weather_enrichment import enrich_weather, add_qa_columns

logger = get_logger('nflfastRv3.transformations.warehouse_weather')


def build_dim_game_weather(engine, logger_override=None) -> pd.DataFrame:
    """
    Build dim_game_weather table with weather enrichment and model filtering.
    
    ⚠️ MULTI-SOURCE DIMENSION - Does NOT use play_by_play DataFrameEngine
    -------------------------------------------------------------------
    This function reads dim_game directly from the warehouse bucket and enriches it.
    The 'engine' parameter is IGNORED and should be None (if configured correctly).
    
    Configuration Requirement:
    - data_sources.py must have: 'source_table': ['dim_game']  (list, not string!)
    - If misconfigured as string, warehouse will waste 2+ minutes loading play_by_play
    - See data_sources.py WAREHOUSE_COLUMN_REQUIREMENTS for detailed config rules
    
    Workflow:
    1. Load dim_game from warehouse bucket (NOT from engine)
    2. Parse weather strings to backfill missing temp/wind (via shared module)
    3. Detect malformed weather strings (via shared module)
    4. Filter weather for model eligibility (exclude indoor games)
    5. Add audit columns (stadium metadata, QA flags)
    6. Add provenance and lineage metadata
    
    Args:
        engine: DataFrameEngine - IGNORED (should be None for multi-source dimensions)
        logger_override: Optional logger to use instead of module logger
    
    Returns:
        pd.DataFrame with enriched weather columns:
        - Raw: temp_raw, wind_raw, weather_raw, roof_raw
        - Enriched: temp_filled, wind_filled, temp_source, wind_source
        - Quality: parsing_attempted, parsing_used, is_malformed_weather_string
        - Model: temp_model, wind_model, is_weather_model_eligible, model_weather_exclusion_reason
        - Audit: stadium_roof_type, stadium_name, is_outdoor_dim_game, is_missing_weather_after_parse
        - Lineage: source_table, enrichment_version, loaded_at
    
    Performance:
        - Typical runtime: ~2-3 seconds
        - Memory usage: <50MB (only loads dim_game, ~10K rows)
        - If slowdown observed, check if engine is being created unnecessarily
    """
    from weather.utils.stadium_registry import NFL_STADIUMS
    from commonv2.persistence.bucket_adapter import get_bucket_adapter
    
    log = logger_override or logger
    
    # ============================================================
    # MULTI-SOURCE PATTERN: Load data directly from bucket
    # ============================================================
    # This function does NOT use the 'engine' parameter (should be None).
    # Instead, it loads dim_game directly from warehouse bucket.
    # This avoids the performance penalty of loading play_by_play.
    bucket_adapter = get_bucket_adapter(logger=log)
    
    # Load dim_game from warehouse bucket (NOT from engine parameter!)
    log.info("Loading dim_game from warehouse bucket...")
    dim_game = bucket_adapter.read_data('dim_game', 'warehouse')
    log.info(f"Loaded {len(dim_game):,} games from dim_game")
    
    df = dim_game.copy()
    
    # =====================================================================
    # Step 1: Store raw columns
    # =====================================================================
    df['temp_raw'] = df['temp']
    df['wind_raw'] = df['wind']
    df['weather_raw'] = df['weather']
    df['roof_raw'] = df['roof']
    
    # =====================================================================
    # Step 2: Backfill temp/wind from weather strings (using shared module)
    # =====================================================================
    log.info("Parsing weather strings to backfill missing values...")
    df = enrich_weather(df)
    
    # Log enrichment results
    parsed_used_count = int(df['parsing_used'].sum())
    malformed_count = int(df['is_malformed_weather_string'].sum())
    if malformed_count > 0:
        log.warning(f"Detected {malformed_count} malformed weather strings")
    if parsed_used_count > 0:
        log.info(f"Applied parsed weather values to {parsed_used_count} games")
    
    # =====================================================================
    # Step 3: Add stadium audit columns (persist for transparency)
    # =====================================================================
    log.info("Adding stadium audit columns...")
    stadium_roof_map = {team: info.get('roof_type', 'unknown')
                        for team, info in NFL_STADIUMS.items()}
    df['stadium_roof_type'] = df['home_team'].map(stadium_roof_map)
    df['stadium_name'] = df['home_team'].map({
        team: info['name'] for team, info in NFL_STADIUMS.items()
    })
    
    # =====================================================================
    # Step 4: Filter for modeling (exclude indoor/closed roof games)
    # =====================================================================
    log.info("Filtering weather for model eligibility...")
    df['temp_model'] = df['temp_filled']
    df['wind_model'] = df['wind_filled']
    df['is_weather_model_eligible'] = True
    df['model_weather_exclusion_reason'] = None
    
    # Fixed domes: always exclude (outside weather != gameplay conditions)
    fixed_dome_mask = df['stadium_roof_type'] == 'fixed_dome'
    df.loc[fixed_dome_mask, 'temp_model'] = np.nan
    df.loc[fixed_dome_mask, 'wind_model'] = np.nan
    df.loc[fixed_dome_mask, 'is_weather_model_eligible'] = False
    df.loc[fixed_dome_mask, 'model_weather_exclusion_reason'] = 'fixed_dome'
    
    # Retractables closed: exclude (only include when explicitly open)
    retractable_closed_mask = (df['stadium_roof_type'] == 'retractable') & (df['roof'] != 'open')
    df.loc[retractable_closed_mask, 'temp_model'] = np.nan
    df.loc[retractable_closed_mask, 'wind_model'] = np.nan
    df.loc[retractable_closed_mask, 'is_weather_model_eligible'] = False
    df.loc[retractable_closed_mask, 'model_weather_exclusion_reason'] = 'retractable_closed'
    
    model_eligible_count = int(df['is_weather_model_eligible'].sum())
    log.info(f"Model-eligible weather: {model_eligible_count} games (excludes fixed domes and closed retractables)")
    
    # =====================================================================
    # Step 5: Add QA convenience columns (using shared module)
    # =====================================================================
    log.info("Adding QA convenience columns...")
    df = add_qa_columns(df)
    
    # Log data quality metrics
    outdoor_missing = int(df['is_missing_weather_after_parse'].sum())
    if outdoor_missing > 0:
        outdoor_total = int(df['is_outdoor_dim_game'].sum())
        missing_pct = (outdoor_missing / outdoor_total) * 100 if outdoor_total > 0 else 0
        log.warning(f"⚠️ Quality Alert: {outdoor_missing} outdoor games missing weather ({missing_pct:.1f}%)")
    
    # =====================================================================
    # Step 6: Add lineage metadata
    # =====================================================================
    df['source_table'] = 'dim_game'
    df['enrichment_version'] = 'v1_parse_based_2026-01-27'
    df['loaded_at'] = datetime.now()
    
    log.info(f"✓ Built dim_game_weather: {len(df):,} games with enriched weather data")
    
    return df
