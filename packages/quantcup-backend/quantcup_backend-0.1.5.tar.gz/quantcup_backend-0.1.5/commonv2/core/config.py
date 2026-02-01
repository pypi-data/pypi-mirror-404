"""
Configuration validation utilities for quantcup-simple projects.

This module provides validation for environment variables and system configuration
to ensure applications fail fast with clear error messages if misconfigured.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url
from .logging import get_logger

# Module-level logger for simple utilities (following database.py pattern)
_logger = get_logger('commonv2.core.config')


class ConfigError(Exception):
    """Configuration validation error."""
    pass


@dataclass(frozen=True)
class DatabaseConfig:
    """Value object for database configuration with validation."""
    host: str
    port: int
    user: str
    password: str
    database: str
    
    @classmethod
    def load_from_env(cls, database_name: str) -> "DatabaseConfig":
        """
        Internal method: Create config from environment variables with explicit database name.
        
        This is the internal implementation that still takes database parameters.
        Use table-aware functions for parameter-free configuration.
        
        Args:
            database_name: Database name (e.g., 'NFLFASTR_DB', 'SEVALLA_QUANTCUP_DB')
        
        Returns:
            DatabaseConfig instance
            
        Raises:
            ConfigError: If required variables are missing or invalid
        """
        load_dotenv()
        
        # Support full URL override
        url_env = os.getenv(f"{database_name}_URL")
        if url_env:
            try:
                url = make_url(url_env)
                if not all([url.host, url.username, url.password, url.database]):
                    raise ConfigError(f"Invalid database URL format: {database_name}_URL")
                
                return cls(
                    host=str(url.host),
                    port=url.port or 5432,
                    user=str(url.username),
                    password=str(url.password),
                    database=str(url.database)
                )
            except Exception as e:
                raise ConfigError(f"Failed to parse {database_name}_URL: {e}")
        
        # Individual environment variables
        config_map = {
            'host': f'{database_name}_HOST',
            'port': f'{database_name}_PORT', 
            'user': f'{database_name}_USER',
            'password': f'{database_name}_PASSWORD',
            'database': f'{database_name}_NAME'
        }
        
        values = {}
        missing = []
        
        for key, env_var in config_map.items():
            value = os.getenv(env_var)
            if value is None:
                missing.append(env_var)
            else:
                values[key] = int(value) if key == 'port' else value
        
        if missing:
            raise ConfigError(f"Missing database environment variables: {missing}")
        
        return cls(**values)
    
    @property
    def connection_url(self) -> str:
        """Get SQLAlchemy connection URL."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def masked_url(self) -> str:
        """Get connection URL with masked password for logging."""
        return f"postgresql+psycopg2://{self.user}:****@{self.host}:{self.port}/{self.database}"


class DatabasePrefixes:
    """Database prefix constants for table routing."""
    LOCAL_DEV = "NFLFASTR_DB"
    API_PRODUCTION = "SEVALLA_QUANTCUP_DB" 
    ANALYTICS = "ANALYTICS_DB"
    
    @classmethod
    def get_all(cls):
        return [cls.LOCAL_DEV, cls.API_PRODUCTION, cls.ANALYTICS]


class TransformNames:
    """Transform function names for table routing."""
    STANDARDIZE_TEAMS = "standardize_team_names"
    PARSE_DATES = "parse_dates"
    ADD_METADATA = "add_metadata"
    
    @classmethod
    def get_all(cls):
        return [cls.STANDARDIZE_TEAMS, cls.PARSE_DATES, cls.ADD_METADATA]


class SchemaNames:
    """Schema name constants."""
    RAW_NFLFASTR = "raw_nflfastr"
    ANALYTICS = "analytics"
    STAGING = "staging"
    FEATURES = "features"


class Environment:
    """Deployment environment detection using ENVIRONMENT env variable."""
    LOCAL = "local"
    PRODUCTION = "production"
    TESTING = "testing"
    
    @classmethod
    def get_current(cls) -> str:
        """
        Get current environment from ENVIRONMENT env variable.
        
        Returns:
            Environment string (local, production, or testing)
            Defaults to 'local' if not set
        """
        return os.getenv('ENVIRONMENT', cls.LOCAL).lower()
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.get_current() == cls.PRODUCTION
    
    @classmethod
    def is_local(cls) -> bool:
        """Check if running in local development environment."""
        return cls.get_current() == cls.LOCAL
    
    @classmethod
    def is_testing(cls) -> bool:
        """Check if running in testing environment."""
        return cls.get_current() == cls.TESTING


class FeatureConfig:
    """
    Simple configuration for ML feature routing (non-R-based features).
    
    Unlike DataSourceConfig which is designed for R-based data sources,
    this is for features built from warehouse data that need bucket-first
    architecture with environment-aware database routing.
    """
    def __init__(self, table: str, schema: str, unique_keys: list, databases: list, bucket: bool = True):
        self.table = table
        self.schema = schema
        self.unique_keys = unique_keys
        self.databases = databases
        self.bucket = bucket
        self.strategy = 'full_refresh'  # Features always use full refresh
        self.transforms = {}  # No transforms for features


__all__ = [
    'ConfigError',
    'DatabaseConfig',
    'DatabasePrefixes',
    'TransformNames',
    'SchemaNames',
    'Environment',
    'FeatureConfig'
]