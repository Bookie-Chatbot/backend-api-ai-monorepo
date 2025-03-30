import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일의 환경변수 로드

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VIRTUAL_DB_DIR = os.getenv("VIRTUAL_DB_DIR", "src/data/db")

# 가상 DB JSON 파일들이 있는 디렉토리 경로
VIRTUAL_DB_DIR = os.path.join("data", "db")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

