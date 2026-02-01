"""
Interactive endpoint testing script for sdv_wrapper.py

This script helps you explore what data different sportsdataverse endpoints return.
"""

from sportsdataverse.sdv_wrapper import SportsDataVerseClient
import json
from typing import Any
from pathlib import Path
from datetime import datetime


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def inspect_data(data: Any, name: str, max_rows: int = 5):
    """Inspect and display data returned from an endpoint"""
    print(f"\n📊 {name}")
    print("-" * 80)
    
    if isinstance(data, Exception):
        print(f"❌ Error: {type(data).__name__}: {data}")
        return
    
    # Check if it's a pandas DataFrame
    try:
        import pandas as pd
        if isinstance(data, pd.DataFrame):
            print(f"✅ Type: pandas DataFrame")
            print(f"   Shape: {data.shape} (rows, columns)")
            print(f"   Columns: {list(data.columns)}")
            print(f"\n   First {max_rows} rows:")
            print(data.head(max_rows).to_string())
            return
    except ImportError:
        pass
    
    # Check if it's a Polars DataFrame
    try:
        import polars as pl
        if isinstance(data, pl.DataFrame):
            print(f"✅ Type: Polars DataFrame")
            print(f"   Shape: {data.shape} (rows, columns)")
            print(f"   Columns: {data.columns}")
            print(f"\n   First {max_rows} rows:")
            print(data.head(max_rows))
            return
    except ImportError:
        pass
    
    # Handle dict
    if isinstance(data, dict):
        print(f"✅ Type: dict with {len(data)} keys")
        print(f"   Keys: {list(data.keys())[:10]}")  # Show first 10 keys
        if data:
            first_key = list(data.keys())[0]
            print(f"\n   Sample (first item):")
            print(f"   {first_key}: {data[first_key]}")
        return
    
    # Handle list
    if isinstance(data, list):
        print(f"✅ Type: list with {len(data)} items")
        if data:
            print(f"\n   First item type: {type(data[0])}")
            print(f"   First {min(3, len(data))} items:")
            for i, item in enumerate(data[:3]):
                print(f"   [{i}]: {item}")
        return
    
    # Default: just show type and value
    print(f"✅ Type: {type(data).__name__}")
    print(f"   Value: {str(data)[:500]}")  # Truncate long values


def main():
    # Prepare report output
    report_lines = []
    
    def log_to_report(message):
        """Add message to report"""
        report_lines.append(message)
    
    # Override print_section to also log to report
    original_print = print
    
    def tracked_print(*args, **kwargs):
        """Print and capture to report"""
        message = ' '.join(str(arg) for arg in args)
        original_print(message, **kwargs)
        log_to_report(message)
    
    # Temporarily replace print
    import builtins
    builtins.print = tracked_print
    
    print_section("🏈 SportsDataVerse Endpoint Explorer")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Initialize client
    client = SportsDataVerseClient(prefer_pandas=True, max_retries=2)
    
    # 1. Show available sports
    print_section("1. Available Sports")
    sports = client.available_sports()
    print(f"Found {len(sports)} sports: {sports}")
    
    # 2. Pick a sport to explore (default: NFL)
    sport = "nfl"
    print_section(f"2. Exploring {sport.upper()} Endpoints")
    
    try:
        endpoints = client.list_endpoints(sport)
        print(f"\nFound {len(endpoints)} endpoints:")
        for i, ep in enumerate(endpoints, 1):
            print(f"  {i:2d}. {ep}")
    except Exception as e:
        print(f"❌ Error listing endpoints: {e}")
        return
    
    # 3. Test simple endpoints (ones that don't require specific IDs)
    print_section("3. Testing Simple Endpoints (No Required Parameters)")
    
    # These typically work without parameters
    simple_endpoints = [
        "load_nfl_teams",
        "load_nfl_rosters", 
        "load_nfl_injuries",
    ]
    
    for endpoint in simple_endpoints:
        if endpoint in endpoints:
            print(f"\n🔍 Testing: {endpoint}")
            try:
                result = client.call(
                    sport,
                    endpoint,
                    shared_kwargs={"return_as_pandas": True}
                )
                inspect_data(result, endpoint)
            except Exception as e:
                print(f"❌ Error calling {endpoint}: {e}")
        else:
            print(f"⚠️  {endpoint} not found in available endpoints")
    
    # 4. Test endpoints with season parameter
    print_section("4. Testing Endpoints with Season Parameter")
    
    season_endpoints = [
        "load_nfl_pbp",
        "load_nfl_schedule",
    ]
    
    for endpoint in season_endpoints:
        if endpoint in endpoints:
            print(f"\n🔍 Testing: {endpoint} (seasons=[2024])")
            try:
                result = client.call(
                    sport,
                    endpoint,
                    shared_kwargs={"seasons": [2024], "return_as_pandas": True}
                )
                inspect_data(result, endpoint, max_rows=3)
            except Exception as e:
                print(f"❌ Error calling {endpoint}: {e}")
        else:
            print(f"⚠️  {endpoint} not found in available endpoints")
    
    # 5. Show ESPN endpoints (these usually need specific IDs)
    print_section("5. ESPN Endpoints (Require Specific IDs)")
    
    espn_endpoints = [ep for ep in endpoints if ep.startswith("espn_")]
    print(f"\nFound {len(espn_endpoints)} ESPN endpoints:")
    for ep in espn_endpoints[:10]:  # Show first 10
        print(f"  • {ep}")
    
    print("\n💡 Note: ESPN endpoints typically require specific IDs (game_id, team_id, etc.)")
    print("   Use per_endpoint_kwargs to provide these when testing.")
    
    # 6. Summary
    print_section("Summary")
    print(f"""
✅ Successfully explored sportsdataverse endpoints!

Next steps:
1. Try other sports: {', '.join(sports[:5])}
2. Test ESPN endpoints with specific IDs
3. Use fetch_many() to get multiple datasets at once
4. Use fetch_all() with filters to get comprehensive data

Example usage:
    # Get multiple datasets
    results = client.fetch_many(
        "nfl",
        endpoints=["load_nfl_teams", "load_nfl_injuries"],
        shared_kwargs={{"return_as_pandas": True}}
    )
    
    # Get all data for a season
    all_data = client.fetch_all(
        "nfl",
        shared_kwargs={{"seasons": [2024]}},
        exclude={{"espn_nfl_pbp"}}  # Skip slow endpoints
    )
""")
    
    # Restore original print
    builtins.print = original_print
    
    # Save report to file with domain-based organization
    # TODO: If generating multiple artifact types (CSV + MD + JSON), consider using
    # timestamped subfolders: Path('reports/endpoint_tests') / f"test_{timestamp}"
    # This groups related artifacts together (see scripts/analyze_pbp_odds_data_v4.py)
    domain_folder = Path('reports') / 'endpoint_tests'
    domain_folder.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"endpoint_test_report_{timestamp}.txt"
    output_path = domain_folder / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\n📄 Report saved to: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()