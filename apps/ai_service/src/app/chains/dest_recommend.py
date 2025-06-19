# ── DEST_RECOMMEND 서브체인 (v2-fixed-b) ─────────────────────
from __future__ import annotations
import json, re
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
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
    """
    BaseMessage → content
    dict/list   → 재귀 처리
    기타         → str(obj)
    """
    if isinstance(obj, BaseMessage):
        return obj.content
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]
    return str(obj)

# ── 1. STEP-1: React-Agent 호출 ──────────────────────────────
def _call_dest_reco(inputs: Dict[str, Any]) -> Dict[str, Any]:
    q = inputs["question"]
    raw = dest_reco_executor.invoke({"messages": [{"role": "user", "content": q}]})
    raw_txt = strip_fence(_to_plain(raw))

    # chat_history → 순수 문자열/딕트 배열
    hist: List[Any] = _to_plain(inputs.get("chat_history", []))

    return {
        "question": q,
        "format_instructions": inputs["format_instructions"],
        "raw_json": raw_txt,
        "chat_history": hist,
    }

# ── 2. STEP-2: LLM 재포맷 ────────────────────────────────────
reformat_prompt = PromptTemplate.from_template(
    "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
    "raw_json 안의 cards·message 를 그대로 유지하되, "
    "contents.message 를 두 줄 한국어 설명으로 갱신하고 항상 ‘부키!🦉’로 끝내. "
    "마크다운 코드블럭 없이 순수 JSON만 반환해.\n"
    ""
    "{format_instructions}\n"
    "질문: {question}\n"
    "이전 대화:\n{chat_history}\n"
    "raw_json: {raw_json}\n"
)
_llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

# ── 3. STEP-3: 파싱 & 직렬화 검증 ────────────────────────────
def _post_parse(text: str) -> DestRecommendContent:
    clean = strip_fence(text)
    parsed = dest_recommend_parser.parse(clean)
    # 직렬화 테스트
    json.dumps(parsed.model_dump(mode="python"), ensure_ascii=False)
    return parsed

# ── 4. 파이프라인 정의 ──────────────────────────────────────
dest_recommend_chain = (
    RunnableLambda(_call_dest_reco)
    | reformat_prompt | _llm
    | StrOutputParser()
    | RunnableLambda(_post_parse)
)

# ── CLI 테스트 ──────────────────────────────────────────────
if __name__ == "__main__":
    sample = dest_recommend_chain.invoke(
        {
            "question": "서유럽 낭만 여행지를 추천해줘",
            "format_instructions": dest_recommend_parser.get_format_instructions(),
            "chat_history": [],
        }
    )
    print(json.dumps(sample, indent=2, ensure_ascii=False))
