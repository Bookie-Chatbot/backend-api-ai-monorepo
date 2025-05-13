from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.service.dest_recommend.place_tools import SearchPlaceId, GetDestinationPhotos
from app.service.dest_recommend.hashtag_catalog import HASHTAGS

SYS_MSG = f"""
You are a step-by-step ReAct travel agent.
### Tools
1) search_place_id(query [,country]) → place_id
2) get_destination_photos(place_id, limit) → photos[]
3) web_search_preview → 최신 트렌드 조사

### 반드시 지킬 순서
• 도시마다 **search_place_id → get_destination_photos** 순으로 호출하라.

### Built-in Hashtags (30)
{', '.join('#'+t.tag for t in HASHTAGS)}

### 최종 출력(JSON only)
{{{{
  "cards": [ {{{{ "city": "", "score": 0-1,
                 "photos": […], "hashtags": […] }}}} ],
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
    model_kwargs={
        "response_format": {"type": "json_object"}
    }
)

# 2) Bind built-in web search tool in strict mode
llm_with_web = base_llm.bind_tools([
    {"type": "web_search_preview"}
], strict=True)

# 3) Bind structured Pydantic tools in strict mode
llm_strict = llm_with_web.bind_tools([
    SearchPlaceId,
    GetDestinationPhotos,
], strict=True)

# 4) Create the ReAct agent graph with matching tool list
react_graph = create_react_agent(
    model=llm_strict,
    tools=[SearchPlaceId, GetDestinationPhotos],
    prompt=PROMPT,
)

dest_reco_executor = react_graph  # .invoke / .ainvoke for usage
