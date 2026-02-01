"""
CLI interface for odds API operations.

Provides a modern Typer-based CLI that wraps the existing pipeline
functionality without changing the underlying business logic.
"""

from typing import List, Optional
import typer
import warnings
from pathlib import Path
from .core.types import SportKey, MarketKey, EventID

# Import shared CLI utilities
from commonv2 import (
    opt_verbose, opt_dry_run, opt_config, opt_workers, opt_season, opt_force, opt_no_cache,
    parse_seasons_or_none, echo_success, echo_error, echo_info, echo_warning, ExitCodes
)
from commonv2 import NFLfastRError, handle_cli_error

# Import existing pipeline components
from .config import SUPPORTED_SPORTS, MARKET_MAP, validate_sport_and_markets
from .pipeline import run_pipeline

app = typer.Typer(help="Sports betting odds and market data operations")
sync_app = typer.Typer(help="Data synchronization operations")
app.add_typer(sync_app, name="sync")


@app.command("list-sports")
def list_sports_cmd() -> None:
    """List available sports and their keys."""
    try:
        echo_info("Available sports:")
        for sport_key, sport_name in SUPPORTED_SPORTS.items():
            echo_info(f"  {sport_key}: {sport_name}")
        
        echo_info(f"\nTotal: {len(SUPPORTED_SPORTS)} sports available")
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=False)
        raise typer.Exit(exit_code)


@app.command("list-markets")
def list_markets_cmd() -> None:
    """List available market types and endpoints."""
    try:
        echo_info("Available markets and endpoints:")
        
        # Group by schema for better organization
        by_schema = {}
        for market_key, config in MARKET_MAP.items():
            schema = config.get('schema', 'unknown')
            if schema not in by_schema:
                by_schema[schema] = []
            by_schema[schema].append((market_key, config))
        
        for schema, items in by_schema.items():
            echo_info(f"\n{schema.upper()} Schema:")
            for market_key, config in items:
                description = config.get('description', 'No description')
                uses_quota = config.get('uses_quota', False)
                quota_str = " (uses quota)" if uses_quota else " (no quota)"
                echo_info(f"  {market_key}: {description}{quota_str}")
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=False)
        raise typer.Exit(exit_code)


# ============================================================================
# NEW SYNC COMMANDS (Phase 3)
# ============================================================================

@sync_app.command("ref")
def sync_ref_cmd(
    only: Optional[str] = typer.Option(
        None, "--only", help="Sync only specific reference data type (leagues|teams|schedule)"
    ),
    sport: SportKey = typer.Option("americanfootball_nfl", "--sport", help="Sport key (for teams/schedule)"),
    csv: bool = typer.Option(False, "--csv", help="Also write CSV files"),
    force: bool = opt_force(),
    verbose: bool = opt_verbose(),
    dry_run: bool = opt_dry_run(),
):
    """
    Sync reference data (leagues, teams, schedule).
    
    Consolidates leagues, teams, and schedule into a single command.
    Does not use API quota.
    
    Examples:
        # Sync all reference data for NFL
        quantcup odds sync ref
        
        # Sync only teams
        quantcup odds sync ref --only teams
        
        # Sync for specific sport
        quantcup odds sync ref --sport basketball_nba
    """
    try:
        # Validate --only parameter
        valid_only_values = ["leagues", "teams", "schedule"]
        if only is not None and only not in valid_only_values:
            raise NFLfastRError(
                f"Invalid --only value: {only}. Must be one of: {', '.join(valid_only_values)}"
            )
        
        # Validate sport if needed
        if only in ("teams", "schedule") or only is None:
            if sport not in SUPPORTED_SPORTS:
                raise NFLfastRError(f"Unknown sport: {sport}. Use 'list-sports' to see available options.")
        
        sport_name = SUPPORTED_SPORTS.get(sport, sport)
        
        # Determine what to sync
        sync_leagues = only == "leagues" or only is None
        sync_teams = only == "teams" or only is None
        sync_schedule = only == "schedule" or only is None
        
        if dry_run:
            echo_info("DRY RUN - Would sync reference data:")
            if sync_leagues:
                echo_info("  - Leagues")
            if sync_teams:
                echo_info(f"  - Teams ({sport_name})")
            if sync_schedule:
                echo_info(f"  - Schedule ({sport_name})")
            echo_info("  Quota usage: None")
            echo_success("Dry run completed")
            return
        
        total_rows = 0
        
        if sync_leagues:
            echo_info("Syncing leagues...")
            rows = run_pipeline('leagues', write_csv=csv)
            total_rows += rows
            echo_success(f"  ✓ Leagues: {rows:,} rows")
        
        if sync_teams:
            echo_info(f"Syncing teams for {sport_name}...")
            rows = run_pipeline('teams', sport_key=sport, write_csv=csv)
            total_rows += rows
            echo_success(f"  ✓ Teams: {rows:,} rows")
        
        if sync_schedule:
            echo_info(f"Syncing schedule for {sport_name}...")
            rows = run_pipeline('schedule', sport_key=sport, write_csv=csv)
            total_rows += rows
            echo_success(f"  ✓ Schedule: {rows:,} rows")
        
        echo_success(f"Reference data sync completed - {total_rows:,} total rows")
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=verbose)
        raise typer.Exit(exit_code)


@sync_app.command("odds")
def sync_odds_cmd(
    sport: SportKey = typer.Option("americanfootball_nfl", "--sport", help="Sport key"),
    markets: str = typer.Option("h2h,spreads,totals", "--markets", help="Comma-separated market types"),
    csv: bool = typer.Option(False, "--csv", help="Also write CSV files"),
    force: bool = opt_force(),
    verbose: bool = opt_verbose(),
    dry_run: bool = opt_dry_run(),
):
    """
    Sync live/upcoming odds data.
    
    Formerly the 'run' command. Fetches current odds for live and upcoming events.
    
    Examples:
        # Sync NFL odds (every 60s with cron)
        quantcup odds sync odds --sport americanfootball_nfl
        
        # Force immediate update (bypass cool-down)
        quantcup odds sync odds --force
    """
    try:
        markets_list = validate_sport_and_markets(sport, markets)
        sport_name = SUPPORTED_SPORTS[sport]
        
        if dry_run:
            echo_info("DRY RUN - Would sync odds data:")
            echo_info(f"  Sport: {sport} ({sport_name})")
            echo_info(f"  Markets: {', '.join(markets_list)}")
            echo_info(f"  Output: Database{' + CSV' if csv else ''}")
            echo_success("Dry run completed")
            return
        
        echo_info(f"Syncing {sport_name} odds for markets: {', '.join(markets_list)}")
        
        rows_processed = run_pipeline(
            'odds',
            write_csv=csv,
            sport_key=sport,
            markets=markets_list
        )
        
        echo_success(f"Odds sync completed - {rows_processed:,} rows processed")
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=verbose)
        raise typer.Exit(exit_code)


@sync_app.command("results")
def sync_results_cmd(
    sport: SportKey = typer.Option("americanfootball_nfl", "--sport", help="Sport key"),
    days_from: int = typer.Option(3, "--days-from", help="Number of days back to fetch results"),
    csv: bool = typer.Option(False, "--csv", help="Also write CSV files"),
    force: bool = opt_force(),
    verbose: bool = opt_verbose(),
    dry_run: bool = opt_dry_run(),
):
    """
    Sync results/scores for recent games.
    
    Uses /v4/sports/{sport}/scores endpoint for games within last 3 days.
    Cost: 1-2 credits (operational sync for model settlement).
    
    Examples:
        # Sync last 3 days of results
        quantcup odds sync results
        
        # Sync last week
        quantcup odds sync results --days-from 7
    """
    try:
        if sport not in SUPPORTED_SPORTS:
            raise NFLfastRError(f"Unknown sport: {sport}. Use 'list-sports' to see available options.")
        
        sport_name = SUPPORTED_SPORTS[sport]
        
        if dry_run:
            echo_info("DRY RUN - Would sync results data:")
            echo_info(f"  Sport: {sport} ({sport_name})")
            echo_info(f"  Days back: {days_from}")
            echo_warning("  Quota usage: Yes (1-2 credits)")
            echo_success("Dry run completed")
            return
        
        echo_info(f"Syncing results for {sport_name} (last {days_from} days)...")
        echo_warning("This operation uses API quota (1-2 credits)")
        rows_processed = run_pipeline('results', sport_key=sport, days_from=days_from, write_csv=csv)
        echo_success(f"Results sync completed - {rows_processed:,} rows processed")
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=verbose)
        raise typer.Exit(exit_code)


@sync_app.command("props")
def sync_props_cmd(
    event_id: EventID = typer.Argument(..., help="Event ID to fetch props for"),
    sport: SportKey = typer.Option("americanfootball_nfl", "--sport", help="Sport key"),
    markets: Optional[str] = typer.Option(None, "--markets", help="Comma-separated prop market types"),
    force: bool = opt_force(),
    verbose: bool = opt_verbose(),
    dry_run: bool = opt_dry_run(),
):
    """
    Sync props/event-specific odds data.
    
    Fetches player props and additional markets for a specific event.
    
    Examples:
        # Sync props for specific event
        quantcup odds sync props abc123def456
    """
    try:
        if sport not in SUPPORTED_SPORTS:
            raise NFLfastRError(f"Unknown sport: {sport}. Use 'list-sports' to see available options.")
        
        sport_name = SUPPORTED_SPORTS[sport]
        markets_list = markets.split(',') if markets else None
        
        if dry_run:
            echo_info("DRY RUN - Would sync props data:")
            echo_info(f"  Sport: {sport} ({sport_name})")
            echo_info(f"  Event ID: {event_id}")
            if markets_list:
                echo_info(f"  Markets: {', '.join(markets_list)}")
            echo_warning("  Quota usage: Yes")
            echo_success("Dry run completed")
            return
        
        echo_info(f"Syncing props for event {event_id} in {sport_name}...")
        echo_warning("This operation uses API quota")
        rows_processed = run_pipeline(
            'props',
            sport_key=sport,
            event_id=event_id,
            markets=markets_list,
            write_csv=csv
        )
        echo_success(f"Props sync completed - {rows_processed:,} rows processed")
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=verbose)
        raise typer.Exit(exit_code)



@app.command("backfill")
def backfill_cmd(
    # Season and week selection
    season_start: int = typer.Option(2023, "--season-start", help="Start season year"),
    season_end: Optional[int] = typer.Option(None, "--season-end", help="End season year (defaults to season-start)"),
    week_start: int = typer.Option(1, "--week-start", help="Start week (1-22)"),
    week_end: int = typer.Option(22, "--week-end", help="End week (1-22)"),
    
    # Sport and market selection
    sport: SportKey = typer.Option("americanfootball_nfl", "--sport", help="Sport key"),
    markets: str = typer.Option("h2h,spreads,totals", "--markets", help="Comma-separated market types"),
    
    # Event filtering (for testing)
    event_id: Optional[str] = typer.Option(None, "--event-id", help="Process only this specific event ID (for testing)"),
    
    # Resume and confirmation
    resume: bool = typer.Option(False, "--resume", help="Resume from saved state (.backfill_state)"),
    confirm: bool = typer.Option(False, "--confirm", help="Bypass high-cost confirmation (>5,000 credits)"),
    
    # Output options (mutually exclusive)
    bucket: bool = typer.Option(False, "--bucket", help="Write to bucket storage only"),
    csv: bool = typer.Option(False, "--csv", help="Write CSV files only"),
    
    # Standard options
    verbose: bool = opt_verbose(),
    dry_run: bool = opt_dry_run(),
):
    """
    Backfill historical odds data using event-driven snapshots.
    
    This command uses the new backfill orchestrator with state persistence,
    allowing resumable multi-season backfills with quota-aware execution.
    
    Examples:
        # Backfill to bucket (default behavior)
        quantcup odds backfill --season-start 2023 --week-end 18
        
        # Backfill to bucket (explicit)
        quantcup odds backfill --season-start 2023 --bucket
        
        # Backfill to CSV only
        quantcup odds backfill --season-start 2023 --csv
        
        # Test with single event (saves quota)
        quantcup odds backfill --season-start 2025 --week-start 4 --event-id abc123 --csv
        
        # Resume interrupted backfill
        quantcup odds backfill --resume
        
        # Backfill with high-cost bypass
        quantcup odds backfill --season-start 2020 --season-end 2023 --confirm
    """
    try:
        from .config import get_settings
        from .etl.backfill import BackfillOrchestrator
        from .utils.schedulers.nfl import NFLScheduler
        
        # Validate sport
        if sport not in SUPPORTED_SPORTS:
            raise NFLfastRError(f"Unknown sport: {sport}. Use 'list-sports' to see available options.")
        
        sport_name = SUPPORTED_SPORTS[sport]
        
        # Validate markets
        markets_list = validate_sport_and_markets(sport, markets)
        
        # Set season_end to season_start if not provided
        if season_end is None:
            season_end = season_start
        
        # Validate ranges
        if season_start > season_end:
            raise NFLfastRError(f"season-start ({season_start}) cannot be greater than season-end ({season_end})")
        
        if week_start < 1 or week_start > 22:
            raise NFLfastRError(f"week-start must be between 1 and 22 (got {week_start})")
        
        if week_end < 1 or week_end > 22:
            raise NFLfastRError(f"week-end must be between 1 and 22 (got {week_end})")
        
        if week_start > week_end:
            raise NFLfastRError(f"week-start ({week_start}) cannot be greater than week-end ({week_end})")
        
        # Handle mutually exclusive output flags with default to bucket
        if bucket and csv:
            raise NFLfastRError("Cannot specify both --bucket and --csv. Choose one output destination.")
        
        # Default to bucket if neither is specified
        if not bucket and not csv:
            bucket = True
            echo_info("No output specified, defaulting to --bucket")
        
        if dry_run:
            echo_info("DRY RUN - Would backfill historical odds:")
            echo_info(f"  Sport: {sport} ({sport_name})")
            echo_info(f"  Seasons: {season_start} to {season_end}")
            echo_info(f"  Weeks: {week_start} to {week_end}")
            echo_info(f"  Markets: {', '.join(markets_list)}")
            
            if event_id:
                echo_info(f"  Event Filter: {event_id} (single event only)")
            
            # Output destination (mutually exclusive, only one will be true)
            if bucket:
                echo_info("  Output: Bucket")
            elif csv:
                echo_info("  Output: CSV")
            
            if resume:
                echo_info("  Mode: Resume from .backfill_state")
            else:
                echo_info("  Mode: Fresh start")
            echo_warning("  This operation uses significant API quota")
            echo_success("Dry run completed")
            return
        
        echo_info(f"Starting historical odds backfill for {sport_name}...")
        echo_info(f"  Seasons: {season_start} to {season_end}")
        echo_info(f"  Weeks: {week_start} to {week_end}")
        echo_info(f"  Markets: {', '.join(markets_list)}")
        if event_id:
            echo_info(f"  Event Filter: {event_id} (single event only)")
        echo_warning("This operation uses significant API quota")
        
        # Get config and update for backfill
        cfg = get_settings().backfill
        cfg.season_range = (season_start, season_end)
        cfg.week_range = (week_start, week_end)
        cfg.sport_key = sport
        cfg.markets = markets_list
        cfg.save_to_csv = csv
        cfg.save_to_bucket = bucket
        cfg.event_id_filter = event_id  # Add event filter for testing
        
        # Initialize scheduler and orchestrator
        scheduler = NFLScheduler(cfg, save_to_bucket=bucket)
        orchestrator = BackfillOrchestrator(cfg, scheduler)
        
        # Run backfill
        orchestrator.run(resume=resume, confirm_cost=confirm)
        
        echo_success("Backfill completed successfully")
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=verbose)
        raise typer.Exit(exit_code)


@app.command("pipeline")
def pipeline_cmd(
    sport: SportKey = typer.Option("americanfootball_nfl", "--sport", help="Sport key"),
    all_data: bool = typer.Option(False, "--all", help="Load all data types (odds + reference data)"),
    reference_only: bool = typer.Option(False, "--reference-only", help="Load only reference data (no quota)"),
    
    # Individual flags for reference data
    leagues: bool = typer.Option(False, "--leagues", help="Include leagues data"),
    teams: bool = typer.Option(False, "--teams", help="Include teams data"),
    schedule: bool = typer.Option(False, "--schedule", help="Include schedule data"),
    results: bool = typer.Option(False, "--results", help="Include results data (uses quota)"),
    
    # Options for quota-using operations
    markets: str = typer.Option("h2h,spreads,totals", "--markets", help="Markets for odds data"),
    days_from: int = typer.Option(3, "--days-from", help="Days back for results"),
    csv: bool = typer.Option(False, "--csv", help="Also write CSV files for odds"),
    
    # Standard options
    verbose: bool = opt_verbose(),
    dry_run: bool = opt_dry_run(),
    config: Optional[str] = opt_config(),
):
    """
    Run bulk data loading operations.
    
    Examples:
        # Load all data for NFL
        quantcup odds pipeline --sport americanfootball_nfl --all
        
        # Load only reference data (no quota usage)
        quantcup odds pipeline --sport americanfootball_nfl --reference-only
        
        # Load specific data types
        quantcup odds pipeline --sport americanfootball_nfl --leagues --teams --schedule
    """
    try:
        # Validate sport
        if sport not in SUPPORTED_SPORTS:
            raise NFLfastRError(f"Unknown sport: {sport}. Use 'list-sports' to see available options.")
        
        sport_name = SUPPORTED_SPORTS[sport]
        
        # Validate mutually exclusive options
        if all_data and reference_only:
            raise NFLfastRError("Cannot specify both --all and --reference-only")
        
        # Determine what to load
        load_plan = []
        quota_operations = []
        
        if reference_only:
            # Default to all reference data if none specified
            if not any([leagues, teams, schedule]):
                leagues = teams = schedule = True
            
            if leagues:
                load_plan.append(("leagues", "Load leagues data", False))
            if teams:
                load_plan.append(("teams", f"Load teams data for {sport_name}", False))
            if schedule:
                load_plan.append(("schedule", f"Load schedule data for {sport_name}", False))
                
        elif all_data:
            # Load everything
            load_plan = [
                ("leagues", "Load leagues data", False),
                ("teams", f"Load teams data for {sport_name}", False),
                ("schedule", f"Load schedule data for {sport_name}", False),
                ("results", f"Load results data for {sport_name}", True),
                ("odds", f"Load odds data for {sport_name}", True),
            ]
            quota_operations = ["results", "odds"]
            
        else:
            # Load based on individual flags
            if leagues:
                load_plan.append(("leagues", "Load leagues data", False))
            if teams:
                load_plan.append(("teams", f"Load teams data for {sport_name}", False))
            if schedule:
                load_plan.append(("schedule", f"Load schedule data for {sport_name}", False))
            if results:
                load_plan.append(("results", f"Load results data for {sport_name}", True))
                quota_operations.append("results")
            
            # Default to odds if no specific operations requested
            if not load_plan:
                markets_list = validate_sport_and_markets(sport, markets)
                load_plan.append(("odds", f"Load odds data for {sport_name}", True))
                quota_operations.append("odds")
        
        if not load_plan:
            raise NFLfastRError("No operations specified. Use --all, --reference-only, or specific flags.")
        
        if dry_run:
            echo_info("DRY RUN - Would execute pipeline:")
            echo_info(f"  Sport: {sport} ({sport_name})")
            for operation, description, uses_quota in load_plan:
                quota_str = " (uses quota)" if uses_quota else " (no quota)"
                echo_info(f"  - {description}{quota_str}")
            if quota_operations:
                echo_warning(f"  Quota-using operations: {', '.join(quota_operations)}")
            echo_success("Dry run completed")
            return
        
        # Execute the pipeline
        echo_info(f"Starting pipeline for {sport_name}...")
        if quota_operations:
            echo_warning(f"This pipeline includes quota-using operations: {', '.join(quota_operations)}")
        
        total_rows = 0
        
        for operation, description, uses_quota in load_plan:
            echo_info(f"\n▶ {description}...")
            
            try:
                if operation == "leagues":
                    rows = run_pipeline('leagues')
                elif operation == "teams":
                    rows = run_pipeline('teams', sport_key=sport)
                elif operation == "schedule":
                    rows = run_pipeline('schedule', sport_key=sport)
                elif operation == "results":
                    rows = run_pipeline('results', sport_key=sport, days_from=days_from)
                elif operation == "odds":
                    markets_list = validate_sport_and_markets(sport, markets)
                    rows = run_pipeline(
                        'odds',
                        sport_key=sport,
                        markets=markets_list
                    )
                else:
                    raise NFLfastRError(f"Unknown operation: {operation}")
                
                total_rows += rows
                echo_success(f"✓ {operation}: {rows:,} rows processed")
                
            except Exception as e:
                echo_error(f"✗ {operation} failed: {e}")
                raise
        
        echo_success(f"\nPipeline completed successfully - {total_rows:,} total rows processed")
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=verbose)
        raise typer.Exit(exit_code)


@app.command("status")
def status_cmd():
    """
    Show odds API status, quota, and pipeline state.
    
    Displays current configuration, quota usage, and last run information
    from pipeline state files.
    """
    try:
        from .config import get_settings
        from datetime import datetime, timezone
        import json
        
        echo_info("=" * 60)
        echo_info("ODDS API STATUS")
        echo_info("=" * 60)
        
        # Configuration
        echo_info("\nConfiguration:")
        echo_info(f"  Supported sports: {len(SUPPORTED_SPORTS)}")
        echo_info(f"  Available markets: {len(MARKET_MAP)}")
        
        # Show quota vs non-quota operations
        quota_ops = [k for k, v in MARKET_MAP.items() if v.get('uses_quota', False)]
        no_quota_ops = [k for k, v in MARKET_MAP.items() if not v.get('uses_quota', False)]
        
        echo_info(f"  Quota operations: {len(quota_ops)}")
        echo_info(f"  No-quota operations: {len(no_quota_ops)}")
        
        # Quota tracking
        try:
            from .core import setup_quota_tracker
            settings = get_settings()
            tracker = setup_quota_tracker(settings)
            if tracker:
                echo_info(f"\nQuota Status:")
                echo_info(f"  Requests today: {tracker.requests_today}")
                echo_info(f"  Estimated remaining: {max(0, 500 - tracker.requests_today)}")
        except Exception:
            echo_info(f"\nQuota Status: Tracking unavailable")
        
        # Pipeline state
        echo_info("\nPipeline State:")
        pipelines_dir = Path.cwd() / ".pipelines"
        if pipelines_dir.exists():
            state_files = list(pipelines_dir.glob("*.json"))
            if state_files:
                for state_file in sorted(state_files):
                    try:
                        with open(state_file, 'r') as f:
                            state = json.load(f)
                        
                        pipeline_name = state_file.stem
                        last_run = state.get('last_run', 'Never')
                        status = state.get('status', 'Unknown')
                        rows = state.get('rows_processed', 0)
                        
                        echo_info(f"  {pipeline_name}:")
                        echo_info(f"    Last Run: {last_run}")
                        echo_info(f"    Status: {status}")
                        if rows > 0:
                            echo_info(f"    Rows: {rows:,}")
                    except Exception:
                        pass
            else:
                echo_info("  No pipeline state files found")
        else:
            echo_info("  No pipeline state directory (.pipelines/)")
        
        # Backfill state
        backfill_state = Path.cwd() / ".backfill_state"
        if backfill_state.exists():
            try:
                with open(backfill_state, 'r') as f:
                    state = json.load(f)
                echo_info("\nBackfill State:")
                echo_info(f"  Season: {state.get('season', 'N/A')}")
                echo_info(f"  Last Game Index: {state.get('last_game_idx', 0)}")
                echo_info(f"  Games Processed: {len(state.get('processed_game_ids', []))}")
                echo_info(f"  Quota Consumed: {state.get('quota_consumed', 0):,} credits")
                echo_info(f"  Started: {state.get('started_at', 'N/A')}")
                echo_info("\n  Use 'backfill --resume' to continue")
            except Exception as e:
                echo_warning(f"\nBackfill state exists but cannot be read: {e}")
        
        echo_info("=" * 60)
        
    except Exception as e:
        exit_code = handle_cli_error(e, verbose=False)
        raise typer.Exit(exit_code)


@app.callback()
def main():
    """
    Sports betting odds and market data operations.
    
    SYNC COMMANDS (Phase 3):
    - sync ref: Sync reference data (leagues, teams, schedule)
    - sync odds: Sync live/upcoming odds
    - sync results: Sync recent game results
    - sync props: Sync event-specific props
    
    BACKFILL COMMAND:
    - backfill: Backfill historical odds with resume support
    
    UTILITY COMMANDS:
    - list-sports: Show available sports
    - list-markets: Show available markets and endpoints
    - pipeline: Bulk data loading operations
    - status: Show API status, quota, and pipeline state
    """
    pass


if __name__ == "__main__":
    app()
