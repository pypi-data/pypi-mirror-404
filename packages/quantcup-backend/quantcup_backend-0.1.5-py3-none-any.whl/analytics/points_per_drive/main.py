"""
Points Per Drive Analysis Main

Entry point for points per drive efficiency analysis.
Simplified from analytics/generate_points_per_drive_chart.py following Solo Developer pattern.
"""

import uuid
import time
from typing import Tuple

from commonv2 import get_logger
from . import data_loader
from . import calculator
from . import chart_renderer
from .models import AnalysisConfig, EfficiencyAnalysisResult


def generate_points_per_drive_analysis(engine, logger, config: AnalysisConfig) -> EfficiencyAnalysisResult:
    """
    Generate points per drive efficiency analysis.
    
    Args:
        engine: Database engine
        logger: Logger instance
        config: AnalysisConfig with season, max_week, and chart_config
        
    Returns:
        EfficiencyAnalysisResult with metrics and chart path
    """
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    
    logger.info(f"Starting points per drive analysis (ID: {analysis_id})")
    logger.info(f"Season: {config.season}, Max Week: {config.max_week}")
    
    try:
        # Step 1: Load data
        logger.info("Loading play data...")
        play_data = data_loader.load_play_data(engine, config.season, config.max_week)
        
        logger.info("Loading team data...")
        team_data = data_loader.load_team_data()
        
        # Step 2: Calculate efficiency metrics
        logger.info("Calculating efficiency metrics...")
        team_metrics = calculator.calculate_efficiency_metrics(play_data, team_data)
        
        # Step 3: Calculate league averages
        logger.info("Calculating league averages...")
        league_averages = calculator.calculate_league_averages(team_metrics)
        
        # Step 4: Render chart (if requested)
        chart_path = None
        if config.include_chart and config.chart_config:
            logger.info("Rendering efficiency chart...")
            
            # Validate chart config
            if chart_renderer.validate_chart_config(config.chart_config):
                chart_path = chart_renderer.render_efficiency_chart(
                    team_metrics, league_averages, config.chart_config
                )
            else:
                logger.warning("Invalid chart configuration, skipping chart generation")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Create result
        result = EfficiencyAnalysisResult(
            team_efficiency_metrics=team_metrics,
            league_averages=league_averages,
            chart_path=chart_path,
            analysis_id=analysis_id,
            season=config.season,
            max_week=config.max_week,
            execution_time_seconds=execution_time
        )
        
        logger.info(f"Analysis completed successfully in {execution_time:.2f} seconds")
        logger.info(f"Analyzed {len(team_metrics)} teams")
        if chart_path:
            logger.info(f"Chart saved to: {chart_path}")
        
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Analysis failed after {execution_time:.2f} seconds: {e}")
        raise


def generate_points_per_drive_analysis_simple(engine, logger, season: int, max_week: int, 
                                            chart_title: str, chart_path: str) -> Tuple[list, str]:
    """
    Simplified interface for backward compatibility.
    
    Args:
        engine: Database engine
        logger: Logger instance
        season: NFL season year
        max_week: Maximum week number
        chart_title: Title for the chart
        chart_path: Path to save the chart
        
    Returns:
        Tuple of (team_metrics, chart_path)
    """
    from .models import ChartConfig, AnalysisConfig, CalculationMethod
    
    # Create configuration
    chart_config = ChartConfig(
        title=chart_title,
        x_axis_label="Opponent-Adjusted Scoring Efficiency (higher = better)",
        y_axis_label="Opponent-Adjusted Stopping Efficiency (higher = better)",
        save_path=chart_path,
        use_dynamic_ranges=True,
        padding_percent=0.15,
        min_range_size=2.0,
        center_on_averages=True
    )
    
    config = AnalysisConfig(
        season=season,
        max_week=max_week,
        calculation_method=CalculationMethod.EPA_BASED,
        chart_config=chart_config,
        include_chart=True
    )
    
    # Run analysis
    result = generate_points_per_drive_analysis(engine, logger, config)
    
    return result.team_efficiency_metrics, result.chart_path


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
            title="NFL Points Per Drive Adjusted for Opponent After Week 3 2025-26",
            x_axis_label="Opponent-Adjusted Scoring Efficiency (higher = better)",
            y_axis_label="Opponent-Adjusted Stopping Efficiency (higher = better)",
            save_path="analyticsv2/points_per_drive_chart_v2.png",
            use_dynamic_ranges=True,
            padding_percent=0.15,
            min_range_size=2.0,
            center_on_averages=True
        )
        
        config = AnalysisConfig(
            season=2025,
            max_week=3,
            calculation_method=CalculationMethod.EPA_BASED,
            chart_config=chart_config,
            include_chart=True
        )
        
        # Run analysis
        result = generate_points_per_drive_analysis(engine, logger, config)
        
        # Display results
        print(f"\nAnalysis completed successfully!")
        print(f"Teams analyzed: {len(result.team_efficiency_metrics)}")
        print(f"Execution time: {result.execution_time_seconds:.2f} seconds")
        if result.chart_path:
            print(f"Chart saved to: {result.chart_path}")
        
        # Show top performers
        print(f"\nTop 5 Scoring Efficiency:")
        top_scoring = sorted(result.team_efficiency_metrics, 
                           key=lambda x: x.scoring_efficiency_ppd, reverse=True)[:5]
        for i, team in enumerate(top_scoring, 1):
            print(f"  {i}. {team.team} ({team.team_name}): {team.scoring_efficiency_ppd:.3f} PPD")
        
    except Exception as e:
        logger.error(f"Standalone execution failed: {e}")
        sys.exit(1)
