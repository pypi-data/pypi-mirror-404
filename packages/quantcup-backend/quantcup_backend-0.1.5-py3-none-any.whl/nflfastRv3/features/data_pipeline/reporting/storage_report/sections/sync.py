"""
Sync Status Section Generator

Generates storage sync comparison and recommendations sections.
Compares bucket vs database storage to identify sync issues and gaps.

Pattern: Single Responsibility Principle
One class per report section for clear separation of concerns.
"""

from typing import Optional, Dict, Any, List, Set
import os
from commonv2.persistence.bucket_adapter import get_bucket_adapter


class SyncStatusSectionGenerator:
    """
    Generate storage sync status sections.
    
    Responsibilities:
    - Compare bucket vs database table availability  
    - Identify sync gaps and mismatches
    - Generate sync recommendations
    
    Pattern: Simple generator (1 complexity point)
    Complexity: Fetches data + formats output
    """
    
    def __init__(self, logger=None):
        """
        Initialize sync status section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        self.bucket_adapter = get_bucket_adapter(logger=logger)
    
    def generate_sync_comparison(self) -> str:
        """
        Generate storage sync comparison section.
        
        Compares bucket and database storage to identify gaps.
        
        Returns:
            Markdown section for sync comparison
        """
        section = "## 🔄 Storage Sync Status\n\n"
        section += "### Sync Comparison\n\n"
        
        # Get storage inventories
        bucket_tables = self._get_bucket_tables()
        db_tables = self._get_database_tables()
        
        if not bucket_tables and not db_tables:
            section += "⚠️ No data found in either storage location\n"
            return section
        
        # Calculate sync status
        all_tables = bucket_tables | db_tables
        in_both = bucket_tables & db_tables
        only_bucket = bucket_tables - db_tables
        only_db = db_tables - bucket_tables
        
        # Overall metrics
        total_tables = len(all_tables)
        synced_tables = len(in_both)
        sync_rate = (synced_tables / total_tables * 100) if total_tables > 0 else 0
        
        section += f"**Sync Rate:** {sync_rate:.1f}% ({synced_tables}/{total_tables} tables)\n\n"
        
        # Status indicator
        if sync_rate == 100:
            section += "**Status:** ✅ Fully synchronized\n\n"
        elif sync_rate >= 80:
            section += "**Status:** ⚠️ Mostly synchronized (minor gaps)\n\n"
        elif sync_rate >= 50:
            section += "**Status:** ⚠️ Partially synchronized (significant gaps)\n\n"
        else:
            section += "**Status:** ❌ Poorly synchronized (major gaps)\n\n"
        
        # Breakdown table
        section += "| Location | Tables | Details |\n"
        section += "|----------|--------|----------|\n"
        section += f"| Bucket | {len(bucket_tables)} | S3/Sevalla object storage |\n"
        section += f"| Database | {len(db_tables)} | SQLite local storage |\n"
        section += f"| **Both** | **{len(in_both)}** | **Synced tables** |\n"
        section += f"| Bucket Only | {len(only_bucket)} | Missing from database |\n"
        section += f"| Database Only | {len(only_db)} | Missing from bucket |\n"
        section += "\n"
        
        # Detail missing tables
        if only_bucket:
            section += "**Tables in Bucket but not Database:**\n\n"
            for table in sorted(only_bucket):
                section += f"- `{table}`\n"
            section += "\n"
        
        if only_db:
            section += "**Tables in Database but not Bucket:**\n\n"
            for table in sorted(only_db):
                section += f"- `{table}`\n"
            section += "\n"
        
        return section
    
    def generate_sync_recommendations(self) -> str:
        """
        Generate sync recommendations section.
        
        Provides actionable recommendations based on sync status.
        
        Returns:
            Markdown section for sync recommendations
        """
        section = "### Sync Recommendations\n\n"
        
        # Get storage inventories
        bucket_tables = self._get_bucket_tables()
        db_tables = self._get_database_tables()
        
        if not bucket_tables and not db_tables:
            section += "⚠️ No recommendations - no data found\n"
            return section
        
        only_bucket = bucket_tables - db_tables
        only_db = db_tables - bucket_tables
        
        recommendations = []
        
        # Recommendations for bucket-only tables
        if only_bucket:
            priority = "🔴 High" if len(only_bucket) > 5 else "🟡 Medium"
            recommendations.append({
                'priority': priority,
                'action': f"Load {len(only_bucket)} table(s) from bucket to database",
                'tables': sorted(only_bucket)[:3],  # Show first 3
                'benefit': "Sync bucket data to database for local access"
            })
        
        # Recommendations for database-only tables
        if only_db:
            priority = "🟡 Medium"
            recommendations.append({
                'priority': priority,
                'action': f"Upload {len(only_db)} table(s) from database to bucket",
                'tables': sorted(only_db)[:3],  # Show first 3
                'benefit': "Backup database tables to bucket storage"
            })
        
        # Perfect sync
        if not only_bucket and not only_db:
            section += "✅ **No action required** - Storage is fully synchronized\n\n"
            section += "All tables are available in both bucket and database storage.\n"
            return section
        
        # Format recommendations
        if recommendations:
            section += "**Priority Actions:**\n\n"
            
            for i, rec in enumerate(recommendations, 1):
                section += f"{i}. **{rec['priority']} Priority**: {rec['action']}\n\n"
                section += f"   **Example tables:** {', '.join(f'`{t}`' for t in rec['tables'])}\n\n"
                section += f"   **Benefit:** {rec['benefit']}\n\n"
        
        # General recommendations
        section += "**Best Practices:**\n\n"
        section += "- Always write to bucket first (primary storage)\n"
        section += "- Use database as secondary storage for querying\n"
        section += "- Run regular sync checks to detect gaps early\n"
        section += "- Consider automated sync tasks for critical tables\n"
        
        return section
    
    def _get_bucket_tables(self) -> Set[str]:
        """
        Get set of all tables in bucket (across all schemas).
        
        Returns:
            Set of table names found in bucket
        """
        tables = set()
        
        if not self.bucket_adapter._is_available():
            return tables
        
        # Check common schemas
        common_schemas = ['raw_nflfastr', 'warehouse']
        
        for schema in common_schemas:
            schema_tables = self.bucket_adapter.list_tables(schema=schema)
            tables.update(schema_tables)
        
        return tables
    
    def _get_database_tables(self) -> Set[str]:
        """
        Get set of all tables in database.
        
        Returns:
            Set of table names found in database
        """
        tables = set()
        
        # Find database
        db_path = os.getenv('DATABASE_PATH') or os.getenv('DB_PATH')
        
        if not db_path:
            common_paths = [
                'data/quantcup.db',
                'data/nflfastr.db',
                '../data/quantcup.db'
            ]
            for path in common_paths:
                if os.path.exists(path):
                    db_path = path
                    break
        
        if not db_path or not os.path.exists(db_path):
            return tables
        
        # Query database for tables
        try:
            import sqlite3
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type = 'table' 
                    AND name NOT LIKE 'sqlite_%'
                """)
                
                tables = {row[0] for row in cursor.fetchall()}
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error reading database tables: {e}")
        
        return tables


__all__ = ['SyncStatusSectionGenerator']
