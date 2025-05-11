# apps/ai_service/src/app/service/service_utils/amadeus_params.py
from __future__ import annotations
import re, datetime as dt
from typing import Dict, Any
from dateutil import parser as dtparse

# ────────────────── 공용 유틸 ──────────────────
def _iso_date(text: str) -> str:
    """여러 날짜 표현 → YYYY-MM-DD (ISO-8601). 실패 시 ValueError."""
    text = text.strip()
    today = dt.date.today()

    special = {"내일": 1, "모레": 2}
    if text in special:
        return (today + dt.timedelta(days=special[text])).isoformat()

    if text in ("이번주", "이번 주"):
        # 이번 주 토요일
        return (today + dt.timedelta(days=(5 - today.weekday()) % 7)).isoformat()

    if re.fullmatch(r"\d{8}", text):                 # 20250817 → 2025-08-17
        text = f"{text[:4]}-{text[4:6]}-{text[6:]}"

    try:
        return dtparse.parse(text).date().isoformat()
    except Exception:
        raise ValueError(f"날짜 형식 오류: {text!r}")


def _int(val: Any, name: str) -> int:
    """정수 변환 (문자열·float 허용). 실패 시 ValueError."""
    try:
        return int(float(val))
    except Exception:
        raise ValueError(f"{name}는 정수여야 합니다: {val!r}")


# ────────────────── 새로 추가된 보정 로직 ──────────────────
def _fix_iata(code: str) -> str | None:
    """
    IATA 공항코드 보정·검증
    - 3자리 영문 대문자만 허용
    - 잘못된 형식이면 None 반환
    """
    code = code.strip().upper()

    # 흔한 오타 처리 예: 'ICN-'  / 'ICN/' 등
    if len(code) == 4 and not code.isalpha():
        code = code[:3]

    # 두 글자(국가코드) 들어오면 거부
    if len(code) != 3 or not code.isalpha():
        return None

    return code


# ────────────────── 메인 변환기 ──────────────────
def to_amadeus_params(slots: Dict[str, Any]) -> Dict[str, Any]:
    """LLM 슬롯 → Amadeus Flight-Offers Search 파라미터 dict"""

    # 1) 슬롯 이름 매핑
    key_map = {
        "origin":                "originLocationCode",
        "originLocationCode":    "originLocationCode",
        "destination":           "destinationLocationCode",
        "destinationLocationCode": "destinationLocationCode",
        "departure_date":        "departureDate",
        "departureDate":         "departureDate",
        "return_date":           "returnDate",
        "returnDate":            "returnDate",
        "budget":                "maxPrice",
        "maxPrice":              "maxPrice",
        "class":                 "travelClass",
        "travelClass":           "travelClass",
        "adults":                "adults",
        "children":              "children",
        "infants":               "infants",
        "currency":              "currencyCode",
        "currencyCode":          "currencyCode",
        "nonStop":               "nonStop",
        "non_stop":              "nonStop",
    }

    # 2) 매핑 & 빈 값 제거
    params: Dict[str, Any] = {
        key_map[k]: v for k, v in slots.items()
        if k in key_map and str(v).strip() not in ("", "null", "None")
    }

    # 3) 필수 키 존재 여부
    for req in ("originLocationCode", "destinationLocationCode", "departureDate"):
        if req not in params:
            raise ValueError(f"필수 인자 '{req}' 누락")

    # 4) IATA 코드 보정·검증
    for k in ("originLocationCode", "destinationLocationCode"):
        fixed = _fix_iata(params[k])
        if not fixed:
            raise ValueError(f"IATA 3-letter code required: {params[k]!r}")
        params[k] = fixed

    # 5) 날짜 파싱
    params["departureDate"] = _iso_date(params["departureDate"])
    if "returnDate" in params:
        params["returnDate"] = _iso_date(params["returnDate"])

    # 6) 숫자형 필드
    if "maxPrice" in params:
        params["maxPrice"] = _int(params["maxPrice"], "maxPrice")
    for k in ("adults", "children", "infants"):
        if k in params:
            params[k] = _int(params[k], k)

    # 7) nonStop 다양한 표현 허용
    non_stop_alias = {"nonstop", "논스톱", "직항", "direct"}
    # 슬롯 키 또는 값(문자열)으로 들어온 경우 모두 처리
    if (
        any(alias in slots for alias in ("nonStop", "non_stop"))
        or any(str(v).strip().lower() in non_stop_alias for v in slots.values())
    ):
        params["nonStop"] = "true"
    elif "nonStop" in params:  # 불리언/문자열 표준화
        params["nonStop"] = (
            "true" if str(params["nonStop"]).lower() in ("1", "true", "yes") else "false"
        )

    # 8) 기본값
    params.setdefault("adults", 1)
    params.setdefault("currencyCode", "KRW")

    return params
