#!/usr/bin/env python3
"""
Bucket Data Sources Comparison Script

Compares data sources available in the S3/Sevalla bucket with the data sources
defined in nflfastRv3/features/data_pipeline/config/data_sources.py

This script helps identify:
- Data sources that exist in the bucket but are not in the configuration
- Data sources that are configured but missing from the bucket
- Summary statistics and recommendations
"""

import sys
import os
from typing import Set, Dict, List, Tuple, Any
from datetime import datetime
from pathlib import Path

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from commonv2.persistence.bucket_adapter import BucketAdapter
    from nflfastRv3.features.data_pipeline.config.data_sources import (
        DATA_SOURCE_GROUPS, 
        list_all_sources
    )
    from commonv2 import get_logger
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this script from the project root directory")
    print("and that all dependencies are installed.")
    sys.exit(1)


class BucketDataSourceComparison:
    """
    Compares bucket data sources with configuration file definitions.
    """
    
    def __init__(self, schema: str = 'raw_nflfastr'):
        """
        Initialize the comparison tool.
        
        Args:
            schema: Schema name to check in bucket (default: 'raw_nflfastr')
        """
        self.schema = schema
        self.logger = get_logger('bucket_comparison')
        self.bucket_adapter = BucketAdapter(logger=self.logger)
        
        # Check bucket availability
        if not self.bucket_adapter._is_available():
            self.logger.error("❌ Bucket is not available. Check your configuration:")
            status = self.bucket_adapter.get_status()
            for key, value in status.items():
                self.logger.error(f"   {key}: {value}")
            raise RuntimeError("Bucket not available - cannot perform comparison")
    
    def get_bucket_data_sources(self) -> Set[str]:
        """
        Get all data source table names from the bucket.
        
        Returns:
            Set of table names found in the bucket
        """
        self.logger.info(f"🔍 Querying bucket for data sources in schema '{self.schema}'...")
        
        try:
            tables = self.bucket_adapter.list_tables(self.schema)
            self.logger.info(f"✅ Found {len(tables)} tables in bucket")
            return set(tables)
        except Exception as e:
            self.logger.error(f"❌ Failed to query bucket: {e}")
            return set()
    
    def get_config_data_sources(self) -> Dict[str, Set[str]]:
        """
        Get all data source names from the configuration file.
        
        Returns:
            Dict mapping group names to sets of data source names
        """
        self.logger.info("📋 Extracting data sources from configuration file...")
        
        config_sources = {}
        total_sources = 0
        
        for group_name, sources in DATA_SOURCE_GROUPS.items():
            source_names = set(sources.keys())
            config_sources[group_name] = source_names
            total_sources += len(source_names)
            self.logger.debug(f"   {group_name}: {len(source_names)} sources")
        
        self.logger.info(f"✅ Found {total_sources} configured data sources across {len(config_sources)} groups")
        return config_sources
    
    def compare_sources(self) -> Dict[str, Any]:
        """
        Compare bucket sources with configuration sources.
        
        Returns:
            Dict containing comparison results
        """
        self.logger.info("🔄 Starting comparison...")
        
        # Get data from both sources
        bucket_sources = self.get_bucket_data_sources()
        config_sources = self.get_config_data_sources()
        
        # Flatten config sources for comparison
        all_config_sources = set()
        for group_sources in config_sources.values():
            all_config_sources.update(group_sources)
        
        # Perform comparison
        missing_from_bucket = all_config_sources - bucket_sources
        missing_from_config = bucket_sources - all_config_sources
        present_in_both = bucket_sources & all_config_sources
        
        # Analyze missing sources by group
        missing_by_group = {}
        for group_name, group_sources in config_sources.items():
            missing_in_group = group_sources - bucket_sources
            if missing_in_group:
                missing_by_group[group_name] = missing_in_group
        
        results = {
            'bucket_sources': bucket_sources,
            'config_sources': all_config_sources,
            'config_by_group': config_sources,
            'missing_from_bucket': missing_from_bucket,
            'missing_from_config': missing_from_config,
            'present_in_both': present_in_both,
            'missing_by_group': missing_by_group,
            'total_bucket': len(bucket_sources),
            'total_config': len(all_config_sources),
            'total_missing_bucket': len(missing_from_bucket),
            'total_missing_config': len(missing_from_config),
            'total_present_both': len(present_in_both)
        }
        
        self.logger.info("✅ Comparison completed")
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a detailed comparison report.
        
        Args:
            results: Results from compare_sources()
            
        Returns:
            Formatted report string
        """
        report_lines = []
        
        # Header
        report_lines.extend([
            "=" * 80,
            "BUCKET DATA SOURCES COMPARISON REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Schema: {self.schema}",
            f"Bucket: {self.bucket_adapter.bucket_name}",
            ""
        ])
        
        # Summary Statistics
        report_lines.extend([
            "📊 SUMMARY STATISTICS",
            "-" * 40,
            f"Total sources in bucket:        {results['total_bucket']:3d}",
            f"Total sources in config:        {results['total_config']:3d}",
            f"Sources present in both:        {results['total_present_both']:3d}",
            f"Sources missing from bucket:    {results['total_missing_bucket']:3d}",
            f"Sources missing from config:    {results['total_missing_config']:3d}",
            ""
        ])
        
        # Coverage Analysis
        if results['total_config'] > 0:
            coverage_pct = (results['total_present_both'] / results['total_config']) * 100
            report_lines.extend([
                "📈 COVERAGE ANALYSIS",
                "-" * 40,
                f"Bucket coverage of config:      {coverage_pct:.1f}%",
                ""
            ])
        
        # Missing from Bucket (Priority Items)
        if results['missing_from_bucket']:
            report_lines.extend([
                "❌ DATA SOURCES MISSING FROM BUCKET",
                "-" * 40,
                "These are configured but not yet loaded to bucket:",
                ""
            ])
            
            # Group missing sources by category
            if results['missing_by_group']:
                for group_name, missing_sources in results['missing_by_group'].items():
                    if missing_sources:
                        report_lines.append(f"  {group_name.upper()}:")
                        for source in sorted(missing_sources):
                            report_lines.append(f"    • {source}")
                        report_lines.append("")
            else:
                for source in sorted(results['missing_from_bucket']):
                    report_lines.append(f"  • {source}")
                report_lines.append("")
        
        # Missing from Config (Potential New Sources)
        if results['missing_from_config']:
            report_lines.extend([
                "🆕 DATA SOURCES IN BUCKET BUT NOT IN CONFIG",
                "-" * 40,
                "These exist in bucket but are not configured:",
                ""
            ])
            for source in sorted(results['missing_from_config']):
                report_lines.append(f"  • {source}")
            report_lines.append("")
        
        # Successfully Loaded Sources
        if results['present_in_both']:
            report_lines.extend([
                "✅ DATA SOURCES PRESENT IN BOTH",
                "-" * 40,
                f"These {len(results['present_in_both'])} sources are successfully loaded:",
                ""
            ])
            
            # Group by config category for better organization
            present_by_group = {}
            for group_name, group_sources in results['config_by_group'].items():
                present_in_group = group_sources & results['present_in_both']
                if present_in_group:
                    present_by_group[group_name] = present_in_group
            
            if present_by_group:
                for group_name, present_sources in present_by_group.items():
                    report_lines.append(f"  {group_name.upper()}:")
                    for source in sorted(present_sources):
                        report_lines.append(f"    • {source}")
                    report_lines.append("")
            else:
                for source in sorted(results['present_in_both']):
                    report_lines.append(f"  • {source}")
                report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "💡 RECOMMENDATIONS",
            "-" * 40
        ])
        
        if results['missing_from_bucket']:
            report_lines.extend([
                f"1. Load {len(results['missing_from_bucket'])} missing data sources to bucket:",
                "   Run the data pipeline for the missing sources listed above.",
                ""
            ])
        
        if results['missing_from_config']:
            report_lines.extend([
                f"2. Review {len(results['missing_from_config'])} unconfigured sources in bucket:",
                "   These may be test data, deprecated sources, or new sources",
                "   that need to be added to the configuration.",
                ""
            ])
        
        if not results['missing_from_bucket'] and not results['missing_from_config']:
            report_lines.extend([
                "🎉 Perfect sync! All configured sources are in bucket,",
                "   and all bucket sources are configured.",
                ""
            ])
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def run_comparison(self, save_report: bool = True) -> Dict[str, Any]:
        """
        Run the complete comparison and optionally save report.
        
        Args:
            save_report: Whether to save the report to a file
            
        Returns:
            Comparison results
        """
        self.logger.info("🚀 Starting bucket data sources comparison...")
        
        try:
            # Perform comparison
            results = self.compare_sources()
            
            # Generate and display report
            report = self.generate_report(results)
            print(report)
            
            # Save report if requested
            if save_report:
                # Use domain-based subfolder for organization
                # TODO: If generating multiple artifact types (CSV + MD + JSON), consider using
                # timestamped subfolders: Path("reports/bucket_comparison") / f"comparison_{timestamp}"
                # This groups related artifacts together (see scripts/analyze_pbp_odds_data_v4.py)
                domain_folder = Path('reports') / 'bucket_comparison'
                domain_folder.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"bucket_comparison_report_{timestamp}.txt"
                output_path = domain_folder / filename
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                self.logger.info(f"📄 Report saved to: {output_path}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Comparison failed: {e}")
            raise


def main():
    """
    Main function to run the comparison.
    """
    print("🔍 Bucket Data Sources Comparison Tool")
    print("=" * 50)
    
    try:
        # Create and run comparison
        comparison = BucketDataSourceComparison(schema='raw_nflfastr')
        results = comparison.run_comparison(save_report=True)
        
        # Exit with appropriate code
        if results['missing_from_bucket']:
            print(f"\n⚠️  {len(results['missing_from_bucket'])} data sources are missing from bucket")
            sys.exit(1)  # Non-zero exit for missing sources
        else:
            print("\n✅ All configured data sources are present in bucket")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Comparison cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Comparison failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()