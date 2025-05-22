import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from tasks.price_check_task import check_price
from database import Session, get_db

router = APIRouter()

class PriceTrackRequest(BaseModel):
    user_id: int
    search_params: dict
    price_threshold: int

# POST /price/track
@router.post("/price/track")
def track_price(req: PriceTrackRequest, db: Session = Depends(get_db)):
    new_req = PriceTrackRequest(**req.dict(), is_active=True)
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return {"msg": "✅ 추적 요청이 저장되었습니다."}