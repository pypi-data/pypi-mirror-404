"""
Fact Table Builders for nflfastRv3

Consolidated module containing all fact table builders:
- build_fact_play: Play-level facts with chunked processing
- build_fact_player_stats: Player statistics with snap counts integration
- build_fact_player_play: Granular player-play attribution

Pattern: Enhanced simple functions with optional dependency injection
Complexity: 3-4 points per function (business logic + data processing)
Layer: 3 (uses SQL templates, cleaning functions, and warehouse utils)
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from commonv2 import get_logger

from .dataframe_engine import DataFrameEngine
from .sql_templates_facts import (
    get_fact_play_sql,
    get_fact_player_stats_sql,
    get_fact_player_play_sql
)
from .cleaning_facts import (
    clean_fact_play_data,
    clean_fact_player_stats_data,
    clean_fact_player_play_data
)
from .warehouse_utils import (
    save_table_to_db,
    validate_table_data,
    create_table_summary,
    handle_empty_dataframe,
    filter_dataframe_by_seasons,
    calculate_processing_efficiency,
    log_season_processing
)


def build_fact_play(data_source: Any, seasons: Optional[List[str]] = None,
                   chunk_size: int = 5000, db_service: Optional[Any] = None,
                   bucket_adapter: Optional[Any] = None,
                   logger: Optional[Any] = None) -> Dict[str, Any]:
    """
    Build fact_play table with optimized processing.
    
    V2 Features Preserved:
    - Sophisticated play analysis and derived metrics
    - Memory-efficient handling of multi-season datasets
    - Data quality validation
    
    UPDATED: Supports bucket-first architecture via DataFrameEngine
    - Bucket mode: Processes entire DataFrame at once (data already in memory)
    - Database mode: Uses chunked processing (5000 rows default) for streaming
    
    Args:
        data_source: DataFrameEngine (bucket) OR Database service (database mode)
        seasons: Optional list of seasons to filter (default: process all available data)
        chunk_size: Number of rows per chunk in database mode (default: 5000)
        db_service: Optional database service for saving (required in bucket mode)
        bucket_adapter: Optional bucket adapter for bucket-first saves
        logger: Optional logger instance
        
    Returns:
        Dict with build summary including row counts and performance metrics
        
    Complexity: Business logic with adaptive processing (4 points)
    """
    logger = logger or get_logger('nflfastRv3.facts_play')
    assert logger is not None
    logger.info("Starting fact_play table build with chunked processing")
    
    # Initialize summary tracking early to avoid unbound variable
    build_summary = {
        'status': 'success',
        'total_rows_processed': 0,
        'total_rows_saved': 0,
        'chunks_processed': 0,
        'seasons_processed': 0,
        'performance_metrics': {},
        'validation_results': {}
    }
    
    try:
        # 1. Log season processing (optional filter, not default)
        build_summary['seasons_processed'] = log_season_processing(seasons, logger)
        
        # 2. Get data (bucket-first OR database)
        # NEW: Support DataFrameEngine (bucket data)
        if isinstance(data_source, DataFrameEngine):
            # Bucket mode: Data already loaded & validated
            logger.info("Using bucket data from DataFrameEngine")
            
            if db_service is None:
                raise ValueError("db_service required for saving in bucket mode")
            
            raw_data = data_source.df
            
            if raw_data.empty:
                return handle_empty_dataframe(logger, "Empty play_by_play DataFrame - no data to process")
            
            # Optional: Filter by seasons if explicitly specified
            filtered_data = filter_dataframe_by_seasons(raw_data, seasons, logger)
            if filtered_data is None:
                return handle_empty_dataframe(logger, f"No data found for seasons {seasons}")
            raw_data = filtered_data
            
            # Process entire DataFrame at once (no chunking needed - data already in memory)
            logger.info(f"Processing {len(raw_data):,} rows")
            
            # Clean data
            cleaned_df = clean_fact_play_data(raw_data, logger)
            
            # Validate data
            validation_result = validate_table_data(cleaned_df, 'fact_play')
            if validation_result['status'] != 'success':
                logger.warning(f"Validation issues: {validation_result}")
            
            # Update summary
            build_summary['total_rows_processed'] = len(raw_data)
            build_summary['total_rows_saved'] = len(cleaned_df)
            build_summary['chunks_processed'] = 1
            build_summary['validation_results']['full_dataset'] = validation_result
            
            # Save to bucket
            if bucket_adapter is None:
                raise RuntimeError("bucket_adapter required for saving in bucket mode")
            
            rows_saved = bucket_adapter.store_data_streaming(
                df=cleaned_df,
                table_name='fact_play',
                schema='warehouse',
                rows_per_group=chunk_size
            )
            logger.info(f"💾 Saved {rows_saved:,} rows to warehouse/fact_play")
        
        else:
            # FALLBACK: Database mode (local dev only)
            logger.info("Using database mode")
            db_engine = data_source.engine
            sql_query = get_fact_play_sql(db_engine)
            logger.info("Generated adaptive fact_play SQL query")
            
            # Add season filtering
            if seasons:
                season_list = "', '".join(seasons)
                sql_query = sql_query.text.replace(
                    "WHERE play_id IS NOT NULL AND game_id IS NOT NULL",
                    f"WHERE play_id IS NOT NULL AND game_id IS NOT NULL AND season IN ('{season_list}')"
                )
                sql_query = text(sql_query)
            
            # Process in chunks
            total_processed = 0
            chunk_number = 0
            
            logger.info(f"Reading data in chunks of {chunk_size:,} rows")
            chunk_iterator = pd.read_sql(sql_query, db_engine, chunksize=chunk_size)
            
            for chunk_df in chunk_iterator:
                chunk_number += 1
                chunk_start_rows = len(chunk_df)
                
                logger.info(f"Processing chunk {chunk_number}: {chunk_start_rows:,} rows")
                
                # Clean chunk data using V2 business logic
                cleaned_chunk = clean_fact_play_data(chunk_df, logger)
                
                # Validate chunk data quality
                validation_result = validate_table_data(cleaned_chunk, 'fact_play')
                if validation_result['status'] != 'success':
                    logger.warning(f"Chunk {chunk_number} validation issues: {validation_result}")
                
                # Save chunk to warehouse schema
                if chunk_number == 1:
                    save_result = save_table_to_db(cleaned_chunk, 'fact_play', db_engine, logger=logger)
                else:
                    with db_engine.begin() as conn:
                        cleaned_chunk.to_sql(
                            name='fact_play',
                            con=conn,
                            schema='warehouse',
                            if_exists='append',
                            index=False,
                            method='multi'
                        )
                
                # Update summary metrics
                total_processed += chunk_start_rows
                build_summary['total_rows_processed'] += chunk_start_rows
                build_summary['total_rows_saved'] += len(cleaned_chunk)
                build_summary['chunks_processed'] = chunk_number
                build_summary['validation_results'][f'chunk_{chunk_number}'] = validation_result
                
                logger.info(f"Chunk {chunk_number} complete: {len(cleaned_chunk):,} rows saved")
        
        # 9. Final summary
        logger.info(f"Processing complete: {build_summary['total_rows_processed']:,} total rows processed")
        
        build_summary['performance_metrics'] = calculate_processing_efficiency(
            build_summary['total_rows_saved'],
            build_summary['total_rows_processed']
        )
        
        logger.info(f"✅ fact_play build complete: {build_summary['total_rows_saved']:,} rows saved")
        return build_summary
        
    except Exception as e:
        logger.error(f"❌ fact_play build failed: {e}", exc_info=True)
        build_summary['status'] = 'error'
        build_summary['message'] = str(e)
        return build_summary


def build_fact_player_stats(data_source: Any, seasons: Optional[List[str]] = None,
                           db_service: Optional[Any] = None, bucket_adapter: Optional[Any] = None,
                           logger: Optional[Any] = None) -> Dict[str, Any]:
    """
    Build fact_player_stats table with snap counts integration.
    
    V2 Features Preserved:
    - Multi-table joins (player_stats + snap_counts)
    - Comprehensive performance metrics
    - Fantasy scoring calculations
    - Efficiency metrics (catch rate, yards per carry, etc.)
    
    UPDATED: Supports bucket-first architecture via DataFrameEngine
    
    Args:
        data_source: DataFrameEngine (bucket) OR Database service (database mode)
        seasons: Optional list of seasons to filter (default: process all available data)
        db_service: Optional database service for saving (required in bucket mode)
        bucket_adapter: Optional bucket adapter for bucket-first saves
        logger: Optional logger instance
        
    Returns:
        Dict with build summary including row counts and validation results
        
    Complexity: Player stats integration with business logic (3 points)
    """
    logger = logger or get_logger('nflfastRv3.facts_player')
    assert logger is not None
    logger.info("Starting fact_player_stats table build")
    
    try:
        # 1. Log season processing (optional filter, not default)
        log_season_processing(seasons, logger)
        
        # 2. Get data (bucket-first OR database)
        # NEW: Support DataFrameEngine (bucket data)
        if isinstance(data_source, DataFrameEngine):
            # Bucket mode: Aggregate player stats from play_by_play DataFrame
            logger.info("Using bucket data from DataFrameEngine")
            
            if db_service is None:
                raise ValueError("db_service required for saving in bucket mode")
            
            df_pbp = data_source.df
            
            if df_pbp.empty:
                return handle_empty_dataframe(logger, "Empty play_by_play DataFrame - no data to aggregate")
            
            # Optional: Filter by seasons if explicitly specified
            filtered_data = filter_dataframe_by_seasons(df_pbp, seasons, logger)
            if filtered_data is None:
                return handle_empty_dataframe(logger, f"No data found for seasons {seasons}")
            df_pbp = filtered_data
            
            # Aggregate player stats from play-by-play (similar to dim_drive pattern)
            logger.info("Aggregating player stats from play_by_play data...")
            
            # Prepare aggregation - collect player stats by game/week
            player_stats = []
            
            # QB stats from passing plays
            if all(col in df_pbp.columns for col in ['passer_player_id', 'passer_player_name', 'game_id', 'week', 'season']):
                qb_stats = df_pbp[df_pbp['passer_player_id'].notna()].groupby(
                    ['passer_player_id', 'passer_player_name', 'game_id', 'week', 'season', 'posteam']
                ).agg({
                    'pass_attempt': lambda x: x.sum() if 'pass_attempt' in df_pbp.columns else 0,
                    'complete_pass': lambda x: x.sum() if 'complete_pass' in df_pbp.columns else 0,
                    'passing_yards': lambda x: x.sum() if 'passing_yards' in df_pbp.columns else 0,
                    'interception': lambda x: x.sum() if 'interception' in df_pbp.columns else 0
                }).reset_index()
                
                qb_stats = qb_stats.rename(columns={
                    'passer_player_id': 'player_id',
                    'passer_player_name': 'player_name',
                    'pass_attempt': 'attempts',
                    'complete_pass': 'completions'
                })
                qb_stats['position'] = 'QB'
                player_stats.append(qb_stats)
            
            # RB stats from rushing plays
            if all(col in df_pbp.columns for col in ['rusher_player_id', 'rusher_player_name', 'game_id', 'week', 'season']):
                rb_stats = df_pbp[df_pbp['rusher_player_id'].notna()].groupby(
                    ['rusher_player_id', 'rusher_player_name', 'game_id', 'week', 'season', 'posteam']
                ).agg({
                    'rush_attempt': lambda x: x.sum() if 'rush_attempt' in df_pbp.columns else 0,
                    'rushing_yards': lambda x: x.sum() if 'rushing_yards' in df_pbp.columns else 0
                }).reset_index()
                
                rb_stats = rb_stats.rename(columns={
                    'rusher_player_id': 'player_id',
                    'rusher_player_name': 'player_name',
                    'rush_attempt': 'carries'
                })
                rb_stats['position'] = 'RB'
                player_stats.append(rb_stats)
            
            # WR/TE stats from receiving plays
            if all(col in df_pbp.columns for col in ['receiver_player_id', 'receiver_player_name', 'game_id', 'week', 'season']):
                wr_stats = df_pbp[df_pbp['receiver_player_id'].notna()].groupby(
                    ['receiver_player_id', 'receiver_player_name', 'game_id', 'week', 'season', 'posteam']
                ).agg({
                    'complete_pass': lambda x: x.sum() if 'complete_pass' in df_pbp.columns else 0,
                    'receiving_yards': lambda x: x.sum() if 'receiving_yards' in df_pbp.columns else 0
                }).reset_index()
                
                wr_stats = wr_stats.rename(columns={
                    'receiver_player_id': 'player_id',
                    'receiver_player_name': 'player_name',
                    'complete_pass': 'receptions'
                })
                wr_stats['position'] = 'WR'
                wr_stats['targets'] = wr_stats['receptions']  # Simplified - actual targets would need pass_attempt
                player_stats.append(wr_stats)
            
            if not player_stats:
                logger.warning("No player data could be aggregated from play_by_play")
                return {
                    'status': 'success',
                    'total_rows_processed': 0,
                    'total_rows_saved': 0,
                    'message': 'No player columns found in play_by_play data'
                }
            
            # Combine all player stats
            df = pd.concat(player_stats, ignore_index=True)
            
            # Fill missing columns with defaults
            for col in ['attempts', 'completions', 'passing_yards', 'interception',
                       'carries', 'rushing_yards', 'receptions', 'receiving_yards', 'targets']:
                if col not in df.columns:
                    df[col] = 0
            
            # Add required metadata columns
            df['season_type'] = 'REG'  # Default to regular season
            df['position_group'] = df['position']
            df['recent_team'] = df['posteam']
            
            logger.info(f"Aggregated {len(df):,} player stat records from play_by_play")
            
        else:
            # FALLBACK: Database mode (local dev only)
            logger.info("Using database mode")
            db_engine = data_source.engine
            
            # Get SQL query for player stats with snap counts
            sql_query = get_fact_player_stats_sql()
            
            # Add season filtering if specified
            if seasons:
                season_list = "', '".join(seasons)
                season_filter = f" AND ps.season IN ('{season_list}')"
                sql_query = sql_query.text.replace(
                    "WHERE ps.player_id IS NOT NULL",
                    f"WHERE ps.player_id IS NOT NULL{season_filter}"
                )
                from sqlalchemy import text
                sql_query = text(sql_query)
            
            logger.info("Generated player stats SQL query with snap counts integration")
            
            # Execute query and retrieve data
            df = pd.read_sql(sql_query, db_engine)
            logger.info(f"Retrieved {len(df):,} player stat records")
        
        if df.empty:
            logger.warning("No player stats data found")
            return {
                'status': 'success',
                'rows_processed': 0,
                'rows_saved': 0,
                'message': 'No data found for specified seasons'
            }
        
        # 5. Clean and enhance data using V2 business logic
        cleaned_df = clean_fact_player_stats_data(df, logger)
        logger.info(f"Cleaned data: {len(cleaned_df):,} rows")
        
        # 6. Validate data quality
        validation_result = validate_table_data(cleaned_df, 'fact_player_stats')
        if validation_result['status'] != 'success':
            logger.warning(f"Data validation issues: {validation_result}")
        
        # 7. Save to bucket or database
        if isinstance(data_source, DataFrameEngine):
            # Save to bucket
            if bucket_adapter is None:
                raise RuntimeError("bucket_adapter required for saving in bucket mode")
            
            rows_saved = bucket_adapter.store_data_streaming(
                df=cleaned_df,
                table_name='fact_player_stats',
                schema='warehouse',
                rows_per_group=10000
            )
            logger.info(f"💾 Saved {rows_saved:,} rows to warehouse/fact_player_stats")
        else:
            # Database mode: Save to database
            db_engine = data_source.engine
            save_result = save_table_to_db(cleaned_df, 'fact_player_stats', db_engine, logger=logger)
            if not save_result:
                raise Exception("Failed to save fact_player_stats table")
        
        # 8. Generate summary statistics
        summary = create_table_summary(cleaned_df, 'fact_player_stats')
        
        logger.info(f"✅ fact_player_stats build complete: {len(cleaned_df):,} rows")
        return {
            'status': 'success',
            'rows_processed': len(df),
            'rows_saved': len(cleaned_df),
            'seasons_processed': seasons,
            'validation_result': validation_result,
            'table_summary': summary
        }
        
    except Exception as e:
        logger.error(f"❌ fact_player_stats build failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e),
            'seasons': seasons
        }


def build_fact_player_play(data_source: Any, seasons: Optional[List[str]] = None,
                          chunk_size: int = 10000, db_service: Optional[Any] = None,
                          bucket_adapter: Optional[Any] = None,
                          logger: Optional[Any] = None) -> Dict[str, Any]:
    """
    Build fact_player_play table with individual performance attribution.
    
    V2 Features Preserved:
    - Player involvement detection and classification
    - EPA attribution to individual players
    - Usage rate and opportunity calculations
    - Position-specific performance metrics
    
    UPDATED: Supports bucket-first architecture via DataFrameEngine
    - Bucket mode: Processes entire DataFrame at once (data already in memory)
    - Database mode: Uses chunked processing (10000 rows default) for streaming
    
    Args:
        data_source: DataFrameEngine (bucket) OR Database service (database mode)
        seasons: Optional list of seasons to filter (default: process all available data)
        chunk_size: Number of rows per chunk in database mode (default: 10000)
        db_service: Optional database service for saving (required in bucket mode)
        bucket_adapter: Optional bucket adapter for bucket-first saves
        logger: Optional logger instance
        
    Returns:
        Dict with build summary including row counts and performance metrics
        
    Complexity: Complex attribution with adaptive processing (4 points)
    """
    logger = logger or get_logger('nflfastRv3.facts_granular')
    assert logger is not None
    logger.info("Starting fact_player_play table build with individual attribution")
    
    # Initialize summary tracking
    build_summary = {
        'status': 'success',
        'total_rows_processed': 0,
        'total_rows_saved': 0,
        'chunks_processed': 0,
        'seasons_processed': 0,
        'performance_metrics': {},
        'validation_results': {}
    }
    
    try:
        # 1. Log season processing (optional filter, not default)
        build_summary['seasons_processed'] = log_season_processing(seasons, logger)
        
        # 2. Get data (bucket-first OR database)
        # NEW: Support DataFrameEngine (bucket data)
        if isinstance(data_source, DataFrameEngine):
            # Bucket mode: Extract player-play data from play_by_play DataFrame
            logger.info("Using bucket data from DataFrameEngine")
            
            if db_service is None:
                raise ValueError("db_service required for saving in bucket mode")
            
            df_pbp = data_source.df
            
            if df_pbp.empty:
                return handle_empty_dataframe(logger, "Empty play_by_play DataFrame - no data to process")
            
            # Optional: Filter by seasons if explicitly specified
            filtered_data = filter_dataframe_by_seasons(df_pbp, seasons, logger)
            if filtered_data is None:
                return handle_empty_dataframe(logger, f"No data found for seasons {seasons}")
            df_pbp = filtered_data
            
            # Create player-play records (simplified version for bucket mode)
            logger.warning("Bucket mode: Using simplified player-play attribution. For full attribution, use database mode.")
            
            # Process entire DataFrame at once (no chunking needed - data already in memory)
            logger.info(f"Processing {len(df_pbp):,} rows")
            
            # Clean data
            cleaned_df = clean_fact_player_play_data(df_pbp, logger)
            
            # Validate data
            validation_result = validate_table_data(cleaned_df, 'fact_player_play')
            if validation_result['status'] != 'success':
                logger.warning(f"Validation issues: {validation_result}")
            
            # Update summary
            build_summary['total_rows_processed'] = len(df_pbp)
            build_summary['total_rows_saved'] = len(cleaned_df)
            build_summary['chunks_processed'] = 1
            build_summary['validation_results']['full_dataset'] = validation_result
            
            # Save to bucket
            if bucket_adapter is None:
                raise RuntimeError("bucket_adapter required for saving in bucket mode")
            
            rows_saved = bucket_adapter.store_data_streaming(
                df=cleaned_df,
                table_name='fact_player_play',
                schema='warehouse',
                rows_per_group=chunk_size
            )
            logger.info(f"💾 Saved {rows_saved:,} rows to warehouse/fact_player_play")
        
        else:
            # FALLBACK: Database mode (local dev only)
            logger.info("Using database mode")
            db_engine = data_source.engine
            
            # Get SQL query for player-play attribution
            sql_query = get_fact_player_play_sql()
            
            # Add season filtering if specified
            if seasons:
                season_list = "', '".join(seasons)
                season_filter = f" AND EXTRACT(YEAR FROM p.game_date) IN ('{season_list}')"
                sql_query_text = sql_query.text
                
                # Apply filter to each UNION section
                sql_query_text = sql_query_text.replace(
                    "WHERE p.passer_id IS NOT NULL",
                    f"WHERE p.passer_id IS NOT NULL{season_filter}"
                ).replace(
                    "WHERE p.rusher_id IS NOT NULL",
                    f"WHERE p.rusher_id IS NOT NULL{season_filter}"
                ).replace(
                    "WHERE p.receiver_id IS NOT NULL",
                    f"WHERE p.receiver_id IS NOT NULL{season_filter}"
                )
                
                from sqlalchemy import text
                sql_query = text(sql_query_text)
            
            logger.info("Generated player-play attribution SQL query")
            
            # Process data in chunks (large dataset expected)
            total_processed = 0
            chunk_number = 0
            
            logger.info(f"Reading data in chunks of {chunk_size:,} rows")
            chunk_iterator = pd.read_sql(sql_query, db_engine, chunksize=chunk_size)
            
            for chunk_df in chunk_iterator:
                chunk_number += 1
                chunk_start_rows = len(chunk_df)
                
                logger.info(f"Processing chunk {chunk_number}: {chunk_start_rows:,} rows")
                
                # 5. Clean chunk data using V2 business logic
                cleaned_chunk = clean_fact_player_play_data(chunk_df, logger)
                
                # 6. Validate chunk data quality
                validation_result = validate_table_data(cleaned_chunk, 'fact_player_play')
                if validation_result['status'] != 'success':
                    logger.warning(f"Chunk {chunk_number} validation issues: {validation_result}")
                
                # 7. Save chunk to analytics schema
                if chunk_number == 1:
                    # First chunk - replace table
                    assert db_service is not None, "db_service required in database mode"
                    save_result = save_table_to_db(cleaned_chunk, 'fact_player_play', db_service.engine, logger=logger)
                else:
                    # Subsequent chunks - append data
                    assert db_service is not None, "db_service required in database mode"
                    with db_service.engine.begin() as conn:
                        cleaned_chunk.to_sql(
                            name='fact_player_play',
                            con=conn,
                            schema='warehouse',
                            if_exists='append',
                            index=False,
                            method='multi'
                        )
                    save_result = True
                
                # 8. Update summary metrics
                total_processed += chunk_start_rows
                build_summary['total_rows_processed'] += chunk_start_rows
                build_summary['total_rows_saved'] += len(cleaned_chunk)
                build_summary['chunks_processed'] = chunk_number
                
                # Store validation results for this chunk
                build_summary['validation_results'][f'chunk_{chunk_number}'] = validation_result
                
                logger.info(f"Chunk {chunk_number} complete: {len(cleaned_chunk):,} rows saved")
        
        # 9. Final summary
        logger.info(f"Processing complete: {build_summary['total_rows_processed']:,} total rows processed")
        
        build_summary['performance_metrics'] = calculate_processing_efficiency(
            build_summary['total_rows_saved'],
            build_summary['total_rows_processed']
        )
        
        logger.info(f"✅ fact_player_play build complete: {build_summary['total_rows_saved']:,} rows saved")
        return build_summary
        
    except Exception as e:
        logger.error(f"❌ fact_player_play build failed: {e}", exc_info=True)
        build_summary['status'] = 'error'
        build_summary['message'] = str(e)
        return build_summary