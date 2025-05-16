from mcp.server.fastmcp import FastMCP
import requests
from dotenv import load_dotenv
import os
from typing import Any
import json
import httpx

mcp = FastMCP(
    "test",  # Name of the MCP server
    instructions="You are a weather assistant that can answer questions about the weather in a given location.",  # LLM이 이 MCP에서 제공하는 tool을 어떻게 사용할지 이해하도록 돕는 설명(prompt)
    host="0.0.0.0",  # Host address (0.0.0.0 allows connections from any IP)
    port=8000,  # Port number for the server
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
async def get_weather(city: str) -> json:
    """
    Args: 날씨 조회할 도시 이름(eng)
    
    Body: weathermapapi_key로 openweathermap.org에 접속해서 
    """
    load_dotenv()
    api_key = os.getenv("WEATHERMAPAPI_KEY")

    http_params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"http://api.openweathermap.org/data/2.5/weather",
                params=http_params
            )
            response.raise_for_status()
            data = response.json()
    # return {
    #     "temperature": data["main"]["temp"],
    #     "conditions": data["weather"][0]["description"],
    #     "humidity": data["main"]["humidity"],
    #     "wind_speed": data["wind"]["speed"],
    # }
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error occurred: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}    
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