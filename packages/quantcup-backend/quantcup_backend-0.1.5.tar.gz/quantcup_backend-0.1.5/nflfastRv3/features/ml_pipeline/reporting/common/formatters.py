"""
Markdown formatting utilities for report generation.

Extracted from analyzers.py to provide shared formatting functions
across all reporting components.
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
        >>> headers = ['Name', 'Value', 'Status']
        >>> rows = [['Feature1', '0.123', 'Active'], ['Feature2', '0.456', 'Disabled']]
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
        >>> format_section_header("Performance Metrics", level=2)
        '## Performance Metrics'
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
        unit: Optional unit suffix (, %, etc.)
        description: Optional description text
        
    Returns:
        str: Formatted metric display line
    
    Example:
        >>> format_metric_row("Accuracy", 0.856, "%")
        '- **Accuracy:** 85.6%'
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
        >>> format_code_block("x = 5\\ny = 10", "python")
        '```python\\nx = 5\\ny = 10\\n```'
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
        >>> items = ['Item 1', 'Item 2', 'Item 3']
        >>> format_list_items(items, 'unordered')
        '- Item 1\\n- Item 2\\n- Item 3'
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


__all__ = [
    'format_markdown_table',
    'format_section_header',
    'format_metric_row',
    'format_code_block',
    'format_list_items',
]
