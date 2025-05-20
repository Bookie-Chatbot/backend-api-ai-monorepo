# reset_messages.py
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from api_server.models.chat_log import Message      # ORM 모델 경로에 맞게 조정

load_dotenv()  # .env에서 DATABASE_URL 읽기

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

print(">>> Dropping 'messages' table if it exists...")
Message.__table__.drop(bind=engine, checkfirst=True)  # DROP TABLE IF EXISTS :contentReference[oaicite:0]{index=0}
print(">>> 'messages' table dropped.")

print(">>> Creating 'messages' table...")
Message.__table__.create(bind=engine, checkfirst=True)  # CREATE TABLE only if missing :contentReference[oaicite:1]{index=1}
print(">>> 'messages' table created.")
