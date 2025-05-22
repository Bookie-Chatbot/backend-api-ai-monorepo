#!/usr/bin/env python3
"""
통합 MCP 런처
 - 날씨  : Python FastMCP  → 8010/sse
 - Amadeus : Node(TypeScript) → 8020/sse
"""
import asyncio, socket, sys, os, signal, subprocess, time, json
from pathlib import Path
from dotenv import load_dotenv
import time
from datetime import datetime
import pytz,re


def strip_fence(s: str) -> str:
    """
    ai 응답에 ```json ... ``` 형태로 감싸진 경우
    ```json ... ``` 로 감싸진 부분을 제거하고
    순수 JSON 문자열만 리턴함.
    """
    return re.sub(r"^```json\s*|\s*```$", "", s, flags=re.MULTILINE).strip()


# ──────────────────────────────────────────────────────────
# 1. 공통 유틸
# ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
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
# 2. 날씨 서버 (기존과 동일)
# ──────────────────────────────────────────────────────────
def start_weather():
    cmd = [sys.executable, "-m", "mcp.mcp_server"]
    print(f"[DEBUG] start_weather: 실행 → {cmd}")
    return subprocess.Popen(
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

# ----------------------------------------
# LangChain ⇄ MCP 통합: ask_mcp 함수
# ----------------------------------------
async def ask_mcp(question: str) -> str:
    load_dotenv()
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent

    # 1) MCP 서버 연결
    print("[DEBUG] 1) Initializing MultiServerMCPClient")
    connections = {
        "weather": {"transport": "sse", "url": f"http://localhost:{WEATHER_PORT}/sse"},
        "amadeus": {"transport": "sse", "url": f"http://localhost:{AMADEUS_PORT}/sse"},
    }
    client = MultiServerMCPClient(connections)
    print(f"[DEBUG] 1) client initialized: {client}")
    print(f"[DEBUG] 1) client connections: {client.connections}")

    # 2) available tools 가져오기
    raw_tools = await client.get_tools()
    print(f"[DEBUG] 2) got tools: {[t.name for t in raw_tools]}")

    # 3) 불필요 툴 필터링
    skip = {"query_llm", "initialize", "get_weather"}
    tools = [t for t in raw_tools if t.name not in skip]
    print(f"[DEBUG] 3) filtered tools: {[t.name for t in tools]}")

    limited = {"search-flights", "find-cheapest-dates"}
    tool_cache = {}
    wrapped_tools = []
    print("[DEBUG] 4) wrapping tools with cache guard if needed", flush=True)
    for idx, tool in enumerate(tools):
        print(f"[DEBUG]    tool[{idx}] name => {tool.name}", flush=True)
        if tool.name not in limited:
            wrapped_tools.append(tool)
            continue
        async def arun_wrapper(*args, _tool=tool, **kwargs):
            if _tool.name in tool_cache:
                return tool_cache[_tool.name]
            result = await _tool.arun(*args, **kwargs)
            tool_cache[_tool.name] = result
            return result
        def run_wrapper(*args, _tool=tool, **kwargs):
            if _tool.name in tool_cache:
                return tool_cache[_tool.name]
            result = _tool.run(*args, **kwargs)
            tool_cache[_tool.name] = result
            return result
        tool.arun = arun_wrapper
        tool.run = run_wrapper
        wrapped_tools.append(tool)

        print(f"[DEBUG]      ✅ '{tool.name}' wrapped and added")

    print("[DEBUG] 5) Creating ChatOpenAI agent", flush=True)
    tz = pytz.timezone("Asia/Seoul")
    today = datetime.now(tz).strftime("%Y-%m-%d")

    llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    agent = create_react_agent(model=llm, tools=wrapped_tools, verbose=True)
    print(f"[DEBUG] 5) Agent created with tools: {[t.name for t in wrapped_tools]}")

    # 6) 시스템 + 유저 메시지
    persona = (
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "항공권 질문에는 반드시 search-flights 또는 find-cheapest-dates 툴을 사용해야 해. "
        "모든 답변 끝에 ‘부키!’를 붙여줘. 오늘 날짜는 "
        f"{today}입니다."
    )
    msgs = [("system", persona), ("human", question)]
    print(f"[DEBUG] 6) Sending messages to agent: {msgs}")

    # 7) 에이전트 호출
    result = await agent.ainvoke({"messages": msgs})
    print(f"[DEBUG] 7) raw agent result: {result}")

    # 8) 최종 응답 추출
    final = result["messages"][-1].content
    print(f"[DEBUG] 8) final content: {final}")

    return final



# ──────────────────────────────────────────────────────────
# 5. 메인
# ──────────────────────────────────────────────────────────
def main():
    print("❄️  날씨 MCP  +  ✈️  Amadeus MCP  부팅 중…")
    weather_proc  = start_weather()

    try:
        build_amadeus()            # 컴파일
    except Exception as e:
        print(f"[ERROR] build_amadeus 실패: {e}")
        stop_weather(weather_proc)
        sys.exit(1)
    amadeus_proc  = start_amadeus()
    # 포트 오픈 대기
    try:
        wait_port("127.0.0.1", WEATHER_PORT)
        wait_port("127.0.0.1", AMADEUS_PORT)
    except Exception as e:
        print("❌ 서버 기동 실패:", e)
        stop_amadeus(amadeus_proc)
        stop_weather(weather_proc)
        sys.exit(1)

    print("✅ 두 MCP 서버가 준비되었습니다!")
    print("부엉이 부키와 대화하기 (종료: 빈 줄 + Enter)\n")

    def shutdown(sig, _frame):
        print("\n⏹️  MCP 서버들을 종료합니다…")
        stop_amadeus(amadeus_proc)
        stop_weather(weather_proc)
        sys.exit(0)

    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGTSTP):
        signal.signal(s, shutdown)

    loop = asyncio.get_event_loop()
    try:
        while True:
            q = input("You: ").strip()
            if not q:
                break
            a = loop.run_until_complete(ask_mcp(q))  # Indented this line
        try:
            # if the tool returned a JSON resource, it will already be a JSON string:
            parsed = json.loads(a)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
            print()  # blank line
        except (json.JSONDecodeError, TypeError):
            # fallback to natural-language response
            print(f"부엉이 부키: {a}\n")
    finally:
        shutdown(None, None)

if __name__ == "__main__":
    main()
