"""
Weather CLI for QuantCup

Simplified command-line interface for NOAA weather integration with schedule integration.
"""

import typer
from typing import Optional
from datetime import datetime
import json

from commonv2 import setup_logger
from commonv2.domain.schedules import SeasonParser
from .weather_processor import WeatherProcessor
from .game_weather import GameWeatherService

# Set up weather-specific logger
logger = setup_logger('weather_forecast', project_name='weather')

app = typer.Typer(help="NOAA Weather API integration for NFL games")


@app.command()
def week(
    week_number: int = typer.Argument(..., help="NFL week number (1-18)"),
    season: Optional[int] = typer.Option(None, help="Season year (defaults to current)"),
    include_domes: bool = typer.Option(False, help="Include dome games"),
    output_format: str = typer.Option("summary", help="Output format: summary, full, json, dataframe"),
    verbose: bool = typer.Option(False, help="Enable verbose output")
):
    """
    Get weather for all games in a specific NFL week.
    
    Examples:
        quantcup noaa week 15
        quantcup noaa week 1 --season 2024
        quantcup noaa week 10 --include-domes --output-format json
    """
    if verbose:
        logger.setLevel('DEBUG')
    
    if season is None:
        season = SeasonParser.get_current_season(logger)
    
    logger.info(f"Getting weather for Week {week_number}, {season} season")
    
    try:
        # Validate week number
        if not 1 <= week_number <= 22:
            typer.echo(f"❌ Invalid week number: {week_number}. Must be 1-22.", err=True)
            raise typer.Exit(1)
        
        # Get weather for all games in the week
        service = GameWeatherService(logger=logger)
        games_weather, meta = service.get_weather_for_week(
            week=week_number, 
            season=season, 
            include_domes=include_domes
        )
        
        scheduled = meta.get("scheduled_count", 0)
        returned = meta.get("returned_count", 0)
        unavailable = meta.get("unavailable_count", 0)
        
        if scheduled == 0:
            typer.echo(f"❌ No scheduled games for Week {week_number}, {season}")
            raise typer.Exit(0)
        
        # We always have rows now (placeholders included). If for some reason we don't, keep it non-fatal.
        if returned == 0:
            logger.warning("Games scheduled but no rows returned (unexpected).")
            typer.echo(f"⚠️  Games are scheduled for Week {week_number}, {season}, but forecasts aren't available yet.")
            raise typer.Exit(0)
        
        # Output results using consolidated processor
        processor = WeatherProcessor(logger=logger)
        if output_format == "json":
            typer.echo(json.dumps(games_weather, indent=2, default=str))
        elif output_format == "dataframe":
            processor.display_week_dataframe(games_weather, week_number, season)
        elif output_format == "full":
            processor.display_week_full(games_weather, week_number, season)
        else:  # summary
            processor.display_week_summary(games_weather, week_number, season)
        
        logger.info(f"Week {week_number} weather data displayed for {len(games_weather)} games")
        
    except Exception as e:
        logger.error(f"Failed to get weather for Week {week_number}: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def today(
    include_domes: bool = typer.Option(False, help="Include dome games"),
    output_format: str = typer.Option("summary", help="Output format: summary, full, json, dataframe"),
    verbose: bool = typer.Option(False, help="Enable verbose output")
):
    """
    Get weather for all NFL games happening today.
    
    Examples:
        quantcup noaa today
        quantcup noaa today --include-domes
        quantcup noaa today --output-format json
    """
    if verbose:
        logger.setLevel('DEBUG')
    
    today_date = datetime.now()
    logger.info(f"Getting weather for games today: {today_date.strftime('%Y-%m-%d')}")
    
    try:
        # Get weather for today's games
        service = GameWeatherService(logger=logger)
        games_weather = service.get_weather_for_day(
            date=today_date,
            include_domes=include_domes
        )
        
        if not games_weather:
            typer.echo(f"❌ No games scheduled for today ({today_date.strftime('%Y-%m-%d')})")
            logger.info(f"No games found for today: {today_date.strftime('%Y-%m-%d')}")
            raise typer.Exit(1)
        
        # Output results using consolidated processor
        processor = WeatherProcessor(logger=logger)
        if output_format == "json":
            typer.echo(json.dumps(games_weather, indent=2, default=str))
        elif output_format == "dataframe":
            processor.display_today_dataframe(games_weather, today_date)
        elif output_format == "full":
            processor.display_today_full(games_weather, today_date)
        else:  # summary
            processor.display_today_summary(games_weather, today_date)
        
        logger.info(f"Today's weather data displayed for {len(games_weather)} games")
        
    except Exception as e:
        logger.error(f"Failed to get weather for today: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
