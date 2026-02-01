"""
Data Pipeline CLI Commands

Command-line interface for data pipeline operations.

Pattern: Simple command handlers with extracted utilities
Complexity: 2 points (basic routing + extracted functions)
Layer: 1 (Public interface)

ENHANCED: Phase 1 - Simple error tracking and session summary logging
REFACTORED: Extracted utility functions to reduce complexity per function
"""

import argparse
from typing import Any

from commonv2 import get_logger
from ..features.data_pipeline.config.data_sources import (
    list_all_sources,
    log_datasource_stats,
    WAREHOUSE_COLUMN_REQUIREMENTS
)

# Module-level logger following proper singleton pattern
_logger = get_logger('nflfastRv3.cli.data')


class DataCommands:
    """Data pipeline command handlers."""
    
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        """Setup data command arguments."""
        subparsers = parser.add_subparsers(dest='data_command', help='Data operations')
        
        # Data processing command
        process_parser = subparsers.add_parser(
            'process',
            help='Process data through pipeline'
        )
        # V1-style mutually exclusive table/group processing
        process_parser.add_argument(
            '--table',
            action='append',
            help='Specific table(s) to load (auto-discovers group)'
        )
        process_parser.add_argument(
            '--group',
            action='append',
            choices=['nfl_data', 'fantasy', 'draft', 'health', 'teams', 'all'],
            help='Data source group(s) to process'
        )
        process_parser.add_argument(
            '--output-format',
            choices=['console', 'json', 'file'],
            default='console',
            help='Output format'
        )
        
        # Data validation command
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate data quality'
        )
        validate_parser.add_argument(
            '--table',
            action='append',
            help='Specific table(s) to validate'
        )
        validate_parser.add_argument(
            '--group',
            action='append',
            choices=['nfl_data', 'fantasy', 'draft', 'health', 'teams', 'all'],
            help='Data source group(s) to validate'
        )
        
        # Data warehouse command
        warehouse_parser = subparsers.add_parser(
            'warehouse',
            help='Build data warehouse'
        )
        
        # Table selection arguments - dynamically populate from WAREHOUSE_COLUMN_REQUIREMENTS
        warehouse_tables = list(WAREHOUSE_COLUMN_REQUIREMENTS.keys()) + ['all']
        warehouse_parser.add_argument(
            '--tables',
            nargs='+',
            choices=warehouse_tables,
            help=f'Specific tables to build (choices: {", ".join(warehouse_tables)}, default: all)'
        )
        
        warehouse_parser.add_argument(
            '--dimensions-only',
            action='store_true',
            help='Build only dimension tables'
        )
        
        warehouse_parser.add_argument(
            '--facts-only',
            action='store_true',
            help='Build only fact tables'
        )
        
        warehouse_parser.add_argument(
            '--seasons',
            nargs='+',
            type=int,
            help='Specific seasons for fact tables (e.g., --seasons 2023 2024)'
        )
        
        warehouse_parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Rebuild warehouse from scratch (clears existing data)'
        )
    
    @staticmethod
    def handle(args: Any, logger=None) -> int:
        """Handle data commands."""
        logger = logger or _logger
        
        if args.data_command == 'process':
            return DataCommands._handle_process(args, logger)
        elif args.data_command == 'validate':
            return DataCommands._handle_validate(args, logger)
        elif args.data_command == 'warehouse':
            return DataCommands._handle_warehouse(args, logger)
        else:
            logger.error("No data command specified. Use --help for options.")
            return 1
    
    @staticmethod
    def _handle_process(args: Any, logger=None) -> int:
        """
        Handle data processing command.
        
        Pattern: Simple command handler with extracted utilities
        Complexity: 2 points (basic routing + validation)
        """
        logger = logger or _logger
        
        # V1-style validation: mutually exclusive table/group
        if args.table and args.group:
            logger.error("Cannot specify both --table and --group options")
            return 1
        
        # Log what we're processing
        _log_processing_intent(args, logger)
        
        try:
            # Execute the pipeline processing
            result = _execute_pipeline_processing(args, logger)
            
            # Handle results and logging
            return _handle_processing_results(result, logger)
            
        except Exception as e:
            logger.error(f"❌ Data processing failed: {e}")
            _log_simple_session_summary({
                'total_groups': 0,
                'successful_groups': 0,
                'success_rate': 0,
                'total_rows': 0,
                'error_count': 1,
                'warning_count': 0,
                'status': 'CRITICAL_FAILURE'
            }, logger)
            return 1
    
    @staticmethod
    def _handle_validate(args: Any, logger=None) -> int:
        """Handle data validation command."""
        logger = logger or _logger
        
        # V1-style validation: mutually exclusive table/group
        if args.table and args.group:
            logger.error("Cannot specify both --table and --group options")
            return 1
        
        if args.table:
            logger.info(f"🔍 Validating specific tables: {args.table}")
            sources = args.table
        elif args.group:
            logger.info(f"🔍 Validating groups: {args.group}")
            # Get all tables from specified groups
            sources = []
            from ..features.data_pipeline.config.data_sources import DATA_SOURCE_GROUPS
            for group_name in args.group:
                if group_name == 'all':
                    sources = list_all_sources()
                    break
                elif group_name in DATA_SOURCE_GROUPS:
                    sources.extend(DATA_SOURCE_GROUPS[group_name].keys())
        else:
            logger.info("🔍 Validating all data...")
            sources = list_all_sources()
        
        try:
            from ..shared.database_router import get_database_router

            # Create database connection and run basic validation
            db_service = get_database_router()
            
            # Basic validation: check if tables exist and have data
            engine = db_service.get_engine()
            if engine is None:
                logger.error("Failed to get database engine for validation")
                return 1
            
            validation_results = {}
            for source in sources:
                try:
                    with engine.connect() as conn:
                        from sqlalchemy import text
                        # Check if table exists in raw schema
                        result = conn.execute(text(f"""
                            SELECT COUNT(*) as row_count 
                            FROM raw_nflfastr.{source}
                        """))
                        row = result.fetchone()
                        row_count = row[0] if row else 0
                        
                        validation_results[source] = {
                            'exists': True,
                            'row_count': row_count,
                            'status': 'valid' if row_count > 0 else 'empty'
                        }
                        
                except Exception as e:
                    validation_results[source] = {
                        'exists': False,
                        'error': str(e),
                        'status': 'invalid'
                    }
            
            # Report results
            all_valid = True
            for source, result in validation_results.items():
                if result['status'] == 'valid':
                    logger.info(f"✅ {source}: {result['row_count']:,} rows")
                elif result['status'] == 'empty':
                    logger.warning(f"⚠️ {source}: Table exists but is empty")
                    all_valid = False
                else:
                    logger.error(f"❌ {source}: {result.get('error', 'Table not found')}")
                    all_valid = False
            
            if all_valid:
                logger.info("✅ All data validation passed")
                return 0
            else:
                logger.warning("⚠️ Some validation issues found")
                return 1
            
        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")
            return 1
    
    @staticmethod
    def _handle_warehouse(args: Any, logger=None) -> int:
        """
        Handle warehouse building command.
        
        Supports:
        - Building all tables
        - Building specific tables
        - Building dimensions only
        - Building facts only
        - Season filtering for facts
        """
        logger = logger or _logger
        logger.info("🏗️ Building data warehouse...")
        
        try:
            from ..features.data_pipeline import create_warehouse_builder
            
            # Create warehouse builder (auto-detects bucket vs database mode)
            builder = create_warehouse_builder(logger=logger)
            
            # Validate mutually exclusive options
            exclusive_options = [
                args.dimensions_only,
                args.facts_only,
                bool(args.tables and 'all' not in args.tables)
            ]
            if sum(exclusive_options) > 1:
                logger.error(
                    "❌ Cannot use --dimensions-only, --facts-only, and --tables together. "
                    "Choose one option."
                )
                return 1
            
            # Determine what to build
            if args.dimensions_only:
                logger.info("📊 Building dimension tables only...")
                result = builder.build_dimensions_only()
                
            elif args.facts_only:
                logger.info("📊 Building fact tables only...")
                if args.seasons:
                    logger.info(f"Filtering to seasons: {args.seasons}")
                result = builder.build_facts_only(seasons=args.seasons)
                
            elif args.tables and 'all' not in args.tables:
                logger.info(f"📊 Building specific tables: {args.tables}")
                if args.seasons:
                    logger.info(f"Filtering to seasons: {args.seasons}")
                result = builder.build_specific_tables(
                    table_names=args.tables,
                    seasons=args.seasons
                )
                
            else:
                logger.info("📊 Building all warehouse tables...")
                if args.seasons:
                    logger.info(f"Filtering fact tables to seasons: {args.seasons}")
                result = builder.build_all_tables(seasons=args.seasons)
            
            # Report results - handle success, partial, and failed statuses
            status = result.get('status', 'unknown')
            
            if status == 'success':
                # Handle both 'tables_built' (from build_all_tables/build_specific_tables)
                # and 'tables' (from build_dimensions_only/build_facts_only)
                tables = result.get('tables_built') or result.get('tables', [])
                logger.info("=" * 60)
                logger.info("✅ Data warehouse built successfully")
                logger.info(f"Tables built: {len(tables)}")
                logger.info(f"Tables: {', '.join(tables)}")
                logger.info(f"Total rows: {result.get('total_rows', 0):,}")
                logger.info("=" * 60)
                return 0
            elif status == 'partial':
                # Handle both 'tables_built' and 'tables' keys
                tables = result.get('tables_built') or result.get('tables', [])
                logger.warning("=" * 60)
                logger.warning("⚠️ Data warehouse built with some failures")
                logger.warning(f"Tables built: {len(tables)}")
                logger.warning(f"Tables: {', '.join(tables)}")
                logger.warning(f"Total rows: {result.get('total_rows', 0):,}")
                logger.warning("=" * 60)
                return 0  # Partial success still returns 0
            else:
                logger.error("=" * 60)
                logger.error(f"❌ Warehouse build failed: {result.get('error', 'Unknown error')}")
                logger.error("=" * 60)
                return 1
                
        except Exception as e:
            logger.error(f"❌ Warehouse building failed: {e}", exc_info=True)
            return 1


def _log_processing_intent(args: Any, logger):
    """Log what processing will be performed."""
    if args.table:
        logger.info(f"🔍 Processing specific tables: {args.table}")
    elif args.group:
        logger.info(f"🔍 Processing groups: {args.group}")
    else:
        logger.info("🔍 Processing default group: nfl_data")


def _execute_pipeline_processing(args: Any, logger):
    """Execute the data orchestrator processing based on arguments."""
    from ..features.data_pipeline.pipeline_orchestrator import DataPipeline
    from ..shared.database_router import get_database_router

    # Create and run data pipeline
    db_service = get_database_router()
    pipeline = DataPipeline(db_service, logger)
    
    # V1-style processing: either tables OR groups
    if args.table:
        # Process specific tables with auto-discovery
        return pipeline.process(tables=args.table, seasons=None)
    elif args.group:
        # Process specific groups
        groups_to_process = args.group
        if 'all' in groups_to_process:
            groups_to_process = ['nfl_data', 'fantasy', 'draft', 'health', 'teams']
        logger.info(f"📊 Processing groups: {groups_to_process}")
        return pipeline.process(groups=groups_to_process, seasons=None)
    else:
        # Default: process nfl_data group
        logger.info("📊 Processing default group: nfl_data")
        return pipeline.process(groups=['nfl_data'], seasons=None)


def _handle_processing_results(result: dict, logger) -> int:
    """Handle pipeline processing results and generate session summary."""
    group_results = result.get('group_results', {})
    error_count = 0
    
    # Count successful vs failed groups
    successful_groups = 0
    total_groups = len(group_results)
    
    for group, group_result in group_results.items():
        if group_result['status'] == 'success':
            successful_groups += 1
        else:
            error_count += 1
    
    if result.get('status') == 'success':
        logger.info("✅ Data processing completed successfully")
        total_rows = result.get('total_rows', 0)
        tables = result.get('tables', [])
        logger.info(f"Total records processed: {total_rows:,}")
        logger.info(f"Tables processed: {', '.join(tables)}")
        
        # Show group results
        for group, group_result in group_results.items():
            if group_result['status'] == 'success':
                logger.info(f"  ✓ {group}: {group_result['rows']:,} rows")
            else:
                logger.error(f"  ✗ {group}: {group_result.get('error', 'Unknown error')}")
                error_count += 1
        
        # Log session summary for successful runs
        _log_simple_session_summary({
            'total_groups': total_groups,
            'successful_groups': successful_groups,
            'success_rate': (successful_groups / total_groups * 100) if total_groups > 0 else 100,
            'total_rows': result.get('total_rows', 0),
            'error_count': error_count,
            'warning_count': 0,
            'status': 'SUCCESS'
        }, logger)
        
        logger.info("🎉 Data processing complete")
        return 0
    else:
        logger.error(f"❌ Data processing failed: {result.get('message', 'Unknown error')}")
        error_count += 1
        
        # Log session summary for failed runs
        _log_simple_session_summary({
            'total_groups': total_groups,
            'successful_groups': successful_groups,
            'success_rate': (successful_groups / total_groups * 100) if total_groups > 0 else 0,
            'total_rows': result.get('total_rows', 0),
            'error_count': error_count,
            'warning_count': 0,
            'status': 'FAILED'
        }, logger)
        return 1


def _log_simple_session_summary(summary: dict, logger=None):
    """
    Log simple session summary for trend analysis.
    
    ENHANCED: Phase 1 - Session summary logging (addresses degradation pattern)
    Pattern: Simple function with DI fallback (1 complexity point)
    
    Args:
        summary: Session summary metrics
        logger: Logger instance (optional, uses module logger if not provided)
    """
    # Use module-level logger with DI fallback pattern
    logger = logger or _logger
    
    # Get correlation context if available
    try:
        from commonv2.core.logging import LoggingSessionManager
        session_manager = LoggingSessionManager.get_instance()
        context = session_manager.get_execution_context()
        correlation_id = context.get('correlation_id', 'unknown')
        session_id = context.get('session_id', 'unknown')
    except:
        correlation_id = 'unknown'
        session_id = 'unknown'
    
    # Format summary for structured logging
    summary_str = " | ".join([f"{k}: {v}" for k, v in summary.items()])
    
    logger.info(
        f"SESSION_SUMMARY: {session_id} | {summary_str} | Correlation: {correlation_id}"
    )
    
    # Generate alerts based on success rate degradation
    success_rate = summary.get('success_rate', 0)
    if success_rate < 60:
        logger.warning(f"🚨 SESSION_ALERT: Success rate {success_rate:.1f}% below 60% threshold")
    elif success_rate < 80:
        logger.warning(f"⚠️ SESSION_NOTICE: Success rate {success_rate:.1f}% below 80% target")
