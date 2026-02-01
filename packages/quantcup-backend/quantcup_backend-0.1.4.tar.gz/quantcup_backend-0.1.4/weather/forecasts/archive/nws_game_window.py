#!/usr/bin/env python3
"""
nws_game_window.py
QuantCup-style weather extraction for a game window using NWS Weather.gov API.

Given:
  - stadium lat/lon
  - kickoff time (ISO-8601 with timezone, or naive assumed local)
Produces:
  - hourly slice for kickoff window
  - computed flags (wind, cold, precip)
  - compact summary JSON

Docs:
- https://www.weather.gov/documentation/services-web-api
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests


DEFAULT_UA = "QuantCup (https://quantcup.example, contact@quantcup.example)"
ACCEPT = "application/geo+json"


def request_json(url: str, headers: Dict[str, str], timeout_s: float = 15.0, retries: int = 6) -> Dict[str, Any]:
    backoff = 1.0
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout_s)
            if r.status_code in (429, 500, 502, 503, 504):
                if attempt == retries:
                    r.raise_for_status()
                ra = r.headers.get("Retry-After")
                wait = float(ra) if (ra and ra.isdigit()) else backoff
                time.sleep(wait)
                backoff = min(backoff * 2.0, 16.0)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            if attempt == retries:
                break
            time.sleep(backoff)
            backoff = min(backoff * 2.0, 16.0)
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


_WIND_RE = re.compile(r"(\d+)\s*(?:to\s*(\d+))?\s*mph", re.IGNORECASE)


def parse_wind_mph(wind_speed: str) -> Tuple[Optional[int], Optional[int]]:
    """
    NWS windSpeed strings are usually like:
      "8 mph" or "2 to 6 mph"
    Returns (min_mph, max_mph)
    """
    if not wind_speed:
        return (None, None)
    m = _WIND_RE.search(wind_speed)
    if not m:
        return (None, None)
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    return (min(a, b), max(a, b))


def parse_iso(dt_str: str) -> datetime:
    # datetime.fromisoformat handles offsets like -05:00
    return datetime.fromisoformat(dt_str)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--kickoff", type=str, required=True, help="ISO-8601, e.g. 2026-01-19T20:15:00-05:00")
    p.add_argument("--window_hours", type=float, default=4.0, help="Hours after kickoff to include")
    p.add_argument("--pre_hours", type=float, default=1.0, help="Hours before kickoff to include")
    p.add_argument("--ua", type=str, default=DEFAULT_UA)
    p.add_argument("--raw_hours", type=int, default=0, help="If >0, include that many raw hourly periods in output")
    args = p.parse_args()

    headers = {"User-Agent": args.ua, "Accept": ACCEPT}

    points_url = f"https://api.weather.gov/points/{args.lat:.4f},{args.lon:.4f}"
    points = request_json(points_url, headers=headers)
    props = points.get("properties", {})

    hourly_url = props.get("forecastHourly")
    if not hourly_url:
        raise RuntimeError("Missing forecastHourly in points response.")

    hourly = request_json(hourly_url, headers=headers)
    periods: List[Dict[str, Any]] = hourly.get("properties", {}).get("periods", [])
    if not periods:
        raise RuntimeError("No hourly periods returned.")

    kickoff = parse_iso(args.kickoff)
    start = kickoff - timedelta(hours=args.pre_hours)
    end = kickoff + timedelta(hours=args.window_hours)

    slice_periods: List[Dict[str, Any]] = []
    for pr in periods:
        st = pr.get("startTime")
        if not st:
            continue
        t = parse_iso(st)
        if start <= t < end:
            slice_periods.append(pr)

    # Compute metrics
    temps = [pr.get("temperature") for pr in slice_periods if isinstance(pr.get("temperature"), (int, float))]
    wind_maxes = []
    precip_probs = []
    short_fc = []

    for pr in slice_periods:
        mn, mx = parse_wind_mph(pr.get("windSpeed", ""))
        if mx is not None:
            wind_maxes.append(mx)

        pop = pr.get("probabilityOfPrecipitation", {})
        if isinstance(pop, dict):
            val = pop.get("value")
            if isinstance(val, (int, float)):
                precip_probs.append(val)

        sf = pr.get("shortForecast")
        if sf:
            short_fc.append(sf)

    temp_min = min(temps) if temps else None
    temp_max = max(temps) if temps else None
    wind_max = max(wind_maxes) if wind_maxes else None
    pop_max = max(precip_probs) if precip_probs else None

    # Simple flags (tune thresholds later)
    flags = {
        "windy": (wind_max is not None and wind_max >= 15),
        "very_windy": (wind_max is not None and wind_max >= 25),
        "cold": (temp_min is not None and temp_min <= 32),
        "very_cold": (temp_min is not None and temp_min <= 20),
        "precip_likely": (pop_max is not None and pop_max >= 40),
        "precip_very_likely": (pop_max is not None and pop_max >= 60),
    }

    out = {
        "input": {
            "lat": args.lat,
            "lon": args.lon,
            "kickoff": args.kickoff,
            "window": {"start": start.isoformat(), "end": end.isoformat()},
        },
        "location_hint": {
            "cwa": props.get("cwa"),
            "gridId": props.get("gridId"),
            "gridX": props.get("gridX"),
            "gridY": props.get("gridY"),
        },
        "metrics": {
            "temp_min_f": temp_min,
            "temp_max_f": temp_max,
            "wind_max_mph": wind_max,
            "precip_prob_max_pct": pop_max,
        },
        "flags": flags,
        "headline": {
            "most_common_shortForecast": max(set(short_fc), key=short_fc.count) if short_fc else None
        },
    }

    if args.raw_hours and slice_periods:
        out["hourly_slice"] = slice_periods[: args.raw_hours]

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
