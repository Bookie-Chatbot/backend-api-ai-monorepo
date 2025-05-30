from celery_app import celery_app
from apps.api_server.workspace.fastapi_project.amadeus_client import search_flight_offers
from time import sleep
import logging
from utils.email_alert import send_email
from utils.get_email import get_user_email
from database import SessionLocal

logger = logging.getLogger(__name__)

@celery_app.task
def check_price(user_id: int, search_params: dict, threshold: int):
    logger.info(f"[📦 Celery Task] Checking price for user {user_id} with threshold {threshold}")

    db = SessionLocal()
    try:
        ##user_email = get_user_email(db, user_id)
        user_email = "dokkang01@sogang.ac.kr"
        if not user_email:
            logger.warning(f"User {user_id}: 이메일을 찾을수 없음")
            return
        flights = search_flight_offers(
            origin=search_params["origin"],
            destination=search_params["destination"],
            departure_date=search_params["departure_date"]
        )
        if not flights:
            print("항공편 없음")
            return

        price = int(flights[0]["price"]["total"])
        print(f"현재 가격: {price}원")
        if price < threshold:
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

       

