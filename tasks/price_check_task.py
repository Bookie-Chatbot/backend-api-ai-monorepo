from celery_app import celery_app
from apps.api_server.workspace.fastapi_project.amadeus_client import search_flight_offers
from time import sleep

@celery_app.task
def check_price(user_id: int, search_params: dict, threshold: int):
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
        print(f"알림: {price}원이므로 {threshold}원 이하입니다! 알림 발송!")
        # TODO: DB에 저장하거나 알림 발송

