# global_token.py
import time, requests

KAUTH = "https://kauth.kakao.com/oauth/token"
CLIENT_ID     = "b4a89fae7185745b6e0ff46dc4c60a7b"
CLIENT_SECRET = "HvXeqHCmZjgOBl2015RvxGDgcbbsV0cb"
REDIRECT_URI  = "http://localhost:4000/dummy"   # 실제 등록된 URI

# 메모리 전역 토큰 (앱 시작 시 try_load() 로 초기화)
TOKEN = {
    "access_token":  None,
    "refresh_token": None,
    "expires_at":    0
}

# ---- 파일 또는 DB 에 영구 저장하고 싶으면 아래 두 함수 구현만 교체 ----
import json, os
_STORE = "kakao_global_token.json"

def try_load():
    if os.path.exists(_STORE):
        TOKEN.update(json.load(open(_STORE, encoding="utf-8")))

def save():
    json.dump(TOKEN, open(_STORE, "w", encoding="utf-8"))

# ------------------------------------------------------------------------

def _need_refresh() -> bool:
    """토큰이 없거나 30초 안에 만료되면 True"""
    return not TOKEN["access_token"] or TOKEN["expires_at"] < time.time() + 30

def _refresh_with_refresh_token():
    """refresh_token으로 access_token 재발급"""
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
    if j.get("refresh_token"):
        TOKEN["refresh_token"] = j["refresh_token"]
    save()

def _issue_with_authorization_code(auth_code: str):
    """최초/만료 시 authorization_code 로 새 토큰 발급"""
    data = {
        "grant_type":    "authorization_code",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "code":          auth_code
    }
    r = requests.post(KAUTH, data=data, timeout=10)
    r.raise_for_status()
    j = r.json()
    TOKEN.update({
        "access_token":  j["access_token"],
        "refresh_token": j["refresh_token"],
        "expires_at":    time.time() + j["expires_in"]
    })
    save()

def ensure_access_token(auth_code_if_needed: str | None = None) -> str:
    """
    1) access_token 이 유효하면 그대로 반환
    2) 만료됐으면 refresh_token 재발급
    3) refresh_token 도 없으면 auth_code 로 신규 발급
    """
    if _need_refresh():
        if TOKEN["refresh_token"]:
            _refresh_with_refresh_token()
        elif auth_code_if_needed:
            _issue_with_authorization_code(auth_code_if_needed)
        else:
            raise RuntimeError("No valid token. Provide Kakao auth_code.")
    return TOKEN["access_token"]
