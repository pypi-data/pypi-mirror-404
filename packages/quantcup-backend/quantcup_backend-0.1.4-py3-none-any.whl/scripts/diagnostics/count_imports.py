#!/usr/bin/env python3
"""
Import Coupling Analyzer for Python Projects

This script analyzes import coupling between folders, helping identify
tight coupling and potential refactoring opportunities.
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


def extract_imports_from_file(file_path: str) -> List[Tuple[str, str]]:
    """
    Extract all import statements from a Python file.
    
    Returns:
        List of tuples (module_path, imported_items)
        - For 'from X import Y, Z': ('X', 'Y, Z')
        - For 'import X': ('X', '')
    """
    imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Remove comments and strings to avoid false matches
        # This is a simple approach - doesn't handle all edge cases but works for most code
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove inline comments (simple approach)
            if '#' in line:
                line = line[:line.index('#')]
            cleaned_lines.append(line)
        content = '\n'.join(cleaned_lines)
        
        # Match: from module import ...
        # Handle both single-line and multi-line imports
        # Pattern: from X import (anything until we hit a line that doesn't continue)
        from_pattern = r'^\s*from\s+([\w.]+)\s+import\s+(.+?)(?=^\s*(?:from|import|class|def|@|$))'
        from_imports = re.findall(from_pattern, content, re.MULTILINE | re.DOTALL)
        
        for module, items in from_imports:
            # Clean up items: remove parentheses, newlines, extra spaces
            items_clean = items.replace('(', '').replace(')', '').replace('\n', ' ')
            # Normalize whitespace
            items_clean = ' '.join(items_clean.split())
            imports.append((module, items_clean))
        
        # Match: import module
        direct_imports = re.findall(r'^\s*import\s+([\w.]+)', content, re.MULTILINE)
        for module in direct_imports:
            imports.append((module, ''))
        
    except Exception as e:
        pass  # Skip files that can't be read
    
    return imports


def find_python_files(directory: str) -> List[str]:
    """Find all Python files in a directory recursively."""
    python_files = []
    
    if not os.path.exists(directory):
        return python_files
    
    for root, dirs, files in os.walk(directory):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', '.venv'}]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    
    return python_files


def normalize_module_path(import_path: str, source_folder: str) -> str:
    """Normalize import path to folder-based module name."""
    # Convert relative imports to absolute
    parts = import_path.split('.')
    
    # Get the root module (first part)
    if parts:
        return parts[0]
    
    return import_path


def categorize_import(import_path: str, imported_items: str, target_folder: str) -> str:
    """
    Categorize import by type for better analysis.
    
    Categories:
    - 'logging': Logging infrastructure
    - 'config': Configuration constants
    - 'data_layer': Database operations and adapters
    - 'domain': Domain logic and models
    - 'utility': Utility functions
    - 'other': Uncategorized
    
    Args:
        import_path: Full import path (e.g., 'commonv2.core.config')
        imported_items: What's being imported (e.g., 'get_logger' or 'Environment, DatabasePrefixes')
        target_folder: Target folder name (e.g., 'commonv2')
        
    Returns:
        Category string
    """
    # Combine path and items for comprehensive matching
    combined = f"{import_path} {imported_items}".lower()
    
    # Logging patterns - check both path and imported items
    if any(x in combined for x in ['logging', 'get_logger', 'setup_logger']):
        return 'logging'
    
    # Config patterns - check both path and imported items
    if 'config' in combined or any(x.lower() in combined for x in [
        'environment', 'databaseprefixes', 'transformnames', 'schemanames', 'databaseconfig'
    ]):
        return 'config'
    
    # Data layer patterns
    if any(x in combined for x in [
        '_data', 'database', 'adapter', 'schema_detector', 'loading_strategies',
        'execute_incremental_load', 'execute_full_refresh'
    ]):
        return 'data_layer'
    
    # Domain patterns
    if 'domain' in combined or any(x in combined for x in [
        'get_schedule', 'get_games', 'get_upcoming_games', 'get_all_teams',
        'validate_team', 'validate_schedule'
    ]):
        return 'domain'
    
    # Utility patterns
    if any(x in combined for x in ['utils', 'helpers', 'apply_cleaning', 'validation', 'validate_dataframe']):
        return 'utility'
    
    return 'other'


def count_imports_between_folders(source_folder: str, target_folder: str) -> Dict:
    """
    Count imports from source_folder to target_folder with categorization.
    
    Returns:
        Dict with import count, files involved, specific imports, and categories
    """
    source_name = os.path.basename(source_folder.rstrip('/'))
    target_name = os.path.basename(target_folder.rstrip('/'))
    
    import_count = 0
    files_with_imports = []
    specific_imports = defaultdict(int)
    categories = defaultdict(int)  # Track by category
    category_details = defaultdict(list)  # Track imports per category
    
    python_files = find_python_files(source_folder)
    
    for py_file in python_files:
        imports = extract_imports_from_file(py_file)
        file_has_imports = False
        
        for module_path, imported_items in imports:
            # Check if import starts with target folder name
            root_module = normalize_module_path(module_path, source_folder)
            
            if root_module == target_name:
                import_count += 1
                # Create a readable import string for tracking
                if imported_items:
                    import_str = f"{module_path} ({imported_items})"
                else:
                    import_str = module_path
                specific_imports[import_str] += 1
                file_has_imports = True
                
                # Categorize the import using both path and items
                category = categorize_import(module_path, imported_items, target_name)
                categories[category] += 1
                category_details[category].append(import_str)
        
        if file_has_imports:
            rel_path = os.path.relpath(py_file).replace('\\', '/')
            files_with_imports.append(rel_path)
    
    return {
        'count': import_count,
        'files': files_with_imports,
        'specific_imports': dict(specific_imports),
        'unique_files': len(files_with_imports),
        'categories': dict(categories),
        'category_details': dict(category_details)
    }


def analyze_coupling(folder_a: str, folder_b: str) -> Dict:
    """Analyze bidirectional coupling between two folders."""
    a_to_b = count_imports_between_folders(folder_a, folder_b)
    b_to_a = count_imports_between_folders(folder_b, folder_a)
    
    folder_a_name = os.path.basename(folder_a.rstrip('/'))
    folder_b_name = os.path.basename(folder_b.rstrip('/'))
    
    is_bidirectional = a_to_b['count'] > 0 and b_to_a['count'] > 0
    
    return {
        'folder_a': folder_a_name,
        'folder_b': folder_b_name,
        'a_to_b': a_to_b,
        'b_to_a': b_to_a,
        'bidirectional': is_bidirectional,
        'total_coupling': a_to_b['count'] + b_to_a['count']
    }


def detect_patterns(analysis: Dict) -> Dict[str, bool]:
    """
    Detect architectural patterns in import coupling.
    
    Patterns detected:
    - adapter_pattern: Single file importing domain logic
    - fallback_pattern: Multiple imports from data layer
    - shared_infrastructure: High logging/config imports
    - tight_coupling: High data layer imports
    
    Args:
        analysis: Coupling analysis result
        
    Returns:
        Dict of pattern names to boolean detection
    """
    a_to_b = analysis['a_to_b']
    categories = a_to_b.get('categories', {})
    
    patterns = {
        'adapter_pattern': False,
        'fallback_pattern': False,
        'shared_infrastructure': False,
        'tight_coupling': False
    }
    
    # Adapter pattern: Domain imports concentrated in few files
    if categories.get('domain', 0) > 0:
        domain_files = len([f for f in a_to_b['files']
                           if 'schedule_integration' in f or 'adapter' in f])
        if domain_files <= 2:
            patterns['adapter_pattern'] = True
    
    # Fallback pattern: Multiple data layer imports
    if categories.get('data_layer', 0) >= 5:
        patterns['fallback_pattern'] = True
    
    # Shared infrastructure: High logging/config ratio
    infra_count = categories.get('logging', 0) + categories.get('config', 0)
    if a_to_b['count'] > 0 and infra_count > a_to_b['count'] * 0.7:  # >70% infrastructure
        patterns['shared_infrastructure'] = True
    
    # Tight coupling: High data layer imports
    if categories.get('data_layer', 0) > 10:
        patterns['tight_coupling'] = True
    
    return patterns


def format_coupling_report(analysis: Dict) -> str:
    """Format coupling analysis into a readable report with categories."""
    output = []
    
    folder_a = analysis['folder_a']
    folder_b = analysis['folder_b']
    a_to_b = analysis['a_to_b']
    b_to_a = analysis['b_to_a']
    
    output.append(f"\n{'='*70}")
    output.append(f"Import Coupling Analysis: {folder_a} ↔ {folder_b}")
    output.append(f"{'='*70}\n")
    
    # A to B direction with categories
    if a_to_b['count'] > 0:
        output.append(f"{folder_a} → {folder_b}")
        output.append(f"  Total Imports: {a_to_b['count']}")
        output.append(f"  Files Involved: {a_to_b['unique_files']}")
        
        # NEW: Category breakdown
        if 'categories' in a_to_b:
            output.append(f"\n  Import Categories:")
            for category, count in sorted(a_to_b['categories'].items(),
                                         key=lambda x: x[1], reverse=True):
                percentage = (count / a_to_b['count']) * 100
                output.append(f"    - {category}: {count} ({percentage:.1f}%)")
        
        # Top imports by category
        if 'category_details' in a_to_b:
            output.append(f"\n  Top Imports by Category:")
            for category in ['logging', 'config', 'data_layer', 'domain', 'utility']:
                if category in a_to_b['category_details']:
                    imports = a_to_b['category_details'][category]
                    unique_imports = list(set(imports))[:3]  # Top 3 unique
                    if unique_imports:
                        output.append(f"    {category}:")
                        for imp in unique_imports:
                            output.append(f"      - {imp}")
        
        output.append("")
    else:
        output.append(f"{folder_a} → {folder_b}: No imports\n")
    
    # B to A direction (similar structure)
    if b_to_a['count'] > 0:
        output.append(f"{folder_b} → {folder_a}")
        output.append(f"  Total Imports: {b_to_a['count']}")
        output.append(f"  Files Involved: {b_to_a['unique_files']}")
        
        # NEW: Category breakdown
        if 'categories' in b_to_a:
            output.append(f"\n  Import Categories:")
            for category, count in sorted(b_to_a['categories'].items(),
                                         key=lambda x: x[1], reverse=True):
                percentage = (count / b_to_a['count']) * 100
                output.append(f"    - {category}: {count} ({percentage:.1f}%)")
        
        # Top imports by category
        if 'category_details' in b_to_a:
            output.append(f"\n  Top Imports by Category:")
            for category in ['logging', 'config', 'data_layer', 'domain', 'utility']:
                if category in b_to_a['category_details']:
                    imports = b_to_a['category_details'][category]
                    unique_imports = list(set(imports))[:3]  # Top 3 unique
                    if unique_imports:
                        output.append(f"    {category}:")
                        for imp in unique_imports:
                            output.append(f"      - {imp}")
        
        output.append("")
    else:
        output.append(f"{folder_b} → {folder_a}: No imports\n")
    
    # NEW: Pattern Detection
    patterns = detect_patterns(analysis)
    if any(patterns.values()):
        output.append("Detected Patterns:")
        if patterns['adapter_pattern']:
            output.append("  ✅ Adapter Pattern: Domain logic isolated to specific files")
        if patterns['fallback_pattern']:
            output.append("  ✅ Fallback Pattern: Multiple data layer imports for resilience")
        if patterns['shared_infrastructure']:
            output.append("  ✅ Shared Infrastructure: Mostly logging/config imports")
        if patterns['tight_coupling']:
            output.append("  ⚠️  Tight Coupling: High data layer dependency")
        output.append("")
    
    # Assessment with category-aware recommendations
    output.append("Assessment:")
    if analysis['bidirectional']:
        output.append("  ⚠️  BIDIRECTIONAL coupling detected")
        output.append("  Consider: Are these folders properly separated?")
    elif a_to_b['count'] > 0:
        output.append(f"  ✅ One-way dependency ({folder_a} → {folder_b})")
        
        # Category-specific recommendations
        categories = a_to_b.get('categories', {})
        if categories.get('config', 0) > 0:
            output.append(f"  💡 RECOMMENDATION: Extract {categories['config']} config imports to shared/config.py")
        if categories.get('logging', 0) > 10:
            output.append(f"  💡 RECOMMENDATION: Extract {categories['logging']} logging imports to shared/logging.py")
        if categories.get('domain', 0) > 0:
            output.append(f"  ✅ GOOD: Domain logic ({categories['domain']} imports) uses adapter pattern")
        if categories.get('data_layer', 0) > 5:
            output.append(f"  ⚠️  REVIEW: {categories['data_layer']} data layer imports - consider V3 implementations")
    elif b_to_a['count'] > 0:
        output.append(f"  ✅ One-way dependency ({folder_b} → {folder_a})")
        
        # Category-specific recommendations for reverse direction
        categories = b_to_a.get('categories', {})
        if categories.get('config', 0) > 0:
            output.append(f"  💡 RECOMMENDATION: Extract {categories['config']} config imports to shared/config.py")
        if categories.get('logging', 0) > 10:
            output.append(f"  💡 RECOMMENDATION: Extract {categories['logging']} logging imports to shared/logging.py")
    else:
        output.append("  ✅ No coupling detected")
    
    # Coupling strength
    total = analysis['total_coupling']
    if total > 50:
        output.append(f"  ⚠️  HIGH coupling strength ({total} total imports)")
        output.append("  Consider: Extracting shared abstractions or reducing dependencies")
    elif total > 20:
        output.append(f"  ⚠️  MODERATE coupling strength ({total} total imports)")
        output.append("  Monitor: May need refactoring if it increases")
    elif total > 0:
        output.append(f"  ✅ LOW coupling strength ({total} total imports)")
    
    output.append("")
    
    return '\n'.join(output)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze import coupling between Python folders'
    )
    parser.add_argument(
        'folders',
        nargs='*',
        default=['nflfastRv3', 'commonv2'],
        help='Folders to analyze (default: nflfastRv3 commonv2)'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed import breakdown by file'
    )
    parser.add_argument(
        '--export',
        type=str,
        help='Export results to JSON file'
    )
    parser.add_argument(
        '--threshold',
        type=int,
        default=50,
        help='Coupling threshold for warnings (default: 50)'
    )
    
    return parser.parse_args()


def main():
    """Main function with argument parsing."""
    args = parse_arguments()
    
    print("=== Import Coupling Analyzer ===")
    print()
    
    if len(args.folders) < 2:
        print("Error: Need at least 2 folders to analyze")
        return
    
    folder_a, folder_b = args.folders[0], args.folders[1]
    
    print(f"Analyzing: {folder_a} ↔ {folder_b}")
    analysis = analyze_coupling(folder_a, folder_b)
    report = format_coupling_report(analysis)
    print(report)
    
    # Export if requested
    if args.export:
        with open(args.export, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"Results exported to {args.export}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total coupling strength: {analysis['total_coupling']} imports")
    print(f"Bidirectional: {'Yes ⚠️' if analysis['bidirectional'] else 'No ✅'}")
    
    # Category summary
    if 'categories' in analysis['a_to_b']:
        print(f"\nCategory Breakdown ({folder_a} → {folder_b}):")
        for category, count in sorted(analysis['a_to_b']['categories'].items(),
                                     key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
    
    print()


if __name__ == "__main__":
    main()