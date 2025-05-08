# apps/ai_service/src/app/service/service_utils/amadeus_params.py
from __future__ import annotations
import re, datetime as dt, json
from typing import Dict, Any
from dateutil import parser as dtparse

def _iso_date(text: str) -> str:
    """여러 날짜 표현 → YYYY-MM-DD . 실패 시 ValueError."""
    text = text.strip()
    today = dt.date.today()

    special = {"내일": 1, "모레": 2}
    if text in special:
        return (today + dt.timedelta(days=special[text])).isoformat()

    if text in ("이번주", "이번 주"):
        # 이번 주 토요일
        return (today + dt.timedelta(days=(5 - today.weekday()) % 7)).isoformat()

    if re.fullmatch(r"\d{8}", text):
        text = f"{text[:4]}-{text[4:6]}-{text[6:]}"

    try:
        return dtparse.parse(text).date().isoformat()
    except Exception:
        raise ValueError(f"날짜 형식 오류: {text!r}")

def _int(val: Any, name: str) -> int:
    try:
        return int(float(val))
    except Exception:
        raise ValueError(f"{name}는 정수여야 합니다: {val!r}")

def to_amadeus_params(slots: Dict[str, Any]) -> Dict[str, Any]:
    """LLM 슬롯 → Flight Offers Search 파라미터"""
    map_ = {
        "origin": "originLocationCode",
        "originLocationCode": "originLocationCode",
        "destination": "destinationLocationCode",
        "destinationLocationCode": "destinationLocationCode",
        "departure_date": "departureDate",
        "departureDate": "departureDate",
        "return_date": "returnDate",
        "returnDate": "returnDate",
        "budget": "maxPrice",
        "maxPrice": "maxPrice",
        "class": "travelClass",
        "travelClass": "travelClass",
        "adults": "adults",
        "children": "children",
        "infants": "infants",
        "currency": "currencyCode",
        "currencyCode": "currencyCode",
        "nonStop": "nonStop",
    }

    # 1) 키 변환 + 빈 값 제거
    params: Dict[str, Any] = {
        map_[k]: v for k, v in slots.items()
        if k in map_ and str(v).strip() not in ("", "null", "None")
    }

    # 2) 필수 검사
    for req in ("originLocationCode", "destinationLocationCode", "departureDate"):
        if req not in params:
            raise ValueError(f"필수 인자 '{req}' 누락")

    # 3) 날짜 변환
    params["departureDate"] = _iso_date(params["departureDate"])
    if "returnDate" in params:
        params["returnDate"] = _iso_date(params["returnDate"])

    # 4) 숫자 변환
    if "maxPrice" in params:
        params["maxPrice"] = _int(params["maxPrice"], "maxPrice")
    for k in ("adults", "children", "infants"):
        if k in params:
            params[k] = _int(params[k], k)

    # 5) 불리언 → 'true'/'false'
    if "nonStop" in params:
        params["nonStop"] = "true" if str(params["nonStop"]).lower() in ("1", "true", "yes") else "false"

    # 6) 기본값
    params.setdefault("adults", 1)
    params.setdefault("currencyCode", "KRW")

    return params
