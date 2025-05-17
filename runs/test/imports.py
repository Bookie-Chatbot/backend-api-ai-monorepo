# examples/test_imports.py

# 1) data 디렉터리 내 모듈 테스트
import root_data  # data/__init__.py 또는 data/*.py 가 잘 인식되는지 확인

# 2) ai_preprocess 앱의 virtual_db 모듈 경로 테스트
from app_service.virtual_db import load_virtual_db

# 4) packages/core_backend 모듈 테스트
from core_backend.amadeus_client import get_client

def main():
    print("data 모듈 로드 OK:", root_data)
    print("load_virtual_db 함수 OK:", load_virtual_db)
    print("amadeus_client 모듈 OK:", get_client)

if __name__ == "__main__":
    main()
