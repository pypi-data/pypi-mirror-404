#!/usr/bin/env python3
"""
NCEI Daily Summaries historical weather smoketest (ADS: /access/services/data/v1).

What it does:
- Loads GHCN-Daily station metadata (robust: fixed-width ghcnd-stations.txt).
- Finds nearest station candidates to a given lat/lon.
- Calls NCEI Access Data Service for dataset=daily-summaries (stations=... required).
- Tries candidate stations until it gets data.

Key behaviors:
- Missing datatype detection: reports which requested datatypes were absent in returned rows.
- Quality-aware station ordering: prefers GSN / HCN/CRN flagged stations, then distance.
- Simple retries for transient errors.

Example:
  python ncei/ncei_daily_history_smoketest.py \
    --lat 35.2251 --lon -80.8529 \
    --start 2025-01-10 --end 2025-01-12 \
    --datatypes TMAX,TMIN,PRCP,AWND \
    --radius_km 80 --max_candidates 15

Manual station:
  python ncei/ncei_daily_history_smoketest.py \
    --lat 35.2251 --lon -80.8529 \
    --start 2025-01-10 --end 2025-01-12 \
    --stations USW00013881
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

NCEI_DAILY_ENDPOINT = "https://www.ncei.noaa.gov/access/services/data/v1"

# Official fixed-width station list (robust)
DEFAULT_GHCND_STATIONS_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"


@dataclass(frozen=True)
class Station:
    id: str
    latitude: float
    longitude: float
    elevation_m: Optional[float]
    name: str
    country: str
    state: str
    gsn_flag: str
    hcn_crn_flag: str
    wmo_id: str
    distance_km: float = 1e18


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_float(s: str) -> Optional[float]:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    p = Path(base) / "quantcup" / "ncei"
    p.mkdir(parents=True, exist_ok=True)
    return p


def download_if_needed(url: str, dest: Path, max_age_days: int = 14) -> None:
    if dest.exists():
        age_sec = time.time() - dest.stat().st_mtime
        if age_sec < max_age_days * 86400:
            return

    tmp = dest.with_suffix(dest.suffix + ".tmp")
    headers = {"User-Agent": "QuantCup-NCEI-Smoketest/1.1 (contact: you@example.com)"}
    with requests.get(url, stream=True, timeout=60, headers=headers) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
    tmp.replace(dest)


def load_stations_fwf(path: Path) -> List[Station]:
    """
    Parse fixed-width GHCN-Daily stations file (ghcnd-stations.txt).

    Field layout (1-based):
      1-11   ID
      13-20  LATITUDE
      22-30  LONGITUDE
      32-37  ELEVATION
      39-40  STATE
      42-71  NAME
      73-75  GSN FLAG
      77-79  HCN/CRN FLAG
      81-85  WMO ID
    """
    stations: List[Station] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if len(line) < 30:
                continue
            sid = line[0:11].strip()
            lat = parse_float(line[12:20])
            lon = parse_float(line[21:30])
            elev = parse_float(line[31:37]) if len(line) >= 37 else None
            state = line[38:40].strip() if len(line) >= 40 else ""
            name = line[41:71].strip() if len(line) >= 71 else ""
            gsn = line[72:75].strip() if len(line) >= 75 else ""
            hcn = line[76:79].strip() if len(line) >= 79 else ""
            wmo = line[80:85].strip() if len(line) >= 85 else ""
            if not sid or lat is None or lon is None:
                continue
            country = sid[:2]
            stations.append(
                Station(
                    id=sid,
                    latitude=float(lat),
                    longitude=float(lon),
                    elevation_m=elev,
                    name=name,
                    country=country,
                    state=state,
                    gsn_flag=gsn,
                    hcn_crn_flag=hcn,
                    wmo_id=wmo,
                )
            )
    return stations


def nearest_stations(
    stations: Iterable[Station],
    lat: float,
    lon: float,
    radius_km: float,
    limit: int,
    name_query: Optional[str] = None,
    prefer_quality: bool = False,
    prefer_us: bool = True,
) -> List[Station]:
    q = (name_query or "").strip().lower()
    out: List[Station] = []
    for s in stations:
        if prefer_us and not s.id.startswith("US"):
            continue
        if q:
            hay = f"{s.name} {s.state} {s.id}".lower()
            if q not in hay:
                continue
        d = haversine_km(lat, lon, s.latitude, s.longitude)
        if d <= radius_km:
            out.append(Station(**{**s.__dict__, "distance_km": d}))

    # For game-day weather, prioritize distance over quality flags
    # Airport stations (USW prefix) are typically better despite lacking HCN/CRN flags
    def sort_key(st: Station) -> tuple:
        # 1. Distance first (most important for game location)
        # 2. Airport stations preferred (USW prefix = Weather Service airports)
        # 3. Quality flags as tiebreaker
        is_airport = st.id.startswith("USW")
        has_quality = bool(st.gsn_flag or st.hcn_crn_flag)
        
        if prefer_quality:
            # When quality explicitly requested, use hybrid approach
            return (st.distance_km, 0 if is_airport else 1, 0 if has_quality else 1)
        else:
            # Default: distance + prefer airports
            return (st.distance_km, 0 if is_airport else 1)

    out.sort(key=sort_key)
    return out[:limit]


def request_with_retries(
    url: str,
    params: Dict[str, Any],
    timeout_s: float,
    headers: Dict[str, str],
    retries: int = 5,
) -> requests.Response:
    backoff = 1.0
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout_s, headers=headers)
            if r.status_code in (429, 500, 502, 503, 504):
                if attempt == retries:
                    return r
                ra = r.headers.get("Retry-After")
                wait = float(ra) if (ra and ra.isdigit()) else backoff
                time.sleep(wait)
                backoff = min(backoff * 2.0, 16.0)
                continue
            return r
        except Exception as e:
            last_exc = e
            if attempt == retries:
                raise
            time.sleep(backoff)
            backoff = min(backoff * 2.0, 16.0)
    raise RuntimeError(f"request_with_retries failed: {last_exc}")


def ncei_daily_summaries(
    station_id: str,
    start_date: str,
    end_date: str,
    datatypes: List[str],
    units: str = "standard",
    timeout: int = 45,
) -> Tuple[int, Any, List[str], List[str]]:
    """
    Returns:
      (status_code, payload_json_or_text, missing_datatypes, present_requested_datatypes)
    """
    params = {
        "dataset": "daily-summaries",
        "stations": station_id,
        "startDate": start_date,
        "endDate": end_date,
        "dataTypes": ",".join(datatypes),
        "format": "json",
        "units": units,
        "includeStationName": "true",
        "includeStationLocation": "1",
    }
    headers = {"User-Agent": "QuantCup-NCEI-Smoketest/1.1 (contact: you@example.com)"}
    r = request_with_retries(NCEI_DAILY_ENDPOINT, params=params, timeout_s=timeout, headers=headers)

    payload: Any
    try:
        payload = r.json()
    except Exception:
        payload = {"raw_text": (r.text or "")[:2000]}

    missing: List[str] = []
    present: List[str] = []

    if r.status_code == 200 and isinstance(payload, list) and payload:
        requested = set(datatypes)
        present_set = set()
        # Union over all rows to detect datatypes that appear later
        for row in payload:
            if isinstance(row, dict):
                present_set |= (set(row.keys()) & requested)
        present = sorted(present_set)
        missing = sorted(list(requested - present_set))

    return r.status_code, payload, missing, present


def to_game_features(rows: List[dict]) -> Dict[str, Any]:
    if not rows:
        return {}
    latest = rows[-1]  # assume endDate is "game day" in this smoketest
    tmax = parse_float(latest.get("TMAX") or "")
    tmin = parse_float(latest.get("TMIN") or "")
    prcp = parse_float(latest.get("PRCP") or "0")

    temp_mean = (tmax + tmin) / 2 if (tmax is not None and tmin is not None) else None

    return {
        "date": latest.get("DATE"),
        "station": latest.get("STATION"),
        "temp_max": tmax,
        "temp_min": tmin,
        "temp_mean": temp_mean,
        "precip": prcp,
        "precip_any": (prcp is not None and prcp > 0),
        "cold_weather": (tmin is not None and tmin <= 32),
        "hot_weather": (tmax is not None and tmax >= 85),
        "raw": latest,
    }


def validate_dates(start_s: str, end_s: str) -> None:
    start_d = date.fromisoformat(start_s)
    end_d = date.fromisoformat(end_s)
    if start_d > end_d:
        raise ValueError("start must be <= end")
    # NOTE: some NCEI datasets lag; this is just a guardrail
    # Allow recent dates, but warn if clearly future.
    today = date.today()
    if start_d > today or end_d > today:
        print(f"WARNING: dates appear to be in the future ({start_s} to {end_s}). NCEI typically has a 1-2 day lag.", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--datatypes", default="TMAX,TMIN,PRCP,AWND", help="Comma-separated")
    ap.add_argument("--units", default="standard", choices=["standard", "metric"])
    ap.add_argument("--radius_km", type=float, default=50.0)
    ap.add_argument("--max_candidates", type=int, default=10)
    ap.add_argument("--name_query", default="", help="Optional substring filter (e.g. 'CHARLOTTE')")
    ap.add_argument("--stations", default="", help="Optional comma-separated station IDs (skip lookup)")
    ap.add_argument("--prefer_quality", action="store_true", help="Prefer quality-flagged stations over distance")
    ap.add_argument("--no_prefer_us", action="store_true", help="Include non-US stations")
    args = ap.parse_args()

    validate_dates(args.start, args.end)

    datatypes = [x.strip() for x in args.datatypes.split(",") if x.strip()]
    meta: Dict[str, Any] = {
        "fetched_at_utc": utc_now_iso(),
        "input": {
            "lat": args.lat,
            "lon": args.lon,
            "start": args.start,
            "end": args.end,
            "datatypes": datatypes,
            "units": args.units,
        },
        "notes": [
            "daily-summaries requires stations=...; bbox alone can 400.",
            "Not all stations report all datatypes (e.g., AWND often missing).",
        ],
        "station_source": None,
        "station_candidates": None,
    }

    manual_stations = [x.strip() for x in args.stations.split(",") if x.strip()]
    candidates: List[Station] = []

    if manual_stations:
        meta["station_source"] = "manual"
        candidates = [
            Station(
                id=s,
                latitude=0.0,
                longitude=0.0,
                elevation_m=None,
                name="",
                country="",
                state="",
                gsn_flag="",
                hcn_crn_flag="",
                wmo_id="",
                distance_km=0.0,
            )
            for s in manual_stations
        ]
    else:
        url = os.environ.get("GHCND_STATIONS_URL") or DEFAULT_GHCND_STATIONS_URL
        cdir = cache_dir()
        stations_path = cdir / "ghcnd-stations.txt"
        download_if_needed(url, stations_path, max_age_days=30)

        stations = load_stations_fwf(stations_path)
        meta["station_source"] = "ghcnd-stations.txt"
        meta["station_file"] = str(stations_path)
        meta["stations_loaded"] = len(stations)

        candidates = nearest_stations(
            stations=stations,
            lat=args.lat,
            lon=args.lon,
            radius_km=args.radius_km,
            limit=args.max_candidates,
            name_query=args.name_query or None,
            prefer_quality=args.prefer_quality,
            prefer_us=not args.no_prefer_us,
        )
        meta["station_candidates"] = [
            {
                "id": s.id,
                "name": s.name,
                "state": s.state,
                "lat": s.latitude,
                "lon": s.longitude,
                "distance_km": round(s.distance_km, 2),
                "gsn": bool(s.gsn_flag),
                "hcn_crn": bool(s.hcn_crn_flag),
            }
            for s in candidates
        ]

    attempts: List[Dict[str, Any]] = []
    for s in candidates:
        sid = s.id
        status, payload, missing, present = ncei_daily_summaries(
            station_id=sid,
            start_date=args.start,
            end_date=args.end,
            datatypes=datatypes,
            units=args.units,
        )
        attempts.append(
            {
                "station": sid,
                "status": status,
                "present_datatypes": present,
                "missing_datatypes": missing,
            }
        )

        if status == 200 and isinstance(payload, list) and len(payload) > 0:
            out = {
                "meta": meta,
                "selected_station": sid,
                "attempts": attempts,
                "rows": payload,
                "game_features": to_game_features(payload),
            }
            print(json.dumps(out, indent=2))
            return 0

    out = {
        "meta": meta,
        "attempts": attempts,
        "error": "No station returned data. Try a larger radius, fewer datatypes, or different dates.",
    }
    print(json.dumps(out, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
