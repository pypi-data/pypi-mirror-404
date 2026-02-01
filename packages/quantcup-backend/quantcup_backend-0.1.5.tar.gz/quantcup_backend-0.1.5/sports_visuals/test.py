# Import required packages
import matplotlib.pyplot as plt
from sportypy.surfaces.hockey import NHLRink
from sportypy.surfaces.basketball import NBACourt, NCAACourt
from sportypy.surfaces.football import NFLField

# Test 1: NHL Rink
print("Creating NHL Rink...")
nhl = NHLRink()
fig1, ax1 = plt.subplots(1, 1, figsize=(12, 8))
nhl.draw(ax=ax1)
plt.title("NHL Rink")
plt.savefig("nhl_rink.png", dpi=300, bbox_inches='tight')
plt.close(fig1)  # Close figure to prevent display issues

# Test 2: NBA Court (Basic)
print("Creating NBA Court...")
court = NBACourt()
fig2, ax2 = plt.subplots(1, 1, figsize=(10, 6))
court.draw(ax=ax2, display_range="offense")
plt.title("NBA Court - Offensive Half")
plt.savefig("nba_court.png", dpi=300, bbox_inches='tight')
plt.close(fig2)  # Close figure to prevent display issues

# Test 2b: Basic NCAA Court (colors_dict has a bug in current version)
print("Creating basic NCAA Court...")
ncaa_court = NCAACourt()
fig2b, ax2b = plt.subplots(1, 1, figsize=(10, 6))
ncaa_court.draw(ax=ax2b)
plt.title("NCAA Basketball Court")
plt.savefig("ncaa_court_basic.png", dpi=300, bbox_inches='tight')
plt.close(fig2b)  # Close figure to prevent display issues

# Test 3: NFL Field
print("Creating NFL Field...")
nfl = NFLField()
fig3, ax3 = plt.subplots(1, 1, figsize=(15, 8))
nfl.draw(ax=ax3)
plt.title("NFL Field")
plt.savefig("nfl_field.png", dpi=300, bbox_inches='tight')
plt.close(fig3)  # Close figure to prevent display issues

# Test 4: NFL Red Zone
print("Creating NFL Red Zone...")
nfl_redzone = NFLField()
fig4, ax4 = plt.subplots(1, 1, figsize=(10, 8))
nfl_redzone.draw(ax=ax4, display_range="red zone")
plt.title("NFL Red Zone")
plt.savefig("nfl_redzone.png", dpi=300, bbox_inches='tight')
plt.close(fig4)  # Close figure to prevent display issues

print("All tests completed! Check the generated PNG files.")
