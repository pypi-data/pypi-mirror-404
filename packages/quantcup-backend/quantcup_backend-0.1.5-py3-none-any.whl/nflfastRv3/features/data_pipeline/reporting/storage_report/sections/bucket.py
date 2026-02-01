"""
Bucket Health Section Generator

Generates bucket connectivity and content analysis sections for storage health reporting.
Validates S3/Sevalla bucket accessibility and analyzes available data.

Pattern: Single Responsibility Principle
One class per report section for clear separation of concerns.
"""

from typing import Optional, Dict, Any, List
from commonv2.persistence.bucket_adapter import get_bucket_adapter


class BucketHealthSectionGenerator:
    """
    Generate bucket health monitoring sections.
    
    Responsibilities:
    - Validate bucket connectivity and credentials
    - List and analyze available tables
    - Report storage capacity and content metrics
    
    Pattern: Simple generator (1 complexity point)
    Complexity: Fetches data + formats output
    """
    
    def __init__(self, logger=None):
        """
        Initialize bucket health section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        self.bucket_adapter = get_bucket_adapter(logger=logger)
    
    def generate_connectivity_status(self) -> str:
        """
        Generate bucket connectivity and configuration status section.
        
        Returns:
            Markdown section for bucket connectivity status
        """
        status = self.bucket_adapter.get_status()
        
        section = "## 🪣 Bucket Health\n\n"
        section += "### Connectivity Status\n\n"
        
        # Overall status indicator
        if status['available'] and status.get('bucket_accessible', False):
            section += "**Status:** ✅ Connected and accessible\n\n"
        elif status['available']:
            section += "**Status:** ⚠️ Client created but bucket inaccessible\n\n"
        else:
            section += "**Status:** ❌ Not available\n\n"
        
        # Configuration details
        section += "**Configuration:**\n\n"
        section += f"- **Bucket Name:** `{status['bucket_name'] or 'Not configured'}`\n"
        section += f"- **Endpoint:** `{status['endpoint_url'] or 'Default AWS S3'}`\n"
        section += f"- **Credentials:** {'✅ Configured' if status['has_credentials'] else '❌ Missing'}\n"
        section += f"- **S3 Client:** {'✅ Created' if status['client_created'] else '❌ Failed'}\n"
        
        # Access test results
        if status.get('bucket_accessible') is not None:
            if status['bucket_accessible']:
                section += f"- **Bucket Access:** ✅ Accessible\n"
            else:
                error_msg = status.get('bucket_error', 'Unknown error')
                section += f"- **Bucket Access:** ❌ Failed - {error_msg}\n"
        
        return section
    
    def generate_content_analysis(self) -> str:
        """
        Generate bucket content analysis section.
        
        Analyzes available schemas, tables, and storage patterns.
        
        Returns:
            Markdown section for bucket content analysis
        """
        section = "\n### Content Analysis\n\n"
        
        # Check if bucket is available
        if not self.bucket_adapter._is_available():
            section += "⚠️ Bucket not available - cannot analyze content\n"
            return section
        
        # Analyze schemas and tables
        schemas = self._discover_schemas()
        
        if not schemas:
            section += "⚠️ No data found in bucket\n"
            return section
        
        # Overview
        total_tables = sum(len(tables) for tables in schemas.values())
        section += f"**Overview:** {len(schemas)} schema(s), {total_tables} table(s)\n\n"
        
        # Per-schema breakdown
        for schema_name, tables in schemas.items():
            section += f"#### Schema: `{schema_name}`\n\n"
            section += f"**Tables:** {len(tables)}\n\n"
            
            if tables:
                section += "| Table | Partitioned | Files |\n"
                section += "|-------|-------------|-------|\n"
                
                for table_name in sorted(tables):
                    is_partitioned, file_count = self._analyze_table(schema_name, table_name)
                    partition_indicator = "✅ Yes" if is_partitioned else "No"
                    section += f"| `{table_name}` | {partition_indicator} | {file_count} |\n"
                
                section += "\n"
        
        return section
    
    def _discover_schemas(self) -> Dict[str, List[str]]:
        """
        Discover available schemas and tables in bucket.
        
        Returns:
            Dictionary mapping schema names to list of table names
        """
        schemas = {}
        
        # Try common schema patterns
        common_schemas = [
            'raw_nflfastr',
            'raw_nflcom_2024',
            'raw_nflcom_2025',
            'warehouse'
        ]
        
        for schema in common_schemas:
            tables = self.bucket_adapter.list_tables(schema=schema)
            if tables:
                schemas[schema] = tables
        
        return schemas
    
    def _analyze_table(self, schema: str, table_name: str) -> tuple:
        """
        Analyze table structure (partitioned vs single file).
        
        Args:
            schema: Schema name
            table_name: Table name
            
        Returns:
            Tuple of (is_partitioned, file_count)
        """
        prefix = f"{schema}/{table_name}/"
        files = self.bucket_adapter.list_files(prefix=prefix)
        
        # Check if table is partitioned by looking for partition directories
        is_partitioned = any('season=' in f or 'date=' in f or 'timestamp=' in f for f in files)
        
        # Count parquet files
        file_count = len([f for f in files if f.endswith('.parquet')])
        
        return is_partitioned, file_count


__all__ = ['BucketHealthSectionGenerator']
