import requests
from urllib.parse import urlparse

BASE = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"

def _get(url, params=None):
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def _get_status_description(status):
    """Safely extract status description from ESPN status field."""
    if not status:
        return None
    if isinstance(status, str):
        return status
    if isinstance(status, dict):
        status_type = status.get("type")
        if isinstance(status_type, dict):
            return status_type.get("description")
        elif isinstance(status_type, str):
            return status_type
    return None

def _resolve_athlete(ath_ref):
    """Expand ESPN $ref to pull display fields."""
    a = _get(ath_ref)
    # Common fields; add more if you need (status, jersey, team, headshot, etc.)
    return {
        "espn_athlete_id": a.get("id"),
        "full_name": a.get("fullName") or a.get("displayName"),
        "short_name": a.get("shortName"),
        "position": (a.get("position") or {}).get("abbreviation"),
        "team_ref": (a.get("team") or {}).get("$ref"),
        "status": _get_status_description(a.get("status")),
    }

def _normalize_position_key(k):
    """Map ESPN keys to your canonical positions (optional)."""
    # Keep as-is or remap to your schema
    mapping = {
        "lilb": "ILB", "rilb": "ILB", "slb": "SLB", "wlb": "WLB",
        "lcb": "CB", "rcb": "CB", "nb": "NB",
        "lt": "LT", "lg": "LG", "c": "C", "rg": "RG", "rt": "RT",
        "wr": "WR", "rb": "RB", "te": "TE", "qb": "QB",
        "lde": "DE", "rde": "DE", "nt": "NT",
        "fs": "FS", "ss": "SS",
        "pk": "K", "p": "P", "ls": "LS", "pr": "PR", "kr": "KR", "h": "H",
    }
    return mapping.get(k.lower(), k.upper())

def get_depth_chart(team_id: int, season: int = 2025):
    """
    Return a unified depth chart list across offense/defense/ST for a team/season.
    Each row: {package, position, rank, espn_athlete_id, full_name, ...}
    """
    url = f"{BASE}/seasons/{season}/teams/{team_id}/depthcharts"
    payload = _get(url)

    # Prefer common packages if present; otherwise keep all
    preferred = {"3WR 1TE", "Base 3-4 D", "Base 4-3 D", "Special Teams"}
    items = payload.get("items", [])
    # Stable order: offense, defense, ST
    items_sorted = sorted(items, key=lambda i: (
        0 if i.get("name") in {"3WR 1TE"} else
        1 if i.get("name") in {"Base 3-4 D", "Base 4-3 D"} else
        2 if i.get("name") == "Special Teams" else 3
    ))

    rows = []
    for pkg in items_sorted:
        pkg_name = pkg.get("name")
        positions = (pkg.get("positions") or {})
        for pos_key, pos_obj in positions.items():
            pos_label = _normalize_position_key(pos_key)
            athletes = (pos_obj.get("athletes") or [])
            for ent in athletes:
                rank = ent.get("rank")
                ath_ref = (ent.get("athlete") or {}).get("$ref")
                if not ath_ref:
                    continue
                a = _resolve_athlete(ath_ref)
                rows.append({
                    "package": pkg_name,
                    "position": pos_label,
                    "rank": rank,
                    "espn_athlete_id": a["espn_athlete_id"],
                    "full_name": a["full_name"],
                    "short_name": a["short_name"],
                    "pos_from_athlete": a["position"],
                    "status": a["status"],
                })

    # You can choose starters by rank==1 per position
    starters = [r for r in rows if r["rank"] == 1]
    return {"all": rows, "starters": starters}

def get_injuries(team_id: int):
    """
    Pull current injuries for a team.
    Returns: {espn_athlete_id, full_name, injury, practice_status, game_status, date}
    """
    url = f"{BASE}/teams/{team_id}/injuries"
    data = _get(url)
    items = data.get("items", [])
    out = []
    for item in items:
        inj = _get(item.get("$ref")) if "$ref" in item else item
        # Many injury objects contain nested athlete + details
        a_ref = (inj.get("athlete") or {}).get("$ref")
        a = _resolve_athlete(a_ref) if a_ref else {}
        details = inj.get("details") or {}
        # Extract injury description properly
        injury_info = details.get("bodyPart") or inj.get("type")
        if isinstance(injury_info, dict):
            injury_desc = injury_info.get("description") or injury_info.get("name", "Unknown")
        else:
            injury_desc = injury_info or "Unknown"
            
        out.append({
            "espn_athlete_id": a.get("espn_athlete_id"),
            "full_name": a.get("full_name"),
            "injury": injury_desc,
            "practice_status": details.get("practiceStatus"),
            "game_status": details.get("status") or details.get("gameStatus"),
            "date": inj.get("date") or details.get("date"),
        })
    return out


team_id = 29 
season = 2025

depth = get_depth_chart(team_id, season)
starters = depth["starters"]   # rank==1 per spot
inj = get_injuries(team_id)

print(f"=== DEPTH CHART FOR TEAM {team_id} (Season {season}) ===")
print(f"Total players: {len(depth['all'])}")
print(f"Starters: {len(starters)}")
print()

print("=== STARTERS ===")
for starter in starters[:22]:  # Show first 22 starters
    print(f"{starter['position']:>3} | {starter['full_name']:<25} | {starter['package']}")

if len(starters) > 22:
    print(f"... and {len(starters) - 22} more starters")

print()
print(f"=== INJURIES ({len(inj)} total) ===")
for injury in inj[:5]:  # Show first 5 injuries
    name = injury.get('full_name') or 'Unknown'
    injury_type = injury.get('injury') or 'Unknown'
    status = injury.get('game_status') or 'Unknown'
    date = injury.get('date', '').split('T')[0] if injury.get('date') else 'Unknown'
    
    print(f"{name:<25} | {injury_type:<15} | {status:<10} | {date}")

if len(inj) > 5:
    print(f"... and {len(inj) - 5} more injuries")
elif len(inj) == 0:
    print("No injuries reported")