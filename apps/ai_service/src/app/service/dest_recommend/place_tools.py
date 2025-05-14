"""
Google Places 기반 여행지 툴 – strict tool-calling 호환 + 디버그 로그
"""
import os
import requests
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")
DBG = os.getenv("DEBUG_DEST_TOOLS", "0") == "1"

def _dbg(msg: str) -> None:
    if DBG:
        print(f"[place_tools] {msg}")

# ────────────────────────────────────────────────────────────
# 1) 도시 이름 → place_id
#    * strict=True 에 맞추기 위해 JSON-Schema 제약( default / min / max 등 ) 추가 불가능함.
# ────────────────────────────────────────────────────────────
class SearchPlaceIdInput(BaseModel):
    query: str = Field(..., description="City name or landmark (e.g. 'Barcelona')")
    country: str = Field(..., description="ISO 3166-1 alpha-2 country code (e.g. 'ES')")

def _search_place_id(query: str, country: str) -> str:
    _dbg(f"▶ search_place_id(query='{query}', country='{country}')")
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": GOOGLE_KEY,
        "locationbias": f"ipbias&region={country.lower()}",
    }
    js = requests.get(
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
        params=params,
        timeout=10,
    ).json()
    _dbg(f"  ↳ raw candidates={len(js.get('candidates', []))}")
    if not js.get("candidates"):
        raise ValueError(f"No place_id for '{query}' in country '{country}'")
    return js["candidates"][0]["place_id"]

SearchPlaceId: StructuredTool = StructuredTool.from_function(
    name="search_place_id",
    description="Google Find-Place 를 호출해 첫 번째 후보의 place_id 반환",
    args_schema=SearchPlaceIdInput,
    func=_search_place_id,
)

# ────────────────────────────────────────────────────────────
# 2) place_id → 대표 사진 URL 리스트
# ────────────────────────────────────────────────────────────
class GetDestinationPhotosInput(BaseModel):
    place_id: str = Field(..., description="Google Places place_id")
    limit: int = Field(..., description="Number of photos to fetch (각 place당 1장)")

def _get_destination_photos(place_id: str, limit: int) -> list[str]:
    _dbg(f"▶ get_destination_photos(place_id='{place_id}', limit={limit})")
    if not 1 <= limit <= 10:
        raise ValueError("limit must be 1")

    js = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={"place_id": place_id, "fields": "photo", "key": GOOGLE_KEY},
        timeout=10,
    ).json()
    photos = (js.get("result") or {}).get("photos") or []
    _dbg(f"  ↳ photos returned: {len(photos)}")
    urls: list[str] = []
    for photo in photos[:limit]:
        ref = photo.get("photo_reference")
        if ref:
            urls.append(
                f"https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=800&photo_reference={ref}&key={GOOGLE_KEY}"
            )
    _dbg(f"  ↳ final url count: {len(urls)}")
    return urls

GetDestinationPhotos: StructuredTool = StructuredTool.from_function(
    name="get_destination_photos",
    description="place_id로부터 장소 대표 사진 URL 리스트(1장) 반환",
    args_schema=GetDestinationPhotosInput,
    func=_get_destination_photos,
)
