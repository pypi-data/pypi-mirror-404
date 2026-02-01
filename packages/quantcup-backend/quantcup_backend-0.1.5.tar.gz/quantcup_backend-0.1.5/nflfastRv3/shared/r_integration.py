"""
Simplified R Integration Infrastructure

Pattern: Minimum Viable Decoupling
Complexity: 2 points (singleton + simple DI)
Depth: 2 layers (service → R execution)

Provides clean interface to R nflfastR packages with
simple error handling and direct rpy2 integration.
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import warnings

from commonv2 import get_logger
from .models import ValidationResult

# Handle rpy2 import gracefully
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    from rpy2.rinterface_lib.embedded import RRuntimeError
    HAS_RPY2 = True
except ImportError:
    HAS_RPY2 = False
    # Create dummy objects for type checking
    robjects = None  # type: ignore
    pandas2ri = None  # type: ignore
    importr = None  # type: ignore
    RRuntimeError = Exception  # type: ignore


class RIntegrationService:
    """
    Simplified R integration following Minimum Viable Decoupling pattern.
    
    Pattern: Module-level singleton with simple DI
    Complexity: 2 points (singleton + simple DI)
    Depth: 2 layers (service → R execution)
    
    Features:
    - Direct rpy2 integration with fallback
    - Simple error handling
    - String-based R function execution
    - Basic caching for package resolution
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, logger=None):
        """Initialize simplified R integration service."""
        self.logger = logger or get_logger('nflfastRv3.r_integration')
        self.r_available = False
        self.nflfastr_available = False
        self.nflreadr_available = False
        self._function_cache = {}  # Simple caching for package resolution
        
        # Initialize R environment
        self._initialize_r_environment()
    
    def _initialize_r_environment(self) -> None:
        """Initialize R environment with basic validation."""
        try:
            if HAS_RPY2:
                self._initialize_rpy2()
            else:
                self.logger.warning("rpy2 not available, using fallback methods")
                self.r_available = True  # Still allow basic functionality
                
        except Exception as e:
            self.logger.error(f"R environment initialization failed: {e}")
            self.r_available = False
    
    def _initialize_rpy2(self) -> None:
        """Initialize rpy2 direct R integration."""
        if not HAS_RPY2 or robjects is None or pandas2ri is None:
            raise ImportError("rpy2 not available")
            
        try:
            # Activate pandas conversion
            pandas2ri.activate()
            
            # Test R availability
            version = robjects.r('R.version.string')[0]
            self.logger.info(f"R environment initialized: {version}")
            self.r_available = True
            
            # Check for packages
            self._check_packages()
            
        except Exception as e:
            self.logger.error(f"rpy2 initialization failed: {e}")
            raise
    
    def _check_packages(self) -> None:
        """Check if nflfastR and nflreadr packages are available."""
        if not HAS_RPY2 or importr is None:
            return
            
        try:
            importr('nflfastR')
            self.nflfastr_available = True
            self.logger.info("nflfastR package available")
        except Exception:
            self.nflfastr_available = False
            
        try:
            importr('nflreadr')
            self.nflreadr_available = True
            self.logger.info("nflreadr package available")
        except Exception:
            self.nflreadr_available = False
    
    def execute_r_call_string(self, r_call: str, data_source_name: Optional[str] = None) -> pd.DataFrame:
        """
        Execute R call using simplified approach (V1-style).
        
        Args:
            r_call: Complete R function call string (e.g., "load_teams(current = FALSE)")
            data_source_name: Optional name for logging
            
        Returns:
            pd.DataFrame: Results from R function
            
        Raises:
            RuntimeError: If R is not available or function fails
        """
        if not self.r_available:
            raise RuntimeError("R environment not available")
        
        source_name = data_source_name or r_call
        self.logger.info(f"Executing R call: {r_call}")
        
        try:
            if HAS_RPY2:
                return self._execute_r_call(r_call, source_name)
            else:
                self.logger.warning(f"Using fallback execution for {source_name}")
                return pd.DataFrame()  # Fallback returns empty DataFrame
                
        except Exception as e:
            self.logger.error(f"R function call failed: {e}")
            raise RuntimeError(f"R call '{r_call}' execution failed: {e}")
    
    def _execute_r_call(self, r_call: str, source_name: str) -> pd.DataFrame:
        """
        Execute R call with simple package resolution.
        
        Simplified V1 Strategy:
        1. Try function with explicit package prefix if provided
        2. Try function without prefix (R search path)
        3. Try with nflreadr:: prefix
        4. Try with nflfastR:: prefix
        """
        if not HAS_RPY2 or robjects is None or pandas2ri is None:
            raise RuntimeError("rpy2 not available")
        
        # Handle explicit package prefixes
        if '::' in r_call:
            return self._direct_r_execution(r_call, source_name)
        
        # Check cache for previously resolved functions
        function_name = r_call.split('(')[0].strip()
        if function_name in self._function_cache:
            cached_package = self._function_cache[function_name]
            if cached_package:
                prefixed_call = f"{cached_package}::{r_call}"
                return self._direct_r_execution(prefixed_call, source_name)
            else:
                # Cache indicates function works without prefix
                return self._direct_r_execution(r_call, source_name)
        
        # Try without prefix first
        try:
            self.logger.debug(f"Trying {function_name} without package prefix")
            result = self._direct_r_execution(r_call, source_name)
            self._function_cache[function_name] = None  # Cache success
            return result
            
        except RRuntimeError as e:
            if "could not find function" in str(e):
                # Try with package prefixes
                for package in ['nflreadr', 'nflfastR']:
                    try:
                        self.logger.debug(f"Trying {package}::{function_name}")
                        prefixed_call = f"{package}::{r_call}"
                        result = self._direct_r_execution(prefixed_call, source_name)
                        self._function_cache[function_name] = package  # Cache success
                        self.logger.info(f"✓ Resolved {function_name} to {package}")
                        return result
                    except RRuntimeError:
                        continue
                
                # Function not found in any package
                raise RuntimeError(f"Function {function_name} not available in nflfastR or nflreadr")
            else:
                raise  # Re-raise non-function-not-found errors
    
    def _direct_r_execution(self, r_call: str, source_name: str) -> pd.DataFrame:
        """
        Direct R call execution (simplified approach).
        
        Uses the same simple approach as the working V1 system.
        """
        if not HAS_RPY2 or robjects is None or pandas2ri is None:
            raise RuntimeError("rpy2 not available")
            
        try:
            self.logger.debug(f"Executing R call: {r_call}")
            
            # Direct R call execution
            r_data = robjects.r(r_call)
            
            # Convert to pandas DataFrame
            if isinstance(r_data, pd.DataFrame):
                df = r_data
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    df = pandas2ri.rpy2py(r_data)
                    
                    if not isinstance(df, pd.DataFrame):
                        df = pd.DataFrame(df)
            
            self.logger.info(f"Fetched {len(df):,} rows for {source_name}")
            return df
                
        except RRuntimeError as e:
            self.logger.error(f"R runtime error in {source_name}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"R execution error in {source_name}: {e}")
            raise

    @property
    def is_healthy(self) -> bool:
        """Check if R integration is healthy and ready to use."""
        return self.r_available and (self.nflfastr_available or self.nflreadr_available if HAS_RPY2 else True)


# Module-level convenience functions (preserved for API compatibility)
def get_r_service() -> RIntegrationService:
    """
    Get R integration service instance.
    
    Returns:
        RIntegrationService: R service instance
    """
    return RIntegrationService.get_instance()


def execute_real_r_call(r_call: str, data_source_name: Optional[str] = None) -> pd.DataFrame:
    """
    Convenience function for executing R function calls using string approach.
    
    Args:
        r_call: Complete R function call string (e.g., "load_teams(current = FALSE)")
        data_source_name: Optional name for logging
        
    Returns:
        pd.DataFrame: Results from R function
    """
    return get_r_service().execute_r_call_string(r_call, data_source_name)


def current_nfl_season() -> int:
    """
    Return the current NFL season using nflreadr::most_recent_season().

    This function dynamically determines the current NFL season instead of
    using hardcoded defaults, matching V1's intelligent approach.

    Returns:
        int: Current NFL season year

    Raises:
        RuntimeError: If R integration fails or season cannot be determined
    """
    if not HAS_RPY2 or robjects is None:
        raise RuntimeError("rpy2 not available for season detection")

    try:
        service = get_r_service()
        if not service.r_available:
            raise RuntimeError("R environment not available")

        # Use nflreadr::most_recent_season() like V1
        season_result = robjects.r("nflreadr::most_recent_season()")
        season = int(season_result[0])

        service.logger.debug(f"Current NFL season detected: {season}")
        return season

    except Exception as e:
        service = get_r_service()
        service.logger.error(f"Failed to determine current NFL season: {e}")
        raise RuntimeError(f"Could not determine current NFL season: {e}")
