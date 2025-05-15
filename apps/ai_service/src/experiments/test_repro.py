# test_repro.py
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from dotenv import load_dotenv
import os
import sys


load_dotenv()
SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)
    
from app.service.dest_recommend.place_tools import SearchPlaceId, GetDestinationPhotos
from app.service.dest_recommend.hashtag_catalog import HASHTAGS
from langchain_core.tools import StructuredTool

for t in (SearchPlaceId, GetDestinationPhotos):
    if isinstance(t, StructuredTool):
        print("─", t.name)
        print(t.args_schema.schema_json(indent=2))  # pydantic 모델 스키마


@tool
def web_search_preview(query: str) -> str:
    """Responses API 내장 웹 검색 툴 호출"""
    client = OpenAI()
    resp = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=query,
    )
    return resp.output_text

if __name__ == "__main__":
    # 1) LLM 구성
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        use_responses_api=True,
    )
    # 2) 에이전트 생성 (웹 검색 툴만)
    agent = create_react_agent(
        model=llm,
        tools=[web_search_preview],
    )

    # 3) 간단히 한 번만 호출
    result = agent.invoke(
        {"messages": [("user", "파리 사진 보여줘")]}
    )
    # 4) 마지막 어시스턴트 메시지 출력
    assistant_msgs = result["messages"]
    print("===== ASSISTANT =====")
    print(assistant_msgs[-1].content)
