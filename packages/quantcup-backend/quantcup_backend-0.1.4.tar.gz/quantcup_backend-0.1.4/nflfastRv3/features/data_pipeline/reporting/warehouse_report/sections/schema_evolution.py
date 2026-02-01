"""
Schema Evolution Section Generator for Warehouse Reports

PHASE 5: Enhanced report sections with schema evolution visualizations.
Generates comprehensive schema change detection and drift tracking sections.

Pattern: Single Responsibility Principle
One class per report section for clear separation of concerns.
"""

from typing import Dict, Any, List, Optional


class SchemaEvolutionSectionGenerator:
    """
    Generate schema evolution sections for warehouse reports.
    
    PHASE 5 Implementation: Visualizes schema changes detected during warehouse builds.
    
    Responsibilities:
    - Display schema changes across all tables
    - Show severity-based classification (critical, warning, info)
    - Visualize schema drift trends
    - Provide actionable recommendations
    - Track schema stability metrics
    
    Pattern: Simple formatter (1 complexity point)
    Complexity: Formats schema_changes list passed from warehouse builders
    """
    
    def __init__(self, logger=None):
        """
        Initialize schema evolution section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_schema_overview(self, results: Dict[str, Any]) -> str:
        """
        Generate high-level schema change overview.
        
        Shows total changes, severity breakdown, and health score.
        
        Args:
            results: Warehouse build results containing schema_changes list
            
        Returns:
            Markdown section for schema overview
        """
        schema_changes = results.get('schema_changes', [])
        
        if not schema_changes:
            return self._generate_stable_schema_message()
        
        # Count by severity
        critical = sum(1 for c in schema_changes if c.get('severity') == 'critical')
        warnings = sum(1 for c in schema_changes if c.get('severity') == 'warning')
        info = sum(1 for c in schema_changes if c.get('severity') == 'info')
        
        # Count by type
        additions = sum(1 for c in schema_changes if c.get('type') == 'column_added')
        removals = sum(1 for c in schema_changes if c.get('type') == 'column_removed')
        type_changes = sum(1 for c in schema_changes if c.get('type') == 'type_changed')
        
        # Count requires_action
        requires_action = sum(1 for c in schema_changes if c.get('requires_action', False))
        
        section = "## 🔄 Schema Evolution\n\n"
        section += "### Schema Change Overview\n\n"
        
        # Health status indicator
        if critical > 0:
            section += "**Schema Health:** 🔴 **CRITICAL** - Breaking changes detected\n\n"
        elif warnings > 0:
            section += "**Schema Health:** ⚠️ **WARNING** - Compatibility concerns\n\n"
        else:
            section += "**Schema Health:** ✅ **STABLE** - Only non-breaking changes\n\n"
        
        # Summary stats
        section += f"**Total Changes Detected:** {len(schema_changes)}\n\n"
        section += "**Severity Breakdown:**\n"
        section += f"- 🔴 **Critical:** {critical} (Breaking changes)\n"
        section += f"- ⚠️ **Warning:** {warnings} (Compatibility concerns)\n"
        section += f"- ℹ️ **Info:** {info} (Non-breaking changes)\n\n"
        
        section += "**Change Types:**\n"
        section += f"- ➕ **Columns Added:** {additions}\n"
        section += f"- ➖ **Columns Removed:** {removals}\n"
        section += f"- 🔄 **Type Changes:** {type_changes}\n\n"
        
        if requires_action > 0:
            section += f"⚠️ **Action Required:** {requires_action} change(s) require immediate attention\n\n"
        
        return section
    
    def _generate_stable_schema_message(self) -> str:
        """Generate message when no schema changes detected."""
        section = "## 🔄 Schema Evolution\n\n"
        section += "### Schema Change Overview\n\n"
        section += "**Schema Health:** ✅ **STABLE** - No schema changes detected\n\n"
        section += "All table schemas match previous build. No drift detected.\n\n"
        return section
    
    def generate_changes_by_severity(self, results: Dict[str, Any]) -> str:
        """
        Generate detailed breakdown of changes by severity level.
        
        Shows critical changes first, then warnings, then info.
        
        Args:
            results: Warehouse build results containing schema_changes list
            
        Returns:
            Markdown section for changes by severity
        """
        schema_changes = results.get('schema_changes', [])
        
        if not schema_changes:
            return ""
        
        section = "### Schema Changes by Severity\n\n"
        
        # Group by severity
        critical = [c for c in schema_changes if c.get('severity') == 'critical']
        warnings = [c for c in schema_changes if c.get('severity') == 'warning']
        info = [c for c in schema_changes if c.get('severity') == 'info']
        
        # Critical changes (highest priority)
        if critical:
            section += "#### 🔴 Critical Changes (Breaking)\n\n"
            section += "These changes may break downstream consumers and require immediate attention.\n\n"
            
            for change in critical:
                section += self._format_change_detail(change, show_severity=False)
            
            section += "\n"
        
        # Warning changes (medium priority)
        if warnings:
            section += "#### ⚠️ Warning Changes (Compatibility Concerns)\n\n"
            section += "These changes may affect compatibility and should be monitored.\n\n"
            
            for change in warnings:
                section += self._format_change_detail(change, show_severity=False)
            
            section += "\n"
        
        # Info changes (low priority)
        if info:
            section += "#### ℹ️ Info Changes (Non-Breaking)\n\n"
            section += "These changes are non-breaking additions to the schema.\n\n"
            
            for change in info:
                section += self._format_change_detail(change, show_severity=False)
            
            section += "\n"
        
        return section
    
    def generate_changes_by_table(self, results: Dict[str, Any]) -> str:
        """
        Generate detailed breakdown of changes organized by table.
        
        Shows per-table schema evolution for traceability.
        
        Args:
            results: Warehouse build results containing schema_changes list
            
        Returns:
            Markdown section for changes by table
        """
        schema_changes = results.get('schema_changes', [])
        
        if not schema_changes:
            return ""
        
        section = "### Schema Changes by Table\n\n"
        
        # Group by table
        by_table = {}
        for change in schema_changes:
            table = change.get('table', 'unknown')
            if table not in by_table:
                by_table[table] = []
            by_table[table].append(change)
        
        # Sort tables by number of changes (descending)
        sorted_tables = sorted(by_table.items(), key=lambda x: len(x[1]), reverse=True)
        
        for table_name, changes in sorted_tables:
            # Count severity for this table
            critical = sum(1 for c in changes if c.get('severity') == 'critical')
            warnings = sum(1 for c in changes if c.get('severity') == 'warning')
            info = sum(1 for c in changes if c.get('severity') == 'info')
            
            # Table header with severity indicators
            severity_badge = ""
            if critical > 0:
                severity_badge = "🔴"
            elif warnings > 0:
                severity_badge = "⚠️"
            else:
                severity_badge = "ℹ️"
            
            section += f"#### {severity_badge} `{table_name}`\n\n"
            section += f"**Changes:** {len(changes)} "
            section += f"(🔴 {critical}, ⚠️ {warnings}, ℹ️ {info})\n\n"
            
            # List changes for this table
            for change in changes:
                section += self._format_change_detail(change, show_severity=True)
            
            section += "\n"
        
        return section
    
    def generate_schema_drift_summary(self, results: Dict[str, Any]) -> str:
        """
        Generate schema drift summary table.
        
        Provides quick reference table showing all affected tables.
        
        Args:
            results: Warehouse build results containing schema_changes list
            
        Returns:
            Markdown table summarizing schema drift
        """
        schema_changes = results.get('schema_changes', [])
        
        if not schema_changes:
            return ""
        
        section = "### Schema Drift Summary Table\n\n"
        
        # Group by table and aggregate
        by_table = {}
        for change in schema_changes:
            table = change.get('table', 'unknown')
            if table not in by_table:
                by_table[table] = {
                    'critical': 0,
                    'warning': 0,
                    'info': 0,
                    'total': 0,
                    'requires_action': False
                }
            
            severity = change.get('severity', 'info')
            by_table[table][severity] = by_table[table].get(severity, 0) + 1
            by_table[table]['total'] += 1
            if change.get('requires_action', False):
                by_table[table]['requires_action'] = True
        
        # Create table
        section += "| Table | Total Changes | Critical | Warning | Info | Action Required |\n"
        section += "|-------|---------------|----------|---------|------|------------------|\n"
        
        # Sort by severity (critical first)
        sorted_tables = sorted(
            by_table.items(),
            key=lambda x: (x[1]['critical'], x[1]['warning'], x[1]['info']),
            reverse=True
        )
        
        for table_name, stats in sorted_tables:
            action = "⚠️ Yes" if stats['requires_action'] else "✅ No"
            section += (
                f"| `{table_name}` | {stats['total']} | "
                f"{stats.get('critical', 0)} | {stats.get('warning', 0)} | "
                f"{stats.get('info', 0)} | {action} |\n"
            )
        
        section += "\n"
        
        return section
    
    def generate_recommendations(self, results: Dict[str, Any]) -> str:
        """
        Generate actionable recommendations based on schema changes.
        
        Provides specific actions to take based on detected changes.
        
        Args:
            results: Warehouse build results containing schema_changes list
            
        Returns:
            Markdown section with recommendations
        """
        schema_changes = results.get('schema_changes', [])
        
        if not schema_changes:
            return ""
        
        section = "### 📋 Recommendations\n\n"
        
        # Collect specific recommendations
        recommendations = []
        
        # Check for critical changes
        critical_changes = [c for c in schema_changes if c.get('severity') == 'critical']
        if critical_changes:
            recommendations.append(
                "**URGENT:** Critical schema changes detected. Review all downstream "
                "consumers (ML pipelines, reports, APIs) for compatibility."
            )
            
            # Check for column removals
            removals = [c for c in critical_changes if c.get('type') == 'column_removed']
            if removals:
                affected_tables = {c.get('table') for c in removals}
                recommendations.append(
                    f"**Column Removals:** {len(removals)} column(s) removed from "
                    f"{len(affected_tables)} table(s). Update all queries and code "
                    f"that reference removed columns."
                )
        
        # Check for type changes
        type_changes = [c for c in schema_changes if c.get('type') == 'type_changed']
        if type_changes:
            recommendations.append(
                f"**Type Changes:** {len(type_changes)} column type change(s) detected. "
                f"Verify data transformations and type casting logic in downstream processes."
            )
        
        # Check for additions
        additions = [c for c in schema_changes if c.get('type') == 'column_added']
        if additions:
            recommendations.append(
                f"**New Columns:** {len(additions)} new column(s) added. "
                f"Consider incorporating these into downstream analytics and models."
            )
        
        # General recommendations
        if critical_changes or len(type_changes) > 3:
            recommendations.append(
                "**Testing:** Run full integration tests to validate downstream compatibility."
            )
        
        if len(schema_changes) > 5:
            recommendations.append(
                "**Documentation:** Update schema documentation and data dictionary "
                "to reflect recent changes."
            )
        
        # Add monitoring recommendation
        recommendations.append(
            "**Monitoring:** Review schema change trends over time to identify "
            "patterns and potential data quality issues."
        )
        
        # Format recommendations
        for i, rec in enumerate(recommendations, 1):
            section += f"{i}. {rec}\n\n"
        
        return section
    
    def generate_change_timeline(self, results: Dict[str, Any]) -> str:
        """
        Generate chronological timeline of schema changes.
        
        Shows when each change was detected for temporal tracking.
        
        Args:
            results: Warehouse build results containing schema_changes list
            
        Returns:
            Markdown section with change timeline
        """
        schema_changes = results.get('schema_changes', [])
        
        if not schema_changes:
            return ""
        
        section = "### Change Timeline\n\n"
        section += "Chronological order of schema changes detected in this build:\n\n"
        
        # Sort by timestamp
        sorted_changes = sorted(
            schema_changes,
            key=lambda x: x.get('timestamp', ''),
            reverse=False
        )
        
        for change in sorted_changes:
            timestamp = change.get('timestamp', 'Unknown time')
            table = change.get('table', 'unknown')
            change_type = change.get('type', 'unknown')
            severity = change.get('severity', 'info')
            
            # Emoji for severity
            emoji = '🔴' if severity == 'critical' else '⚠️' if severity == 'warning' else 'ℹ️'
            
            section += f"- **{timestamp}** - {emoji} `{table}`: {self._format_change_type(change_type)}\n"
        
        section += "\n"
        
        return section
    
    def _format_change_detail(self, change: Dict[str, Any], show_severity: bool = True) -> str:
        """
        Format a single change detail.
        
        Args:
            change: Change dictionary
            show_severity: Whether to include severity emoji
            
        Returns:
            Formatted markdown string
        """
        table = change.get('table', 'unknown')
        change_type = change.get('type', 'unknown')
        details = change.get('details', {})
        severity = change.get('severity', 'info')
        requires_action = change.get('requires_action', False)
        
        # Severity emoji
        emoji = '🔴' if severity == 'critical' else '⚠️' if severity == 'warning' else 'ℹ️'
        
        # Format based on change type
        if change_type == 'column_added':
            columns = details.get('added_columns', [])
            detail_str = f"**Added Columns:** {', '.join(f'`{c}`' for c in columns)}"
        elif change_type == 'column_removed':
            columns = details.get('removed_columns', [])
            detail_str = f"**Removed Columns:** {', '.join(f'`{c}`' for c in columns)}"
        elif change_type == 'type_changed':
            col = details.get('column', 'unknown')
            old_type = details.get('old_type', 'unknown')
            new_type = details.get('new_type', 'unknown')
            detail_str = f"**Type Change:** `{col}` changed from `{old_type}` → `{new_type}`"
        else:
            detail_str = f"**Change Type:** {change_type}"
        
        # Build output
        output = ""
        if show_severity:
            output += f"{emoji} "
        
        output += f"**`{table}`** - {detail_str}"
        
        if requires_action:
            output += " ⚠️ *Action Required*"
        
        output += "\n\n"
        
        return output
    
    def _format_change_type(self, change_type: str) -> str:
        """Format change type for display."""
        type_map = {
            'column_added': 'Column Addition',
            'column_removed': 'Column Removal',
            'type_changed': 'Type Change',
            'schema_mismatch': 'Schema Mismatch',
            'schema_drift': 'Schema Drift'
        }
        return type_map.get(change_type, change_type.replace('_', ' ').title())
    
    def generate_schema_evolution_section(self, results: Dict[str, Any]) -> str:
        """
        Generate complete schema evolution section.
        
        PHASE 5: Main entry point that orchestrates all schema evolution subsections.
        
        Combines all schema evolution visualizations into one comprehensive section.
        
        Args:
            results: Warehouse build results containing schema_changes list
            
        Returns:
            Complete markdown schema evolution section
        """
        if self.logger:
            self.logger.debug("[SchemaEvolution] Generating schema evolution section...")
        
        schema_changes = results.get('schema_changes', [])
        
        if self.logger:
            self.logger.info(f"[SchemaEvolution] Processing {len(schema_changes)} schema change(s)")
        
        sections = []
        
        # Add all sub-sections
        sections.append(self.generate_schema_overview(results))
        
        if schema_changes:  # Only add detailed sections if changes exist
            sections.append(self.generate_schema_drift_summary(results))
            sections.append(self.generate_changes_by_severity(results))
            sections.append(self.generate_changes_by_table(results))
            sections.append(self.generate_change_timeline(results))
            sections.append(self.generate_recommendations(results))
        
        # Join non-empty sections
        full_section = '\n'.join(filter(None, sections))
        
        if self.logger:
            self.logger.debug(f"[SchemaEvolution] Generated section: {len(full_section)} chars")
        
        return full_section


__all__ = ['SchemaEvolutionSectionGenerator']
