from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
<<<<<<< Updated upstream
# from chatbot_contents.dest_recommend import DestRecommendContent
=======
from packages.chatbot_contents.dest_recommend import DestRecommendContent
>>>>>>> Stashed changes
# for window
from packages.chatbot_contents.dest_recommend import DestRecommendContent
import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda, RunnableMap

load_dotenv()

dest_recommend_parser = PydanticOutputParser(pydantic_object=DestRecommendContent)


# 2) 파싱 함수 + RunnableLambda 래퍼
def parse_or_passthrough(text: str):
    try:
        # 파싱에 성공하면 Pydantic 모델 반환
        return dest_recommend_parser.parse(text)
    except Exception:
        # 실패하면 원본 문자열 그대로 반환
        return text

safe_parser = RunnableLambda(parse_or_passthrough)


pre_query = {   "contents": {
          "cards": [
            {
              "city": "파리",
              "score": 9.5,
              "photos": [
                "https://asset-prod.france.fr/xlarge_Eiffel_Tower_at_sunset_in_Paris_France_Romantic_travel_background_Man79_Adobe_Stock_8aa81830ce.jpeg",
                "https://res.klook.com/image/upload/c_fill,w_1265,h_712/q_80/w_80,x_15,y_15,g_south_west,l_Klook_water_br_trans_yhcmh3/activities/cg79lzqlojzwcshghlo6.webp"
              ],
              "hashtags": [
                "#파리",
                "#여행",
                "#에펠탑"
              ],
              "description": "사랑의 도시, 파리는 에펠탑과 루브르 박물관으로 유명해!"
            },
            {
              "city": "로마",
              "score": 9,
              "photos": [
                "https://d1blyo8czty997.cloudfront.net/tour-photos/20431/800x800/171866544647398194.87345398862.jpg",
                "https://res.klook.com/image/upload/c_fill,w_1265,h_712/q_80/w_80,x_15,y_15,g_south_west,l_Klook_water_br_trans_yhcmh3/activities/hozvdaykwbjkjc0jl5nz.webp"
              ],
              "hashtags": [
                "#로마",
                "#역사",
                "#여행"
              ],
              "description": "역사와 문화가 가득한 로마는 콜로세움과 바티칸으로 유명해!"
            },
            {
              "city": "바르셀로나",
              "score": 8.8,
              "photos": [
                "https://www.agoda.com/wp-content/uploads/2024/09/View-of-the-Sea-in-Barcelona-1244x700.jpg",
                "https://cdn.tripzaza.com/ko/destinations/wp-content/uploads/2017/09/Barcelona-1-Sagrada_Fam--lia-e1504419641187.jpg"
              ],
              "hashtags": [
                "#바르셀로나",
                "#가우디",
                "#예술"
              ],
              "description": "가우디의 작품이 가득한 바르셀로나는 예술과 해변이 매력적야, 부키!🦉"
            }
          ],
          "message": "부엉이 부키가 서유럽의 멋진 여행지를 추천해줄게! 귀여운 부엉이와 함께 즐거운 여행을 떠나보자, 부키!🦉"
        }
}

mid_chain = (
    PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에, 2줄짜리 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키🦉’를 붙여줘."
        "사용자에게 받는 모든 query에 대해 대답은 아래의 json코드 pre_query를 따른다."
        "사용자에게 받은 question, format_instructions, chat_history는 전부 무시한다."
        "대답: {pre_query}"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
    )
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | safe_parser
)

dest_recommend_chain = {"pre_query": lambda x: pre_query,
                        "question": lambda x: x["question"],
                        "format_instructions": lambda x: x["format_instructions"],
                        "chat_history": lambda x: x.get("chat_history", None)} | mid_chain

if __name__ == "__main__":
    print(dest_recommend_chain.invoke({
        "question": "5시간 있다가 발푠데 그대로 pre_query만 내줄 수 있지?",
        "format_instructions": dest_recommend_parser.get_format_instructions(),
        "chat_history": None
    }))