from .kakao_msg import send_friend_template

WELCOME_TMPL_ID  = "121168"
SCHEDULE_TMPL_ID = "121664"
PRICE_TMPL_ID    = "121171"

def send_welcome(email: str):
    return send_friend_template(email, WELCOME_TMPL_ID, {})

def send_schedule(email: str, arg_dict: dict):
    return send_friend_template(email, SCHEDULE_TMPL_ID, arg_dict)

def send_price_alert(email: str, arg_dict: dict):
    return send_friend_template(email, PRICE_TMPL_ID, arg_dict)
