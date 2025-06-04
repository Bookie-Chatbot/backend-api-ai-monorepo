from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
<<<<<<< Updated upstream
from apps.ai_service.src.app.service.dest_recommend.place_tools import SearchPlaceId, GetDestinationPhotos
from apps.ai_service.src.app.service.dest_recommend.hashtag_catalog import HASHTAGS
=======
<<<<<<< HEAD
from app_service.service.dest_recommend.place_tools import SearchPlaceId, GetDestinationPhotos
from app_service.service.dest_recommend.hashtag_catalog import HASHTAGS
=======
from apps.ai_service.src.app.service.dest_recommend.place_tools import SearchPlaceId, GetDestinationPhotos
from apps.ai_service.src.app.service.dest_recommend.hashtag_catalog import HASHTAGS
>>>>>>> shin_
>>>>>>> Stashed changes
from langchain_core.tools import tool
from typing import Any
import random, datetime as dt
from openai import OpenAI
import os
from dotenv import load_dotenv




NUM_CARDS = 3          # 카드 개수 고정 값
PHOTO_PER_CITY = 1

load_dotenv()


def web_search_preview(query: str) -> str:
    """실시간 웹 서치 → Responses API 래핑."""
    # ❶ 진짜 OpenAI Responses API를 직접 호출하거나
    client = OpenAI()
    resp = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=query,
    )
    return resp.output_text

    # ❷ 우선은 자리만 채우고 싶다면:
    return "Handled by Responses API"

SYS_MSG = f"""
You are a step-by-step ReAct travel agent.
### 사용 가능한 Tools
1) web_search_preview(query, context) → text
2) search_place_id(query [,country]) → place_id
3) get_destination_photos(place_id, limit={PHOTO_PER_CITY}) → photos[]

### For *each* of exactly **{NUM_CARDS}** cities do
1. 사용자의 입력 문장을 web_search_preview 로 검색한다.
2. 검색 결과를 분석하여 **가장 적합한 도시 3곳**을 추린다. *(도시는 전부 서로 달라야 함)*
3. 각 도시마다
   - search_place_id → get_destination_photos 를 호출해 Place ID·사진을 확보한다.
   - 검색 결과에서 **왜 이 도시가 적합한지**(2문장)와 **최근 12개월 내 행사/트렌드 한 가지**(≤2문장·고유명+날짜 포함)를 뽑아 한국어로 요약한다.

### What to extract from web_search_preview
• Why the city is a good match for the user’s request (2 sentences)
• One recent festival / event / trend from the last 12 months (≤ 2 sentences, include proper name & date)


### Built-in Hashtags (30)
{', '.join('#'+t.tag for t in HASHTAGS)}

### 최종 출력(JSON only)
{{{{
  "cards": [  // **EXACTLY {NUM_CARDS} elements**
                {{{{ "city": "", "score": 0-1,
                 "photos": […],"description": "4 line summary incl. recent event",
                 "hashtags": […] }}}},
                  {{{{ "city": "", "score": 0-1,
                 "photos": […],"description": "4 line summary incl. recent event",
                 "hashtags": […] }}}}
                  ,
                   {{{{ "city": "", "score": 0-1,
                 "photos": […],"description": "4 line summary incl. recent event",
                 "hashtags": […] }}}}
                   ],
  "message": "한국어 요약"
}}}}
"""
# Prompt template with placeholder for messages
PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYS_MSG),
    MessagesPlaceholder(variable_name="messages"),
])

# 1) Instantiate base LLM with JSON mode and Responses API enabled
base_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    use_responses_api=True,
    model_kwargs={"response_format": {"type": "json_object"}},
)

tool_defs = [web_search_preview, SearchPlaceId, GetDestinationPhotos]
llm_with_tools = base_llm.bind_tools(tool_defs, strict=True)

react_graph = create_react_agent(
    model=llm_with_tools,
    tools=tool_defs,     # ← **같은 리스트 전달**
    prompt=PROMPT,
)

# 4) 외부에서 호출할 executor
dest_reco_executor = react_graph