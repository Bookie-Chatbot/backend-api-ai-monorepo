from fastapi import APIRouter, Depends
from pydantic import BaseModel
from tasks.price_check_task import check_price

router = APIRouter()

class PriceTrackRequest(BaseModel):
    user_id: int
    search_params: dict
    price_threshold: int

@router.post("/price/track")
def track_price(req: PriceTrackRequest):
    # Celery task 호출
    check_price.delay(req.user_id, req.search_params, req.price_threshold)
    return {"message": "가격 추적을 서비스를 시작합니다."}