#!/usr/bin/env python3
import asyncio
import subprocess
import time
import signal
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# LangChain MCP client libraries
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# ── 기존 날씨 서버 래퍼 ───────────────────────────────────
def start_weather_server():
    return subprocess.Popen([
        sys.executable, "-m", "mcp.mcp_server"
    ], preexec_fn=os.setsid,
       stdout=subprocess.DEVNULL,
       stderr=subprocess.DEVNULL)

def stop_weather_server(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except Exception:
        pass
    proc.wait()

# ── Amadeus 서버 래퍼 (§4 참고) ────────────────────────────
ROOT = Path(__file__).resolve().parent
def start_amadeus_server():
    return subprocess.Popen(
        ["npm", "run", "start", "--prefix", str(ROOT / "amadeus_server" / "apps" / "amadeus_mcp_server")],
        preexec_fn=os.setsid,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def stop_amadeus_server(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except ProcessLookupError:
        pass
    proc.wait()

# ── MCP 질의 함수 ─────────────────────────────────────────
async def query_mcp(question: str) -> str:
    load_dotenv()

    llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    server_connections = {
        "weather": {
            "transport": "sse",
            "url": "http://localhost:8010/sse",
        },
        "amadeus": {
            "transport": "sse",
            "url": "http://localhost:8020/sse",
        },
    }

    client = MultiServerMCPClient(server_connections)
    tools = await client.get_tools()
    agent = create_react_agent(model=llm, tools=tools)

    persona = (
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "모든 질문에 친절하고 상냥한 말투로 대답해주세요. "
        "말끝마다 '부키!'를 붙여주세요."
    )
    messages = [("system", persona), ("human", question)]

    result = await agent.ainvoke({"messages": messages})
    return result["messages"][-1].content

# ── 메인 루틴 ────────────────────────────────────────────
def main():
    # 1) 두 서버 시작
    weather_proc = start_weather_server()
    amadeus_proc = start_amadeus_server()
    print("❄️ 날씨 MCP 서버 및 ✈️ Amadeus MCP 서버를 시작했습니다...")
    time.sleep(1)  # 각 포트(8010, 8020) 준비 대기

    # 2) 시그널 핸들러 등록 (SIGINT, SIGTERM, SIGTSTP)
    def cleanup(sig, frame):
        print("\n시그널 감지, MCP 서버들을 종료합니다...")
        stop_amadeus_server(amadeus_proc)
        stop_weather_server(weather_proc)
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGTSTP):
        signal.signal(sig, cleanup)

    # 3) 대화형 루프
    try:
        loop = asyncio.get_event_loop()
        print("부엉이 부키와 대화하기 (종료: 빈 입력 후 Enter)")
        while True:
            question = input("You: ").strip()
            if not question:
                break
            answer = loop.run_until_complete(query_mcp(question))
            print(f"부엉이 부키: {answer}\n")
    finally:
        # 4) 서버 종료
        print("MCP 서버들을 종료합니다...")
        stop_amadeus_server(amadeus_proc)
        stop_weather_server(weather_proc)

if __name__ == "__main__":
    main()
