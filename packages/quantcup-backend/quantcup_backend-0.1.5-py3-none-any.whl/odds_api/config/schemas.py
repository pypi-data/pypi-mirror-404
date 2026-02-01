"""
Data configuration for odds API pipeline.
Single source of truth for market schemas, following nflfastR patterns.
"""

from collections import OrderedDict

# Single schema map drives table creation, DataFrame preparation, and upserts
MARKET_MAP = {
    "h2h": {
        "description": "Moneyline/Head-to-Head betting odds",
        "schema": "markets",
        "uses_quota": True,
        "columns": OrderedDict([
            # Core identifiers
            ("event_id", "TEXT"),
            ("bookmaker_key", "TEXT"),
            ("commence_time", "TIMESTAMPTZ"),
            ("home_team", "TEXT"),
            ("away_team", "TEXT"),
            
            # Market-specific odds
            ("home_team_odds", "INTEGER"),
            ("away_team_odds", "INTEGER"),
            
            # Calculated payouts (bet_amount = 100)
            ("home_team_payout", "DECIMAL(8,2)"),
            ("away_team_payout", "DECIMAL(8,2)"),
            ("home_team_profit", "DECIMAL(8,2)"),
            ("away_team_profit", "DECIMAL(8,2)"),
            
            # Implied probabilities and juice
            ("home_implied_prob_pct", "DECIMAL(6,3)"),
            ("away_implied_prob_pct", "DECIMAL(6,3)"),
            ("moneyline_juice_pct", "DECIMAL(6,3)"),
            
            # Metadata
            ("sport_key", "TEXT"),
            ("sport_title", "TEXT"),
            ("bookmaker_title", "TEXT"),
            ("bookmaker_last_update", "TIMESTAMPTZ"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()")
        ]),
        "pk": ["event_id", "bookmaker_key"],
        "indexes": ["commence_time", "bookmaker_key", "sport_key"]
    },
    
    "spreads": {
        "description": "Point spread betting odds",
        "schema": "markets",
        "uses_quota": True,
        "columns": OrderedDict([
            # Core identifiers
            ("event_id", "TEXT"),
            ("bookmaker_key", "TEXT"),
            ("commence_time", "TIMESTAMPTZ"),
            ("home_team", "TEXT"),
            ("away_team", "TEXT"),
            
            # Market-specific data
            ("home_team_spread", "DECIMAL(4,1)"),
            ("away_team_spread", "DECIMAL(4,1)"),
            ("home_team_spread_odds", "INTEGER"),
            ("away_team_spread_odds", "INTEGER"),
            
            # Calculated payouts (bet_amount = 100)
            ("home_spread_payout", "DECIMAL(8,2)"),
            ("away_spread_payout", "DECIMAL(8,2)"),
            ("home_spread_profit", "DECIMAL(8,2)"),
            ("away_spread_profit", "DECIMAL(8,2)"),
            
            # Implied probabilities and juice
            ("home_spread_implied_prob_pct", "DECIMAL(6,3)"),
            ("away_spread_implied_prob_pct", "DECIMAL(6,3)"),
            ("spread_juice_pct", "DECIMAL(6,3)"),
            
            # Metadata
            ("sport_key", "TEXT"),
            ("sport_title", "TEXT"),
            ("bookmaker_title", "TEXT"),
            ("bookmaker_last_update", "TIMESTAMPTZ"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()")
        ]),
        "pk": ["game_id", "bookmaker_key"],
        "indexes": ["commence_time", "bookmaker_key", "sport_key"]
    },
    
    "totals": {
        "description": "Over/Under total points betting odds",
        "schema": "markets",
        "uses_quota": True,
        "columns": OrderedDict([
            # Core identifiers
            ("game_id", "TEXT"),
            ("bookmaker_key", "TEXT"),
            ("commence_time", "TIMESTAMPTZ"),
            ("home_team", "TEXT"),
            ("away_team", "TEXT"),
            
            # Market-specific data
            ("total_points", "DECIMAL(4,1)"),
            ("over_odds", "INTEGER"),
            ("under_odds", "INTEGER"),
            
            # Calculated payouts (bet_amount = 100)
            ("over_payout", "DECIMAL(8,2)"),
            ("under_payout", "DECIMAL(8,2)"),
            ("over_profit", "DECIMAL(8,2)"),
            ("under_profit", "DECIMAL(8,2)"),
            
            # Implied probabilities and juice
            ("over_implied_prob_pct", "DECIMAL(6,3)"),
            ("under_implied_prob_pct", "DECIMAL(6,3)"),
            ("totals_juice_pct", "DECIMAL(6,3)"),
            
            # Metadata
            ("sport_key", "TEXT"),
            ("sport_title", "TEXT"),
            ("bookmaker_title", "TEXT"),
            ("bookmaker_last_update", "TIMESTAMPTZ"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()")
        ]),
        "pk": ["game_id", "bookmaker_key"],
        "indexes": ["commence_time", "bookmaker_key", "sport_key"]
    },
    
    # New endpoint schemas
    "leagues": {
        "description": "Available sports and leagues",
        "schema": "sports",
        "endpoint": "sports",
        "uses_quota": False,
        "columns": OrderedDict([
            ("sport_key", "TEXT"),
            ("group_name", "TEXT"),
            ("title", "TEXT"),
            ("description", "TEXT"),
            ("active", "BOOLEAN"),
            ("has_outrights", "BOOLEAN"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()")
        ]),
        "pk": ["sport_key"],
        "indexes": ["active", "group_name"]
    },
    
    "teams": {
        "description": "Teams and players by sport",
        "schema": "sports",
        "endpoint": "participants",
        "uses_quota": False,
        "columns": OrderedDict([
            ("participant_id", "TEXT"),
            ("sport_key", "TEXT"),
            ("full_name", "TEXT"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()")
        ]),
        "pk": ["participant_id", "sport_key"],
        "indexes": ["sport_key", "full_name"]
    },
    
    "schedule": {
        "description": "Game/event listings",
        "schema": "games",
        "endpoint": "events",
        "uses_quota": False,
        "columns": OrderedDict([
            ("event_id", "TEXT"),
            ("sport_key", "TEXT"),
            ("sport_title", "TEXT"),
            ("commence_time", "TIMESTAMPTZ"),
            ("home_team", "TEXT"),
            ("away_team", "TEXT"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()")
        ]),
        "pk": ["event_id"],
        "indexes": ["sport_key", "commence_time", "home_team", "away_team"]
    },
    
    "results": {
        "description": "Live scores and game results",
        "schema": "games",
        "endpoint": "scores",
        "uses_quota": True,
        "columns": OrderedDict([
            ("event_id", "TEXT"),
            ("sport_key", "TEXT"),
            ("sport_title", "TEXT"),
            ("commence_time", "TIMESTAMPTZ"),
            ("completed", "BOOLEAN"),
            ("home_team", "TEXT"),
            ("away_team", "TEXT"),
            ("home_score", "INTEGER"),
            ("away_score", "INTEGER"),
            ("last_update", "TIMESTAMPTZ"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()")
        ]),
        "pk": ["event_id"],
        "indexes": ["sport_key", "commence_time", "completed", "last_update"]
    },
    
    "props": {
        "description": "Player props and event-specific odds",
        "schema": "markets",
        "endpoint": "event_odds",
        "uses_quota": True,
        "columns": OrderedDict([
            ("event_id", "TEXT"),
            ("sport_key", "TEXT"),
            ("bookmaker_key", "TEXT"),
            ("market_key", "TEXT"),
            ("market_data", "JSONB"),
            ("last_update", "TIMESTAMPTZ"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()")
        ]),
        "pk": ["event_id", "bookmaker_key", "market_key"],
        "indexes": ["sport_key", "market_key", "last_update", "event_id"]
    }
}

# API configuration
SUPPORTED_SPORTS = {
    "americanfootball_nfl": "NFL",
    "basketball_nba": "NBA", 
    "basketball_ncaab": "NCAA Basketball",
    "americanfootball_ncaaf": "NCAA Football",
    "baseball_mlb": "MLB",
    "icehockey_nhl": "NHL"
}

__all__ = [
    'MARKET_MAP',
    'SUPPORTED_SPORTS', 
    'get_market_columns',
    'get_market_ddl',
    'get_market_indexes',
    'validate_sport_and_markets'
]

def get_market_columns(market_type):
    """Get column names for a specific market type."""
    if market_type not in MARKET_MAP:
        raise ValueError(f"Unknown market type: {market_type}")
    return list(MARKET_MAP[market_type]["columns"].keys())

def get_market_ddl(market_type, schema=None):
    """Generate DDL for a specific market table."""
    if market_type not in MARKET_MAP:
        raise ValueError(f"Unknown market type: {market_type}")
    
    config = MARKET_MAP[market_type]
    columns = config["columns"]
    pk = config["pk"]
    
    # Use schema from config if not provided
    if schema is None:
        schema = config.get("schema", "markets")
    
    # Build column definitions with proper comma separation
    col_block = ",\n".join(f"    {name} {dtype}" for name, dtype in columns.items())
    
    ddl = f"""CREATE TABLE IF NOT EXISTS {schema}.{market_type} (
{col_block},
    PRIMARY KEY ({', '.join(pk)})
);"""
    
    return ddl

def get_market_indexes(market_type, schema=None):
    """Generate index DDL for a specific market table."""
    if market_type not in MARKET_MAP:
        raise ValueError(f"Unknown market type: {market_type}")
    
    config = MARKET_MAP[market_type]
    indexes = config.get("indexes", [])
    
    # Use schema from config if not provided
    if schema is None:
        schema = config.get("schema", "markets")
    
    index_ddls = []
    for index_col in indexes:
        index_name = f"idx_{market_type}_{index_col}"
        ddl = f"CREATE INDEX IF NOT EXISTS {index_name} ON {schema}.{market_type} ({index_col});"
        index_ddls.append(ddl)
    
    return index_ddls

def validate_sport_and_markets(sport_key, markets):
    """Validate sport and market parameters."""
    if sport_key not in SUPPORTED_SPORTS:
        raise ValueError(f"Unsupported sport: {sport_key}. Supported: {list(SUPPORTED_SPORTS.keys())}")
    
    if isinstance(markets, str):
        markets = [m.strip() for m in markets.split(",")]
    
    for market in markets:
        if market not in MARKET_MAP:
            raise ValueError(f"Unsupported market: {market}. Supported: {list(MARKET_MAP.keys())}")
    
    return markets