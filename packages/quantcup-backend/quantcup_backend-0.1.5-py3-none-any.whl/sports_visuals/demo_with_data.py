# Demo: sportypy with data visualization
import matplotlib.pyplot as plt
import numpy as np
from sportypy.surfaces.football import NFLField
from sportypy.surfaces.basketball import NBACourt

def demo_nfl_field_with_data():
    """Demonstrate NFL field with sample play data"""
    print("Creating NFL field with sample play data...")
    
    # Create NFL field
    nfl = NFLField()
    fig, ax = plt.subplots(1, 1, figsize=(15, 8))
    nfl.draw(ax=ax)
    
    # Sample play data (yard lines)
    play_positions = [20, 35, 45, 60, 75]  # Yard line positions
    play_types = ['Rush', 'Pass', 'Sack', 'TD', 'FG']
    colors = ['blue', 'green', 'red', 'gold', 'orange']
    
    # Plot plays on the field
    for i, (pos, play_type, color) in enumerate(zip(play_positions, play_types, colors)):
        # Convert yard line to field coordinates (NFL field is 120 yards total)
        x_coord = pos
        y_coord = 26.67  # Center of field (53.33 yards / 2)
        
        ax.scatter(x_coord, y_coord, s=200, c=color, alpha=0.8, 
                  edgecolors='black', linewidth=2, zorder=20)
        ax.annotate(play_type, (x_coord, y_coord + 5), 
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.title("NFL Field with Sample Play Data", fontsize=16, fontweight='bold')
    plt.savefig("nfl_field_with_data.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("✓ NFL field with data saved as 'nfl_field_with_data.png'")

def demo_nba_shot_chart():
    """Demonstrate NBA court with sample shot data"""
    print("Creating NBA shot chart with sample data...")
    
    # Create NBA court (offensive half)
    court = NBACourt()
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    court.draw(ax=ax, display_range="offense")
    
    # Sample shot data (simplified coordinates)
    np.random.seed(42)  # For reproducible results
    
    # Generate sample shot locations
    n_shots = 50
    shot_x = np.random.uniform(-25, 25, n_shots)  # Court width
    shot_y = np.random.uniform(0, 47, n_shots)    # Half court length
    
    # Generate shot results (made/missed)
    shot_made = np.random.choice([0, 1], n_shots, p=[0.6, 0.4])  # 40% made
    
    # Plot shots
    colors = ['red' if made == 0 else 'green' for made in shot_made]
    ax.scatter(shot_x, shot_y, c=colors, alpha=0.7, s=60, 
              edgecolors='black', linewidth=0.5, zorder=20)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='green', label='Made Shot'),
                      Patch(facecolor='red', label='Missed Shot')]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.title("NBA Shot Chart - Sample Data", fontsize=16, fontweight='bold')
    plt.savefig("nba_shot_chart.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("✓ NBA shot chart saved as 'nba_shot_chart.png'")

def demo_nfl_heatmap():
    """Demonstrate NFL field with heatmap overlay"""
    print("Creating NFL field with heatmap...")
    
    # Create NFL field
    nfl = NFLField()
    fig, ax = plt.subplots(1, 1, figsize=(15, 8))
    nfl.draw(ax=ax)
    
    # Generate sample player position data
    np.random.seed(42)
    n_positions = 200
    
    # Focus on red zone area (0-20 yard line)
    x_positions = np.random.uniform(0, 20, n_positions)
    y_positions = np.random.normal(26.67, 8, n_positions)  # Center field with spread
    
    # Create heatmap
    heatmap = ax.hexbin(x_positions, y_positions, gridsize=15, 
                       cmap='Reds', alpha=0.7, zorder=15)
    
    # Add colorbar
    cbar = plt.colorbar(heatmap, ax=ax, shrink=0.6)
    cbar.set_label('Player Density', rotation=270, labelpad=20)
    
    plt.title("NFL Red Zone - Player Position Heatmap", fontsize=16, fontweight='bold')
    plt.savefig("nfl_heatmap.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("✓ NFL heatmap saved as 'nfl_heatmap.png'")

if __name__ == "__main__":
    print("🏈 sportypy Data Visualization Demo")
    print("=" * 40)
    
    demo_nfl_field_with_data()
    demo_nba_shot_chart()
    demo_nfl_heatmap()
    
    print("\n✅ All demos completed!")
    print("Generated files:")
    print("  - nfl_field_with_data.png")
    print("  - nba_shot_chart.png") 
    print("  - nfl_heatmap.png")
    print("\nThese examples show how sportypy can be integrated with your")
    print("quantcup_backend analytics for enhanced sports visualizations!")