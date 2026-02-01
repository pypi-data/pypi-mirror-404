#!/usr/bin/env python3
"""
Enhanced Code Analysis Script for Python Projects

This script provides comprehensive code analysis including:
- Detailed LOC metrics (total, code, comments, blank lines, ratios)
- God Class detection with class metrics
- Code smell detection (complexity, nesting, long functions)
- Python-specific quality metrics
- Project-level summary statistics and health scoring
- Formatted output with color coding and visual indicators

Follows CODING_GUIDE.md principles for identifying refactoring candidates.
"""

import os
import ast
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


# ============================================================================
# CONFIGURATION & THRESHOLDS
# ============================================================================

class Severity(Enum):
    """Severity levels for code issues."""
    HEALTHY = "green"
    WARNING = "yellow"
    CRITICAL = "red"


@dataclass
class Thresholds:
    """Configurable thresholds for code analysis."""
    # File size thresholds (from CODING_GUIDE.md)
    file_warning_lines: int = 500  # Yellow flag
    file_critical_lines: int = 1000  # Red flag
    
    # Function complexity thresholds
    function_warning_lines: int = 50
    function_critical_lines: int = 100
    max_nesting_depth: int = 4
    max_cyclomatic_complexity: int = 10
    
    # Class thresholds (God Class detection)
    class_warning_lines: int = 300
    class_critical_lines: int = 500
    max_methods_per_class: int = 20
    max_instance_variables: int = 15
    max_dependencies: int = 10
    
    # Code quality thresholds
    min_comment_ratio: float = 0.1  # 10% comments minimum
    max_imports_per_file: int = 30
    max_function_params: int = 7


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class LOCMetrics:
    """Lines of code metrics for a file."""
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: float = 0.0  # Float to handle inline comments
    blank_lines: int = 0
    docstring_lines: int = 0
    
    @property
    def comment_ratio(self) -> float:
        """Calculate code-to-comment ratio."""
        if self.code_lines == 0:
            return 0.0
        return self.comment_lines / self.code_lines
    
    @property
    def code_density(self) -> float:
        """Calculate percentage of actual code vs total lines."""
        if self.total_lines == 0:
            return 0.0
        return self.code_lines / self.total_lines


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""
    name: str
    line_number: int
    lines: int
    params: int
    nesting_depth: int
    cyclomatic_complexity: int
    
    def get_severity(self, thresholds: Thresholds) -> Severity:
        """Determine severity level for this function."""
        if (self.lines >= thresholds.function_critical_lines or
            self.nesting_depth > thresholds.max_nesting_depth or
            self.cyclomatic_complexity > thresholds.max_cyclomatic_complexity):
            return Severity.CRITICAL
        elif self.lines >= thresholds.function_warning_lines:
            return Severity.WARNING
        return Severity.HEALTHY


@dataclass
class ClassMetrics:
    """Metrics for a single class (God Class detection)."""
    name: str
    line_number: int
    lines: int
    methods: int
    instance_vars: int
    dependencies: int
    inheritance_depth: int
    base_classes: List[str] = field(default_factory=list)
    
    def get_severity(self, thresholds: Thresholds) -> Severity:
        """Determine if this is a God Class."""
        god_class_score = 0
        
        if self.lines >= thresholds.class_critical_lines:
            god_class_score += 3
        elif self.lines >= thresholds.class_warning_lines:
            god_class_score += 1
            
        if self.methods > thresholds.max_methods_per_class:
            god_class_score += 2
            
        if self.instance_vars > thresholds.max_instance_variables:
            god_class_score += 2
            
        if self.dependencies > thresholds.max_dependencies:
            god_class_score += 1
        
        if god_class_score >= 5:
            return Severity.CRITICAL
        elif god_class_score >= 2:
            return Severity.WARNING
        return Severity.HEALTHY
    
    def get_issues(self, thresholds: Thresholds) -> List[str]:
        """Get list of specific issues with this class."""
        issues = []
        if self.lines >= thresholds.class_critical_lines:
            issues.append(f"Excessive length: {self.lines} lines")
        if self.methods > thresholds.max_methods_per_class:
            issues.append(f"Too many methods: {self.methods}")
        if self.instance_vars > thresholds.max_instance_variables:
            issues.append(f"Too many instance variables: {self.instance_vars}")
        if self.dependencies > thresholds.max_dependencies:
            issues.append(f"Too many dependencies: {self.dependencies}")
        return issues


@dataclass
class FileAnalysis:
    """Complete analysis results for a single file."""
    path: str
    loc_metrics: LOCMetrics
    functions: List[FunctionMetrics] = field(default_factory=list)
    classes: List[ClassMetrics] = field(default_factory=list)
    imports: int = 0
    import_names: List[str] = field(default_factory=list)
    code_hashes: Set[str] = field(default_factory=set)
    parse_error: Optional[str] = None
    
    def get_severity(self, thresholds: Thresholds) -> Severity:
        """Determine overall file severity."""
        if self.loc_metrics.total_lines >= thresholds.file_critical_lines:
            return Severity.CRITICAL
        elif self.loc_metrics.total_lines >= thresholds.file_warning_lines:
            return Severity.WARNING
        return Severity.HEALTHY
    
    def get_issues(self, thresholds: Thresholds) -> List[str]:
        """Get list of all issues in this file."""
        issues = []
        
        # File size issues
        if self.loc_metrics.total_lines >= thresholds.file_critical_lines:
            issues.append(f"God File: {self.loc_metrics.total_lines} lines (>1000)")
        elif self.loc_metrics.total_lines >= thresholds.file_warning_lines:
            issues.append(f"Large file: {self.loc_metrics.total_lines} lines (>500)")
        
        # Comment ratio issues
        if self.loc_metrics.comment_ratio < thresholds.min_comment_ratio:
            issues.append(f"Low comment ratio: {self.loc_metrics.comment_ratio:.1%}")
        
        # Import issues
        if self.imports > thresholds.max_imports_per_file:
            issues.append(f"Too many imports: {self.imports}")
        
        # God Classes
        god_classes = [c for c in self.classes if c.get_severity(thresholds) == Severity.CRITICAL]
        if god_classes:
            issues.append(f"God Classes: {', '.join(c.name for c in god_classes)}")
        
        # Complex functions
        complex_funcs = [f for f in self.functions if f.get_severity(thresholds) == Severity.CRITICAL]
        if complex_funcs:
            issues.append(f"Complex functions: {', '.join(f.name for f in complex_funcs)}")
        
        return issues


@dataclass
class ModuleAnalysis:
    """Analysis results for a module."""
    name: str
    files: List[FileAnalysis] = field(default_factory=list)
    
    @property
    def total_lines(self) -> int:
        return sum(f.loc_metrics.total_lines for f in self.files)
    
    @property
    def total_code_lines(self) -> int:
        return sum(f.loc_metrics.code_lines for f in self.files)
    
    @property
    def avg_comment_ratio(self) -> float:
        if not self.files:
            return 0.0
        return sum(f.loc_metrics.comment_ratio for f in self.files) / len(self.files)


# ============================================================================
# AST ANALYSIS
# ============================================================================

class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor for analyzing Python code structure."""
    
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.functions: List[FunctionMetrics] = []
        self.classes: List[ClassMetrics] = []
        self.imports: int = 0
        self.import_names: List[str] = []
        self.current_class: Optional[str] = None
        self.current_class_vars: Set[str] = set()
        self.current_class_deps: Set[str] = set()
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Analyze function definitions."""
        # Calculate function metrics
        end_line = self._get_end_line(node)
        lines = end_line - node.lineno + 1
        params = len(node.args.args)
        nesting = self._calculate_nesting_depth(node)
        complexity = self._calculate_cyclomatic_complexity(node)
        
        func_metrics = FunctionMetrics(
            name=node.name,
            line_number=node.lineno,
            lines=lines,
            params=params,
            nesting_depth=nesting,
            cyclomatic_complexity=complexity
        )
        self.functions.append(func_metrics)
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Analyze class definitions."""
        prev_class = self.current_class
        prev_vars = self.current_class_vars
        prev_deps = self.current_class_deps
        
        self.current_class = node.name
        self.current_class_vars = set()
        self.current_class_deps = set()
        
        # Count methods
        methods = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
        
        # Get base classes
        base_classes = [self._get_name(base) for base in node.bases]
        
        # Calculate inheritance depth (simplified)
        inheritance_depth = 1 if base_classes else 0
        
        # Visit class body to collect instance variables and dependencies
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._analyze_function_for_class_metrics(item)
        
        # Calculate class metrics
        end_line = self._get_end_line(node)
        lines = end_line - node.lineno + 1
        
        class_metrics = ClassMetrics(
            name=node.name,
            line_number=node.lineno,
            lines=lines,
            methods=methods,
            instance_vars=len(self.current_class_vars),
            dependencies=len(self.current_class_deps),
            inheritance_depth=inheritance_depth,
            base_classes=base_classes
        )
        self.classes.append(class_metrics)
        
        # Restore previous class context
        self.current_class = prev_class
        self.current_class_vars = prev_vars
        self.current_class_deps = prev_deps
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Count import statements."""
        self.imports += len(node.names)
        for alias in node.names:
            self.import_names.append(alias.name)
            if self.current_class:
                self.current_class_deps.add(alias.name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Count from-import statements."""
        self.imports += len(node.names)
        module = node.module or ''
        for alias in node.names:
            self.import_names.append(f"{module}.{alias.name}")
            if self.current_class:
                self.current_class_deps.add(module.split('.')[0] if module else alias.name)
        self.generic_visit(node)
    
    def _analyze_function_for_class_metrics(self, node: ast.FunctionDef):
        """Analyze function to extract class-level metrics."""
        for item in ast.walk(node):
            # Look for self.variable assignments
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                            self.current_class_vars.add(target.attr)
    
    def _get_end_line(self, node: ast.AST) -> int:
        """Get the last line number of a node."""
        end_line = getattr(node, 'lineno', 0)
        for child in ast.walk(node):
            if hasattr(child, 'lineno'):
                end_line = max(end_line, getattr(child, 'lineno', 0))
        return end_line
    
    def _get_name(self, node: ast.AST) -> str:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth in a function."""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity (simplified)."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Add 1 for each decision point
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity


# ============================================================================
# FILE ANALYSIS
# ============================================================================

def analyze_file(file_path: str, thresholds: Thresholds) -> FileAnalysis:
    """Perform comprehensive analysis on a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Calculate LOC metrics
        loc_metrics = calculate_loc_metrics(lines)
        
        # Parse AST for deeper analysis
        source = ''.join(lines)
        try:
            tree = ast.parse(source)
            analyzer = CodeAnalyzer(lines)
            analyzer.visit(tree)
            
            # Detect duplicate code (simple hash-based)
            code_hashes = detect_duplicate_code_blocks(lines)
            
            return FileAnalysis(
                path=file_path,
                loc_metrics=loc_metrics,
                functions=analyzer.functions,
                classes=analyzer.classes,
                imports=analyzer.imports,
                import_names=analyzer.import_names,
                code_hashes=code_hashes
            )
        except SyntaxError as e:
            return FileAnalysis(
                path=file_path,
                loc_metrics=loc_metrics,
                parse_error=str(e)
            )
    
    except Exception as e:
        return FileAnalysis(
            path=file_path,
            loc_metrics=LOCMetrics(),
            parse_error=str(e)
        )


def calculate_loc_metrics(lines: List[str]) -> LOCMetrics:
    """Calculate detailed LOC metrics for source lines."""
    metrics = LOCMetrics()
    metrics.total_lines = len(lines)
    
    in_docstring = False
    docstring_char = None
    
    for line in lines:
        stripped = line.strip()
        
        # Check for blank lines
        if not stripped:
            metrics.blank_lines += 1
            continue
        
        # Check for docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            docstring_char = stripped[:3]
            if stripped.count(docstring_char) >= 2:
                # Single-line docstring
                metrics.docstring_lines += 1
                metrics.comment_lines += 1
            else:
                # Start of multi-line docstring
                in_docstring = True
                metrics.docstring_lines += 1
                metrics.comment_lines += 1
            continue
        
        if in_docstring:
            metrics.docstring_lines += 1
            metrics.comment_lines += 1
            if docstring_char and docstring_char in stripped:
                in_docstring = False
            continue
        
        # Check for comments
        if stripped.startswith('#'):
            metrics.comment_lines += 1
            continue
        
        # Otherwise it's code
        metrics.code_lines += 1
        
        # Check for inline comments
        if '#' in stripped:
            metrics.comment_lines += 0.5  # Count inline comments as half
    
    return metrics


def detect_duplicate_code_blocks(lines: List[str], min_lines: int = 5) -> Set[str]:
    """Detect potential duplicate code blocks using hashing."""
    code_hashes = set()
    
    # Extract code-only lines (no comments/blanks)
    code_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            # Remove inline comments
            code_part = stripped.split('#')[0].strip()
            if code_part:
                code_lines.append(code_part)
    
    # Create sliding window hashes
    for i in range(len(code_lines) - min_lines + 1):
        block = '\n'.join(code_lines[i:i+min_lines])
        block_hash = hashlib.md5(block.encode()).hexdigest()
        code_hashes.add(block_hash)
    
    return code_hashes


# ============================================================================
# MODULE & PROJECT ANALYSIS
# ============================================================================

def analyze_module(module_path: str, thresholds: Thresholds) -> ModuleAnalysis:
    """Analyze all Python files in a module."""
    module_name = os.path.basename(module_path)
    files = []
    
    if not os.path.exists(module_path):
        return ModuleAnalysis(name=module_name, files=[])
    
    for root, dirs, filenames in os.walk(module_path):
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path).replace('\\', '/')
                analysis = analyze_file(file_path, thresholds)
                analysis.path = rel_path
                files.append(analysis)
    
    # Sort by total lines
    files.sort(key=lambda x: x.loc_metrics.total_lines)
    
    return ModuleAnalysis(name=module_name, files=files)


def get_project_modules() -> List[str]:
    """Automatically detect Python modules in the current directory."""
    modules = []
    current_dir = Path('.')
    
    for item in current_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if directory contains Python files
            python_files = list(item.rglob('*.py'))
            if python_files:
                modules.append(item.name)
    
    return sorted(modules)


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

class ColorFormatter:
    """ANSI color codes for terminal output."""
    # Colors
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    
    # Styles
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    @classmethod
    def colorize(cls, text: str, severity: Severity) -> str:
        """Apply color based on severity."""
        color_map = {
            Severity.HEALTHY: cls.GREEN,
            Severity.WARNING: cls.YELLOW,
            Severity.CRITICAL: cls.RED
        }
        color = color_map.get(severity, cls.RESET)
        return f"{color}{text}{cls.RESET}"
    
    @classmethod
    def header(cls, text: str) -> str:
        """Format as header."""
        return f"{cls.BOLD}{cls.CYAN}{text}{cls.RESET}"
    
    @classmethod
    def subheader(cls, text: str) -> str:
        """Format as subheader."""
        return f"{cls.BOLD}{text}{cls.RESET}"


def format_module_output(module: ModuleAnalysis, thresholds: Thresholds, detailed: bool = False) -> str:
    """Format output for a single module."""
    cf = ColorFormatter
    
    if not module.files:
        return f"{cf.header(module.name.upper() + ' MODULE:')}\nNo Python files found\n"
    
    output = f"{cf.header(module.name.upper() + ' MODULE:')}\n"
    
    for file in module.files:
        severity = file.get_severity(thresholds)
        loc = file.loc_metrics.total_lines
        
        # Format line with severity indicator
        indicator = "🔴" if severity == Severity.CRITICAL else "🟡" if severity == Severity.WARNING else "🟢"
        line_str = f"{loc:5d}"
        colored_line = cf.colorize(line_str, severity)
        
        output += f"{indicator} {colored_line} ./{file.path}\n"
        
        # Add detailed metrics if requested
        if detailed and (severity != Severity.HEALTHY or file.parse_error):
            if file.parse_error:
                output += f"         ⚠️  Parse error: {file.parse_error}\n"
            else:
                issues = file.get_issues(thresholds)
                if issues:
                    for issue in issues:
                        output += f"         ⚠️  {issue}\n"
    
    total = module.total_lines
    output += f"{cf.subheader(f'{total:5d} total')}\n"
    
    return output


def format_god_class_report(modules: List[ModuleAnalysis], thresholds: Thresholds) -> str:
    """Generate God Class detection report."""
    cf = ColorFormatter
    output = f"\n{cf.header('='*80)}\n"
    output += f"{cf.header('GOD CLASS DETECTION REPORT')}\n"
    output += f"{cf.header('='*80)}\n\n"
    
    all_classes = []
    for module in modules:
        for file in module.files:
            for cls in file.classes:
                all_classes.append((module.name, file.path, cls))
    
    # Filter and sort by severity
    critical_classes = [(m, f, c) for m, f, c in all_classes if c.get_severity(thresholds) == Severity.CRITICAL]
    warning_classes = [(m, f, c) for m, f, c in all_classes if c.get_severity(thresholds) == Severity.WARNING]
    
    if critical_classes:
        output += f"{cf.colorize('🔴 CRITICAL - God Classes (Immediate Refactoring Needed):', Severity.CRITICAL)}\n\n"
        for module_name, file_path, cls in sorted(critical_classes, key=lambda x: x[2].lines, reverse=True):
            output += f"  Class: {cf.BOLD}{cls.name}{cf.RESET}\n"
            output += f"  File:  {file_path}\n"
            output += f"  Lines: {cls.lines} | Methods: {cls.methods} | Instance Vars: {cls.instance_vars}\n"
            issues = cls.get_issues(thresholds)
            for issue in issues:
                output += f"    ⚠️  {issue}\n"
            output += "\n"
    
    if warning_classes:
        output += f"{cf.colorize('🟡 WARNING - Large Classes (Monitor for Growth):', Severity.WARNING)}\n\n"
        for module_name, file_path, cls in sorted(warning_classes, key=lambda x: x[2].lines, reverse=True)[:10]:
            output += f"  {cls.name}: {cls.lines} lines, {cls.methods} methods ({file_path})\n"
        output += "\n"
    
    if not critical_classes and not warning_classes:
        output += f"{cf.colorize('✅ No God Classes detected!', Severity.HEALTHY)}\n\n"
    
    return output


def format_summary_statistics(modules: List[ModuleAnalysis], thresholds: Thresholds) -> str:
    """Generate project-level summary statistics."""
    cf = ColorFormatter
    
    # Calculate totals
    total_files = sum(len(m.files) for m in modules)
    total_lines = sum(m.total_lines for m in modules)
    total_code = sum(m.total_code_lines for m in modules)
    
    # Get all files
    all_files = []
    for module in modules:
        all_files.extend(module.files)
    
    # Calculate averages
    avg_file_size = total_lines / total_files if total_files > 0 else 0
    avg_comment_ratio = sum(f.loc_metrics.comment_ratio for f in all_files) / total_files if total_files > 0 else 0
    
    # Get top 10 largest files
    largest_files = sorted(all_files, key=lambda x: x.loc_metrics.total_lines, reverse=True)[:10]
    
    # Get all classes and find largest
    all_classes = []
    for module in modules:
        for file in module.files:
            for cls in file.classes:
                all_classes.append((file.path, cls))
    largest_classes = sorted(all_classes, key=lambda x: x[1].lines, reverse=True)[:10]
    
    # Count issues
    critical_files = [f for f in all_files if f.get_severity(thresholds) == Severity.CRITICAL]
    warning_files = [f for f in all_files if f.get_severity(thresholds) == Severity.WARNING]
    
    # Calculate health score
    health_score = calculate_health_score(all_files, thresholds)
    
    # Format output
    output = f"\n{cf.header('='*80)}\n"
    output += f"{cf.header('PROJECT SUMMARY STATISTICS')}\n"
    output += f"{cf.header('='*80)}\n\n"
    
    output += f"{cf.subheader('Overall Metrics:')}\n"
    output += f"  Total Files:        {total_files:,}\n"
    output += f"  Total Lines:        {total_lines:,}\n"
    output += f"  Total Code Lines:   {total_code:,}\n"
    output += f"  Average File Size:  {avg_file_size:.0f} lines\n"
    output += f"  Avg Comment Ratio:  {avg_comment_ratio:.1%}\n"
    output += f"  Health Score:       {cf.colorize(f'{health_score}/100', get_health_severity(health_score))}\n\n"
    
    output += f"{cf.subheader('Top 10 Largest Files:')}\n"
    for i, file in enumerate(largest_files, 1):
        severity = file.get_severity(thresholds)
        indicator = "🔴" if severity == Severity.CRITICAL else "🟡" if severity == Severity.WARNING else "🟢"
        output += f"  {i:2d}. {indicator} {file.loc_metrics.total_lines:5d} lines - {file.path}\n"
    output += "\n"
    
    if largest_classes:
        output += f"{cf.subheader('Top 10 Largest Classes:')}\n"
        for i, (file_path, cls) in enumerate(largest_classes, 1):
            severity = cls.get_severity(thresholds)
            indicator = "🔴" if severity == Severity.CRITICAL else "🟡" if severity == Severity.WARNING else "🟢"
            output += f"  {i:2d}. {indicator} {cls.lines:5d} lines - {cls.name} ({file_path})\n"
        output += "\n"
    
    output += f"{cf.subheader('Issues Summary:')}\n"
    output += f"  {cf.colorize(f'🔴 Critical Files: {len(critical_files)}', Severity.CRITICAL)}\n"
    output += f"  {cf.colorize(f'🟡 Warning Files:  {len(warning_files)}', Severity.WARNING)}\n"
    output += f"  {cf.colorize(f'🟢 Healthy Files:  {total_files - len(critical_files) - len(warning_files)}', Severity.HEALTHY)}\n\n"
    
    if critical_files:
        output += f"{cf.subheader('Critical Files Requiring Immediate Attention:')}\n"
        for file in critical_files[:5]:
            output += f"  🔴 {file.path} ({file.loc_metrics.total_lines} lines)\n"
            for issue in file.get_issues(thresholds)[:3]:
                output += f"      - {issue}\n"
        if len(critical_files) > 5:
            output += f"  ... and {len(critical_files) - 5} more\n"
        output += "\n"
    
    return output


def calculate_health_score(files: List[FileAnalysis], thresholds: Thresholds) -> int:
    """Calculate overall project health score (0-100)."""
    if not files:
        return 100
    
    score = 100
    
    # Penalize for large files
    critical_files = sum(1 for f in files if f.get_severity(thresholds) == Severity.CRITICAL)
    warning_files = sum(1 for f in files if f.get_severity(thresholds) == Severity.WARNING)
    
    score -= (critical_files / len(files)) * 30
    score -= (warning_files / len(files)) * 15
    
    # Penalize for low comment ratios
    low_comment_files = sum(1 for f in files if f.loc_metrics.comment_ratio < thresholds.min_comment_ratio)
    score -= (low_comment_files / len(files)) * 10
    
    # Penalize for God Classes
    god_classes = sum(1 for f in files for c in f.classes if c.get_severity(thresholds) == Severity.CRITICAL)
    score -= min(god_classes * 5, 20)
    
    return max(0, int(score))


def get_health_severity(score: int) -> Severity:
    """Get severity level for health score."""
    if score >= 80:
        return Severity.HEALTHY
    elif score >= 60:
        return Severity.WARNING
    return Severity.CRITICAL


# ============================================================================
# MARKDOWN EXPORT
# ============================================================================

def strip_ansi_codes(text: str) -> str:
    """
    Remove ANSI color codes for markdown export.
    
    Args:
        text: Text containing ANSI escape sequences
        
    Returns:
        str: Clean text without ANSI codes
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def export_markdown_report(output: str, output_dir: str = 'reports/codebase_health') -> str:
    """
    Export analysis report to markdown file.
    
    Follows the same pattern as other reporters in the codebase
    (feature_reporter.py, training_reporter.py, backtest_reporter.py).
    
    Args:
        output: Report content as string
        output_dir: Directory to save report (default: 'reports/codebase_health' for domain-based organization)
    
    Note:
        TODO: If generating multiple artifact types (CSV + MD + JSON), consider using
        timestamped subfolders: 'reports/codebase_health/{timestamp}' to group related artifacts
        together (see scripts/analyze_pbp_odds_data_v4.py for reference)
        
    Returns:
        str: Path to generated report
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f'codebase_health_analysis_{timestamp}.md'
    report_path = Path(output_dir) / report_filename
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Write report
    report_path.write_text(output, encoding='utf-8')
    
    print(f"\n📊 Report saved: {report_path}")
    
    return str(report_path)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function to run comprehensive code analysis."""
    cf = ColorFormatter
    thresholds = Thresholds()
    
    # Collect all output sections
    output_sections = []
    
    output_sections.append(f"{cf.header('='*80)}")
    output_sections.append(f"{cf.header('COMPREHENSIVE CODE ANALYSIS REPORT')}")
    output_sections.append(f"{cf.header('='*80)}\n")
    
    # Get all modules
    modules = get_project_modules()
    
    if not modules:
        output_sections.append("No Python modules found in the current directory.")
        full_output = '\n'.join(output_sections)
        print(full_output)
        return
    
    # Analyze all modules
    output_sections.append(f"{cf.subheader('Analyzing modules...')}\n")
    module_analyses = []
    
    for module_name in modules:
        module_analysis = analyze_module(module_name, thresholds)
        module_analyses.append(module_analysis)
        
        # Collect module output
        module_output = format_module_output(module_analysis, thresholds, detailed=False)
        output_sections.append(module_output)
    
    # Collect God Class report
    output_sections.append(format_god_class_report(module_analyses, thresholds))
    
    # Collect summary statistics
    output_sections.append(format_summary_statistics(module_analyses, thresholds))
    
    # Collect recommendations
    output_sections.append(f"{cf.header('='*80)}")
    output_sections.append(f"{cf.header('RECOMMENDATIONS (Based on CODING_GUIDE.md)')}")
    output_sections.append(f"{cf.header('='*80)}\n")
    output_sections.append(f"{cf.subheader('Refactoring Priority:')}\n")
    output_sections.append(f"  🔴 {cf.BOLD}HIGH{cf.RESET}   - Files >1000 lines: Use Facade Pattern or split into modules")
    output_sections.append(f"  🟡 {cf.BOLD}MEDIUM{cf.RESET} - Files >500 lines: Monitor and consider splitting")
    output_sections.append(f"  🟢 {cf.BOLD}LOW{cf.RESET}    - Files <500 lines: Healthy, maintain current structure\n")
    output_sections.append(f"{cf.subheader('God Class Detection:')}\n")
    output_sections.append(f"  - Classes >500 lines with >20 methods are God Classes")
    output_sections.append(f"  - Refactor by splitting responsibilities into smaller classes")
    output_sections.append(f"  - Follow Single Responsibility Principle\n")
    output_sections.append(f"{cf.subheader('Code Quality:')}\n")
    output_sections.append(f"  - Maintain comment ratio >10%")
    output_sections.append(f"  - Keep functions <50 lines")
    output_sections.append(f"  - Limit nesting depth to 4 levels")
    output_sections.append(f"  - Keep cyclomatic complexity <10\n")
    
    # Combine all sections
    full_output = '\n'.join(output_sections)
    
    # Print to console with colors
    print(full_output)
    
    # Export to markdown (strip ANSI color codes)
    md_output = strip_ansi_codes(full_output)
    # Use default domain-based output_dir (reports/codebase_health)
    export_markdown_report(md_output)


if __name__ == "__main__":
    main()
