# apps/ai_service/src/app/service/dest_recommend/hashtag_catalog.py
"""
고정 30슬롯 해시태그: ①지역/국가 15 + ②카테고리·무드 15
"""
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class TagInfo:
    tag: str
    category: str       # 'region' | 'category' | 'mood'

HASHTAGS: List[TagInfo] = [
    # ── Region / Country
    TagInfo("europe", "region"), TagInfo("usa", "region"),
    TagInfo("italy", "region"), TagInfo("germany", "region"),
    TagInfo("france", "region"), TagInfo("spain", "region"),
    TagInfo("australia", "region"), TagInfo("nyc", "region"),
    TagInfo("bali", "region"), TagInfo("phuket", "region"),
    TagInfo("tulum", "region"), TagInfo("ubud", "region"),
    TagInfo("mykonos", "region"), TagInfo("monaco", "region"),
    TagInfo("barcelona", "region"),
    # ── Category / Mood
    TagInfo("beachlife",       "category"),
    TagInfo("familytravel",    "category"),
    TagInfo("foodie",          "category"),
    TagInfo("relaxation",      "mood"),
    TagInfo("wanderlust",      "mood"),
    TagInfo("luxurytravel",    "category"),
    TagInfo("solotravel",      "category"),
    TagInfo("wellnessretreat", "mood"),
    TagInfo("citybreak",       "category"),
    TagInfo("ecotravel",       "category"),
    TagInfo("budgettravel",    "category"),
    TagInfo("culturetrip",     "mood"),
    TagInfo("vacationmode",    "mood"),
    TagInfo("adventureseeker", "mood"),
    TagInfo("travelphotography", "category"),
]
