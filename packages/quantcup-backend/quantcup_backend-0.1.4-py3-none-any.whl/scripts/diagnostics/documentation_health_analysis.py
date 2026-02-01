#!/usr/bin/env python3
"""
Enhanced Documentation Analysis Script for Markdown Files

This script provides comprehensive documentation analysis including:
- Detailed LOC metrics (total, content, blank lines, code blocks)
- Structure analysis (headers, sections, hierarchy)
- Content quality metrics (code blocks, links, images, tables)
- Documentation smell detection (God Documents, missing structure, excessive sections)
- Project-level summary statistics and health scoring
- Formatted output with color coding and visual indicators

Follows similar principles to codebase_health_analysis.py for identifying documentation issues.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


# ============================================================================
# CONFIGURATION & THRESHOLDS
# ============================================================================

class Severity(Enum):
    """Severity levels for documentation issues."""
    HEALTHY = "green"
    WARNING = "yellow"
    CRITICAL = "red"


@dataclass
class Thresholds:
    """Configurable thresholds for documentation analysis."""
    # File size thresholds
    file_warning_lines: int = 500  # Yellow flag
    file_critical_lines: int = 1000  # Red flag - God Document
    
    # Section thresholds
    section_warning_lines: int = 150
    section_critical_lines: int = 200
    
    # Structure thresholds
    min_headers: int = 3
    max_header_depth: int = 4
    max_h1_count: int = 1  # Should typically have one main title
    
    # Content quality thresholds
    code_block_ratio_warning: float = 0.4  # 40% code blocks
    code_block_ratio_critical: float = 0.6  # 60% code blocks
    min_content_ratio: float = 0.3  # At least 30% should be content
    max_links_per_100_lines: int = 20
    
    # Completeness indicators
    max_todo_markers: int = 5


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class LOCMetrics:
    """Lines of code metrics for a Markdown file."""
    total_lines: int = 0
    content_lines: int = 0  # Non-blank, non-code-block lines
    blank_lines: int = 0
    code_block_lines: int = 0
    
    @property
    def code_block_ratio(self) -> float:
        """Calculate ratio of code blocks to total lines."""
        if self.total_lines == 0:
            return 0.0
        return self.code_block_lines / self.total_lines
    
    @property
    def content_density(self) -> float:
        """Calculate percentage of actual content vs total lines."""
        if self.total_lines == 0:
            return 0.0
        return self.content_lines / self.total_lines


@dataclass
class HeaderInfo:
    """Information about a header."""
    level: int  # 1-6 for H1-H6
    text: str
    line_number: int


@dataclass
class SectionMetrics:
    """Metrics for a documentation section."""
    header: HeaderInfo
    lines: int
    code_blocks: int
    links: int
    
    def get_severity(self, thresholds: Thresholds) -> Severity:
        """Determine severity level for this section."""
        if self.lines >= thresholds.section_critical_lines:
            return Severity.CRITICAL
        elif self.lines >= thresholds.section_warning_lines:
            return Severity.WARNING
        return Severity.HEALTHY


@dataclass
class CodeBlock:
    """Information about a code block."""
    language: str
    line_number: int
    lines: int


@dataclass
class FileAnalysis:
    """Complete analysis results for a single Markdown file."""
    path: str
    loc_metrics: LOCMetrics
    headers: List[HeaderInfo] = field(default_factory=list)
    sections: List[SectionMetrics] = field(default_factory=list)
    code_blocks: List[CodeBlock] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    tables: int = 0
    max_list_depth: int = 0
    has_toc: bool = False
    todo_markers: int = 0
    parse_error: Optional[str] = None
    
    @property
    def header_counts(self) -> Dict[int, int]:
        """Count headers by level."""
        counts = defaultdict(int)
        for header in self.headers:
            counts[header.level] += 1
        return dict(counts)
    
    @property
    def max_header_depth(self) -> int:
        """Get maximum header depth."""
        if not self.headers:
            return 0
        return max(h.level for h in self.headers)
    
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
            issues.append(f"God Document: {self.loc_metrics.total_lines} lines (>1000)")
        elif self.loc_metrics.total_lines >= thresholds.file_warning_lines:
            issues.append(f"Large document: {self.loc_metrics.total_lines} lines (>500)")
        
        # Structure issues
        if len(self.headers) < thresholds.min_headers:
            issues.append(f"Missing structure: only {len(self.headers)} headers")
        
        h1_count = self.header_counts.get(1, 0)
        if h1_count > thresholds.max_h1_count:
            issues.append(f"Multiple H1 headers: {h1_count} (should be 1)")
        elif h1_count == 0:
            issues.append("Missing H1 header (main title)")
        
        if self.max_header_depth > thresholds.max_header_depth:
            issues.append(f"Excessive header depth: H{self.max_header_depth}")
        
        # Check for orphaned headers (e.g., H3 without H2)
        if self._has_orphaned_headers():
            issues.append("Broken header hierarchy (orphaned headers)")
        
        # Content quality issues
        if self.loc_metrics.code_block_ratio >= thresholds.code_block_ratio_critical:
            issues.append(f"Code-heavy: {self.loc_metrics.code_block_ratio:.1%} code blocks")
        elif self.loc_metrics.code_block_ratio >= thresholds.code_block_ratio_warning:
            issues.append(f"High code ratio: {self.loc_metrics.code_block_ratio:.1%}")
        
        if self.loc_metrics.content_density < thresholds.min_content_ratio:
            issues.append(f"Low content density: {self.loc_metrics.content_density:.1%}")
        
        # Link density
        if self.loc_metrics.total_lines > 0:
            links_per_100 = (len(self.links) / self.loc_metrics.total_lines) * 100
            if links_per_100 > thresholds.max_links_per_100_lines:
                issues.append(f"Link-heavy: {len(self.links)} links ({links_per_100:.0f} per 100 lines)")
        
        # Excessive sections
        long_sections = [s for s in self.sections if s.get_severity(thresholds) == Severity.CRITICAL]
        if long_sections:
            section_names = ', '.join(f'"{s.header.text}"' for s in long_sections[:3])
            issues.append(f"Excessive sections: {section_names}")
        
        # Completeness
        if not self.has_toc and self.loc_metrics.total_lines > 300:
            issues.append("Missing Table of Contents (recommended for >300 lines)")
        
        if self.todo_markers > thresholds.max_todo_markers:
            issues.append(f"Incomplete: {self.todo_markers} TODO/FIXME markers")
        
        return issues
    
    def _has_orphaned_headers(self) -> bool:
        """Check if there are orphaned headers (e.g., H3 without H2)."""
        if not self.headers:
            return False
        
        seen_levels = set()
        for header in self.headers:
            level = header.level
            # Check if we're jumping levels (e.g., H1 -> H3)
            if level > 1:
                # Should have seen level-1
                if (level - 1) not in seen_levels:
                    return True
            seen_levels.add(level)
        
        return False


@dataclass
class ModuleAnalysis:
    """Analysis results for a documentation module."""
    name: str
    files: List[FileAnalysis] = field(default_factory=list)
    
    @property
    def total_lines(self) -> int:
        return sum(f.loc_metrics.total_lines for f in self.files)
    
    @property
    def total_content_lines(self) -> int:
        return sum(f.loc_metrics.content_lines for f in self.files)
    
    @property
    def avg_code_block_ratio(self) -> float:
        if not self.files:
            return 0.0
        return sum(f.loc_metrics.code_block_ratio for f in self.files) / len(self.files)


# ============================================================================
# MARKDOWN PARSING
# ============================================================================

class MarkdownParser:
    """Parser for analyzing Markdown structure."""
    
    # Regex patterns
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$')
    CODE_FENCE_PATTERN = re.compile(r'^```(\w*)$')
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    TABLE_ROW_PATTERN = re.compile(r'^\|(.+)\|$')
    LIST_PATTERN = re.compile(r'^(\s*)([-*+]|\d+\.)\s+')
    TOC_PATTERN = re.compile(r'(?i)(table of contents|toc)', re.IGNORECASE)
    TODO_PATTERN = re.compile(r'(?i)(TODO|FIXME|TBD|XXX|HACK)')
    
    def __init__(self, lines: List[str]):
        self.lines = lines
        self.headers: List[HeaderInfo] = []
        self.sections: List[SectionMetrics] = []
        self.code_blocks: List[CodeBlock] = []
        self.links: List[str] = []
        self.images: List[str] = []
        self.tables: int = 0
        self.max_list_depth: int = 0
        self.has_toc: bool = False
        self.todo_markers: int = 0
    
    def parse(self) -> None:
        """Parse the Markdown content."""
        in_code_block = False
        code_block_start = 0
        code_block_lang = ""
        current_section_start = 0
        last_header: Optional[HeaderInfo] = None
        in_table = False
        
        for i, line in enumerate(self.lines, start=1):
            stripped = line.strip()
            
            # Check for code fences
            fence_match = self.CODE_FENCE_PATTERN.match(stripped)
            if fence_match:
                if not in_code_block:
                    in_code_block = True
                    code_block_start = i
                    code_block_lang = fence_match.group(1) or "text"
                else:
                    # End of code block
                    code_block_lines = i - code_block_start - 1
                    self.code_blocks.append(CodeBlock(
                        language=code_block_lang,
                        line_number=code_block_start,
                        lines=code_block_lines
                    ))
                    in_code_block = False
                continue
            
            # Skip lines inside code blocks
            if in_code_block:
                continue
            
            # Check for headers
            header_match = self.HEADER_PATTERN.match(stripped)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2).strip()
                header = HeaderInfo(level=level, text=text, line_number=i)
                self.headers.append(header)
                
                # Calculate previous section metrics
                if last_header is not None:
                    section_lines = i - current_section_start - 1
                    section_code_blocks = sum(1 for cb in self.code_blocks 
                                            if current_section_start < cb.line_number < i)
                    section_links = sum(1 for link_line in range(current_section_start, i)
                                      if link_line < len(self.lines) and 
                                      self.LINK_PATTERN.search(self.lines[link_line]))
                    
                    self.sections.append(SectionMetrics(
                        header=last_header,
                        lines=section_lines,
                        code_blocks=section_code_blocks,
                        links=section_links
                    ))
                
                last_header = header
                current_section_start = i
                
                # Check for TOC
                if self.TOC_PATTERN.search(text):
                    self.has_toc = True
                
                continue
            
            # Check for links
            for match in self.LINK_PATTERN.finditer(line):
                self.links.append(match.group(2))
            
            # Check for images
            for match in self.IMAGE_PATTERN.finditer(line):
                self.images.append(match.group(2))
            
            # Check for tables
            if self.TABLE_ROW_PATTERN.match(stripped):
                if not in_table:
                    self.tables += 1
                    in_table = True
            else:
                in_table = False
            
            # Check for list depth
            list_match = self.LIST_PATTERN.match(line)
            if list_match:
                indent = len(list_match.group(1))
                depth = indent // 2 + 1  # Assuming 2-space indents
                self.max_list_depth = max(self.max_list_depth, depth)
            
            # Check for TODO markers
            if self.TODO_PATTERN.search(line):
                self.todo_markers += 1
        
        # Handle last section
        if last_header is not None:
            section_lines = len(self.lines) - current_section_start
            section_code_blocks = sum(1 for cb in self.code_blocks 
                                    if cb.line_number > current_section_start)
            section_links = sum(1 for link_line in range(current_section_start, len(self.lines))
                              if self.LINK_PATTERN.search(self.lines[link_line]))
            
            self.sections.append(SectionMetrics(
                header=last_header,
                lines=section_lines,
                code_blocks=section_code_blocks,
                links=section_links
            ))


# ============================================================================
# FILE ANALYSIS
# ============================================================================

def analyze_file(file_path: str, thresholds: Thresholds) -> FileAnalysis:
    """Perform comprehensive analysis on a single Markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Calculate LOC metrics
        loc_metrics = calculate_loc_metrics(lines)
        
        # Parse Markdown structure
        parser = MarkdownParser(lines)
        parser.parse()
        
        return FileAnalysis(
            path=file_path,
            loc_metrics=loc_metrics,
            headers=parser.headers,
            sections=parser.sections,
            code_blocks=parser.code_blocks,
            links=parser.links,
            images=parser.images,
            tables=parser.tables,
            max_list_depth=parser.max_list_depth,
            has_toc=parser.has_toc,
            todo_markers=parser.todo_markers
        )
    
    except Exception as e:
        return FileAnalysis(
            path=file_path,
            loc_metrics=LOCMetrics(),
            parse_error=str(e)
        )


def calculate_loc_metrics(lines: List[str]) -> LOCMetrics:
    """Calculate detailed LOC metrics for Markdown lines."""
    metrics = LOCMetrics()
    metrics.total_lines = len(lines)
    
    in_code_block = False
    code_fence_pattern = re.compile(r'^```')
    
    for line in lines:
        stripped = line.strip()
        
        # Check for blank lines
        if not stripped:
            metrics.blank_lines += 1
            continue
        
        # Check for code fences
        if code_fence_pattern.match(stripped):
            in_code_block = not in_code_block
            continue
        
        # Count code block lines
        if in_code_block:
            metrics.code_block_lines += 1
        else:
            # Otherwise it's content
            metrics.content_lines += 1
    
    return metrics


# ============================================================================
# MODULE & PROJECT ANALYSIS
# ============================================================================

def analyze_module(module_path: str, thresholds: Thresholds) -> ModuleAnalysis:
    """Analyze all Markdown files in a module."""
    module_name = os.path.basename(module_path)
    files = []
    
    if not os.path.exists(module_path):
        return ModuleAnalysis(name=module_name, files=[])
    
    for root, dirs, filenames in os.walk(module_path):
        for filename in filenames:
            if filename.endswith('.md'):
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path).replace('\\', '/')
                analysis = analyze_file(file_path, thresholds)
                analysis.path = rel_path
                files.append(analysis)
    
    # Sort by total lines
    files.sort(key=lambda x: x.loc_metrics.total_lines)
    
    return ModuleAnalysis(name=module_name, files=files)


def get_project_modules() -> List[str]:
    """Automatically detect documentation modules in the current directory."""
    modules = []
    current_dir = Path('.')
    
    for item in current_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if directory contains Markdown files
            md_files = list(item.rglob('*.md'))
            if md_files:
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
        return f"{cf.header(module.name.upper() + ' MODULE:')}\nNo Markdown files found\n"
    
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


def format_god_document_report(modules: List[ModuleAnalysis], thresholds: Thresholds) -> str:
    """Generate God Document detection report."""
    cf = ColorFormatter
    output = f"\n{cf.header('='*80)}\n"
    output += f"{cf.header('GOD DOCUMENT DETECTION REPORT')}\n"
    output += f"{cf.header('='*80)}\n\n"
    
    all_files = []
    for module in modules:
        for file in module.files:
            all_files.append((module.name, file))
    
    # Filter and sort by severity
    critical_files = [(m, f) for m, f in all_files if f.get_severity(thresholds) == Severity.CRITICAL]
    warning_files = [(m, f) for m, f in all_files if f.get_severity(thresholds) == Severity.WARNING]
    
    if critical_files:
        output += f"{cf.colorize('🔴 CRITICAL - God Documents (Split Recommended):', Severity.CRITICAL)}\n\n"
        for module_name, file in sorted(critical_files, key=lambda x: x[1].loc_metrics.total_lines, reverse=True):
            output += f"  File: {cf.BOLD}{file.path}{cf.RESET}\n"
            output += f"  Lines: {file.loc_metrics.total_lines} | Headers: {len(file.headers)} | "
            output += f"Code Blocks: {len(file.code_blocks)}\n"
            issues = file.get_issues(thresholds)
            for issue in issues:
                output += f"    ⚠️  {issue}\n"
            output += "\n"
    
    if warning_files:
        output += f"{cf.colorize('🟡 WARNING - Large Documents (Monitor for Growth):', Severity.WARNING)}\n\n"
        for module_name, file in sorted(warning_files, key=lambda x: x[1].loc_metrics.total_lines, reverse=True)[:10]:
            output += f"  {os.path.basename(file.path)}: {file.loc_metrics.total_lines} lines, "
            output += f"{len(file.headers)} headers ({file.path})\n"
        output += "\n"
    
    if not critical_files and not warning_files:
        output += f"{cf.colorize('✅ No God Documents detected!', Severity.HEALTHY)}\n\n"
    
    return output


def format_summary_statistics(modules: List[ModuleAnalysis], thresholds: Thresholds) -> str:
    """Generate project-level summary statistics."""
    cf = ColorFormatter
    
    # Calculate totals
    total_files = sum(len(m.files) for m in modules)
    total_lines = sum(m.total_lines for m in modules)
    total_content = sum(m.total_content_lines for m in modules)
    
    # Get all files
    all_files = []
    for module in modules:
        all_files.extend(module.files)
    
    # Calculate averages
    avg_file_size = total_lines / total_files if total_files > 0 else 0
    avg_code_ratio = sum(f.loc_metrics.code_block_ratio for f in all_files) / total_files if total_files > 0 else 0
    
    # Get top 10 largest files
    largest_files = sorted(all_files, key=lambda x: x.loc_metrics.total_lines, reverse=True)[:10]
    
    # Count issues
    critical_files = [f for f in all_files if f.get_severity(thresholds) == Severity.CRITICAL]
    warning_files = [f for f in all_files if f.get_severity(thresholds) == Severity.WARNING]
    
    # Calculate health score
    health_score = calculate_health_score(all_files, thresholds)
    
    # Format output
    output = f"\n{cf.header('='*80)}\n"
    output += f"{cf.header('DOCUMENTATION SUMMARY STATISTICS')}\n"
    output += f"{cf.header('='*80)}\n\n"
    
    output += f"{cf.subheader('Overall Metrics:')}\n"
    output += f"  Total Files:          {total_files:,}\n"
    output += f"  Total Lines:          {total_lines:,}\n"
    output += f"  Total Content Lines:  {total_content:,}\n"
    output += f"  Average File Size:    {avg_file_size:.0f} lines\n"
    output += f"  Avg Code Block Ratio: {avg_code_ratio:.1%}\n"
    output += f"  Health Score:         {cf.colorize(f'{health_score}/100', get_health_severity(health_score))}\n\n"
    
    output += f"{cf.subheader('Top 10 Largest Files:')}\n"
    for i, file in enumerate(largest_files, 1):
        severity = file.get_severity(thresholds)
        indicator = "🔴" if severity == Severity.CRITICAL else "🟡" if severity == Severity.WARNING else "🟢"
        output += f"  {i:2d}. {indicator} {file.loc_metrics.total_lines:5d} lines - {file.path}\n"
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
    """Calculate overall documentation health score (0-100)."""
    if not files:
        return 100
    
    score = 100
    
    # Penalize for large files
    critical_files = sum(1 for f in files if f.get_severity(thresholds) == Severity.CRITICAL)
    warning_files = sum(1 for f in files if f.get_severity(thresholds) == Severity.WARNING)
    
    score -= (critical_files / len(files)) * 30
    score -= (warning_files / len(files)) * 15
    
    # Penalize for missing structure
    no_structure_files = sum(1 for f in files if len(f.headers) < thresholds.min_headers)
    score -= (no_structure_files / len(files)) * 10
    
    # Penalize for missing TOC in large files
    large_no_toc = sum(1 for f in files if f.loc_metrics.total_lines > 300 and not f.has_toc)
    score -= (large_no_toc / len(files)) * 5
    
    # Penalize for incomplete documentation
    incomplete_files = sum(1 for f in files if f.todo_markers > thresholds.max_todo_markers)
    score -= min(incomplete_files * 3, 15)
    
    return max(0, int(score))


def get_health_severity(score: int) -> Severity:
    """Get severity level for health score."""
    if score >= 80:
        return Severity.HEALTHY
    elif score >= 60:
        return Severity.WARNING
    return Severity.CRITICAL


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function to run comprehensive documentation analysis."""
    cf = ColorFormatter
    thresholds = Thresholds()
    
    print(f"{cf.header('='*80)}")
    print(f"{cf.header('COMPREHENSIVE DOCUMENTATION ANALYSIS REPORT')}")
    print(f"{cf.header('='*80)}\n")
    
    # Get all modules
    modules = get_project_modules()
    
    if not modules:
        print("No Markdown files found in the current directory.")
        return
    
    # Analyze all modules
    print(f"{cf.subheader('Analyzing modules...')}\n")
    module_analyses = []
    
    for module_name in modules:
        module_analysis = analyze_module(module_name, thresholds)
        module_analyses.append(module_analysis)
        
        # Print module output
        output = format_module_output(module_analysis, thresholds, detailed=False)
        print(output)
    
    # Print God Document report
    print(format_god_document_report(module_analyses, thresholds))
    
    # Print summary statistics
    print(format_summary_statistics(module_analyses, thresholds))
    
    # Print recommendations
    print(f"{cf.header('='*80)}")
    print(f"{cf.header('RECOMMENDATIONS')}")
    print(f"{cf.header('='*80)}\n")
    print(f"{cf.subheader('Documentation Priority:')}\n")
    print(f"  🔴 {cf.BOLD}HIGH{cf.RESET}   - Files >1000 lines: Split into multiple documents")
    print(f"  🟡 {cf.BOLD}MEDIUM{cf.RESET} - Files >500 lines: Monitor and consider splitting")
    print(f"  🟢 {cf.BOLD}LOW{cf.RESET}    - Files <500 lines: Healthy, maintain current structure\n")
    print(f"{cf.subheader('Structure Best Practices:')}\n")
    print(f"  - Use single H1 header for main title")
    print(f"  - Maintain proper header hierarchy (no orphaned headers)")
    print(f"  - Keep sections under 200 lines")
    print(f"  - Add Table of Contents for files >300 lines\n")
    print(f"{cf.subheader('Content Quality:')}\n")
    print(f"  - Balance code blocks with explanatory text")
    print(f"  - Aim for <40% code block ratio")
    print(f"  - Resolve TODO/FIXME markers")
    print(f"  - Verify all links are valid\n")


if __name__ == "__main__":
    main()