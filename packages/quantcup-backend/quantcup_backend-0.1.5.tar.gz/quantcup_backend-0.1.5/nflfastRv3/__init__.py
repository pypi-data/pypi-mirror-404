"""
NFLfastRv3 - Clean Architecture Public API

Facade APIs following Minimum Viable Decoupling pattern:
- Maximum 3 layers depth
- 5 complexity points per module
- DI with sensible defaults
- "Can I Trace This?" test compliance

Architecture:
Layer 1: Public APIs (this file) →
Layer 2: Feature implementations →
Layer 3: Infrastructure (database, R, etc.)
"""

__version__ = "3.0.0"

# Core imports for facade functions
from commonv2 import get_logger
from .shared.database_router import get_database_router

# Module-level logger following REFACTORING_SPECS.md pattern
_logger = get_logger('nflfastRv3.__init__')


def run_data_pipeline(groups=None, seasons=None, **kwargs):
    """
    Load and process NFL data with clean architecture.
    
    Pattern: Minimum Viable Decoupling (2 points, 2 layers)
    Call Chain: run_data_pipeline() → DataPipeline() → Database
    
    Args:
        groups: Data source groups to load (default: ['nfl_data'])
        seasons: Seasons to load (default: current season)
        **kwargs: Optional overrides:
            - db_service: Custom database service (for testing)
            - logger: Custom logger instance
            
    Returns:
        dict: Processing summary with status, tables, and row counts
        
    Example:
        >>> # Simple usage - all defaults
        >>> result = run_data_pipeline()
        >>> print(f"Status: {result['status']}")
        
        >>> # Custom groups
        >>> result = run_data_pipeline(groups=['nfl_data', 'fantasy'])
    """
    # Set API context for lazy session naming before logger creation
    from commonv2.core.logging import LoggingSessionManager
    session_manager = LoggingSessionManager.get_instance()
    session_manager.set_api_context('data_pipeline')
    
    # Layer 1: Create dependencies with sensible defaults (hidden complexity)
    db_service = kwargs.get('db_service') or get_database_router()
    logger = kwargs.get('logger') or get_logger('nflfastRv3.data_pipeline')
    
    # Layer 2: Delegate to orchestrator (single call - no pattern stacking)
    from .features.data_pipeline.pipeline_orchestrator import DataPipeline
    return DataPipeline(db_service, logger).process(groups, seasons)


def run_ml_pipeline(train_seasons, feature_sets=None, **kwargs):
    """
    Execute machine learning pipeline with clean architecture.
    
    Pattern: Minimum Viable Decoupling (2 points, 2 layers)
    Call Chain: run_ml_pipeline() → MLPipelineImpl() → Database/Models
    
    Args:
        train_seasons: Seasons for training (default: last 4 years)
        feature_sets: Feature sets to build (default: all)
        **kwargs: Optional overrides:
            - db_service: Custom database service (for testing)
            - logger: Custom logger instance
            
    Returns:
        dict: ML summary with model path, features built, predictions
        
    Example:
        >>> # Train on recent data
        >>> result = run_ml_pipeline(train_seasons='2020-2023')
        >>> print(f"Model saved: {result['model_path']}")
    """
    # Set API context for lazy session naming before logger creation
    from commonv2.core.logging import LoggingSessionManager
    session_manager = LoggingSessionManager.get_instance()
    session_manager.set_api_context('ml_pipeline')
    
    # Layer 1: Create dependencies with sensible defaults
    db_service = kwargs.get('db_service') or get_database_router()
    logger = kwargs.get('logger') or get_logger('nflfastRv3.ml_pipeline')
    
    # Layer 2: Delegate to implementation
    from .features.ml_pipeline.main import MLPipelineImpl
    return MLPipelineImpl(db_service, logger).process(train_seasons, feature_sets)


def run_analytics(analysis_type='exploratory', **kwargs):
    """
    Run analytics and reporting with clean architecture.
    
    Pattern: Minimum Viable Decoupling (2 points, 2 layers)
    Call Chain: run_analytics() → AnalyticsImpl() → Database/Reports
    
    Args:
        analysis_type: Type of analysis ('exploratory', 'feature_analysis')
        **kwargs: Optional overrides:
            - output_format: 'console', 'file', 'json'
            - db_service: Custom database service (for testing)
            - logger: Custom logger instance
            
    Returns:
        dict: Analysis results with status, type, and outputs
        
    Example:
        >>> # Basic exploratory analysis
        >>> result = run_analytics()
        >>> print(result['summary'])
    """
    # Set API context for lazy session naming before logger creation
    from commonv2.core.logging import LoggingSessionManager
    session_manager = LoggingSessionManager.get_instance()
    session_manager.set_api_context('analytics')
    
    # Layer 1: Create dependencies with sensible defaults
    db_service = kwargs.get('db_service') or get_database_router()
    logger = kwargs.get('logger') or get_logger('nflfastRv3.analytics')
    
    # Layer 2: Delegate to implementation
    from .features.analytics_suite.main import AnalyticsImpl
    return AnalyticsImpl(db_service, logger).process(analysis_type, **kwargs)


# CLI support
from .cli.main import main as cli_main

# Public API exports
__all__ = [
    'run_data_pipeline',
    'run_ml_pipeline',
    'run_analytics',
    'cli_main',  # CLI entry point
]

