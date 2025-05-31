# kakao_msg.py
import json, requests
from global_token import ensure_access_token

KAPI = "https://kapi.kakao.com"

def send_friend_template(uuid: str, template_id: str, args: dict,
                         auth_code_if_needed: str | None = None) -> dict:
    access = ensure_access_token(auth_code_if_needed)
    headers = {
        "Authorization": f"Bearer {access}",
        "Content-Type":  "application/x-www-form-urlencoded;charset=utf-8"
    }
    data = {
        "receiver_uuids": json.dumps([uuid], ensure_ascii=False),
        "template_id":    template_id
    }
    if args:
        data["template_args"] = json.dumps(args, ensure_ascii=False)

    r = requests.post(f"{KAPI}/v1/api/talk/friends/message/send",
                      headers=headers, data=data, timeout=10)
    return r.json()
