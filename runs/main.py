#!/usr/bin/env python3
"""
통합 MCP + LangChain 런처
 - 날씨  : Python FastMCP  → 8010/sse
 - Amadeus : Node(TypeScript) → 8020/sse
 - LangChain Intent Classification → Routing → Sub-chain 처리
"""
import asyncio, socket, sys, os, signal, subprocess, time, json
from pathlib import Path
from dotenv import load_dotenv
from typing import Any
# LangChain imports
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableLambda
from fastapi.responses import JSONResponse,PlainTextResponse



# Pydantic 모델 & 체인
from chatbot_contents.intents import IntentOnly, Intent
from chains.classify_intent import classification_chain, intent_parser
from chains.intent_router import router
import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────
# 1. 공통 유틸
# ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
WEATHER_PORT  = 8010
AMADEUS_PORT  = int(os.getenv("AMADEUS_PORT", 8020))

# 포트 오픈 대기
def wait_port(host: str, port: int, timeout: float = 20.0):
    start = time.perf_counter()
    while time.perf_counter() - start < timeout:
        with socket.socket() as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError(f"포트 {port} 대기 시간 초과")

# ──────────────────────────────────────────────────────────
# 2. 날씨 MCP 서버
# ──────────────────────────────────────────────────────────

def start_weather():
    cmd = [sys.executable, "-m", "mcp.mcp_server"]
    return subprocess.Popen(cmd, preexec_fn=os.setsid,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_weather(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except Exception:
        pass
    proc.wait()

# ──────────────────────────────────────────────────────────
# 3. Amadeus MCP 서버
# ──────────────────────────────────────────────────────────
AMADEUS_DIR = "apps/amadeus_mcp_server"

def build_amadeus():
    subprocess.run(["npm", "run", "build"], cwd=str(AMADEUS_DIR), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_amadeus():
    cmd = ["npm", "run", "start"]
    return subprocess.Popen(cmd, cwd=str(AMADEUS_DIR), preexec_fn=os.setsid)

def stop_amadeus(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except Exception:
        pass
    proc.wait()


def _json_safe(obj: Any):
    """LangChain Message 객체 등을 str로 바꿔 JSON 직렬화."""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except TypeError:
        # dict이지만 message 내부에 HumanMessage 같은 객체가 있을 때
        def convert(o):
            if isinstance(o, list):
                return [convert(i) for i in o]
            if isinstance(o, dict):
                return {k: convert(v) for k, v in o.items()}
            return str(o)
        return json.dumps(convert(obj), ensure_ascii=False, indent=2)

# ──────────────────────────────────────────────────────────
# 4. LangChain → Intent 분류 & 라우팅 → Sub-chain
# ──────────────────────────────────────────────────────────
async def query_chain(question: str) -> str:
    # 1) IntentOnly 분류
    parsed = await asyncio.get_event_loop().run_in_executor(
        None,
        classification_chain.invoke,
        {
            "question": question,
            "format_instructions": intent_parser.get_format_instructions()
        }
    )
    print(f"  - IntentOnly: {parsed}")

    # 2) 라우터에 분류 + question 전달 → 즉시 실행된 결과 반환
    raw = await asyncio.get_event_loop().run_in_executor(
        None,
        router.invoke,
        {"intent_only": parsed, "question": question}
    )
    if hasattr(raw, "content"):
            try:
                parsed = json.loads(raw.content)
            except json.JSONDecodeError:
                # 혹시 유효 JSON이 아닐 경우, 그냥 문자열로 래핑
                return JSONResponse(content=raw.content)
    return JSONResponse(content=parsed)
    #return  _json_safe(raw)


    # 3) contents 가 있으면 JSON, 아니면 문자열
   # if hasattr(raw, "contents"):
   # return str(raw)

# ──────────────────────────────────────────────────────────
# 5. 메인
# ──────────────────────────────────────────────────────────
def main():
    load_dotenv()
    print("❄️  날씨 MCP  +  ✈️  Amadeus MCP + LangChain 런처 기동 중…")

    # 1) 날씨 서버
    weather_proc = start_weather()
    print("  - 날씨 서버 시작...")

    # 2) Amadeus
    try:
        build_amadeus()
        amadeus_proc = start_amadeus()
        print("  - Amadeus 서버 시작...")
    except Exception as e:
        print(f"[ERROR] Amadeus 빌드/기동 실패: {e}")
        stop_weather(weather_proc)
        sys.exit(1)

    # 3) 포트 대기
    try:
        wait_port("127.0.0.1", WEATHER_PORT)
        wait_port("127.0.0.1", AMADEUS_PORT)
    except Exception as e:
        print(f"[ERROR] 포트 대기 실패: {e}")
        stop_amadeus(amadeus_proc)
        stop_weather(weather_proc)
        sys.exit(1)

    print("✅ MCP 서버들 기동 완료! 부엉이 부키와 대화 시작...")

    # 시그널 핸들러
    def shutdown(sig, frame):
        print("\n⏹️  종료 신호 감지, 모든 서버 종료 중…")
        stop_amadeus(amadeus_proc)
        stop_weather(weather_proc)
        sys.exit(0)
    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGTSTP):
        signal.signal(s, shutdown)

    # 사용자 인터랙션
    loop = asyncio.get_event_loop()
    try:
        while True:
            q = input("You: ").strip()
            if not q:
                break
            answer = loop.run_until_complete(query_chain(q))
            print(type(answer))
            print("부키의 응답",answer.body.decode("utf-8"))
    finally:
        shutdown(None, None)

if __name__ == "__main__":
    main()
