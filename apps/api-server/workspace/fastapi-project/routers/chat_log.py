from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.chat_log import ChatLog
from schemas.chat_log import ChatLogCreate, ChatLogRead
from models.chat_log import Message
from schemas.message import MessageCreate, MessageRead
from models.ai_response import AI_Response
from schemas.ai_response import ai_responseCreate
from runs.main import query_chain

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


@router.post("/message", response_model=MessageRead)
async def chat_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
):
    # 1) LLM 호출: question + user_id → JSONResponse(payload)
    ai_resp = await query_chain(question=data.message, user_id=data.user_id, db=db)
    try:
        resp_dict = ai_resp.json()
    except Exception:
        raise HTTPException(500, detail="AI 응답 처리 중 에러 발생")

    # 2) DB 저장: question + {"intent": ..., "content": ...}
    msg = Message(
        user_id = data.user_id,
        question = data.question,
        answer   = {
            "intent":  resp_dict.get("intent", ""),
            "contents": resp_dict.get("contents", {})
        }
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # 3) client 에 저장된 레코드 전체 리턴
    return msg