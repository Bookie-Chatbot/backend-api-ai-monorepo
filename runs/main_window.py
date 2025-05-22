import asyncio, socket, sys, os, signal, subprocess, time, json
from pathlib import Path
from dotenv import load_dotenv
from typing import Any
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.responses import JSONResponse

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

# 프로젝트 경로 상수
ROOT = Path(__file__).resolve().parent.parent
WEATHER_PORT = 8010
AMADEUS_PORT = int(os.getenv("AMADEUS_PORT", 8020))

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_ctx():
    db_gen = get_db()
    db = next(db_gen)
    try:
        yield db
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

def wait_port(host: str, port: int, timeout: float = 20.0):
    print(f"[DEBUG] wait_port: {host}:{port}")
    start = time.perf_counter()
    while time.perf_counter() - start < timeout:
        with socket.socket() as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                print(f"[DEBUG] Port {port} is open")
                return
        time.sleep(0.5)
    raise RuntimeError(f"[ERROR] Port {port} connection timed out")

# ──────────────── 서버 프로세스 실행 함수들 ────────────────
def start_api_server():
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--reload",
        "--app-dir", "apps/api-server/workspace/fastapi-project",
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        stdout=None, stderr=None
    )
    return proc

def stop_process(proc):
    try:
        if os.name == 'nt':
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except Exception as e:
        print(f"[WARN] stop_process failed: {e}")
    proc.wait()

def start_weather():
    cmd = [sys.executable, "-m", "mcp.mcp_server"]
    proc = subprocess.Popen(
        cmd,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        stdout=None, stderr=None,
    )
    return proc

AMADEUS_DIR = "apps/amadeus_mcp_server"

def build_amadeus():
    ret = subprocess.run(["npm", "run", "build"], cwd=AMADEUS_DIR)
    dist_path = Path(AMADEUS_DIR) / "dist" / "cli.js"
    if ret.returncode != 0 or not dist_path.exists():
        raise RuntimeError("[ERROR] Amadeus build failed")

def start_amadeus():
    proc = subprocess.Popen(
        ["npm", "run", "start"],
        cwd=AMADEUS_DIR,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        stdout=None, stderr=None,
    )
    return proc

# ──────────────── LangChain 처리 ────────────────
async def query_chain(user_id: int, question: str, db: Session) -> JSONResponse:
    from api_server.models.chat_log import Message
    from apps.ai_service.src.app.chains.classify_intent import classification_chain, intent_parser
    from apps.ai_service.src.app.chains.intent_router import router

    chat_logs = db.query(Message).filter(Message.user_id == user_id).order_by(Message.timestamp.asc()).all()

    history = []
    for log in chat_logs:
        history.append(("human", log.message))
        try:
            bot_msg = json.loads(log.answer) if isinstance(log.answer, str) else log.answer
        except Exception:
            bot_msg = log.answer
        history.append(("chatbot", bot_msg))

    parsed = await asyncio.get_event_loop().run_in_executor(
        None,
        classification_chain.invoke,
        {
            "question": question,
            "format_instructions": intent_parser.get_format_instructions(),
            "chat_history": history,
        }
    )

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
            return JSONResponse(content=raw.content)
    return JSONResponse(content=parsed)

# ──────────────── 메인 함수 ────────────────
def main():
    load_dotenv()

    print("[INFO] Starting services...")
    api_proc = start_api_server()
    time.sleep(1)
    wait_port("127.0.0.1", 8000)

    weather_proc = start_weather()
    try:
        build_amadeus()
        amadeus_proc = start_amadeus()
    except Exception as e:
        print(f"[ERROR] {e}")
        stop_process(api_proc)
        stop_process(weather_proc)
        sys.exit(1)

    try:
        wait_port("127.0.0.1", WEATHER_PORT)
        wait_port("127.0.0.1", AMADEUS_PORT)
    except Exception as e:
        print(f"[ERROR] Port wait failed: {e}")
        stop_process(api_proc)
        stop_process(weather_proc)
        stop_process(amadeus_proc)
        sys.exit(1)

    def shutdown(sig=None, frame=None):
        print("[INFO] Shutdown signal received")
        stop_process(amadeus_proc)
        stop_process(weather_proc)
        stop_process(api_proc)
        print("[INFO] All processes terminated")
        sys.exit(0)

    if os.name != 'nt':
        for s in (signal.SIGINT, signal.SIGTERM):
            signal.signal(s, shutdown)

    loop = asyncio.get_event_loop()
    try:
        while True:
            q = input("You: ").strip()
            if not q:
                break
            with get_db_ctx() as db:
                answer = loop.run_until_complete(query_chain(user_id=1, question=q, db=db))
                print(f"[BUKI 응답] {answer.body.decode('utf-8')}")
    finally:
        shutdown()

if __name__ == "__main__":
    main()
