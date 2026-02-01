"""
Injury Analysis Constants

Shared constants for severity scoring, position weights, and injury patterns.
Extracted from lines 34-123 of original injury_features.py.

Pattern: Self-contained constants module
Complexity: 0 points (pure data)
Layer: N/A (constants only)
"""

# Position importance weights (based on NFL analytics research)
# From FEATURE_ENHANCEMENT_PLAN.md lines 604-615
POSITION_WEIGHTS = {
    'QB': 0.35,   # Quarterback - most important
    'WR': 0.15,   # Wide receiver
    'OL': 0.15,   # Offensive line
    'RB': 0.10,   # Running back
    'DL': 0.10,   # Defensive line
    'LB': 0.08,   # Linebacker
    'DB': 0.07,   # Defensive back
    'TE': 0.05,   # Tight end
    'K': 0.02,    # Kicker
    'P': 0.01     # Punter
}

# Injury status impact scores
# Out = 100% impact, Doubtful = 75%, Questionable = 25%
INJURY_STATUS_WEIGHTS = {
    'Out': 1.0,
    'Doubtful': 0.75,
    'Questionable': 0.25,
    'Probable': 0.10,  # Rarely used anymore
    'IR': 1.0,  # Injured Reserve
    'PUP': 1.0,  # Physically Unable to Perform
    'NFI': 1.0,  # Non-Football Injury
}

# Configuration constants for snap-weighted injury impact (Phase 1)
SNAP_SHARE_STARTER_THRESHOLD = 0.50   # >50% snaps = effective starter
SNAP_SHARE_INJURY_REPLACEMENT_THRESHOLD = 0.30  # <30% = injury replacement
DEFAULT_SNAP_SHARE = 0.15  # Unknown player default assumption

# Injury type severity scores (based on NFL medical research)
# Full impact = 1.0, Moderate = 0.5-0.7, Minor = 0.1-0.4
INJURY_SEVERITY = {
    # Severe (Season-ending or Multi-week)
    'Concussion': 1.0,  # NFL protocol required (minimum 1 week)
    'ACL': 1.0,         # Season-ending
    'Achilles': 1.0,    # Season-ending
    'MCL': 0.8,         # 4-8 weeks typically
    'Fracture': 0.9,    # Varies but typically 6+ weeks
    
    # Moderate (1-4 weeks)
    'Hamstring': 0.6,   # 2-4 weeks average
    'Knee': 0.7,        # Various knee injuries (non-ACL)
    'Back': 0.6,        # Lower back injuries
    'Quadricep': 0.5,   # Quad strains
    'Hip': 0.6,         # Hip/groin area
    'Groin': 0.5,       # Groin pulls
    
    # Minor (Days to 1 week)
    'Ankle': 0.5,       # Sprains (varies widely)
    'Shoulder': 0.4,    # Upper body (less impact on skill positions)
    'Calf': 0.4,        # Calf strains
    'Foot': 0.5,        # Foot injuries
    'Hand': 0.3,        # Skill positions affected
    'Finger': 0.2,      # Minimal impact
    'Wrist': 0.3,       # Minimal impact
    
    # Very Minor (Practice only)
    'Illness': 0.2,     # Flu, COVID (short-term)
    'Rest': 0.1,        # Veteran rest days
    'Personal': 0.1,    # Personal reasons
    
    # Default for unmapped injuries
    'Unknown': 0.5      # Conservative middle ground
}

# Pattern matching for injury type classification (handles typos/variations)
INJURY_SEVERITY_PATTERNS = {
    'Concussion': ['concussion', 'head', 'brain', 'protocol'],
    'ACL': ['acl', 'anterior cruciate', 'torn acl'],
    'Achilles': ['achilles', 'achille', 'achillies'],  # Common misspellings
    'MCL': ['mcl', 'medial collateral'],
    'Fracture': ['fracture', 'broken', 'break'],
    'Hamstring': ['hamstring', 'hammy'],
    'Knee': ['knee'],
    'Back': ['back', 'spine', 'lumbar'],
    'Quadricep': ['quadricep', 'quad'],
    'Hip': ['hip'],
    'Groin': ['groin', 'adductor'],
    'Ankle': ['ankle'],
    'Shoulder': ['shoulder', 'rotator'],
    'Calf': ['calf'],
    'Foot': ['foot', 'metatarsal'],
    'Hand': ['hand'],
    'Finger': ['finger'],
    'Wrist': ['wrist'],
    'Illness': ['illness', 'sick', 'flu', 'covid', 'virus'],
    'Rest': ['rest', 'load management', 'vet rest'],
    'Personal': ['personal', 'family']
}

__all__ = [
    'POSITION_WEIGHTS',
    'INJURY_STATUS_WEIGHTS',
    'SNAP_SHARE_STARTER_THRESHOLD',
    'SNAP_SHARE_INJURY_REPLACEMENT_THRESHOLD',
    'DEFAULT_SNAP_SHARE',
    'INJURY_SEVERITY',
    'INJURY_SEVERITY_PATTERNS'
]
