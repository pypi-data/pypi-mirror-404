"""
Storage Health Section Generator for Pipeline Reports

Generates storage health and validation sections within pipeline reports.
Displays bucket/database connectivity and storage results from ingestion.

Pattern: Single Responsibility Principle
One class per report section for clear separation of concerns.
"""

from typing import Dict, Any
# Reuse existing storage section generators
from ...storage_report.sections import (
    BucketHealthSectionGenerator,
    DatabaseHealthSectionGenerator
)


class PipelineStorageHealthSectionGenerator:
    """
    Generate storage health sections for pipeline reports.
    
    Responsibilities:
    - Delegate to bucket/database health generators
    - Format storage results from pipeline ingestion
    - Show consistency between bucket and database writes
    
    Pattern: Adapter pattern (adapts storage generators for pipeline context)
    Complexity: 1 point (delegates to existing generators)
    """
    
    def __init__(self, logger=None):
        """
        Initialize pipeline storage section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        self.bucket_gen = BucketHealthSectionGenerator(logger=logger)
        self.database_gen = DatabaseHealthSectionGenerator(logger=logger)
    
    def generate_storage_health_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate complete storage health section for pipeline report.
        
        Combines bucket connectivity, database connectivity, and ingestion storage results.
        
        Args:
            result: Pipeline result dictionary from DataPipeline.process()
            
        Returns:
            Complete markdown storage health section
        """
        sections = []
        
        # Header
        sections.append("## 🗄️ Storage Health\n")
        
        # Bucket connectivity
        sections.append(self._generate_bucket_status())
        
        # Database connectivity  
        sections.append(self._generate_database_status())
        
        # Storage results from ingestion
        sections.append(self._generate_ingestion_storage_results(result))
        
        # Cross-validation: Check for contradictions
        sections.append(self._generate_cross_validation(result))
        
        # Join non-empty sections
        return '\n'.join(filter(None, sections))
    
    def _generate_bucket_status(self) -> str:
        """Generate bucket connectivity section."""
        try:
            connectivity = self.bucket_gen.generate_connectivity_status()
            # Remove the header since we have our own
            if connectivity.startswith("## "):
                lines = connectivity.split("\n")
                return "\n".join(lines[2:])  # Skip header
            return connectivity
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not generate bucket status: {e}")
            return "⚠️ Bucket status unavailable\n"
    
    def _generate_database_status(self) -> str:
        """Generate database connectivity section."""
        try:
            connectivity = self.database_gen.generate_connectivity_status()
            # Remove the header since we have our own
            if connectivity.startswith("## "):
                lines = connectivity.split("\n")
                return "\n".join(lines[2:])  # Skip header
            return connectivity
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not generate database status: {e}")
            return "⚠️ Database status unavailable\n"
    
    def _generate_ingestion_storage_results(self, result: Dict[str, Any]) -> str:
        """
        Generate storage results from pipeline ingestion.
        
        Shows success/failure of bucket and database writes during ingestion.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            Markdown section for storage results
        """
        storage_results = result.get('storage_results', {})
        
        if not storage_results:
            return ""
        
        section = "\n### Ingestion Storage Results\n\n"
        
        # Bucket write results
        bucket_success = storage_results.get('bucket_success', False)
        bucket_tables = storage_results.get('bucket_tables', [])
        
        section += "**Bucket Writes:**\n"
        if bucket_success:
            section += f"- **Status:** ✅ Success ({len(bucket_tables)} tables)\n"
            if bucket_tables:
                section += f"- **Tables:** {', '.join(f'`{t}`' for t in bucket_tables)}\n"
        else:
            error = storage_results.get('bucket_error', 'Unknown error')
            section += f"- **Status:** ❌ Failed\n"
            section += f"- **Error:** {error}\n"
        
        section += "\n"
        
        # Database write results  
        db_success = storage_results.get('database_success', False)
        db_tables = storage_results.get('database_tables', [])
        
        section += "**Database Writes:**\n"
        if db_success:
            section += f"- **Status:** ✅ Success ({len(db_tables)} tables)\n"
            if db_tables:
                section += f"- **Tables:** {', '.join(f'`{t}`' for t in db_tables)}\n"
        else:
            error = storage_results.get('database_error', 'Unknown error')
            section += f"- **Status:** ❌ Failed\n"
            section += f"- **Error:** {error}\n"
        
        section += "\n"
        
        # Sync consistency check
        if bucket_success and db_success:
            if set(bucket_tables) == set(db_tables):
                section += "**Sync Status:** ✅ Consistent (bucket and database match)\n"
            else:
                section += "**Sync Status:** ⚠️ Inconsistent (bucket/database mismatch)\n"
                bucket_only = set(bucket_tables) - set(db_tables)
                db_only = set(db_tables) - set(bucket_tables)
                if bucket_only:
                    section += f"- Bucket only: {', '.join(f'`{t}`' for t in bucket_only)}\n"
                if db_only:
                    section += f"- Database only: {', '.join(f'`{t}`' for t in db_only)}\n"
        
        return section
   
    def _generate_cross_validation(self, result: Dict[str, Any]) -> str:
        """
        Cross-validate connectivity status against actual write results.
        
        Detects contradictions where health check says database is not configured
        but writes are actually succeeding.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            Markdown warning section if contradictions detected
        """
        # Get database configuration status
        db_config = self.database_gen._get_database_config()
        has_db_config = db_config.get('has_config', False)
        
        # Count actual successful database writes
        db_write_count = 0
        total_sources = 0
        
        group_results = result.get('group_results', {})
        for group_data in group_results.values():
            source_details = group_data.get('source_details', {})
            for source_info in source_details.values():
                total_sources += 1
                if source_info.get('database_success', False):
                    db_write_count += 1
        
        # Check for contradiction
        if not has_db_config and db_write_count > 0:
            section = "\n### ⚠️ Configuration Contradiction Detected\n\n"
            section += f"**Alert:** Health check reports database is not configured, but **{db_write_count}/{total_sources}** sources successfully wrote to database.\n\n"
            section += "**Likely Cause:** Database configuration uses environment variables not checked by health monitor.\n\n"
            section += "**Action Required:**\n"
            section += "- Verify database configuration in environment variables (e.g., `NFLFASTR_DB_URL`)\n"
            section += "- Update health check to detect actual database configuration method\n\n"
            section += "**Note:** Data writes are working correctly despite health check warning.\n"
            return section
        
        return ""


__all__ = ['PipelineStorageHealthSectionGenerator']
