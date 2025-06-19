"""
kakao_msg.py ― 친구/나에게 템플릿 메시지 전송 유틸
"""
from __future__ import annotations

import json
import logging
from typing import Final

import requests
from requests import HTTPError
from user_data import get_uuid

from global_token import ensure_access_token
from user_data     import EMAIL_UUID

KAPI: Final = "https://kapi.kakao.com"

def send_friend_template(email: str, template_id: str, args: dict) -> dict:
    # …
    if email not in EMAIL_UUID:
      raise ValueError(f"unknown email={email}")
    uuid: str = get_uuid(email)
    access_token: str = ensure_access_token()

    # ⬇︎ 추가 : 어떤 템플릿을 누구에게 보내는지, access 토큰 앞자리 확인
    logging.debug("[kakao_msg] send template_id=%s to uuid=%s "
                  "(token=%s…)", template_id, uuid,
                  access_token[:10])

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/x-www-form-urlencoded;charset=utf-8",
    }

    data: dict[str, str] = {
        "receiver_uuids": json.dumps([uuid]),
        "template_id":    template_id,
    }
    if args:
        data["template_args"] = json.dumps(args, ensure_ascii=False)

    # ⬇︎ 추가 : 최종 payload 도 찍어 둠
    logging.debug("[kakao_msg] POST /v1/api/talk/friends/message/send "
                  "data=%s", data)

    resp = requests.post(
        f"{KAPI}/v1/api/talk/friends/message/send",
        headers=headers,
        data=data,
        timeout=10,
    )

    try:
        resp.raise_for_status()
    except HTTPError as e:
        # 이미 있던 상세 에러 로그와 함께 HTTP status 추가
        logging.error("[kakao_msg] HTTPError status=%s body=%s",
                      resp.status_code, resp.text)
        raise
    return resp.json()
