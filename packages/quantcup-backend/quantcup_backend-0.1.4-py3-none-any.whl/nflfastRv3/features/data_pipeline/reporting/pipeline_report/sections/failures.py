"""
Pipeline Report Failures Section Generator

Generates error analysis and recovery section for pipeline reports.
Documents failures, circuit breaker activations, and recovery recommendations.
"""

from typing import Dict, Any, List

from ...common.formatters import (
    format_section_header,
    format_markdown_table,
    format_list_items
)
from ...common.config import get_status_indicator


class FailuresSectionGenerator:
    """
    Generates failure analysis section for pipeline reports.
    
    Provides:
    - Error tracking and categorization
    - Circuit breaker activation history
    - Recovery recommendations
    - Retry strategies
    """
    
    def __init__(self, logger=None):
        """
        Initialize failures section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_failures_analysis(self, result: Dict[str, Any]) -> str:
        """
        Generate comprehensive failure analysis section.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted failures analysis section
        """
        sections = [format_section_header("Error Analysis & Recovery", level=2)]
        
        # Check if there are any failures
        has_failures = self._has_failures(result)
        
        if not has_failures:
            sections.append("✅ **No errors detected during pipeline execution.**")
            sections.append("\nAll data sources processed successfully with no failures or circuit breaker activations.")
            return "\n\n".join(sections)
        
        # Generate failure breakdown
        sections.append(self._generate_failure_breakdown(result))
        
        # Generate circuit breaker status
        sections.append(self._generate_circuit_breaker_status(result))
        
        # Generate storage failure analysis
        sections.append(self._generate_storage_failure_analysis(result))
        
        # Generate recovery recommendations
        sections.append(self._generate_recovery_recommendations(result))
        
        return "\n\n".join(sections)
    
    def _has_failures(self, result: Dict[str, Any]) -> bool:
        """
        Check if pipeline has any failures.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            bool: True if failures detected
        """
        # Check for failed groups
        group_results = result.get('group_results', {})
        for group_data in group_results.values():
            if group_data.get('status') == 'failed':
                return True
            
            # Check source-level failures
            source_details = group_data.get('source_details', {})
            for source_info in source_details.values():
                if source_info.get('status') == 'failed':
                    return True
        
        # Check for circuit breaker activations
        if result.get('circuit_breaker_activations'):
            return True
        
        # Check for storage failures
        if result.get('storage_failures'):
            return True
        
        return False
    
    def _generate_failure_breakdown(self, result: Dict[str, Any]) -> str:
        """
        Generate detailed failure breakdown.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted failure breakdown
        """
        sections = [format_section_header("Failure Breakdown", level=3)]
        
        failure_rows = []
        group_results = result.get('group_results', {})
        
        for group_name, group_data in group_results.items():
            if group_data.get('status') == 'failed':
                error = group_data.get('error', 'Unknown error')
                failure_rows.append([
                    'Group',
                    group_name,
                    error[:100] + '...' if len(error) > 100 else error
                ])
            
            # Check source-level failures
            source_details = group_data.get('source_details', {})
            for source_name, source_info in source_details.items():
                if source_info.get('status') == 'failed':
                    error = source_info.get('error', 'Unknown error')
                    failure_rows.append([
                        'Source',
                        source_name,
                        error[:100] + '...' if len(error) > 100 else error
                    ])
        
        if not failure_rows:
            sections.append("_No fetch or processing failures._")
            return "\n\n".join(sections)
        
        # Create table
        headers = ['Type', 'Name', 'Error Message']
        table = format_markdown_table(headers, failure_rows)
        
        sections.append(table)
        
        # Add failure statistics
        total_failures = len(failure_rows)
        group_failures = sum(1 for row in failure_rows if row[0] == 'Group')
        source_failures = sum(1 for row in failure_rows if row[0] == 'Source')
        
        stats = [
            f"\n**Failure Statistics:**",
            f"- Total Failures: {total_failures}",
            f"- Group-level Failures: {group_failures}",
            f"- Source-level Failures: {source_failures}",
        ]
        
        sections.append("\n".join(stats))
        
        return "\n\n".join(sections)
    
    def _generate_circuit_breaker_status(self, result: Dict[str, Any]) -> str:
        """
        Generate circuit breaker activation status.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted circuit breaker status
        """
        sections = [format_section_header("Circuit Breaker Status", level=3)]
        
        activations = result.get('circuit_breaker_activations', [])
        
        if not activations:
            sections.append("✅ No circuit breaker activations.")
            sections.append("\n_All sources operating within failure thresholds._")
            return "\n\n".join(sections)
        
        # List activated circuit breakers
        sections.append("⚠️ **Circuit breakers activated for the following sources:**\n")
        
        activation_rows = []
        for activation in activations:
            source = activation.get('source', 'unknown')
            failure_count = activation.get('failure_count', 0)
            last_error = activation.get('last_error', 'Unknown')
            
            activation_rows.append([
                source,
                str(failure_count),
                last_error[:80] + '...' if len(last_error) > 80 else last_error
            ])
        
        headers = ['Source', 'Failure Count', 'Last Error']
        table = format_markdown_table(headers, activation_rows)
        
        sections.append(table)
        
        # Add circuit breaker explanation
        explanation = """
**Circuit Breaker Pattern:**
When a source experiences 3+ consecutive failures, the circuit breaker activates to:
- Prevent cascading failures
- Reduce unnecessary API calls
- Allow time for issue resolution
- Maintain pipeline stability

Manual intervention is required to reset circuit breakers after resolving underlying issues.
"""
        sections.append(explanation.strip())
        
        return "\n\n".join(sections)
    
    def _generate_storage_failure_analysis(self, result: Dict[str, Any]) -> str:
        """
        Generate storage failure analysis.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted storage failure analysis
        """
        sections = [format_section_header("Storage Failures", level=3)]
        
        storage_failures = result.get('storage_failures', [])
        
        if not storage_failures:
            sections.append("✅ No storage failures detected.")
            sections.append("\n_All data successfully stored to bucket and routed to databases._")
            return "\n\n".join(sections)
        
        # List storage failures
        sections.append("⚠️ **Storage failures detected:**\n")
        
        failure_rows = []
        for failure in storage_failures:
            table = failure.get('table', 'unknown')
            bucket_success = failure.get('bucket_success', False)
            error = failure.get('error', 'Unknown')
            recovery_needed = failure.get('recovery_needed', True)
            
            bucket_status = '✓' if bucket_success else '✗'
            recovery_icon = '🔴' if recovery_needed else '🟡'
            
            failure_rows.append([
                table,
                bucket_status,
                f"{recovery_icon} {'Required' if recovery_needed else 'Optional'}",
                error[:60] + '...' if len(error) > 60 else error
            ])
        
        headers = ['Table', 'Bucket', 'Recovery', 'Error']
        table = format_markdown_table(headers, failure_rows)
        
        sections.append(table)
        
        # Add storage failure notes
        notes = """
**Storage Status Legend:**
- ✓ = Successfully stored
- ✗ = Storage failed

**Recovery Priority:**
- 🔴 Required: Data not in bucket - immediate action needed
- 🟡 Optional: Data safe in bucket - database sync can be retried
"""
        sections.append(notes.strip())
        
        return "\n\n".join(sections)
    
    def _generate_recovery_recommendations(self, result: Dict[str, Any]) -> str:
        """
        Generate recovery recommendations for failures.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted recovery recommendations
        """
        sections = [format_section_header("Recovery Recommendations", level=3)]
        
        recommendations: List[str] = []
        
        # Analyze failures and provide specific recommendations
        group_results = result.get('group_results', {})
        
        # Check for fetch failures
        fetch_failures = []
        for group_name, group_data in group_results.items():
            if group_data.get('status') == 'failed':
                fetch_failures.append(group_name)
        
        if fetch_failures:
            recommendations.append(
                f"**Fetch Failures ({len(fetch_failures)}):**\n"
                f"  - Groups affected: {', '.join(fetch_failures)}\n"
                f"  - Action: Check R service health and API availability\n"
                f"  - Command: Re-run pipeline after resolving R integration issues"
            )
        
        # Check for circuit breaker activations
        activations = result.get('circuit_breaker_activations', [])
        if activations:
            recommendations.append(
                f"**Circuit Breaker Activations ({len(activations)}):**\n"
                f"  - Sources affected: {', '.join(a.get('source', 'unknown') for a in activations)}\n"
                f"  - Action: Investigate and resolve underlying issues\n"
                f"  - Next Step: Manual circuit breaker reset required after fix"
            )
        
        # Check for storage failures
        storage_failures = result.get('storage_failures', [])
        critical_storage_failures = [
            f for f in storage_failures 
            if not f.get('bucket_success', False)
        ]
        
        if critical_storage_failures:
            recommendations.append(
                f"**Critical Storage Failures ({len(critical_storage_failures)}):**\n"
                f"  - Tables affected: {', '.join(f.get('table', 'unknown') for f in critical_storage_failures)}\n"
                f"  - Action: IMMEDIATE - Data not persisted to bucket\n"
                f"  - Recovery: Re-run pipeline immediately to prevent data loss"
            )
        
        partial_storage_failures = [
            f for f in storage_failures 
            if f.get('bucket_success', False)
        ]
        
        if partial_storage_failures:
            recommendations.append(
                f"**Partial Storage Failures ({len(partial_storage_failures)}):**\n"
                f"  - Tables affected: {', '.join(f.get('table', 'unknown') for f in partial_storage_failures)}\n"
                f"  - Status: Data safe in bucket, database sync failed\n"
                f"  - Recovery: Can retry database routing from bucket storage"
            )
        
        if not recommendations:
            recommendations.append(
                "✅ **No recovery actions required.**\n\n"
                "Pipeline completed successfully with no failures."
            )
        
        sections.append("\n\n".join(recommendations))
        
        return "\n\n".join(sections)


__all__ = ['FailuresSectionGenerator']
