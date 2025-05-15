"""
Google Places 기반 여행지 툴 – Responses API strict-tool 호환 + 디버그 로그
"""

import os, requests, json
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool 

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")
DBG        = os.getenv("DEBUG_DEST_TOOLS", "0") == "1"


# ───────────────────────────────────────── helper ─────────────────────────────────────────
def _dbg(msg: str) -> None:
    if DBG:
        print(f"[place_tools] {msg}")




# ───────────────────────────────────────── 1) search_place_id ────────────────────────────
class SearchPlaceIdArgs(BaseModel):
    query:   str = Field(..., description="City name or landmark, e.g. 'Barcelona'")
    country: str = Field(..., description="ISO-3166-1 alpha-2 code, e.g. 'ES'")

def _search_place_id(query: str, country: str) -> str:
    _dbg(f"▶ search_place_id('{query}', '{country}')")
    params = {
        "input":       query,
        "inputtype":   "textquery",
        "fields":      "place_id",
        "key":         GOOGLE_KEY,
        "locationbias": f"ipbias&region={country.lower()}",
    }
    js = requests.get(
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
        params=params, timeout=10,
    ).json()
    _dbg(f"  ↳ candidates = {len(js.get('candidates', []))}")
    if not js.get("candidates"):
        raise ValueError(f"no place_id for '{query}' in '{country}'")
    return js["candidates"][0]["place_id"]

SearchPlaceId: StructuredTool = StructuredTool.from_function(
    name="search_place_id",
    description="Return the first Google Place ID that matches the text query",
    args_schema=SearchPlaceIdArgs,
    func=_search_place_id,
)


# ───────────────────────────────────────── 2) get_destination_photos ─────────────────────
class GetDestinationPhotosArgs(BaseModel):
    place_id: str = Field(..., description="Google Places place_id")
    limit:    int = Field(..., description="1 ≤ limit ≤ 5 (usually 1)")

def _get_destination_photos(place_id: str, limit: int) -> List[str]:
    _dbg(f"▶ get_destination_photos('{place_id}', {limit})")
    if not 1 <= limit <= 5:
        raise ValueError("limit must be between 1 and 5")

    js = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={"place_id": place_id, "fields": "photo", "key": GOOGLE_KEY},
        timeout=10,
    ).json()
    photos = (js.get("result") or {}).get("photos") or []
    _dbg(f"  ↳ photos returned: {len(photos)}")

    urls: List[str] = []
    for photo in photos[:limit]:
        ref = photo.get("photo_reference")
        if ref:
            urls.append(
                "https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=800&photo_reference={ref}&key={GOOGLE_KEY}"
            )
    _dbg(f"  ↳ final url count: {len(urls)}")
    return urls

GetDestinationPhotos: StructuredTool = StructuredTool.from_function(
    name="get_destination_photos",
    description="Return up to <limit> photo URLs for the given place_id",
    args_schema=GetDestinationPhotosArgs,
    func=_get_destination_photos,
)
