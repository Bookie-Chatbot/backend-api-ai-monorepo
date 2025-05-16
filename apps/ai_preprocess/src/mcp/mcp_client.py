import requests
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import asyncio
from dotenv import load_dotenv

async def adapter(query):
    load_dotenv()

    model = ChatOpenAI(
        model="gpt-3.5-turbo"
    )

    server_connections = {
        # "math_service": {
        #     "transport": "stdio",
        #     "command": "python",
        #     "args": [math_server_script_path],
        #     # 필요한 경우 다른 StdioConnection 매개변수를 추가합니다 (env, cwd 등)
        # }, stdio 형식으로 mcp server 연결할 때
        "test": { # 이 연결의 고유 이름
            "transport": "sse",
            "url": "http://localhost:8000/sse", # 날씨 서버가 실행 중인 URL
            # 필요한 경우 다른 SSEConnection 매개변수를 추가합니다 (headers, timeout 등)
        },
    }

    # MultiServerMCPClient 컨텍스트 관리자. 일회성 사용
    async with MultiServerMCPClient(server_connections) as client:
        print("연결 설정 완료")

        all_tools = client.get_tools()
        print(f"연결된 도구: {[tool.name for tool in all_tools]}")

        # 결합된 도구 목록으로 agent 생성
        agent = create_react_agent(model=model, tools=all_tools)

        # agent로 invoke 대신하기
        # query = {"messages": [("human", "뉴욕의 날씨는 어떤가요?")]}
        response = await agent.ainvoke(query)
        print("응답 : ", response['messages'][-1].content)


    """
    client = MultiServerMCPClient(server_connections)   # client를 이런식으로 async 없이 사용하면
    await client.__aenter__()                           # 명시적으로 초기화 필수.

    print(f"연결된 도구: {[tool.name for tool in client.get_tools()]}")
    
    await client.__aexit__()

    근데 이 방법은 안하는게 좋은 듯
    async 환경에서 비동기 컨텍스트(anyio, asyncio)를 사용할 때
    async with를 제대로 안 감싸고 수동으로 __aenter__()->__aexit__() 하다가
    다른 task나 event loop context에서 빠져나가게 되면 충돌 발생.
    """



# Example usage
if __name__ == "__main__":
    asyncio.run(adapter({"messages": [("human", "How's the weather like in New York? Answer using MCP tool.")]}))


