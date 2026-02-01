#!/usr/bin/env python3
"""
climatologyforecast.py
API-based climatology forecaster using NCEIClient.

Generates baseline climatology forecasts using NOAA Daily Normals (1991-2020)
fetched via the NCEI API instead of pre-distilled CSV files.
"""
import argparse
from typing import Optional, Dict, Any
import pandas as pd

from commonv2.core.logging import setup_logger

# Handle both module import and direct script execution
try:
    from .ncei_client import NCEIClient
except ImportError:
    from ncei_client import NCEIClient

# Set up logger
logger = setup_logger('weather.historical.climatology', project_name='WEATHER')


def format_forecast(normals: pd.Series) -> Dict[str, Any]:
    """
    Format normals_for_date() output to match legacy CSV-based behavior.
    
    Args:
        normals: Series returned from NCEIClient.normals_for_date()
        
    Returns:
        Dictionary with formatted forecast fields
    """
    def safe_float(val, default=0.0):
        """Safely convert to float, handling None/NaN."""
        if pd.isna(val):
            return default
        return float(val)
    
    return {
        "date": normals["date"].strftime("%Y-%m-%d") if hasattr(normals["date"], "strftime") else str(normals["date"]),
        # 🌡 Temperature
        "high_temp": f"{safe_float(normals.get('tmax_normal')):.1f}°F ±{safe_float(normals.get('tmax_stddev')):.1f}",
        "low_temp": f"{safe_float(normals.get('tmin_normal')):.1f}°F ±{safe_float(normals.get('tmin_stddev')):.1f}",
        # 🌧 Rain
        "rain_chance": f"{safe_float(normals.get('prcp_pct_ge001')):.0f}%",
        "rain_median_if_wet": f"{safe_float(normals.get('prcp_50pctl')):.2f}\"",
        "rain_daily_normal": f"{safe_float(normals.get('prcp_normal')):.2f}\"",
        # ❄️ Snow
        "snow_chance": f"{safe_float(normals.get('snow_pct_ge001')):.0f}%",
        "snow_median_if_snow": f"{safe_float(normals.get('snow_50pctl')):.2f}\"",
    }


def climatology_forecast(
    client: NCEIClient,
    date: str,
    lat: float,
    lon: float,
    station: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get climatology forecast for a date near a location.
    
    Args:
        client: NCEIClient instance
        date: Target date (YYYY-MM-DD or MM-DD)
        lat, lon: Location coordinates
        station: Optional station ID; will auto-discover if not provided
    
    Returns:
        Formatted forecast dict
        
    Raises:
        ValueError: If no normals station found or no data available
    """
    # Normalize date
    try:
        parsed_date = pd.to_datetime(date)
    except Exception as e:
        raise ValueError(f"Invalid date format '{date}': {e}")
    
    # Resolve station
    if not station:
        logger.info(f"Auto-discovering normals station near ({lat}, {lon})")
        # Try nearby first (50km), then expand if needed
        station = client.find_normals_station_near(lat, lon, radius_km=50.0)
        if not station:
            logger.warning("No stations found within 50km, expanding to 100km...")
            station = client.find_normals_station_near(lat, lon, radius_km=100.0)
        if not station:
            raise ValueError(f"No normals station found within 100km of ({lat}, {lon})")
        logger.info(f"Using station: {station}")
    
    # Fetch normals once (cached for multiple dates)
    logger.debug(f"Fetching normals data for station {station}")
    normals_df = client.normals_daily([station])
    if normals_df.empty:
        raise ValueError(f"No normals data available for station {station}")
    
    # Get specific date
    normals = client.normals_for_date(station, parsed_date, cache_normals=normals_df)
    if normals is None:
        raise ValueError(f"No normals data for {parsed_date.date()} at {station}")
    
    return format_forecast(normals)


def main():
    """CLI entry point for climatology forecasting."""
    parser = argparse.ArgumentParser(
        description="Generate climatology forecast using NCEI API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-discover station near Charlotte, NC
  python climatologyforecast.py --lat 35.2271 --lon -80.8431 --date 2025-09-07
  
  # Use specific station
  python climatologyforecast.py --lat 35.2271 --lon -80.8431 --date 2025-09-07 --station USC00311677
  
  # Multiple dates
  python climatologyforecast.py --lat 35.2271 --lon -80.8431 --date 2025-01-15 --date 2025-07-10
        """
    )
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lon", type=float, required=True, help="Longitude")
    parser.add_argument("--date", action="append", required=True, help="Target date (YYYY-MM-DD). Can specify multiple times.")
    parser.add_argument("--station", help="Optional station ID (e.g., USC00311677)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logger.setLevel('DEBUG')
    
    # Initialize client
    client = NCEIClient()
    
    # Process each date
    for date_str in args.date:
        try:
            forecast = climatology_forecast(
                client, date_str, args.lat, args.lon, args.station
            )
            
            print(f"\n{'='*60}")
            print(f"Climatology Forecast for {forecast['date']}")
            print(f"{'='*60}")
            print(f"  High: {forecast['high_temp']}")
            print(f"  Low:  {forecast['low_temp']}")
            print(f"  Rain: {forecast['rain_chance']} (median if wet: {forecast['rain_median_if_wet']})")
            print(f"       (daily normal: {forecast['rain_daily_normal']})")
            print(f"  Snow: {forecast['snow_chance']} (median if snow: {forecast['snow_median_if_snow']})")
            
        except Exception as e:
            logger.error(f"Failed to generate forecast for {date_str}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
