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
from typing import List

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

@router.post("/ai-response")
def log_ai_response(data: ai_responseCreate, db: Session = Depends(get_db)):
    new_response = AI_Response(**data.dict())
    db.add(new_response)
    db.commit()
    return {"message": "AI 응답 저장 완료"}

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
            question=data.message,
            user_id=data.user_id,
            db=db
        )
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
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    messages = db.query(Message).filter(Message.user_id == data.user_id).all()
    messagesList = [MessageRead.from_orm(m) for m in messages]
    response = MessagesRead(user_id=data.user_id, messages=messagesList)
    print(f"    DB에 저장된 메시지: {messagesList}")
    print(f"    응답: {response}")
    return response


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