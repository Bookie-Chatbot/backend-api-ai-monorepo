SCHEDULE_ARGS = {
    "ORIGIN": "서울", "DEST": "제주", "AIRLINE": "KAL",
    "DEPARTDATE": "2025.06.01",
    "TARGET_PRICE": "120000", "CURRENT_PRICE": "118500",
    "CHANGE_RATE": "-1.25", "BOOK_URL": "https://bookie-chatbot.vercel.app/flights?src=sel&dst=cju"
}
PRICE_ARGS = {
    "ORIGIN": "서울", "DEST": "제주", "AIRLINE": "KAL",
    "DEPARTDATE": "2025.06.01",
    "TARGET_PRICE": "120000",
    "BOOK_URL": "https://bookie-chatbot.vercel.app/flights?src=sel&dst=cju"
}
# url은 일단 가상

## 카카오 템플릿
"""
1. 주기적 스케줄링 알림 템픞릿
🦉 현재 가격을 전해드려요!
✈️ ${ORIGIN} → ${DEST} | ${DEPARTDATE}
🎯 목표: ${TARGET_PRICE}원
💸 현재: ${CURRENT_PRICE}원 ( ${CHANGE_RATE}%)

부키로 이동하기 버튼


2. 가격 임계치 알림 템플릿
🦉 가격 임계치 도달!
✈️ ${AIRLINE} | ${DEPARTDATE}
 🎉 ${ORIGIN} → ${DEST} 항공권 가격이  ${TARGET_PRICE}원 이하로 내려왔어요!

 예약 바로가기 버튼 ${BOOK_URL}

"""