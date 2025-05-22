from celery_app import celery_app
from apps.api_server.workspace.fastapi_project.amadeus_client import search_flight_offers
from apps.api_server.workspace.fastapi_project.models.price_track_request import PriceTrackRequest
from apps.api_server.workspace.fastapi_project.database import SessionLocal
from time import sleep

@celery_app.task
def check_price(user_id: int, search_params: dict, threshold: int):
    flights = search_flight_offers(
        origin=search_params["origin"],
        destination=search_params["destination"],
        departure_date=search_params["departure_date"],
        currency=search_params["KRW"]
    )
    if not flights:
        print("항공편 없음")
        return

    price = int(flights[0]["price"]["total"])
    print(f"현재 가격: {price}원")
    if price < threshold:
        print(f"알림: {price}원이므로 {threshold}원 이하입니다! 알림 발송!")
        # TODO: DB에 저장하거나 알림 발송

@celery_app.task
def check_price_and_notify():
    db = SessionLocal()
    try:
        # is_active인 요청만 가져옴
        requests = db.query(PriceTrackRequest).filter_by(is_active=True).all()
        for req in requests:
            flights = search_flight_offers(
                origin=req.origin,
                destination=req.destination,
                departure_date=req.departure_date,
                currency="KRW"
            )
            if not flights:
                continue

            current_price = int(flights[0]["price"]["total"])
            if current_price <= req.threshold:
                print(f"[ALERT] 유저 {req.user_id}에게 알림 전송: {current_price}원!")
                # 여기서 카카오톡/이메일 등 알림 전송 로직 추가 가능

                # 요청 비활성화
                req.is_active = False
        db.commit()
    finally:
        db.close()