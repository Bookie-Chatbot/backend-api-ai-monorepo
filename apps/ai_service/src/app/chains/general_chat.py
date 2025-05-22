# chains/general_chat.py
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from chatbot_contents.general_chat import GeneralChatContent

# GeneralChatContent 전용 파서
general_chat_parser = PydanticOutputParser(pydantic_object=GeneralChatContent)

# 일반 대화(GENERAL_CHAT)용 프롬프트
general_chat_prompt = PromptTemplate.from_template(
    '''
당신은 친절한 AI 어시스턴트 '부키'입니다.
아래 형식({format_instructions})에 맞춰, 사용자의 질문에 자연스럽게 응답해 주세요.
'''
)

# 체인 정의: Prompt → LLM → Parser
general_chat_chain = (
    general_chat_prompt
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)
    | general_chat_parser
)
