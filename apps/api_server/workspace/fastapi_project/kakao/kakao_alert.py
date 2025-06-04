import sys
import json
import alert_api as api
import global_token as gt
from dotenv import load_dotenv
import os

load_dotenv()

# 저장된 토큰을 메모리로 불러오기
gt.try_load()

# .env에 설정한 이메일/UUID 정보
USER_EMAIL = os.getenv("USER_EMAIL")
if not USER_EMAIL:
    print("ERROR: 환경 변수 USER_EMAIL이 설정되어 있지 않습니다.")
    sys.exit(1)



async def main():
    SCHEDULE_ARGS = {
        "ORIGIN": "서울",
        "DEST": "제주",
        "AIRLINE": "KAL",
        "DEPARTDATE": "2025.06.01",
        "TARGET_PRICE": "120000",
        "CURRENT_PRICE": "118500",
        "CHANGE_RATE": "-1.25",
        "BOOK_URL": "https://chatbot-bookie.pages.dev"
    }
    PRICE_ARGS = {
        "ORIGIN": "서울",
        "DEST": "제주",
        "AIRLINE": "KAL",
        "DEPARTDATE": "2025.06.01",
        "TARGET_PRICE": "120000",
        "BOOK_URL": "https://chatbot-bookie.pages.dev"
    }

    while True:
        print("\n=== 카카오 알림 테스트 메뉴 ===")
        print("1) 웰컴 메시지 보내기")
        print("2) 스케줄링 알림 보내기")
        print("3) 가격 임계치 알림 보내기")
        print("Q) 종료")
        choice = input("메뉴 번호를 입력하세요 (1/2/3 또는 Q): ").strip().lower()

        if choice == "q":
            print("프로그램을 종료합니다.")
            return

        try:
            if choice == "1":
                response = api.send_welcome(USER_EMAIL)
                print("\n--- 웰컴 메시지 결과 ---")
                if response.get("successful_receiver_uuids"):
                    print("웰컴 메시지가 성공적으로 전송되었습니다.")
            elif choice == "2":
                response = api.send_schedule(USER_EMAIL, SCHEDULE_ARGS)
                print("\n--- 스케줄링 알림 결과 ---")
                if response.get("successful_receiver_uuids"):
                    print("스케줄링 알림이 성공적으로 전송되었습니다.")
            elif choice == "3":
                response = api.send_price_alert(USER_EMAIL, PRICE_ARGS)
                print("\n--- 가격 임계치 알림 결과 ---")
                if response.get("successful_receiver_uuids"):
                    print("가격 임계치 알림이 성공적으로 전송되었습니다.")
            else:
                print("잘못된 입력입니다. 1, 2, 3 중 하나 또는 Q를 입력해 주세요.")
        except Exception as e:
            print(f"오류 발생: {e}")


if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")