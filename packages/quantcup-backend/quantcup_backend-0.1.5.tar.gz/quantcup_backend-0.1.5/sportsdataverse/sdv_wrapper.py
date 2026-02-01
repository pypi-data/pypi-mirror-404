"""
sdv_wrapper.py — Minimal dynamic wrapper around sportsdataverse

Features
--------
- Discovers ALL callable endpoints in `sportsdataverse.<sport>` submodules whose names
  start with `load_` or `espn_` (e.g., load_nfl_pbp, espn_nfl_game_rosters).
- Exposes a unified interface to call one, many, or ALL endpoints with shared kwargs.
- Normalizes outputs to pandas if requested (sportsdataverse often returns Polars by default).
- Lightweight retry/backoff for flaky network calls (ESPN endpoints).
- Simple include/exclude filters so you can limit which endpoints run.
- Returns a dict: {endpoint_name: object_or_exception}

Usage
-----
from sdv_wrapper import SportsDataVerseClient

client = SportsDataVerseClient(prefer_pandas=True, max_retries=2)
# List available sports
print(client.available_sports())  # e.g., ["nfl", "cfb", "nba", "wnba", "nhl"] (depends on installed sdv version)

# List discovered endpoints for NFL
print(client.list_endpoints("nfl"))

# Call a single endpoint
pbp = client.call("nfl", "load_nfl_pbp", shared_kwargs={"seasons": [2024]})

# Call many endpoints with shared kwargs
out = client.fetch_many(
    "nfl",
    endpoints=["load_nfl_injuries", "espn_nfl_game_rosters"],
    shared_kwargs={"return_as_pandas": True},
    per_endpoint_kwargs={"espn_nfl_game_rosters": {"game_id": 401220403}}
)

# Call ALL endpoints (discovered dynamically)
all_out = client.fetch_all(
    "nfl",
    shared_kwargs={"seasons": [2024]},  # passed to any function that accepts it
    include=None,  # or a whitelist like ["load_nfl_pbp", "load_nfl_injuries"]
    exclude={"espn_nfl_pbp"}  # skip heavy/slow ones if desired
)

Notes
-----
- This module performs best-effort kwargs passing. If a function doesn't accept a kwarg,
  it will be ignored. You can override per-endpoint kwargs as needed.
- Some ESPN functions require specific identifiers (game_id, team_id, etc.). Provide
  those via per_endpoint_kwargs.
- To keep things predictable in production, consider pinning sportsdataverse version.
"""

from __future__ import annotations

import inspect
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union

try:
    import sportsdataverse as sdv
except Exception as e:
    raise ImportError(
        "sportsdataverse is required. Install with `pip install sportsdataverse` or "
        "`pip install sportsdataverse[all]`."
    ) from e


def _is_endpoint(name: str, obj: Any) -> bool:
    if not callable(obj):
        return False
    return name.startswith("load_") or name.startswith("espn_")

def _accepts_kw(fn: Callable, kw: str) -> bool:
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError):
        return False
    return any(p.kind in (p.KEYWORD_ONLY, p.VAR_KEYWORD) or (p.kind == p.POSITIONAL_OR_KEYWORD and p.name == kw)
                for p in sig.parameters.values())

def _filter_kwargs(fn: Callable, kwargs: Mapping[str, Any]) -> Dict[str, Any]:
    """Pass only kwargs accepted by the function signature, but allow **kwargs if present."""
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError):
        # If we can't inspect, just pass nothing
        return {}
    params = sig.parameters
    if any(p.kind == p.VAR_KEYWORD for p in params.values()):
        # Function accepts **kwargs; pass all
        return dict(kwargs)
    # Otherwise pass only matching names
    return {k: v for k, v in kwargs.items() if k in params}


@dataclass
class SportsDataVerseClient:
    prefer_pandas: bool = True
    max_retries: int = 1
    backoff_seconds: float = 0.8
    # cache of discovered endpoints per sport
    _registry: Dict[str, Dict[str, Callable]] = field(default_factory=dict, init=False)

    def available_sports(self) -> List[str]:
        """Return sdv submodules that look like sports namespaces (nfl, cfb, nba, etc.)."""
        sports = []
        for name in dir(sdv):
            if name.startswith("_"):
                continue
            try:
                sub = getattr(sdv, name)
            except Exception:
                continue
            if inspect.ismodule(sub):
                # heuristic: contains at least one endpoint function
                try:
                    if any(_is_endpoint(n, getattr(sub, n, None)) for n in dir(sub)):
                        sports.append(name)
                except Exception:
                    continue
        return sorted(sports)

    def _discover(self, sport: str) -> Dict[str, Callable]:
        sport = sport.lower()
        if sport in self._registry:
            return self._registry[sport]

        try:
            sub = getattr(sdv, sport)
        except AttributeError:
            raise ValueError(f"Unknown sport namespace '{sport}'. Installed namespaces: {self.available_sports()}")

        endpoints: Dict[str, Callable] = {}
        for name in dir(sub):
            try:
                obj = getattr(sub, name)
            except Exception:
                continue
            if _is_endpoint(name, obj):
                endpoints[name] = obj
        if not endpoints:
            raise ValueError(f"No endpoints discovered for sportsdataverse.{sport}")
        self._registry[sport] = endpoints
        return endpoints

    def list_endpoints(self, sport: str) -> List[str]:
        return sorted(self._discover(sport).keys())

    def _call_with_retries(self, fn: Callable, *, shared_kwargs: Mapping[str, Any], per_kwargs: Mapping[str, Any]) -> Any:
        # Merge kwargs with precedence: per_kwargs > shared_kwargs
        merged = dict(shared_kwargs)
        merged.update(per_kwargs or {})

        # Normalize pandas preference if function supports it
        if self.prefer_pandas and "return_as_pandas" not in merged and _accepts_kw(fn, "return_as_pandas"):
            merged["return_as_pandas"] = True

        # Filter kwargs to those accepted by function (unless it has **kwargs)
        call_kwargs = _filter_kwargs(fn, merged)

        last_exc: Optional[BaseException] = None
        for attempt in range(self.max_retries + 1):
            try:
                return fn(**call_kwargs)
            except Exception as e:
                last_exc = e
                if attempt >= self.max_retries:
                    break
                time.sleep(self.backoff_seconds * (2 ** attempt))
        # If we get here, we failed
        return last_exc  # return the exception object for downstream inspection

    def call(
        self,
        sport: str,
        endpoint: str,
        *,
        shared_kwargs: Optional[Mapping[str, Any]] = None,
        per_endpoint_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        endpoints = self._discover(sport)
        if endpoint not in endpoints:
            raise ValueError(f"Endpoint '{endpoint}' not found in sportsdataverse.{sport}. "
                              f"Available: {sorted(endpoints)}")
        return self._call_with_retries(endpoints[endpoint], shared_kwargs=shared_kwargs or {}, per_kwargs=per_endpoint_kwargs or {})

    def fetch_many(
        self,
        sport: str,
        *,
        endpoints: Sequence[str],
        shared_kwargs: Optional[Mapping[str, Any]] = None,
        per_endpoint_kwargs: Optional[Mapping[str, Mapping[str, Any]]] = None,
    ) -> Dict[str, Any]:
        discovered = self._discover(sport)
        results: Dict[str, Any] = {}
        shared_kwargs = shared_kwargs or {}
        per_endpoint_kwargs = per_endpoint_kwargs or {}

        for ep in endpoints:
            fn = discovered.get(ep)
            if fn is None:
                results[ep] = ValueError(f"Unknown endpoint: {ep}")
                continue
            per_kwargs = per_endpoint_kwargs.get(ep, {})
            results[ep] = self._call_with_retries(fn, shared_kwargs=shared_kwargs, per_kwargs=per_kwargs)
        return results

    def fetch_all(
        self,
        sport: str,
        *,
        shared_kwargs: Optional[Mapping[str, Any]] = None,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
        per_endpoint_kwargs: Optional[Mapping[str, Mapping[str, Any]]] = None,
    ) -> Dict[str, Any]:
        discovered = self._discover(sport)
        shared_kwargs = shared_kwargs or {}
        per_endpoint_kwargs = per_endpoint_kwargs or {}

        include_set: Set[str] | None = set(include) if include else None
        exclude_set: Set[str] = set(exclude) if exclude else set()

        results: Dict[str, Any] = {}
        for ep, fn in discovered.items():
            # Skip if not in include list (when include list is specified)
            if include_set is not None:
                if ep not in include_set:  # pylint: disable=unsupported-membership-test
                    continue
            # Skip if in exclude list
            if ep in exclude_set:
                continue
            per_kwargs = per_endpoint_kwargs.get(ep, {})
            results[ep] = self._call_with_retries(fn, shared_kwargs=shared_kwargs, per_kwargs=per_kwargs)
        return results


if __name__ == "__main__":
    # Quick smoke test (does not execute endpoints).
    client = SportsDataVerseClient(prefer_pandas=True, max_retries=1)
    print("Available sports:", client.available_sports())
    # Listing endpoints only (safe). Uncomment below to try on your machine:
    # print("NFL endpoints:", client.list_endpoints("nfl"))
    # out = client.fetch_many(
    #     "nfl",
    #     endpoints=["load_nfl_injuries"],
    #     shared_kwargs={"seasons": [2024], "return_as_pandas": True},
    # )
    # print(out.keys())
    pass