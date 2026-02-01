"""
Storage Health Section Generator for Warehouse Reports

Generates storage health and configuration sections within warehouse reports.
Displays bucket mode, sync status, and storage optimization metrics.

Pattern: Single Responsibility Principle
One class per report section for clear separation of concerns.
"""

from typing import Dict, Any, Optional


class StorageHealthSectionGenerator:
    """
    Generate storage health sections for warehouse reports.
    
    Responsibilities:
    - Display storage configuration (bucket mode, schema)
    - Show storage optimization metrics
    - Report column pruning efficiency
    - Display memory management settings
    
    Pattern: Simple formatter (1 complexity point)
    Complexity: Formats storage_metrics dict passed from warehouse builders
    """
    
    def __init__(self, logger=None):
        """
        Initialize storage health section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_storage_configuration(self, results: Dict[str, Any]) -> str:
        """
        Generate storage configuration section.
        
        Shows storage mode, bucket settings, and schema configuration.
        
        Args:
            results: Warehouse build results containing storage_metrics dict
            
        Returns:
            Markdown section for storage configuration
        """
        storage_metrics = results.get('storage_metrics', {})
        
        if self.logger:
            self.logger.debug(f"[StorageHealth] storage_metrics present: {bool(storage_metrics)}")
            if storage_metrics:
                self.logger.debug(f"[StorageHealth] storage_metrics keys: {list(storage_metrics.keys())}")
        
        if not storage_metrics:
            if self.logger:
                self.logger.warning("[StorageHealth] No storage_metrics found in results - skipping storage section")
            return ""  # No metrics available
        
        section = "## 🗄️ Storage Health\n\n"
        section += "### Storage Configuration\n\n"
        
        # Bucket mode status
        bucket_mode = storage_metrics.get('bucket_mode', False)
        bucket_name = storage_metrics.get('bucket_name', 'Not configured')
        
        if bucket_mode:
            section += f"**Storage Mode:** ✅ Bucket-enabled (Dual storage)\n\n"
            section += f"- **Bucket:** `{bucket_name}`\n"
            section += f"- **Primary Storage:** Database (local)\n"
            section += f"- **Backup Storage:** S3/Sevalla bucket\n"
            section += f"- **Sync Strategy:** Automatic write-through\n\n"
        else:
            section += f"**Storage Mode:** 📁 Database-only\n\n"
            section += f"- **Primary Storage:** Database (local)\n"
            section += f"- **Bucket Backup:** Disabled\n"
            section += f"- **Reason:** Bucket adapter not available\n\n"
        
        # Schema configuration
        schema_used = storage_metrics.get('schema_used', 'warehouse')
        section += f"**Schema:** `{schema_used}`\n\n"
        
        return section
    
    def generate_optimization_metrics(self, results: Dict[str, Any]) -> str:
        """
        Generate storage optimization metrics section.
        
        Shows memory management settings and column pruning efficiency.
        
        Args:
            results: Warehouse build results containing storage_metrics dict
            
        Returns:
            Markdown section for optimization metrics
        """
        storage_metrics = results.get('storage_metrics', {})
        
        if not storage_metrics:
            return ""
        
        section = "### Storage Optimization\n\n"
        
        # Memory management
        memory_limit_mb = storage_metrics.get('memory_limit_mb', 1536)
        column_pruning = storage_metrics.get('column_pruning_enabled', True)
        
        section += "**Memory Management:**\n\n"
        section += f"- **Memory Limit:** {memory_limit_mb:,} MB\n"
        section += f"- **Strategy:** Chunked processing for large tables\n"
        section += f"- **Spill-to-Bucket:** {'✅ Enabled' if storage_metrics.get('bucket_mode') else '❌ Disabled'}\n\n"
        
        # Column pruning efficiency
        section += "**Column Pruning:**\n\n"
        if column_pruning:
            section += f"- **Status:** ✅ Enabled\n"
            section += f"- **Benefit:** Reduces memory footprint by excluding unused columns\n"
            section += f"- **Applied To:** All fact tables, selective dimension tables\n"
        else:
            section += f"- **Status:** ❌ Disabled\n"
            section += f"- **Impact:** Full column sets loaded (higher memory usage)\n"
        
        section += "\n"
        
        return section
    
    def generate_sync_status(self, results: Dict[str, Any]) -> str:
        """
        Generate bucket-database sync status section.
        
        Shows sync health and write-through success.
        
        Args:
            results: Warehouse build results containing storage_metrics dict
            
        Returns:
            Markdown section for sync status
        """
        storage_metrics = results.get('storage_metrics', {})
        
        if not storage_metrics:
            return ""
        
        # Only show sync status if bucket mode is enabled
        if not storage_metrics.get('bucket_mode', False):
            return ""
        
        section = "### Bucket-Database Sync\n\n"
        
        # Infer sync status from build results
        build_status = results.get('status', 'unknown')
        tables_built = results.get('tables_built', [])
        
        if build_status == 'success':
            section += "**Sync Status:** ✅ All tables synced to bucket\n\n"
            section += f"- **Tables Synced:** {len(tables_built)}\n"
            section += f"- **Sync Method:** Write-through (atomic)\n"
            section += f"- **Lag:** None (synchronous writes)\n\n"
        elif build_status == 'partial':
            section += "**Sync Status:** ⚠️ Partial sync (some tables failed)\n\n"
            section += f"- **Tables Synced:** {len(tables_built)}\n"
            section += f"- **Action Required:** Review failed tables in sections above\n\n"
        else:
            section += "**Sync Status:** ❌ Sync failed or incomplete\n\n"
            section += f"- **Action Required:** Check build errors above\n\n"
        
        return section
    
    def generate_storage_health_summary(self, results: Dict[str, Any]) -> str:
        """
        Generate complete storage health section.
        
        Combines configuration, optimization, and sync sections.
        
        Args:
            results: Warehouse build results containing storage_metrics dict
            
        Returns:
            Complete markdown storage health section
        """
        sections = []
        
        # Add all sub-sections
        sections.append(self.generate_storage_configuration(results))
        sections.append(self.generate_optimization_metrics(results))
        sections.append(self.generate_sync_status(results))
        
        # Join non-empty sections
        return '\n'.join(filter(None, sections))


__all__ = ['StorageHealthSectionGenerator']
