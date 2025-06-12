from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv
import warnings

'''
    db = Chroma.from_documents(
        documents=doc, <- type(doc)=List[Document]
        embedding=embedder,
        persist_directory="./chroma_db", <- 문서를 disk에 저장할 때. 영구 저장하려면 persist_directory에 저장 경로 지정
        collection_name="my_db", <- 생성할 collection 이름
        ids=List[str], <- id 리스트

    ) <- document로부터 vector db 생성

    persist_db = Chroma(persist_directory=, embedding_function=, collection_name=) <- 디스크에서 문서 로드
    << 이때 collection_name은 똑같이 써야돼

    db.get(where 등 조건 삽입 가능) <- 저장된 데이터 확인

    db.similarity_search(
        "query",
        filter={"source": "찾기 원하는 해당 space"},
        k=4, <- default가 4

    ) <- query와 유사도 계산. k-nearest

    db.add_documents([docs]) <- 생성된 db에 document 추가
    db.delete(ids=["삭제할id들 str list"])

'''
load_dotenv()

def create_doc_Chroma(split_doc, persist_directory="db_Chroma"):
    # split doc들로 Chroma DB를 생성하는 메소드. 해당 데이터는 persist_directory 폴더에 저장

    DB_PATH = "./chroma_db"
    # embedder = OpenAIEmbeddings(model = "text-embedding-3-small", )
    embedder = HuggingFaceEmbeddings(
        model_name = "intfloat/multilingual-e5-large-instruct",
        # task= "feature-extraction",
        # huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
        # model_kwargs={"device": "cpu"},
    )
    db = Chroma.from_documents(
        split_doc, embedder,
        persist_directory=persist_directory,
        # collection_name="my_db"
    )

    return db

def add_doc_to_Chroma(db: Chroma, new_docs):
    # 만들어져 있는 db에 새 docmunet 추가할 때 사용
    db.add_documents(new_docs)

'''
    warnings.filterwarnings("ignore")

    db = FAISS(
        embedding_function=embedder,
        index=faiss.IndexFlatL2(dim_size), <- embedding의 차원 크기를 미리 계산해 dim_size로 넘겨주기
        docstore=InMemoryDocstore(), <- 사용할 문서 저장소
        index_to_docstore_id={Dict[int, str]}, <- 인덱스에서 문서 저장소 ID로의 매핑

    )

    db = FAISS.from_documents(
        documents=doc,
        embedding=embedder,

    ) <- FAISS 벡터 저장소 생성

    db.add_documents([Document], ids=["new_id"])
    db.delete(ids)

    db.save_local(
        folder_path="저장할 폴더 경로",
        index_name="저장할 인덱스 파일 이름"
    ) <- FAISS 인덱스, store, id mapping을 로컬 disk에 저장
    원래 FAISS가 메모리에만 저장되기 때문에 로켈 disk에 저장하려면 save_local 필수

    loaded_db = FAISS.load_local(
        folder_path="폴더 경로",
        index_name="인덱스 파일 이름",
        embeddings=embedder,
        allow_dangerous_deserialization=False(default)

    ) <- 해당 폴더에 있는 저장된 데이터 로드 가능

    db.merge_from(db2) <- 원래 db 뒤에 db2를 병합. db2에 정보 손실은 없음

'''

warnings.filterwarnings("ignore")
os.environ["HF_HOME"] = "./cache/"
# filterwarnings("module") 실제 운영 환경에서 이게 더 안전

def create_doc_FAISS(split_doc, persist_directory="db_FAISS"):
    # split doc들로 FAISS DB를 생성하는 메소드. persist_directory 폴더에 저장

    # embedder = OpenAIEmbeddings(model = "text-embedding-3-small", )
    embedder = HuggingFaceEmbeddings(
        model_name= "intfloat/multilingual-e5-large-instruct",
    )
    db = FAISS.from_documents(
        split_doc, embedder,
    )
    db.save_local(persist_directory)

    return db

def add_doc_to_FAISS(db: FAISS, new_docs, persist_directory="db_FAISS"):
    # 만들어져 있는 db에 새 docmunet 추가할 때 사용
    db.add_documents(new_docs)
    db.save_local(persist_directory)
<<<<<<< Updated upstream
=======

def delete_ids_FAISS(db: FAISS, ids, persist_directory="db_FAISS"):
    # db에 해당 ids 가진 chunk들 모두 삭제
    db.delete(ids=ids)
    db.save_local(persist_directory)

def add_query(message, persist_directory="db_query"):
    '''
    message로 받은 query를 persist_directory에 저장하는 함수.

    현재는 인자로 user query를 string으로 받으면
    정해진 userID, time, llm answer를 metadata로 저장하고 있습니다.
    추후에 message를 json으로 바꿔서 add_text 함수에 들어가는 내용, metadata들을 바꿀 수 있습니다.

    Args :
        message (str) :
            user query에 대한 문자열.
        persist_directory (str) :
            path to query vector DB

    '''
    db=FAISS.load_local(persist_directory, config.Embedding_Model, allow_dangerous_deserialization=True)

    # FAISS 저장 시에 각 query마다 고유값으로 붙는 ids라는 arg가 따로 있습니다.
    # user id와는 다른 argument이니 조심해야 합니다
    db.add_texts([message], 
                 metadatas=[{"userID": 8462,
                             "time": 20250602150030,
                             "answer": "노르웨이, 스웨덴, 핀란드가 있습니다."}])

    db.save_local(persist_directory)

def find_similar_history(message, persist_directory="db_query"):
    '''
    persist_directory의 vector DB에서 message로 받은 query에 대해 해당 query와
    유사도가 제일 큰 k개의 document를 반환. filter로 원하는 userID를 골라서 추출 가능
    반환시 최신 내용부터 출력되도록 sort

    마찬가지로 인자로 user query에 대한 문자열을 받고 있으나 추후 json으로 받고
    거기에서 user query만 따로 추출해서 message 부분에 넣어도 무관합니다.

    Args :
        message (str) :
            user query에 대한 문자열.
        persist_directory (str) :
            path to query vector DB
    
    Hyperparameter :
        k (int) :
            유사도 측정할 때 최대 몇 개의 document를 반환할지 정의            
            
    Return :
        sim (List[Document]) :
            message와의 유사도가 제일 큰 k개의 user History에 대한 list.

    '''
    db=FAISS.load_local(persist_directory, config.Embedding_Model, allow_dangerous_deserialization=True)

    sim = db.similarity_search(message, k=3, filter={"userID": 8462})

    sim.sort(key=lambda x: -x.metadata["time"])

    return sim

def initialize_FAISS(persist_directory):
    '''
    persist_dirctory에 있는 FAISS DB 초기화.
    내부 데이터 전부 삭제. 주의해서 사용
    
    Args :
        persist_directory (str) :
            초기화 할 vector DB file path

    '''
    db=FAISS.load_local(persist_directory, config.Embedding_Model, allow_dangerous_deserialization=True)
    db.delete(db.index_to_docstore_id.values())
    db.save_local(persist_directory)

if __name__=="__main__" :
    db=FAISS.load_local("db_query", config.Embedding_Model, allow_dangerous_deserialization=True)
    print(len(db.index_to_docstore_id))
    # add_query("서유럽 가기 좋은 나라 추천")
    # add_query("서유럽 가는 가장 싼 항공편 알려줘")
    # add_query("열대지방에서 제일 맛있는 과일 추천해줘")
    # sim = db.similarity_search("디저트로 먹을게 뭐가 있을까",
    #                      k=2, filter={"userID": 8462})
    
    # print(type(sim))
    # print(sim)
    
    # print(db.index_to_docstore_id)
    # print(list(db.index_to_docstore_id.values()))
    print(db.docstore.__dict__)



'''
@router.post("/message", response_model=MessagesRead, status_code=status.HTTP_200_OK)
async def chat_message(
    data: MessageCreate,
    db: Session = Depends(get_db)
):
    """
    1) LangChain → query_chain 호출
    2) 결과를 DB에 저장
    3) 전체 히스토리를 반환
    """
    # ── 1. LLM / 툴 호출 ───────────────────────────────────────────────
    try:
        payload: dict = await query_chain(          # ← JSONResponse 대신 dict!
            question=data.message,
            user_id=data.user_id,
            db=db
        )
        print(f"[DEBUG] query_chain 결과: {payload!r}")
    except Exception as exc:
        # 내부 예외를 502 Bad Gateway 로 래핑
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 호출 실패: {exc!s}"
        ) from exc

    # ── 2. DB 저장 ───────────────────────────────────────────────────
    db_msg = Message(
        user_id=data.user_id,
        message=data.message,
        answer=payload.get("answer", ""),
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    # ── 3. 전체 히스토리 조회 & 반환 ─────────────────────────────────
    msgs = (
        db.query(Message)
          .filter(Message.user_id == data.user_id)
          .order_by(Message.timestamp.asc())
          .all()
    )
    return MessagesRead(
        user_id=data.user_id,
        messages=[MessageRead.from_orm(m) for m in msgs]
    )

여기서 2, 3 
DB에 message를 user_id, message, answer에 따라 저장.
metadata에 user_id를 통해 history 살펴보면 될듯
'''
#################################################################
'''
# context에 기존 대화 내역 추가하는 코드

async def query_chain(user_id: int,
                      question: str,
                      db: Session) -> dict[str, Any]:
    """
    ① DB 에서 과거 대화 이력 조회
    ② LangChain 분류 체인으로 IntentOnly 얻기
    ③ Intent 라우터(chain) 실행 → 결과(Pydantic | dict | str)
    ④ 언제나 JSON 직렬화 가능한 형태로 감싸서 JSONResponse 반환
    """
    # 지연 import – 순환 참조 방지
    from api_server.models.chat_log import Message

    print(f"[DEBUG] query_chain: 시작 user_id={user_id}, question={question!r}")

    # ── 1) 대화 이력 —————————————————————————————
    history: list[tuple[str, Any]] = []
    try:
        chat_logs = (
            db.query(Message)
              .filter(Message.user_id == user_id)
              .order_by(Message.timestamp.asc())
              .all()
        )
    except Exception as e:
        print(f"[WARN] DB 조회 실패: {e}")
        chat_logs = []

    for log in chat_logs:
        # human
        history.append(("human", _to_plain(log.message)))
        # bot
        try:
            bot_payload = (
                log.answer
                if isinstance(log.answer, dict)
                else json.loads(log.answer)
            )
        except Exception:
            bot_payload = log.answer
        history.append(("chatbot", _to_plain(bot_payload)))

    print(f"[DEBUG] history 길이 = {len(history)}")

    # ── 2) IntentOnly 분류 ——————————————————————————
    intent_only: IntentOnly = await asyncio.get_event_loop().run_in_executor(
        None,
        classification_chain.invoke,
        {
            "question": question,
            "format_instructions": intent_parser.get_format_instructions(),
            "chat_history": history,
        },
    )
    print(f"[DEBUG] IntentOnly = {intent_only}")

    # ── 3) Intent 라우팅 체인 —————————————————————————
    chain_output = await asyncio.get_event_loop().run_in_executor(
        None,
        router.invoke,
        {
            "intent_only": intent_only,
            "question":    question,
            "chat_history": history,
        },
    )

    # ── 4) 결과 직렬화 & 응답 —————————————————————————
    try:
     # 3) 라우팅 후
      if isinstance(chain_output, BaseModel):
       chain_output = chain_output.model_dump(mode="python")

       answer = {
        "answer": {
            "intent": intent_only.intent.value,
            "contents": chain_output["contents"]   # 이미 dict
        }
    }
    except Exception as err:
        # 마지막 보루 – 문자열로라도 반환
        print(f"[ERROR] 직렬화 실패: {err}")
        answer = {
            "answer": {
                "intent": intent_only.intent.value,  # Intent 문자열로 변환
                "contents": chain_output.contents,       # Pydantic 모델이나 dict
            }
        }
    return answer
    
'''
>>>>>>> Stashed changes
