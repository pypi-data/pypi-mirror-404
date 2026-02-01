"""
CLI Interface for nflfastRv3

Provides command-line interfaces for all major workflows:
- Data pipeline operations
- ML pipeline workflows
- System utilities and validation

Pattern: Simple command orchestration
Complexity: 1 point (basic CLI routing)
Layer: 1 (Public interface)
"""

from .main import main as cli_main
from .data_commands import DataCommands
from .ml_commands import MLCommands

__all__ = [
    'cli_main',
    'DataCommands',
    'MLCommands'
]
