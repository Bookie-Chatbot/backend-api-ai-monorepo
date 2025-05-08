# packages/core_backend/amadeus_client.py
import os
from functools import lru_cache
from amadeus import Client

@lru_cache
def get_client() -> Client:            # 싱글턴
    return Client(
        client_id  = os.getenv("AMADEUS_CLIENT_ID"),
        client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    )


# @lru_cache 로 AI 노드·API 서버가 공유하는 싱글턴 세션을 제공
# -> from core_backend.amadeus_client import get_client 로 두 앱에서 동일 코드 재사용
