"""검색 결과를 사람이 읽을 문장으로 변환하는 LLM 프롬프트."""
import json, datetime as dt
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

TODAY = dt.date.today().isoformat()

PROMPT = ChatPromptTemplate.from_messages([
    ("system", f"오늘 날짜는 {TODAY} 입니다. 아래 JSON 데이터를 읽고 사용자에게 친절히 안내하세요."),
    ("user",   "질문: {question}\n\n검색결과(JSON): ```{result}```")
])

_llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)

def build_answer(question: str, result: dict) -> str:
    msg = _llm.invoke(PROMPT.format(
        question = question,
        result   = json.dumps(result, ensure_ascii=False)
    ))
    return msg.content.strip()
