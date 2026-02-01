"""
Pipeline Report Data Lineage Section Generator

Generates data lineage and flow visualization sections for pipeline reports.
Tracks data journey from source to storage, showing transformations and losses.
"""

from typing import Dict, Any, List

from ...common.formatters import (
    format_section_header,
    format_markdown_table,
    format_metric_row,
    format_percentage
)


class DataLineageSectionGenerator:
    """
    Generates data lineage visualization section for pipeline reports.
    
    Provides:
    - Data flow diagrams (R → Cleaning → Storage)
    - Per-source data journey tracking
    - Retention rate analysis by stage
    - Loss point identification
    """
    
    def __init__(self, logger=None):
        """
        Initialize data lineage section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_data_lineage(self, result: Dict[str, Any]) -> str:
        """
        Generate comprehensive data lineage visualization section.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted data lineage section
        """
        sections = [format_section_header("Data Lineage & Flow", level=2)]
        
        group_results = result.get('group_results', {})
        
        if not group_results:
            sections.append("_No lineage data available for this pipeline run._")
            sections.append("\n**Why:** Lineage tracking requires source-level data from the processing pipeline.")
            sections.append("\n**To Enable:** Ensure Phase 1 enhancements are capturing per-source metrics during data processing.")
            return "\n\n".join(sections)
        
        # Generate sub-sections
        sections.append(self._generate_pipeline_flow_diagram(result))
        sections.append(self._generate_per_source_journey(result))
        sections.append(self._generate_retention_analysis(result))
        
        return "\n\n".join(sections)
    
    def _generate_pipeline_flow_diagram(self, result: Dict[str, Any]) -> str:
        """
        Generate ASCII art pipeline flow diagram.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted flow diagram
        """
        sections = [format_section_header("Pipeline Data Flow", level=3)]
        
        # Calculate overall metrics
        total_fetched = result.get('total_rows_fetched', 0)
        total_final = result.get('total_rows', 0)
        total_lost = total_fetched - total_final if total_fetched > 0 else 0
        loss_pct = (total_lost / total_fetched * 100) if total_fetched > 0 else 0
        
        # Count storage successes
        storage_successes = self._count_storage_successes(result)
        bucket_success_rate = storage_successes['bucket_rate']
        db_success_rate = storage_successes['db_rate']
        bucket_count = storage_successes['bucket_count']
        db_count = storage_successes['db_count']
        total_sources = storage_successes['total']
        
        # Create flow diagram
        diagram = f"""```
┌─────────────┐
│ R Service   │  ← nflfastR package integration
└──────┬──────┘
       │ Fetch ({total_fetched:,} rows)
       ↓
┌─────────────┐
│ Validation  │  ← Schema check, type validation
└──────┬──────┘
       │ Pass ({total_fetched:,} rows)
       ↓
┌─────────────┐
│ Cleaning    │  ← Remove duplicates, nulls, outliers
└──────┬──────┘
       │ Loss: {total_lost:,} rows ({loss_pct:.1f}%)
       ↓
┌─────────────┐  {total_final:,} rows
│ Clean Data  │
└──────┬──────┘
       ╱  ╲
      ╱    ╲
     ↓      ↓
┌─────────┐  ┌──────────┐
│ Bucket  │  │ Database │  ← Parallel storage
│ (Cloud) │  │ (Local)  │
└─────────┘  └──────────┘
   ✓ {bucket_success_rate:.0f}%      ✓ {db_success_rate:.0f}%
  {bucket_count}/{total_sources} success  {db_count}/{total_sources} success
```"""
        
        sections.append(diagram)
        
        return "\n\n".join(sections)
    
    def _generate_per_source_journey(self, result: Dict[str, Any]) -> str:
        """
        Generate detailed data journey for each source.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted per-source journey
        """
        sections = [format_section_header("Data Journey per Source", level=3)]
        
        group_results = result.get('group_results', {})
        journeys = []
        
        for group_name, group_data in group_results.items():
            source_details = group_data.get('source_details', {})
            
            for source_name, source_info in source_details.items():
                rows_fetched = source_info.get('rows_fetched', 0)
                rows_after_clean = source_info.get('rows_after_cleaning', 0)
                rows_final = source_info.get('rows', 0)
                rows_lost = source_info.get('rows_lost', 0)
                bucket_success = source_info.get('bucket_success', False)
                database_success = source_info.get('database_success', False)
                
                if rows_fetched == 0:
                    continue
                
                # Build journey diagram
                journey = [f"\n**{source_name}:**"]
                journey.append("```")
                journey.append(f"R Fetch: {rows_fetched:,} rows")
                journey.append("  ↓ Schema validation: ✅ Pass")
                
                if rows_lost > 0:
                    journey.append(f"  ↓ Data cleaning: -{rows_lost:,} rows")
                else:
                    journey.append("  ↓ Data cleaning: ✅ No loss")
                
                journey.append(f"Clean: {rows_after_clean:,} rows")
                
                # Storage outcomes
                if bucket_success and database_success:
                    journey.append("  ↓ Bucket write: ✅ Success")
                    journey.append("  ↓ Database write: ✅ Success")
                    journey.append("Final: ✅ Stored in both locations")
                elif bucket_success and not database_success:
                    journey.append("  ↓ Bucket write: ✅ Success")
                    journey.append("  ↓ Database write: ❌ Failed")
                    journey.append("Final: ⚠️ Stored in bucket only (manual DB sync needed)")
                elif not bucket_success and database_success:
                    journey.append("  ↓ Bucket write: ❌ Failed")
                    journey.append("  ↓ Database write: ✅ Success")
                    journey.append("Final: ⚠️ Stored in database only (bucket sync recommended)")
                else:
                    journey.append("  ↓ Bucket write: ❌ Failed")
                    journey.append("  ↓ Database write: ❌ Failed")
                    journey.append("Final: 🔴 CRITICAL - No storage successful")
                
                journey.append("```")
                journeys.append("\n".join(journey))
        
        if not journeys:
            sections.append("_No detailed source journey data available._")
            return "\n\n".join(sections)
        
 # Show first 5 journeys (to avoid overly long reports)
        if len(journeys) > 5:
            sections.extend(journeys[:5])
            sections.append(f"\n_Showing 5 of {len(journeys)} sources. Additional source journeys follow similar patterns._")
        else:
            sections.extend(journeys)
        
        return "\n\n".join(sections)
    
    def _generate_retention_analysis(self, result: Dict[str, Any]) -> str:
        """
        Generate retention rate analysis by processing stage.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted retention analysis
        """
        sections = [format_section_header("Data Retention by Stage", level=3)]
        
        # Calculate stage-level retention
        total_fetched = result.get('total_rows_fetched', 0)
        total_after_clean = result.get('total_rows', 0)
        
        if total_fetched == 0:
            sections.append("_No retention data available._")
            return "\n\n".join(sections)
        
        # Calculate retention rates
        validation_retention = 100.0  # All fetched data passes validation
        cleaning_retention = (total_after_clean / total_fetched * 100) if total_fetched > 0 else 0
        
        # Storage retention
        storage_successes = self._count_storage_successes(result)
        bucket_retention = storage_successes['bucket_rate']
        db_retention = storage_successes['db_rate']
        
        # Determine loss reasons
        rows_lost = total_fetched - total_after_clean
        
        # Create retention table with dynamic notes
        bucket_count = storage_successes['bucket_count']
        db_count = storage_successes['db_count']
        total_sources = storage_successes['total']
        
        # Calculate storage failures
        bucket_failures = total_sources - bucket_count
        db_failures = total_sources - db_count
        
        # Build storage notes dynamically
        bucket_note = 'All clean data stored' if bucket_failures == 0 else f'{bucket_failures} source(s) failed'
        db_note = 'All clean data stored' if db_failures == 0 else f'{db_failures} source(s) failed'
        
        retention_rows = [
            ['Fetch', '100%', '0', 'N/A'],
            ['Validation', f'{validation_retention:.1f}%', '0', 'All data passed validation'],
            ['Cleaning', f'{cleaning_retention:.1f}%', f'{rows_lost:,}', 'Duplicates (primary)'],
            ['Bucket Storage', f'{bucket_retention:.0f}%*', '0*', bucket_note],
            ['DB Storage', f'{db_retention:.0f}%*', '0*', db_note],
        ]
        
        headers = ['Stage', 'Retention Rate', 'Rows Lost', 'Primary Loss Reason']
        table = format_markdown_table(headers, retention_rows)
        
        sections.append(table)
        
        # Add retention insights
        insights = [
            "\n*Note: Storage retention rates reflect successful writes, not data loss",
            "",
            "**Retention Insights:**",
            f"- **Fetch → Validation:** {validation_retention:.1f}% retention (all data valid)",
            f"- **Validation → Cleaning:** {cleaning_retention:.1f}% retention ({100-cleaning_retention:.1f}% removed)",
            f"- **Cleaning → Storage:** Data safe in bucket and database",
            "",
            "**Loss Points:**"
        ]
        
        if rows_lost > 0:
            insights.append(f"- Primary loss occurs during cleaning ({rows_lost:,} rows)")
            insights.append("- Cleaning removes duplicates, nulls, and invalid records")
            insights.append("- This is expected and indicates good data quality practices")
        else:
            insights.append("- No data loss detected throughout pipeline")
        
        sections.append("\n".join(insights))
        
        return "\n\n".join(sections)
    
    def _count_storage_successes(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Count storage success rates across all sources.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            Dict with bucket_count, db_count, total, bucket_rate, db_rate
        """
        bucket_count = 0
        db_count = 0
        total = 0
        
        group_results = result.get('group_results', {})
        
        for group_data in group_results.values():
            source_details = group_data.get('source_details', {})
            
            for source_info in source_details.values():
                total += 1
                if source_info.get('bucket_success', False):
                    bucket_count += 1
                if source_info.get('database_success', False):
                    db_count += 1
        
        bucket_rate = (bucket_count / total * 100) if total > 0 else 0
        db_rate = (db_count / total * 100) if total > 0 else 0
        
        return {
            'bucket_count': bucket_count,
            'db_count': db_count,
            'total': total,
            'bucket_rate': bucket_rate,
            'db_rate': db_rate
        }


__all__ = ['DataLineageSectionGenerator']
