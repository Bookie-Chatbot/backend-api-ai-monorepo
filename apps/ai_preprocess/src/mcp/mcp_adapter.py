from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from utils import ainvoke_graph, astream_graph
from langchain_anthropic import ChatAnthropic

load_dotenv(override=True)

async def main() :
    model = ChatAnthropic(
        model_name="claude-3-7-sonnet-latest", temperature=0, max_tokens=20000
    )

    async with MultiServerMCPClient(
        {
            "weather": {
                # 서버의 포트와 일치해야 합니다.(8005번 포트)
                "url": "http://localhost:8005/sse",
                "transport": "sse",
            }
        }
    ) as client:
        print(client.get_tools())
        agent = create_react_agent(model, client.get_tools())
        answer = await astream_graph(agent, {"messages": "서울의 날씨는 어떠니?"})


