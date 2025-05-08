import os
from dotenv import load_dotenv

load_dotenv()

# (1) 이 파일이 있는 디렉터리
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# (2) 기본 가상 DB 위치: ../data/db
DEFAULT_DB_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "db"))

# (3) .env 에 설정된 VIRTUAL_DB_DIR 이 있으면 raw_env 에 담고,
#     절대 경로가 아니면 BASE_DIR 기준으로 절대 경로로 변환
raw_env = os.getenv("VIRTUAL_DB_DIR", "").strip()
if raw_env:
    if os.path.isabs(raw_env):
        VIRTUAL_DB_DIR = raw_env
    else:
        # BASE_DIR/../(raw_env) 와 같이 해석
        VIRTUAL_DB_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", raw_env))
else:
    VIRTUAL_DB_DIR = DEFAULT_DB_DIR

# (4) 나머지 키들
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
MODEL_NAME        = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
