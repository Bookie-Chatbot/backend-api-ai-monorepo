#!/usr/bin/env python3
import asyncio
import subprocess
import time
import signal
import sys
import os
from dotenv import load_dotenv

# LangChain MCP client libraries
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


def start_server():
    """
    MCP 서버를 백그라운드에서 실행.
    """
    # 새로운 세션을 만들어, 자식 프로세스 그룹 전체를 제어할 수 있도록 함
    return subprocess.Popen([
        sys.executable,
        "-m", "mcp.mcp_server"
    ], preexec_fn=os.setsid,
       stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
       )


def stop_server(proc):
    """
    MCP 서버 프로세스를 안전하게 종료.
    """
    try:
        # 프로세스 그룹 전체에 SIGINT 신호 전달
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    except Exception:
        pass
    proc.wait()


async def query_mcp(question: str) -> str:
    """
    주어진 질문을 MCP 서버에 보내고, 응답 콘텐츠를 반환.
    """
    load_dotenv()  # .env에서 API 키 로드

    llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    server_connections = {
        "test": {
            "transport": "sse",
            "url": "http://localhost:8010/sse",
        },
    }

    client = MultiServerMCPClient(server_connections)
    tools = await client.get_tools()
    agent = create_react_agent(model=llm, tools=tools)

    # 부엉이 부키 페르소나 지시문 추가
    persona = (
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "모든 질문에 친절하고 상냥한 말투로 대답해주세요. "
        "말끝마다 '부키!'를 붙여주세요."
    )
    messages = [
        ("system", persona),
        ("human", question)
    ]

    result = await agent.ainvoke({"messages": messages})

    # 마지막 메시지의 content를 반환
    return result["messages"][-1].content


def main():
    # 1) 서버 시작
    proc = start_server()
    print("부엉이 부키 MCP 서버를 시작했습니다...")
    time.sleep(1)  # 서버 준비 대기

    # 2) 시그널 핸들러 등록: SIGINT, SIGTERM, SIGTSTP
    def cleanup(sig, frame):
        print("\n시그널 감지, MCP 서버를 종료합니다...")
        stop_server(proc)
        sys.exit(0)

    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGTSTP):
        signal.signal(s, cleanup)

    try:
        loop = asyncio.get_event_loop()
        print("부엉이 부키와 대화하기 (종료: 빈 입력 후 Enter)")
        while True:
            question = input("You: ")
            if not question.strip():
                break
            answer = loop.run_until_complete(query_mcp(question))
            print(f"부엉이 부키: {answer}\n")
    finally:
        # 3) 서버 종료
        print("MCP 서버를 종료합니다...")
        stop_server(proc)


if __name__ == "__main__":
    main()


'''
for window

import asyncio
import subprocess
import time
import signal
import sys
import os
import platform
from dotenv import load_dotenv

# LangChain MCP client libraries
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

def start_server():
    """
    MCP 서버를 백그라운드에서 실행 (Windows 호환).
    """
    return subprocess.Popen(
        [sys.executable, "-m", "mcp.mcp_server"],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def stop_server(proc):
    """
    MCP 서버 프로세스를 안전하게 종료 (Windows 호환).
    """
    try:
        proc.send_signal(signal.CTRL_BREAK_EVENT)
    except Exception:
        pass
    proc.wait()

async def query_mcp(question: str) -> str:
    """
    주어진 질문을 MCP 서버에 보내고, 응답 콘텐츠를 반환.
    """
    load_dotenv()
    llm = ChatOpenAI(model_name="gpt-3.5-turbo")

    server_connections = {
        "test": {
            "transport": "sse",
            "url": "http://localhost:8010/sse",
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

    messages = [
        ("system", persona),
        ("human", question)
    ]

    result = await agent.ainvoke({"messages": messages})
    return result["messages"][-1].content

def register_signals(cleanup):
    """
    Windows/Unix 호환 시그널 핸들러 등록 함수
    """
    signals = [signal.SIGINT, signal.SIGTERM]
    for s in signals:
        signal.signal(s, cleanup)

def main():
    proc = start_server()
    print("부엉이 부키 MCP 서버를 시작했습니다...")
    time.sleep(1)

    def cleanup(sig, frame):
        print("\n시그널 감지, MCP 서버를 종료합니다...")
        stop_server(proc)
        sys.exit(0)

    register_signals(cleanup)

    try:
        loop = asyncio.get_event_loop()
        print("부엉이 부키와 대화하기 (종료: 빈 입력 후 Enter)")
        while True:
            question = input("You: ")
            if not question.strip():
                break
            answer = loop.run_until_complete(query_mcp(question))
            print(f"부엉이 부키: {answer}\n")
    finally:
        print("MCP 서버를 종료합니다...")
        stop_server(proc)

if __name__ == "__main__":
    main()

'''