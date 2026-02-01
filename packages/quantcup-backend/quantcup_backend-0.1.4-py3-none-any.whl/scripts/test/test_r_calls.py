"""
Test R calls directly to identify issues with participation data source.

This script focuses on testing participation R calls to understand why
the pipeline process gets killed when loading participation data.

INVESTIGATION COMPLETED (2025-10-25):
- R calls work perfectly in isolation (433K rows in 4 seconds)
- Pipeline memory issues identified and optimizations implemented:
  * Removed Universal List-Column Sanitizer from R integration
  * Optimized data cleaning for large datasets (>200K rows)
  * Added efficient duplicate detection and schema matching
  * Added chunked processing for quality checks
- Use this script to verify R call functionality before pipeline changes
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
    
    try:
        start_time = time.time()
        
        # Load required R packages
        print("Loading R packages...")
        robjects.r('library(nflfastR)')
        robjects.r('library(nflreadr)')
        
        print(f"Executing R call: {r_call}")
        print("⚠️  Note: Large datasets may take several minutes. Press Ctrl+C to cancel if needed.")
        
        # Execute the R call
        result = robjects.r(r_call)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Execution time: {elapsed_time:.2f}s")
        
        if elapsed_time > max_time_warning:
            print(f"⚠️  WARNING: Execution took longer than {max_time_warning}s")
        
        # Check if result has data
        if result is None:
            print("❌ ERROR: R call returned None")
            return 0
            
        # Try to get dimensions using R
        try:
            nrows = robjects.r('nrow')(result)[0]
            ncols = robjects.r('ncol')(result)[0]
            
            print(f"✓ SUCCESS: {nrows:,} rows, {ncols} columns")
            
            if nrows > 0:
                # Get column names
                colnames = list(robjects.r('colnames')(result))
                print(f"  Sample columns: {colnames[:5]}")
                
                # Check for season column
                if 'season' in colnames:
                    seasons = list(robjects.r('unique')(result.rx2('season')))
                    print(f"  Available seasons: {sorted(seasons)[:10]}...")
                    
                # Memory usage estimate
                memory_mb = (nrows * ncols * 8) / (1024 * 1024)  # Rough estimate
                print(f"  Estimated memory: {memory_mb:.1f} MB")
            else:
                print("  ⚠️  WARNING: 0 rows returned")
                
            return int(nrows)
            
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
                        print(f"  Available seasons: {sorted(seasons)[:10]}...")
                        
                    # Memory usage estimate
                    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
                    print(f"  Actual memory: {memory_mb:.1f} MB")
                else:
                    print("  ⚠️  WARNING: 0 rows returned")
                    
                return rows
                
            except Exception as pandas_error:
                print(f"❌ ERROR: Cannot determine dimensions - {dim_error}")
                print(f"❌ ERROR: Pandas conversion also failed - {pandas_error}")
                print(f"  Result type: {type(result)}")
                return 0
    
    except KeyboardInterrupt:
        print(f"❌ CANCELLED: User interrupted the R call")
        return -1
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return 0

def main():
    """Test participation R calls systematically."""
    
    print("🔍 PARTICIPATION DATA TESTING")
    print("=" * 80)
    print("Testing different participation R calls to identify the correct configuration")
    print("and understand why the pipeline process gets killed.")
    print("=" * 80)
    
    # Focus on participation calls with different strategies
    test_calls = [
        # Start with safe, small tests
        ("participation (basic)", 'load_participation()', 30),
        ("participation (2024 only)", 'load_participation(seasons = 2024)', 60),
        ("participation (2023 only)", 'load_participation(seasons = 2023)', 60),
        
        # Test file types
        ("participation (2024 rds)", 'load_participation(seasons = 2024, file_type = "rds")', 60),
        ("participation (2024 parquet)", 'load_participation(seasons = 2024, file_type = "parquet")', 60),
        
        # Test recent years
        ("participation (2022 only)", 'load_participation(seasons = 2022)', 60),
        ("participation (2021 only)", 'load_participation(seasons = 2021)', 60),
        ("participation (2020 only)", 'load_participation(seasons = 2020)', 60),
        
        # Test multiple recent years (smaller sets)
        ("participation (2023-2024)", 'load_participation(seasons = c(2023, 2024))', 120),
        ("participation (2022-2024)", 'load_participation(seasons = c(2022, 2023, 2024))', 180),
        
        # Test the dangerous call last (with longer timeout)
        ("participation (ALL seasons)", 'load_participation(seasons = TRUE)', 300),
        ("participation (ALL parquet)", 'load_participation(seasons = TRUE, file_type = "parquet")', 300),
    ]
    
    results = {}
    
    for call_name, r_call, max_time in test_calls:
        print(f"\n🧪 Testing: {call_name}")
        rows = test_r_call(call_name, r_call, max_time)
        results[call_name] = rows
        
        # Stop if user cancelled or major error
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
    
    for call_name, rows in results.items():
        if rows > 0:
            working_calls.append((call_name, rows))
            print(f"✅ {call_name}: {rows:,} rows")
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
    
    # Analysis and recommendations
    print(f"\n{'='*80}")
    print("💡 ANALYSIS & RECOMMENDATIONS")
    print(f"{'='*80}")
    
    if working_calls:
        print("✅ WORKING CALLS FOUND:")
        # Find the call with most data that works
        best_call = max(working_calls, key=lambda x: x[1])
        print(f"   Best option: {best_call[0]} ({best_call[1]:,} rows)")
        
        # Analyze patterns
        working_years = []
        for call_name, rows in working_calls:
            if "2024" in call_name:
                working_years.append("2024")
            elif "2023" in call_name:
                working_years.append("2023")
            elif "2022" in call_name:
                working_years.append("2022")
        
        if working_years:
            print(f"   Working years: {set(working_years)}")
    
    if cancelled_calls:
        print("\n🚫 CANCELLED CALLS:")
        print("   These calls were interrupted:")
        for call in cancelled_calls:
            print(f"     - {call}")
        print("   💡 Likely too resource-intensive - use incremental loading")
    
    if failing_calls:
        print("\n❌ FAILING CALLS:")
        print("   These calls returned no data:")
        for call in failing_calls:
            print(f"     - {call}")
        print("   💡 Possible causes: Data not available, wrong parameters")
    
    # Configuration recommendations
    print(f"\n🔧 CONFIGURATION RECOMMENDATIONS:")
    
    if working_calls:
        # Find best working call
        best_call_name, best_rows = max(working_calls, key=lambda x: x[1])
        
        if "2024" in best_call_name or "2023" in best_call_name:
            print("1. ✅ INCREMENTAL STRATEGY RECOMMENDED:")
            print("   - Use: strategy='incremental'")
            print("   - Use: r_call='load_participation(file_type = \"parquet\")'")
            print("   - Let pipeline add current season automatically")
            print("   - This avoids memory issues with historical data")
        
        if "ALL" in best_call_name:
            print("1. ⚠️  FULL REFRESH POSSIBLE BUT RISKY:")
            print("   - Use: strategy='full_refresh'")
            print("   - Use: r_call='load_participation(seasons = TRUE, file_type = \"parquet\")'")
            print("   - WARNING: High memory usage, may need chunking")
    
    if cancelled_calls and not working_calls:
        print("1. 🚨 MEMORY/PERFORMANCE ISSUE:")
        print("   - All calls cancelled - system cannot handle participation data")
        print("   - Consider: Increase system memory")
        print("   - Consider: Use smaller date ranges")
        print("   - Consider: Process data in chunks")
    
    print(f"\n2. 🎯 IMMEDIATE NEXT STEPS:")
    if working_calls:
        best_call_name, _ = max(working_calls, key=lambda x: x[1])
        if "incremental" in best_call_name.lower() or any(year in best_call_name for year in ["2024", "2023", "2022"]):
            print("   - Update config to use incremental strategy")
            print("   - Test with single recent season first")
        else:
            print("   - Use the working call configuration")
            print("   - Monitor memory usage during pipeline runs")
    else:
        print("   - Check R package versions")
        print("   - Verify data availability")
        print("   - Consider alternative data sources")

if __name__ == "__main__":
    main()
