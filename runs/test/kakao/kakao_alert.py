# test_alert.py
import alert_api as api, time, sys, json, global_token as gt

gt.try_load()                    # 디스크에 저장돼 있던 토큰 로드

email  = sys.argv[1]
which  = sys.argv[2]

# 최초 실행이라 토큰이 없으면 auth_code 인자를 넣어주세요.
auth_code = None   # 예: "KakaoRedirect에서받은code"  (1회만 필요)

SCHEDULE_ARGS = {
    "ORIGIN":"서울","DEST":"제주","AIRLINE":"KAL","DEPARTDATE":"2025.06.01",
    "TARGET_PRICE":"120000","CURRENT_PRICE":"118500",
    "CHANGE_RATE":"-1.25","BOOK_URL":"https://bookie-chatbot.vercel.app/flights?src=sel&dst=cju"
}
PRICE_ARGS = {
    "ORIGIN":"서울","DEST":"제주","AIRLINE":"KAL","DEPARTDATE":"2025.06.01",
    "TARGET_PRICE":"120000",
    "BOOK_URL":"https://bookie-chatbot.vercel.app/flights?src=sel&dst=cju"
}

if which == "welcome":
    print(api.send_welcome(email, auth_code))
elif which == "schedule":
    print(api.send_schedule(email, SCHEDULE_ARGS, auth_code))
elif which == "price":
    print(api.send_price_alert(email, PRICE_ARGS, auth_code))
else:
    print("unknown command")
