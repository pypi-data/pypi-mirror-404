"""
Storage Report Section Generators

Reusable section generators for storage health monitoring.
These generators can be used by pipeline and warehouse reports to add storage health context.

Pattern: Minimum Viable Decoupling (2 complexity points)
Architecture: Composition pattern - sections as building blocks
"""

# Note: The standalone StorageReportGenerator has been removed.
# Storage health sections are now integrated directly into pipeline and warehouse reports.
# Import section generators individually if needed.

__all__ = []
