# backend-api-ai-monorepo

<p align="center">
  <img src="https://github.com/user-attachments/assets/99a1dcbf-05ec-4ab3-99f9-45abed127f45" width="400" height="300"/>
</p>

**backend-api-ai-monorepo** 는 기존 **backend-api**(FastAPI)와 **backend-ai**(LangChain/LangGraph) 두 저장소를 `git-filter-repo`로 병합한 단일 모노레포입니다.

API 서버는 MySQL CRUD·Amadeus 항공 검색을 제공하고, AI 서비스는 LangGraph/LangChain 파이프라인으로 가격 추적·날씨 요약·추천·정책 QA 등을 처리합니다.

공용 패키지(`packages/core-backend`)에는 도메인 모델, Amadeus·OpenWeather(MCP) 클라이언트, 알림 템플릿이 포함돼 있어 **하나의 레포만으로 개발-테스트-배포**가 가능합니다.

### 주요 구성 기능
<p align="center">
  <img src="https://github.com/user-attachments/assets/330f8a30-6691-43c9-a97d-4c3bf6ed0f00"/>
</p>

### 실행 예시
<p align="center">
  <img src="https://github.com/user-attachments/assets/f086da4d-20f2-4434-a6b6-bd28d9a8122d"/>
</p>




## 0. 아키텍처 구성
### High Level 아키텍처
![image](https://github.com/user-attachments/assets/85a5c331-b636-4689-a88e-467687f9516c)


### 기본 상세 아키텍처
![image](https://github.com/user-attachments/assets/4e3be0f4-77bb-4314-bde8-fe19d19d1ffd)

### intent 기반 아키텍처
![image](https://github.com/user-attachments/assets/fe02a6d0-486f-4677-ae3b-2a2c04576526)


## 1. 레이어 구성

| 레이어 | 기술 스택 | 핵심 기능 |
| --- | --- | --- |
| **API Server**<br>`apps/api-server` | FastAPI · SQLAlchemy · MySQL · Amadeus SDK | 사용자·호텔·항공 CRUD, JWT 인증, Amadeus 최저가 조회, Alert Webhook, 도메인 모델 |
| **AI Service**<br>`apps/ai-service` | LangGraph · OpenAI API · ChromaDB | 7개 RAG 파이프라인<br>· Flight Price Tracker<br>· Weather Summariser (MCP 연동)<br>· Destination Recommender (MCP 캐시 활용)<br>· Hotel Finder<br>· Air-Policy QA<br>· Redirect Service<br>· Alert Dispatcher(카카오·이메일) |
| **Core 패키지**<br>`packages/core-backend` | Pydantic · 공용 유틸 | Amadeus 래퍼, MCP(OpenWeather) 클라이언트, 캐시 관련, 알림 템플릿 |

# A. 프로젝트 구조
**디렉토리 구조**
아래는 실제 디렉터리 구조를 반영한 backend-api-ai-monorepo/의 구조입니다.
```
backend-api-ai-monorepo/
```text
.
├── apps/                            # 독립 실행 서비스 모음
│   ├── ai_preprocess/               # · 전처리용 모듈 
│   ├── ai_service/                  # · 전처리된 데이터로 실제 RAG 서비스 (챗봇 응답 생성) 수행
│   ├── amadeus_mcp_server/          # · Amadeus API를 MCP(SSE)로 노출하는 Node.js 서버
│   └── api-server/                  # · 챗봇 클라이언트용 메인 FastAPI REST 서버
├── bookie.egg-info/                 # Python 패키지 배포 메타데이터
├── cache/                           # · HuggingFace·OpenAI 모델 캐시 저장소
├── db_FAISS/                        # · 벡터 검색용 FAISS 인덱스 파일(index.faiss, index.pkl)
├── launch_api.py                    # · 전체 서버(FastAPI + MCP) 실행·모니터링 진입 스크립트
├── packages/                        # · 사내 공통 모듈
│   ├── chatbot_contents/            #   – Intent별 응답 핸들러 & Pydantic 스키마
│   └── core_backend/                #   – Amadeus 클라이언트 래퍼, 유틸리티
├── requirements.txt                 # · Python 종속성 목록
├── root_data/                       # · 원본 참조 데이터(e.g. koreanair.pdf)
├── runs/                            # · 테스트·실험 스크립트 모음(main.py, mcp_client.py 등)
├── setup.py                         # · 패키지 설치용 설정 파일
└── tmp/                             # · 임시 결과물(dest_reco_*.html 등)


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


아래 예시는 `README.md`에 추가할 수 있는 두 가지 주요 섹션입니다. 첫 번째는 `setup.py` + `pip install -e .`을 이용한 설치 및 CLI 실행 간소화 방법이고, 두 번째는 `runs/test` 폴더에 새로 추가된 테스트 스크립트들에 대한 간단한 설명입니다.

---

## 🚀 설치 및 실행 (Setup & CLI)

```bash
# 1. 프로젝트 루트에서 개발 모드로 설치
pip install -e . (requirments.txt에 있으므로 별도 설치 불필요)

# 2. entry point로 제공되는 명령어 예시
#    - MCP 서버·클라이언트·테스트
mcp-server      # MCP 서버 기동
mcp-client      # MCP 클라이언트 호출
mcp-test        # 통합 테스트 스크립트 실행

#    - 전처리 및 챗봇 서비스
preprocess      # PDF → FAISS, 혹은 기존 FAISS에 추가
bookie-chat     # 대화형 AI 서비스 실행

#    - FastAPI 서버 (Uvicorn wrapper)
api-server      # uvicorn으로 FastAPI 앱 기동
```
 
### ⚙️ `setup.py` 구성 및 사용법

프로젝트를 쉽고 간편하게 설치·실행하기 위해 `setup.py`에 다음과 같은 설정을 해두었습니다:


#### 주요 항목 설명

* **`packages` 및 `package_dir`**

  * `find_packages(where=".")`로 최상위 패키지 전부를 자동으로 수집합니다.
  * 추가로 “싱글 파일 모듈”(`launch_api.py`)과, 앱별 디렉터리 위치를 `package_dir`로 1:1 매핑하여 패키지로 인식되도록 설정합니다.
     ```
        "": ".",
        "mcp":                  "apps/ai_preprocess/src/mcp",
        "app_preprocess":       "apps/ai_preprocess/src/app",
        "service":              "apps/ai_service/src",
        "app_service":          "apps/ai_service/src/app",
        "app_service.service":  "apps/ai_service/src/app/service",
        "api_server":           "apps/api-server/workspace/fastapi-project",
        "api_server.routers":   "apps/api-server/workspace/fastapi-project/routers",
        "core_backend":         "packages/core_backend",
    ```

* **`py_modules`**

  * 패키지로 묶이지 않는 단일 모듈(`launch_api.py`)을 포함시켜, CLI 엔트리포인트에서 사용할 수 있게 합니다.

* **`entry_points.console_scripts`**

  * 설치 후 패스(Path)에 자동 등록되는 실행 명령어를 정의합니다.
  * 예) `preprocess`, `bookie-chat`, `api-server` 등을 터미널에서 바로 호출할 수 있습니다.



---

위 내용을 `README.md`에 복사·붙여넣기하시면, 사용자와 개발자가 설치부터 실행, 테스트까지 보다 직관적으로 따라올 수 있습니다.


  

## 🧪 테스트 스크립트 (runs/test)

`runs/test` 디렉터리안에 다음과 같은 스크립트를 배치해 두었습니다. 모두 `mcp-test`, `preprocess`, `bookie-chat` 등의 entry point로 쉽게 실행할 수 있습니다.

| 파일명           | 설명                                                         |
| ---------------- | ------------------------------------------------------------ |
| **imports.py**   | - **`setup.py`에 정의된 `console_scripts` 엔트리포인트**가 잘 작동하는지 테스트<br>- `data`, `app_service.virtual_db`, `core_backend.amadeus_client` 등 주요 모듈 임포트 경로 확인 |
| **mcp.py**       | - MCP 서버(백그라운드) 기동/종료<br>- `langchain_mcp_adapters`를 통한 QA 에이전트 테스트<br>- `mcp-server`/`mcp-client` CLI 명령어 구현 |
| **policy.py**    | - FAISS 기반 PDF RAG 체인 테스트 스크립트<br>- `--db-path` 옵션 지원, 인터랙티브 Q&A 루프<br>- `policy` 전용 entry point (`mcp-test`로 묶어서 실행) |
| **preprocess.py**| - PDF 파일 → FAISS 벡터 스토어 생성 및 추가 기능 테스트<br>- `--mode=create|add` 옵션 지원<br>- 전처리 워크플로우 검증용 스크립트 |

```bash
# 예시: imports.py를 직접 실행해 console_scripts 설치 확인
imports          # setup.py에 정의된 console_scripts 중 하나가 정상 동작하는지 테스트

# 예시: 전처리 스크립트 실행
preprocess sample.pdf --mode create

# 예시: MCP 통합 테스트
mcp-test
```

    

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

