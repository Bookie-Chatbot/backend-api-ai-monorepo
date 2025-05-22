from amadeus import Client, ResponseError
from dotenv import load_dotenv
import os

load_dotenv()

amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

def search_flight_offers(params: dict):
    try:
        response = amadeus.shopping.flight_offers_search.get(**params)
        return response.data
    except ResponseError as error:
        print(f"[Amadeus Error] {error}")
        raise