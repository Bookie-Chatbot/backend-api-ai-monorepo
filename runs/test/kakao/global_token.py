import time, json, os, requests
from dotenv import load_dotenv
from user_data import TOKEN

load_dotenv()

KAUTH = "https://kauth.kakao.com/oauth/token"
CLIENT_ID     = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

_STORE = "kakao_global_token.json"

# ──────────────────────────────────────────────
def try_load():
    """앱 시작 시 디스크에 저장된 토큰 불러오기"""
    if os.path.exists(_STORE):
        TOKEN.update(json.load(open(_STORE, encoding="utf-8")))

def save():
    """토큰 정보 영구 저장"""
    json.dump(TOKEN, open(_STORE, "w", encoding="utf-8"), ensure_ascii=False)

# ──────────────────────────────────────────────
def _need_refresh() -> bool:
    """access_token이 없거나 곧 만료(True)"""
    return (not TOKEN["access_token"]) or TOKEN["expires_at"] < time.time() + 30

def _refresh_with_refresh_token():
    data = {
        "grant_type":    "refresh_token",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": TOKEN["refresh_token"]
    }
    r = requests.post(KAUTH, data=data, timeout=10)
    r.raise_for_status()
    j = r.json()
    TOKEN["access_token"] = j["access_token"]
    TOKEN["expires_at"]   = time.time() + j["expires_in"]
    if j.get("refresh_token"):                       # 새 refresh_token이 오면 교체
        TOKEN["refresh_token"] = j["refresh_token"]
    save()

def ensure_access_token() -> str:
    """
    항상 최신 access_token 반환.
    refresh_token이 있으면 자동 재발급.
    """
    try_load()
    if _need_refresh():
        if not TOKEN["refresh_token"]:
            raise RuntimeError("refresh_token not set")
        _refresh_with_refresh_token()
    return TOKEN["access_token"]
