# Test sportypy football field features and classes
import matplotlib.pyplot as plt
from sportypy.surfaces.football import NFLField

def test_basic_nfl_field():
    """Test basic NFL field creation"""
    print("Testing basic NFL field...")
    
    nfl = NFLField()
    fig, ax = plt.subplots(1, 1, figsize=(15, 8))
    nfl.draw(ax=ax)
    plt.title("Basic NFL Field")
    plt.savefig("football_basic.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("✓ Basic NFL field saved as 'football_basic.png'")

def test_nfl_display_ranges():
    """Test different display ranges for NFL field"""
    print("Testing NFL field display ranges...")
    
    display_ranges = [
        ("red zone", "Red Zone"),
        ("offense", "Offensive Half"),
        ("defense", "Defensive Half")
    ]
    
    for i, (range_name, title) in enumerate(display_ranges):
        try:
            nfl = NFLField()
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            nfl.draw(ax=ax, display_range=range_name)
            plt.title(f"NFL Field - {title}")
            plt.savefig(f"football_{range_name.replace(' ', '_')}.png", dpi=300, bbox_inches='tight')
            plt.close(fig)
            print(f"✓ NFL {title} saved as 'football_{range_name.replace(' ', '_')}.png'")
        except Exception as e:
            print(f"✗ Error with {range_name}: {e}")

def test_nfl_field_features():
    """Test accessing NFL field features"""
    print("Testing NFL field features...")
    
    nfl = NFLField()
    
    # Try to access some features mentioned in the documentation
    print("Available attributes in NFLField:")
    attributes = [attr for attr in dir(nfl) if not attr.startswith('_')]
    for attr in sorted(attributes)[:10]:  # Show first 10 attributes
        print(f"  - {attr}")
    
    # Check if we can access field dimensions
    try:
        print(f"\nField information:")
        if hasattr(nfl, 'field_length'):
            print(f"  - Field length: {nfl.field_length}")
        if hasattr(nfl, 'field_width'):
            print(f"  - Field width: {nfl.field_width}")
        if hasattr(nfl, 'feature_units'):
            print(f"  - Units: {nfl.feature_units}")
    except Exception as e:
        print(f"Error accessing field properties: {e}")

def test_nfl_with_custom_params():
    """Test NFL field with custom parameters"""
    print("Testing NFL field with custom parameters...")
    
    try:
        # Try different field units
        nfl_ft = NFLField(field_units='ft')
        fig, ax = plt.subplots(1, 1, figsize=(15, 8))
        nfl_ft.draw(ax=ax)
        plt.title("NFL Field (feet units)")
        plt.savefig("football_feet_units.png", dpi=300, bbox_inches='tight')
        plt.close(fig)
        print("✓ NFL field with feet units saved as 'football_feet_units.png'")
    except Exception as e:
        print(f"✗ Error with custom units: {e}")
    
    try:
        # Try with rotation
        nfl_rot = NFLField(rotation=90)
        fig, ax = plt.subplots(1, 1, figsize=(8, 15))
        nfl_rot.draw(ax=ax)
        plt.title("NFL Field (90° rotation)")
        plt.savefig("football_rotated.png", dpi=300, bbox_inches='tight')
        plt.close(fig)
        print("✓ Rotated NFL field saved as 'football_rotated.png'")
    except Exception as e:
        print(f"✗ Error with rotation: {e}")

def test_field_coordinate_system():
    """Test the coordinate system of the NFL field"""
    print("Testing NFL field coordinate system...")
    
    nfl = NFLField()
    fig, ax = plt.subplots(1, 1, figsize=(15, 8))
    nfl.draw(ax=ax)
    
    # Add coordinate markers
    import numpy as np
    
    # Mark yard lines
    yard_lines = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for yard in yard_lines:
        ax.axvline(x=yard, color='red', alpha=0.5, linestyle='--', linewidth=1)
        ax.text(yard, 55, f'{yard}', ha='center', va='bottom', 
                color='red', fontweight='bold', fontsize=8)
    
    # Mark field width points
    width_points = [0, 13.33, 26.67, 40, 53.33]
    for width in width_points:
        ax.axhline(y=width, color='blue', alpha=0.5, linestyle='--', linewidth=1)
        ax.text(105, width, f'{width:.1f}', ha='left', va='center', 
                color='blue', fontweight='bold', fontsize=8)
    
    plt.title("NFL Field with Coordinate Grid")
    plt.savefig("football_coordinates.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("✓ NFL field with coordinates saved as 'football_coordinates.png'")

if __name__ == "__main__":
    print("🏈 NFL Field Features Test")
    print("=" * 40)
    
    test_basic_nfl_field()
    test_nfl_display_ranges()
    test_nfl_field_features()
    test_nfl_with_custom_params()
    test_field_coordinate_system()
    
    print("\n✅ All football tests completed!")
    print("Generated files:")
    print("  - football_basic.png")
    print("  - football_red_zone.png")
    print("  - football_offense.png") 
    print("  - football_defense.png")
    print("  - football_feet_units.png")
    print("  - football_rotated.png")
    print("  - football_coordinates.png")