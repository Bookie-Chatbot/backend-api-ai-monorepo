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
from langchain_core.messages import AIMessage, BaseMessage
from pydantic import BaseModel

def _to_plain(obj: Any) -> Any:
    """
    ✅  AIMessage            → obj.content
    ✅  list[ ... ]          → 각 원소 재귀 변환
    ✅  dict / pydantic Base → value 재귀 변환
    나머지는 그대로 반환
    """
    if isinstance(obj, AIMessage):
        return obj.content

    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]

    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}

    # pydantic BaseModel 도 dict 로 내려치기
    if isinstance(obj, BaseModel):
        return _to_plain(obj.model_dump())

    return obj



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

# ----------------------------------------------------------------------
# query_chain  ──  LangChain → Intent 분류 → 서브체인 호출 → 결과 반환
# ----------------------------------------------------------------------
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, PlainTextResponse
from chatbot_contents.intents import IntentOnly, Intent   # 타입 힌트용
from sqlalchemy.orm import Session                       # DB 타입 힌트

async def query_chain(user_id: int,
                      question: str,
                      db: Session) -> dict[str, Any]:
    """
    ① DB 에서 과거 대화 이력 조회
    ② LangChain 분류 체인으로 IntentOnly 얻기
    ③ Intent 라우터(chain) 실행 → 결과(Pydantic | dict | str)
    ④ 언제나 JSON 직렬화 가능한 형태로 감싸서 JSONResponse 반환
    """
    # 지연 import – 순환 참조 방지
    from api_server.models.chat_log import Message

    print(f"[DEBUG] query_chain: 시작 user_id={user_id}, question={question!r}")

    # ── 1) 대화 이력 ----------------------------------------------------------
    history: list[tuple[str, Any]] = []
    try:
        chat_logs = (
            db.query(Message)
              .filter(Message.user_id == user_id)
              .order_by(Message.timestamp.asc())
              .all()
        )
    except Exception as e:
        print(f"[WARN] DB 조회 실패: {e}")
        chat_logs = []

    for log in chat_logs:
        # human
        history.append(("human", _to_plain(log.message)))
        # bot
        try:
            bot_payload = (
                log.answer
                if isinstance(log.answer, dict)
                else json.loads(log.answer)
            )
        except Exception:
            bot_payload = log.answer
        history.append(("chatbot", _to_plain(bot_payload)))

    print(f"[DEBUG] history 길이 = {len(history)}")

    # ── 2) IntentOnly 분류 ----------------------------------------------------
    intent_only: IntentOnly = await asyncio.get_event_loop().run_in_executor(
        None,
        classification_chain.invoke,
        {
            "question": question,
            "format_instructions": intent_parser.get_format_instructions(),
            "chat_history": history,
        },
    )
    print(f"[DEBUG] IntentOnly = {intent_only}")

    # ── 3) Intent 라우팅 체인 --------------------------------------------------
    chain_output = await asyncio.get_event_loop().run_in_executor(
        None,
        router.invoke,
        {
            "intent_only": intent_only,
            "question":    question,
            "chat_history": history,
        },
    )

    # ── 4) 결과 직렬화 & 응답 --------------------------------------------------
    try:
     # 3) 라우팅 후
      if isinstance(chain_output, BaseModel):
       chain_output = chain_output.model_dump(mode="python")

       answer = {
        "answer": {
            "intent": intent_only.intent.value,
            "contents": chain_output["contents"]   # 이미 dict
        }
    }
    except Exception as err:
        # 마지막 보루 – 문자열로라도 반환
        print(f"[ERROR] 직렬화 실패: {err}")
        answer = {
            "answer": {
                "intent": intent_only.intent.value,  # Intent 문자열로 변환
                "contents": chain_output.contents,       # Pydantic 모델이나 dict
            }
        }
    return answer





    # 3) contents 가 있으면 JSON, 아니면 문자열
   # if hasattr(raw, "contents"):
   # return str(raw)
""""""
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
        wait_port("0.0.0.0", WEATHER_PORT)
        wait_port("0.0.0.0", AMADEUS_PORT)
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
                loop.run_until_complete(asyncio.sleep(3600))
    finally:
        print("[INFO] 메인 루프 종료 — 종료 핸들러 실행")
        shutdown(None, None)


if __name__ == "__main__":
    main()