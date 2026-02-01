"""
QuantCup Unified CLI

Provides a single front door for all QuantCup ecosystem modules with
production-ready orchestration capabilities.
"""

from __future__ import annotations

import sys
from typing import Optional
from pathlib import Path

import typer
from . import __version__

# Ensure project root is in Python path for module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Context settings for pass-through commands
FORWARD_CTX = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "help_option_names": [],  # disable Typer's --help so we can forward it
}

app = typer.Typer(help="QuantCup unified CLI for sports analytics ecosystem")

def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"quantcup {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True,
        help="Show version and exit"
    )
):
    """QuantCup unified CLI for sports analytics ecosystem."""
    pass


# ---- Odds API ----------------------------------------------------------------
from odds_api.cli import app as odds_app
app.add_typer(odds_app, name="odds", help="Sports betting data pipeline")

# ---- Odds Scraper ------------------------------------------------------
from odds_scraper.cli import app as scraper_app
app.add_typer(scraper_app, name="odds_scraper", help="Odds scraper")

# ---- Weather Module ----------------------------------------------------------
# Unified weather namespace with forecasts and historical data
weather = typer.Typer(help="Weather data and forecasting for NFL games")
app.add_typer(weather, name="weather")

# Forecasts sub-command (NWS/NOAA forecasts for upcoming games)
from weather.forecasts.cli import app as forecasts_app
weather.add_typer(forecasts_app, name="forecast", help="NOAA/NWS weather forecasts for upcoming games")

# Historical sub-command (NCEI historical data and climatology)
from weather.historical.cli import app as historical_app
weather.add_typer(historical_app, name="historical", help="NCEI historical weather data and climatology")


# ---- NFLfastRv3 (Clean Architecture version) ------------------------------
try:
    from nflfastRv3.cli.main import main as nflfastrv3_main
    
    nflfastrv3 = typer.Typer(help="NFLfastRv3 - Clean Architecture pipeline (Preview)")
    app.add_typer(nflfastrv3, name="nflfastrv3")
    
    @nflfastrv3.command(context_settings=FORWARD_CTX)
    def data(ctx: typer.Context):
        """Data pipeline operations"""
        try:
            exit_code = nflfastrv3_main(["data"] + ctx.args)
            if exit_code != 0:
                raise typer.Exit(exit_code)
        except Exception as e:
            typer.echo(f"Error executing nflfastrv3 data command: {e}", err=True)
            raise typer.Exit(1)
    
    @nflfastrv3.command(context_settings=FORWARD_CTX)
    def ml(ctx: typer.Context):
        """Machine learning workflows"""
        try:
            exit_code = nflfastrv3_main(["ml"] + ctx.args)
            if exit_code != 0:
                raise typer.Exit(exit_code)
        except Exception as e:
            typer.echo(f"Error executing nflfastrv3 ml command: {e}", err=True)
            raise typer.Exit(1)
    
    @nflfastrv3.command(context_settings=FORWARD_CTX)
    def analytics(ctx: typer.Context):
        """Analytics and reporting"""
        try:
            exit_code = nflfastrv3_main(["analytics"] + ctx.args)
            if exit_code != 0:
                raise typer.Exit(exit_code)
        except Exception as e:
            typer.echo(f"Error executing nflfastrv3 analytics command: {e}", err=True)
            raise typer.Exit(1)

    @nflfastrv3.command(context_settings=FORWARD_CTX)
    def info(ctx: typer.Context):
        """Display system information"""
        try:
            exit_code = nflfastrv3_main(["info"] + ctx.args)
            if exit_code != 0:
                raise typer.Exit(exit_code)
        except Exception as e:
            typer.echo(f"Error executing nflfastrv3 info command: {e}", err=True)
            raise typer.Exit(1)

except ImportError as e:
    # Graceful degradation if nflfastRv3 is not ready
    nflfastrv3 = typer.Typer(help="NFLfastRv3 - Not available (incomplete implementation)")
    app.add_typer(nflfastrv3, name="nflfastrv3")
    
    @nflfastrv3.callback()
    def unavailable():
        typer.echo("❌ NFLfastRv3 is not yet fully implemented.", err=True)
        typer.echo("Please use 'quantcup nflfastr' instead.")
        typer.echo(f"Import error: {e}")
        raise typer.Exit(1)

# ---- Future expansion placeholders -------------------------------------------
# Uncomment and implement when these modules have CLIs

# @app.command(help="API Sports integration")
# def api_sports(ctx: typer.Context):
#     """Multi-sport data access via API Sports."""
#     raise typer.Exit(_forward("api_sports", ctx.args))

# @app.command(help="NFL data wrapper utilities")
# def nfl_wrapper(ctx: typer.Context):
#     """Enhanced NFL data access wrapper."""
#     raise typer.Exit(_forward("nfl_wrapper", ctx.args))

if __name__ == "__main__":
    app()
