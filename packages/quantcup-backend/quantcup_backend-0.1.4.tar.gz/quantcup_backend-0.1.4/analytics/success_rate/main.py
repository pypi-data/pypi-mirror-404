"""
Success Rate Analysis Main

Entry point for success rate analysis.
Simplified from analytics/generate_success_rate_chart_refactored.py following Solo Developer pattern.
"""

import uuid
import time

from commonv2 import get_logger
from . import data_loader
from . import calculator
from . import chart_renderer
from .models import AnalysisConfig, SuccessRateAnalysisResult


def generate_success_rate_analysis(engine, logger, config: AnalysisConfig) -> SuccessRateAnalysisResult:
    """
    Generate success rate analysis.
    
    Args:
        engine: Database engine
        logger: Logger instance
        config: AnalysisConfig with season, max_week, and chart_config
        
    Returns:
        SuccessRateAnalysisResult
    """
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    
    logger.info(f"Starting success rate analysis (ID: {analysis_id})")
    logger.info(f"Season: {config.season}, Max Week: {config.max_week}")
    
    try:
        # Step 1: Load data
        logger.info("Loading play data...")
        play_data_df = data_loader.load_play_data_raw(engine, config.season, config.max_week)
        
        logger.info("Loading team data...")
        team_data = data_loader.load_team_data()
        
        # Step 2: Calculate success rates
        logger.info("Calculating success rates...")
        team_success_rates = calculator.calculate_success_rates(play_data_df, team_data)
        
        # Step 3: Calculate league averages
        logger.info("Calculating league averages...")
        league_averages = calculator.calculate_league_averages(team_success_rates)
        
        # Step 4: Render chart (if requested)
        chart_path = None
        if config.include_chart and config.chart_config:
            logger.info("Rendering success rate chart...")
            
            # Validate chart config
            if chart_renderer.validate_chart_config(config.chart_config):
                chart_path = chart_renderer.render_success_rate_chart(
                    team_success_rates, league_averages, config.chart_config
                )
            else:
                logger.warning("Invalid chart configuration, skipping chart generation")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Create result
        result = SuccessRateAnalysisResult(
            team_success_rates=team_success_rates,
            league_averages=league_averages,
            chart_path=chart_path,
            analysis_id=analysis_id,
            season=config.season,
            max_week=config.max_week,
            execution_time_seconds=execution_time
        )
        
        logger.info(f"Success rate analysis completed in {execution_time:.2f} seconds")
        logger.info(f"Analyzed {len(team_success_rates)} teams")
        if chart_path:
            logger.info(f"Chart saved to: {chart_path}")
        
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Success rate analysis failed after {execution_time:.2f} seconds: {e}")
        raise


if __name__ == "__main__":
    """
    Standalone execution for testing.
    """
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from commonv2 import create_db_engine_from_env
    from .models import ChartConfig, AnalysisConfig, CalculationMethod
    
    # Setup logging
    logger = get_logger(__name__)
    
    try:
        # Create database engine
        engine = create_db_engine_from_env('NFLFASTR_DB')
        
        # Configure analysis
        chart_config = ChartConfig(
            title="Success Rate on Rushes vs Passes\nThrough Week 3 of the 2025 NFL Season",
            x_axis_label="Success Rate on Rushes",
            y_axis_label="Success Rate on Passes",
            save_path="analyticsv2/success_rate_chart_v2.png"
        )
        
        config = AnalysisConfig(
            season=2025,
            max_week=3,
            calculation_method=CalculationMethod.EPA_BASED,
            chart_config=chart_config,
            include_chart=True
        )
        
        # Run analysis
        result = generate_success_rate_analysis(engine, logger, config)
        
        # Display results
        print(f"\nSuccess rate analysis completed!")
        print(f"Teams analyzed: {len(result.team_success_rates)}")
        print(f"Execution time: {result.execution_time_seconds:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Standalone execution failed: {e}")
        sys.exit(1)
