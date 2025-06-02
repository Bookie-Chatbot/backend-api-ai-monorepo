from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.price_track import PriceTrackRequestModel
from schemas.price_track import PriceTrackCreate, PriceTrackResponse
from tasks.price_check_task import check_price

router = APIRouter()

@router.post("/price/track", response_model=PriceTrackResponse)
def track_price(req: PriceTrackCreate, db: Session = Depends(get_db)):
    # 요청 저장
    new_track = PriceTrackRequestModel(
        user_id=req.user_id,
        search_params=req.search_params,
        price_threshold=req.price_threshold,
        is_active=True,
    )
    db.add(new_track)
    db.commit()
    db.refresh(new_track)

    print("🔥 BEFORE TASK")
    print(f"[DEBUG] Sending to task: user_id={new_track.user_id}, params={new_track.search_params}")
    check_price.delay(
        new_track.user_id,
        new_track.search_params,
        new_track.price_threshold
    )

    print("🔥 AFTER TASK")
    return new_track
