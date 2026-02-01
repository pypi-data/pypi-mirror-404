"""
NFLfastRv3 Shared Infrastructure

Layer 3: Infrastructure components
- Database router with environment-aware routing
- R integration service
- Temporal validation utilities
- Validation utilities

Pattern: Module-level singletons with DI override capability
Complexity: 1 point each (simple resource management)
"""

from .r_integration import RIntegrationService
from .temporal_validator import TemporalValidator

__all__ = [
    'RIntegrationService',
    'TemporalValidator'
]
