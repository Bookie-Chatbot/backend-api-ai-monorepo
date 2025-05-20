from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.chat_log import ChatLog
from schemas.chat_log import ChatLogCreate
from models.ai_response import AI_Response
from schemas.ai_response import ai_responseCreate

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
    return logs

@router.post("/ai-response")
def log_ai_response(data: ai_responseCreate, db: Session = Depends(get_db)):
    new_response = AI_Response(**data.dict())
    db.add(new_response)
    db.commit()
    return {"message": "AI 응답 저장 완료"}