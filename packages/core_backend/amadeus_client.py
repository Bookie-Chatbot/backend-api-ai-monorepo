# packages/core_backend/amadeus_client.py
from amadeus import Client, ResponseError
import os
from dotenv import load_dotenv

load_dotenv()                                     # ① .env → env vars

def get_client() -> Client:
    """
    Always returns a live Amadeus Client or raises a helpful exception.
    """
    cid  = os.getenv("AMADEUS_CLIENT_ID")
    csec = os.getenv("AMADEUS_CLIENT_SECRET")

    if not cid or not csec:                       # ② helpful error
        raise RuntimeError(
            "❌ AMADEUS_CLIENT_ID / _SECRET not set – check your .env"
        )

    return Client(
        client_id     = cid,
        client_secret = csec,
        log_level     = "debug",                  # extra transparency
        timeout       = 10
    )
