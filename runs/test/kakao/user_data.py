# user_data.py
from __future__ import annotations
import os, logging
from dotenv import load_dotenv

# 매번 .env 를 다시 읽어 최신 값 반영
def get_uuid(email: str) -> str:
    load_dotenv(override=True)               # ← 핵심: override 로 재로딩
    uuid = os.getenv("USER_UUID")
    if not uuid:
        raise ValueError("USER_UUID not set")
    logging.debug("[user_data] email=%s → uuid=%s", email, uuid)
    return uuid


load_dotenv()

# 이메일 → 친구 UUID 매핑
EMAIL_UUID = {
    os.getenv("USER_EMAIL"): os.getenv("USER_UUID")
}

# 전역 토큰: access_token 없음, refresh_token만 미리 지정
TOKEN = {
    "access_token":  None,
   "refresh_token": os.getenv("REFRESH_TOKEN"),
    "expires_at":    0                # 만료 시각 0 → 즉시 갱신 시도
}
