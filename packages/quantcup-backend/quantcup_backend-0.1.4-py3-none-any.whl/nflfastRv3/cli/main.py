"""
Main CLI Entry Point for nflfastRv3

Simple command-line interface for accessing all nflfastRv3 capabilities.

Pattern: Basic CLI routing
Complexity: 1 point (simple command dispatch)
Layer: 1 (Public interface)
"""

import argparse
import sys
from typing import List, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

from commonv2 import get_logger
from .data_commands import DataCommands
from .ml_commands import MLCommands

# Module-level logger following proper singleton pattern
_logger = get_logger('nflfastRv3.cli.main')

def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog='nflfastRv3',
        description='NFL Data Analysis Pipeline - Clean Architecture v3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  nflfastRv3 data process --group nfl_data
  nflfastRv3 ml train --model-name game_outcome --train-years 5 --test-year 2025
  nflfastRv3 ml backtest --model-name game_outcome --train-years 5 --start-year 2020 --end-year 2024
  nflfastRv3 ml optimize-window --model-name game_outcome --test-year 2025 --test-week 13
        '''
    )
    
    # Add version info
    parser.add_argument('--version', action='version', version='nflfastRv3 3.0.0')
    
    # Create subparsers for main command groups
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='COMMAND'
    )
    
    # Data pipeline commands
    data_parser = subparsers.add_parser(
        'data',
        help='Data pipeline operations',
        description='Run data pipeline workflows'
    )
    DataCommands.setup_parser(data_parser)
    
    # ML pipeline commands
    ml_parser = subparsers.add_parser(
        'ml',
        help='Machine learning workflows',
        description='Run ML training and prediction workflows'
    )
    MLCommands.setup_parser(ml_parser)
    
    # Info command
    info_parser = subparsers.add_parser(
        'info',
        help='Display system information'
    )
    info_parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed information'
    )
    
    return parser

def show_system_info(detailed: bool, logger=None) -> int:
    """Show system information."""
    logger = logger or _logger
    
    logger.info("🏗️ nflfastRv3 System Information")
    logger.info("=" * 40)
    import nflfastRv3
    from ..features.data_pipeline.config.data_sources import log_datasource_stats
    logger.info(f"Version: {nflfastRv3.__version__}")
    logger.info("Architecture: Clean Architecture with Minimum Viable Decoupling")
    logger.info("Components: Data Pipeline, ML Pipeline, Analytics Suite")
    
    # Data pipeline status
    try:
        from ..features.data_pipeline import validate_data_architecture
        data_status = validate_data_architecture()
        logger.info(f"Data Pipeline: {data_status['overall_status']}")
    except Exception as e:
        logger.info(f"Data Pipeline: error ({str(e)[:50]}...)")
    
    if detailed:
        # Log data source statistics in detailed mode
        log_datasource_stats()
        
        logger.info("Component Details:")
        logger.info("- Data Pipeline: ETL workflows with quality checks")
        logger.info("- ML Pipeline: XGBoost training and prediction")
        logger.info("- Analytics Suite: Exploratory and feature analysis")
        logger.info("Architecture Constraints:")
        logger.info("- Maximum 3 layers depth")
        logger.info("- 5 complexity points budget per module")
        logger.info("- Dependency injection throughout")
    
    return 0

def main(argv: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        argv: Command line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if argv is None:
        argv = sys.argv[1:]
    
    parser = create_parser()
    
    # Handle no arguments
    if not argv:
        parser.print_help()
        return 1
    
    try:
        args = parser.parse_args(argv)
        
        # Create logger for CLI session
        logger = get_logger('nflfastRv3.cli')
        # Dispatch to appropriate command handler
        if args.command == 'data':
            return DataCommands.handle(args, logger)
        elif args.command == 'ml':
            return MLCommands.handle(args, logger)
        elif args.command == 'info':
            return show_system_info(args.detailed, logger)
        else:
            parser.print_help()
            return 1

            
    except KeyboardInterrupt:
        logger = get_logger('nflfastRv3.cli')
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger = get_logger('nflfastRv3.cli')
        logger.error(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
