# ── data_sources.py ──────────────────────────────────────────
import os, httpx, asyncio, pprint
from dotenv import load_dotenv
from urllib.parse import quote_plus
from typing import Optional

load_dotenv()



FX_URL = (
    "https://api.exchangerate.host/live"
    "?access_key=5f553f30a3f0b47ac91dfac706c627aa"
    "&source=USD&currencies=KRW"
)

# ── 환율 ──────────────────────────────────────────
async def usd_to_krw() -> float:
    async with httpx.AsyncClient() as c:
        r = await c.get(FX_URL)
    data = r.json()

    # ── DEBUG ────────────────────────────────────
    print("\n[FX] raw json ➜")
    pprint.pprint(data)

    # API 오류라도 quotes["USDKRW"]가 있으면 사용, 없으면 기본값
    rate = data.get("quotes", {}).get("USDKRW", 1395.550124)
    if not data.get("success", True):
        print(f"[FX] warning: API returned success=False, using quotes['USDKRW']={rate:.6f}")

    print(f"[FX] USD→KRW rate = {rate:.2f}")
    return rate