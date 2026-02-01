"""
SQL queries for database operations.
Extracted from Python code for better maintainability and testability.
"""

from typing import List

# ============================================================================
# Table Introspection Queries
# ============================================================================

GET_TABLES_IN_SCHEMA = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = :schema 
    AND table_type = 'BASE TABLE'
"""

CHECK_TABLE_EXISTS = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = :schema 
        AND table_name = :table_name
    )
"""

# ============================================================================
# Table Management Queries
# ============================================================================

DROP_TABLE_IF_EXISTS = """
    DROP TABLE IF EXISTS "{schema}"."{table_name}"
"""


# ============================================================================
# Query Parameter Builders
# ============================================================================

def table_exists_params(schema: str, table_name: str) -> dict:
    """Build parameters for table existence check."""
    return {"schema": schema, "table_name": table_name}


def schema_tables_params(schema: str) -> dict:
    """Build parameters for getting tables in schema."""
    return {"schema": schema}


# ============================================================================
# Team Data Queries
# ============================================================================

GET_TEAMS_BY_ABBREVIATIONS = """
    SELECT
        team_abbr,
        team_name,
        team_nick,
        team_id,
        team_conf,
        team_division,
        team_color,
        team_color2,
        team_color3,
        team_color4,
        team_logo_wikipedia,
        team_logo_espn,
        team_wordmark,
        team_conference_logo,
        team_league_logo,
        team_logo_squared
    FROM raw_nflfastr.teams
    WHERE team_abbr IN :canonical_abbrs
    ORDER BY team_abbr
"""
