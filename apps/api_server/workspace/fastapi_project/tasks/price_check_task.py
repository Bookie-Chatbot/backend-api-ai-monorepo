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
        user_email = "dokkang@sogang.ac.kr"
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
                subject = "Bookie - 항공권 가격 하락 알림 ✈️"
                body = (
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
                break

            logger.info("아직 임계값보다 가격이 높습니다. 24시간 후 다시 확인합니다.")
            sleep(86400)
    finally:
        db.close()
       
