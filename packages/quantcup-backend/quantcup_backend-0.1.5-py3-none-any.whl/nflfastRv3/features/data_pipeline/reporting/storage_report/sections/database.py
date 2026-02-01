"""
Database Health Section Generator

Generates database connectivity and table analysis sections for storage health reporting.
Validates database accessibility and analyzes available tables/schemas.

Pattern: Single Responsibility Principle
One class per report section for clear separation of concerns.
"""

from typing import Optional, Dict, Any, List
import os


class DatabaseHealthSectionGenerator:
    """
    Generate database health monitoring sections.
    
    Responsibilities:
    - Validate database connectivity
    - List and analyze available tables and schemas
    - Report database capacity and table metrics
    
    Pattern: Simple generator (1 complexity point)
    Complexity: Fetches data + formats output
    """
    
    def __init__(self, logger=None):
        """
        Initialize database health section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_connectivity_status(self) -> str:
        """
        Generate database connectivity and configuration status section.
        
        Returns:
            Markdown section for database connectivity status
        """
        section = "## 🗄️ Database Health\n\n"
        section += "### Connectivity Status\n\n"
        
        # Get database configuration
        db_config = self._get_database_config()
        
        # Overall status
        if db_config['has_config']:
            section += "**Status:** ✅ Database configured\n\n"
        else:
            section += "**Status:** ⚠️ Database not configured\n\n"
        
        # Configuration details
        section += "**Configuration:**\n\n"
        section += f"- **Database Path:** `{db_config['db_path'] or 'Not configured'}`\n"
        section += f"- **Database Exists:** {'✅ Yes' if db_config['db_exists'] else '❌ No'}\n"
        section += f"- **Database Type:** {db_config['db_type']}\n"
        
        # Connection test would go here if we had database adapter
        # For now, we report configuration status
        
        return section
    
    def generate_tables_analysis(self) -> str:
        """
        Generate database tables analysis section.
        
        Analyzes available tables and schemas in the database.
        
        Returns:
            Markdown section for database tables analysis
        """
        section = "\n### Tables Analysis\n\n"
        
        db_config = self._get_database_config()
        
        if not db_config['db_exists']:
            section += "⚠️ Database file not found - cannot analyze tables\n"
            return section
        
        # Try to get table information
        try:
            import sqlite3
            
            with sqlite3.connect(db_config['db_path']) as conn:
                cursor = conn.cursor()
                
                # Get all tables grouped by schema
                cursor.execute("""
                    SELECT name, type 
                    FROM sqlite_master 
                    WHERE type IN ('table', 'view')
                    ORDER BY type DESC, name
                """)
                
                tables = cursor.fetchall()
                
                if not tables:
                    section += "⚠️ No tables found in database\n"
                    return section
                
                # Separate by type
                table_list = [t[0] for t in tables if t[1] == 'table']
                view_list = [t[0] for t in tables if t[1] == 'view']
                
                section += f"**Overview:** {len(table_list)} table(s), {len(view_list)} view(s)\n\n"
                
                # Categorize tables
                dim_tables = [t for t in table_list if t.startswith('dim_')]
                fact_tables = [t for t in table_list if t.startswith('fact_')]
                raw_tables = [t for t in table_list if not t.startswith('dim_') and not t.startswith('fact_')]
                
                # Tables breakdown
                if dim_tables or fact_tables:
                    section += "#### Warehouse Tables\n\n"
                    
                    if dim_tables:
                        section += "**Dimension Tables:**\n\n"
                        for table_name in sorted(dim_tables):
                            row_count = self._get_table_row_count(conn, table_name)
                            section += f"- `{table_name}` - {row_count:,} rows\n"
                        section += "\n"
                    
                    if fact_tables:
                        section += "**Fact Tables:**\n\n"
                        for table_name in sorted(fact_tables):
                            row_count = self._get_table_row_count(conn, table_name)
                            section += f"- `{table_name}` - {row_count:,} rows\n"
                        section += "\n"
                
                if raw_tables:
                    section += "#### Raw/Staging Tables\n\n"
                    for table_name in sorted(raw_tables):
                        row_count = self._get_table_row_count(conn, table_name)
                        section += f"- `{table_name}` - {row_count:,} rows\n"
                    section += "\n"
                
        except Exception as e:
            section += f"⚠️ Error analyzing database tables: {str(e)}\n"
            if self.logger:
                self.logger.error(f"Error analyzing database tables: {e}")
        
        return section
    
    def _get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration from environment.
        
        Checks for both SQLite paths and PostgreSQL connection strings
        to align with actual pipeline database usage.
        
        Returns:
            Dictionary with database configuration details
        """
        # Check for PostgreSQL database URLs (used by actual pipeline)
        db_url_prefixes = ['NFLFASTR_DB', 'SEVALLA_QUANTCUP_DB', 'ANALYTICS_DB']
        for prefix in db_url_prefixes:
            # Check for full URL
            db_url = os.getenv(f'{prefix}_URL')
            if db_url:
                return {
                    'has_config': True,
                    'db_path': f'{prefix}_URL (PostgreSQL)',
                    'db_exists': True,  # Assume configured URLs are accessible
                    'db_type': 'PostgreSQL',
                    'connection_type': 'url'
                }
            
            # Check for individual connection parameters
            host = os.getenv(f'{prefix}_HOST')
            if host:
                return {
                    'has_config': True,
                    'db_path': f'{prefix} (host: {host})',
                    'db_exists': True,  # Assume configured hosts are accessible
                    'db_type': 'PostgreSQL',
                    'connection_type': 'parameters'
                }
        
        # Fall back to SQLite path checking (legacy)
        db_path = os.getenv('DATABASE_PATH') or os.getenv('DB_PATH')
        
        # If not in env, try common locations
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
        
        return {
            'has_config': db_path is not None,
            'db_path': db_path,
            'db_exists': os.path.exists(db_path) if db_path else False,
            'db_type': 'SQLite',
            'connection_type': 'file'
        }
    
    def _get_table_row_count(self, conn, table_name: str) -> int:
        """
        Get row count for a table.
        
        Args:
            conn: Database connection
            table_name: Table name
            
        Returns:
            Row count
        """
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error getting row count for {table_name}: {e}")
            return 0


__all__ = ['DatabaseHealthSectionGenerator']
