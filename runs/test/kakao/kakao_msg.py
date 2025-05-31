import json, requests
from global_token import ensure_access_token
from user_data     import EMAIL_UUID

KAPI = "https://kapi.kakao.com"

def send_friend_template(email: str, template_id: str, args: dict) -> dict:
    if email not in EMAIL_UUID:
        raise ValueError(f"unknown email={email}")
    uuid = EMAIL_UUID[email]

    access = ensure_access_token()
    headers = {
        "Authorization": f"Bearer {access}",
        "Content-Type":  "application/x-www-form-urlencoded;charset=utf-8"
    }
    data = {
        "receiver_uuids": json.dumps([uuid]),
        "template_id":    template_id
    }
    if args:
        data["template_args"] = json.dumps(args, ensure_ascii=False)

    r = requests.post(f"{KAPI}/v1/api/talk/friends/message/send",
                      headers=headers, data=data, timeout=10)
    r.raise_for_status()
    return r.json()
