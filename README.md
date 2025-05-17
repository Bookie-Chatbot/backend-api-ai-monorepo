# backend-api-ai-monorepo

**backend-api-ai-monorepo** 는 기존 **backend-api**(FastAPI)와 **backend-ai**(LangChain/LangGraph) 두 저장소를 `git-filter-repo`로 병합한 단일 모노레포입니다.

API 서버는 MySQL CRUD·Amadeus 항공 검색을 제공하고, AI 서비스는 LangGraph/LangChain 파이프라인으로 가격 추적·날씨 요약·추천·정책 QA 등을 처리합니다.

공용 패키지(`packages/core-backend`)에는 도메인 모델, Amadeus·OpenWeather(MCP) 클라이언트, 알림 템플릿이 포함돼 있어 **하나의 레포만으로 개발-테스트-배포**가 가능합니다.

## 1. 레이어 구성

| 레이어 | 기술 스택 | 핵심 기능 |
| --- | --- | --- |
| **API Server**<br>`apps/api-server` | FastAPI · SQLAlchemy · MySQL · Amadeus SDK | 사용자·호텔·항공 CRUD, JWT 인증, Amadeus 최저가 조회, Alert Webhook, 도메인 모델 |
| **AI Service**<br>`apps/ai-service` | LangGraph · OpenAI API · ChromaDB | 7개 RAG 파이프라인<br>· Flight Price Tracker<br>· Weather Summariser (MCP 연동)<br>· Destination Recommender (MCP 캐시 활용)<br>· Hotel Finder<br>· Air-Policy QA<br>· Redirect Service<br>· Alert Dispatcher(카카오·이메일) |
| **Core 패키지**<br>`packages/core-backend` | Pydantic · 공용 유틸 | Amadeus 래퍼, MCP(OpenWeather) 클라이언트, 캐시 관련, 알림 템플릿 |

# A. 프로젝트 구조
**디렉토리 구조**

```
backend-api-ai-monorepo/
├── apps/
│   ├── api-server/          # ⇢ 기존 backend-api
│   ├── ai_preprocess/       # ⇢ 기존 backend-ai
│   └── ai-service/          # ⇢ 기존 backend-ai
├── packages/
│   └── core-backend/
│       ├── amadeus_client.py
│       ├── mcp_client.py
│       ├── alert_templates.py
│       
├── infra/
├── .github/workflows/       # 통합 CI - 미완
├── requirements.txt 
└── pyproject.toml           
-- .env // 깃에 올리지 않을 예정 - 각자 로컬에서 생성해서 토큰 변수 저장하기

```

## **설치 및 실행 방법**

1.  파이썬 가상환경 생성 및 활성화
- 가상환경 생성
    
    ```tsx
    python -m venv env
    ```
    
- 가상환경 활성화
    - Windows
        
        ```tsx
        env\Scripts\activate
        ```
        
    - macOS/Linux
        
        ```tsx
        source env/bin/activate
        ```
        
1. **패키지 설치**
    - 가상환경이 활성화된 상태에서 루트 디렉토리에서, 아래 명령어로 패키지를 한 번에 설치합니다. 
        
        ```
        pip install -r requirements.txt
        
        // 패키지 삭제
        pip uninstall -r requirements.txt -y
        ```
        ```markdown
        fastapi
        sqlalchemy
        pydantic
        alembic
        uvicorn
        pymysql
        python-dotenv
        amadeus

        # --- AI/RAG 쪽 ---
        langchain
        huggingface_hub
        langchain-openai
        pypdf
        numpy==1.26.2
        langsmith
        openai
        langgraph
        python-dateutil

        ```
        
      
2. **환경변수 설정**
    - 프로젝트 루트에 `.env` 파일을 생성하고, `OPENAI_API_KEY` 및 `AMADEUS_CLIENT_ID/AMADEUS_CLIENT_SECRET` 등 필요한 환경변수를 설정합니다.
    
3. **서버**
    - uvicorn 서버 실행
        
        ```
        uvicorn main:app \
        --reload \
        --app-dir apps/api-server/workspace/fastapi-project \
        --host 0.0.0.0 \
        --port 8000
        ```
        - 정상 작동 실행 결과 
        <img width="620" alt="image" src="https://github.com/user-attachments/assets/2396e629-6ccd-4f10-a321-1abc94f0b8be" />

        
    
    
4. **전처리**
    - 전처리 메인 플로우 실행
        
        ```
        python -m apps.ai_service.src.main_preprocess
        ```
        - 정상 작동 실행 결과 
        <img width="606" alt="image" src="https://github.com/user-attachments/assets/4e14f82f-8c75-4b02-8090-e416f8f3b682" />

        
5. **시스템 실행** 
    - 서비스 메인 플로우 실행
        
        ```
        python -m apps.ai_service.src.main_service
        ```
        - 정상 작동 실행 결과
         <img width="593" alt="image" src="https://github.com/user-attachments/assets/5e65bd03-9e5a-43ed-bcf2-e4912cb2f869" />
          <img width="605" alt="image" src="https://github.com/user-attachments/assets/a54ce5c1-0c1a-400e-b2ce-e6cbe7e032aa" />

          주의 : 대부분 요청 params을 알맞게 생성하나, 아직 모든 사용자 질의에 대해 올바른 요청 Params을 생성하지는 않는 것으로 확인됨
           (대략 90프로 정확도 / 응답은 정확도 조금 더 떨어져서 최적화 작업 필요할듯)
          질문 : 인천에서 뉴욕 가는 왕복 항공권 200만원 이하로 2025년 8월 중에 찾아줘 - 성공
          질문 : 인천에서 GERMANY 가는거 100만원 아래꺼 2025년도 6월달것중에 젤 싼걸로 찾아줘 - 성공
          질문: 인천에서 도쿄 편도 5월 15일, 50만원 이하 (요청 파라미터 정확 / but 응답이 부정확)
          
      <img width="528" alt="image" src="https://github.com/user-attachments/assets/08f9ff5c-2cd7-4e05-a7a7-45f9fa71035e" />

      <img width="647" alt="image" src="https://github.com/user-attachments/assets/ce02a4bb-b843-4537-ac62-bda5578aa545" />


## B. 브랜치 전략
모노레포 환경에서 DB, 전처리·Preprocess, LLM 서비스 영역을 독립 개발하면서도 `develop` 브랜치에서 전체 통합 테스트를 수행하고, `main` 브랜치로 배포하는 단순화된 구조입니다.

### 1. 브랜치 개요

module/db, module/preprocess, module/service → 영역별 독립 개발

develop → 전체 통합 테스트

main → 실제 프로덕션 배포

| 브랜치명                   | 역할                                       |
|----------------------------|--------------------------------------------|
| `main`                     | 프로덕션에 배포된 안정된 코드               |
| `develop`                  | 다음 배포를 위한 통합 개발 브랜치            |
| **Module 브랜치**          | 각 영역별 집중 개발                         |
| ├ `module/db`              | DB 스키마·마이그레이션·Core 패키지 개발 전용 |
| ├ `module/preprocess`      | RAG 전처리 파이프라인 개발 전용             |
| └ `module/service`         | LLM 서비스(Price Tracker, QA 등) 개발 전용  |
          

## C. 📦 Conventional Commits 가이드
아래 표를 참고하여, 커밋 메시지 앞에 접두사를 붙여 변경 의도를 명확히 관리할 수 있습니다.

무조건 지켜야하는 것은 아니지만, “무엇을”과 “어떻게” 바꾼 것인지를 기준으로 일관성 있게 커밋들을 관리하는데 도움이 되고자 추가해보았습니다.

| 커밋 종류     | 목적                                                         | 언제 사용할까요?                                                                                      | 예시 커밋 메시지                                                        | 비고                                                                                 |
|--------------|------------------------------------------------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `[feat]`     | 새로운 기능(기능 단위) 추가                                    | - 새로운 API 엔드포인트 추가<br>- DB 스키마·마이그레이션 추가<br>- LLM 모델 파이프라인 통합          | `feat(api): 사용자 프로필 조회 엔드포인트 추가`<br>`feat(llm): streaming 응답 지원` | 기능 단위로 나눠서 작은 단위 커밋 권장                                                  |
| `[fix]`      | 일반 버그 수정                                               | - 잘못된 응답 포맷 처리<br>- SQL 쿼리 오류 해결<br>- 예외 처리 로직 보완                           | `fix(api): token 검증 실패 시 401 반환하도록 수정`<br>`fix(db): foreign key cascade 설정`   | 개발 브랜치에서 발견된 버그에 사용                                                      |
| `[hotfix]`   | 프로덕션 긴급 패치                                           | - 장애를 유발하는 크래시<br>- 치명적 보안 취약점 긴급 수정                                          | `hotfix(api): 로그인 null 포인터 예외 패치`                                 | main/release 브랜치에 바로 머지 후 배포                                                  |
| `[refactor]` | 코드 구조·가독성·중복 제거 (동작 변경 없음)                      | - 서비스·모듈 계층 분리<br>- 반복 로직 함수로 추출<br>- 네임스페이스·패키지 재배치                   | `refactor(api): 유효성 검사 로직을 미들웨어로 추출`                          | 기능·성능 변화 없이 내부 구조만 개선                                                    |
| `[perf]`     | 성능 최적화                                                  | - DB 인덱스 추가로 쿼리 속도 개선<br>- 캐싱 로직 도입<br>- 불필요한 연산 제거                       | `perf(db): orders 테이블에 composite index 추가`<br>`perf(api): response 캐싱 적용`   | 실제 벤치마크 데이터(속도, 메모리) 개선이 보이는 작업에 사용                             |
| `[docs]`     | 문서 작성·수정                                              | - README·설계 문서 업데이트<br>- API 스펙·Swagger 주석 작성<br>- 주석 보강                          | `docs: LLM 파이프라인 구성 흐름 다이어그램 추가`<br>`docs: API 인증 가이드 보강`   | 코드 변경 없이 문서만 바뀔 때                                                        |
| `[style]`    | 코드 포맷팅·세미콜론·공백 등 스타일 수정                      | - 린트 오류 수정<br>- 들여쓰기·라인 길이 맞춤<br>- 파일 헤더 정리                                  | `style: ESLint 규칙에 맞춰 들여쓰기 통일`                                    | 로직·빌드·테스트에는 영향 없는 순수 스타일 변경                                         |
| `[test]`     | 테스트 코드 작성·수정 및 커버리지 개선                         | - 단위/통합/E2E 테스트 추가<br>- 테스트 모의(Mock) 설정<br>- 커버리지 설정 파일 수정               | `test(api): /orders integration 테스트 추가`<br>`test(llm): embedding mock 도입` | 테스트 관련 폴더·파일만 변경될 때                                                   |
| `[build]`    | 빌드·패키징 설정 변경                                         | - Dockerfile 수정<br>- 패키징 스크립트 변경<br>- 버전 태그 자동화 설정                            | `build: Dockerfile 베이스 이미지를 python:3.11-alpine 으로 변경`            | 배포 아티팩트(파일, 바이너리) 생성 로직에 영향                                          |
| `[ci/cd]`    | CI/CD 워크플로우·스크립트 설정 수정                            | - GitHub Actions·Jenkinsfile 추가/수정<br>- 배포 스크립트 변경<br>- 체크리스트 워크플로우 개선       | `ci: PR 린트·테스트 워크플로우 추가`<br>`ci/cd: 모델 재훈련 잡 스케줄링 설정` | 배포 자동화·검증 파이프라인만 변경될 때                                              |
| `[chore]`    | 그 외 운영·관리 작업 (문서·의존성·도구 설정 등)                  | - 의존성 업그레이드<br>- 린트/포매터 설정<br>- GitHub badge 업데이트                              | `chore: requirements.txt 의존성 버전 업그레이드`<br>`chore: Prettier 설정 추가`  | 코드 로직·테스트·빌드·CI에 직접 영향 없는 잡무                                         |
| `[revert]`   | 이전 커밋을 되돌릴 때 사용                                     | - 잘못된 변경 롤백<br>- 의도치 않은 병합 복구                                                   | `revert: feat(api): user-auth 엔드포인트 추가`                             | 되돌릴 커밋 메시지를 뒤에 괄호로 명시                                                    |

---

