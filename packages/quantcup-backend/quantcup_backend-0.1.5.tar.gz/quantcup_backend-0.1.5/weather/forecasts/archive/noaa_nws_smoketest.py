#!/usr/bin/env python3
"""
noaa_nws_smoketest.py
Smoke-test the NWS Weather.gov API:
  1) /points/{lat},{lon} to discover the grid + forecast URLs
  2) fetch forecast (12h periods) and hourly forecast
  3) print a compact summary you can plug into a QuantCup "game weather" module

Docs:
- https://www.weather.gov/documentation/services-web-api
- https://api.weather.gov/

Notes:
- NWS requires a User-Agent identifying your app (ideally with contact info). :contentReference[oaicite:1]{index=1}
- Use /points first, then follow the returned forecast URLs. :contentReference[oaicite:2]{index=2}
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests


DEFAULT_UA = "QuantCup (https://quantcup.example, contact@quantcup.example)"
DEFAULT_ACCEPT = "application/geo+json"  # GeoJSON is the typical default. :contentReference[oaicite:3]{index=3}


def _sleep_with_jitter(seconds: float) -> None:
    # tiny jitter without importing random (keeps script minimal)
    frac = (time.time() % 1.0) * 0.25
    time.sleep(max(0.0, seconds + frac))


def request_json(
    url: str,
    headers: Dict[str, str],
    timeout_s: float = 15.0,
    max_retries: int = 6,
) -> Dict[str, Any]:
    """
    GET JSON with basic retry/backoff on 429/5xx.
    NWS rate limit is not published; when exceeded, retry shortly. :contentReference[oaicite:4]{index=4}
    """
    backoff = 1.0
    last_err: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout_s)
            if resp.status_code == 304:
                raise RuntimeError("Got 304 Not Modified but no cache layer implemented in this script.")
            if resp.status_code in (429, 500, 502, 503, 504):
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait_s = float(retry_after)
                    except ValueError:
                        wait_s = backoff
                else:
                    wait_s = backoff

                if attempt == max_retries:
                    resp.raise_for_status()

                _sleep_with_jitter(wait_s)
                backoff = min(backoff * 2.0, 16.0)
                continue

            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            last_err = e
            if attempt == max_retries:
                break
            _sleep_with_jitter(backoff)
            backoff = min(backoff * 2.0, 16.0)

    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def summarize_forecast_periods(periods: list[dict], limit: int = 6) -> list[dict]:
    out = []
    for p in periods[:limit]:
        out.append(
            {
                "name": p.get("name"),
                "startTime": p.get("startTime"),
                "endTime": p.get("endTime"),
                "temperature": p.get("temperature"),
                "temperatureUnit": p.get("temperatureUnit"),
                "windSpeed": p.get("windSpeed"),
                "windDirection": p.get("windDirection"),
                "shortForecast": p.get("shortForecast"),
                "detailedForecast": p.get("detailedForecast"),
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="NOAA/NWS API smoke test for QuantCup.")
    parser.add_argument("--lat", type=float, required=True, help="Latitude (e.g., 35.2251)")
    parser.add_argument("--lon", type=float, required=True, help="Longitude (e.g., -80.8529)")
    parser.add_argument("--ua", type=str, default=DEFAULT_UA, help="User-Agent string (include contact info)")
    parser.add_argument("--limit", type=int, default=6, help="How many forecast periods to print")
    parser.add_argument("--raw", action="store_true", help="Print raw JSON (points + forecast URLs)")
    args = parser.parse_args()

    headers = {
        "User-Agent": args.ua,           # required :contentReference[oaicite:5]{index=5}
        "Accept": DEFAULT_ACCEPT,        # GeoJSON :contentReference[oaicite:6]{index=6}
    }

    points_url = f"https://api.weather.gov/points/{args.lat:.4f},{args.lon:.4f}"
    points = request_json(points_url, headers=headers)

    props = points.get("properties", {})
    forecast_url = props.get("forecast")          # 12h periods :contentReference[oaicite:7]{index=7}
    hourly_url = props.get("forecastHourly")      # hourly :contentReference[oaicite:8]{index=8}
    grid_url = props.get("forecastGridData")      # raw grid data :contentReference[oaicite:9]{index=9}
    rel_loc = props.get("relativeLocation", {}).get("properties", {})
    wfo = props.get("cwa")  # Weather Forecast Office id (often)
    grid_id = props.get("gridId")
    grid_x = props.get("gridX")
    grid_y = props.get("gridY")

    if not forecast_url or not hourly_url:
        raise RuntimeError("Points response missing forecast URLs. Try a different lat/lon.")

    forecast = request_json(forecast_url, headers=headers)
    hourly = request_json(hourly_url, headers=headers)

    out = {
        "meta": {
            "fetched_at_utc": iso_now(),
            "input": {"lat": args.lat, "lon": args.lon},
            "location_hint": {
                "city": rel_loc.get("city"),
                "state": rel_loc.get("state"),
            },
            "grid": {"wfo": wfo, "gridId": grid_id, "gridX": grid_x, "gridY": grid_y},
            "endpoints": {
                "points": points_url,
                "forecast": forecast_url,
                "forecastHourly": hourly_url,
                "forecastGridData": grid_url,
            },
        },
        "forecast_12h": summarize_forecast_periods(forecast.get("properties", {}).get("periods", []), args.limit),
        "forecast_hourly": summarize_forecast_periods(hourly.get("properties", {}).get("periods", []), args.limit),
    }

    if args.raw:
        print(json.dumps({"points": points, "forecast": forecast, "hourly": hourly}, indent=2))
    else:
        print(json.dumps(out, indent=2))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
