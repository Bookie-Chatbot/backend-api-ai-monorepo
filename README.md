# backend-api-ai-monorepo

<p align="center">
  <img src="https://github.com/user-attachments/assets/99a1dcbf-05ec-4ab3-99f9-45abed127f45" width="400" height="300"/>
</p>

**backend-api-ai-monorepo** 는 **FastAPI API 서버**와 **LangChain/LangGraph AI 서비스**를 하나의 모노레포로 통합한 프로젝트입니다.  
항공 가격 · 날씨 · 정책 · 추천 데이터를 LLM 파이프라인에 연결해 **대화형 원스톱 여행 플래너** 기능을 제공합니다.

---

## 📑 목차 <!-- omit in toc -->
- [1. 서비스 기능 개요](#1-서비스-기능-개요)
- [2. 데모](#2-데모)
- [3. 팀원별 기여 현황](#3-팀원별-기여-현황)
- [4. 구현 기능 관련](#4-구현-기능-관련)
- [5. 아키텍처 구성](#5-아키텍처-구성)
  - [5.1 High Level 아키텍처](#51-high-level-아키텍처)
  - [5.2 기본 상세 아키텍처](#52-기본-상세-아키텍처)
  - [5.3 intent 기반 아키텍처](#53-intent-기반-아키텍처)
- [6. 레이어 구성](#6-레이어-구성)
- [7. 프로젝트 구조](#7-프로젝트-구조)
- [8. 설치 및 실행](#8-설치-및-실행-setup--cli)
- [9. 테스트 스크립트](#9-테스트-스크립트-runstest)
- [10. 브랜치 전략](#10-브랜치-전략)
- [11. Conventional Commits 가이드](#11-conventional-commits-가이드)



---

 ## 1. 서비스 기능 개요

### ✨ 서비스 기능 개요
여행자는 노선·시즌·발권 시점·환불‧수수료 규정 등 수십 개 옵션을 직접 설정해야만 합리적인 결정을 내릴 수 있습니다.  
기존 플랫폼은 이 복잡도를 그대로 노출해 ‘정보만 던져주는 리스트 UI’에 머무르기 때문에 ▲가격 변동 추적 부재 ▲약관 해석 난이도 ▲결정 피로도가 큰 문제가 됩니다.

**backend-api-ai-monorepo**는 이러한 한계를 해결하기 위해 ―  
1. **LLM 기반 Intent Router**로 사용자의 자연어 의도를 구분하고,  
2. **7개의 체인**(가격·추천·날씨·정책·알림 등)으로 기능을 모듈화하며,  
3. **Amadeus·OpenWeather MCP** + **PDF RAG** + **Celery 알림**을 결합해,  
4. 챗(UI) 한 줄 ↔ 추천 → 예약 → 알림까지 **원스톱 UX**를 제공합니다.

아래 표는 각 Intent·체인·UI 컴포넌트가 어떻게 매핑되어 있는지 한눈에 정리한 것입니다.


| 기능 분류 | Intent ID | LangChain / 백엔드 Chain | 외부 API | UI 컴포넌트 |
|-----------|-----------|-------------------------|----------|-------------|
| **요금 조회·추적** | `PRICE_SEARCH` | `price_search_chain` → *Amadeus Flight Offer Search → Cheapest N* | Amadeus MCP · Flight Offer Search | `FlightCardList` |
| **가장 저렴한 가격** | `CHEAPEST_PRICE` | `cheapest_price_chain` → *min(price)* | Amadeus MCP | `BestDealCard` |
| **가격 트래킹** | `PRICE_TRACKING` | Celery + Redis / `price_tracker` | Redis · Celery | `PriceTrendSection` |
| **가격 분석** | `PRICE_ANALYSIS` | `price_analysis_chain` → Metrics 분석 | Amadeus MCP | `InsightBubble` |
| **정책 Q&A** | `POLICY_QA` | `policy_qa_rag_chain` (PDFPlumber → Chroma → Reranker) | PDF Vector | `PolicyAnswerCard` |
| **목적지 추천** | `DEST_RECOMMEND` | ReAct Agent + Google Places | Google Places | `RecoCarousel` |
| **날씨 요약** | `WEATHER_SUMMARY` | `weather_summary_chain` (5-day forecast) | OpenWeather MCP | `WeatherStrip` |
| **알림 문구** | `ALERT_DISPATCH` | `alert_dispatch_chain` → MySQL → Celery → Kakao/Email | – | `AlertModal` |
| **일반 대화** | `GENERAL_CHAT` | `chat_fallback_chain` | – | `ChatBubble` |

> **요약**  
> *한 줄 대화*로 ▲항공권 탐색 ▲가격 알림 ▲날씨 위험 경고 ▲정책 FAQ ▲개인화 추천을 **실시간·능동형**으로 수행하며, 사용자는 복잡한 필터링 없이 “지금 예약할까?” 버튼만 누르면 됩니다.

### ✨ 서비스 차별점
기존 항공권 플랫폼이 *“필터 - 리스트 - 직접 판단”* 방식이라면, **Bookie**는  
**자연어 1문장 → 분석 → 능동 제안** 흐름으로 사용자의 의사결정 피로를 크게 줄입니다.

| 구분 | 기존 서비스 (예: 스카이스캐너/구글플라이트) | Bookie 챗봇 | 사용자가 체감하는 변화 |
|------|-------------------------------------------|--------------|------------------------|
| **예약 인터페이스** | 복잡한 필터·표 형식 | 카드·버튼 중심 챗 UI | 클릭 ↓, 정보 탐색 시간 ↓ |
| **가격 알림 등록** | 버튼 → 이메일만 지원 | “15만원 이하 되면 알려줘” 즉시 등록 | 알림 설정 시간 ↓, 실시간성 ↑ |
| **실시간 대화 대응** | 불가 | 가능 (LLM 7-chain) | 탐색→결정 턴 ↓ |
| **취소·변경 규정** | 약관 PDF 링크 | 200자 요약 + 근거 하이라이트 | 이해도 ↑, 오류 ↓ |
| **가격 트렌드** | 사용자가 직접 조회 | “가격 추이 분석 그래프 제공 | 최적 예약 타이밍 제시 |
| **가격 트래킹* | 없음 | 카톡/메일 자동 발송 | 불필요 수수료 ↓ |

> **핵심**: Bookie는 *정보*를 넘어서 **행동(Action)** 을 유도합니다.  
> 예) 가격 하락 알림 → “지금 예약할까요?” 버튼으로 즉시 전환,  


---

## 2. 데모

### 🎬 Demo Video
[![Demo Video](https://img.youtube.com/vi/m6fngPmND2E/hqdefault.jpg)](https://www.youtube.com/watch?v=m6fngPmND2E "클릭하면 YouTube로 이동")

### 📸 실행 스크린샷
<p align="center">
  <img src="https://github.com/user-attachments/assets/f086da4d-20f2-4434-a6b6-bd28d9a8122d" width="480"/>
  <img src="https://github.com/user-attachments/assets/f701d87a-da6c-4dd3-afa6-15a064cc0df6" width="480"/>
  <img src="https://github.com/user-attachments/assets/781810e4-2e88-4ae6-8ff2-fef9a16e9655" width="480"/>
  <img width="578" alt="결과부키5" src="https://github.com/user-attachments/assets/8a7f5181-64cf-42e7-8f0c-e7ab2487a049" />
</p>



### 🗺️ Demo Flow Walk-through

0. **시작 대화**  
   사용자가 “지금 종강하고 동남아 여행 가고 싶은데 … 말레이시아 여행지 추천해줘”라고 입력하면 **DEST_RECOMMEND** 체인이 작동합니다.

1. **여행지 추천 – *DEST_RECOMMEND* (결과 부키 ①)**  
   *ReAct Agent + Google Places* 가 **쿠알라룸푸르·조지타운**을 카드 형태로 제시합니다 → 사용자는 카드 스와이프로 상세 정보를 확인할 수 있습니다.

2. **날씨 요약 – *WEATHER_SUMMARY* (부키 ②)**  
   “쿠알라룸푸르 날씨 어때?” 질문 → *OpenWeather MCP* 를 호출해 **현재 기온·체감·강수 가능성**을 1문단 요약으로 반환합니다.

3. **가격 추세 분석 – *PRICE_ANALYSIS* (부키 ②-③)**  
   “6월 30일 인천 → KUL 항공권 가격 추이 분석해줘” →  
   *MCP-subchain -> Amadeus MCP + 가격 히스토리 * 로 최소·최대·중간값을 계산, **추세 그래프**와 함께 응답합니다.

4. **최저가 조회 – *CHEAPEST_PRICE* (부키 ③-④)**  
   “그럼 그 날짜에 지금 살 수 있는 가장 싼 항공권 알려줘” →  
   최저가 항공편(₩172,400) 카드 + **‘예약하러 가기 →’** 버튼이 제공됩니다.

5. **외부 리다이렉트 – *REDIRECTING* (부키 ④-⑤)**  
   버튼 클릭 시 **스카이스캐너**로 심리스 딥링크되어, 동일 편명을 이미 필터링한 상태로 바로 이동합니다.

6. **맞춤 가격 재질문 & 알림 등록 – *PRICE_SEARCH → ALERT_DISPATCH* (부키 ④-⑤)**  
   “15만원 이하로 떨어지면 알려줘” →  
   · 프런트에서 **AlertModal** 을 열어 임계값(150,000) 확인  
   · 백엔드가 `alert_dispatch_chain`을 통해 **MySQL 저장 → Celery** 등록  
   · 추후 30초 주기로 가격이 떨어지면 **카카오톡/이메일** 실시간 알림 전송 (부키 ⑤-⑧).

7. **가격 트래킹 결과 – *PRICE_TRACK* (부키 ⑤-⑧)**  
   데모에서는 30초 간격 시뮬레이션으로 가격이 변동될 때마다 알림이 카톡·메일로 누적 발송되는 모습을 확인할 수 있습니다.

8. **정책 FAQ – *POLICY_QA* (부키 ⑤-⑨)**  
   “과자·액체류 기내 반입 가능해?” →  
   · **PDFPlumber → Chroma** 로 벡터화된 항공사 규정에서 근거 + 출처 페이지를 찾아 200자 내외로 답변합니다.  
   · 하단 ‘출처: ㉿항공사 규정 (§5) 개정: 2023-10-01’ 링크로 신뢰도 확보.

---

## 3. 팀원별 기여 현황

| 이름 | 역할 | 핵심 기여 |
|------|------|-----------|
| **이지인** | 팀장 · LLM | · RAG 체인  · Git 관리, 일정/경로 관리 · Intent Router · Pydantic 모델 · `dest_recommend_chain` · Kakao 알림 · Amadeus MCP · Sub-chain 병합 · LLM 평가 · 모노레포 통합 |
| **신승철** | LLM | 정책 PDF 전처리 · Policy Vector DB · Weather MCP · Query Vector DB · Prompt 컨텍스트 보강 |
| **김도의** | 백엔드 | FastAPI REST · Celery + Redis · MySQL ERD · Amadeus API 래퍼 · AWS 배포(HTTPS) |
| **이신행** | 프론트 | React + Vite Chat UI · Intent별 컴포넌트 · 가격 알림/리마인드 UX · API 연동(fetch/axios) · Cloudflare 배포 · 스카이스캐너 딥링크 |

---

## 4. 구현 기능 관련

| 구분 | 기능 | MVP | 구현 | 비고 |
|------|------|-----|------|------|
| A₁ | 실시간 날씨 반영 | ✔︎ | ✔︎ | OpenWeather MCP |
| A₂ | 사용자 맞춤 정보 | ✔︎ | ✔︎ | 컨텍스트 기반 추천 |
| A₃ | 항공권 가격 조회·알림 | ✔︎ | ✔︎ | Amadeus API + Celery |
| A₄ | 여행지 옵션 추천 | ✔︎ | ✔︎ | 예산·날씨·취향 카드 |
| A₅ | 항공 정책 Q&A | ✔︎ | ✔︎ | PDF RAG 요약 |
| A₆ | 예약 딥링크 | ✔︎ | ✔︎ | 스카이스캐너 리다이렉트 |




## 5. 아키텍처 구성
### High Level 아키텍처
![image](https://github.com/user-attachments/assets/85a5c331-b636-4689-a88e-467687f9516c)


### 기본 상세 아키텍처
![image](https://github.com/user-attachments/assets/4e3be0f4-77bb-4314-bde8-fe19d19d1ffd)

### intent 기반 아키텍처
![image](https://github.com/user-attachments/assets/fe02a6d0-486f-4677-ae3b-2a2c04576526)


 ## 6. 레이어 구성

| 레이어 | 기술 스택 | 핵심 기능 |
| --- | --- | --- |
| **API Server**<br>`apps/api-server` | FastAPI · SQLAlchemy · MySQL · Amadeus SDK | 사용자·호텔·항공 CRUD, JWT 인증, Amadeus 최저가 조회, Alert Webhook, 도메인 모델 |
| **AI Service**<br>`apps/ai-service` | LangGraph · OpenAI API · ChromaDB | 7개 RAG 파이프라인<br>· Flight Price Tracker<br>· Weather Summariser (MCP 연동)<br>· Destination Recommender (MCP 캐시 활용)<br>· Hotel Finder<br>· Air-Policy QA<br>· Redirect Service<br>· Alert Dispatcher(카카오·이메일) |
| **Core 패키지**<br>`packages/core-backend` | Pydantic · 공용 유틸 | Amadeus 래퍼, MCP(OpenWeather) 클라이언트, 캐시 관련, 알림 템플릿 |

## 7. 프로젝트 구조    

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

## 8. 설치 및 실행 (Setup & CLI)

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

### 🚀 설치 및 실행 (Setup & CLI)

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



  

 ## 9. 테스트 스크립트 (runs/test)

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

    

## 10. 브랜치 전략

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
          

## 11. Conventional Commits 가이드
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

