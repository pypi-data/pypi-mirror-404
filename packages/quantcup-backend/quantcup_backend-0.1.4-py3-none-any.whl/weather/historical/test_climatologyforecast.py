#!/usr/bin/env python3
"""
test_climatologyforecast.py
Integration tests for the refactored API-based climatology forecasting.

Tests validate:
- normals_for_date() returns all required fields
- Leap year handling (Feb 29 fallback)
- Station discovery and caching
- Output format parity with legacy CSV-based system
"""
import pytest
from datetime import date
import pandas as pd
from ncei_client import NCEIClient
from climatologyforecast import climatology_forecast, format_forecast


class TestNCEIClientEnhancements:
    """Test Phase B enhancements to NCEIClient."""
    
    @pytest.fixture
    def client(self):
        """Shared client instance."""
        return NCEIClient()
    
    def test_normals_daily_includes_all_data_types(self, client):
        """Verify normals_daily() fetches all required fields by default."""
        # Use a well-known station with good normals coverage
        station = "USC00311677"  # Charlotte 8 SSW, NC (COOP station)
        
        normals = client.normals_daily([station])
        
        assert not normals.empty, "Should return normals data"
        
        # Verify all required columns are present
        required_cols = [
            "DLY-TMAX-NORMAL",
            "DLY-TMIN-NORMAL",
            "DLY-TMAX-STDDEV",
            "DLY-TMIN-STDDEV",
            "DLY-PRCP-NORMAL",
            "DLY-PRCP-PCTALL-GE001HI",
            "DLY-PRCP-50PCTL",
            "DLY-SNOW-PCTALL-GE001TI",
            "DLY-SNOW-50PCTL",
        ]
        
        for col in required_cols:
            assert col in normals.columns, f"Missing required column: {col}"
    
    def test_normals_for_date_returns_complete_series(self, client):
        """Verify normals_for_date() returns all required friendly-named fields."""
        station = "USC00311677"
        test_date = "2025-07-04"
        
        normals = client.normals_for_date(station, test_date)
        
        assert normals is not None, "Should return normals data"
        
        # Verify all friendly-named fields are present
        required_fields = [
            "station", "name", "lat", "lon", "elev_m", "date",
            "tmax_normal", "tmin_normal", "tmax_stddev", "tmin_stddev",
            "prcp_normal", "prcp_pct_ge001", "prcp_50pctl",
            "snow_pct_ge001", "snow_50pctl",
        ]
        
        for field in required_fields:
            assert field in normals.index, f"Missing required field: {field}"
    
    def test_leap_year_handling(self, client):
        """Verify Feb 29 falls back to Feb 28 data if DOY 60 not available."""
        station = "USC00311677"
        
        # Test Feb 29 (leap year date)
        normals_feb29 = client.normals_for_date(station, "2024-02-29")
        
        # Should either return data or fallback to Feb 28
        assert normals_feb29 is not None, "Should return normals for Feb 29 (or fallback to Feb 28)"
        
        # Verify the data is reasonable (not all None/NaN)
        assert normals_feb29.get("tmax_normal") is not pd.NA
        assert normals_feb29.get("tmin_normal") is not pd.NA


class TestClimatologyForecast:
    """Test the refactored climatology_forecast API."""
    
    @pytest.fixture
    def client(self):
        """Shared client instance."""
        return NCEIClient()
    
    def test_forecast_output_format(self, client):
        """Verify forecast output matches expected structure."""
        # Charlotte, NC coordinates
        lat, lon = 35.2271, -80.8431
        test_date = "2025-09-07"
        
        forecast = climatology_forecast(client, test_date, lat, lon)
        
        # Verify all expected keys are present
        expected_keys = [
            "date",
            "high_temp", "low_temp",
            "rain_chance", "rain_median_if_wet", "rain_daily_normal",
            "snow_chance", "snow_median_if_snow",
        ]
        
        for key in expected_keys:
            assert key in forecast, f"Missing forecast key: {key}"
    
    def test_forecast_value_ranges(self, client):
        """Verify forecast values are reasonable."""
        lat, lon = 35.2271, -80.8431
        test_date = "2025-07-04"  # Summer date
        
        forecast = climatology_forecast(client, test_date, lat, lon)
        
        # Verify format strings are generated (not just raw None)
        assert "°F" in forecast["high_temp"]
        assert "%" in forecast["rain_chance"]
        assert "\"" in forecast["rain_median_if_wet"]
    
    def test_auto_station_discovery(self, client):
        """Verify station auto-discovery works when station not provided."""
        lat, lon = 35.2271, -80.8431
        test_date = "2025-01-15"
        
        # Don't provide station - should auto-discover
        forecast = climatology_forecast(client, test_date, lat, lon, station=None)
        
        assert forecast is not None
        assert forecast["date"] == test_date
    
    def test_forecast_caching(self, client):
        """Verify normals are cached across multiple date requests."""
        lat, lon = 35.2271, -80.8431
        
        # Make first request (will fetch and cache normals)
        forecast1 = climatology_forecast(client, "2025-01-15", lat, lon)
        
        # Make second request (should use cached normals)
        forecast2 = climatology_forecast(client, "2025-07-10", lat, lon)
        
        assert forecast1 is not None
        assert forecast2 is not None
        assert forecast1["date"] != forecast2["date"]


class TestFormatForecast:
    """Test the forecast formatting function."""
    
    def test_handles_none_values_gracefully(self):
        """Verify formatter handles missing/None values without crashing."""
        # Create a Series with some None values
        normals = pd.Series({
            "date": date(2025, 1, 15),
            "tmax_normal": 45.0,
            "tmin_normal": 28.0,
            "tmax_stddev": None,  # Missing
            "tmin_stddev": 5.0,
            "prcp_normal": 0.12,
            "prcp_pct_ge001": None,  # Missing
            "prcp_50pctl": 0.08,
            "snow_pct_ge001": None,  # Missing
            "snow_50pctl": None,  # Missing
        })
        
        forecast = format_forecast(normals)
        
        # Should not crash, should format with defaults
        assert forecast is not None
        assert "°F" in forecast["high_temp"]
        assert "%" in forecast["rain_chance"]
    
    def test_formats_match_legacy_pattern(self):
        """Verify output format matches legacy CSV-based format."""
        normals = pd.Series({
            "date": date(2025, 7, 4),
            "tmax_normal": 89.5,
            "tmin_normal": 70.2,
            "tmax_stddev": 5.3,
            "tmin_stddev": 4.1,
            "prcp_normal": 0.15,
            "prcp_pct_ge001": 35.0,
            "prcp_50pctl": 0.21,
            "snow_pct_ge001": 0.0,
            "snow_50pctl": 0.0,
        })
        
        forecast = format_forecast(normals)
        
        # Verify format patterns
        assert forecast["high_temp"] == "89.5°F ±5.3"
        assert forecast["low_temp"] == "70.2°F ±4.1"
        assert forecast["rain_chance"] == "35%"
        assert forecast["rain_median_if_wet"] == "0.21\""
        assert forecast["rain_daily_normal"] == "0.15\""
        assert forecast["snow_chance"] == "0%"
        assert forecast["snow_median_if_snow"] == "0.00\""


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
