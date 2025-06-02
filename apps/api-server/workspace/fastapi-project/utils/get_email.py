from sqlalchemy.orm import Session
from models.user import User

def get_user_email(db: Session, user_id: int) -> str | None:
    user = db.query(User).filter(User.id == user_id).first()
    return user.email if user else None
