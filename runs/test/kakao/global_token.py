"""
global_token.py ― Kakao access / refresh 토큰 핸들러

✔ 토큰 캐시(`kakao_global_token.json`)에 현재 앱의 client_id 를 함께 저장한다.
✔ 항상 .env 의 최신 값(REFRESH_TOKEN · CLIENT_ID 등)을 우선 적용한다.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Final

import requests
from dotenv import load_dotenv

# ──────────────────────────────────────────── 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ──────────────────────────────────────────── .env 헬퍼

def _reload_env() -> None:
    """항상 override=True 로 .env 재로딩"""
    load_dotenv(override=True)

_reload_env()

# ──────────────────────────────────────────── 상수 및 동적 ENV 읽기 함수
KAUTH: Final[str] = "https://kauth.kakao.com/oauth/token"

def _client_id() -> str | None:
    _reload_env()
    return os.getenv("CLIENT_ID")

def _client_secret() -> str | None:
    _reload_env()
    return os.getenv("CLIENT_SECRET")

def _env_refresh_token() -> str | None:
    _reload_env()
    return os.getenv("REFRESH_TOKEN")

# 캐시 파일
_STORE: Final[str] = "kakao_global_token.json"
APP_ID_KEY: Final[str] = "client_id"

# 메모리 상 TOKEN 기본값
TOKEN: dict[str, str | float] = {
    "access_token":  "",
    "refresh_token": _env_refresh_token() or "",
    "expires_at":    0.0,
    APP_ID_KEY:       _client_id(),
}

# ──────────────────────────────────────────── 내부 유틸

def _save() -> None:
    with open(_STORE, "w", encoding="utf-8") as f:
        json.dump(TOKEN, f, ensure_ascii=False)

def _delete_cache() -> None:
    if os.path.exists(_STORE):
        os.remove(_STORE)
        logging.info("[global_token] 캐시 파일 삭제")

def _load() -> None:
    """디스크 캐시→메모리 복원 + ENV 값 반영"""
    _reload_env()

    if os.path.exists(_STORE):
        TOKEN.update(json.load(open(_STORE, encoding="utf-8")))

    # 앱 ID 변경 감지
    if TOKEN.get(APP_ID_KEY) != _client_id():
        logging.warning("[global_token] client_id 변경 – 캐시 초기화")
        _delete_cache()
        TOKEN.update({
            "access_token": "",
            "refresh_token": _env_refresh_token() or "",
            "expires_at": 0.0,
            APP_ID_KEY: _client_id(),
        })

    # ENV의 REFRESH_TOKEN 우선 사용
    env_refresh = _env_refresh_token()
    if env_refresh and env_refresh != TOKEN.get("refresh_token"):
        logging.info("[global_token] ENV refresh_token 으로 업데이트")
        TOKEN.update({
            "refresh_token": env_refresh,
            "access_token":  "",
            "expires_at":    0.0,
        })
        _save()

def _need_refresh() -> bool:
    return (not TOKEN["access_token"]) or TOKEN["expires_at"] < time.time() + 30

def _refresh_with_refresh_token() -> None:
    """refresh_token으로 access_token 재발급"""
    masked = f"{TOKEN['refresh_token'][:6]}…{TOKEN['refresh_token'][-4:]}"
    logging.debug("[global_token] try refresh with token=%s", masked)

    data = {
        "grant_type":    "refresh_token",
        "client_id":     _client_id(),
        "client_secret": _client_secret(),
        "refresh_token": TOKEN["refresh_token"],
    }
    r = requests.post(KAUTH, data=data, timeout=10)

    logging.debug("[global_token] refresh status=%s body=%s", r.status_code, r.text)

    if r.status_code in (400, 401):
        _delete_cache()
        raise RuntimeError("refresh_token invalid or expired")

    r.raise_for_status()
    j = r.json()

    TOKEN["access_token"] = j["access_token"]
    TOKEN["expires_at"]   = time.time() + j["expires_in"]

    if j.get("refresh_token"):
        TOKEN["refresh_token"] = j["refresh_token"]

    _save()

def ensure_access_token(retry: int = 1) -> str:
    """
    유효한 access_token 반환.
    오류 발생 시 캐시 삭제 후 최대 1회 재시도.
    """
    _load()
    try:
        if _need_refresh():
            if not TOKEN["refresh_token"]:
                raise RuntimeError("refresh_token not set")
            _refresh_with_refresh_token()
        return TOKEN["access_token"]
    except Exception as exc:
        if retry > 0:
            logging.warning("[global_token] 재발급 실패 – 캐시 삭제 후 재시도")
            _delete_cache()
            return ensure_access_token(retry - 1)
        raise exc

# 편의를 위해 토큰 캐시 수동 삭제 함수 export
def reset_cache() -> None:
    """외부에서 호출해 캐시 파일을 지울 수 있다"""
    _delete_cache()

# ──────────────────────────────────────────── 디버그 실행
if __name__ == "__main__":
    print("access_token =", ensure_access_token()[:15] + "…")
