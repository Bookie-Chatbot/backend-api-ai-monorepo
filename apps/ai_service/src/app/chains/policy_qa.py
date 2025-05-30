<<<<<<< Updated upstream
=======
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from packages.chatbot_contents.policy_qa import PolicyQAContent
# for window
# from packages.chatbot_contents.policy_qa import PolicyQAContent
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda

load_dotenv()

policy_qa_parser = PydanticOutputParser(pydantic_object=PolicyQAContent)

def parse_or_passthrough(text: str):
    try:
        return policy_qa_parser.parse(text)
    except Exception:
        return text

safe_parser = RunnableLambda(parse_or_passthrough)

policy_qa_chain = (
    PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
        "특정 항공사나 호텔에 관한 정책은 source가 해당 회사 이름인 DB에서 찾아줘."
        "회사를 특정하지 않으면 항공 관련 정책 질의는 flight_policy.pdf에서, 호텔 관련 정책 질의는 hotel_policy.pdf에서 찾아줘."
        "질문에 대해 아래 JSON Schema에 맞춰서 결과 반환해줘.\n"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
    )
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | safe_parser
)

>>>>>>> Stashed changes
