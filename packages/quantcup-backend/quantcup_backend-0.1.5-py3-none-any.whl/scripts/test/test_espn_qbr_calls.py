"""
Test ESPN QBR R calls directly to identify latest year and package usage.

This script focuses on testing ESPN QBR R calls to understand:
- Latest available season/year in the data
- Which R package is being used (nflfastR vs nflreadr)
- Data structure and memory usage
- Performance characteristics

INVESTIGATION: ESPN QBR data sources
- espn_qbr_season: load_espn_qbr(seasons = TRUE, summary_type = "season")
- espn_qbr_wk: load_espn_qbr(seasons = TRUE, summary_type = "weekly")
"""

import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
import pandas as pd
import sys
import time
import os

def test_r_call(call_name, r_call, max_time_warning=60, expected_min_rows=0):
    """Test an R call and report results."""
    print(f"\n{'='*60}")
    print(f"Testing: {call_name}")
    print(f"R Call: {r_call}")
    print(f"Max time warning: {max_time_warning}s")
    print(f"{'='*60}")

    latest_year = None  # Initialize to avoid unbound variable

    try:
        start_time = time.time()

        # Load required R packages
        print("Loading R packages...")
        robjects.r('library(nflfastR)')
        robjects.r('library(nflreadr)')

        print(f"Executing R call: {r_call}")
        print("⚠️  Note: ESPN QBR data may take time to load. Press Ctrl+C to cancel if needed.")

        # Execute the R call
        result = robjects.r(r_call)

        elapsed_time = time.time() - start_time
        print(f"⏱️  Execution time: {elapsed_time:.2f}s")

        if elapsed_time > max_time_warning:
            print(f"⚠️  WARNING: Execution took longer than {max_time_warning}s")

        # Check if result has data
        if result is None:
            print("❌ ERROR: R call returned None")
            return 0, None

        # Try to get dimensions using R
        try:
            nrows = robjects.r('nrow')(result)[0]
            ncols = robjects.r('ncol')(result)[0]

            print(f"✓ SUCCESS: {nrows:,} rows, {ncols} columns")

            if nrows > 0:
                # Get column names
                colnames = list(robjects.r('colnames')(result))
                print(f"  Sample columns: {colnames[:5]}")

                # Check for season column and get latest year
                if 'season' in colnames:
                    seasons = list(robjects.r('unique')(result.rx2('season')))
                    seasons = [int(s) for s in seasons if str(s).isdigit()]
                    if seasons:
                        latest_year = max(seasons)
                        print(f"  Available seasons: {sorted(seasons)}")
                        print(f"  📅 Latest season: {latest_year}")

                # Check for year/week columns in weekly data
                if 'game_week' in colnames or 'week' in colnames:
                    week_col = 'game_week' if 'game_week' in colnames else 'week'
                    weeks = list(robjects.r('unique')(result.rx2(week_col)))
                    weeks = [int(w) for w in weeks if str(w).isdigit()]
                    if weeks:
                        print(f"  Available weeks: {sorted(weeks)}")

                # Memory usage estimate
                memory_mb = (nrows * ncols * 8) / (1024 * 1024)  # Rough estimate
                print(f"  Estimated memory: {memory_mb:.1f} MB")

                # Check which package was actually used
                package_info = check_package_usage(r_call)
                print(f"  📦 Package used: {package_info}")

            else:
                print("  ⚠️  WARNING: 0 rows returned")

            return int(nrows), latest_year

        except Exception as dim_error:
            # Fallback: try to convert to see if it's a dataframe
            try:
                # Enable conversion temporarily
                pandas2ri.activate()
                df = pandas2ri.rpy2py(result)
                pandas2ri.deactivate()

                rows = len(df)
                cols = len(df.columns) if hasattr(df, 'columns') else 0

                print(f"✓ SUCCESS (pandas): {rows:,} rows, {cols} columns")

                if rows > 0:
                    print(f"  Sample columns: {list(df.columns[:5])}")

                    if 'season' in df.columns:
                        seasons = df['season'].unique()
                        seasons = [int(s) for s in seasons if str(s).isdigit()]
                        if seasons:
                            latest_year = max(seasons)
                            print(f"  Available seasons: {sorted(seasons)}")
                            print(f"  📅 Latest season: {latest_year}")

                    if 'game_week' in df.columns or 'week' in df.columns:
                        week_col = 'game_week' if 'game_week' in df.columns else 'week'
                        weeks = df[week_col].unique()
                        weeks = [int(w) for w in weeks if str(w).isdigit()]
                        if weeks:
                            print(f"  Available weeks: {sorted(weeks)}")

                    # Memory usage estimate
                    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
                    print(f"  Actual memory: {memory_mb:.1f} MB")

                    # Check which package was actually used
                    package_info = check_package_usage(r_call)
                    print(f"  📦 Package used: {package_info}")

                else:
                    print("  ⚠️  WARNING: 0 rows returned")

                return rows, latest_year

            except Exception as pandas_error:
                print(f"❌ ERROR: Cannot determine dimensions - {dim_error}")
                print(f"❌ ERROR: Pandas conversion also failed - {pandas_error}")
                print(f"  Result type: {type(result)}")
                return 0, None

    except KeyboardInterrupt:
        print(f"❌ CANCELLED: User interrupted the R call")
        return -1, None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return 0, None

def check_package_usage(r_call):
    """Check which package the function likely comes from."""
    if 'load_espn_qbr' in r_call:
        # ESPN QBR functions are typically from nflreadr
        return "nflreadr (load_espn_qbr function)"
    elif 'nflfastR::' in r_call:
        return "nflfastR (explicit namespace)"
    elif 'nflreadr::' in r_call:
        return "nflreadr (explicit namespace)"
    else:
        return "Unknown (check function name)"

def main():
    """Test ESPN QBR R calls systematically."""

    print("🔍 ESPN QBR DATA TESTING")
    print("=" * 80)
    print("Testing ESPN QBR R calls to identify latest year and package usage")
    print("for espn_qbr_season and espn_qbr_wk data sources.")
    print("=" * 80)

    # Focus on ESPN QBR calls from data_sources.py
    test_calls = [
        # Test season summary first (smaller dataset)
        ("espn_qbr_season", 'load_espn_qbr(seasons = TRUE, summary_type = "season")', 60),

        # Test weekly summary (larger dataset)
        ("espn_qbr_wk", 'load_espn_qbr(seasons = TRUE, summary_type = "weekly")', 120),

        # Test specific recent years to verify data availability
        ("espn_qbr_season (2024 only)", 'load_espn_qbr(seasons = 2024, summary_type = "season")', 30),
        ("espn_qbr_wk (2024 only)", 'load_espn_qbr(seasons = 2024, summary_type = "weekly")', 60),

        # Test current season (may be empty if season not started)
        ("espn_qbr_season (2025 only)", 'load_espn_qbr(seasons = 2025, summary_type = "season")', 30),
        ("espn_qbr_wk (2025 only)", 'load_espn_qbr(seasons = 2025, summary_type = "weekly")', 30),
    ]

    results = {}

    for call_name, r_call, max_time in test_calls:
        print(f"\n🧪 Testing: {call_name}")
        rows, latest_year = test_r_call(call_name, r_call, max_time)
        results[call_name] = {'rows': rows, 'latest_year': latest_year}

        # Stop if user cancelled
        if rows == -1:
            print(f"\n⚠️  STOPPING: {call_name} was cancelled - remaining tests skipped")
            break

        # Add a small delay between tests
        time.sleep(2)

    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY OF RESULTS")
    print(f"{'='*80}")

    working_calls = []
    failing_calls = []
    cancelled_calls = []
    latest_years = []

    for call_name, result in results.items():
        rows = result['rows']
        latest_year = result['latest_year']

        if rows > 0:
            working_calls.append((call_name, rows, latest_year))
            year_info = f" (latest: {latest_year})" if latest_year else ""
            print(f"✅ {call_name}: {rows:,} rows{year_info}")
            if latest_year:
                latest_years.append(latest_year)
        elif rows == -1:
            cancelled_calls.append(call_name)
            print(f"🚫 {call_name}: CANCELLED")
        else:
            failing_calls.append(call_name)
            print(f"❌ {call_name}: 0 rows or error")

    print(f"\n📈 STATISTICS:")
    print(f"  Working calls: {len(working_calls)}")
    print(f"  Failing calls: {len(failing_calls)}")
    print(f"  Cancelled calls: {len(cancelled_calls)}")

    if latest_years:
        overall_latest_year = max(latest_years)
        print(f"  📅 Overall latest season: {overall_latest_year}")

    # Analysis and recommendations
    print(f"\n{'='*80}")
    print("💡 ANALYSIS & RECOMMENDATIONS")
    print(f"{'='*80}")

    if working_calls:
        print("✅ WORKING CALLS FOUND:")
        # Find the call with most data that works
        best_call = max(working_calls, key=lambda x: x[1])
        print(f"   Best option: {best_call[0]} ({best_call[1]:,} rows)")

        # Analyze latest year
        if latest_years:
            print(f"   📅 Latest available season: {max(latest_years)}")

        # Package analysis
        package_info = check_package_usage("load_espn_qbr")
        print(f"   📦 Package: {package_info}")

    if cancelled_calls:
        print("\n🚫 CANCELLED CALLS:")
        print("   These calls were interrupted:")
        for call in cancelled_calls:
            print(f"     - {call}")
        print("   💡 Likely too resource-intensive - consider incremental loading")

    if failing_calls:
        print("\n❌ FAILING CALLS:")
        print("   These calls returned no data:")
        for call in failing_calls:
            print(f"     - {call}")
        print("   💡 Possible causes: Data not available for that season/year")

    # Configuration recommendations
    print(f"\n🔧 CONFIGURATION RECOMMENDATIONS:")

    if working_calls:
        # Check if current season data exists
        current_season_tests = [r for r in results.items() if '2025' in r[0]]
        has_current_season = any(r['rows'] > 0 for _, r in current_season_tests)

        if has_current_season:
            print("1. ✅ FULL REFRESH STRATEGY RECOMMENDED:")
            print("   - Use: strategy='full_refresh'")
            print("   - Use: r_call='load_espn_qbr(seasons = TRUE, summary_type = \"...\")'")
            print("   - Current season data is available")
        else:
            print("1. ✅ INCREMENTAL STRATEGY RECOMMENDED:")
            print("   - Use: strategy='incremental'")
            print("   - Use: r_call='load_espn_qbr(file_type = \"parquet\")' (let pipeline add seasons)")
            print("   - Current season data not yet available")

        # Package confirmation
        print("2. 📦 PACKAGE CONFIRMATION:")
        print("   - Function: load_espn_qbr comes from nflreadr package")
        print("   - Ensure nflreadr is installed and up to date")

    if cancelled_calls and not working_calls:
        print("1. 🚨 MEMORY/PERFORMANCE ISSUE:")
        print("   - All calls cancelled - system cannot handle ESPN QBR data")
        print("   - Consider: Increase system memory")
        print("   - Consider: Use smaller date ranges")
        print("   - Consider: Process data in chunks")

    print(f"\n2. 🎯 IMMEDIATE NEXT STEPS:")
    if working_calls:
        if latest_years:
            latest = max(latest_years)
            print(f"   - Latest season available: {latest}")
            print("   - Verify this matches expectations for current NFL season")
        print("   - Test pipeline integration with working R calls")
        print("   - Monitor memory usage during full pipeline runs")
    else:
        print("   - Check R package versions (nflreadr)")
        print("   - Verify ESPN QBR data availability")
        print("   - Check network connectivity to ESPN data sources")

if __name__ == "__main__":
    main()