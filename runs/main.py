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
import launch_api

import subprocess
import sys
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
ROOT = Path(__file__).resolve().parent.parent
WEATHER_PORT  = 8010
AMADEUS_PORT  = int(os.getenv("AMADEUS_PORT", 8020))



def wait_port(host: str, port: int, timeout: float = 2000.0):
    """포트가 열릴 때까지 블로킹 대기"""
    print(f"[DEBUG] wait_port: start waiting {host}:{port} (timeout={timeout}s)")
    start = time.perf_counter()
    while time.perf_counter() - start < timeout:
        with socket.socket() as sock:
            sock.settimeout(1)
            res = sock.connect_ex((host, port))
            print(f"[DEBUG] wait_port: try connect → {res}")
            if res == 0:
                print(f"[DEBUG] wait_port: port {port} is open!")
                return
        time.sleep(0.2)
    raise RuntimeError(f"포트 {port} 대기 시간 초과")

# ──────────────────────────────────────────────────────────
# 1. API 서버 (Uvicorn)
# ──────────────────────────────────────────────────────────
def start_api_server():
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--reload",
        "--app-dir", "apps/api-server/workspace/fastapi-project",
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
    print(f"[DEBUG] start_api_server: 실행 → {cmd}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        preexec_fn=os.setsid,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,                # 텍스트 모드로 출력
    )
    return proc




def stop_api_server(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except Exception:
        pass
    proc.wait()


# ──────────────────────────────────────────────────────────
# 2. 날씨 서버 (기존과 동일)
# ──────────────────────────────────────────────────────────
def start_weather():
    cmd = [sys.executable, "-m", "mcp.mcp_server"]
    print(f"[DEBUG] start_weather: 실행 → {cmd}")
    proc = subprocess.Popen(
        cmd,
        preexec_fn=os.setsid,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"[DEBUG] start_weather: PID={proc.pid}")
    return proc

def stop_weather(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except ProcessLookupError:
        pass
    proc.wait()

# ──────────────────────────────────────────────────────────
# 3. Amadeus 서버(Node) – cwd 지정 & 빌드 보장
# ──────────────────────────────────────────────────────────
AMADEUS_DIR = "apps/amadeus_mcp_server"

def build_amadeus():
    cmd = ["npm", "run", "build"]
    cwd_path: Path = Path(AMADEUS_DIR)
    print(f"[DEBUG] build_amadeus: cwd={cwd_path}")
    print(f"[DEBUG] build_amadeus: 실행 → {cmd}")

    ret = subprocess.run(
        cmd,
        cwd=str(cwd_path),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"[DEBUG] build_amadeus: returncode={ret.returncode}")

    dist_path = cwd_path / "dist" / "cli.js"
    print(f"[DEBUG] build_amadeus: looking for {dist_path}")
    if ret.returncode != 0 or not dist_path.exists():
        raise RuntimeError("[ERROR] build_amadeus: 빌드 실패 또는 dist/cli.js 누락")


def start_amadeus():
    cmd = ["npm", "run", "start"]
    cwd = str(AMADEUS_DIR)
    print(f"[DEBUG] start_amadeus: cwd={cwd}")
    print(f"[DEBUG] start_amadeus: 실행 → {cmd}")
    proc = subprocess.Popen(
        cmd,
        cwd=AMADEUS_DIR,
        preexec_fn=os.setsid,
        stdout=None,
        stderr=None,
    )
    print(f"[DEBUG] start_amadeus: PID={proc.pid}")
    return proc

def stop_amadeus(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except ProcessLookupError:
        pass
    proc.wait()

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

     # 1) API 서버 실행 및 포트 대기
    api_proc = start_approc = start_api_server()
# 1초 정도 대기한 뒤
    time.sleep(1)
   # print(api_proc.stdout.read())  # 또는 readline() 반복
    wait_port("127.0.0.1", 8000)
    print("  - API 서버 시작 완료 (포트 8000)")
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
        stop_api_server(api_proc)
        print("  - API 서버 종료")
        sys.exit(1)

    print("✅ MCP 서버들 기동 완료! 부엉이 부키와 대화 시작...")

    # 시그널 핸들러
    def shutdown(sig, frame):
        print("\n⏹️  종료 신호 감지, 모든 서버 종료 중…")
        stop_amadeus(amadeus_proc)
        stop_weather(weather_proc)
        stop_api_server(api_proc)
        print("✅ 모든 서버 종료 완료!")
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
