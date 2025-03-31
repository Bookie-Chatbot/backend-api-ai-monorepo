from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import reservation as models
from schemas import reservation as schemas

router = APIRouter(
    prefix="/reservations",
    tags=["reservations"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ReservationResponse)
def create_reservation(reservation: schemas.ReservationCreate, db: Session = Depends(get_db)):
    db_reservation = models.Reservation(
        user_id=reservation.user_id,
        hotel_id=reservation.hotel_id,
        flight_id=reservation.flight_id,
        status=reservation.status
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation