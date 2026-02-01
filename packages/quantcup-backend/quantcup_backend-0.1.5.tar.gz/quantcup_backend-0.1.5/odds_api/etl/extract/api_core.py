"""
Shared HTTP utilities for The Odds API.

Centralizes retry logic, rate‑limit handling, quota logging,
and connection‑pooled session usage so the rest of the codebase can
make clean one‑line calls.

Usage example in api.py:
    from .api_core import _api_get
    def fetch_sports_data():
        return _api_get('/v4/sports')
"""

from __future__ import annotations

from typing import Any, Union, List
import json

import requests
from commonv2 import get_logger
from requests.adapters import HTTPAdapter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ...config.settings import get_settings
from ...core.types import OddsData, QuotaCost

logger = get_logger(__name__)

__all__ = [
    'BASE_URL',
    'get_session',
    'close_session',
    '_api_get'
]

# Base URL for all API endpoints
BASE_URL = "https://api.the-odds-api.com"

# Global session for connection pooling
_session = None

def get_session():
    """Get or create a persistent requests session for connection pooling"""
    global _session
    if _session is None:
        _session = requests.Session()
        # Configure session for better performance
        _session.headers.update({
            'User-Agent': 'odds-api-client/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        # Connection pooling settings
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=0  # We handle retries with tenacity
        )
        _session.mount('https://', adapter)
        _session.mount('http://', adapter)
        logger.debug("Created new HTTP session with connection pooling")
    return _session

def close_session():
    """Close the global session (useful for cleanup)"""
    global _session
    if _session:
        _session.close()
        _session = None
        logger.debug("Closed HTTP session")

# Exceptions worth retrying
_RETRYABLE_EXCEPTIONS = (
    requests.exceptions.RequestException,
    requests.exceptions.Timeout,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
    reraise=True,
)
def _api_get(path: str, use_paid_key: bool = False, **params) -> OddsData:  # noqa: D401, N802  (private helper is fine)
    """GET *path* from The Odds API and return JSON payload.

    All parameters common to every endpoint (``apiKey`` and ``dateFormat``) are
    applied automatically so the caller only needs to pass what is unique.

    Args:
        path: Endpoint path that follows ``BASE_URL`` – e.g. ``"/v4/sports"``.
        use_paid_key: If True, use paid_odds_api_key instead of odds_api_key.
        **params: Additional query‑string parameters for the request.

    Returns
    -------
    OddsData
        Parsed JSON (dict or list) from the response.
    """

    # Determine which key we're using
    settings = get_settings()
    key_id = 'paid' if use_paid_key else 'free'
    
    # Check quota availability BEFORE making paid request (fail fast)
    if use_paid_key:
        from ...core.quota_tracker import QuotaTracker
        tracker = QuotaTracker.get_instance()
        if not tracker.check_quota_available(key_id=key_id, buffer=100):
            logger.warning(f"[{key_id}] Proceeding with request despite low quota (server is authoritative)")

    session = get_session()

    # Choose API key based on use_paid_key flag
    api_key = settings.paid_odds_api_key if use_paid_key else settings.odds_api_key
    
    if not api_key:
        key_type = "PAID_ODDS_API_KEY" if use_paid_key else "ODDS_API_KEY"
        raise ValueError(f"{key_type} not found in environment variables")

    default_params = {
        "apiKey": api_key,
        "dateFormat": "iso",
    }

    url = f"{BASE_URL}{path}"
    final_params = {**default_params, **params}
    
    # DEBUG: Log full request details
    logger.debug(f"API Request: {url}")
    logger.debug(f"Parameters: {final_params}")
    
    response = session.get(url, params=final_params, timeout=30)

    # DEBUG: Log response details
    logger.debug(f"Response Status: {response.status_code}")
    logger.debug(f"Response URL: {response.url}")

    if response.status_code == 429:
        logger.warning("Rate limit hit (429). Check API quota and retry later.")
        # Raise so *tenacity* retry kicks in
        raise requests.exceptions.RequestException("Rate limit exceeded")
    
    # Log detailed error information for 422 errors
    if response.status_code == 422:
        logger.error(f"422 Unprocessable Entity Error")
        logger.error(f"  Requested URL: {response.url}")
        logger.error(f"  Request params: {final_params}")
        try:
            error_body = response.json()
            logger.error(f"  API Response: {json.dumps(error_body, indent=2)}")
        except (ValueError, json.JSONDecodeError):
            logger.error(f"  Response text: {response.text}")

    response.raise_for_status()

    # Surface quota usage headers when present (per API docs)
    # All three headers provide complete visibility into API credit usage
    remaining = response.headers.get("x-requests-remaining")
    used = response.headers.get("x-requests-used")
    last_cost = response.headers.get("x-requests-last")
    
    # Consolidated logging: single line with all quota metrics
    if remaining or used or last_cost:
        logger.info(
            "API quota - Used: %s, Remaining: %s, Cost: %s",
            used or "N/A",
            remaining or "N/A",
            last_cost or "N/A"
        )
    
    # Update QuotaTracker with authoritative server state
    if used is not None and remaining is not None:
        try:
            from ...core.quota_tracker import QuotaTracker
            tracker = QuotaTracker.get_instance()
            tracker.update_usage(
                used=int(used),
                remaining=int(remaining),
                key_id=key_id
            )
        except Exception as e:
            logger.debug(f"[{key_id}] Could not update quota tracker: {e}")

    return response.json()
