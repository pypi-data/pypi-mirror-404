"""
Success Rate Chart Renderer

Simple functions for rendering success rate charts.
Extracted from analytics/adapters/matplotlib_renderer.py following Solo Developer pattern.
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
from .models import TeamSuccessRate, LeagueAverages, ChartConfig


def render_success_rate_chart(
    data: List[TeamSuccessRate], 
    averages: LeagueAverages,
    config: ChartConfig
) -> str:
    """
    Render a success rate scatter plot chart with team logos.
    
    Args:
        data: List of team success rate data
        averages: League average success rates for reference lines
        config: Chart configuration
        
    Returns:
        Path to the saved chart file
    """
    logger = get_logger(__name__)
    logger.info("Rendering success rate chart with team logos...")
    
    try:
        # Set up the figure with high DPI for quality
        fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
        
        # Set background color
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#f8f9fa')
        
        # Set axis limits
        ax.set_xlim(config.x_min, config.x_max)
        ax.set_ylim(config.y_min, config.y_max)
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Add reference lines at league averages
        ax.axhline(y=averages.avg_pass_success_rate, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
        ax.axvline(x=averages.avg_rush_success_rate, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
        
        # Download and place team logos
        for team in data:
            x = team.rush_success_rate
            y = team.pass_success_rate
            
            # Skip if coordinates are invalid
            if not (config.x_min <= x <= config.x_max and config.y_min <= y <= config.y_max):
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
        
        # Format axis ticks as percentages
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.1%}'))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, p: f'{y:.1%}'))
        
        # Set tick parameters
        ax.tick_params(axis='both', which='major', labelsize=12)
        
        # Adjust layout to prevent clipping
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(config.save_path, dpi=config.dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        # Close the figure to free memory
        plt.close(fig)
        
        logger.info(f"Success rate chart saved to {config.save_path}")
        return config.save_path
        
    except Exception as e:
        logger.error(f"Failed to render success rate chart: {e}")
        raise


def render_fallback_chart(
    data: List[TeamSuccessRate], 
    averages: LeagueAverages,
    config: ChartConfig
) -> str:
    """
    Render a fallback version of the chart using team abbreviations.
    
    Args:
        data: List of team success rate data
        averages: League average success rates for reference lines
        config: Chart configuration
        
    Returns:
        Path to the saved fallback chart file
    """
    logger = get_logger(__name__)
    logger.info("Rendering fallback success rate chart with team abbreviations...")
    
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
    ax.axhline(y=averages.avg_pass_success_rate, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
    ax.axvline(x=averages.avg_rush_success_rate, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
    
    # Plot team abbreviations as text
    for team in data:
        x = team.rush_success_rate
        y = team.pass_success_rate
        
        if config.x_min <= x <= config.x_max and config.y_min <= y <= config.y_max:
            _place_team_text(ax, team, x, y)
    
    # Set labels and title
    ax.set_xlabel(config.x_axis_label, fontsize=14, fontweight='bold')
    ax.set_ylabel(config.y_axis_label, fontsize=14, fontweight='bold')
    ax.set_title(config.title, fontsize=16, fontweight='bold', pad=20)
    
    # Format as percentages
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.1%}'))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, p: f'{y:.1%}'))
    
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    plt.tight_layout()
    
    # Save with fallback suffix
    fallback_path = config.save_path.replace('.png', '_fallback.png')
    plt.savefig(fallback_path, dpi=config.dpi, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    
    plt.close(fig)
    
    logger.info(f"Fallback success rate chart saved to {fallback_path}")
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
        
        # Check axis ranges
        if config.x_min >= config.x_max or config.y_min >= config.y_max:
            return False
        
        return True
        
    except Exception:
        return False


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


def _place_team_text(ax, team: TeamSuccessRate, x: float, y: float):
    """
    Place team abbreviation as text on the chart.
    
    Args:
        ax: Matplotlib axes
        team: Team success rate data
        x: X coordinate
        y: Y coordinate
    """
    # Use team color if available, otherwise default
    color = team.team_color if team.team_color else '#333333'
    
    ax.text(x, y, team.team, fontsize=10, fontweight='bold', 
           ha='center', va='center', color=color,
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
