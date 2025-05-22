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
from fastapi import Depends

import launch_api
from contextlib import contextmanager



import subprocess
import sys
# Pydantic 모델 & 체인
from chatbot_contents.intents import IntentOnly, Intent
from chains.classify_intent import classification_chain, intent_parser
from chains.intent_router import router
import os
from dotenv import load_dotenv

from database import Base, get_db
load_dotenv()


# ──────────────────────────────────────────────────────────
# 1. 공통 유틸
# ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
WEATHER_PORT  = 8010
AMADEUS_PORT  = int(os.getenv("AMADEUS_PORT", 8020))

@contextmanager
def get_db_ctx():
    db_gen = get_db()     # this is a generator
    db = next(db_gen)      # enter the generator to get the Session
    try:
        yield db
    finally:
        try:
            next(db_gen)   # run the finally block inside get_db()
        except StopIteration:
            pass

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
    print(f"[DEBUG] start_api_server: 실행할 명령 → {cmd}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        preexec_fn=os.setsid,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(f"[DEBUG] start_api_server: 프로세스 PID={proc.pid}")
    return proc


def stop_api_server(proc):
    print(f"[DEBUG] stop_api_server: 종료 신호 보냄 to PID={proc.pid}")
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except Exception as e:
        print(f"[DEBUG] stop_api_server: 예외 발생 {e}")
    proc.wait()
    print("[DEBUG] stop_api_server: 완료")


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
async def query_chain(user_id: int, question: str, db: any) -> JSONResponse:
    # Message 모델 import 지연
    from api_server.models.chat_log import Message
    print(f"[DEBUG] query_chain: 시작 user_id={user_id}, question={question}")
    print("[DEBUG] DB 세션 열기 완료")

    # 이전 대화 조회
    print("[DEBUG] DB에서 messages 쿼리 시작")
    try:
        chat_logs = db.query(Message) \
            .filter(Message.user_id == user_id) \
            .order_by(Message.timestamp.asc()) \
            .all()
        print(f"[DEBUG] {len(chat_logs)}개의 대화 내역 로드 완료")
    except Exception as e:
        print(f"[DEBUG] DB 쿼리 에러: {e}")
        chat_logs = []

    # 히스토리 구성
    history = []
    for log in chat_logs:
        history.append(("human", log.message))
        print(f"[DEBUG] history append user: {log.message}")
        try:
            bot_msg = log.answer if isinstance(log.answer, dict) else json.loads(log.answer)
        except Exception:
            bot_msg = log.answer
        history.append(("chatbot", bot_msg))
        print(f"[DEBUG] history append bot: {bot_msg}")
    print(f"[DEBUG] 히스토리 구성 완료 ({len(history)} entries)")

    # 1) IntentOnly 분류
    parsed = await asyncio.get_event_loop().run_in_executor(
    None,                             # executor: None은 기본 스레드 풀
    classification_chain.invoke,     # func: 실행할 함수
    {                                 # *args: 함수에 넘길 딕셔너리
        "question": question,
        "format_instructions": intent_parser.get_format_instructions(),
        "chat_history": history,
    }
)



    print(f"  - IntentOnly: {parsed}")

    raw = await asyncio.get_event_loop().run_in_executor(
    None,
    router.invoke,
    {
        "intent_only": parsed,
        "question": question,
        "chat_history": history,
    }
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

    print("[INFO] 메인 시작: API 서버, MCP 서버, Launcher 기동")
    api_proc = start_api_server()
    time.sleep(1)
    wait_port("127.0.0.1", 8000)
    print("[INFO] API 서버 준비 완료")

    weather_proc = start_weather()
    print("[INFO] 날씨 MCP 서버 시작 완료")

    try:
        build_amadeus()
        amadeus_proc = start_amadeus()
        print("[INFO] Amadeus MCP 서버 시작 완료")
    except Exception as e:
        print(f"[ERROR] Amadeus 초기화 실패: {e}")
        stop_weather(weather_proc)
        stop_api_server(api_proc)
        sys.exit(1)

    try:
        wait_port("127.0.0.1", WEATHER_PORT)
        wait_port("127.0.0.1", AMADEUS_PORT)
    except Exception as e:
        print(f"[ERROR] 포트 대기 실패: {e}")
        stop_amadeus(amadeus_proc)
        stop_weather(weather_proc)
        stop_api_server(api_proc)
        sys.exit(1)

    print("[INFO] 모든 MCP 서버 기동 완료 — 대화 대기 중…")

    # 시그널 핸들러 등록
    def shutdown(sig, frame):
        print("[INFO] 종료 신호 감지 — 서버 중단 시작")
        stop_amadeus(amadeus_proc)
        stop_weather(weather_proc)
        stop_api_server(api_proc)
        print("[INFO] 모든 서버 종료 완료")
        sys.exit(0)
    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGTSTP):
        signal.signal(s, shutdown)

    loop = asyncio.get_event_loop()
    try:
        while True:
            print("[DEBUG] 사용자 입력 대기 중… (빈 줄 입력 시 종료)")
            q = input("You: ").strip()
            if not q:
                print("[DEBUG] 빈 입력 감지 — 종료 루프")
                break
            print(f"[DEBUG] 입력 값 = {q}")
            try:
                with get_db_ctx() as db:
                    answer = loop.run_until_complete(query_chain(
                        user_id=1,
                        question=q,
                        db=db  # FastAPI 의존성 주입
                    ))
                print(f"[DEBUG] query_chain 반환 타입 = {type(answer)}")
                print(f"[BUKI 응답] {answer.body.decode('utf-8')}")
            except Exception as e:
                print(f"[ERROR] query_chain 실행 중 예외: {e}")
    finally:
        print("[INFO] 메인 루프 종료 — 종료 핸들러 실행")
        shutdown(None, None)


if __name__ == "__main__":
    main()
