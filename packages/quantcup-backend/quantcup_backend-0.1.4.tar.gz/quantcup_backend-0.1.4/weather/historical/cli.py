"""
Historical Weather CLI for QuantCup

Command-line interface for NCEI historical weather data and climatology.
"""

import typer
from typing import Optional, List
from datetime import datetime
import json

from commonv2.core.logging import setup_logger
from .ncei_client import NCEIClient
from .climatologyforecast import climatology_forecast, format_forecast

# Set up logger
logger = setup_logger('weather.historical.cli', project_name='WEATHER')

app = typer.Typer(help="NCEI historical weather data and climatology")


@app.command()
def climatology(
    lat: float = typer.Option(..., help="Latitude (e.g., 35.2271)"),
    lon: float = typer.Option(..., help="Longitude (e.g., -80.8431)"),
    date: List[str] = typer.Option(..., help="Date(s) in YYYY-MM-DD format (can specify multiple)"),
    station: Optional[str] = typer.Option(None, help="NCEI station ID (auto-discovered if not specified)"),
    output_format: str = typer.Option("text", help="Output format: text, json"),
    verbose: bool = typer.Option(False, help="Enable verbose logging")
):
    """
    Get climatology forecast for specific date(s) and location.
    
    Retrieves 30-year climate normals for temperature, precipitation, and snow.
    Useful for baseline weather expectations when building models.
    
    Examples:
        quantcup weather historical climatology --lat 35.2271 --lon -80.8431 --date 2025-09-07
        quantcup weather historical climatology --lat 35.2271 --lon -80.8431 --date 2025-01-15 --date 2025-07-10
        quantcup weather historical climatology --lat 35.2271 --lon -80.8431 --date 2025-09-07 --station USC00311677
    """
    if verbose:
        logger.setLevel('DEBUG')
    
    try:
        client = NCEIClient()
        results = []
        
        for date_str in date:
            forecast = climatology_forecast(
                client=client,
                date=date_str,
                lat=lat,
                lon=lon,
                station=station
            )
            
            if forecast is None:
                typer.echo(f"❌ No climatology data available for {date_str}", err=True)
                continue
            
            if output_format == "json":
                results.append({
                    'date': date_str,
                    'forecast': forecast
                })
            else:
                # Text output - display formatted forecast
                typer.echo(f"\n{'='*60}")
                typer.echo(f"Climatology Forecast for {date_str}")
                typer.echo(f"{'='*60}")
                typer.echo(f"  High: {forecast['high_temp']}")
                typer.echo(f"  Low:  {forecast['low_temp']}")
                typer.echo(f"  Rain: {forecast['rain_chance']} (median if wet: {forecast['rain_median_if_wet']})")
                typer.echo(f"       (daily normal: {forecast['rain_daily_normal']})")
                typer.echo(f"  Snow: {forecast['snow_chance']} (median if snow: {forecast['snow_median_if_snow']})")
                if len(date) > 1:
                    typer.echo()  # Blank line between multiple dates
        
        if output_format == "json":
            typer.echo(json.dumps(results, indent=2))
            
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(1)


@app.command()
def daily(
    station: str = typer.Argument(..., help="NCEI station ID (e.g., USC00311677)"),
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    output_format: str = typer.Option("text", help="Output format: text, json, csv"),
    verbose: bool = typer.Option(False, help="Enable verbose logging")
):
    """
    Get daily weather observations for a specific station and date range.
    
    Retrieves actual historical observations (temperature, precipitation, wind, etc.).
    Useful for backtesting models with real weather conditions.
    
    Examples:
        quantcup weather historical daily USC00311677 2024-09-01 2024-09-07
        quantcup weather historical daily USC00311677 2024-09-01 2024-09-07 --output-format json
    """
    if verbose:
        logger.setLevel('DEBUG')
    
    try:
        client = NCEIClient()
        
        # Get daily summaries
        df = client.daily_summaries(
            stations=station,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            typer.echo(f"❌ No data found for station {station} between {start_date} and {end_date}")
            raise typer.Exit(1)
        
        if output_format == "csv":
            typer.echo(df.to_csv(index=False))
        elif output_format == "json":
            typer.echo(df.to_json(orient="records", indent=2))
        else:
            # Text table output
            typer.echo(f"\n📊 Daily Weather Data: {station}")
            typer.echo(f"{'Date':<12} | {'High':<8} | {'Low':<8} | {'Precip':<8} | {'Snow':<8} | {'Wind':<8}")
            typer.echo("-" * 75)
            
            for _, row in df.iterrows():
                date_val = row.get('date', 'N/A')
                tmax = f"{row.get('TMAX', 'N/A')}°F" if row.get('TMAX') else 'N/A'
                tmin = f"{row.get('TMIN', 'N/A')}°F" if row.get('TMIN') else 'N/A'
                prcp = f"{row.get('PRCP', 'N/A'):}\"" if row.get('PRCP') else 'N/A'
                snow = f"{row.get('SNOW', 'N/A')}\"" if row.get('SNOW') else 'N/A'
                awnd = f"{row.get('AWND', 'N/A')}mph" if row.get('AWND') else 'N/A'
                
                typer.echo(f"{str(date_val):<12} | {tmax:<8} | {tmin:<8} | {prcp:<8} | {snow:<8} | {awnd:<8}")
            
            typer.echo()
            
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(1)


@app.command()
def find_stations(
    lat: float = typer.Option(..., help="Latitude"),
    lon: float = typer.Option(..., help="Longitude"),
    radius_km: float = typer.Option(50.0, help="Search radius in kilometers"),
    dataset: str = typer.Option("normals-daily", help="Dataset type: normals-daily, daily-summaries"),
    limit: int = typer.Option(10, help="Maximum number of stations to return"),
    verbose: bool = typer.Option(False, help="Enable verbose logging")
):
    """
    Find NCEI weather stations near a location.
    
    Useful for discovering station IDs to use with other commands.
    
    Examples:
        quantcup weather historical find-stations --lat 35.2271 --lon -80.8431
        quantcup weather historical find-stations --lat 35.2271 --lon -80.8431 --radius-km 100
    """
    if verbose:
        logger.setLevel('DEBUG')
    
    try:
        client = NCEIClient()
        
        # Use internal method to get station list
        stations = client._get_station_candidates(
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            limit=limit
        )
        
        if not stations:
            typer.echo(f"❌ No stations found within {radius_km}km of ({lat}, {lon})")
            raise typer.Exit(1)
        
        typer.echo(f"\n📍 Weather Stations near ({lat}, {lon})")
        typer.echo(f"Found {len(stations)} station(s) within {radius_km}km\n")
        typer.echo(f"{'ID':<15} | {'Name':<40} | {'Distance (km)':<15} | {'Elevation (m)':<15}")
        typer.echo("-" * 90)
        
        for station in stations[:limit]:
            station_id = station.id
            name = station.name[:38] if len(station.name) > 38 else station.name
            distance = f"{station.distance_km:.1f}"
            elevation = f"{station.elevation_m:.1f}" if station.elevation_m is not None else "N/A"
            
            typer.echo(f"{station_id:<15} | {name:<40} | {distance:<15} | {elevation:<15}")
        
        typer.echo()
        
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            typer.echo(traceback.format_exc(), err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
