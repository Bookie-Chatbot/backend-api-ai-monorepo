# Backend-ai
Backend service dedicated to RAG chatbot functionalities using Langchain and OpenAI API


---

# 스터디용 : LangChain 기반 호텔·항공 예약 질의 응답 시스템 

호텔 및 항공 예약 관련 질문에 대해 PDF 문서와 가상 데이터베이스(JSON 파일)를 활용하여 적절한 답변을 제공하는 질의 응답 시스템
LangChain 라이브러리를 활용하여 문서 임베딩, 벡터스토어 검색, SQL 기반 가상 DB 조회 등 다양한 모듈을 통합해 사용자 질문에 대해 PDF 기반 정보와 DB 데이터를 병합한 최종 응답을 생성합니다.

## 주요 기능

- **PDF 로드 및 전처리**  
  - PDF 문서(예: *HotelReservations.pdf*)를 로드하고, 텍스트를 적절한 청크로 분할합니다.
  - 분할된 청크를 HuggingFace 임베딩 모델을 사용해 벡터로 변환한 후 FAISS 벡터스토어에 저장합니다.

- **가상 데이터베이스 및 SQL 쿼리 실행**  
  - JSON 파일들로 구성된 가상 DB를 로드하여, 호텔, 항공편, 예약, 사용자 등의 데이터를 제공합니다.
  - 사용자의 질문에 따라 적절한 SQL 쿼리를 실행해 DB 데이터를 조회합니다.

- **질문 분류 및 응답 생성**  
  - 사용자 질문을 분석해 PDF 기반 응답과 SQL 조회 결과 중 어떤 정보를 사용할지 분류합니다.
  - PDF와 SQL 결과를 각각 생성한 후, 이를 통합하여 최종 답변을 제공합니다.

- **모듈화된 체인 구성**  
  - LangChain의 체인(chain) 개념을 이용해 PDF RAG 체인, SQL 결과 요약 체인, 그리고 두 결과를 병합하는 체인을 구성하였습니다.

## 디렉토리 구조

```
└── src
    ├── app
    │   ├── __init__.py
    │   ├── chains.py
    │   ├── config.py
    │   ├── embeddings.py
    │   ├── loaders.py
    │   ├── prompts.py
    │   ├── question_handler.py
    │   ├── retrievers.py
    │   ├── splitters.py
    │   ├── sql_executor.py
    │   ├── sql_queries.py
    │   ├── utils.py
    │   └── virtual_db.py
    ├── data
    │   ├── db
    │   │   ├── admin.json
    │   │   ├── faiss_index
    │   │   ├── flight.json
    │   │   ├── hotel.json
    │   │   ├── querylog.json
    │   │   ├── reservation.json
    │   │   └── user.json
    │   ├── processed
    │   └── raw
    │       └── HotelReservations.pdf
    ├── experiments
    ├── preprocess.py
    ├── requirements.txt
    ├── search.py
    └── tests
        └── test_app.py
```

## 구조 설명 

### src/app 폴더

- **__init__.py**  
  - **역할:** `app` 패키지를 초기화합니다.  
  - **특징:** 다른 모듈에서 상대 경로로 불러올 수 있도록 패키지로 인식시킵니다.

- **chains.py**  
  - **역할:** LangChain을 활용한 체인(chain) 구성 로직을 포함합니다.  
  - **주요 함수:**  
    - `create_rag_chain(retriever, prompt=DEFAULT_PROMPT)`  
      - PDF 문서 기반의 RAG 체인을 생성하여, 문서 컨텍스트와 질문을 바탕으로 답변을 도출합니다.

- **config.py**  
  - **역할:** 환경변수 및 상수 값들을 설정합니다.  
  - **주요 내용:**  
    - `.env` 파일을 통해 `OPENAI_API_KEY`, `VIRTUAL_DB_DIR`, `MODEL_NAME` 등의 설정을 로드합니다.

- **embeddings.py**  
  - **역할:** 문서 임베딩 및 FAISS 벡터스토어 생성을 담당합니다.  
  - **주요 함수:**  
    - `create_vectorstore(splits)`  
      - 분할된 텍스트 청크를 Document 객체로 변환 후 임베딩하여 FAISS 인덱스를 생성하고 저장합니다.  
    - `load_vectorstore()`  
      - 저장된 FAISS 벡터스토어를 디스크에서 불러옵니다.

- **loaders.py**  
  - **역할:** PDF 등 외부 문서를 로드하는 기능을 제공합니다.  
  - **주요 함수:**  
    - `load_pdf(file_path: str)`  
      - 주어진 PDF 파일 경로에서 문서를 읽어 Document 객체 리스트로 반환합니다.

- **prompts.py**  
  - **역할:** 사용자 질문에 대한 분류, SQL 결과 요약, PDF RAG 체인 등을 위한 프롬프트 템플릿과 체인을 정의합니다.  
  - **주요 함수 및 객체:**  
    - `create_prompt()`  
      - DB 스키마 정보를 포함하여 질문을 SQL 또는 PDF로 분류하는 체인을 생성합니다.  
    - `create_sql_summary_prompt()`  
      - SQL 조회 결과와 사용자 질문을 통합해 자연어 요약을 생성하는 체인을 만듭니다.  
    - `DEFAULT_PROMPT`  
      - PDF RAG용 기본 프롬프트 템플릿을 정의합니다.

- **question_handler.py**  
  - **역할:** 사용자 질문을 처리하여 PDF 기반 응답과 가상 DB(SQL) 결과를 결합한 최종 답변을 생성합니다.  
  - **주요 함수:**  
    - `handle_question(question, classification_key, rag_chain, db_data, sql_summary_chain, retriever)`  
      - 질문의 분류 결과에 따라 PDF와 SQL 조회를 수행하고, 두 결과를 병합하는 로직을 실행합니다.  
    - `merge_pdf_and_sql1()`, `merge_pdf_and_sql2()`  
      - PDF와 SQL 응답을 통합하는 방식(간단 병합 또는 LLM 프롬프트 활용)을 제공합니다.

- **retrievers.py**  
  - **역할:** FAISS 벡터스토어에서 상위 k개의 문서를 검색할 retriever를 생성합니다.  
  - **주요 함수:**  
    - `create_retriever(vectorstore, k: int = 3)`

- **splitters.py**  
  - **역할:** 긴 텍스트를 적절한 청크로 분할합니다.  
  - **주요 함수:**  
    - `split_text(text: str, chunk_size: int = 250, chunk_overlap: int = 50)`  
      - `RecursiveCharacterTextSplitter`를 사용해 문서를 재귀적으로 청크로 나눕니다.

- **sql_executor.py**  
  - **역할:** 가상 DB 데이터에서 SQL 쿼리 실행을 흉내 내는(pseudo) 로직을 구현합니다.  
  - **주요 함수:**  
    - `pseudo_execute_sql(query_key, db_data)`  
      - query_key에 따라 DB의 호텔, 항공편, 예약 등의 데이터를 필터링하여 반환합니다.

- **sql_queries.py**  
  - **역할:** 질문 분류에 따른 SQL 쿼리 키 매핑 정보를 제공합니다.  
  - **주요 내용:**  
    - `sql_query_map` 딕셔너리  
      - 예: `"available_rooms": "SHOW_AVAILABLE_ROOMS"`, `"customer_reservation": "SHOW_CUSTOMER_RESERVATION"` 등.

- **utils.py**  
  - **역할:** 보조 유틸리티 함수들을 포함합니다.  
  - **주요 함수:**  
    - `format_docs(documents)`  
      - Document 객체 리스트의 텍스트를 하나의 문자열로 결합합니다.

- **virtual_db.py**  
  - **역할:** JSON 파일들을 로드하여 가상 DB를 구성합니다.  
  - **주요 함수:**  
    - `load_json_file(filename: str)`  
      - 개별 JSON 파일을 읽어 파이썬 객체로 반환합니다.  
    - `load_virtual_db()`  
      - 여러 JSON 파일을 조합하여 가상 DB(Hotel, Flight, Reservation, User 등)를 생성합니다.

---

### src/data 폴더

- **db 폴더**  
  - **역할:** 가상 DB 데이터 파일들이 위치합니다.
  - 도의님이 설계한 스키마 참고하였습니다. 
  - **주요 파일:**  
    - `admin.json`: 시스템 관리자 관련 설정
    - `flight.json`: 항공편 정보
    - `hotel.json`: 호텔 정보 
    - `querylog.json`: 사용자 질의 기록  
    - `reservation.json`: 예약 내역 정보  
    - `user.json`: 사용자 정보  
    - `faiss_index` 폴더: FAISS 벡터스토어 인덱스 파일들이 저장됨

- **processed 폴더**  
  - **역할:** 전처리 후 처리된 데이터를 저장할 디렉토리 

- **raw 폴더**  
  - **역할:** 원본 문서 파일들이 위치합니다.  
  - **주요 파일:**  
    - `HotelReservations.pdf`: 호텔 예약 관련 PDF 문서

---

### 기타 주요 파일

- **experiments 폴더**  
  - **역할:** 다양한 실험적 시도나 프로토타입 코드가 위치하는 디렉토리입니다.
  - 미구현
  
- **preprocess.py**  
  - **역할:** PDF 문서를 로드, 텍스트 청크 분할, 임베딩 생성 및 FAISS 벡터스토어 저장 과정을 실행하는 전처리 파이프라인을 구현합니다.

- **requirements.txt**  
  - **역할:** 프로젝트에 필요한 Python 패키지들의 목록을 제공합니다.  

- **search.py**  
  - **역할:** 전처리된 벡터스토어를 로드하고, retriever와 체인들을 생성하여 사용자 질문을 처리하고 최종 답변을 출력하는 메인 실행 스크립트입니다.

- **tests/test_app.py**  
  - **역할:** 각 모듈에 대한 단위 테스트를 포함합니다.  
  - **주요 테스트 케이스:**  
    - PDF 파일 로딩 테스트  
    - 텍스트 분할 테스트  
    - 가상 DB의 JSON 파일 로드 및 필수 키 검증

---

## 설치 및 실행 방법

1. **Python 및 패키지 설치**  
   - 프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 필요한 패키지를 설치합니다.
     ```bash
     pip install -r src/requirements.txt
     ```

2. **환경변수 설정**  
   - 프로젝트 루트에 `.env` 파일을 생성하고, `OPENAI_API_KEY` 및 `VIRTUAL_DB_DIR` 등 필요한 환경변수를 설정합니다.

3. **벡터스토어 생성 (전처리)**  
   - PDF 문서를 로드하고, 텍스트 청크로 분할 후 FAISS 벡터스토어를 생성하기 위해 다음 스크립트를 실행합니다.
     ```bash
     python src/preprocess.py
     ```

4. **시스템 실행 및 테스트**  
   - PDF 기반 검색, 질문 처리 및 DB 조회를 확인하려면 다음 스크립트를 실행합니다.
     ```bash
     python src/search.py
     ```
   - 유닛 테스트는 아래 명령어로 실행할 수 있습니다.(미완성)
     ```bash
     python -m unittest discover src/tests
     ```

## 실험 결과 및 개선 사항

### 1. SQL Summary Prompt 개선
- **개선 내용:**  
  SQL summary prompt에 [사용자의 원본 질문을 포함]하도록 프롬프트를 강화하여 최종 결과의 명확성과 정확성을 높임
  
- **실험 결과:**  
  - **[User Question 1]** "가장 저렴한 방이 있는지 확인하고 싶어요."  
  - **[Classification Key 1]** `available_rooms`  
  - **최종 응답 예시:**  
    > 죄송하지만, 제가 찾은 문서에는 방의 요금 정보가 포함되어 있지 않습니다. 하지만 가상 DB에서 조회된 결과에 따르면, 현재 Mountain Inn (덴버)이 가장 저렴한 객실로 $180.0에 이용 가능한 객실이 있습니다. 해당 숙소의 공식 웹사이트나 전화로 직접 문의하시면 더 자세한 정보를 얻을 수 있을 것입니다.

### 2. PDF 및 SQL 결과 병합 프롬프트 구체화
- **개선 내용:**  
  [PDF 응답과 SQL 응답을 통합하는 프롬프트를 구체화]하여 중복되거나 모호한 표현을 제거하고, 사용자의 의도에 맞는 구체적 답변을 제공하도록 개선
  
- **실험 결과:**  
  - **[User Question 1]** "가장 저렴한 방이 있는지 확인하고 싶어요."  
  - **[Classification Key 1]** `available_rooms`  
  - **최종 응답 예시:**  
    > 가장 저렴한 객실을 찾고 계신다면, Mountain Inn (덴버)의 객실이 $180.0으로 현재 가장 저렴한 가격입니다. 만약 추가 정보나 예약이 필요하시다면 해당 숙소의 공식 웹사이트나 전화로 문의하시는 것이 좋습니다.

### 3. DB 스키마 필드 정보 포함
- **개선 내용:**  
  [질문 분류 프롬프트에 DB 스키마의 필드 정보를 구체적으로 제공]하여, 특정 사용자(예: user1)의 예약 정보와 같이 구체적인 질의에 대해 정확한 결과를 반환할 수 있도록 개선
  
- **실험 결과:**  
  - **[User Question 3]** "저는 user1인데, 제가 예약한 비행기의 도착 시간을 알고 싶어요."  
  - **초기 분류 결과:** `pdf_only`  
  - **개선 후 분류 결과:** `customer_reservation`  
  - **최종 응답 예시:**  
    > 고객님의 예약 정보를 확인해보니, 도착 시간은 2025년 4월 1일 11:00입니다. 만약 추가적인 정보가 필요하시거나 다른 도움이 필요하시면 언제든지 문의해주시기 바랍니다.


---

