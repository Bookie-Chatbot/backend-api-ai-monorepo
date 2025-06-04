from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.chat_log import ChatLog
from schemas.chat_log import ChatLogCreate, ChatLogRead
from models.chat_log import Message
from schemas.message import MessageCreate, MessageRead, MessagesRead
from models.ai_response import AI_Response
from schemas.ai_response import ai_responseCreate
from runs.main import query_chain
from fastapi.responses import JSONResponse
import re,json
<<<<<<< Updated upstream
from typing import List
=======
from typing import List, Any, Union
from pydantic import BaseModel
from langchain_core.messages import AIMessage
>>>>>>> Stashed changes

router = APIRouter(prefix="/chat")

@router.post("/log")
def log_chat_message(data: ChatLogCreate, db: Session = Depends(get_db)):
    new_log = ChatLog(**data.dict())
    db.add(new_log)
    db.commit()
    return {"message": "유저 메시지 저장 완료"}

@router.get("/log/{session_id}")
def get_chat_logs(session_id: str, db: Session = Depends(get_db)):
    logs = db.query(ChatLog)\
             .filter(ChatLog.session_id == session_id)\
             .order_by(ChatLog.timestamp.asc())\
             .all()
    print(f"▶️ 세션 ID: {session_id}에 대한 로그:")
    for log in logs:
        print(f"  - {log.timestamp}: {log.message} (role: {log.role})")
    return logs

<<<<<<< Updated upstream
=======
from langchain_core.messages import BaseMessage   # 이미 있다면 생략

def _to_plain(obj):
    """LangChain BaseMessage → str | dict | list 로 평탄화."""
    if isinstance(obj, BaseMessage):
        return obj.content            # AIMessage / HumanMessage 등
    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]
    if isinstance(obj, dict):
        # dict 안에 또 메시지가 있으면 재귀
        return {k: _to_plain(v) for k, v in obj.items()}
    return obj                        # str, int, float, None …

def strip_fence(txt: Any) -> Any:
    # 0️⃣  BaseMessage → 평문
    txt = _to_plain(txt)

    # 1️⃣  문자열이 아니면 strip 불필요
    if not isinstance(txt, str):
        return txt

    # 2️⃣  코드 펜스 제거
    return re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        flags=re.IGNORECASE | re.MULTILINE,
    )


>>>>>>> Stashed changes
@router.post("/ai-response")
def log_ai_response(data: ai_responseCreate, db: Session = Depends(get_db)):
    new_response = AI_Response(**data.dict())
    db.add(new_response)
    db.commit()
    return {"message": "AI 응답 저장 완료"}

<<<<<<< Updated upstream
def strip_fence(s: str) -> str:
    """
    ai 응답에 ```json ... ``` 형태로 감싸진 경우
    ```json ... ``` 로 감싸진 부분을 제거하고
    순수 JSON 문자열만 리턴함.
    """
    return re.sub(r"^```json\s*|\s*```$", "", s, flags=re.MULTILINE).strip()

@router.post("/message", response_model=MessagesRead)
async def chat_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
):
    # --- [0] 시작 로그 ---
    print(">>> [chat_message] 시작")
    print(f"    입력 데이터: user_id={data.user_id}, message={data.message!r}")

    # --- [1] AI 호출 ---
    print(">>> [1] query_chain 호출 직전")
    try:
        ai_resp: JSONResponse = await query_chain(
=======

def _safe_json(text: str) -> Union[str, dict, list]:
    """
    fence 제거 → json.loads → 실패 시 원문 그대로 반환.
    text 가 이미 dict/ list 면 그대로 pass-through.
    """
    if isinstance(text, (dict, list)):
        return text

    txt = strip_fence(text)
    try:
        return json.loads(txt)
    except Exception as e:
        print(f"[WARN] json.loads 실패 → 원문 반환: {e}")
        return text          # 평문 그대로



from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

router = APIRouter()

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
>>>>>>> Stashed changes
            question=data.message,
            user_id=data.user_id,
            db=db
        )
<<<<<<< Updated upstream
    except Exception as e:
        print("!!! [1] query_chain 실행 중 예외 발생:", repr(e))
        raise HTTPException(500, detail="AI 호출 중 에러 발생")

    print(">>> [1] query_chain 리턴됨:", ai_resp)
    # --- [2] JSONResponse → dict ---

    raw_text   = ai_resp.body.decode("utf-8")
    clean_text = strip_fence(raw_text)

    # --- 파이썬 객체로 변환 ---
    parsed = json.loads(clean_text)

    # --- if we still have a JSON string, unwrap it ---
    if isinstance(parsed, str) and "{" in parsed and "}" in parsed:
        inner = strip_fence(parsed)
        try:
            parsed = json.loads(inner)
        except json.JSONDecodeError:
            # 아직도 제이슨 아니면 놔둠
            pass

    resp_dict = parsed

    # --- optionally unwrap nested contents ---
    raw_contents = resp_dict.get("contents", "")
    if isinstance(raw_contents, str):
        inner = strip_fence(raw_contents)
        try:
            resp_dict["contents"] = json.loads(inner)
        except json.JSONDecodeError:
            # 아직도 제이슨 아니면 놔둠
            pass

    # --- save to DB ---
    db_msg = Message(
        user_id = data.user_id,
        message = data.message,
        answer  = {
            "intent":   resp_dict.get("intent", ""),
            "contents": resp_dict.get("contents", {}),
        }
=======
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
>>>>>>> Stashed changes
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
<<<<<<< Updated upstream
    messages = db.query(Message).filter(Message.user_id == data.user_id).all()
    messagesList = [MessageRead.from_orm(m) for m in messages]
    response = MessagesRead(user_id=data.user_id, messages=messagesList)
    print(f"    DB에 저장된 메시지: {messagesList}")
    print(f"    응답: {response}")
    return response
=======

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

>>>>>>> Stashed changes


@router.get("/messages/", response_model=MessagesRead)
async def read_messages(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    messages = db.query(Message).filter(Message.user_id == user_id).offset(skip).limit(limit).all()
    messagesList = [MessageRead.from_orm(m) for m in messages]

    response = MessagesRead(user_id=user_id, messages=messagesList)
    print(f"read_messages: {messagesList}")
    return response


@router.delete("/messages/{user_id}/{session_id}")
async def delete_message(
    user_id: int,
    session_id: str,
    db: Session = Depends(get_db)
):
    try:
        db.query(Message).filter(Message.user_id == user_id, Message.session_id == session_id).delete()
        db.commit()
        return {"message": "Message deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete message")



@router.delete("/messages/{user_id}")
async def delete_messages(
    user_id: int,
    db: Session = Depends(get_db)
):
    try:
        db.query(Message).filter(Message.user_id == user_id).delete()
        db.commit()
        return {"message": "Messages deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete messages")