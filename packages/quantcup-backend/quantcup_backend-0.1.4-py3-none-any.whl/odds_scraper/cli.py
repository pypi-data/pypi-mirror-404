"""
Sportsbook CLI - Thin interface layer for Sportsbook NFL scraping pipeline.

Provides a modern Typer-based CLI for the Sportsbook NFL odds scraper,
following the same architectural pattern as odds_api/cli.py.
"""

from typing import List, Optional
import typer
from pathlib import Path

from commonv2 import (
    opt_verbose, opt_dry_run, opt_force,
    echo_success, echo_error, echo_info, echo_warning
)
from commonv2 import NFLfastRError, handle_cli_error

from odds_scraper.pipeline import SportsbookPipeline

app = typer.Typer(help="Sportsbook NFL scraper commands")


@app.command("scrape-nfl")
def scrape_nfl_cmd(
    markets: str = typer.Option(
        'spreads,totals,h2h',
        "--markets",
        help="Markets to scrape (Note: Sportsbook shows all markets, this parameter is for documentation compatibility)"
    ),
    force: bool = opt_force(),
    dry_run: bool = opt_dry_run(),
    write_csv: bool = typer.Option(False, "--csv", help="Export to CSV file"),
    verbose: bool = opt_verbose(),
):
    """
    Scrape live Sportsbook NFL odds.
    
    Fetches current odds for all live and upcoming NFL games from Sportsbook
    sportsbook. Uses browser-based scraping with anti-detection measures.
    
    Features:
        - Automatic cooldown interval enforcement (5 min default)
        - PID-based locking (prevents concurrent runs)
        - Bucket storage with 'odds_scraper' schema namespace
        - Optional CSV export
        - State persistence for tracking last run
    
    Examples:
        # Basic scrape (respects cooldown)
        quantcup odds_scraper scrape-nfl
        
        # Force immediate scrape (bypass cooldown)
        quantcup draft kings scrape-nfl --force
        
        # Scrape with CSV export
        quantcup odds_scraper scrape-nfl --csv
        
        # Dry run (simulate without storing)
        quantcup odds_scraper scrape-nfl --dry-run
    
    Output:
        - Bucket: odds_scraper/gamelines/
        - CSV (if --csv): data/odds_scraper/odds_YYYYMMDD_HHMMSS.csv
    
    Cooldown:
        Default 300s (5 min). Override with --force flag.
    """
    try:
        # Convert markets string to list (though Sportsbook ignores this)
        markets_list = [m.strip() for m in markets.split(',')]
        
        if dry_run:
            echo_info("DRY RUN - Would scrape Sportsbook NFL odds:")
            echo_info(f"  Markets: {', '.join(markets_list)} (Note: sportsbook shows all)")
            echo_info(f"  Output: Bucket (odds_scraper/gamelines)")
            if write_csv:
                echo_info(f"  CSV: data/odds_scraper/odds_YYYYMMDD_HHMMSS.csv")
            echo_info("  Cooldown: 5 min (bypass with --force)")
            echo_success("Dry run completed")
            return
        
        echo_info("Starting Sportsbook NFL odds scrape...")
        
        # Initialize pipeline
        pipeline = SportsbookPipeline()
        
        # Run pipeline
        rows = pipeline.run(
            markets=markets_list,
            force=force,
            dry_run=dry_run,
            write_csv=write_csv
        )
        
        if rows > 0:
            echo_success(f"✅ Processed {rows:,} records")
        elif rows == 0:
            # Could be cooldown or no data
            echo_warning("⚠️  No data returned (check cooldown status or game availability)")
            raise typer.Exit(1)
        else:
            echo_error("❌ Scraping failed")
            raise typer.Exit(1)
            
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=verbose)
        raise typer.Exit(exit_code)


@app.command("status")
def status_cmd():
    """
    Show Sportsbook pipeline status and configuration.
    
    Displays current configuration, last run information, and state
    from pipeline state files.
    
    Examples:
        quantcup odds_scraper status
    """
    try:
        from odds_scraper.config.settings import get_odds_scraper_settings
        from datetime import datetime
        import json
        
        echo_info("=" * 60)
        echo_info("ODDS SCRAPER NFL STATUS")
        echo_info("=" * 60)
        
        # Configuration
        settings = get_odds_scraper_settings()
        echo_info("\nConfiguration:")
        echo_info(f"  Update interval: {settings.update_interval}s ({settings.update_interval // 60} min)")
        echo_info(f"  Max retries: {settings.max_retries}")
        echo_info(f"  Browser headless: {settings.browser.headless}")
        echo_info(f"  User agents: {len(settings.browser.user_agents)}")
        echo_info(f"  Locations: {len(settings.browser.locations)}")
        echo_info(f"  Proxies configured: {len(settings.browser.proxies)}")
        
        # Pipeline state
        echo_info("\nPipeline State:")
        pipelines_dir = Path.cwd() / ".pipelines"
        state_file = pipelines_dir / "odds_scraper_nfl.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                last_run_timestamp = state.get('last_run', 0)
                if last_run_timestamp:
                    last_run_dt = datetime.fromtimestamp(last_run_timestamp)
                    last_run_str = last_run_dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    last_run_str = 'Never'
                
                status_value = state.get('status', 'Unknown')
                rows = state.get('last_rows', 0)
                
                echo_info(f"  Last Run: {last_run_str}")
                echo_info(f"  Status: {status_value}")
                if rows > 0:
                    echo_info(f"  Last Rows: {rows:,}")
                
                # Calculate time until next allowed run
                if last_run_timestamp:
                    import time
                    elapsed = time.time() - last_run_timestamp
                    remaining = max(0, settings.update_interval - elapsed)
                    
                    if remaining > 0:
                        mins = int(remaining // 60)
                        secs = int(remaining % 60)
                        echo_warning(f"  Cooldown: {mins}m {secs}s remaining")
                    else:
                        echo_success(f"  Cooldown: Ready to run")
            except Exception as e:
                echo_warning(f"  Cannot read state file: {e}")
        else:
            echo_info("  No state file found - never executed")
        
        # Lock status
        lock_file = pipelines_dir / "locks" / "odds_scraper_nfl.lock"
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    pid = f.read().strip()
                echo_warning(f"  Lock file exists (PID: {pid})")
                echo_warning("  Pipeline may be running or crashed")
            except Exception:
                pass
        
        # Storage info
        echo_info("\nStorage:")
        echo_info(f"  Bucket schema: odds_scraper")
        echo_info(f"  Bucket table: gamelines")
        echo_info(f"  CSV export: data/odds_scraper/")
        
        echo_info("=" * 60)
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=False)
        raise typer.Exit(exit_code)


@app.callback()
def main():
    """
    Sportsbook NFL scraper commands.
    
    Provides browser-based scraping of live NFL odds from Sportsbook sportsbook
    using the new clean architecture pipeline (Phase 2 implementation).
    
    COMMANDS:
    - scrape-nfl: Scrape live Sportsbook NFL odds
    - status: Show pipeline status and configuration
    
    ARCHITECTURE:
    This CLI follows the 3-Layer Clean Architecture pattern:
      Layer 1 (CLI): odds_scraper/cli.py - Command-line interface
      Layer 2 (Pipeline): odds_scraper/pipeline.py - Orchestration
      Layer 3 (Infrastructure): odds_scraper/core/* - Browser, Processor
    
    For more information, see odds_scraper/docs/REFACTORING_PLAN.md
    """
    pass


if __name__ == "__main__":
    app()
