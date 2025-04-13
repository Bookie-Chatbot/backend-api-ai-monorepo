# FastAPI 프로젝트 - 챗봇 기반 호텔/항공 서비스 예약 관리 시스템

## 📌 프로젝트 개요
- **주제:** 챗봇을 활용한 호텔 및 항공 서비스 예약 관리 시스템
- **진행 기간:** 2025년 3월 ~ 6월
- **팀 구성:** 총 4명 (백엔드 담당: 나)
- **사용 기술:** FastAPI, SQLAlchemy, Pydantic, MySQL, Uvicorn


## ✅ 프로젝트 구조
```
fastapi-project/
├── env/               (가상환경 폴더)
├── main.py            (FastAPI 서버 메인 파일)
├── database.py        (SQLAlchemy 설정 파일)
├── models/            (DB 모델 정의 폴더)
├── routers/           (API 라우터 정의 폴더)
├── schemas/           (Pydantic 스키마 정의 폴더)
```

## 🚀 설치 및 실행 방법
### 1. 가상환경 설정 및 활성화
```bash
python3 -m venv env
source env/bin/activate  # Windows는 .\env\Scripts\activate
```

### 2. 필요한 패키지 설치
```bash
pip install fastapi sqlalchemy pydantic alembic uvicorn pymysql
```

### 3. FastAPI 서버 실행하기
```bash
uvicorn main:app --reload
```

### 4. API 문서 확인하기 (Swagger UI)
```
http://127.0.0.1:8000/docs
```

## 📂 모델 정의 (`models/`)
- **User 모델:** 사용자 정보 (ID, 이름, 이메일, 비밀번호 등)
- **Hotel 모델:** 호텔 정보 (ID, 이름, 위치, 가격, 방 수 등)
- **Flight 모델:** 항공편 정보 (ID, 항공사, 출발/도착지, 시간, 가격 등)
- **Reservation 모델:** 예약 정보 (사용자, 호텔, 항공 정보와 연결)
- **AdminSettings 모델:** 관리자 설정 정보 (예약 정책, API 업데이트 주기 등)

## 📂 API 라우터 (`routers/`)
### User API
- `POST /users/` - 사용자 생성
- `GET /users/` - 사용자 목록 조회
- `GET /users/{user_id}` - 사용자 단일 조회
- `PUT /users/{user_id}` - 사용자 정보 수정
- `DELETE /users/{user_id}` - 사용자 삭제

### Hotel API
- `POST /hotels/` - 호텔 생성
- `GET /hotels/` - 호텔 목록 조회
- `GET /hotels/{hotel_id}` - 호텔 단일 조회
- `PUT /hotels/{hotel_id}` - 호텔 정보 수정
- `DELETE /hotels/{hotel_id}` - 호텔 삭제

## 📂 데이터베이스 설정 (`database.py`)
- **MySQL** 사용 (`fastapi_project` 데이터베이스)
- SQLAlchemy ORM 설정
- 접속 URL 예시:
  ```
  mysql+pymysql://root@localhost/fastapi_project
  ```

## 📂 API 문서화
- FastAPI의 자동 문서화 기능 사용
- Swagger UI에서 모든 API 확인 가능 (`http://127.0.0.1:8000/docs`)

