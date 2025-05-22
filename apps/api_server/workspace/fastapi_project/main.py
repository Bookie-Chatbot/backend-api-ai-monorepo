from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal, Base
from models import user, hotel, flight, reservation, admin_settings, chat_log
from routers import user_router, hotel_router, flight_router, reservation_router, chat_log, price_track
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:5173",      # Vite dev server
    "http://127.0.0.1:5173",      # sometimes your browser uses 127.0.0.1
]

# 2) Add the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # <-- your front-end origin(s)
    allow_credentials=True,
    allow_methods=["*"],         # <-- allow all HTTP methods
    allow_headers=["*"],         # <-- allow all headers
)

@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("✔︎ DB 초기화 성공")
    except Exception as e:
        logging.error(f"❌ DB 초기화 실패 (계속 진행): {e}")
     # 2) 세션 열기
    db = SessionLocal()
    try:
        # 3) 원하는 쿼리 실행
        users = db.query(user.User).all()


        # 4) 콘솔에 출력
        print("▶️ 현재 DB에 저장된 User 레코드들:")
        for u in users:
            print(f"  - id={u.id}, name={u.name}, email={u.email}")


        # 챗 로그 불러오기 테스트
        session_id = "wldls317@naver.com"
        print(f"▶️ 세션 ID: {session_id}에 대한 로그:")
        logs = db.query(chat_log.ChatLog)\
                 .filter(chat_log.ChatLog.session_id == session_id)\
                 .order_by(chat_log.ChatLog.timestamp.asc())\
                 .all()
        for log in logs:
            print(f" 프린트 {log.timestamp}: {log.message} (role: {log.role})")
    except Exception as e:
        logging.error(f"DB 조회 중 에러: {e}")
    finally:
        # 5) 세션 닫기
        db.close()

# 데이터베이스 초기화
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(user_router)
app.include_router(hotel_router)
app.include_router(flight_router)
app.include_router(reservation_router)
app.include_router(chat_log.router)
app.include_router(price_track.router)

@app.get("/")
def read_root():
    return {"message": "FastAPI 프로젝트 성공!"}