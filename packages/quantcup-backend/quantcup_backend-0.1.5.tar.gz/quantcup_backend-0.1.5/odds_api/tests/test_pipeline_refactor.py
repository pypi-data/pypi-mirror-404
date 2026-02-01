
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))

from odds_api.pipeline import run_pipeline

def test_pipeline():
    print("Testing Leagues Pipeline (Dry Run)...")
    try:
        rows = run_pipeline('leagues', dry_run=True, force=True)
        print(f"Success! Processed {rows} rows.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_pipeline()
