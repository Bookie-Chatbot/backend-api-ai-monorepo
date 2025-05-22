# chains/weather_summary.py
from langchain_core.runnables import RunnableLambda
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_openai import ChatOpenAI
from chatbot_contents.weather_summary import WeatherSummaryContent
import asyncio

# 1) 파서 생성
weather_parser = PydanticOutputParser(pydantic_object=WeatherSummaryContent)

# 2) MCP weather 서버 호출 헬퍼 가져오기
#    (이는 ask_mcp 함수가 정의된 모듈을 import)
from test import ask_mcp

# 3) 체인: ask_mcp → (LLM 없이) → parser
weather_summary_chain = RunnableLambda(
    # RunnableLambda는 동기/비동기 둘 다 지원합니다.
    lambda inputs: asyncio.get_event_loop().run_until_complete(
        ask_mcp(inputs["question"])
    )
) | weather_parser



"""
ask_mcp(inputs["question"]):

MCP weather 서버에 question을 보내면,

내부적으로 get_weather 툴을 호출해 JSON 기후 정보를 받아오고,

그 데이터를 LLM(React agent)을 통해 요약·정제해 반환합니다.

"""