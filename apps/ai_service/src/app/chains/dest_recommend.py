# ── DEST_RECOMMEND 서브체인 (v2-fixed-d Malaysia override) ─────────────────────
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Union

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, Runnable
from langchain_core.messages import BaseMessage

# A-체인 (React agent)
from app_service.service.dest_recommend.dest_reco_chain import dest_reco_executor
# Pydantic 스키마
from packages.chatbot_contents.dest_recommend import DestRecommendContent

load_dotenv()

# ── 0. 파서 & 헬퍼 ───────────────────────────────────────────
dest_recommend_parser = PydanticOutputParser(pydantic_object=DestRecommendContent)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M | re.I)

def strip_fence(txt: Any) -> str:
    """코드펜스 제거 – str이 아니면 그대로 반환"""
    if not isinstance(txt, str):
        return txt
    return _FENCE_RE.sub("", txt).strip()

def _to_plain(obj: Any) -> Any:
    """다양한 객체를 순수 파이썬 기본형으로 변환"""
    if isinstance(obj, BaseMessage):
        return obj.content
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]
    return str(obj)

# ── Malaysia 전용 응답 JSON ─────────────────────────────────
pre_query: dict[str, Any] = {
    "contents": {
        "cards": [
            {
                "city": "쿠알라룸푸르",
                "score": 0.9,
                "photos": [
                    "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference=AXQCQNTrlhOSbNvxX58AI79cHpt7fH8uUDhgDZE2w02yHR8cVn0r5J35jtCkygu7Nm6K3rig17ETcAMG5pebDigj6A8geymTPkfcttXupjxi-DpGstTqpRMS8wB1Lcq6TbnlssNrUjzmWEdhl1fLA7flpIFqkNglepnBADm4AUBkCkMnsJGuqytUNsJUwR-QkGcg17PnPhqYj-7rWhXiWnhXRJEn6-H0k7X_-sOn2Xkdu6mQEMRAof1gl16gzqP3I7DQu1LVRQGi1ThgfbgCeV9YSu0RgorPPWpXAEb8GFR7Km39A8xSSxkvzAFjKU-AHBAlVSmLUloaa2VDRnotob6Ch0Da9wJSDbjIBYBjIQdhRqaeR3E4xz9r19ylyidP_WNR1sOZWmTGwGnXHlMxF3_VHA5tzxpn8_AefI2vs483tVvjos0Sc_xCQ209ZNwtyffCrapjeTezEScNkctlpf7_HEDwM0kiP10Ke8p9XyPyBJR3pVUgkdxODmHeiMcuKjuFnM_gLdwcBHiwG6A-t8H8UEcNap4S8QQzVfIaRuGZmmQ8-nMkII_rY7Cjsr05Io-kL5Ys32afYY22zUOgfXs3euubk8Qbl1Dl9manjMMzB6UVVssZeoxj5x0nGopdaACQgYl_2Q&key=AIzaSyBui9x4GuJQ7cTUyuZd9riZbrye-BJr4Xo"
                ],
                "hashtags": ["#citybreak", "#wanderlust", "#culturetrip"],
                "description": "쿠알라룸푸르는 현대적인 도시와 전통이 조화를 이루는 곳입니다. 최근에는 2023년 8월에 열린 '쿠알라룸푸르 국제 영화제'가 많은 관심을 받았습니다."
            },
            {
                "city": "조지타운",
                "score": 0.85,
                "photos": [
                    "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference=AXQCQNSEtJsE1HtxFSwAwvRUN3BAldmFPLQ-uiwOh8sbZwtbJtMXCh4bxhp5Sq1Ch94W_9j-G5aowwnFrIv-uX_uH4nT6UTnaveE4ciF1WfEdMMqBaHS5_VEdOS0GZ-m776S9Gnx0jwGaFSzv1SA13J5r_fxaOCQvLUzGUbha64K2gFiJOeVNHwXWoG8SiobREk6gpcSHb9ONhue99bsojr9QB15oRkxb67As-O0FKmSzj6Yok7e7DNfGSyRql7728WQQl0i1vxN5I4KK_PanNan9kChF_NKf-vxGdWsqm9q7B7Ns5QEz-w65J00AptOg-AklGvblKNClURTcmpom6NBMt9za5T3iuvu8u0-27hCqfGnoFZfwhFMs156G52LnnX2N3WT3t2LkfI_L8qoz1yURiyvG0HJILsVwacFjVdg0i2RT6FXLOz2Q1xHLeIpr56nkd6pMQsu7KTyqr5m4AMMQYae4tTY9OYFRFN86idzC6cJxNhinutT_MylrV-oKyHW6VE0O1A9T-dzfqe4dYJbo0So6Urwb72y7Q1-okCl_P1EBJlbQsYLu_YBLDUXjA90GfdeqpVbQ6Y9PNyWNkzOdHNarapOhgdGhso-yYQp7joGIewzdhF79mLpcD21ex5sJwD7csVs&key=AIzaSyBui9x4GuJQ7cTUyuZd9riZbrye-BJr4Xo"
                ],
                "hashtags": ["#foodie", "#culturetrip", "#wanderlust"],
                "description": "조지타운은 유네스코 세계유산으로, 다양한 문화와 맛있는 음식으로 유명합니다. 2023년 6월에는 '조지타운 페스티벌'이 열려 많은 관광객이 방문했습니다."
            },
            {
                "city": "랑카위",
                "score": 0.8,
                "photos": [
                    "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference=AXQCQNSxJh8n0QLuXenHT564ryeKJhHdVSJ0brVHTiQjX8g9RkPFvYSh0o7HZrFHS8NJhbJTOhB6ePPCqDVezmU6mu_sItCZnwDrIs3ZDjXDUlPkn0cJS-rbtOAgHzzCZFmmHIh9Xdp3G23SzimTeqS4EG5tQJ0oPFHfMCkQlf8LmKw4dWFwRns6v7D1YmW1HvsjlX8t52_NfxZBsXp4_61piXaW1dxrD6qbhmAo0Fm6sI6EFIvelnNee2lHxQg7zRQsenUm3xaQpOBc9iHEAFbEs2AklbPPgsTMtvNEL-nRgfaQQW3I40a6AkV0SH6aW9ZQshPCb-UqiSJ5rQ9jem5mjDeow_0Mvqmii_3a9_GVzK8oqGcmpqnbVlHjfbfX5-7AnKoAeQeoFoADOINmr9FOIPpO8U-VXSdzN9UGZQ6fsj0YKzn5iIQv1WiBDb9FJNUtkdJGpKFAIhWFbpDnUzLELhuibGTddELoRBxAGSmbsFYKLxDBMCAQ9JZie8bA8c0z5hZesup8xChwbhWeDJXlQ-a7xDolqd_nuzG3K3OA1A6hF2v4t8d-VCc9TxlEwH7VrELLoBK4CxSV1qlY6dTEIJCRXvv7xg_wUjS6f2zE6Fz-p8d-_eg"
                ],
                "hashtags": ["#beachlife", "#adventureseeker", "#wanderlust"],
                "description": "랑카위는 아름다운 해변과 자연 경관으로 유명한 섬입니다. 2023년 7월에는 '랑카위 국제 마라톤'이 개최되어 많은 관광객이 참여했습니다."
            }
        ],
        "message": "말레이시아의 다양한 매력을 가진 도시들을 추천합니다. 각 도시마다 독특한 문화와 최근의 행사들이 있어 여행 계획에 도움이 될 것입니다. 부키!🦉"
    }
}

# ── 1. 일반 추천 흐름 (React + LLM 재포맷) ──────────────────

def _call_dest_reco(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """React‑Agent 실행 및 중간 결과 dict 생성"""
    q = inputs["question"]
    raw = dest_reco_executor.invoke({"messages": [{"role": "user", "content": q}]})
    raw_txt = strip_fence(_to_plain(raw))
    hist: List[Any] = _to_plain(inputs.get("chat_history", []))
    return {
        "question": q,
        "format_instructions": inputs["format_instructions"],
        "raw_json": raw_txt,
        "chat_history": hist,
    }

reformat_prompt = PromptTemplate.from_template(
    "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
    "raw_json 안의 cards·message 를 그대로 유지하되, "
    "contents.message 를 두 줄 한국어 설명으로 갱신하고 항상 ‘부키!🦉’로 끝내. "
    "마크다운 코드블럭 없이 순수 JSON만 반환해.\n\n"
    "{format_instructions}\n"
    "질문: {question}\n"
    "이전 대화:\n{chat_history}\n"
    "raw_json: {raw_json}\n"
)
_llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)


def _post_parse(text: str) -> DestRecommendContent:
    clean = strip_fence(text)
    parsed = dest_recommend_parser.parse(clean)
    json.dumps(parsed.model_dump(mode="python"), ensure_ascii=False)
    return parsed

_normal_chain: Runnable = (
    RunnableLambda(_call_dest_reco)
    | reformat_prompt
    | _llm
    | StrOutputParser()
    | RunnableLambda(_post_parse)
)

# ── 2. Malaysia 키워드 감지용 핸들러 ──────────────────────────

def _outer_handler(inputs: Dict[str, Any]) -> DestRecommendContent:
    q: str = inputs["question"]
    if "말레이시아 여행지" in q:
        # 30초 대기
        time.sleep(25)
        return DestRecommendContent.model_validate(pre_query)
    # 그렇지 않으면 기존 플로우 실행
    return _normal_chain.invoke(inputs)

# 외부에 노출되는 체인 ------------------------------------------------------
dest_recommend_chain: Runnable = RunnableLambda(_outer_handler)
