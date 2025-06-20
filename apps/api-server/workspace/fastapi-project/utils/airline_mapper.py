# utils/airline_mapper.py

AIRLINE_CODE_TO_NAME = {
    "NH": "All Nippon Airways",
    "KE": "Korean Air",
    "OZ": "Asiana Airlines",
    "JL": "Japan Airlines",
    "AA": "American Airlines",
    "UA": "United Airlines",
    "DL": "Delta Air Lines",
    "OD": "Air Asia",
    "TW": "Tway Airline",
    "VN": "Air Asia"
    # 필요한 만큼 추가
}

def get_airline_name(code: str) -> str:
    return AIRLINE_CODE_TO_NAME.get(code, f"Unknown ({code})")
