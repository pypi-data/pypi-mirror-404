"""
Markdown formatting utilities for data pipeline report generation.

Provides shared formatting functions across all reporting components.
"""


def format_markdown_table(headers, rows):
    """
    Format a markdown table with dynamic column widths based on actual content.
    
    Args:
        headers: List of header strings
        rows: List of lists, where each inner list represents a row
        
    Returns:
        str: Formatted markdown table with proper alignment
    
    Example:
        >>> headers = ['Source', 'Rows', 'Status']
        >>> rows = [['pbp', '1000', 'Success'], ['roster', '500', 'Success']]
        >>> table = format_markdown_table(headers, rows)
    """
    if not rows:
        return ""
    
    # Calculate max width for each column
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Build header row
    header_row = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    
    # Build separator row
    separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
    
    # Build data rows
    data_rows = []
    for row in rows:
        formatted_row = "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
        data_rows.append(formatted_row)
    
    return header_row + "\n" + separator + "\n" + "\n".join(data_rows)


def format_section_header(title, level=2):
    """
    Format consistent section headers for markdown reports.
    
    Args:
        title: Section title text
        level: Header level (1-6), default is 2 (##)
        
    Returns:
        str: Formatted markdown header
    
    Example:
        >>> format_section_header("Pipeline Summary", level=2)
        '## Pipeline Summary'
    """
    if not 1 <= level <= 6:
        level = 2
    
    prefix = "#" * level
    return f"{prefix} {title}"


def format_metric_row(metric_name, value, unit="", description=""):
    """
    Format a metric row for display in reports.
    
    Args:
        metric_name: Name of the metric
        value: Metric value (will be formatted based on type)
        unit: Optional unit suffix (s, %, MB, etc.)
        description: Optional description text
        
    Returns:
        str: Formatted metric display line
    
    Example:
        >>> format_metric_row("Success Rate", 0.98, "%")
        '- **Success Rate:** 98.0%'
    """
    # Format value based on type
    if isinstance(value, float):
        if unit == "%":
            formatted_value = f"{value * 100:.1f}%"
        else:
            formatted_value = f"{value:.3f}{unit}"
    elif isinstance(value, int):
        formatted_value = f"{value:,}{unit}"
    else:
        formatted_value = f"{value}{unit}"
    
    base = f"- **{metric_name}:** {formatted_value}"
    
    if description:
        base += f" - {description}"
    
    return base


def format_code_block(content, language=""):
    """
    Format content as a markdown code block.
    
    Args:
        content: Content to wrap in code block (string or list of strings)
        language: Optional language identifier for syntax highlighting
        
    Returns:
        str: Formatted markdown code block
    
    Example:
        >>> format_code_block("SELECT * FROM dim_game", "sql")
        '```sql\\nSELECT * FROM dim_game\\n```'
    """
    if isinstance(content, list):
        content = "\n".join(content)
    
    if language:
        return f"```{language}\n{content}\n```"
    else:
        return f"```\n{content}\n```"


def format_list_items(items, bullet_type="unordered", indent_level=0):
    """
    Format a list of items as markdown list.
    
    Args:
        items: List of items to format
        bullet_type: 'unordered' (-), 'ordered' (1.), or 'checkbox' (- [ ])
        indent_level: Number of indentation levels (0-based)
        
    Returns:
        str: Formatted markdown list
    
    Example:
        >>> items = ['Source 1', 'Source 2', 'Source 3']
        >>> format_list_items(items, 'unordered')
        '- Source 1\\n- Source 2\\n- Source 3'
    """
    indent = "  " * indent_level
    formatted_items = []
    
    for i, item in enumerate(items, start=1):
        if bullet_type == "ordered":
            prefix = f"{i}."
        elif bullet_type == "checkbox":
            prefix = "- [ ]"
        else:  # unordered
            prefix = "-"
        
        formatted_items.append(f"{indent}{prefix} {item}")
    
    return "\n".join(formatted_items)


def format_bytes(bytes_value):
    """
    Format byte value into human-readable format.
    
    Args:
        bytes_value: Size in bytes (integer or float)
        
    Returns:
        str: Formatted size string
    
    Example:
        >>> format_bytes(1536000)
        '1.46 MB'
        >>> format_bytes(1073741824)
        '1.00 GB'
    """
    if bytes_value < 0:
        return "Invalid"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def format_duration(seconds):
    """
    Format duration in seconds into human-readable format.
    
    Args:
        seconds: Duration in seconds (integer or float)
        
    Returns:
        str: Formatted duration string
    
    Example:
        >>> format_duration(125.5)
        '2m 5.5s'
        >>> format_duration(3665)
        '1h 1m 5s'
    """
    if seconds < 0:
        return "Invalid"
    
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {mins}m {secs:.0f}s"


def format_percentage(value, decimals=1):
    """
    Format a decimal value as percentage.
    
    Args:
        value: Decimal value (0.0 to 1.0)
        decimals: Number of decimal places
        
    Returns:
        str: Formatted percentage string
    
    Example:
        >>> format_percentage(0.9856)
        '98.6%'
        >>> format_percentage(0.9856, 2)
        '98.56%'
    """
    return f"{value * 100:.{decimals}f}%"


__all__ = [
    'format_markdown_table',
    'format_section_header',
    'format_metric_row',
    'format_code_block',
    'format_list_items',
    'format_bytes',
    'format_duration',
    'format_percentage',
]
