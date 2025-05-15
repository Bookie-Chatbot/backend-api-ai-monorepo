# ── data_sources.py ─────────────────────────────
import csv, pathlib, asyncio, pprint
from typing import Optional

# ── ① 서유럽 데이터셋 로드 ────────────────────────
BASE_DIR = pathlib.Path(__file__).parent / "data"
DATA_FILE = BASE_DIR / "weu_cost_poi.csv"

_CITY_TABLE: dict[str, dict] = {}
with DATA_FILE.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
        key = row["city_en"].strip().lower()
        _CITY_TABLE[key] = {
            "country_en":  row["country_en"],
            "daily_usd":   float(row["daily_usd"]),
            "shopping_poi": int(row["shopping_poi"]),
        }

# ── ② 환율 함수──────────
from .fx import usd_to_krw

# ── ③ 로컬 룩업 csv 데이터셋으로함 ───────────────────────────────
async def fetch_daily_cost(rate: float, city: str, country: Optional[str] = None) -> float:
    rec = _CITY_TABLE.get(city.lower())
    if not rec:
        print(f"[COST] {city}: not in table → inf")
        return float("inf")
    daily = rec["daily_usd"] * rate
    print(f"[COST] {city}: {rec['daily_usd']}$ × {rate:.2f} = {daily:.0f} KRW")
    return daily

async def fetch_shopping_poi_count(city: str) -> int:
    rec = _CITY_TABLE.get(city.lower())
    count = rec["shopping_poi"] if rec else 0
    print(f"[POI] {city}: count = {count}")
    return count
