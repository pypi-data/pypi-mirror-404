from __future__ import annotations

import datetime as dt
import math
import os
import time
from dataclasses import dataclass
from functools import wraps
from io import StringIO
from pathlib import Path
from typing import Iterable, Optional, Dict, Any, List
import requests
import pandas as pd

from commonv2.core.logging import setup_logger

# Set up logger
logger = setup_logger('weather.historical.ncei_client', project_name='WEATHER')


BASE = "https://www.ncei.noaa.gov/access/services/data/v1"
SEARCH_BASE = "https://www.ncei.noaa.gov/access/services/search/v1"
GHCND_STATIONS_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"


@dataclass(frozen=True)
class Station:
    """GHCN-D station metadata."""
    id: str
    latitude: float
    longitude: float
    elevation_m: Optional[float]
    name: str
    distance_km: float = 0.0


def _cache_dir() -> Path:
    """Get cache directory for station metadata."""
    base = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    p = Path(base) / "quantcup" / "ncei"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _parse_float(s: str) -> Optional[float]:
    """Safely parse float from string."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in kilometers."""
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _download_if_needed(url: str, dest: Path, max_age_days: int = 30) -> None:
    """Download file if not cached or if cache is stale."""
    if dest.exists():
        age_sec = time.time() - dest.stat().st_mtime
        if age_sec < max_age_days * 86400:
            logger.debug(f"Using cached {dest.name} (age: {age_sec/86400:.1f} days)")
            return
    
    logger.info(f"Downloading {url} to {dest}")
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    headers = {"User-Agent": "QuantCup-NCEI-Client/1.0"}
    with requests.get(url, stream=True, timeout=60, headers=headers) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
    tmp.replace(dest)
    logger.info(f"Downloaded {dest.name}")


def _load_stations_fwf(path: Path) -> List[Station]:
    """
    Parse fixed-width GHCN-Daily stations file.
    
    Field layout (1-based):
      1-11   ID
      13-20  LATITUDE
      22-30  LONGITUDE
      32-37  ELEVATION
      39-71  NAME
    """
    stations: List[Station] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if len(line) < 30:
                continue
            sid = line[0:11].strip()
            lat = _parse_float(line[12:20])
            lon = _parse_float(line[21:30])
            elev = _parse_float(line[31:37]) if len(line) >= 37 else None
            name = line[41:71].strip() if len(line) >= 71 else ""
            if not sid or lat is None or lon is None:
                continue
            stations.append(Station(
                id=sid,
                latitude=float(lat),
                longitude=float(lon),
                elevation_m=elev,
                name=name,
            ))
    return stations


def _nearest_stations(
    stations: List[Station],
    lat: float,
    lon: float,
    radius_km: float,
    limit: int = 10,
) -> List[Station]:
    """
    Find nearest stations within radius, prioritizing COOP/airport stations.
    
    US1* stations (volunteer) typically don't have normals data.
    USC* (COOP) and USW* (airport) stations are  best for climatology.
    """
    out: List[Station] = []
    for s in stations:
        d = _haversine_km(lat, lon, s.latitude, s.longitude)
        if d <= radius_km:
            out.append(Station(**{**s.__dict__, "distance_km": d}))
    
    # Sort: COOP/airport first, then by distance
    def sort_key(st: Station) -> tuple:
        is_airport = st.id.startswith("USW")  # Weather Service airports (best)
        is_coop = st.id.startswith("USC")  # COOP stations (great)
        is_volunteer = st.id.startswith("US1")  # Volunteer stations (rarely have normals)
        
        # Priority tiers: 0=airport, 1=COOP, 2=other, 999=volunteer
        if is_airport:
            tier = 0
        elif is_coop:
            tier = 1
        elif is_volunteer:
            tier = 999  # Deprioritize volunteers
        else:
            tier = 2
        
        return (tier, st.distance_km)
    
    out.sort(key=sort_key)
    return out[:limit]


def rate_limited(max_per_second: float = 10.0):
    """
    Rate limiting decorator to prevent overwhelming the NCEI API.
    Default: 10 requests per second (conservative).
    """
    min_interval = 1.0 / max_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator


class NCEIClient:
    """
    Thin wrapper for the NCEI Access Data Service (v1).
    Returns pandas DataFrames for common datasets useful in a forecasting context.
    """

    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 60):
        self.s = session or requests.Session()
        self.timeout = timeout

    # -------- core request helper --------
    @rate_limited(max_per_second=10.0)
    def _get(self, dataset: str, params: Dict[str, Any]) -> pd.DataFrame:
        qp = dict(params)
        qp["dataset"] = dataset
        qp.setdefault("format", "json")
        qp.setdefault("includeStationName", "true")
        qp.setdefault("includeStationLocation", "true")
        qp.setdefault("units", "standard")

        logger.debug(f"NCEI API request: dataset={dataset}, params={qp}")

        r = self.s.get(BASE, params=qp, timeout=self.timeout)
        
        logger.debug(f"NCEI API response: status={r.status_code}, length={len(r.text)}")
        
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            # Surface server message to help debugging (NCEI returns JSON/plain text on 400)
            msg = r.text.strip()
            logger.error(f"NCEI API error: {e} | payload: {msg[:500]}")
            raise requests.HTTPError(f"{e} | payload: {msg[:500]}") from None

        if not r.text.strip():
            logger.warning(f"NCEI API returned empty response for dataset={dataset}")
            return pd.DataFrame()
        return pd.read_json(StringIO(r.text))

    # -------- daily summaries (observed) --------
    def daily_summaries(
        self,
        stations: Iterable[str],
        start_date: str | dt.date,
        end_date: str | dt.date,
        *,
        data_types: Iterable[str] = ("TMAX", "TMIN", "PRCP", "SNOW", "AWND"),
        units: str = "standard",
    ) -> pd.DataFrame:
        """
        GHCND DAILY SUMMARY observations. Useful for backfills and verifying model outputs.
        """
        sd = start_date if isinstance(start_date, str) else start_date.isoformat()
        ed = end_date if isinstance(end_date, str) else end_date.isoformat()

        params = {
            "stations": ",".join(stations),
            "startDate": sd,
            "endDate": ed,
            "dataTypes": ",".join(data_types),
            "units": units,
        }
        df = self._get("daily-summaries", params)
        # Optional: tidy common numeric columns
        for col in ("TMIN", "TMAX", "PRCP", "SNOW", "AWND"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "DATE" in df.columns:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
        return df

    # -------- Robust station discovery using GHCN-D metadata --------
    def _get_station_candidates(
        self,
        lat: float,
        lon: float,
        *,
        radius_km: float = 50.0,
        limit: int = 10,
    ) -> List[Station]:
        """
        Get nearby GHCN-D stations using official fixed-width station list.
        More reliable than Search API for normals coverage.
        
        Downloads and caches ghcnd-stations.txt (~30MB, ~120k stations).
        """
        cache = _cache_dir()
        stations_path = cache / "ghcnd-stations.txt"
        
        # Download/update if needed (30-day cache)
        _download_if_needed(GHCND_STATIONS_URL, stations_path, max_age_days=30)
        
        # Load and filter
        all_stations = _load_stations_fwf(stations_path)
        logger.info(f"Loaded {len(all_stations)} stations from {stations_path.name}")
        
        # Find nearest within radius
        candidates = _nearest_stations(all_stations, lat, lon, radius_km, limit)
        logger.info(f"Found {len(candidates)} stations within {radius_km}km")
        
        return candidates

    # -------- normals (climatology) for daily values --------
    def normals_daily(
        self,
        stations: Iterable[str] | None = None,
        *,
        data_types: Iterable[str] = (
            "DLY-TMAX-NORMAL",
            "DLY-TMIN-NORMAL",
            "DLY-TMAX-STDDEV",
            "DLY-TMIN-STDDEV",
            "DLY-PRCP-NORMAL",
            "DLY-PRCP-PCTALL-GE001HI",
            "DLY-PRCP-50PCTL",
            "DLY-SNOW-PCTALL-GE001TI",
            "DLY-SNOW-50PCTL",
        ),
        units: str = "standard",
        start_date: str = "0001-01-01",
        end_date: str   = "0001-12-31",
    ) -> pd.DataFrame:
        """
        Daily climatology normals (1991–2020 period).
        
        CRITICAL: NCEI normals-daily-1991-2020 dataset uses year 0001 as the placeholder year.
        Day-of-year normals are stored as 0001-MM-DD (not 2010 or 2000).
        Must query with start/end dates in year 0001, otherwise returns empty.
        
        Args:
            stations: Station IDs (bare or GHCND: prefixed - will be normalized)
            data_types: Which normals fields to fetch
            units: "standard" or "metric"
            start_date: Start of query range (must be year 0001 for 1991-2020 normals)
            end_date: End of query range (must be year 0001 for 1991-2020 normals)
        """
        params = {
            "dataTypes": ",".join(data_types),
            "units": units,
            "startDate": start_date,
            "endDate": end_date,
        }
        if stations:
            def _strip_prefix(s: str) -> str:
                """Strip GHCND: prefix - normals endpoint requires bare station IDs."""
                s = s.strip()
                return s.split(":", 1)[1] if ":" in s else s
            params["stations"] = ",".join(_strip_prefix(s) for s in stations)
        else:
            return pd.DataFrame()

        df = self._get("normals-daily-1991-2020", params)

        if "DATE" in df.columns:
            # Normals daily returns MM-DD format (no year) - convert to datetime with dummy year 2000 for DOY calc
            # Use 2000 (leap year) to ensure Feb 29 gets DOY 60
            df["DATE"] = pd.to_datetime("2000-" + df["DATE"].astype(str), format="%Y-%m-%d", errors="coerce")
            df["DOY"] = df["DATE"].dt.dayofyear

        for col in data_types:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    # ---- helper: find a normals-capable station near a point ----
    def find_normals_station_near(
        self,
        lat: float,
        lon: float,
        *,
        radius_km: float = 50.0,
        limit: int = 10
    ) -> Optional[str]:
        """
        Find a nearby station that HAS normals using GHCN-D station list.
        Prefers COOP/USC/Airport stations which typically have better normals coverage.
        Returns a bare station ID (e.g., 'USW00013881')or None.
        
        Args:
            lat: Latitude of search center
            lon: Longitude of search center
            radius_km: Search radius in kilometers (default: 50km)
            limit: Max number of candidates to test (default: 10)
        """
        # Get nearby stations from GHCN-D metadata
        candidates = self._get_station_candidates(lat, lon, radius_km=radius_km, limit=limit)
        
        if not candidates:
            logger.error(f"No stations found within {radius_km}km of ({lat}, {lon})")
            return None
        
        logger.info(f"Testing {len(candidates)} candidates for normals data: {[s.id for s in candidates[:5]]}")
            
        # Test each candidate to ensure it actually has normals data
        for station in candidates:
            logger.debug(f"Testing normals for {station.id} ({station.name}, {station.distance_km:.1f}km away)")
            try:
                df = self.normals_daily([station.id])
                logger.debug(f"Station {station.id} returned {len(df) if df is not None else 0} rows")
                if df is not None and not df.empty:
                    # Return bare station ID (normals endpoint needs bare IDs)
                    logger.info(f"✓ Found working normals station: {station.id} ({station.name}, {station.distance_km:.1f}km, {len(df)} records)")
                    return station.id
                else:
                    logger.debug(f"Station {station.id} returned empty result, trying next...")
            except Exception as e:
                logger.warning(f"Failed to fetch normals for {station.id}: {e}")
                continue
                
        logger.error(f"None of the {len(candidates)} candidate stations returned usable normals data")
        return None

    # -------- hourly observations (for wind/pressure features) --------
    def global_hourly(
        self,
        stations: Iterable[str],
        start_datetime: str | dt.datetime,
        end_datetime: str | dt.datetime,
        *,
        data_types: Iterable[str] = ("TMP", "WND", "PRES", "AA1"),  # temp, wind, pressure, precip obs
        units: str = "standard",
    ) -> pd.DataFrame:
        """
        Hourly observations from the 'global-hourly' dataset (formerly ISD).
        Good for detailed wind features or matching past kickoff hours.
        """
        sd = (
            start_datetime
            if isinstance(start_datetime, str)
            else start_datetime.isoformat()
        )
        ed = end_datetime if isinstance(end_datetime, str) else end_datetime.isoformat()

        params = {
            "stations": ",".join(stations),
            "startDate": sd,
            "endDate": ed,
            "dataTypes": ",".join(data_types),
            "units": units,
        }
        df = self._get("global-hourly", params)
        if "DATE" in df.columns:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce", utc=True)
        # A few helpful parses
        # TMP, WND often encoded strings (e.g., "018.0,1") depending on sub-code; keep as string or parse as needed here.
        return df

    # -------- convenience: get "expected" (climo) for a target date --------
    def normals_for_date(
        self,
        station: str,
        target_date: str | dt.date,
        *,
        cache_normals: Optional[pd.DataFrame] = None,
    ) -> pd.Series | None:
        """
        Returns a one-row Series with climatological 'expected' values for a station on the given calendar date.
        Use this in your pipeline as a pre-forecast fallback (e.g., >7 days out).
        
        Includes temperature normals & stddev, precipitation probabilities & percentiles,
        and snow probabilities & percentiles for full parity with CSV-based forecasting.
        
        Handles leap years: Feb 29 falls back to Feb 28 data if DOY 60 is not available.
        """
        date = target_date if isinstance(target_date, str) else target_date.isoformat()
        date = pd.to_datetime(date, errors="coerce")
        if pd.isna(date):
            return None
        doy = int(date.strftime("%j"))

        if cache_normals is None:
            normals = self.normals_daily([station])
        else:
            normals = cache_normals
        if normals is None or normals.empty or "STATION" not in normals.columns:
            return None
        def _core_id(s: str) -> str:
            return str(s).replace("GHCND:", "")
        core = _core_id(station)
        st = normals[normals["STATION"].map(lambda x: _core_id(x) == core)].copy()
        if st.empty or "DOY" not in st.columns:
            return None
        
        # Handle leap year: use Feb 28 data for Feb 29 if DOY 60 not available
        row = st.loc[st["DOY"] == doy]
        if row.empty and doy == 60:
            logger.debug(f"Feb 29 (DOY 60) not found for station {station}, falling back to Feb 28 (DOY 59)")
            doy = 59
            row = st.loc[st["DOY"] == doy]
        
        if row.empty:
            return None
        
        # return first match as a neat Series with friendlier names + all required fields
        r = row.iloc[0]
        out = pd.Series(
            {
                "station": station,
                "name": r.get("NAME"),
                "lat": r.get("LATITUDE"),
                "lon": r.get("LONGITUDE"),
                "elev_m": r.get("ELEVATION"),
                "date": date.date(),
                # Temperature normals & variability
                "tmax_normal": r.get("DLY-TMAX-NORMAL"),
                "tmin_normal": r.get("DLY-TMIN-NORMAL"),
                "tmax_stddev": r.get("DLY-TMAX-STDDEV"),
                "tmin_stddev": r.get("DLY-TMIN-STDDEV"),
                # Precipitation probabilities & statistics
                "prcp_normal": r.get("DLY-PRCP-NORMAL"),
                "prcp_pct_ge001": r.get("DLY-PRCP-PCTALL-GE001HI"),  # Probability ≥0.01"
                "prcp_50pctl": r.get("DLY-PRCP-50PCTL"),             # Median if wet
                # Snow probabilities & statistics
                "snow_pct_ge001": r.get("DLY-SNOW-PCTALL-GE001TI"),  # Probability ≥0.1"
                "snow_50pctl": r.get("DLY-SNOW-50PCTL"),             # Median if snow
            }
        )
        return out


# -------------------------
# Example usage (commented)
# -------------------------
if __name__ == "__main__":
    STATION = "USW00013881"   # Charlotte Douglas
    client = NCEIClient()

    # 1) Observations
    obs = client.daily_summaries([STATION], "2025-08-01", "2025-08-19")
    print(obs.head())

    # 2) Normals: airport may be empty → auto-discover nearby normals station
    normals = client.normals_daily([STATION])
    ghcnd_near = None
    if normals.empty:
        # use airport lat/lon from your obs frame if present
        lat = float(obs.get("LATITUDE", pd.Series([None])).iloc[0]) if not obs.empty else 35.2225
        lon = float(obs.get("LONGITUDE", pd.Series([None])).iloc[0]) if not obs.empty else -80.9543
        
        # Use Search Service v1 to discover nearby normals stations (no token required)
        ghcnd_near = client.find_normals_station_near(lat, lon)
        print("Nearest normals-capable station:", ghcnd_near)
        if ghcnd_near:
            normals = client.normals_daily([ghcnd_near.replace("GHCND:", "")])
    print(normals.head())

    # 3) Hourly observations for a training window (wind features, etc.)
    hourly = client.global_hourly(
        stations=[STATION],
        start_datetime="2025-08-01T00:00:00Z",
        end_datetime="2025-08-05T00:00:00Z",
    )
    print(hourly.head())

    # 4) Get "expected" values for a future game date (climatology fallback)
    prefer_station = (
        ghcnd_near.replace("GHCND:", "") if ghcnd_near else STATION
    )
    expected = client.normals_for_date(prefer_station, "2025-09-07", cache_normals=normals)
    print(expected)
