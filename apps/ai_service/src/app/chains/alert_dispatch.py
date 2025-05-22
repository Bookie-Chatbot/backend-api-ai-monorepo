# chains/alert_price_drop.py
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
# from chatbot_contents.alert_price_drop import AlertDispatchPriceDrop

from packages.chatbot_contents.alert_dispatch import AlertDispatchContent
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda, RunnableMap

# PriceDropDispatch 전용 파서
price_drop_parser = PydanticOutputParser(pydantic_object=AlertDispatchContent)

def parse_or_passthrough(text: str):
    try:
        return price_drop_parser.parse(text)
    except Exception:
        return text
    
safe_parser = RunnableLambda(parse_or_passthrough)

price_drop_chain = ({
    "question": lambda x: x["question"],
    "format_instructions": lambda x: x["format_instructions"],
    "chat_history": lambda x: x.get("chat_history", None), }
    | PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
        "가장 최신 대화내역을 최대 5개까지 확인해서 사용자가 알림을 요청하는 항공편에 대해 알림 요청 처리해줘."
        "사용자가 본인이 원하는 price_threshold를 제시하지 않으면, selling_price에서 10% 할인된 가격을 100의 자리에서 내린 값을 default price_threshold로 생각해."
        "channel은 사용자의 query와 상관 없이 무조건 email이야."
        "사용자가 원하는 price_threshold보다 selling_price가 낮으면(if payload.price_threshold > payload.selling_price), 즉시 '해당 항공편은 이미 목표 가격 아래입니다. 바로 예약 진행할까요?' 로 message 출력해줘"
        "예시 1. 사용자: 마지막에서 두 번째거 150000아래로 떨어지면 알림줘. 부키: 아래 항공편 가격이 150000이하로 떨어지면 이메일로 알려드릴까요?"
        "예시 2. 사용자: 보여준 거 중에 제일 싼거 알림줘. 부키: (최신 대화 내역 5개에서 확인한 항공편 중 selling_price가 가장 작은 것을 고른 후)아래 항공편 가격이 [selling_price*0.9] 이하로 떨어지면 이메일로 알려드릴까요?"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"        
    )
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | safe_parser
)

if __name__ == "__main__":
    chain = price_drop_chain
    history = { "user_id": 10, "messages": [{
      "session_id": 17,
      "user_id": 10,
      "message": "한국에서 가장 핫플레이스인 도시들 여행가게 추천해줘",
      "answer": {
        "intent": "DEST_RECOMMEND",
        "contents": {
          "cards": [
            {
              "city": "서울",
              "score": 9.5,
              "photos": [
                "https://example.com/photos/seoul1.jpg",
                "https://example.com/photos/seoul2.jpg"
              ],
              "hashtags": [
                "#서울",
                "#한류",
                "#맛집"
              ],
              "description": "서울은 현대와 전통이 어우러진 도시로, 다양한 문화와 맛있는 음식이 가득해요."
            },
            {
              "city": "부산",
              "score": 9,
              "photos": [
                "https://example.com/photos/busan1.jpg",
                "https://example.com/photos/busan2.jpg"
              ],
              "hashtags": [
                "#부산",
                "#해변",
                "#해산물"
              ],
              "description": "부산은 아름다운 해변과 신선한 해산물로 유명한 도시예요."
            },
            {
              "city": "제주",
              "score": 9.2,
              "photos": [
                "https://example.com/photos/jeju1.jpg",
                "https://example.com/photos/jeju2.jpg"
              ],
              "hashtags": [
                "#제주",
                "#자연",
                "#여행"
              ],
              "description": "제주는 자연의 아름다움과 독특한 문화가 어우러진 여행지예요."
            }
          ],
          "message": "부엉이 부키가 추천하는 한국의 핫플레이스 도시들! 여행의 즐거움을 더해줄 곳들이에요, 부키!"
        }
      },
      "timestamp": "2025-05-22T06:49:45"
    },
    {
      "session_id": 18,
      "user_id": 10,
      "message": "일본으로 가는 가장 싼 항공권 가격 추천해줘",
      "answer": {
        "intent": "PRICE_SEARCH",
        "contents": {
          "flights": [
            {
              "price": 300000,
              "origin": "서울",
              "currency": "KRW",
              "bookingUrl": "https://example.com/book/tokyo",
              "returnDate": "2024-06-10",
              "destination": "도쿄",
              "departureDate": "2024-06-01"
            }
          ],
          "message": "부엉이 부키가 추천하는 일본으로 가는 가장 싼 항공권이에요! 멋진 여행을 준비해보세요, 부키!"
        }
      },
      "timestamp": "2025-05-22T07:39:31"
    },
    {
      "session_id": 19,
      "user_id": 10,
      "message": "✅ 선택한 항공편 정보입니다:\n🛫 ICN → 🛬 LAX\n출발: 2025. 5. 30. 오후 8:35:00\n도착: 2025. 5. 30. 오후 8:45:00\n항공사: CI\n비행 시간: 16시간 10분\n잔여 좌석: 9석\n경유 정보: 1회 경유\n가격: ₩494.81",
      "answer": {
        "intent": "PRICE_SEARCH",
        "contents": {
          "flights": [
            {
              "price": 372020,
              "origin": "ICN",
              "currency": "KRW",
              "bookingUrl": None,
              "returnDate": None,
              "destination": "LAX",
              "departureDate": "2025-05-30T12:50:00"
            }
          ],
          "message": "부엉이 부키가 추천하는 항공편 정보입니다! 멋진 여행을 위한 준비를 해보세요, 부키!"
        }
      },
      "timestamp": "2025-05-22T08:28:10"
    },
    {
      "session_id": 20,
      "user_id": 10,
      "message": "✅ 선택한 항공편 정보입니다:\n🛫 ICN → 🛬 LAX\n출발: 2025. 5. 30. 오후 12:50:00\n도착: 2025. 5. 30. 오전 8:20:00\n항공사: YP\n비행 시간: 11시간 30분\n잔여 좌석: 3석\n경유 정보: 직항\n가격: ₩372.02",
      "answer": {
        "intent": "PRICE_SEARCH",
        "contents": {
          "flights": [
            {
              "price": 258270,
              "origin": "ICN",
              "currency": "KRW",
              "bookingUrl": None,
              "returnDate": None,
              "destination": "Hawaii",
              "departureDate": "2025-05-30T12:50:00"
            }
          ],
          "message": "부엉이 부키가 추천하는 항공편 정보입니다! 멋진 여행을 위한 준비를 해보세요, 부키!"
        }
      },
      "timestamp": "2025-05-22T08:36:09"
    },
    {
      "session_id": 21,
      "user_id": 10,
      "message": "✅ 선택한 항공편 정보입니다:\n🛫 ICN → 🛬 LAX\n출발: 2025. 5. 30. 오후 12:50:00\n도착: 2025. 5. 30. 오전 8:20:00\n항공사: YP\n비행 시간: 11시간 30분\n잔여 좌석: 3석\n경유 정보: 직항\n가격: ₩372.02",
      "answer": {
        "intent": "PRICE_SEARCH",
        "contents": {
          "flights": [
            {
              "price": 408020,
              "origin": "ICN",
              "currency": "KRW",
              "bookingUrl": None,
              "returnDate": None,
              "destination": "North Pole",
              "departureDate": "2025-05-30T12:50:00"
            }
          ],
          "message": "부엉이 부키가 추천하는 항공편 정보입니다! 멋진 여행을 위한 준비를 해보세요, 부키!"
        }
      },
      "timestamp": "2025-05-22T08:40:24"
    }]}

    
    input_dict = {"question": "맨 마지막거 50만원 아래로 떨어지면 알려줘",
        "format_instructions": price_drop_parser.get_format_instructions(),
        "chat_history": history,
        }

    print(chain.invoke(input_dict))


"""
# 가격 알림(price_drop) 설정을 위한 1차 질문 프롬프트

price_drop_prompt = PromptTemplate.from_template(
    '''
항공권 가격 알림을 설정해 드릴게요! 아래 스키마에 맞춰 `contents`를 반환해 주세요.
- intent: ALERT_DISPATCH_PRICE_DROP (자동 설정)
- channel: email 또는 kakao
- userId: 사용자 ID
- message: "OO원 이하로 떨어지면 알림을 받으시길 원하시나요? 알림을 받을 이메일(또는 카카오톡 ID)를 입력해주세요."
- payload: {{
    route: "ICN→LAX",
    targetPrice: 1200000,
    currency: "KRW"
  }}

{format_instructions}
'''
)

price_drop_chain = (
    price_drop_prompt
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | price_drop_parser
)
"""



