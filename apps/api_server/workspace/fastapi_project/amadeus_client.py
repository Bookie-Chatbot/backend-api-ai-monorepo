from amadeus import Client, ResponseError
from dotenv import load_dotenv
import os

load_dotenv()

amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

def search_flight_offers(params: dict):
    formatted_params = {
        "originLocationCode": params.get("origin"),
        "destinationLocationCode": params.get("destination"),
        "departureDate": params.get("departure_date"),
        "adults": 1,
        "currencyCode": "KRW",
        "nonStop": False,
        "max": 5
    }
    print(f"[DEBUG] Sending to Amadeus: {formatted_params}")  # 디버깅용
    response = amadeus.shopping.flight_offers_search.get(**formatted_params)
    return response.data
    