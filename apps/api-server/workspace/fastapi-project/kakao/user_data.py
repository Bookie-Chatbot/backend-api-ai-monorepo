import os, time
from dotenv import load_dotenv

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
