import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()  # .env 파일을 불러와서 환경변수로 등록

#SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"[DEBUG] DATABASE_URL: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)
print(f"[DEBUG] engine: {engine}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print(f"[DEBUG] SessionLocal: {SessionLocal}")

Base = declarative_base()



def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
