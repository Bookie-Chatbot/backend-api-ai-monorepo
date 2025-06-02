from celery_app import celery_app
from amadeus_client import search_flight_offers
from time import sleep
import logging
from utils.email_alert import send_email
from utils.get_email import get_user_email
from database import SessionLocal
from utils.airline_mapper import get_airline_name
from kakao import alert_api as api
from kakao import global_token as gt
import sys
from dotenv import load_dotenv
import os

load_dotenv()

# 저장된 토큰을 메모리로 불러오기
gt.try_load()

# .env에 설정한 이메일/UUID 정보
USER_EMAIL = os.getenv("USER_EMAIL")
if not USER_EMAIL:
    print("ERROR: 환경 변수 USER_EMAIL이 설정되어 있지 않습니다.")
    sys.exit(1)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@celery_app.task
def check_price(user_id: int, search_params: dict, threshold: int):
    formatted_params = {
        "originLocationCode": search_params.get("origin"),
        "destinationLocationCode": search_params.get("destination"),
        "departureDate": search_params.get("departure_date"),
        "adults": 1,
        "currencyCode": "KRW"
    }
    logger.info(f"[DEBUG] Received params: {formatted_params}")
    logger.info(f"[📦 Celery Task] Checking price for user {user_id} with threshold {threshold}")
    print("🔥 1. Task START")

    db = SessionLocal()
    try:
        user_email = get_user_email(db, user_id)
        logger.info(f"email of {user_id} = {user_email}")
        if not user_email:
            logger.warning(f"User {user_id}: 이메일을 찾을수 없음")
            return

        while True:
            logger.info(f"🔁 Checking price again for user {user_id}...")
            logger.info(f"[DEBUG] Params to Amadeus: {formatted_params}")
            for key, val in formatted_params.items():
                if not val:
                    logger.error(f"[ERROR] Missing required param: {key}")
            flights = search_flight_offers(formatted_params)
            if not flights:
                logger.info("No flights found. Retrying in 30 minutes...")
                sleep(1800)
                continue

            price = int(float(flights[0]["price"]["total"]))
            logger.info(f"현재 가격: {price}원")

            if price < threshold:
                airline_name = get_airline_name(flights[0]['validatingAirlineCodes'][0])
                PRICE_ARGS = {
                    "ORIGIN": search_params['origin'],
                    "DEST": search_params['destination'],
                    "AIRLINE": airline_name,
                    "DEPARTDATE": search_params['departure_date'],
                    "TARGET_PRICE": threshold,
                    "BOOK_URL": "https://chatbot-bookie.pages.dev"
                }
                logger.info("🅺카카오톡 알림 전송 중...")
                response = api.send_price_alert(USER_EMAIL, PRICE_ARGS)
                if response.get("successful_receiver_uuids"):
                    logger.info("🅺카카오톡 알림 전송 성공")
                else:
                    logger.info("🅺카카오톡 알림 전송 실패")

                
                subject = "🦉부키가 알려드려요!🦉"
                body = (
                    f"🎉 가격 임계치 도달! 🎉\n"
                    f" 🛫 {search_params['origin']} → 🛬{search_params['destination']}\n"
                    f"{airline_name} | {search_params['departure_date']}\n"
                    f"💸 현재가: {price}원으로, 🎯 목표가: {threshold}원 이하로 내려왔어요!\n"
                    f"부키가 알려드리는 이 찬스를 놓치지 마세요!\n"  
                    f"지금 바로 👉 [예약 바로가기 링크]\n"  
                    f"부키와 함께 즐거운 여행 준비하세요!\n"
                    f"부키!🦉"   
                )
                send_email(user_email, subject, body)
                logger.info(f"{user_email}로 알림 전송 완료!")
                break
            else:
                airline_name = get_airline_name(flights[0]['validatingAirlineCodes'][0])
                SCHEDULE_ARGS = {
                    "ORIGIN": "서울",
                    "DEST": "제주",
                    "AIRLINE": "KAL",
                    "DEPARTDATE": "2025.06.01",
                    "TARGET_PRICE": "120000",
                    "CURRENT_PRICE": "118500",
                    "CHANGE_RATE": "-1.25",
                    "BOOK_URL": "https://chatbot-bookie.pages.dev"
                }
                logger.info("🅺카카오톡 알림 전송 중...")
                response = api.send_schedule(USER_EMAIL, SCHEDULE_ARGS)
                if response.get("successful_receiver_uuids"):
                    logger.info("🅺카카오톡 알림 전송 성공")
                else:
                    logger.info("🅺카카오톡 알림 전송 실패")

                subject = "🦉부키가 알려드려요!🦉"
                change_rate = ((price - threshold) / threshold) * 100
                body = (
                    f" 🛫 {search_params['origin']} → 🛬{search_params['destination']}\n"
                    f"{airline_name} | {search_params['departure_date']}\n"
                    f"💸 현재가: {price}원으로, 🎯 목표가: {threshold}원\n"
                    f"임계치와 {change_rate}% 차이😢\n"
                    f"부키가 알려드리는 이 찬스를 놓치지 마세요!\n"  
                    f"지금 바로 👉 [예약 바로가기 링크]\n"  
                    f"부키와 함께 즐거운 여행 준비하세요!\n"
                    f"부키!🦉"   
                )
                send_email(user_email, subject, body)
                logger.info(f"{user_email}로 알림 전송 완료!")
                sleep(86400)

            
    finally:
        db.close()
       
