"""
Points Per Drive Chart Renderer

Simple functions for rendering efficiency charts.
Extracted from analytics/adapters/efficiency_chart_renderer.py following Solo Developer pattern.
"""

import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.ticker import FuncFormatter
import numpy as np
import requests
from PIL import Image
from io import BytesIO
from typing import List

from commonv2 import get_logger
from .models import TeamEfficiencyMetrics, LeagueEfficiencyAverages, ChartConfig


def render_efficiency_chart(
    data: List[TeamEfficiencyMetrics], 
    averages: LeagueEfficiencyAverages,
    config: ChartConfig
) -> str:
    """
    Render an efficiency scatter plot chart with team logos.
    
    Args:
        data: List of team efficiency data
        averages: League average efficiency metrics for reference lines
        config: Chart configuration
        
    Returns:
        Path to the saved chart file
    """
    logger = get_logger(__name__)
    logger.info("Rendering efficiency chart with team logos...")
    
    try:
        # Set up the figure with high DPI for quality
        fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
        
        # Set background color
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#f8f9fa')
        
        # Calculate dynamic ranges if enabled
        if config.use_dynamic_ranges:
            x_values = [team.opponent_adjusted_scoring for team in data]
            y_values = [team.opponent_adjusted_stopping for team in data]
            
            x_min, x_max = _calculate_dynamic_range(
                x_values, averages.avg_opponent_adjusted_scoring, 
                config.padding_percent, config.min_range_size, config.center_on_averages
            )
            y_min, y_max = _calculate_dynamic_range(
                y_values, averages.avg_opponent_adjusted_stopping, 
                config.padding_percent, config.min_range_size, config.center_on_averages
            )
        else:
            x_min, x_max = config.x_min, config.x_max
            y_min, y_max = config.y_min, config.y_max
        
        # Set axis limits
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Add reference lines at league averages
        ax.axhline(y=averages.avg_opponent_adjusted_stopping, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
        ax.axvline(x=averages.avg_opponent_adjusted_scoring, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
        
        # Download and place team logos
        for team in data:
            x = team.opponent_adjusted_scoring
            y = team.opponent_adjusted_stopping
            
            # Skip if coordinates are invalid
            if not (x_min <= x <= x_max and y_min <= y <= y_max):
                logger.warning(f"Skipping {team.team} - coordinates out of bounds: ({x:.3f}, {y:.3f})")
                continue
            
            if team.team_logo_espn:
                try:
                    # Download and place logo
                    logo_img = _download_team_logo(team.team_logo_espn, config.logo_size)
                    logo_array = np.array(logo_img)
                    
                    # Create OffsetImage and AnnotationBbox
                    imagebox = OffsetImage(logo_array, zoom=1.0)
                    ab = AnnotationBbox(imagebox, (x, y), frameon=False, pad=0)
                    ax.add_artist(ab)
                    
                    logger.debug(f"Placed {team.team} logo at ({x:.3f}, {y:.3f})")
                    
                except Exception as e:
                    logger.warning(f"Failed to place logo for {team.team}: {e}")
                    # Fall back to text
                    _place_team_text(ax, team, x, y)
            else:
                # No logo available, use text
                _place_team_text(ax, team, x, y)
        
        # Set labels and title
        ax.set_xlabel(config.x_axis_label, fontsize=14, fontweight='bold')
        ax.set_ylabel(config.y_axis_label, fontsize=14, fontweight='bold')
        ax.set_title(config.title, fontsize=16, fontweight='bold', pad=20)
        
        # Format axis ticks as raw numbers (NOT percentages)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.1f}'))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, p: f'{y:.1f}'))
        
        # Set tick parameters
        ax.tick_params(axis='both', which='major', labelsize=12)
        
        # Adjust layout to prevent clipping
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(config.save_path, dpi=config.dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        # Close the figure to free memory
        plt.close(fig)
        
        logger.info(f"Efficiency chart saved to {config.save_path}")
        return config.save_path
        
    except Exception as e:
        logger.error(f"Failed to render efficiency chart: {e}")
        raise


def render_fallback_chart(
    data: List[TeamEfficiencyMetrics], 
    averages: LeagueEfficiencyAverages,
    config: ChartConfig
) -> str:
    """
    Render a fallback version of the chart using team abbreviations.
    
    Args:
        data: List of team efficiency data
        averages: League average efficiency metrics for reference lines
        config: Chart configuration
        
    Returns:
        Path to the saved fallback chart file
    """
    logger = get_logger(__name__)
    logger.info("Rendering fallback efficiency chart with team abbreviations...")
    
    # Set up the figure
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Set background
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#f8f9fa')
    
    # Set axis limits
    ax.set_xlim(config.x_min, config.x_max)
    ax.set_ylim(config.y_min, config.y_max)
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Add reference lines
    ax.axhline(y=averages.avg_opponent_adjusted_stopping, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
    ax.axvline(x=averages.avg_opponent_adjusted_scoring, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
    
    # Plot team abbreviations as text
    for team in data:
        x = team.opponent_adjusted_scoring
        y = team.opponent_adjusted_stopping
        
        if config.x_min <= x <= config.x_max and config.y_min <= y <= config.y_max:
            _place_team_text(ax, team, x, y)
    
    # Set labels and title
    ax.set_xlabel(config.x_axis_label, fontsize=14, fontweight='bold')
    ax.set_ylabel(config.y_axis_label, fontsize=14, fontweight='bold')
    ax.set_title(config.title, fontsize=16, fontweight='bold', pad=20)
    
    # Format as raw numbers (NOT percentages)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.1f}'))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, p: f'{y:.1f}'))
    
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    plt.tight_layout()
    
    # Save with fallback suffix
    fallback_path = config.save_path.replace('.png', '_fallback.png')
    plt.savefig(fallback_path, dpi=config.dpi, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    
    plt.close(fig)
    
    logger.info(f"Fallback efficiency chart saved to {fallback_path}")
    return fallback_path


def validate_chart_config(config: ChartConfig) -> bool:
    """
    Validate that the chart configuration is valid.
    
    Args:
        config: Chart configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Check required fields
        if not all([config.title, config.x_axis_label, config.y_axis_label, config.save_path]):
            return False
        
        # Check dimensions
        if config.width <= 0 or config.height <= 0:
            return False
        
        # Check axis ranges (only if not using dynamic ranges)
        if not config.use_dynamic_ranges:
            if config.x_min >= config.x_max or config.y_min >= config.y_max:
                return False
        
        return True
        
    except Exception:
        return False


def _calculate_dynamic_range(values: List[float], average: float, padding_percent: float, 
                           min_range_size: float, center_on_averages: bool) -> tuple:
    """
    Calculate dynamic axis range based on data values.
    
    Args:
        values: List of data values
        average: League average value
        padding_percent: Padding around data as percentage
        min_range_size: Minimum range size
        center_on_averages: Whether to center range around average
        
    Returns:
        Tuple of (min_value, max_value)
    """
    if not values:
        return -1.0, 1.0
    
    data_min = min(values)
    data_max = max(values)
    data_range = data_max - data_min
    
    # Add padding
    padding = max(data_range * padding_percent, min_range_size * 0.1)
    
    if center_on_averages:
        # Center around the average
        max_distance = max(abs(data_max - average), abs(data_min - average))
        range_half = max(max_distance + padding, min_range_size / 2)
        return average - range_half, average + range_half
    else:
        # Just add padding to data range
        range_size = max(data_range + 2 * padding, min_range_size)
        center = (data_min + data_max) / 2
        return center - range_size / 2, center + range_size / 2


def _download_team_logo(logo_url: str, size: tuple = (40, 40)) -> Image.Image:
    """
    Download and resize team logo from URL.
    
    Args:
        logo_url: URL to team logo
        size: Tuple of (width, height) for resizing
        
    Returns:
        PIL Image object
    """
    logger = get_logger(__name__)
    
    try:
        response = requests.get(logo_url, timeout=10)
        response.raise_for_status()
        
        # Open image and convert to RGBA for transparency support
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        
        # Resize image
        img = img.resize(size, Image.Resampling.LANCZOS)
        
        return img
        
    except Exception as e:
        logger.warning(f"Failed to download logo from {logo_url}: {e}")
        # Return a placeholder image
        placeholder = Image.new('RGBA', size, (128, 128, 128, 255))
        return placeholder


def _place_team_text(ax, team: TeamEfficiencyMetrics, x: float, y: float):
    """
    Place team abbreviation as text on the chart.
    
    Args:
        ax: Matplotlib axes
        team: Team efficiency data
        x: X coordinate
        y: Y coordinate
    """
    # Use team color if available, otherwise default
    color = team.team_color if team.team_color else '#333333'
    
    ax.text(x, y, team.team, fontsize=10, fontweight='bold', 
           ha='center', va='center', color=color,
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
