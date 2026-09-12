import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.stlouisfed.org/fred"
API_KEY = os.getenv("FRED_API_KEY")

class FredError(Exception):
    """Raised when FRED returns an error or the response is unusable."""


async def _get(endpoint: str, params: dict[str, Any]) -> dict:
    if not API_KEY:
        raise FredError("FRED_API_KEY not set. Check your .env file.")

    params = {**params, "api_key": API_KEY, "file_type": "json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/{endpoint}", params=params)

    if response.status_code != 200:
        raise FredError(f"FRED returned {response.status_code}: {response.text[:300]}")

    return response.json()


async def search_series(query: str, limit: int = 10) -> list[dict]:
    """Search FRED for series matching a keyword."""
    data = await _get("series/search", {
        "search_text": query,
        "limit": limit,
        "order_by": "popularity",
        "sort_order": "desc",
    })

    return [
        {
            "id": s["id"],
            "title": s["title"],
            "units": s["units_short"],
            "frequency": s["frequency_short"],
            "seasonal_adjustment": s["seasonal_adjustment_short"],
            "popularity": s["popularity"],
            "start": s["observation_start"],
            "end": s["observation_end"],
        }
        for s in data.get("seriess", [])
    ]


async def get_series_info(series_id: str) -> dict:
    """Fetch metadata for a single series."""
    data = await _get("series", {"series_id": series_id})
    results = data.get("seriess", [])
    if not results:
        raise FredError(f"No series found with ID '{series_id}'")

    s = results[0]
    return {
        "id": s["id"],
        "title": s["title"],
        "units": s["units"],
        "frequency": s["frequency"],
        "seasonal_adjustment": s["seasonal_adjustment_short"],
        "start": s["observation_start"],
        "end": s["observation_end"],
        "last_updated": s["last_updated"],
        "notes": s.get("notes", "")[:500],
    }


async def get_observations(
    series_id: str,
    start: str | None = None,
    end: str | None = None,
    limit: int = 500,
) -> list[dict]:
    """Fetch observations for a series. Dates as YYYY-MM-DD."""
    params: dict[str, Any] = {
        "series_id": series_id,
        "limit": limit,
        "sort_order": "desc",
    }
    if start:
        params["observation_start"] = start
    if end:
        params["observation_end"] = end

    data = await _get("series/observations", params)

    out = []
    for obs in data.get("observations", []):
        if obs["value"] == ".":      # FRED uses "." for missing values
            continue
        out.append({"date": obs["date"], "value": float(obs["value"])})

    return list(reversed(out))       # oldest first
