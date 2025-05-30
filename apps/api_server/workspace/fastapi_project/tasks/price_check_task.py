from celery_app import celery_app
from amadeus_client import search_flight_offers
from time import sleep
import logging
from utils.email_alert import send_email
from utils.get_email import get_user_email
from database import SessionLocal

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@celery_app.task
def check_price(user_id: int, search_params: dict, threshold: int):
    logger.info(f"[DEBUG] Received params: {search_params}")
    logger.info(f"[📦 Celery Task] Checking price for user {user_id} with threshold {threshold}")
    print("🔥 1. Task START")

    db = SessionLocal()
    try:
        print("🔥 2. Try block 진입")
        ##user_email = get_user_email(db, user_id)
        user_email = "dokkang@sogang.ac.kr"
        if not user_email:
            logger.warning(f"User {user_id}: 이메일을 찾을수 없음")
            return
        # print(search_params) 넣어서 실제 전달된 딕셔너리 확인해보세요
        logger.info(f"search_params: {search_params}")

        # search_params가 이중 딕셔너리로 올 경우 처리
        if "origin" not in search_params and "search_params" in search_params:
            search_params = search_params["search_params"]

        flights = search_flight_offers(search_params)
        if not flights:
            print("항공편 없음")
            return

        price = int(flights[0]["price"]["total"])
        print(f"현재 가격: {price}원")
        ##if price < threshold:
        subject = "Bookie - 항공권 가격 하락 알림 ✈️"
        body =  (
                f"안녕하세요!\n\n"
                f"설정하신 항공권 가격이 {threshold}원 이하로 떨어졌습니다!\n"
                f"- 출발지: {search_params['origin']}\n"
                f"- 도착지: {search_params['destination']}\n"
                f"- 출발일: {search_params['departure_date']}\n"
                f"- 현재 가격: {price}원\n\n"
                f"지금 바로 예약하세요!\n\n"
                f"감사합니다.\n"
            )
        send_email(user_email, subject, body)
        logger.info(f"{user_email}로 알림 전송 완료!")
    finally:
        db.close()

       

