# alert_api.py
from kakao_msg import send_friend_template

WELCOME_TMPL_ID  = "121168"
SCHEDULE_TMPL_ID = "121173"
PRICE_TMPL_ID    = "121171"

# 이메일 → UUID 매핑 (하드코딩)
EMAIL_UUID = {
    "user1@example.com": "R39Of0l5SX9OYlNlXWpdbldnS3pIfUtzR3UC"
}

def _uuid(email: str) -> str:
    if email not in EMAIL_UUID:
        raise ValueError("Unknown email")
    return EMAIL_UUID[email]

def send_welcome(email: str, auth_code_if_needed: str | None = None):
    return send_friend_template(_uuid(email), WELCOME_TMPL_ID, {}, auth_code_if_needed)

def send_schedule(email: str, arg_dict: dict, auth_code_if_needed: str | None = None):
    return send_friend_template(_uuid(email), SCHEDULE_TMPL_ID, arg_dict, auth_code_if_needed)

def send_price_alert(email: str, arg_dict: dict, auth_code_if_needed: str | None = None):
    return send_friend_template(_uuid(email), PRICE_TMPL_ID, arg_dict, auth_code_if_needed)
