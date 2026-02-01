"""
Quick endpoint tester - Run specific endpoints and see results quickly
"""

from sdv_wrapper import SportsDataVerseClient
from pathlib import Path
from datetime import datetime
import sys


def quick_test():
    """Quick test of a few endpoints to see what they return"""
    
    # Prepare report output
    report_lines = []
    
    def log(message):
        """Log to both console and report"""
        print(message)
        report_lines.append(message)
    
    client = SportsDataVerseClient(prefer_pandas=True, max_retries=2)
    
    log("=" * 80)
    log("🏈 QUICK ENDPOINT TEST REPORT")
    log("=" * 80)
    log(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("")
    
    # Test 1: List available sports
    log("1️⃣ Available sports:")
    sports = client.available_sports()
    log(f"   {sports}")
    log("")
    
    # Test 2: List NFL endpoints
    log("2️⃣ NFL endpoints:")
    nfl_endpoints = client.list_endpoints("nfl")
    log(f"   Found {len(nfl_endpoints)} endpoints")
    log(f"   First 10: {nfl_endpoints[:10]}")
    log("")
    
    # Test 3: Get NFL teams
    log("3️⃣ Testing load_nfl_teams:")
    try:
        teams = client.call("nfl", "load_nfl_teams")
        if hasattr(teams, 'shape'):
            log(f"   ✅ Got DataFrame with shape: {teams.shape}")
            log(f"   Columns: {list(teams.columns)}")
            log(f"\n   Sample data:")
            log(str(teams.head(3)))
        else:
            log(f"   ✅ Got {type(teams).__name__}: {teams}")
    except Exception as e:
        log(f"   ❌ Error: {e}")
    
    log("")
    log("=" * 80)
    log("✅ Quick test complete!")
    log("")
    log("To explore more, run: python sportsdataverse/test_endpoints.py")
    log("=" * 80)
    
    # Save report to file with domain-based organization
    # TODO: If generating multiple artifact types (CSV + MD + JSON), consider using
    # timestamped subfolders: Path('reports/quick_tests') / f"test_{timestamp}"
    # This groups related artifacts together (see scripts/analyze_pbp_odds_data_v4.py)
    domain_folder = Path('reports') / 'quick_tests'
    domain_folder.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"quick_test_report_{timestamp}.txt"
    output_path = domain_folder / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\n📄 Report saved to: {output_path}")


if __name__ == "__main__":
    quick_test()