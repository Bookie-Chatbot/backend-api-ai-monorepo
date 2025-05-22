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
from typing import List, Any, Union
from pydantic import BaseModel
from langchain_core.messages import AIMessage

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


@router.post("/ai-response")
def log_ai_response(data: ai_responseCreate, db: Session = Depends(get_db)):
    new_response = AI_Response(**data.dict())
    db.add(new_response)
    db.commit()
    return {"message": "AI 응답 저장 완료"}


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



@router.post("/message", response_model=MessagesRead)
async def chat_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
):
    print(">>> [chat_message] 시작")
    print(f"    입력: user_id={data.user_id}, message={data.message!r}")

    # ① LLM / tool 호출
    try:
        ai_resp: JSONResponse = await query_chain(
            question=data.message,
            user_id=data.user_id,
            db=db
        )
    except Exception as e:
        # LLM 자체 호출 실패 → “fallback” 메시지 구성
        print("!!! query_chain 예외:", repr(e))
        fallback = {
            "intent":   "ERROR",
            "contents": {
                "message": "죄송해요! 잠시 오류가 발생했어요. 나중에 다시 시도해 주세요. 🙏"
            }
        }
        return MessagesRead(user_id=data.user_id, messages=[fallback])

    # ② 성공적으로 돌아온 경우에도 JSON 파싱에 실패할 수 있음
    raw_text = ai_resp.body.decode("utf-8")
    parsed   = _safe_json(raw_text)

    # 여전히 문자열이면 contents 에 그대로 담아서 리턴
    if isinstance(parsed, str):
        parsed = {
            "intent":   "RAW_TEXT",
            "contents": {"message": parsed}
        }

    # ③ 내부 contents 도 안전 파싱
    contents = parsed.get("contents", "")
    parsed["contents"] = _safe_json(contents)

    # ④ DB 저장
    db_msg = Message(
        user_id = data.user_id,
        message = data.message,
        answer  = parsed
    )
    db.add(db_msg);  db.commit();  db.refresh(db_msg)

    # ⑤ 전체 대화 리스트 반환
    messages = db.query(Message).filter(Message.user_id == data.user_id).all()
    return MessagesRead(
        user_id=data.user_id,
        messages=[MessageRead.from_orm(m) for m in messages],
    )


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