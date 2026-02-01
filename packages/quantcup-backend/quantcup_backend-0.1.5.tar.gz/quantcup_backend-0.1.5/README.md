# QuantCup Backend: Comprehensive Sports Analytics Ecosystem

A production-ready, modular sports analytics platform built with the "skinny-but-useful" philosophy. Combines NFL data analytics, machine learning, and sports betting data into a unified ecosystem for research, modeling, and production applications.

## 🎯 Overview

QuantCup Backend is a comprehensive sports analytics ecosystem that transforms raw sports data into sophisticated insights through a multi-stage pipeline. Built for both researchers and production environments, it provides enterprise-grade reliability with minimal complexity.

**Core Philosophy**: "Skinny-but-useful" - Maximum functionality with minimal dependencies and complexity.

**Key Capabilities:**
- ✅ **Complete NFL Analytics Pipeline** - Raw data → Analytics → Features → ML Predictions
- ✅ **Sports Betting Integration** - Real-time odds, lines, and market analysis
- ✅ **NFL Data API Wrapper** - 25+ functions for comprehensive NFL data access
- ✅ **Shared Infrastructure** - Unified database, logging, and configuration management
- ✅ **Machine Learning Ready** - XGBoost models with sophisticated feature engineering
- ✅ **Production Grade** - Robust error handling, logging, and scalability
- ✅ **Modular Design** - Use individual components or the complete system

## 🏗️ System Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           QuantCup Backend Ecosystem                              │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │NFL Data  │  │Odds API  │  │CommonV2  │  │   CFD    │  │ Weather  │  │API     │ │
│  │Wrapper   │  │Pipeline  │  │Infra     │  │College   │  │ Module   │  │Sports  │ │
│  │          │  │          │  │          │  │Football  │  │          │  │(Part.) │ │
│  │25+ NFL   │  │Real-time │  │Database  │  │40+ API   │  │Forecast  │  │Future  │ │
│  │Functions │  │Betting   │  │Logging   │  │Endpoints │  │+Historic │  │Expand  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│       │              │              │            │              │          │      │ 
│       └──────────────┼──────────────┼────────────┼──────────────┼──────────┘      │
│                      │              │            │              │                 │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │                               NFLfastRv3 Pipeline                            │ │
│  │                                                                              │ │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐ │ │
│  │  │   Loading   │ ─▶ │  Warehouse   │ ─▶ │  Features   │ ─▶ │     ML      │ │ │
│  │  │             │     │             │     │             │     │             │ │ │
│  │  │ Raw NFL     │     │ Analytics   │     │ Feature     │     │ Predictive  │ │ │
│  │  │ Data        │     │ Schema      │     │ Engineering │     │ Models      │ │ │
│  │  │ (24 tables) │     │ (8 tables)  │     │ (6 sets)    │     │ (Ensemble)  │ │ │
│  │  └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐       │
│  │                         Data Storage Layer                             │       │
│  │                                                                        │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │       │
│  │  │ PostgreSQL  │  │ PostgreSQL  │  │ PostgreSQL  │  │   Shared    │    │       │
│  │  │             │  │             │  │             │  │             │    │       │
│  │  │ nflreadr    │  │ odds_api    │  │ quantcup    │  │ Utilities   │    │       │
│  │  │ Database    │  │ Database    │  │ Database    │  │ & Logging   │    │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │       │
│  └────────────────────────────────────────────────────────────────────────┘       │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Raw Sources → Extraction → Transformation → Analytics → Features → Predictions
     ↓             ↓            ↓            ↓          ↓           ↓
NFL Data API   nfl_wrapper   Warehouse   Analytics   Features    ML Models
Odds API    →  odds_api   →  Schema   →  Tables   →  Engine   →  XGBoost
Team Data      commonv2      Facts       Dims        Rolling     Outcomes
```

## 🎯 Unified CLI

**NEW**: QuantCup Backend now provides a unified command-line interface that serves as a single entry point for the entire ecosystem.

### Command Structure

```bash
# Unified CLI entry point
python -m quantcup [module] [command] [options]

# NFLfastRv3 Analytics Pipeline
python -m quantcup nflfastrv3 data [args]      # Data pipeline operations
python -m quantcup nflfastrv3 ml [args]        # Machine learning workflows
python -m quantcup nflfastrv3 analytics [args] # Analytics and reporting
python -m quantcup nflfastrv3 system [args]    # System utilities and validation

# Sports Betting Data
python -m quantcup odds [args]                 # Odds API pipeline

# Weather Data
python -m quantcup weather forecast [args]     # NOAA NWS forecasts (7-day outlook)
python -m quantcup weather historical [args]   # NCEI historical & climatology

# Decision Dossier & Weekly Slate Orchestration
python -m quantcup slate build [args]         # Build weekly slate (canonical DecisionInputs)
python -m quantcup dossier addons [args]       # Generate DecisionAddOns (ODR augmentation)
python -m quantcup picks run [args]            # Run analyst picker (weekly mode)
python -m quantcup slates generate [args]      # Complete weekly workflow

# Future expansion
# python -m quantcup api-sports [args]         # Multi-sport data (in development)
```

## Decision Dossier + ODR Integration

### Overview

QuantCup Backend orchestrates **weekly slate generation**—the process of producing betting picks for all games in a given week across multiple analytical perspectives. This integrates canonical data from backend systems with fresh context from the [`open_deep_research`](https://github.com/quantcup/open_deep_research) ODR module.

**North Star Product**: [`WeeklySlateOutput`](https://github.com/quantcup/open_deep_research/blob/main/docs/SPORTS_BETTING_AGENTS_v2.md#weeklyslateoutput-schema) - One object per analyst per week containing picks (or passes) for every scheduled game, plus weekly posture and portfolio summary.

### Architecture

```
quantcup_backend (Weekly Orchestrator)
  ↓
1. Load Week Slate
   - Query schedule for all games in week
   - Generate DecisionInputs (canonical data per game)
  ↓
2. Call ODR per Game (temporal-aware)
   - open_deep_research ODR module (external)
   - DecisionAddOns (fresh context since as_of_utc)
  ↓
3. Merge into DecisionDossiers
   - Combine DecisionInputs + DecisionAddOns
   - Validate schema completeness
  ↓
4. Picker Produces WeeklySlateOutput
   - ONE call per analyst per week
   - Analyzes all games through 4 perspectives
  ↓
5. Store and Expose
   - weekly_slates table
   - API endpoints for UI consumption
```

### Data Contracts

**DecisionInputs** (produced by quantcup_backend - canonical sources):
- Model predictions: [`nflfastRv3.features.ml_pipeline`](nflfastRv3/features/ml_pipeline/)
- Market data: [`odds_api.etl.extract.api`](odds_api/etl/extract/api.py)
- Injury data: [`nflfastRv3.features.data_pipeline.warehouse`](nflfastRv3/features/data_pipeline/warehouse.py)
- Weather: [`noaa/*`](noaa/)

**DecisionAddOns** (produced by open_deep_research ODR module - augment only):
- Fresh context since `as_of_utc` (coach quotes, lineup changes, risk flags)
- Temporal-aware search budgets (≤3d: 10-15 searches, 6+d: 3-5 searches)
- Strict source validation (official sources only for injury data)

**WeeklySlateOutput** (produced by quantcup_backend analyst picker):
- One object per analyst per week
- All games: picks (team/market/line/confidence/units) or passes
- Weekly posture + portfolio summary

### Storage Schema

```sql
-- Database: quantcup (production) / local dev databases

-- Canonical baseline data (per game)
CREATE TABLE decision_inputs (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    season INT NOT NULL,
    week INT NOT NULL,
    as_of_utc TIMESTAMP NOT NULL,
    payload JSONB NOT NULL,  -- DecisionInputs JSON
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(game_id, as_of_utc)
);

-- Fresh research context (per game, per run)
CREATE TABLE decision_addons (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    run_id UUID NOT NULL,
    generated_at_utc TIMESTAMP NOT NULL,
    payload JSONB NOT NULL,  -- DecisionAddOns JSON
    fallback_mode BOOLEAN DEFAULT FALSE,
    odr_cost_usd DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Merged dossiers (per game)
CREATE TABLE decision_dossiers (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    dossier_version VARCHAR(20) NOT NULL,
    payload JSONB NOT NULL,  -- DecisionDossier JSON
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(game_id, dossier_version)
);

-- Weekly slate outputs (per analyst per week)
CREATE TABLE weekly_slates (
    id SERIAL PRIMARY KEY,
    week_id VARCHAR(20) NOT NULL,  -- e.g., "2026_W3"
    season INT NOT NULL,
    week INT NOT NULL,
    analyst_id VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,  -- WeeklySlateOutput JSON
    generated_at_utc TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(week_id, analyst_id)
);

-- Individual picks (denormalized for query efficiency)
CREATE TABLE analyst_picks (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    week_id VARCHAR(20) NOT NULL,
    analyst_id VARCHAR(50) NOT NULL,
    decision VARCHAR(10) NOT NULL,  -- "PICK" or "PASS"
    pick_data JSONB,  -- Pick details if decision="PICK"
    pass_reason TEXT,  -- Reason if decision="PASS"
    created_at TIMESTAMP DEFAULT NOW()
);
```

### CLI Commands

Following the unified CLI pattern:

```bash
# Build weekly slate (canonical DecisionInputs for all games)
python -m quantcup slate build --season 2026 --week 3

# Generate DecisionAddOns (ODR augmentation, temporal-aware)
python -m quantcup dossier addons --season 2026 --week 3 --window auto

# Merge inputs + addons into dossiers
python -m quantcup dossier merge --season 2026 --week 3

# Run analyst picker (weekly mode: ONE call per analyst)
python -m quantcup picks run --season 2026 --week 3 --analyst conservative --mode weekly

# Complete weekly workflow (all steps, all analysts)
python -m quantcup slates generate --season 2026 --week 3 --all-analysts

# Query slates
python -m quantcup slates query --season 2026 --week 3 --analyst holistic
python -m quantcup slates query --season 2026 --week 3 --format summary
```

### Integration with open_deep_research

**Boundary**: `quantcup_backend` owns weekly orchestration. `open_deep_research` is a per-game research tool.

**open_deep_research (ODR Module)**:
- **Scope**: Per-game research augmentation (DecisionInputs → DecisionAddOns)
- **Called by**: `quantcup_backend` for each game (bounded by temporal window)
- **Returns**: DecisionAddOns with `fallback_mode` flag if degraded

**quantcup_backend (Orchestrator)**:
- **Scope**: Weekly orchestration, canonical data, analyst picker, WeeklySlateOutput
- **Calls**: `open_deep_research` ODR module per game as needed
- **Storage**: Persists all data (inputs, addons, dossiers, slates)

### Cost Model

**Per Game Costs**:
- **DecisionInputs**: $0 (cached from backend systems)
- **ODR DecisionAddOns**: $0.20-0.35 per game (6-10 Tavily searches)
- **Picker decision**: $0.03-0.05 per game (LLM call for single game analysis)

**Per Week Per Analyst** (15 games typical):
- ODR total: 15 games × $0.20-0.35 = $3.00-5.25
- Picker total: 15 games × $0.03-0.05 = $0.45-0.75
- Aggregation: negligible (simple data collection)
- **Total per Week per Analyst**: ~$3.50-6.00

**Comparison**: vs $8.50 with deprecated multi-agent pattern (~60% cost reduction)

### Fail-Closed Behavior

If ODR fails or returns degraded output:
```python
if decision_addons.fallback_mode:
    # Picker adjustments:
    pick.confidence -= 0.15  # Reduce confidence
    pick.bet_size_units = min(pick.bet_size_units, 0.5)  # Cap units
    pick.risk_flags.append("Limited fresh context available")
    
    # Consider PASS if confidence too low:
    if pick.confidence < 0.55:
        decision = "PASS"
```

### Documentation

- **[Weekly Slate Workflow](https://github.com/quantcup/open_deep_research/blob/main/docs/WEEKLY_SLATE_WORKFLOW.md)** - Complete orchestration guide
- **[Sports Betting Agents v2](https://github.com/quantcup/open_deep_research/blob/main/docs/SPORTS_BETTING_AGENTS_v2.md)** - Data contracts and ODR responsibilities
- **[Analyst Perspectives](https://github.com/quantcup/open_deep_research/blob/main/docs/ANALYST_PERSPECTIVES.md)** - Four analytical lenses framework

---


### NFLfastRv3 Command Examples

The NFLfastRv3 module provides comprehensive data pipeline, ML, and analytics capabilities:

```bash
# Data Pipeline Operations
python -m quantcup nflfastrv3 data process                    # Process all data sources
python -m quantcup nflfastrv3 data process --group nfl_data  # Process specific groups
python -m quantcup nflfastrv3 data validate                   # Validate data quality
python -m quantcup nflfastrv3 data warehouse                  # Build data warehouse

# Machine Learning Workflows
python -m quantcup nflfastrv3 ml features --seasons 2024       # Engineer features
python -m quantcup nflfastrv3 ml train --model xgboost        # Train ML models
python -m quantcup nflfastrv3 ml predict                      # Generate predictions

# Analytics and Reporting
python -m quantcup nflfastrv3 analytics exploratory --season 2024  # Exploratory analysis
python -m quantcup nflfastrv3 analytics feature-analysis           # Feature analysis
python -m quantcup nflfastrv3 analytics team-performance --team KC # Team analysis

# System Utilities
python -m quantcup nflfastrv3 system validate --component all # Validate architecture
python -m quantcup nflfastrv3 system info --detailed          # System information
```

### Key Features

✅ **Clean Architecture**: Maximum 3-layer depth with dependency injection
✅ **Bucket-First Storage**: S3/Sevalla object storage with PostgreSQL fallback
✅ **Environment-Aware**: Automatic routing between local and production databases
✅ **Data Quality**: Built-in validation and quality checks
✅ **Streaming Operations**: Memory-efficient processing of large datasets
✅ **Comprehensive Logging**: Detailed operation tracking and debugging

### CLI Features

**Shell Completion**: The unified CLI supports auto-completion for commands and options:

```bash
# Install completion for your shell
python -m quantcup --install-completion

# Or show completion script to customize
python -m quantcup --show-completion
```

**Cross-Platform Argument Quoting**: When using argument forwarding, quote properly for your shell:

```bash
# Bash/Linux/macOS
python -m quantcup nflfastr pipeline --loader-args "--group fantasy --strategy incremental"

# PowerShell/Windows
python -m quantcup nflfastr pipeline --loader-args "--group fantasy --strategy incremental"

# Command Prompt/Windows (escape quotes)
python -m quantcup nflfastr pipeline --loader-args """--group fantasy --strategy incremental"""
```

**Version Information**:

```bash
# Check version
python -m quantcup --version
quantcup --version  # If installed via pip
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with pip
2. **R 4.0+** with nflfastR and nflreadr packages
3. **PostgreSQL 12+** database server
4. **API Keys** (optional):
   - The Odds API key for betting data
   - API Sports key for additional sports data

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd quantcup_backend

# 2. Install Python dependencies
pip install -r nflfastRv3/requirements.txt
pip install -r odds_api/requirements.txt
# Or install the entire project
pip install -e .

# 3. Install R packages
R -e "install.packages(c('nflfastR', 'nflreadr'))"

# 4. Configure environment
cp .env.example .env
# Edit .env with your database credentials and API keys
```

### Environment Configuration

Create a `.env` file in the root directory:

```bash
# =============================================================================
# QuantCup Backend Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# API Keys (Optional - for specific modules)
# -----------------------------------------------------------------------------
ODDS_API_KEY=your_odds_api_key_here
API_SPORTS_API_KEY=your_api_sports_key_here

# -----------------------------------------------------------------------------
# NFLfastR Database Configuration
# -----------------------------------------------------------------------------
NFLFASTR_DB_HOST=localhost
NFLFASTR_DB_PORT=5432
NFLFASTR_DB_USER=postgres
NFLFASTR_DB_PASSWORD=your_password
NFLFASTR_DB_NAME=nflreadr

# -----------------------------------------------------------------------------
# Odds API Database Configuration
# -----------------------------------------------------------------------------
ODDS_API_DB_HOST=localhost
ODDS_API_DB_PORT=5432
ODDS_API_DB_USER=postgres
ODDS_API_DB_PASSWORD=your_password
ODDS_API_DB_NAME=odds_api

# -----------------------------------------------------------------------------
# Sevalla Production Database (for API tables)
# -----------------------------------------------------------------------------
SEVALLA_QUANTCUP_DB_HOST=your_production_host
SEVALLA_QUANTCUP_DB_PORT=30339
SEVALLA_QUANTCUP_DB_USER=quantcup
SEVALLA_QUANTCUP_DB_PASSWORD=your_password
SEVALLA_QUANTCUP_DB_NAME=quantcup

# -----------------------------------------------------------------------------
# S3/Sevalla Bucket Storage (for production)
# -----------------------------------------------------------------------------
SEVALLA_BUCKET_NAME=your-bucket-name
SEVALLA_BUCKET_REGION=auto
SEVALLA_BUCKET_ENDPOINT=https://your-endpoint.r2.cloudflarestorage.com
SEVALLA_BUCKET_ACCESS_KEY_ID=your_access_key
SEVALLA_BUCKET_SECRET_ACCESS_KEY=your_secret_key

# -----------------------------------------------------------------------------
# Global Settings
# -----------------------------------------------------------------------------
NFLFASTR_VERBOSE=1
ODDS_API_VERBOSE=1
QUANTCUP_VERBOSE=1
```

### Database Setup

```bash
# Create databases for each module
createdb nflreadr
createdb odds_api

# Test connections
python -c "from commonv2 import create_db_engine_from_env; print('✅ Database connections OK')"
```

### Quick Test Run

```bash
# Test each module
python -c "import nfl_data_wrapper; print('✅ NFL Data Wrapper OK')"  # Test NFL data access
python -m quantcup odds --help                                        # Test odds API
python -m quantcup nflfastrv3 --help                                  # Test NFLfastRv3
python -m quantcup weather --help                                     # Test weather module

# Run data pipeline (if you have data)
python -m quantcup nflfastrv3 data process --group nfl_data  # Load NFL data
python -m quantcup nflfastrv3 ml features --seasons 2024       # Engineer features
python -m quantcup nflfastrv3 ml train --model xgboost        # Train models
```

## 📊 Module Directory

### 🏈 [NFLfastRv3 Analytics & ML Pipeline](nflfastRv3/README.md)
**Production-ready NFL analytics engine** - Excellent stability (0.87x ratio) with clean architecture.

- **Purpose**: Complete NFL analytics pipeline from raw data to ML predictions
- **Architecture**: Clean 3-layer design with dependency injection (max 3 layers, 5 complexity points)
- **Storage**: Bucket-first dual storage (S3/Sevalla + PostgreSQL) with environment-aware routing
- **Performance**: 60.4% mean accuracy (2025 validation, 10 weeks), 0.649 AUC, **Stability Ratio 0.87x** (excellent)
- **Data Flow**: 27 raw sources → 8 warehouse tables → 6 feature sets (300+ features)
- **Memory**: 10x reduction via column pruning (4GB → 400MB)
- **Components**: Data Pipeline → Analytics Suite → ML Pipeline

**Key Features:**
- ✅ **Star Schema Warehouse**: 8 optimized tables (5 dimensions + 3 facts)
- ✅ **Season-Phase Gating**: Early vs late season modeling for improved accuracy
- ✅ **Automated Feature Pruning**: "The Gauntlet" 4-stage filtering system
- ✅ **Streaming Operations**: Memory-efficient processing of large datasets
- ✅ **Comprehensive Validation**: Architecture compliance, data quality, temporal safety

```bash
# Complete workflow
python -m quantcup nflfastrv3 data process --group nfl_data
python -m quantcup nflfastrv3 data warehouse
python -m quantcup nflfastrv3 ml features --seasons 2024
python -m quantcup nflfastrv3 ml train --train-seasons 2020-2023 --test-seasons 2024
python -m quantcup nflfastrv3 ml predict
python -m quantcup nflfastrv3 analytics exploratory --season 2024
```

### 💰 [Odds API Data Pipeline](odds_api/README.md)
**Sports betting data integration** - Real-time odds, lines, and market analysis.

- **Purpose**: Comprehensive sports betting data pipeline
- **Data Types**: Odds, spreads, totals, props, schedules, results, teams
- **Sports**: NFL, NBA, MLB, NHL, NCAA Football/Basketball
- **Output**: Multi-schema database with market analysis and CSV exports

```bash
# Load betting data
python -m odds_api --sport americanfootball_nfl --markets h2h,spreads,totals
python -m odds_api --all --sport basketball_nba
```

### 📊 NFL Data Wrapper
**Robust NFL data access** - Wrapper for nfl_data_py library.

- **Purpose**: Enhanced NFL data access with consistent structure
- **Functions**: 25+ NFL data functions (play-by-play, rosters, schedules, etc.)
- **Features**: Clean API matching odds_api module pattern
- **Integration**: Seamless integration with other quantcup modules

```python
from nfl_data_wrapper import import_pbp_data, import_team_desc
pbp_data = import_pbp_data([2023, 2024])
teams = import_team_desc()
```

### 🏛️ [CommonV2 Infrastructure](commonv2/README.md)
**Shared foundation** - Database utilities, logging, configuration, and domain logic.

- **Purpose**: Unified infrastructure for all quantcup modules
- **Components**: Database operations, logging, configuration, team/schedule operations
- **Architecture**: Clean facade API with dependency injection
- **Features**: Bucket-first data lake, table-driven database routing
- **Integration**: Used by all other modules for core operations

```python
from commonv2 import create_db_engine_from_env, upsert_dataframe
from commonv2 import standardize_team_name, get_upcoming_games
from commonv2 import setup_logger
```

### 🏈 [College Football Data (CFD)](cfd/README.md)
**College football analytics** - Python wrapper for CollegeFootballData.com API.

- **Purpose**: Comprehensive college football data access and analysis
- **Coverage**: Games, teams, rankings, betting lines, recruiting, advanced stats
- **Features**: 40+ endpoint functions, pandas DataFrame outputs, simple interface
- **Data Types**: Play-by-play, team stats, player stats, SP+/FPI ratings, recruiting classes
- **Integration**: Follows project's pragmatic coding patterns (1-2 complexity points)

```python
import cfd

# Get current week's games and betting lines
games = cfd.get_games(year=2024, week=10)
lines = cfd.get_lines(year=2024, week=10)
rankings = cfd.get_rankings(year=2024, week=10)

# Get advanced ratings
sp_ratings = cfd.get_sp_ratings(year=2024)
fpi_ratings = cfd.get_fpi_ratings(year=2024)
```

### 📊 [Sportsdataverse Integration](sportsdataverse/sdv_wrapper.py)
**Multi-sport data expansion** - Dynamic wrapper for sportsdataverse library.

- **Purpose**: Unified access to NFL, CFB, NBA, WNBA, NHL data
- **Features**: Auto-discovery of endpoints, unified interface, retry logic
- **Coverage**: Dynamically discovers ALL `load_*` and `espn_*` endpoints
- **Integration**: Normalizes outputs to pandas, supports batch operations
- **Flexibility**: Include/exclude filters, per-endpoint kwargs, shared parameters

```python
from sportsdataverse import SportsDataVerseClient

client = SportsDataVerseClient(prefer_pandas=True)
# List available sports and endpoints
print(client.available_sports())  # ['nfl', 'cfb', 'nba', 'wnba', 'nhl']
print(client.list_endpoints("nfl"))

# Fetch multiple endpoints with shared kwargs
results = client.fetch_many(
    "nfl",
    endpoints=["load_nfl_injuries", "load_nfl_pbp"],
    shared_kwargs={"seasons": [2024]}
)
```

### 🌤️ [Weather Module](weather/)
**Unified weather data integration** - NOAA forecasts and NCEI historical climate data.

- **Purpose**: Complete weather data access for game analysis and backtesting
- **Components**:
  - **Forecasts** ([`weather/forecasts/`](weather/forecasts/)) - NOAA NWS 7-day forecasts
  - **Historical** ([`weather/historical/`](weather/historical/)) - NCEI climatology & observations
- **Features**: Impact scoring, betting tendency analysis, climatology baselines
- **Integration**: Stadium-aware, dome handling, game-time matching
- **Data Range**: Forecasts (7-day ahead), Historical (30-year normals + daily obs)

#### Forecast Module (NOAA NWS)
Real-time weather forecasts for upcoming NFL games:

```bash
# Get weather for specific NFL week
quantcup weather forecast week 15

# Get weather for today's games
quantcup weather forecast today

# Include dome games with verbose logging
quantcup weather forecast week 18 --include-domes --verbose

# Multiple output formats
quantcup weather forecast today --output-format json
quantcup weather forecast week 15 --output-format dataframe
```

**Key Features:**
- ✅ **Impact Scoring**: Temperature, wind, precipitation analysis
- ✅ **Betting Tendencies**: Auto-detects under/rushing favorable conditions
- ✅ **Stadium-Aware**: Handles domes, retractable roofs, open stadiums
- ✅ **Game-Time Matching**: Finds closest forecast period to game time
- ✅ **Rate Limiting**: 1 req/sec with retry logic and 24hr caching

**Data Available:**
- **Temperature**: Game-time temp with categorical impact (cold, hot, etc.)
- **Wind**: Speed/direction with categorical impact (moderate, strong, etc.)
- **Precipitation**: Type and intensity (rain, snow, severity)
- **Conditions**: Full forecast text with special weather detection

**Limitations:**
- ⚠️ **Forecast Range**: Only 7 days ahead (NOAA API limit)
- ⚠️ **No Historical**: Cannot retrieve past game weather

#### Historical Module (NCEI)
Historical weather observations and 30-year climate normals:

```bash
# Get climatology for a specific date and location
quantcup weather historical climatology --lat 35.2271 --lon -80.8431 --date 2025-09-07

# Multiple dates at once
quantcup weather historical climatology --lat 35.2271 --lon -80.8431 \
  --date 2025-01-15 --date 2025-07-10 --date 2025-12-25

# Get historical observations for a date range
quantcup weather historical daily USC00311677 2024-09-01 2024-09-07

# Find nearby weather stations
quantcup weather historical find-stations --lat 35.2271 --lon -80.8431

# Output formats
quantcup weather historical climatology --lat 35.2271 --lon -80.8431 --date 2025-09-07 --output-format json
quantcup weather historical daily USC00311677 2024-09-01 2024-09-07 --output-format csv
```

**Key Features:**
- ✅ **30-Year Normals**: 1991-2020 climate baselines (TMAX, TMIN, PRCP, SNOW)
- ✅ **Daily Observations**: Historical TMAX, TMIN, PRCP, SNOW, AWND
- ✅ **Climatology Forecasts**: Zero-CSV, API-first baseline predictions
- ✅ **Station Auto-Discovery**: Finds nearest COOP station automatically
- ✅ **Leap Year Handling**: Feb 29 → Feb 28 fallback
- ✅ **Rate Limiting**: 10 req/sec with proper logging

**Data Types:**
- **Temperature Normals**: Daily max/min with standard deviation
- **Precipitation Normals**: Daily amount + probability + median if wet
- **Snow Normals**: Probability + median if snow
- **Hourly Observations**: Detailed wind/pressure for advanced features

**Use Cases:**
- 📊 **Backtesting**: Analyze historical game weather conditions
- 📈 **Model Training**: Weather features for ML pipelines
- 🎯 **Baseline Expectations**: Compare forecasts to climate normals
- 🔬 **Research**: Long-term weather trend analysis

**Programmatic Usage:**

```python
from weather.forecasts import get_game_weather, GameWeatherService
from weather.historical import NCEIClient, climatology_forecast

# Get forecast for upcoming game
weather = get_game_weather(home_team='KC', away_team='BUF')
print(f"Impact: {weather.impact_level}, Favors Under: {weather.favors_under}")

# Get historical climatology
client = NCEIClient()
forecast = climatology_forecast(
    client=client,
    date="2025-09-07",
    lat=35.2271,
    lon=-80.8431
)
print(f"High: {forecast['high_temp']}, Rain: {forecast['rain_chance']}")

# Get week's games weather
service = GameWeatherService()
games_weather, meta = service.get_weather_for_week(week=15, season=2024)
```

**Migration Notes:**
- Previous location: `noaa/` → Now: `weather/forecasts/`
- Old command: `quantcup noaa week 15` → New: `quantcup weather forecast week 15`
- Old imports still work but use `from weather.forecasts import ...` going forward

See: [`weather/forecasts/README.md`](weather/forecasts/README.md) and [`weather/historical/README.md`](weather/historical/README.md) for complete documentation.

### 🎰 [DraftKings Scraper](draftkings/scraper.py)
**Live betting odds scraper** - Async web scraping for DraftKings NFL odds.

- **Purpose**: Real-time NFL betting odds collection from DraftKings
- **Technology**: Playwright + AgentQL for robust web scraping
- **Features**: Async operations, proxy support, comprehensive logging
- **Data**: Spreads, moneylines, totals (over/under), event metadata
- **Integration**: PostgreSQL database storage, CSV export, retry logic

```python
from draftkings.scraper import DraftKingsScraper

scraper = DraftKingsScraper()
df = await scraper.scrape_nfl_odds()
scraper.save_to_database(df)  # Save to PostgreSQL
scraper.save_to_csv(df)       # Export to CSV
```

### 📺 [ESPN Unofficial API](espn_unofficial_api/ESPN_API_TESTCALL.py)
**ESPN data access** - Unofficial API client for ESPN depth charts and injuries.

- **Purpose**: Access ESPN's internal API for depth charts and injury data
- **Coverage**: Team depth charts, injury reports, player status
- **Features**: Position normalization, package-based depth charts (offense/defense/ST)
- **Data Quality**: Real-time injury status, practice participation, game availability
- **Integration**: Simple function-based interface, no authentication required

```python
from espn_unofficial_api.ESPN_API_TESTCALL import get_depth_chart, get_injuries

# Get team depth chart
depth = get_depth_chart(team_id=29, season=2025)
starters = depth["starters"]  # rank==1 per position

# Get current injuries
injuries = get_injuries(team_id=29)
```

### ⚽ [Soccer Analytics](soccerAnimate/analysis.r)
**Soccer tracking data visualization** - R-based soccer animation and analysis.

- **Purpose**: Soccer tracking data analysis and visualization
- **Technology**: R with soccerAnimate package
- **Features**: Player tracking animations, tactical analysis, GIF export
- **Data Source**: Metrica Sports sample tracking data
- **Output**: Animated GIFs of player movements and tactical patterns

```r
# Load and animate tracking data
td <- soccerAnimate::get_tidy_data(home_csv, away_csv)
soccerAnimate::soccer_animate(
    tidy_data = td,
    ini_time = 480,
    end_time = 490,
    export_gif = TRUE
)
```

### 🚀 API Sports Integration *(Early Development)*
**Multi-sport data access** - Partial implementation for multi-sport coverage.

- **Purpose**: Extend beyond NFL to NBA, MLB, NHL, and international sports
- **Status**: Basic files in place, no CLI integration yet
- **Current**: NFL and NBA endpoint definitions exist
- **Integration**: Will leverage commonv2 infrastructure when complete

## 📈 Example Workflows

### Complete NFL Analytics Pipeline

```bash
# Step-by-step workflow
# 1. Process NFL data
python -m quantcup nflfastrv3 data process --group nfl_data

# 2. Validate data quality
python -m quantcup nflfastrv3 data validate --source all

# 3. Build data warehouse (if needed)
python -m quantcup nflfastrv3 data warehouse

# 4. Engineer features
python -m quantcup nflfastrv3 ml features --seasons 2024

# 5. Train ML models
python -m quantcup nflfastrv3 ml train --model xgboost --save-model

# 6. Generate predictions
python -m quantcup nflfastrv3 ml predict --output-format json

# 7. Run analytics
python -m quantcup nflfastrv3 analytics exploratory --season 2024

# View results
python -c "
from commonv2 import create_db_engine_from_env
import pandas as pd
engine = create_db_engine_from_env('NFLFASTR_DB')
predictions = pd.read_sql('SELECT * FROM ml_predictions ORDER BY prediction_date DESC LIMIT 10', engine)
print(predictions)
"
```

### Sports Betting Analysis

```bash
# NEW: Unified CLI approach (recommended)
# 1. Load current NFL odds and schedules
python -m quantcup odds --sport americanfootball_nfl --markets h2h,spreads,totals
python -m quantcup odds --schedule --sport americanfootball_nfl

# 2. Load historical results for analysis
python -m quantcup odds --results --sport americanfootball_nfl

# 3. Export for analysis
python -m quantcup odds --sport americanfootball_nfl --csv

# 4. Complete data loading in one command
python -m quantcup odds --all --sport americanfootball_nfl

# Legacy approach (still works)
python -m odds_api --sport americanfootball_nfl --markets h2h,spreads,totals
python -m odds_api --schedule --sport americanfootball_nfl

# 5. Combine with NFL analytics
python -c "
from commonv2 import create_db_engine_from_env
import pandas as pd

# Load odds data
odds_engine = create_db_engine_from_env('ODDS_API_DB')
odds = pd.read_sql('SELECT * FROM markets.h2h WHERE sport_key = \"americanfootball_nfl\"', odds_engine)

# Load NFL predictions
nfl_engine = create_db_engine_from_env('NFLFASTR_DB')
predictions = pd.read_sql('SELECT * FROM ml_predictions', nfl_engine)

# Merge for comprehensive analysis
combined = odds.merge(predictions, on=['home_team', 'away_team', 'game_date'])
print(f'Combined dataset: {len(combined)} records')
"
```

### Research & Development

```python
# Custom analysis combining all data sources
import pandas as pd
from nfl_data_wrapper import import_pbp_data, import_weekly_data
from commonv2 import create_db_engine_from_env

# 1. Load NFL data using wrapper
pbp_data = import_pbp_data([2023, 2024])
weekly_stats = import_weekly_data([2023, 2024])

# 2. Access analytics warehouse
engine = create_db_engine_from_env('NFLFASTR_DB')
team_efficiency = pd.read_sql('SELECT * FROM features.team_efficiency', engine)

# 3. Load betting market data
odds_engine = create_db_engine_from_env('ODDS_API_DB')
market_data = pd.read_sql('SELECT * FROM markets.spreads', odds_engine)

# 4. Combine for comprehensive analysis
# Your custom research code here
```

## 🛠️ Development & Extension

### Adding New Sports

The system is designed for easy expansion to new sports:

```python
# 1. Add sport configuration to odds_api
# 2. Extend commonv2.domain.teams for new sport
# 3. Create sport-specific analytics in nflfastRv3 pattern
# 4. Leverage shared infrastructure
```

### Custom Feature Engineering

```python
# Extend NFLfastRv3 features
def build_custom_features(engine, season=None):
    """Add your custom feature engineering"""
    # Access analytics warehouse
    # Create new features
    # Store in features schema
    pass
```

### Integration with External Systems

```python
# Example: Airflow integration
from odds_api.pipeline import run_pipeline
import nflfastRv3

def daily_sports_pipeline():
    # Load fresh odds data
    run_pipeline('odds', sport_key='americanfootball_nfl')
    
    # Update ML predictions
    nflfastRv3.run_ml_pipeline(train_seasons='2020-2024')
    
    # Your custom logic here
```

## 🔧 Configuration Management

### Environment Variables

The system uses project-specific prefixes for clean separation:

- **NFLFASTR_DB_*** - NFLfastRv3 local database configuration
- **SEVALLA_QUANTCUP_DB_*** - Production database configuration
- **ODDS_API_DB_*** - Odds API database configuration
- **SEVALLA_BUCKET_*** - S3/Sevalla bucket storage configuration
- **QUANTCUP_*** - Global settings

### Database Architecture

- **Dual Storage Strategy**: Bucket-first with PostgreSQL fallback
- **Environment-Aware Routing**: Automatic database selection (local vs production)
- **Separate Databases**: Each module maintains isolation
- **Shared Utilities**: CommonV2 database operations across all modules
- **Consistent Patterns**: Standardized schema and table management

### Logging System

Centralized logging with module-specific files:

```
logs/
├── nflfastr_loading.log     # Data loading operations
├── warehouse.log            # Analytics warehouse building
├── features.log             # Feature engineering
├── ml_training.log          # Model training
├── ml_predictions.log       # Prediction generation
├── odds_api.log            # Odds API operations
└── test.log                # Development and testing
```

## 📚 Documentation

### Module-Specific Documentation
- **[NFLfastRv3 README](nflfastRv3/README.md)** - Complete analytics pipeline with clean architecture
- **[Odds API README](odds_api/README.md)** - Sports betting data pipeline
- **[CommonV2 README](commonv2/README.md)** - Shared infrastructure and utilities

### Additional Resources
- See individual module READMEs for detailed component documentation
- Check module-specific test files for usage examples
- Review inline documentation and docstrings for API details

## 🔍 Troubleshooting

### Common Issues

#### Database Connection Problems
```bash
# Test all database connections
python -c "
from commonv2 import create_db_engine_from_env
for prefix in ['NFLFASTR_DB', 'ODDS_API_DB', 'SEVALLA_QUANTCUP_DB']:
    try:
        engine = create_db_engine_from_env(prefix)
        print(f'✅ {prefix} connection OK')
    except Exception as e:
        print(f'❌ {prefix} connection failed: {e}')
"
```

#### Module Import Issues
```bash
# Verify module installations
python -c "import pandas, sqlalchemy, psycopg2; print('✅ Core packages OK')"
python -c "import nfl_data_wrapper; print('✅ NFL Data Wrapper OK')"
python -c "import xgboost; print('✅ XGBoost OK')"
python -c "import commonv2; print('✅ CommonV2 OK')"
```

#### R Package Issues
```bash
# Test R packages
R -e "library(nflfastR); library(nflreadr); print('✅ R packages OK')"
```

### Getting Help

1. **Check module-specific READMEs** for detailed troubleshooting
2. **Review log files** in the `logs/` directory
3. **Verify environment configuration** in `.env` file
4. **Test individual components** before running complete pipelines

## 📊 Performance & Scalability

### System Requirements

- **Memory**: 8GB+ recommended for full NFL dataset processing
- **Storage**: 10GB+ for complete historical data
- **CPU**: Multi-core recommended for ML training
- **Database**: PostgreSQL with sufficient storage for multiple schemas

### Performance Optimization

- **Chunked Processing**: Large datasets processed in manageable chunks
- **Connection Pooling**: Efficient database connection management
- **Caching**: Strategic caching for frequently accessed data
- **Vectorized Operations**: Pandas/NumPy optimizations throughout

### Scalability Features

- **Modular Architecture**: Scale individual components independently
- **Database Separation**: Isolate workloads across databases
- **Incremental Processing**: Load only new/updated data
- **Parallel Execution**: Multiple modules can run simultaneously

## 🤝 Contributing

### Development Setup

1. **Fork the repository** and create a feature branch
2. **Install development dependencies** for relevant modules
3. **Follow existing patterns** and architectural principles
4. **Add comprehensive tests** for new functionality
5. **Update documentation** including READMEs and docstrings

### Code Style Guidelines

- **Python**: Follow PEP 8, use type hints, comprehensive docstrings
- **SQL**: Clear, readable queries with proper formatting
- **Documentation**: Update both module and root-level documentation
- **Logging**: Use centralized logging system consistently

### Adding New Modules

1. **Follow established patterns** from existing modules
2. **Integrate with commonv2 infrastructure** for consistency
3. **Add comprehensive README** following existing format
4. **Update root README** to include new module
5. **Ensure database isolation** with appropriate prefixes

## 📄 License

This project is designed for educational and research purposes. Please ensure compliance with data source terms of service and applicable regulations.

## 🆕 Recent Additions & Enhancements

### NFLfastRv3 v3.0 - Production Release
Major architecture overhaul with significant performance improvements:
- ✅ **67.3% prediction accuracy** (2025 validation, +7.3 pts vs v2)
- ✅ **10x memory reduction** via column pruning (4GB → 400MB)
- ✅ **Clean architecture** with max 3-layer depth, 5 complexity points budget
- ✅ **Bucket-first storage** with S3/Sevalla + PostgreSQL dual storage
- ✅ **Season-phase gating** for early vs late season modeling
- ✅ **Automated feature pruning** with "The Gauntlet" 4-stage filtering
- See [`nflfastRv3/README.md`](nflfastRv3/README.md) for complete documentation

### College Football Data (CFD) Module
Comprehensive college football analytics integration:
- 40+ API endpoint functions for CollegeFootballData.com
- Games, rankings, betting lines, recruiting, advanced stats (SP+, FPI, ELO)
- Simple function-based interface with pandas DataFrame outputs
- See [`cfd/README.md`](cfd/README.md) for details

### Sportsdataverse Integration
Multi-sport data access expansion:
- Dynamic wrapper for sportsdataverse library (NFL, CFB, NBA, WNBA, NHL)
- Auto-discovery of all available endpoints
- Unified interface with retry logic and pandas normalization
- Batch operations with include/exclude filters

### DraftKings Live Odds Scraper
Real-time betting odds collection:
- Async web scraping with Playwright + AgentQL
- Spreads, moneylines, totals for NFL games
- PostgreSQL database integration with CSV export
- Comprehensive logging and error handling

### ESPN Unofficial API Client
Access to ESPN's internal data:
- Team depth charts with position normalization
- Real-time injury reports and player status
- Simple function-based interface, no authentication required

### Soccer Analytics
R-based soccer tracking data visualization:
- Player tracking animations with soccerAnimate package
- Tactical analysis and GIF export capabilities
- Metrica Sports sample data integration

### Scripts Reorganization
Improved organization with specialized subdirectories:
- **backfill/** - Data backfill operations
- **diagnostics/** - System diagnostic tools
- **utilities/** - General utility scripts

---

**QuantCup Backend v3.0** - A comprehensive sports analytics ecosystem spanning NFL, college football, soccer, and multi-sport data sources with production-ready ML capabilities and clean architecture principles.

## 🙏 Acknowledgments

- **nflfastR Team**: For comprehensive NFL data and R packages
- **nfl_data_py library**: For Python NFL data access
- **The Odds API**: For sports betting data access
- **Open Source Community**: For the tools and libraries that make this possible

---

**QuantCup Backend** - A comprehensive sports analytics ecosystem built with the "skinny-but-useful" philosophy. Maximum functionality, minimal complexity, production-ready reliability.

*Transform raw sports data into sophisticated insights with enterprise-grade infrastructure and modular design.*
