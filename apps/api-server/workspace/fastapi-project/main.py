from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import user, hotel, flight, reservation, admin_settings
from routers import user_router, hotel_router, flight_router, reservation_router
import logging

app = FastAPI()

origins = [
    "http://localhost:5173",      # Vite dev server
    "http://127.0.0.1:5173",      # sometimes your browser uses 127.0.0.1
]

# 2) Add the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # <-- your front-end origin(s)
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

# 데이터베이스 초기화
# Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(user_router)
app.include_router(hotel_router)
app.include_router(flight_router)
app.include_router(reservation_router)

@app.get("/")
def read_root():
    return {"message": "FastAPI 프로젝트 성공!"}