from mcp.server.fastmcp import FastMCP
import requests
from dotenv import load_dotenv
import os
from typing import Any
import json
import httpx

mcp = FastMCP(
    "test",  # Name of the MCP server
    instructions="You are a weather assistant that always returns 5-day / 3-hour forecast data.",
    host="0.0.0.0",  # Host address (0.0.0.0 allows connections from any IP)
    port=8010,  # Port number for the server
)

"""
# fastapi endpoint를 mcp 호환 도구로 자동 변환.
# endpoint schema, doc, 기능 그대로 유지.
from fastapi_mcp import FastApiMCP

mcp = FastApiMCP(
    fastapi=app, # app = fastapi app
    name="test",  # Name of the MCP server
    description="You are a test server.",  # Instructions for the LLM on how to use this tool
)

mcp.mount()
# 이걸로 mcp server를 https://app.base.url/mcp 에서 이용 가능.
"""

@mcp.tool()
async def get_weather(city: str) -> dict:
    """
    5일 / 3시간 예보( /forecast )를 조회해 원본 JSON을 반환
    """
    load_dotenv()
    api_key = os.getenv("WEATHERMAPAPI_KEY")
    if not api_key:
        return {"error": "WEATHERMAPAPI_KEY 가 설정되어 있지 않습니다."}

    # 도시명 통일
    city = city.upper()
    print(f"[DEBUG] get_weather → city='{city}'")

    # URL 직접 포맷
    url = (
        "http://api.openweathermap.org/data/2.5/"
        f"forecast?appid={api_key}&q={city}&units=metric&lang=kr"
    )
    print(f"[DEBUG] request URL: {url}")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10)
            print(f"[DEBUG] status_code={resp.status_code}")
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"[DEBUG] HTTPStatusError: {e.response.text}")
            try:
                return {"error": e.response.json()}
            except Exception:
                return {"error": f"HTTP error {e.response.status_code}"}
        except Exception as e:
            print(f"[DEBUG] unexpected error: {e}")
            return {"error": f"요청 중 예기치 못한 오류: {e}"}

    data = resp.json()
    print(f"[DEBUG] raw 'cod' type = {type(data.get('cod'))}")

    # 'cod'를 문자열로 캐스팅
    if isinstance(data.get("cod"), int):
        data["cod"] = str(data["cod"])

    print("[DEBUG] 반환 준비 완료")
    return data



@mcp.tool()
async def query_llm(prompt: str) -> str:
    # Return a mock LLM response
    # In a real implementation, this would call the LLM model's API
    return f"LLM response to: {prompt}"

@mcp.resource("greeting://{name}") # GET endpoint 와 similar
def get_greeting(name: str) -> str:

    return f"Hello, {name}!"


# fastapi와 같이 연동 되는지 실험. mount를 잘 해야될 것 같은데 우선 실패했음
# from fastapi import FastAPI
# app = FastAPI()
# @app.get("/")
# async def root():
#     return {"message": "Hello Test Server!"}

# @app.get("/greeting")
# async def get_greeting(name: str):
#     return {"message": f"Hello, {name}!"}

# @app.post("/query_llm")
# async def query_llm_http(prompt: str):
#     return {"result": f"LLM 응답 (REST): {prompt}"}

# @app.get("/get_weather")
# async def get_weather_http(city: str) -> str:
#     url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
#     response = requests.get(url)
#     if response.status_code != 200:
#         return f"날씨 정보를 가져오지 못했습니다. 오류 코드: {response.status_code}"
#     data = response.json()
#     description = data['weather'][0]['description']
#     temp = data['main']['temp']
#     humidity = data['main']['humidity']
#     wind_speed = data['wind']['speed']
#     return (f"현재 {city}의 날씨는 '{description}', 온도는 {temp}°C, "
#             f"습도는 {humidity}%, 풍속은 {wind_speed}m/s입니다.")


if __name__ == "__main__":
    # Print a message indicating the server is starting
    print("mcp remote server is running...")

    # Start the MCP server with SSE transport
    # Server-Sent Events (SSE) transport allows the server to communicate with clients
    # over HTTP, making it suitable for remote/distributed deployments
    mcp.run(transport="sse")