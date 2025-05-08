import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일의 환경변수를 로드

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# .env 파일에 VIRTUAL_DB_DIR이 설정되어 있지 않으면 기본값으로 "data/db"를 사용
VIRTUAL_DB_DIR = os.getenv("VIRTUAL_DB_DIR", os.path.join("data", "db"))
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
