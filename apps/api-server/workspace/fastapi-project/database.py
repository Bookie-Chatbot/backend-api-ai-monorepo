from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"[DEBUG] DATABASE_URL: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)
print(f"[DEBUG] engine: {engine}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print(f"[DEBUG] SessionLocal: {SessionLocal}")

Base = declarative_base()
print(f"[DEBUG] Base: {Base}")